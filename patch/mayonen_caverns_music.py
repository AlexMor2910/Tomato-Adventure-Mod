"""One-map music experiment; run with python -B tools/patch/mayonen_caverns_music.py.

Map records: file 0x62D3E4 + map ID * 0x1C; music is byte +5's low
six bits (loader 0x0803F824). User verified map 0x001E and selectors
0x0D (Pokypine Forest) / 0x07 (Mayonen). No event or other map edits.
"""
import hashlib
import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "Tomato Adventure (Japan) (patched).gba"
SOURCE_SHA256 = "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde"
MAP_ID = 0x001E
RECORD_OFFSET = 0x62D3E4 + MAP_ID * 0x1C
OFFSET = RECORD_OFFSET + 5
EXPECTED_RECORD = bytes.fromhex(
	"1E 00 52 0F 1B 0D 06 0C 00 00 00 00 28 AC 13 08 "
	"E4 9B 15 08 EC 1A 14 08 48 E3 13 08"
)


def digest(data):
	return hashlib.sha256(data).hexdigest()


def verify(source, output):
	if len(output) != len(source):
		raise ValueError("ROM size changed")
	differences = [i for i, (a, b) in enumerate(zip(source, output)) if a != b]
	if differences != [OFFSET] or source[OFFSET] != 0x0D or output[OFFSET] != 0x07:
		raise ValueError("Expected exactly one change: 0x0062D731, 0D -> 07")
	if (source[OFFSET] & 0xC0) != (output[OFFSET] & 0xC0):
		raise ValueError("Packed map flags changed")


def main():
	source = BASELINE.read_bytes()
	if len(source) != 0x800000 or digest(source) != SOURCE_SHA256:
		raise ValueError("Input is not the verified English baseline")
	if source[RECORD_OFFSET:RECORD_OFFSET + 0x1C] != EXPECTED_RECORD:
		raise ValueError("Original map record does not match")
	if OFFSET != 0x62D731 or source[OFFSET] != 0x0D:
		raise ValueError("Original music offset/byte does not match")
	output = bytearray(source)
	output[OFFSET] = 0x07
	verify(source, output)
	outdir = Path(__file__).resolve().parent / "output" / ("mayonen-caverns-map001e-" + uuid.uuid4().hex)
	outdir.mkdir(parents=True, exist_ok=False)
	outrom = outdir / "mayonen_caverns_map001e.gba"
	with outrom.open("xb") as handle:
		handle.write(output)
	readback = outrom.read_bytes()
	verify(source, readback)
	if digest(BASELINE.read_bytes()) != SOURCE_SHA256:
		raise ValueError("Baseline changed during patching")
	manifest = {
		"experiment": "Mayonen Caverns music, map 0x001E only",
		"input": str(BASELINE), "input_sha256": SOURCE_SHA256,
		"output": str(outrom), "output_sha256": digest(readback),
		"size_bytes": len(readback), "map_id": "0x001E",
		"map_record_file_offset": "0x0062D72C",
		"modified_file_offset": "0x0062D731", "modified_rom_address": "0x0862D731",
		"original_byte": "0D", "replacement_byte": "07",
		"changed_byte_count": 1, "full_comparison_and_readback_passed": True,
		"baseline_hash_unchanged": True, "runtime_tested": False,
	}
	with (outdir / "manifest.json").open("x", encoding="utf-8", newline="\n") as handle:
		json.dump(manifest, handle, indent=2)
		handle.write("\n")
	print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
	main()
