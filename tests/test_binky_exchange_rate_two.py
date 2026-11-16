"""Offline rate/capacity and patch safety checks; no emulator or ROM output."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rate_patch", ROOT / "tools/patch/binky_exchange_rate_two.py")
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)
from binky_exchange_rate import BLOCKS, block_bytes, ADVICE_START, ADVICE_END


class RatePatchTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.source = patch.BASELINE.read_bytes()
		cls.output = patch.build(cls.source, "baseline")

	def test_every_reward_and_capacity_boundary(self):
		for start, old_quantity, character in BLOCKS:
			self.assertEqual(self.output[start:start + 0x37], block_bytes(2, character))
			quantity = self.output[start + 0x24]
			threshold = int.from_bytes(self.output[start + 0x19:start + 0x1B], "little")
			for count in range(100):
				if count < threshold:  # FD1F + FD45 allow only count below threshold.
					self.assertEqual(quantity, 2)
					self.assertLessEqual(count + quantity, 99)
				else:
					self.assertGreaterEqual(count, 98)

	def test_rejects_modified_input_and_unintended_output(self):
		with self.assertRaises(ValueError):
			patch.build(self.output, "baseline")
		for offset in (0, 0x107E90, 0x107F84, 0x108176, len(self.output) - 1):
			bad = bytearray(self.output)
			bad[offset] ^= 1
			with self.assertRaises(ValueError):
				patch.verify_output(self.source, bad, "baseline")

	def test_dialogue_does_not_overlap_following_string(self):
		self.assertEqual(self.output[ADVICE_END:ADVICE_END + 32], self.source[ADVICE_END:ADVICE_END + 32])
		self.assertIn(bytes.fromhex("FF 40 FF 00"), self.output[ADVICE_START:ADVICE_END])

	def test_test_derivative_preserves_wrapper(self):
		source = patch.RECRUITMENT.read_bytes()
		output = patch.build(source, "recruitment-test")
		self.assertEqual(output[0x800000:], source[0x800000:])
		self.assertEqual(output[0x10D69D:0x10D6A3], source[0x10D69D:0x10D6A3])

	def test_collision_and_unsafe_names(self):
		with tempfile.TemporaryDirectory() as temp:
			original_file = patch.__file__
			try:
				patch.__file__ = str(Path(temp) / "patch.py")
				out = patch.fresh_directory("collision")
				(out / "sentinel.txt").write_text("preserve")
				with self.assertRaises(FileExistsError):
					patch.fresh_directory("collision")
				self.assertEqual((out / "sentinel.txt").read_text(), "preserve")
				for name in ("../escape", "C:/outside", "bad/name"):
					with self.assertRaises(ValueError):
						patch.fresh_directory(name)
			finally:
				patch.__file__ = original_file


if __name__ == "__main__":
	unittest.main()
