"""Offline cumulative guards, independent rejection, and conditional battle math."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
	spec = importlib.util.spec_from_file_location(name, ROOT / file)
	obj = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(obj)
	return obj


builder = module('cumulative_builder', 'tools/patch/cumulative_v1.py')
verifier = module('cumulative_verifier', 'tools/analyze/verify_cumulative_v1.py')
DIRECTORY = ROOT / 'tools/patch/output/cumulative-v1-20261028/build'


class CumulativeTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.source = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.ops = builder.operations(cls.source)
		cls.target = builder.apply(cls.source, cls.ops)

	def test_real_output_independent_verification(self):
		self.assertEqual(self.target, (DIRECTORY / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes())
		result, rows = verifier.verify(self.source, self.target, DIRECTORY)
		self.assertEqual(result['attack_cases'], 2304)
		self.assertEqual(len(rows), 414)

	def test_wrong_inputs_and_overlap_rejected(self):
		for data in (self.target, self.source[:-1], b'\0' + self.source[1:]):
			with self.assertRaises(ValueError):
				builder.operations(data)
		with self.assertRaises(ValueError):
			builder.apply(self.source, self.ops + [self.ops[0]])
		with self.assertRaises(ValueError):
			builder.apply(self.source, [dict(offset=len(self.source), old='00', new='01')])

	def test_independent_rejects_unlisted_change_and_missing_feature(self):
		bad = bytearray(self.target)
		bad[0x100] ^= 1
		with self.assertRaises(ValueError):
			verifier.verify(self.source, bad, DIRECTORY)
		for address in (0x111E48, 0x638056, 0xFC7A9, 0x62D731, 0x107F54):
			bad = bytearray(self.target)
			bad[address] = self.source[address]
			with self.assertRaises(ValueError):
				verifier.verify(self.source, bad, DIRECTORY)

	def test_bps_crc_and_reconstruction(self):
		patch = builder.bps(self.source, self.target)
		self.assertEqual(verifier.decode_bps(patch, self.source), self.target)
		bad = bytearray(patch)
		bad[8] ^= 1
		with self.assertRaises(ValueError):
			verifier.decode_bps(bad, self.source)

	def test_conditional_battle_path_matched_inputs(self):
		# B1 from retained trace 080485B0. Both records have bit7 clear;
		# unknown action-input provenance is deliberately outside this model.
		bases = [0x62C250 + (i - 1) * 88 for i in (27, 41)]
		for a in bases:
			self.assertEqual(self.source[a + 39] & 128, 0)
		def damage(data, record, upgrade, slot, scaled, subtraction, suppressed):
			h = data[record + 34] + upgrade
			if scaled:
				h = h * data[record + 40 + slot * 2] // 100
			h = (h - subtraction) & 65535
			if h >= 32768 or h == 0:
				h = 1
			return 0 if suppressed else h
		for upgrade in range(46):
			for slot in range(9):
				for scaled in (False, True):
					for subtraction in (1, 25, 54, 100, 999):
						for suppressed in (False, True):
							for a, b in (bases, bases[::-1]):
								self.assertEqual(damage(self.target, a, upgrade, slot, scaled, subtraction, suppressed),
									damage(self.source, b, upgrade, slot, scaled, subtraction, suppressed))


if __name__ == '__main__':
	unittest.main()
