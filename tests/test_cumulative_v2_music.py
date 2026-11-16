"""Focused music safety and cumulative v2 regression tests; offline only."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools/analyze'), str(ROOT / 'tools/patch')]
import cumulative_v2 as builder
import verify_cumulative_v2 as verifier
from verify_cumulative_v1 import decode_bps

DIRECTORY = ROOT / 'tools/patch/output/cumulative-v2-20261028/build'


class MusicV2Tests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.baseline = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.prior = (builder.V1_DIR / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
		cls.target = (DIRECTORY / 'tomato_cumulative_v2_INCOMPLETE.gba').read_bytes()

	def test_canonical_incremental_and_independent_readback(self):
		output, ops, incremental = builder.build(self.baseline, self.prior)
		self.assertEqual(output, self.target)
		self.assertEqual(builder.v1.apply(self.prior, incremental), output)
		result = verifier.verify(self.baseline, self.prior, output, DIRECTORY)
		self.assertEqual(result['attack_comparisons'], 2304)
		self.assertEqual(result['confirmed_patched_rooms'], 87)

	def test_every_upper_bit_and_unrelated_map_byte_preserved(self):
		for mid in range(494):
			a = 0x62D3E4 + mid * 28
			self.assertEqual(self.prior[a + 5] & 192, self.target[a + 5] & 192)
			self.assertEqual(self.prior[a:a + 5], self.target[a:a + 5])
			self.assertEqual(self.prior[a + 6:a + 28], self.target[a + 6:a + 28])

	def test_reject_unapproved_map_adjacent_byte_and_metadata_changes(self):
		for a in (0x62D3E4 + 8 * 28 + 5, 0x62D3E4 + 30 * 28 + 6, 0x62D3E4 + 3 * 28 + 5):
			bad = bytearray(self.target)
			bad[a] ^= 0x80
			with self.assertRaises(ValueError):
				verifier.verify(self.baseline, self.prior, bad, DIRECTORY)

	def test_restore_required_and_special_cues_preserved(self):
		self.assertEqual(self.target[0x128F0A:0x128F0D], bytes.fromhex('FE A9 07'))
		for a in (0x128F0C, 0x128D7A, 0x128E7E, 0x117C23):
			bad = bytearray(self.target)
			bad[a] = 13 if a == 0x128F0C else 7
			with self.assertRaises(ValueError):
				verifier.verify(self.baseline, self.prior, bad, DIRECTORY)

	def test_guarded_input_overlap_and_expected_bytes(self):
		for baseline, prior in ((self.baseline, self.target), (self.baseline[:-1], self.prior)):
			with self.assertRaises(ValueError):
				builder.build(baseline, prior)
		plan = builder.load_plan()['operations']
		with self.assertRaises(ValueError):
			builder.v1.apply(self.baseline, plan + [plan[0]])
		with self.assertRaises(ValueError):
			builder.v1.apply(self.baseline, [dict(plan[0], old='ff')])

	def test_both_distribution_patches_reproduce_output(self):
		for name, source in [('tomato_cumulative_v2.bps', self.baseline), ('v1_to_v2.bps', self.prior)]:
			self.assertEqual(decode_bps((DIRECTORY / name).read_bytes(), source), self.target)

	def test_evidence_bounds_candidates_and_native_title_witness(self):
		evidence = json.loads((DIRECTORY.parent / 'music_evidence.json').read_bytes())
		self.assertTrue(all(not row['traversal']['budget_exhausted'] for row in evidence['maps']))
		for row in evidence['maps']:
			for dynamic in row['dynamic_commands']:
				raw = bytes.fromhex(dynamic['raw'])
				self.assertEqual(raw[:3], bytes.fromhex('FD 84 00'))
				self.assertIn(raw[3], (0x2D, 0x3B))
		for mid in (0x12C, 0x158, 0x16D):
			a = 0x62D3E4 + mid * 28
			self.assertEqual(self.prior[a:a + 28], self.target[a:a + 28])
		# 08033E16 LDRB record+2; 08033E18 LSR #2; +1 sentinel then store.
		self.assertEqual(self.baseline[0x33E16:0x33E1E], bytes.fromhex('80 78 80 08 01 30 08 70'))


if __name__ == '__main__':
	unittest.main()
