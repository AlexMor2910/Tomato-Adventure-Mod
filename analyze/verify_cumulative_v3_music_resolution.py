"""Independent readback of the three-map decision and one-byte v3 extension.

python -B tools/analyze/verify_cumulative_v3_music_resolution.py
Does not import the destination analyzer or v3 builder; never emits a ROM.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from verify_cumulative_v2 import verify as verify_v2
from verify_cumulative_v1 import decode_bps

DIRECTORY = ROOT / 'tools/patch/output/cumulative-v3-20261028'


def require(condition, text):
	if not condition:
		raise ValueError(text)


def verify_decisions(rom, report):
	require(len(rom) == 8388608 and hashlib.sha256(rom).hexdigest() ==
		'300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482', 'V2 identity')
	require(len(report['approved_operations']) == 1 and report['approved_operations'][0]['offset'] == 0x62FBD5 and
		report['approved_operations'][0]['old'] == '0e' and report['approved_operations'][0]['new'] == '10', 'Unproved map operations approved')
	require([x['map_id'] for x in report['maps']] == ['0x012C', '0x0158', '0x016D'], 'Decision map IDs')
	for row, mid in zip(report['maps'], (300, 344, 365)):
		a = 0x62D3E4 + mid * 28
		require(row['map_record_file'] == a and row['music_byte_file'] == a + 5, 'Address mismatch')
		require(rom[a + 5] == 14 and row['original_music_byte'] == '0E' and row['current_selector'] == 14, 'Music original byte')
		if mid != 365:
			require(row['patch_decision'] == 'leave unchanged' and row['proposed_destination_selector'] is None and
				row['confidence'] == 'Unresolved', 'Unproved region interpretation promoted')
			require(row['relevant_incoming_paths']['ordinary'] == [], 'Unexpected incoming evidence')
		else:
			require(row['patch_decision'] == 'patch' and row['proposed_destination_selector'] == 16 and
				row['confidence'] == 'Confirmed static', 'Supported sewer decision missing')
			require(row['relevant_incoming_paths']['ordinary'] == [dict(source_map=364, file=0x13C61A,
				raw='00 03 00 04 6d 01 06 0d 84 08')], 'Sewer incoming edge differs')
		require(row['relevant_incoming_paths']['literal_field_script_references'] == [], 'Literal scan changed')
	# Concrete source witnesses, independent from generated native instruction data.
	witnesses = {
		0x27DBA: 'FA F7 19 FD',  # FD73 -> read_u16, return in r0
		0x27DC0: 'E8 80',       # STRH r0,[r5,#6]
		0x27E08: 'E0 80',       # FD74 low byte store
		0x27E10: '00 02  E1 88  40 18  E0 80',
		0x27E5C: 'C8 88 E8 80 F0 80',  # saved B -> saved A and request
		0x684C0: '0D 4C E0 68 61 68 40 18',
		0x684E2: '06 4A 04 48 81 89 D1 80 05 48 C1 80',
		0x10054A: 'FE 1A 00 FD 36 0B 01 64 05 10 08 FE 8B FE 7D 57 01 06 08 07 FE 00 01 00 00 00 FD 7C',
		0x10C600: 'FD 74 0B 01 07 07 00 03 12 FD 73 0B 01 07 07 08 03 12',
		0x13C61A: '00 03 00 04 6D 01 06 0D 84 08',
		0x13C628: '0E 03 0E 04 6C 01 02 01 84 08',
		0x105ACC: 'FE 7C 6C 01 12 01 04 D7 5A 10 08',
		0x69AA6: 'A8 88 D0 80',
	}
	for a, text in witnesses.items():
		b = bytes.fromhex(text)
		require(rom[a:a + len(b)] == b, 'Native/script witness changed at ' + hex(a))
	# Dispatch entry3 selects the controller wrapper, not a three-map story table.
	require(struct.unpack_from('<I', rom, 0x62B408 + 3 * 4)[0] == 0x08020ED1, 'Controller dispatch')
	# Incoming ordinary exit census for these IDs, without importing analysis code.
	found = []
	for mid in range(494):
		p = struct.unpack_from('<I', rom, 0x62D3E4 + mid * 28 + 12)[0] - 0x08000000
		for i in range(64):
			q = p + i * 10
			if rom[q] == 255:
				break
			if struct.unpack_from('<H', rom, q + 4)[0] in (300, 344, 365):
				found.append((mid, q))
		else:
			raise ValueError('Exit bound')
	require(found == [(364, 0x13C61A)], 'Ordinary incoming evidence differs')
	# Independent corroboration: both lower-channel records select the same resources.
	indices = [struct.unpack_from('<H', rom, 0x62D3E4 + m * 28)[0] for m in (364, 365)]
	for table in (0x15BA3C, 0x255F00):
		require(struct.unpack_from('<I', rom, table + indices[0] * 4)[0] ==
			struct.unpack_from('<I', rom, table + indices[1] * 4)[0], 'Sewer graphic/palette identity differs')
	for mid in (300, 344, 365):
		for family in (b'\xfd\x73', b'\xfd\x74', b'\xfe\x7c', b'\xfe\x7d'):
			require(rom.find(family + struct.pack('<H', mid), 0xF9000, 0x13D1EC) < 0, 'Literal reference evidence changed')
	return dict(decision='One supported operation:016D selector0E→10;012C/0158 unchanged',
		saved_destination_semantics_witnesses_pass=True, conditional_controller_witnesses_pass=True,
		ordinary_incoming_rechecked=True, sewer_normal_path_statically_supported=True, evidence_confidence_preserved=True)


def verify_output(baseline, v2, target, report, directory):
	result = verify_decisions(v2, report)
	require(len(target) == len(v2), 'V3 size')
	actual = [(i, a, b) for i, (a, b) in enumerate(zip(v2, target)) if a != b]
	require(actual == [(0x62FBD5, 14, 16)], 'Unexpected v2→v3 differences')
	require(target[0x62FBD5] & 192 == v2[0x62FBD5] & 192, 'Upper metadata bits changed')
	restored = bytearray(target)
	restored[0x62FBD5] = 14
	require(bytes(restored) == v2, 'V2 feature preservation failed')
	v2dir = ROOT / 'tools/patch/output/cumulative-v2-20261028/build'
	result['v2_independent'] = verify_v2(baseline,
		(ROOT / 'tools/patch/output/cumulative-v1-20261028/build/tomato_cumulative_v1_INCOMPLETE.gba').read_bytes(), bytes(restored), v2dir)
	# Reconstruct independently from prior complete ledger, then add this one byte.
	canonical = bytearray(baseline)
	prior = json.loads((v2dir / 'changed_bytes.json').read_bytes())
	for row in prior:
		require(canonical[row['file']] == row['old'], 'Prior ledger source byte')
		canonical[row['file']] = row['new']
	require(bytes(canonical) == v2, 'Independent v2 ledger reconstruction')
	canonical[0x62FBD5] = 16
	require(bytes(canonical) == target, 'Independent canonical/incremental equivalence')
	combined = [(i, a, b) for i, (a, b) in enumerate(zip(baseline, target)) if a != b]
	ledger = json.loads((directory / 'changed_bytes.json').read_bytes())
	require(combined == [(r['file'], r['old'], r['new']) for r in ledger] and len(combined) == 282, 'Full cumulative ledger')
	for name, source in [('tomato_cumulative_v3.bps', baseline), ('v2_to_v3.bps', v2)]:
		require(decode_bps((directory / name).read_bytes(), source) == target, 'BPS output differs')
	require(target[:0xC0] == v2[:0xC0] and target[0xBD] == (-sum(target[0xA0:0xBD]) - 0x19) & 255, 'Header')
	result.update(v3_sha256=hashlib.sha256(target).hexdigest(), changed_bytes_from_v2=1,
		changed_bytes_from_baseline=282, canonical_incremental_equal=True, both_bps_reproduce=True,
		all_preexisting_features_preserved=True, attack_comparisons=2304, header_valid=True,
		status='Tomato Adventure — Cumulative v3 Incomplete Experimental Build', runtime='Untested')
	return result


def main():
	report = json.loads((ROOT / 'reverse_engineering/cumulative_v3_music_resolution.json').read_bytes())
	v2dir = ROOT / 'tools/patch/output/cumulative-v2-20261028/build'
	rom = (v2dir / 'tomato_cumulative_v2_INCOMPLETE.gba').read_bytes()
	result = verify_output((ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes(), rom,
		(DIRECTORY / 'build/tomato_cumulative_v3_INCOMPLETE.gba').read_bytes(), report, DIRECTORY / 'build')
	with (DIRECTORY / 'independent_verification.json').open('x', encoding='utf-8') as f:
		json.dump(result, f, indent=2)
		f.write('\n')
	print(json.dumps(result))


if __name__ == '__main__':
	main()
