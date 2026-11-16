"""Generate evidence-backed, deliberately incomplete v2 music plan exclusively."""
import csv
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from cumulative_v2_music import GROUPS, TRACKS, DEST, roots, walk, sha, save, BUS, TABLE, V1, DIRECTORY
from hawker_stage1 import native_function

GROUPS = {k: list(v) for k, v in GROUPS.items()}
GROUPS['Oyster Sewers'] += list(range(0x169, 0x16D))
GROUPS['The Vault'] = [m for m in GROUPS['The Vault'] if m != 0x158] + [0x155, 0x156, 0x157, 0x15B]
GROUPS = {k: sorted(v) for k, v in GROUPS.items()}
CANDIDATES = [('Dropper Village', 0x12C), ('The Vault', 0x158), ('Oyster Sewers', 0x16D)]


def csv_write(path, rows):
	with path.open('x', encoding='utf-8', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=list(rows[0]))
		writer.writeheader()
		writer.writerows(rows)


def main():
	r = V1.read_bytes()
	b = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	j = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
	assert sha(r) == '1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f'
	assert sha(b) == '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
	assert sha(j) == '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'
	menus = (ROOT / 'tomatotrans-1.1.1/ta_menus_eng.txt').read_text(encoding='utf-8-sig')
	names_text = menus.split('POINTERLIST 649A08 04 24 31')[1].split('# More')[0]
	names = {int(a, 16): re.sub(r'\[[^]]*\]', '', v) for a, v in re.findall(r'^([0-9A-F]+)-E:(.*)', names_text, re.M)}
	native = {}
	for name, start, end in [('title_loader', 0x33E06, 0x33E1E), ('title_display', 0x6BBBC, 0x6BBEE),
		('map_music', 0x3F824, 0x3F8A4), ('playback', 0x65FD4, 0x65FF4),
		('FEA7', 0x2653C, 0x26578), ('FEA8', 0x26578, 0x265B4), ('FEA9', 0x265B4, 0x265F4),
		('FEAB', 0x26608, 0x26628), ('stop_music', 0x66024, 0x66044), ('stop_sfx', 0x6609C, 0x660B8),
		('FD84', 0x28490, 0x28518), ('FD74_75', 0x27DFC, 0x27F08)]:
		assert r[start:end] == b[start:end] == j[start:end]
		native[name] = dict(file_start=start, file_end_exclusive=end, sha256=sha(r[start:end]),
			original_and_translation_and_v1_identical=True)
		if name in ('FEA7', 'FEA8', 'FEA9', 'FEAB', 'playback', 'stop_music', 'stop_sfx'):
			native[name]['direct_cfg'] = native_function(r, start)
	tracks = []
	for title, (selector, references) in TRACKS.items():
		for mid in references:
			assert r[TABLE + mid * 28 + 5] & 63 == selector
		assert (r[TABLE + references[0] * 28 + 2] >> 2) in names
		tracks.append(dict(destination_track_name=title, verified_selector=f'0x{selector:02X}',
			playback_sound_id=f'0x{selector + 200:02X}', reference_map_ids='|'.join(f'0x{m:04X}' for m in references),
			reference_script_addresses='|'.join(f'0x{p + BUS:08X}' for p, kind, owner in roots(r, references[0]) if kind == 'default'),
			evidence_references='native title loader 08033E12..1C; title display 0806BBBC; ta_menus_eng.txt POINTERLIST 649A08; original map records',
			confidence_status='Confirmed', outstanding_ambiguity='Final-ROM audible behavior untested; Mayonen has prior user audio confirmation'))
	rows, operations, map_evidence, overrides = [], [], [], {}
	for area, mids in GROUPS.items():
		selector = TRACKS[DEST[area]][0]
		for mid in mids:
			a = TABLE + 28 * mid
			resource = struct.unpack_from('<H', r, a)[0]
			commands, traversal = walk(r, roots(r, mid))
			assert not traversal['budget_exhausted']
			local_overrides = [(p, raw) for p, raw in sorted(commands.items()) if raw[:2] in (b'\xfe\xa7', b'\xfe\xa8', b'\xfe\xa9', b'\xfe\xab')]
			for p, raw in local_overrides:
				overrides.setdefault(p, dict(file=p, command=raw.hex(' '), maps=[], patch_required=p == 0x128F0A,
					proposed_behavior='restore Mayonen selector07' if p == 0x128F0A else 'preserve intentional temporary cue or stop',
					confidence='Confirmed' if 0x128D5A <= p < 0x128F48 or p == 0x117C21 else 'Candidate conservative traversal hit'))['maps'].append(mid)
			new = (r[a + 5] & 192) | selector
			title = names.get(r[a + 2] >> 2, '') if r[a + 2] >> 2 else ('The Spillage' if mid == 3 else '')
			if area == 'Mayonen Caverns':
				assert resource == mid
				proof = 'Mayo Hole entry title001E/001F; exact exclusive Caverns tileset family; closed ordinary room component; original recruitment/AWE scenes'
			elif area == 'Captain Grocko Ship':
				proof = 'User-confirmed Sunken Ship alias; title00E2; Garco diary messages712..717; exact ship tileset closure; ship graphics and exits'
			elif area == 'The Vault':
				proof = 'User-confirmed Secret Safe alias; title0124; unique gold-safe tileset; safe/key puzzle scripts; ordinary exits plus 12C8xx/100557/130842/12FBF5 transfers'
			elif area == 'Oyster Sewers':
				proof = 'Sewers1/2 title anchors008F/0094/0095/0098; sewer graphics/resource family; ordinary exits; channels0169..016C explicitly entered from Oystown at10562E/10582A/105975/105ACC'
			else:
				proof = 'Overworld node0 arrival0003/The Spillage; translated Dropper village dialogue; reviewed village exterior/interior graphics; exclusive ordinary village component'
			rows.append(dict(requested_area=area, map_id=f'0x{mid:04X}', verified_map_room_name=title,
				region_membership_evidence=proof, current_selector=f'0x{r[a + 5] & 63:02X}',
				music_byte_file_offset=f'0x{a + 5:08X}', proposed_destination_selector=f'0x{selector:02X}',
				confidence='Confirmed', event_override_status='|'.join(f'0x{p + BUS:08X}' for p, raw in local_overrides) or 'No A7/A8/A9/AB in bounded conservative root closure',
				include_exclude='include', reason='Authored identity, graphics/resource and transition/script evidence combined; not adjacency alone'))
			operations.append(dict(feature='music', area=area, map_id=mid, offset=a + 5, bus=a + 5 + BUS,
				old=f'{b[a + 5]:02x}', old_v1=f'{r[a + 5]:02x}', new=f'{new:02x}',
				original_meaning=f'map selector {b[a + 5] & 63}', new_meaning=DEST[area], evidence=proof, confidence='Confirmed'))
			map_evidence.append(dict(map_id=mid, area=area, resource=resource,
				tileset=hex(struct.unpack_from('<I', r, 0x15BA3C + 4 * resource)[0]),
				palette=hex(struct.unpack_from('<I', r, 0x255F00 + 4 * resource)[0]),
				raw_record=r[a:a + 28].hex(' '), roots=roots(r, mid), traversal=traversal,
				dynamic_commands=[dict(file=p, raw=commands[p].hex(' '), resolved='fixed primary movement opcode; not FE music or script branch') for p in traversal['dynamic_entries']]))
	for area, mid in CANDIDATES:
		a = TABLE + 28 * mid
		rows.append(dict(requested_area=area, map_id=f'0x{mid:04X}', verified_map_room_name='',
			region_membership_evidence='Retained background/resource resembles another area; no ordinary incoming exit or literal FE7C/FE7D/FD74 destination in bounded field-script interval',
			current_selector=f'0x{r[a + 5] & 63:02X}', music_byte_file_offset=f'0x{a + 5:08X}',
			proposed_destination_selector='', confidence='Candidate', event_override_status='Omitted; active-entry provenance unresolved',
			include_exclude='exclude', reason='Do not equate an apparent unused/alternate copy with active normal-play area membership'))
	operations.append(dict(feature='music', area='Mayonen Caverns', map_id=0x24, offset=0x128F0C, bus=0x08128F0C,
		old='0d', old_v1='0d', new='07', original_meaning='AWE lesson restores old area track', new_meaning='restore Mayonen',
		evidence='08128F08 FEAB; 08128F0A FEA90D; 08128F14 FD7C; map0024 default root08128D5A', confidence='Confirmed'))
	assert r[0x128F08:0x128F0D] == bytes.fromhex('FE AB FE A9 0D')
	assert len(operations) == 88 and len({o['offset'] for o in operations}) == 88
	for op in operations:
		assert b[op['offset']] == int(op['old'], 16) and r[op['offset']] == int(op['old_v1'], 16)
	csv_write(ROOT / 'reverse_engineering/cumulative_v2_music_tracks.csv', tracks)
	csv_write(ROOT / 'reverse_engineering/cumulative_v2_music_rooms.csv', rows)
	plan = dict(status='Cumulative v2 — Incomplete Experimental Build', all_five_areas_exhaustively_proven=False,
		baseline_sha256=sha(b), v1_sha256=sha(r), operations=operations,
		confirmed_rooms={a: mids for a, mids in GROUPS.items()}, unresolved_candidates=[dict(area=a, map_id=m) for a, m in CANDIDATES],
		overrides=list(overrides.values()), override_scope='Conservative bounded root/pointer closure, with false paths retained; not universal native-script reachability',
		user_alias_confirmation='User: Yes, both are intended — Sunken Ship/Capn Garco and Soy Bank Secret Safe',
		rooms_csv_sha256=sha((ROOT / 'reverse_engineering/cumulative_v2_music_rooms.csv').read_bytes()),
		tracks_csv_sha256=sha((ROOT / 'reverse_engineering/cumulative_v2_music_tracks.csv').read_bytes()))
	save(ROOT / 'reverse_engineering/cumulative_v2_music_plan.json', plan)
	save(DIRECTORY / 'music_evidence.json', dict(native_windows=native, maps=map_evidence,
		limitations=['conservative pointer closure may contain false paths', 'no dynamic runtime event availability proof',
			'candidate alternate records012C/0158/016D unchanged'],
		sources={p: sha((ROOT / p).read_bytes()) for p in ['tools/extract/extracted_data/maps.csv',
			'tools/extract/extracted_data/map_transitions.csv', 'tomatotrans-1.1.1/ta_menus_eng.txt', 'tomatotrans-1.1.1/ta_script_eng.txt']}))
	print(json.dumps(dict(confirmed_rooms={a: len(v) for a, v in GROUPS.items()}, operations=len(operations), candidates=CANDIDATES)))


if __name__ == '__main__':
	main()
