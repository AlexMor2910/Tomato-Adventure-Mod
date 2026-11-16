"""Isolated Hanzo first-reward experiment; never overwrites an existing output.

Run from any directory: python -B tools/patch/hanzo_dojo_pup.py
Dojo Pup: ta_menus_eng.txt row 28 under RESTRUCT 62C250, name at
English file 0x7F0A1E. asm/gimmick_text.asm uses one-based loader IDs.
Hanzo's FD0B selector 1C operand feeds shared FD15 1C00 / FE54 grant.
Only file 0x10D69B changes; recipient bits 6..7 remain zero (DeMille).
"""
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "Tomato Adventure (Japan) (patched).gba"
BASELINE_SHA256 = "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde"
COMMAND_OFFSET = 0x10D698
OPERAND_OFFSET = 0x10D69B
EXPECTED_COMMAND = bytes.fromhex("FD 0B 1C 1B 00")
DOJO_PUP_ID = 0x29


def sha256(data):
	return hashlib.sha256(data).hexdigest()


def verify_output(source, output):
	if len(output) != len(source):
		raise ValueError("Output size changed")
	differences = [i for i, (old, new) in enumerate(zip(source, output)) if old != new]
	if differences != [OPERAND_OFFSET] or output[OPERAND_OFFSET] != DOJO_PUP_ID:
		raise ValueError("Output does not contain exactly the intended one-byte change")
	return differences


def main():
	source = BASELINE.read_bytes()
	if len(source) != 0x800000 or sha256(source) != BASELINE_SHA256:
		raise ValueError("Input is not the protected English baseline")
	if source[COMMAND_OFFSET:COMMAND_OFFSET + 5] != EXPECTED_COMMAND:
		raise ValueError("Unexpected original Hanzo command")
	# Confirm documented index 0x28's translated name bytes in this baseline.
	if source[0x7F0A1E:0x7F0A2E] != bytes.fromhex("04 8F 8A 8F 00 10 95 90 00 00 00 00 00 00 00 00"):
		raise ValueError("Dojo Pup table-name verification failed")
	if (source[OPERAND_OFFSET] & 0xC0) != (DOJO_PUP_ID & 0xC0):
		raise ValueError("Recipient bits would change")
	patched = bytearray(source)
	patched[OPERAND_OFFSET] = DOJO_PUP_ID
	verify_output(source, patched)
	outdir = Path(__file__).resolve().parent / "output" / ("hanzo-dojo-pup-" + uuid.uuid4().hex)
	outdir.mkdir(parents=True, exist_ok=False)
	outrom = outdir / "hanzo_dojo_pup.gba"
	with outrom.open("xb") as handle:
		handle.write(patched)
	readback = outrom.read_bytes()
	differences = verify_output(source, readback)
	if sha256(BASELINE.read_bytes()) != BASELINE_SHA256:
		raise ValueError("Baseline changed during patching")
	manifest = {
		"experiment": "Hanzo Lab 1 first reward: Erupter to Dojo Pup",
		"source": str(BASELINE), "source_sha256": BASELINE_SHA256,
		"output": str(outrom), "output_sha256": sha256(readback),
		"size_bytes": len(readback), "gimmick_id": DOJO_PUP_ID,
		"gimmick_table_index": 0x28, "recipient_bits": 0,
		"command_file_offset": "0x0010D698",
		"original_command": EXPECTED_COMMAND.hex(" "),
		"patched_command": readback[COMMAND_OFFSET:COMMAND_OFFSET + 5].hex(" "),
		"changed_file_offsets": [f"0x{i:08X}" for i in differences],
		"changed_rom_address": "0x0810D69B",
		"original_operand": "1b 00", "new_operand": "29 00",
		"verification": "Full byte comparison and output readback passed; baseline hash unchanged",
		"runtime_tested": False,
	}
	with (outdir / "manifest.json").open("x", encoding="utf-8", newline="\n") as handle:
		json.dump(manifest, handle, indent=2)
		handle.write("\n")
	print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
	main()
