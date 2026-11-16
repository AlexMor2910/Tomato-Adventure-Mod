"""Offline rejection checks; never writes a ROM or executes an emulator."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/patch/alessa_recruitment_wrapper.py"
spec = importlib.util.spec_from_file_location("alessa_patch", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class WrapperVerificationTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.source = mod.BASELINE.read_bytes()
		cls.output = mod.build(cls.source)

	def test_approved_rom_layout(self):
		result = mod.verify_output(self.source, self.output)
		self.assertEqual(result["prefix_actual_changed_bytes"], 3)
		self.assertEqual(result["payload_bytes"], 21)
		self.assertEqual(result["ff_padding_bytes"], 8388587)

	def test_reject_changed_baseline(self):
		source = bytearray(self.source)
		source[0] ^= 1
		with self.assertRaises(ValueError):
			mod.build(source)

	def test_reject_prefix_payload_padding_and_length_corruption(self):
		for offset in (0xC0, mod.CALL_OFFSET, mod.POINTER_OFFSET,
			mod.PAYLOAD_OFFSET, mod.PAYLOAD_OFFSET + len(mod.PAYLOAD), mod.OUTPUT_SIZE - 1):
			with self.subTest(offset=hex(offset)):
				output = bytearray(self.output)
				output[offset] ^= 1
				with self.assertRaises(ValueError):
					mod.verify_output(self.source, output)
		with self.assertRaises(ValueError):
			mod.verify_output(self.source, self.output[:-1])

	def test_existing_destination_and_path_escape_rejected(self):
		with tempfile.TemporaryDirectory() as temp:
			fake_script = Path(temp) / "patch" / "tool.py"
			with patch.object(mod, "__file__", str(fake_script)):
				outdir = mod.fresh_directory("existing")
				marker = outdir / "sentinel.txt"
				marker.write_text("preserve", encoding="utf-8")
				with self.assertRaises(FileExistsError):
					mod.fresh_directory("existing")
				self.assertEqual(marker.read_text(encoding="utf-8"), "preserve")
				for name in ("../escape", "C:\\escape", "a/b", ""):
					with self.assertRaises(ValueError):
						mod.fresh_directory(name)


if __name__ == "__main__":
	unittest.main()
