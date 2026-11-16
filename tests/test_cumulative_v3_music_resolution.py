"""Offline destination evidence and v3 patch regressions; no emulator/save access."""
import copy
import csv
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools/analyze'), str(ROOT / 'tools/patch')]
import cumulative_v3 as builder
import cumulative_v3_music_resolution as analysis
import verify_cumulative_v3_music_resolution as verifier

DIRECTORY = ROOT / 'tools/patch/output/cumulative-v3-20261028'


class ResolutionTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.baseline = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.v1 = (builder.previous.V1_DIR / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
		cls.v2 = (builder.V2_DIR / 'tomato_cumulative_v2_INCOMPLETE.gba').read_bytes()
		cls.target = (DIRECTORY / 'build/tomato_cumulative_v3_INCOMPLETE.gba').read_bytes()
		cls.report = json.loads((ROOT / 'reverse_engineering/cumulative_v3_music_resolution.json').read_bytes())

	def test_canonical_incremental_reproduction(self):
		output, ops = builder.build(self.baseline, self.v1, self.v2)
		self.assertEqual(output, self.target)
		self.assertEqual(builder.previous.v1.apply(self.v2, self.report['approved_operations']), output)

	def test_independent_full_output_and_existing_features(self):
		result = verifier.verify_output(self.baseline, self.v2, self.target, self.report, DIRECTORY / 'build')
		self.assertEqual(result['changed_bytes_from_v2'], 1)
		self.assertEqual(result['attack_comparisons'], 2304)
		self.assertTrue(result['all_preexisting_features_preserved'])

	def test_uncertain_room_cannot_be_promoted(self):
		for i in (0, 1):
			bad = copy.deepcopy(self.report)
			bad['maps'][i]['patch_decision'] = 'patch'
			bad['maps'][i]['confidence'] = 'Confirmed static'
			with self.assertRaises(ValueError):
				verifier.verify_decisions(self.v2, bad)
		for mid in (0x12C, 0x158):
			a = 0x62D3E4 + mid * 28
			self.assertEqual(self.target[a:a + 28], self.v2[a:a + 28])

	def test_saved_writer_immediates_are_return_ids_not_incoming_ids(self):
		for a in (0x10C600, 0x10C609):
			self.assertEqual(analysis.saved_destination(self.v2[a:a + 9]), 0x10B)
		with self.assertRaises(ValueError):
			analysis.saved_destination(bytes.fromhex('FD 75 10'))
		self.assertEqual(analysis.saved_destination(bytes.fromhex('FD 73 58 01 00 00 00 00 00')), 0x158)
		self.assertEqual(analysis.saved_destination(bytes.fromhex('FD 74 2C 01 00 00 00 00 00')), 0x12C)

	def test_original_catalog_and_actual_rom_agree_on_missed_edge(self):
		with (ROOT / 'tools/extract/extracted_data/map_transitions.csv').open() as f:
			rows = list(csv.DictReader(f))
		for src, dst, pos in [('0x016C', '0x016D', 0x13C61A), ('0x016D', '0x016C', 0x13C628)]:
			matches = [r for r in rows if r['source_map_id'] == src and r['destination_map_id'] == dst]
			self.assertEqual(len(matches), 1)
			self.assertEqual(int(matches[0]['record_address'], 16), pos + 0x08000000)
			self.assertEqual(int.from_bytes(self.v2[pos + 4:pos + 6], 'little'), int(dst, 16))
		self.assertEqual(analysis.ordinary_incoming(self.v2)[0x16D][0]['source_map'], 0x16C)

	def test_reject_unexpected_byte_change_and_wrong_input(self):
		for address in (0x62D3E4 + 0x158 * 28 + 5, 0x62FBD6, 0x128F0C, 0x10D69B):
			bad = bytearray(self.target)
			bad[address] ^= 1
			with self.assertRaises(ValueError):
				verifier.verify_output(self.baseline, self.v2, bad, self.report, DIRECTORY / 'build')
		with self.assertRaises(ValueError):
			builder.build(self.baseline, self.v1, self.target)

	def test_metadata_and_all_other_bytes_preserved(self):
		actual = [(i, a, b) for i, (a, b) in enumerate(zip(self.v2, self.target)) if a != b]
		self.assertEqual(actual, [(0x62FBD5, 14, 16)])
		self.assertEqual(self.v2[0x62FBD5] & 192, self.target[0x62FBD5] & 192)
		self.assertEqual(self.target[:0xC0], self.v2[:0xC0])


if __name__ == '__main__':
	unittest.main()
