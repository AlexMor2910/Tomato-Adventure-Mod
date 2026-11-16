"""Approved Detector-only add-on; default read-only preflight, --apply fresh output.

Accepts only the preserved Kaizo gameplay ROM. Never overwrites inputs/outputs,
changes another enemy, or launches an emulator. Python standard library only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import uuid

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba"
SOURCE_SHA256 = "7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2"
SIZE = 0x1000000
OPERATIONS = ((0x638056, b"\x87\x00", b"\x78\x00", "hp"),
	(0x63805A, b"\x26\x00", b"\x19\x00", "base_mitigation"))


def sha(data):
	return hashlib.sha256(data).hexdigest()


def require(condition, message):
	if not condition:
		raise ValueError(message)


def header_valid(data):
	return data[0xBD] == (-sum(data[0xA0:0xBD]) - 0x19) & 255


def preflight(source):
	require(len(source) == SIZE and sha(source) == SOURCE_SHA256, "Wrong source ROM size/hash")
	require(header_valid(source), "Invalid source GBA header complement")
	for offset, old, _, field in OPERATIONS:
		require(source[offset:offset + 2] == old, "Original field mismatch: " + field)
	require(struct.unpack_from("<H", source, 0x637DAA)[0] == 262, "Dragon HP mismatch")
	require(struct.unpack_from("<H", source, 0x637DAE)[0] == 54, "Dragon mitigation mismatch")
	require(source[0x482CC:0x482DE] == bytes.fromhex("42 89 50 46 10 40 C8 81 18 68 42 89 50 46 10 40 08 82"), "HP loader context mismatch")
	require(source[0x482E4:0x482EA] == bytes.fromhex("18 68 C0 89 88 82"), "Mitigation loader context mismatch")
	evidence = json.loads((ROOT / "reverse_engineering/gimmick_palace_enemy_evidence.json").read_text(encoding="utf-8"))
	row = next(x for x in evidence["enemies_ranked_by_hp"] if x["enemy_id"] == 0xA5)
	require((row["name"], row["hp"], row["base_mitigation"], row["hp_field_bus"], row["mitigation_field_bus"]) ==
		("Detector", 135, 38, "0x08638056", "0x0863805A"), "Original research evidence mismatch")


def build(source):
	preflight(source)
	output = bytearray(source)
	for offset, old, new, _ in OPERATIONS:
		output[offset:offset + len(old)] = new
	verify(source, output)
	return bytes(output)


def verify(source, output):
	require(len(output) == SIZE, "Output size mismatch")
	differences = [(i, a, b) for i, (a, b) in enumerate(zip(source, output)) if a != b]
	require(differences == [(0x638056, 0x87, 0x78), (0x63805A, 0x26, 0x19)], "Unexpected full-file difference")
	require(header_valid(output) and source[:0xC0] == output[:0xC0], "Header changed or invalid")
	require(source[0x637DA0:0x637DEC] == output[0x637DA0:0x637DEC], "Dragon record changed")
	return differences


def protected():
	paths = list(ROOT.glob("*.gba")) + list(ROOT.glob("*.sav"))
	paths += list((ROOT / "savestates").glob("*"))
	for pattern in ("*.gba", "*.sav"):
		paths += list((ROOT / "tools/patch/output").rglob(pattern))
	return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in paths if p.is_file()}


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--apply", action="store_true")
	parser.add_argument("--output-name")
	args = parser.parse_args()
	if args.output_name:
		require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", args.output_name), "Unsafe output name")
	source = SOURCE.read_bytes()
	output = build(source)
	manifest = {"source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(source),
		"output_sha256": sha(output), "bytes": len(output), "enemy_id": "0xA5", "name": "Detector",
		"operations": [{"field": field, "file": f"0x{offset:08X}", "bus": f"0x{offset + 0x08000000:08X}",
			"before": old.hex(" "), "after": new.hex(" "), "old_value": int.from_bytes(old, "little"),
			"new_value": int.from_bytes(new, "little"), "encoding": "uint16 little-endian"}
			for offset, old, new, field in OPERATIONS],
		"actual_changed_bytes": len(verify(source, output)), "gba_header_complement": f"0x{output[0xBD]:02X}",
		"integrity_adjustment": "None: header complement remains valid; header unchanged; no extra writes",
		"dragon": {"hp": 262, "base_mitigation": 54, "entire_record_unchanged": True},
		"runtime_status": "UNTESTED", "builder_sha256": sha(Path(__file__).read_bytes())}
	if not args.apply:
		print(json.dumps({"mode": "read-only preflight", **manifest}, indent=2))
		return
	before = protected()
	directory = ROOT / "tools/patch/output" / (args.output_name or "detector-rebalance-" + uuid.uuid4().hex)
	directory.mkdir(parents=True, exist_ok=False)
	rom_path = directory / "detector_rebalance.gba"
	with rom_path.open("xb") as f:
		f.write(output)
	written = rom_path.read_bytes()
	verify(source, written)
	require(sha(written) == manifest["output_sha256"], "Written output hash mismatch")
	for name, digest in before.items():
		require(sha((ROOT / name).read_bytes()) == digest, "Protected artifact changed: " + name)
	manifest["output"] = str(rom_path.relative_to(ROOT))
	manifest["protected_artifacts_unchanged"] = len(before)
	manifest["protected_sha256"] = before
	with (directory / "manifest.json").open("x", encoding="utf-8") as f:
		json.dump(manifest, f, indent=2)
		f.write("\n")
	print(json.dumps({k: v for k, v in manifest.items() if k != "protected_sha256"}, indent=2))


if __name__ == "__main__":
	main()
