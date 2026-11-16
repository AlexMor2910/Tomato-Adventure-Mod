"""Narrow three-map destination audit. No ROM/save/state writes or emulator.

python -B tools/analyze/cumulative_v3_music_resolution.py
Writes fresh evidence/decision reports; refuses existing destinations.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/analyze'), str(ROOT / 'tools/patch')]
from cumulative_v2_music import roots, walk
from hawker_stage1 import native_function
from thumb_inspect import decode
import verify_cumulative_v2
import cumulative_v2

DIRECTORY = ROOT / 'tools/patch/output/cumulative-v3-20261028'
V2_DIR = ROOT / 'tools/patch/output/cumulative-v2-20261028'
V2_HASH = '300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482'
MAPS = (0x12C, 0x158, 0x16D)


def sha(data):
	return hashlib.sha256(data).hexdigest()


def write(path, data):
	if path.exists():
		if json.loads(path.read_bytes()) != data:
			raise ValueError('Existing evidence differs; choose a new versioned path')
		return
	with path.open('x', encoding='utf-8') as stream:
		json.dump(data, stream, indent=2)
		stream.write('\n')


def saved_destination(raw):
	"""FD73/FD74 read immediate LE map words; FD75's byte is flags, not ID."""
	if raw[:2] not in (b'\xfd\x73', b'\xfd\x74') or len(raw) != 9:
		raise ValueError('Not a saved destination writer')
	return int.from_bytes(raw[2:4], 'little')


def ordinary_incoming(rom):
	result = {m: [] for m in MAPS}
	for mid in range(494):
		a = 0x62D3E4 + 28 * mid
		p = struct.unpack_from('<I', rom, a + 12)[0] - 0x08000000
		for i in range(64):
			q = p + i * 10
			if rom[q] == 255:
				break
			destination = struct.unpack_from('<H', rom, q + 4)[0]
			if destination in result:
				result[destination].append(dict(source_map=mid, file=q, raw=rom[q:q + 10].hex(' ')))
		else:
			raise ValueError('Exit bound exceeded')
	return result


def literal_destinations(rom, mid):
	result = []
	for prefix in (b'\xfd\x73', b'\xfd\x74', b'\xfe\x7c', b'\xfe\x7d'):
		pattern = prefix + struct.pack('<H', mid)
		p = 0xF9000
		while True:
			p = rom.find(pattern, p, 0x13D1EC)
			if p < 0:
				break
			result.append(dict(file=p, prefix=prefix.hex(' '), status='byte-pattern lead; requires command/context proof'))
			p += 1
	return result


def main():
	r = (V2_DIR / 'build/tomato_cumulative_v2_INCOMPLETE.gba').read_bytes()
	b = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	j = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
	p = (ROOT / 'tools/patch/output/cumulative-v1-20261028/build/tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
	assert len(r) == 8388608 and sha(r) == V2_HASH
	assert sha(j) == '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
	validation = verify_cumulative_v2.verify(b, p, r, V2_DIR / 'build')
	assert cumulative_v2.build(b, p)[0] == r
	identity = json.loads((V2_DIR / 'release_identity.json').read_bytes())
	for name, key in [('build/tomato_cumulative_v2.bps', 'bps_sha256'), ('build/v1_to_v2.bps', 'incremental_bps_sha256'),
		('tomato_cumulative_v2_INCOMPLETE_patch.zip', 'zip_sha256')]:
		assert sha((V2_DIR / name).read_bytes()) == identity[key]
	write(DIRECTORY / 'v2_reverification.json', dict(rom_sha256=sha(r), bytes=len(r), independent=validation,
		canonical_incremental_match=True, patch_and_zip_identities_match=True,
		historical_preservation_report=json.loads((V2_DIR / 'preservation_audit.json').read_bytes()),
		note='Historical audit independently checked against current inventory in final preservation audit; historical report alone is not treated as proof.'))
	native_roots = {'FD73': 0x27DB8, 'FD74': 0x27DFC, 'FD75': 0x27E50,
		'byte_operand': 0x22534, 'word_operand': 0x227F0,
		'field_request_start': 0x2C1F0, 'map_offset_controller': 0x68418,
		'controller_dispatch': 0x683A4, 'controller_tick': 0x68090,
		'controller_menu_init': 0x67FDC, 'controller_map_accept': 0x680B8,
		'mode_switch': 0x2C148}
	native = {name: native_function(r, a) for name, a in native_roots.items()}
	for row in native.values():
		for instruction in row['instructions']:
			a = int(instruction['bus'], 16) - 0x08000000
			size = len(bytes.fromhex(instruction['bytes']))
			assert r[a:a + size] == b[a:a + size] == j[a:a + size]
	# Literal-load references only, within known native code; no whole-ROM auto-analysis.
	storage_refs = []
	for a in range(0, 0xF9000, 2):
		if struct.unpack_from('<H', r, a)[0] & 0xF800 == 0x4800:
			i = decode(r, a)
			if i.literal_value in (0x03001ABC, 0x03001AC4, 0x03001AC2, 0x03001ACA):
				storage_refs.append(dict(bus=i.address, literal=i.literal_value, instruction=i.text))
	# Bound registered roots to the three records, the disputed Vault path and
	# existing Oystown channel entry/return rooms; no fresh whole-world traversal.
	scope_maps = sorted(set(MAPS) | {0x124, 0x125, 0x126, 0x127, 0x128, 0x129, 0x12A, 0x12B,
		0x155, 0x156, 0x157, 0x15B} | set(range(0x10B, 0x110)) | set(range(0x169, 0x16D)))
	scopes = []
	for mid in scope_maps:
		commands, status = walk(r, roots(r, mid))
		assert not status['budget_exhausted']
		writes = []
		for a, raw in sorted(commands.items()):
			if raw[:2] in (b'\xfd\x73', b'\xfd\x74', b'\xfd\x75'):
				writes.append(dict(file=a, raw=raw.hex(' '), destination=saved_destination(raw) if raw[1] != 0x75 else None,
					note='FD75 byte is flags, not a destination' if raw[1] == 0x75 else 'LE immediate word from command arguments'))
		scopes.append(dict(map_id=mid, roots=roots(r, mid), traversal=status, saved_destination_commands=writes,
			transfers=[dict(file=a, raw=commands[a].hex(' '), destination=int.from_bytes(commands[a][2:4], 'little')) for a in status['transfers']],
			music_commands=[dict(file=a, raw=raw.hex(' ')) for a, raw in sorted(commands.items()) if raw[:2] in (b'\xfe\xa7', b'\xfe\xa8', b'\xfe\xa9', b'\xfe\xab')]))
	incoming = ordinary_incoming(r)
	# Decode the existing controller labels using the project's original table.
	characters = {}
	for line in (ROOT / 'tomatotrans-1.1.1/ta_table_jpn.txt').read_text(encoding='utf-8-sig').splitlines():
		parts = line.split(maxsplit=1)
		if len(parts) == 2:
			characters[int(parts[0], 16)] = parts[1]
	menu = [''.join(characters.get(v, '?') for v in r[a:a + 8]) for a in range(0x64A19C, 0x64A1D4, 8)]
	assert r[0x684C0:0x684C8] == bytes.fromhex('0D 4C E0 68 61 68 40 18')
	assert r[0x684E2:0x684EE] == bytes.fromhex('06 4A 04 48 81 89 D1 80 05 48 C1 80')
	ledger = []
	for mid in MAPS:
		a = 0x62D3E4 + mid * 28
		context = next(s for s in scopes if s['map_id'] == mid)
		assert r[a + 5] == b[a + 5] == j[a + 5] == 14
		ledger.append(dict(map_id=f'0x{mid:04X}', map_record_file=a, music_byte_file=a + 5,
			original_music_byte=f'{r[a + 5]:02X}', current_selector=r[a + 5] & 63,
			proposed_destination_selector=None, region_identity='Unresolved; graphics/context are not sufficient for an active-region assignment',
			relevant_incoming_paths=dict(ordinary=incoming[mid], literal_field_script_references=literal_destinations(r, mid),
				conditional_controller='080684C0 adds signed/wrapped offset to saved current ID; not a proved normal story entry'),
			destination_writers=[dict(bus='08027DC0', destination_storage='03001ACA', meaning='FD73 immediate LE map word'),
				dict(bus='08027E08/08027E16', destination_storage='03001AC2', meaning='FD74 low byte plus high byte shifted8'),
				dict(bus='080684E8/080684EC', destination_storage='03001ACA/03001936', meaning='conditional map-selection controller sum')],
			transition_consumers=[dict(bus='08027E5C..08027E60', meaning='FD75 copies saved03001AC2 to saved03001ACA and request03001936; no arithmetic ID construction'),
				dict(bus='08027ED8', meaning='FD75 starts transition through0802C1F0'),
				dict(bus='08033D2A..08033D36', meaning='loader selects map record from request+6, stride28')],
			reachability_conclusion='Conditional controller selection supported; normal-play incoming path unproved',
			music_overrides=context['music_commands'], patch_decision='leave unchanged',
			evidence=['cumulative_v3_destination_evidence.json native/scopes; actual map record; all494 ordinary exit lists',
				'v2 music plan and fixed soundtrack mappings retained'], confidence='Unresolved',
			map_facts_confidence='Confirmed static', local_saved_destination_commands=context['saved_destination_commands']))
	# More specific proof stops; never promote conditional UI selection to story reachability.
	ledger[0]['proof_stop'] = '012C rectangle0812D7B3 checks flag0155 and runs battle30; it is local behavior, not an incoming writer. No normal destination writer to012C was found.'
	ledger[0]['local_flags'] = ['0155 guard/set in rectangle0812D7B3..0812D7EF']
	ledger[1]['proof_stop'] = '0127 registered rectangle0810054A branches on flag010B and explicitly transfers to0157 at08100557, not0158. No FD73/74/75 in the scoped0127 closure constructs0158.'
	ledger[1]['local_flags'] = ['010B gates actual0127→0157 path; no established0158 selector flag']
	ledger[2].update(region_identity='Oyster Sewers — side channel connected to confirmed016C',
		proposed_destination_selector=0x10, confidence='Confirmed static', patch_decision='patch',
		reachability_conclusion='Supported static normal field path: Oystown010F→016C→016D; runtime not tested')
	ledger[2]['relevant_incoming_paths']['normal_field_path'] = [
		dict(script='08105ACC', meaning='FE7C selects016C from registered Oystown010F event; alternate08105B3C FE7D also selects016C'),
		dict(exit_record='0813C61A', source_map='016C', destination_map='016D', trigger='x0,y3..4', destination='x13,y4'),
		dict(exit_record='0813C628', source_map='016D', destination_map='016C', trigger='x14,y3..4', destination='x1,y4')]
	ledger[2]['destination_writers'].insert(0, dict(bus='08069AA6..08069AAC',
		destination_storage='03001ACA/03001936', meaning='ordinary exit loader reads destination LE016D from exit record+4 and writes saved/request IDs'))
	ledger[2]['proof_stop'] = 'Ordinary incoming edge0813C61A, already retained in map_transitions.csv row594, was missed in v2 reporting. Actual exit record, normal consumer, mutual return, Oystown entry scripts and sewer resource identity now corroborate membership. FD73/74 in016D set010B return IDs; they are not the incoming mechanism.'
	ledger[2]['local_flags'] = ['00C3 and01FE in default0810C600; no established incoming selector flag']
	write(DIRECTORY / 'cumulative_v3_destination_evidence_final.json', dict(native=native, native_storage_literal_refs=storage_refs,
		controller_labels=menu, controller_label_file='0x0064A19C',
		controller_dispatch_entry=dict(table_file='0x0062B408', index=3, target='0x08020ED1', wrapper_call='0x08020ED2→0x08068090'),
		scopes=scopes, ordinary_incoming=incoming, literal_scan_file_interval=[0xF9000, 0x13D1EC],
		limitations=['Literal-load xrefs do not prove absence of all aliased writes', 'Conservative script closure retains false paths',
			'Controller activation in normal gameplay not proved', 'No claim of exhaustive normal-game unreachability or unused status']))
	operation = dict(feature='music', area='Oyster Sewers', map_id=0x16D,
		offset=0x62D3E4 + 0x16D * 28 + 5, bus=0x0862FBD5, old='0e', new='10', confidence='Confirmed static',
		evidence='0813C61A normal016C→016D exit; consumer08069AA6; return0813C628; Oystown010F script08105ACC; matching sewer resources')
	write(ROOT / 'reverse_engineering/cumulative_v3_music_resolution.json', dict(status='Tomato Adventure — Cumulative v3 Incomplete Experimental Build',
		input_v2_sha256=V2_HASH, maps=ledger, approved_operations=[operation], build_decision='Build canonical and incremental v3 with one additional selector byte',
		correction='V2 no-incoming claim for016D was incorrect: both ordinary edges were already retained in map_transitions.csv. Initial v3 draft preserved locally; corrected through independent readback, not relaxed assertions.',
		retained_v2_room_counts={'Dropper Village': 8, 'Mayonen Caverns': 15, 'Captain Grocko Ship': 29, 'Oyster Sewers': 14, 'The Vault': 21},
		exhaustive_event_coverage=False, runtime='No emulator, RAM, save or savestate operation'))
	print(json.dumps(dict(rom_writes=0, maps=[(x['map_id'], x['patch_decision']) for x in ledger], evidence=str(DIRECTORY))))


if __name__ == '__main__':
	main()
