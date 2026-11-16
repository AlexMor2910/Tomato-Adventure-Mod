"""Synthetic validation tests; no copyrighted ROM required."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/patch"))
import gimmick_balance as gb

HEADER = ",".join(gb.COLUMNS) + "\n"


class BalanceTests(unittest.TestCase):
    def rows(self, body="1,Gear-Yo,base_attack,21,22\n"):
        return (HEADER + body).encode()

    def source(self):
        data = bytearray(gb.TABLE + 50 * gb.STRIDE)
        for gid in range(1, 51):
            data[gb.TABLE + (gid - 1) * gb.STRIDE + 0x22] = 21
        return bytes(data)

    def test_all_50_ids_and_offsets(self):
        body = "".join(f"{i},{name},base_attack,21,22\n" for i, name in enumerate(gb.NAMES, 1))
        entries = gb.parse_csv(self.rows(body))
        source = self.source()
        output = gb.apply_entries(source, entries)
        self.assertEqual(len(gb.verify_differences(source, output, entries)), 50)
        self.assertEqual(entries[0]["file_offset"], 0x62C272)
        self.assertEqual(entries[-1]["file_offset"], 0x62D34A)

    def test_invalid_rows(self):
        for row in ["0,Gear-Yo,base_attack,21,22", "51,Gear-Yo,base_attack,21,22",
                    "1,Kendama,base_attack,21,22", "1,Gear-Yo,difficulty,21,22",
                    "1,Gear-Yo,base_attack,-1,22", "1,Gear-Yo,base_attack,21,256",
                    "1,Gear-Yo,base_attack,21,21", "1,Gear-Yo,base_attack,1.5,22",
                    "1,Gear-Yo,base_attack,21", "1,Gear-Yo,base_attack,21,22,extra"]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                gb.parse_csv(self.rows(row + "\n"))

    def test_duplicate_and_conflicting_rows(self):
        for new in (22, 23):
            with self.assertRaises(ValueError):
                gb.parse_csv(self.rows(f"1,Gear-Yo,base_attack,21,22\n1,Gear-Yo,base_attack,21,{new}\n"))

    def test_empty_and_bad_header(self):
        for data in (HEADER.encode(), b"", b"id,name\n1,Gear-Yo\n"):
            with self.assertRaises(ValueError):
                gb.parse_csv(data)

    def test_expected_byte_and_truncation(self):
        entries = gb.parse_csv(self.rows())
        for source in (b"", bytes(len(self.source()))):
            with self.assertRaises(ValueError):
                gb.apply_entries(source, entries)

    def test_exact_difference_and_size_checks(self):
        entries = gb.parse_csv(self.rows())
        source = self.source()
        output = bytearray(gb.apply_entries(source, entries))
        output[0] = 1
        with self.assertRaises(ValueError):
            gb.verify_differences(source, output, entries)
        with self.assertRaises(ValueError):
            gb.verify_differences(source, source[:-1], entries)

    def test_production_fingerprint_rejects_synthetic(self):
        with self.assertRaises(ValueError):
            gb.plan(self.source(), self.rows())

    def test_deterministic_plan_and_output_collision(self):
        source = self.source()
        # Override profile constants only inside this synthetic unit test.
        with patch.object(gb, "ROM_SIZE", len(source)), patch.object(gb, "SOURCE_SHA256", gb.digest(source)):
            output, manifest = gb.plan(source, self.rows())
            self.assertEqual((output, manifest), gb.plan(source, self.rows()))
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / "new"
            gb.write_outputs(source, output, manifest, directory)
            original = (directory / "manifest.json").read_bytes()
            with self.assertRaises(FileExistsError):
                gb.write_outputs(source, output, manifest, directory)
            self.assertEqual((directory / "manifest.json").read_bytes(), original)

    def test_dry_run_creates_no_outputs(self):
        source = self.source()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "input.bin").write_bytes(source)
            (root / "plan.csv").write_bytes(self.rows())
            with patch.object(gb, "ROM_SIZE", len(source)), patch.object(gb, "SOURCE_SHA256", gb.digest(source)), patch.object(gb, "OUTPUT_ROOT", root / "out"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gb.main(["--rom", str(root / "input.bin"), "--csv", str(root / "plan.csv"), "--dry-run"]), 0)
            self.assertFalse((root / "out").exists())

    def test_row_order_does_not_change_rom(self):
        rows = ["1,Gear-Yo,base_attack,21,22\n", "50,Shadowreel,base_attack,21,22\n"]
        source = self.source()
        self.assertEqual(gb.apply_entries(source, gb.parse_csv(self.rows("".join(rows)))),
                         gb.apply_entries(source, gb.parse_csv(self.rows("".join(reversed(rows))))))


if __name__ == "__main__":
    unittest.main()
