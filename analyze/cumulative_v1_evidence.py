"""Retain narrow missing-dependency investigation; no ROM writes or extraction."""
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from pre_oystown_progression import decode_commands


def main():
	directory = Path(sys.argv[1])
	r = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	j = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
	def save(name, value):
		with (directory / name).open('x', encoding='utf-8') as f:
			json.dump(value, f, indent=2)
	assert hashlib.sha256(j).hexdigest() == '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
	scopes = []
	for label, a, b in [('Lab2', 0x111CE6, 0x111EAB), ('shared acquisition', 0x124B33, 0x124BF2),
		('Alessa natural Caverns scene', 0x1271E9, 0x1275B6)]:
		commands, end = decode_commands(r, a, b)
		assert end == 'exact scoped end'
		scopes.append(dict(label=label, file_start=a, file_end_exclusive=b, commands=commands,
			sha256=hashlib.sha256(r[a:b]).hexdigest(),
			japanese_differing_offsets=[k for k in range(a, b) if r[k] != j[k]],
			music_commands=[c for c in commands if c['bytes'][:5] in ('fe a7', 'fe a8', 'fe a9', 'fe ab')],
			limitation='Linear command boundaries; not exhaustive transitive event reachability'))
	# Verify native calculation windows directly against retained evidence hashes.
	scaling = json.loads((ROOT / 'reverse_engineering/gimmick_difficulty_scaling_evidence.json').read_bytes())
	windows = []
	for row in scaling['bounded_rom_checks']:
		a, b = int(row['file_start'], 16), int(row['file_end_exclusive'], 16)
		assert hashlib.sha256(r[a:b]).hexdigest() == row['english_sha256']
		assert hashlib.sha256(j[a:b]).hexdigest() == row['japanese_sha256']
		windows.append(row)
	records = []
	for ident in (27, 41):
		a = 0x62C250 + (ident - 1) * 88
		assert r[a + 34:a + 58] == j[a + 34:a + 58]
		records.append(dict(id=ident, file=a, base=r[a + 34], cap=r[a + 35], type_flags=r[a + 39],
			percentages=list(r[a + 40:a + 58:2]), auxiliary=list(r[a + 41:a + 58:2])))
	maps = list(csv.DictReader((ROOT / 'tools/extract/extracted_data/maps.csv').open(encoding='utf-8-sig')))
	assert len(maps) == 494
	for row in maps:
		mid = int(row['map_id'], 16)
		assert int(row['music_selector']) == r[0x62D3E4 + mid * 28 + 5] & 63
	transitions = list(csv.DictReader((ROOT / 'tools/extract/extracted_data/map_transitions.csv').open(encoding='utf-8-sig')))
	map_evidence = json.loads((ROOT / 'reverse_engineering/map_extraction_evidence.json').read_bytes())
	near = [0x1E, 0x1F, 0x20, 0x21, 0x22, 0x2A, 0x2B, 0x2E]
	ledger = []
	for mid in near:
		a = 0x62D3E4 + mid * 28 + 5
		confirmed = mid == 0x1E
		ledger.append(dict(area='Mayonen Caverns', map_id=f'0x{mid:04X}', room_name='Caverns entry' if confirmed else None,
			file_offset=a, original_byte=r[a], replacement_byte=(r[a] & 192) | 7 if confirmed else r[a],
			original_selector=r[a] & 63, destination_selector=7, implemented=confirmed,
			source_evidence='session_handoffs/SESSION_HANDOFF_3.md; experiments/mayonen_caverns_music.md; maps.csv; map_transitions.csv',
			event_override_status='Natural recruitment scene has no A7/A8/A9/AB in decoded window; other/transitive paths unresolved',
			confidence='Confirmed' if confirmed else 'Candidate',
			blocker=None if confirmed else 'Only connectivity evidence; area membership unproved'))
	for area, dest in [('Dropper Village', 'Pokypine Forest'), ('Captain Grocko Ship', 'Namp Lagoon'),
		('Oyster Sewers', 'Oystown'), ('The Vault', 'Oops Manor')]:
		ledger.append(dict(area=area, map_id=None, room_name=None, file_offset=None, original_byte=None,
			replacement_byte=None, original_selector=None, destination_selector=13 if dest == 'Pokypine Forest' else None,
			destination_name=dest, source_evidence='maps.csv; map_node_assignments.csv; map_transitions.csv; ta_script_eng.txt; ta_menus_eng.txt',
			event_override_status='Unresolved; no event changes', confidence='Unconfirmed', implemented=False,
			blocker='Complete room membership and area/song anchor not established; no adjacency inference'))
	# Specific named dialogue anchors examined, from actual translation pointer table.
	pointers = (ROOT / 'tomatotrans-1.1.1/pointers1.dat').read_text().splitlines()
	anchors = []
	for ident, label in [(0x36B, 'Oystown Sewer sign'), (0xAC7, 'Oops Manor NPC'), (0xAC8, 'Oops Manor NPC')]:
		sites = [int(x, 16) for x in pointers[ident].split() if x != 'FFFFFFFF']
		anchors.append(dict(message=hex(ident), label=label,
			pointer_sites=[dict(file=p, target=hex(struct.unpack_from('<I', r, p)[0])) for p in sites],
			confidence='Candidate', limitation='Text identity alone does not prove containing room or complete area'))
	save('music_ledger.json', ledger)
	save('investigation.json', dict(scopes=scopes, attack_records=records, verified_calculation_windows=windows,
		lab2_map_event_pointer=hex(struct.unpack_from('<I', r, 0x159D24)[0]),
		music_named_anchors=anchors, transition_count=len(transitions),
		caverns_graph_edges=[e for e in transitions if e['source_map_id'] in [f'0x{m:04X}' for m in near]],
		caverns_script_stops=[s for s in map_evidence['script_prefix_stops'] if s['source_map_id'] in [f'0x{m:04X}' for m in near]],
		music_blocker='Catalog has no proven complete area membership; partial graph cannot supply it; no guessed track/room edits',
		confidence='Confirmed byte facts; Candidate room associations; unresolved transitive music overrides'))
	print('Recorded narrow Lab2, calculation-window, catalog, music-anchor and override evidence')


if __name__ == '__main__':
	main()
