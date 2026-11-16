"""Build the isolated, single-use Sofoubi interpreter initialization experiment.

python -B tools/patch/sofoubi_initialization_wrapper.py
No emulator, checkpoint transformation, RAM edits, or story-flag changes.
The user must use the temporary Hawker carrier once only; it has no replay guard.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import uuid

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba"
SOURCE_SHA256 = "d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3"
SIZE = 0x01000000
# Original wrapper: FD01/FD02 context, FD2F exchange call, FD7D termination.
# FD2F saves 08102D35; payload FD7C returns there without a nested script call.
POINTER_OFFSET = 0x00102D31
PAYLOAD_OFFSET = 0x00800020
OPERATIONS = (
	(POINTER_OFFSET, bytes.fromhex("81 7E 10 08"), bytes.fromhex("20 00 80 08")),
	(PAYLOAD_OFFSET, b"\xff" * 7, bytes.fromhex("FE 49 FE 53 95 FD 7C")),
)
WRAPPER = bytes.fromhex("FE49 FE536B FD0B1A8300 FD0B1C1B00 FD30334B1208")


def sha(data):
	return hashlib.sha256(data).hexdigest()


def require(condition, message):
	if not condition:
		raise ValueError(message)


def snapshot():
	# Also protect retained manifests and patch implementations, beyond ROM/state files.
	return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in ROOT.rglob("*")
		if p.is_file() and (p.suffix.lower() in (".gba", ".sav")
		or re.fullmatch(r"\.ss\d.*", p.suffix.lower())
		or p.name == "manifest.json"
		or (p.parent == ROOT / "tools/patch" and p.suffix == ".py"))}


def validate_source(source):
	require(len(source) == SIZE and sha(source) == SOURCE_SHA256, "Unexpected source identity")
	require(source[0x102D27:0x102D37] == bytes.fromhex("FD01 8600 FD02 8700 FD2F 817E1008 FD7D"),
		"Original Hawker carrier differs")
	require(source[0x800000:0x800015] == WRAPPER, "Existing Alessa payload differs")
	# Existing builder owns this appended region: 21-byte payload, then FF padding.
	# Reserve the first 0x20 bytes for that wrapper; do not use unproven original-ROM free space.
	require(source[0x800015:] == b"\xff" * (SIZE - 0x800015), "Generated extension padding differs")
	for offset, old, new in OPERATIONS:
		require(len(old) == len(new) and source[offset:offset + len(old)] == old,
			"Original operation bytes differ")


def verify(source, output):
	validate_source(source)
	require(len(output) == len(source), "ROM size changed")
	expected = {offset + i: (a, b) for offset, old, new in OPERATIONS
		for i, (a, b) in enumerate(zip(old, new)) if a != b}
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(source, output)) if a != b}
	require(actual == expected, "Full-file comparison found unauthorized differences")
	for offset, old, new in OPERATIONS:
		require(output[offset:offset + len(new)] == new, "Output operation differs")
	require(output[:0xC0] == source[:0xC0], "Header changed")
	require(output[0x107E81:0x1081DA] == source[0x107E81:0x1081DA], "Exchange logic changed")
	require(output[0x65FC48:0x65FD15] == source[0x65FC48:0x65FD15], "Rate-two advice changed")
	require(output[0x10D69D:0x10D6A3] == source[0x10D69D:0x10D6A3]
		and output[0x800000:0x800020] == source[0x800000:0x800020], "Alessa wrapper changed")
	return {
		"compared_bytes": len(source), "actual_changed_bytes": len(actual),
		"full_file_comparison_passed": True, "header_preserved": True,
		"exchange_script_preserved": True, "rate_two_advice_preserved": True,
		"alessa_wrapper_preserved": True,
		"differences": [{"file_offset": f"0x{i:08X}", "bus_address": f"0x{i + 0x08000000:08X}",
			"old": f"{a:02X}", "new": f"{b:02X}"} for i, (a, b) in actual.items()],
	}


def write_json(path, value):
	with path.open("x", encoding="utf-8", newline="\n") as handle:
		json.dump(value, handle, indent=2)
		handle.write("\n")
	require(json.loads(path.read_text(encoding="utf-8")) == value, "JSON readback differs")


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--output-name", default="sofoubi-initialization-" + uuid.uuid4().hex)
	args = parser.parse_args()
	require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", args.output_name) is not None,
		"Output name must be a simple new directory name")
	source = SOURCE.read_bytes()
	validate_source(source)
	before = snapshot()
	output = bytearray(source)
	for offset, old, new in OPERATIONS:
		output[offset:offset + len(new)] = new
	checks = verify(source, output)
	outdir = ROOT / "tools/patch/output" / args.output_name
	outdir.mkdir(exist_ok=False)
	outrom = outdir / "sofoubi_initialization_wrapper.gba"
	with outrom.open("xb") as handle:
		require(handle.write(output) == SIZE, "Short ROM write")
	readback = outrom.read_bytes()
	require(readback == output and verify(source, readback) == checks, "ROM readback differs")
	diffpath = outdir / "byte_differences.json"
	write_json(diffpath, checks)
	after = snapshot()
	require(after.pop(str(outrom.relative_to(ROOT)), None) == sha(readback), "Output inventory mismatch")
	require(before == after, "Protected artifact inventory/hashes changed")
	manifest = {
		"schema_version": 1, "experiment": "Single-use Sofoubi initialization through Hawker FD2F carrier",
		"script_sha256": sha(Path(__file__).read_bytes()),
		"source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(source), "source_size": len(source),
		"output": str(outrom.relative_to(ROOT)), "output_sha256": sha(readback), "output_size": len(readback),
		"operations": [{"file_start": f"0x{offset:08X}", "file_end_exclusive": f"0x{offset + len(old):08X}",
			"bus_start": f"0x{offset + 0x08000000:08X}", "old": old.hex(" ").upper(),
			"new": new.hex(" ").upper()} for offset, old, new in OPERATIONS],
		"allocation_evidence": "Fingerprint-gated existing 16 MiB generated extension; original wrapper reservation [00800000,00800020) preserved; remaining padding verified FF",
		"verification": checks, "difference_report_sha256": sha(diffpath.read_bytes()),
		"protected_artifact_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "runtime_tested": False,
		"limitations": ["No replay guard: use carrier once only", "Requires membership 31 and absent Sofoubi/Relleck",
			"Checkpoint reload with unchanged exchange ROM requires separate validation",
			"Does not reproduce recruitment story scene; no story flags modified"],
	}
	manifestpath = outdir / "manifest.json"
	write_json(manifestpath, manifest)
	final = snapshot()
	final.pop(str(outrom.relative_to(ROOT)), None)
	final.pop(str(manifestpath.relative_to(ROOT)), None)
	require(final == before, "Protected artifacts changed during final manifest verification")
	print(json.dumps({"output": str(outrom), "manifest": str(manifestpath), "byte_differences": str(diffpath),
		"source_sha256": sha(source), "output_sha256": sha(readback),
		"actual_changed_bytes": checks["actual_changed_bytes"], "protected_artifact_count": len(before),
		"protected_unchanged": True, "runtime_tested": False}, indent=2))


if __name__ == "__main__":
	main()
