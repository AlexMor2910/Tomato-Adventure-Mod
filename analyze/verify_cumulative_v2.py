"""Independent v2 readback. No import of v2 planner, builder, or traversal.

python -B tools/analyze/verify_cumulative_v2.py V2_BUILD_DIRECTORY
"""
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from verify_cumulative_v1 import verify as verify_v1, decode_bps, require

V1_DIR = ROOT / 'tools/patch/output/cumulative-v1-20261028/build'
GROUPS = {
	'Dropper Village': ([1, 2, 3, 4, 5, 6, 7, 29], 13, 4),
	'Mayonen Caverns': (list(range(30, 44)) + [46], 7, 13),
	'Captain Grocko Ship': (list(range(226, 251)) + [153, 154, 155, 156], 36, 14),
	'Oyster Sewers': (list(range(143, 153)) + [361, 362, 363, 364], 16, 14),
	'The Vault': (list(range(292, 300)) + list(range(336, 344)) + [347, 487, 488, 489, 490], 8, 14),
}


def sha(data):
	return hashlib.sha256(data).hexdigest()


def verify(baseline, prior, target, directory):
	require(sha(baseline) == '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde', 'Baseline hash')
	require(sha(prior) == '1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f', 'Prior hash')
	require(len(baseline) == len(prior) == len(target) == 8388608, 'ROM size')
	# Separately encoded sets and target selectors, checked against documentary ledger.
	with (ROOT / 'reverse_engineering/cumulative_v2_music_rooms.csv').open(encoding='utf-8') as stream:
		rooms = list(csv.DictReader(stream))
	approved = {(r['requested_area'], int(r['map_id'], 16)): r for r in rooms if r['include_exclude'] == 'include'}
	require(len(approved) == 87, 'Room count')
	require(set(approved) == {(a, m) for a, (ms, selector, old) in GROUPS.items() for m in ms}, 'Room allowlist differs')
	expected = {}
	restored = bytearray(target)
	for area, (mids, selector, original) in GROUPS.items():
		for mid in mids:
			a = 0x62D3E4 + mid * 28 + 5
			row = approved[area, mid]
			require(row['confidence'] == 'Confirmed' and int(row['music_byte_file_offset'], 16) == a, 'Unsupported room')
			require(int(row['proposed_destination_selector'], 16) == selector, 'Selector ledger')
			require(baseline[a] & 63 == original, 'Original map selector')
			require(target[a] & 63 == selector and target[a] & 192 == prior[a] & 192, 'Map readback/upper bits')
			want = (prior[a] & 192) | selector
			if prior[a] != want:
				expected[a] = (prior[a], want)
			restored[a] = prior[a]
	# Native verified named-map destination anchors, independent of human track order.
	for mid, title, selector in [(8, 1, 13), (0x48, 3, 7), (0x60, 4, 36), (0x104, 5, 16), (0x38, 21, 8)]:
		a = 0x62D3E4 + mid * 28
		require(baseline[a + 2] >> 2 == title and baseline[a + 5] & 63 == selector, 'Original named soundtrack anchor')
		require(target[a:a + 28] == prior[a:a + 28], 'Destination source map modified')
	require(prior[0x128F08:0x128F16] == bytes.fromhex('FE AB FE A9 0D FE 07 00 2E 4D 12 08 FD 7C'), 'AWE restore context')
	require(target[0x128F08:0x128F16] == bytes.fromhex('FE AB FE A9 07 FE 07 00 2E 4D 12 08 FD 7C'), 'AWE restore new value')
	expected[0x128F0C] = (13, 7)
	restored[0x128F0C] = prior[0x128F0C]
	for a, raw in [(0x128D76, 'FE AB FE A9 04'), (0x128E7A, 'FE AB FE A9 04'), (0x117C21, 'FE A7 09')]:
		require(target[a:a + len(bytes.fromhex(raw))] == bytes.fromhex(raw), 'Intentional lesson/disco cue changed')
	for mid in (300, 344, 365):
		a = 0x62D3E4 + mid * 28
		require(target[a:a + 28] == prior[a:a + 28], 'Unresolved candidate patched')
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(prior, target)) if a != b}
	require(actual == expected and len(actual) == 87, 'Unexpected v1-to-v2 differences')
	# Restoring exactly these music changes must reproduce and pass the full v1 verifier.
	require(bytes(restored) == prior, 'Prior features changed')
	regression, comparisons = verify_v1(baseline, bytes(restored), V1_DIR)
	require(regression['attack_cases'] == 2304, 'Attack regression')
	for mid in range(494):
		a = 0x62D3E4 + mid * 28
		require(prior[a:a + 5] == target[a:a + 5] and prior[a + 6:a + 28] == target[a + 6:a + 28], 'Unrequested map metadata')
	ledger = json.loads((directory / 'changed_bytes.json').read_bytes())
	combined = {i: (a, b) for i, (a, b) in enumerate(zip(baseline, target)) if a != b}
	require(len(combined) == 281 and {r['file']: (r['old'], r['new']) for r in ledger} == combined and len(ledger) == 281, 'Combined ledger')
	for file, source in [('tomato_cumulative_v2.bps', baseline), ('v1_to_v2.bps', prior)]:
		require(decode_bps((directory / file).read_bytes(), source) == target, 'BPS reconstruction')
	manifest = json.loads((directory / 'manifest.json').read_bytes())
	require(manifest['output_sha256'] == sha(target) and manifest['changed_bytes_from_baseline'] == 281, 'Manifest identity')
	return dict(result='PASS implemented scope; exhaustive music coverage remains unproved',
		status='Cumulative v2 — Incomplete Experimental Build', confirmed_patched_rooms=87,
		changed_bytes_from_v1=87, changed_bytes_from_baseline=281,
		ordinary_restore_overrides_patched=1, intentional_lesson_and_disco_cues_preserved=True,
		previous_feature_groups_byte_identical=True, attack_comparisons=2304, header_valid=True,
		upper_bits_preserved=True, all_other_bytes_identical_to_v1=True, both_bps_reproduce_target=True,
		no_alessa_shortcut=True, no_added_hawkers=True,
		unresolved_maps=['0x012C', '0x0158', '0x016D'], final_rom_runtime='UNTESTED')


def main():
	directory = Path(sys.argv[1])
	result = verify((ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes(),
		(V1_DIR / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes(),
		(directory / 'tomato_cumulative_v2_INCOMPLETE.gba').read_bytes(), directory)
	with (directory / 'independent_verification.json').open('x', encoding='utf-8') as f:
		json.dump(result, f, indent=2)
		f.write('\n')
	print(json.dumps(result))


if __name__ == '__main__':
	main()
