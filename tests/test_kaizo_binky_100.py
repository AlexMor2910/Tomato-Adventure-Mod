"""Offline tests only; no emulator, protected-file writes or test ROM outputs."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kaizo_patch", ROOT / "tools/patch/kaizo_binky_100.py")
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class KaizoPatchTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.source = patch.SOURCE.read_bytes()
		cls.plan = json.loads(patch.PLAN.read_bytes())
		cls.output = patch.build(cls.source, cls.plan)

	def test_exact_independent_byte_ledger_and_preservation(self):
		actual = [(i, a, b) for i, (a, b) in enumerate(zip(self.source, self.output)) if a != b]
		expected = sorted((int(x["file"], 16), int(x["old"], 16), int(x["new"], 16))
			for x in self.plan["expected_actual_byte_differences"])
		self.assertEqual(actual, expected)
		self.assertEqual(len(actual), 51)
		self.assertEqual(len(self.output), 0x1000000)
		for a, b in ((0, 0xC0), (0x800000, len(self.source)), (0x107E81, 0x1081DA),
			(0x65FC48, 0x65FD15), (0x252F4, 0x2536C), (0x62B9D8, 0x62B9DC)):
			self.assertEqual(self.source[a:b], self.output[a:b])

	def test_all_display_compare_boundaries(self):
		for row in self.plan["thresholds"]:
			a, b = int(row["display_file"], 16), int(row["compare_file"], 16)
			display = struct.unpack_from("<H", self.output, a)[0]
			compare = struct.unpack_from("<H", self.output, b)[0]
			self.assertEqual(display, row["new"])
			self.assertEqual(compare, display)
			for total, eligible in ((compare - 1, False), (compare, True), (compare + 1, True)):
				self.assertEqual(total >= compare, eligible)
		self.assertEqual(patch.NEW[-1], 100)
		self.assertLess(99, patch.NEW[-1])

	def test_cap_and_whole_stack_arithmetic_exhaustive(self):
		self.assertEqual(struct.unpack_from("<H", self.output, 0xFC7A9)[0], 100)
		self.assertEqual(self.output[0xFCCD8], 100)
		self.assertEqual(self.output[0xFC79F:0xFC7A7], bytes.fromhex("FE 56 37 FF A7 C7 0F 08"))
		for total in range(181):
			for stock in range(100):
				self.assertEqual(patch.donation_model(total, stock), (min(total + stock, 100), 0))
		self.assertEqual(patch.donation_model(99, 5), (100, 0))
		self.assertEqual(patch.donation_model(100, 5), (100, 0))
		self.assertEqual(patch.donation_model(180, 99), (100, 0))
		self.assertEqual(patch.donation_model(180, 5, completed=True), (180, 5))

	def test_dialogue_changes_one_digit_only(self):
		a, b = 0x64FDF3, 0x64FE34
		changes = [(i + a, x, y) for i, (x, y) in enumerate(zip(self.source[a:b], self.output[a:b])) if x != y]
		self.assertEqual(changes, [(0x64FE13, 0x78, 0x70)])
		self.assertEqual(self.output[0xFCD26:0xFCD2A], bytes.fromhex("F3 FD 64 08"))
		self.assertEqual(self.source[b:b + 32], self.output[b:b + 32])

	def test_rejects_wrong_source_size_hash_and_already_patched(self):
		for data in (self.source[:-1], self.output, bytes([self.source[0] ^ 1]) + self.source[1:]):
			with self.assertRaises(ValueError):
				patch.preflight(data, self.plan)

	def test_rejects_wrong_original_context_reward_claim_and_gate(self):
		# Direct context checks supplement the mandatory whole-file hash gate.
		for offset in (0xFC7C7, 0xFC7E7, 0xFC7F1, 0xFC843, 0xFC79F, 0xFCD26):
			bad = bytearray(self.source)
			bad[offset] ^= 1
			with self.assertRaises((ValueError, KeyError)):
				patch.validate_context(bad)

	def test_rejects_plan_substitutions(self):
		for field, value in (("new", 3), ("packed_reward", "0x61"), ("claim_flag", "0x196"),
			("display_file", "0x000FC7D1"), ("prerequisite_flags", ["0x001"])):
			bad = copy.deepcopy(self.plan)
			bad["thresholds"][0][field] = value
			with self.assertRaises(ValueError):
				patch.validate_plan(bad)
		bad = copy.deepcopy(self.plan)
		bad["operations"][0]["new"] = "03 00"
		with self.assertRaises(ValueError):
			patch.validate_plan(bad)

	def test_rejects_overlapping_operations(self):
		with self.assertRaises(ValueError):
			patch.expected_changes(((10, b"\x01\x00", b"\x02\x00"), (11, b"\x00", b"\x01")))

	def test_rejects_unintended_output_changes(self):
		for offset in (0, 0xFC7EF, 0xFC79F, 0x108165, 0x800000, len(self.output) - 1):
			bad = bytearray(self.output)
			bad[offset] ^= 1
			with self.assertRaises(ValueError):
				patch.verify_output(self.source, bad, self.plan)

	def test_multiple_reward_crossings_claim_skips_and_gate_resumption_model(self):
		def eligible(total, claimed, gates):
			awarded = []
			for i, threshold in enumerate(patch.NEW):
				if i in claimed:
					continue
				if total < threshold or (i in patch.GATES and patch.GATES[i] not in gates):
					break
				awarded.append(i)
			return awarded
		gates = set(patch.GATES.values())
		self.assertEqual(eligible(7, set(), gates), [0, 1, 2, 3])
		self.assertEqual(eligible(7, {0, 1}, gates), [2, 3])
		self.assertEqual(eligible(100, set(), set()), [0, 1])
		self.assertEqual(eligible(100, {0, 1}, gates), list(range(2, 24)))
		self.assertEqual(eligible(100, set(range(24)), gates), [])

	def test_output_directory_collision_and_traversal(self):
		with tempfile.TemporaryDirectory() as temp:
			original = patch.__file__
			try:
				patch.__file__ = str(Path(temp) / "patch.py")
				p = patch.fresh_directory("collision")
				(p / "sentinel.txt").write_text("preserve")
				with self.assertRaises(FileExistsError):
					patch.fresh_directory("collision")
				self.assertEqual((p / "sentinel.txt").read_text(), "preserve")
				for name in ("../escape", "C:/outside", "bad/name", ""):
					with self.assertRaises(ValueError):
						patch.fresh_directory(name)
			finally:
				patch.__file__ = original


if __name__ == "__main__":
	unittest.main()
