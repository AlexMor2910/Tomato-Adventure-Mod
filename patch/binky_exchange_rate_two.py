"""Build a verified constant-two exchange experiment; never launch an emulator.

Default source: unmodified English baseline (standalone, 8 MiB).
--profile recruitment-test: separately hash-gated 16 MiB derivative for checkpoints.
"""
import argparse
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/analyze"))
from binky_exchange_rate import operations, verify_rates, sha, protected, RECRUITMENT

BASELINE = ROOT / "Tomato Adventure (Japan) (patched).gba"
PROFILES = {
	"baseline": (BASELINE, "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde", 0x800000),
	"recruitment-test": (RECRUITMENT, "3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6", 0x1000000),
}
EVIDENCE = ROOT / "reverse_engineering/experiments/binky_exchange_rate_two_evidence.json"


def require(condition, message):
	if not condition:
		raise ValueError(message)


def validate_source(source, profile):
	require(profile in PROFILES, "Unknown source profile")
	path, fingerprint, size = PROFILES[profile]
	require(len(source) == size and sha(source) == fingerprint, "Unexpected or previously patched input ROM")
	return operations(source)


def expected_changes(source, ops):
	result = {}
	for operation in ops:
		start, old, new = operation["offset"], operation["old"], operation["new"]
		require(len(old) == len(new) and source[start:start + len(old)] == old, "Original operation bytes mismatch")
		for i, (a, b) in enumerate(zip(old, new)):
			if a != b:
				require(start + i not in result, "Overlapping operations")
				result[start + i] = (a, b)
	return result


def verify_output(source, output, profile):
	ops = validate_source(source, profile)
	expected = expected_changes(source, ops)
	require(len(source) == len(output), "Output size changed")
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(source, output)) if a != b}
	require(actual == expected, "Unintended full-file differences")
	for operation in ops:
		start = operation["offset"]
		require(output[start:start + len(operation["new"])] == operation["new"], "Output operation mismatch")
	verify_rates(output)
	require(output[:0xC0] == source[:0xC0], "Header changed")
	if profile == "recruitment-test":
		require(output[0x800000:] == source[0x800000:], "Recruitment payload/padding changed")
		require(output[0x10D69D:0x10D6A3] == source[0x10D69D:0x10D6A3], "Recruitment redirect changed")
	ranges = []
	for offset in sorted(actual):
		if not ranges or ranges[-1][1] != offset:
			ranges.append([offset, offset + 1])
		else:
			ranges[-1][1] += 1
	return dict(full_file_comparison_passed=True, compared_bytes=len(source), changed_bytes=len(actual),
		actual_modified_ranges=[dict(start=hex(a), end_exclusive=hex(b),
			old=source[a:b].hex(" "), new=output[a:b].hex(" ")) for a, b in ranges],
		all_five_transaction_blocks_quantity_two=True, header_preserved=True,
		recruitment_payload_preserved=profile == "recruitment-test", runtime_validation="untested")


def build(source, profile):
	ops = validate_source(source, profile)
	expected_changes(source, ops)
	output = bytearray(source)
	for operation in ops:
		start = operation["offset"]
		require(output[start:start + len(operation["old"])] == operation["old"], "Original bytes changed before operation")
		output[start:start + len(operation["new"])] = operation["new"]
	verify_output(source, output, profile)
	return output


def fresh_directory(name):
	require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", name) is not None, "Unsafe output directory name")
	output = Path(__file__).resolve().parent / "output" / name
	output.mkdir(parents=True, exist_ok=False)
	return output


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--profile", choices=PROFILES, default="baseline")
	parser.add_argument("--output-name")
	args = parser.parse_args()
	path, fingerprint, size = PROFILES[args.profile]
	source = path.read_bytes()
	ops = validate_source(source, args.profile)
	before = protected()
	evidence_bytes = EVIDENCE.read_bytes()
	evidence = json.loads(evidence_bytes)
	for name, expected in evidence["protected_before"].items():
		require(before.get(name) == expected, "Protected artifact differs from preflight: " + name)
	for window in evidence["native_windows"]:
		start, end = (int(v, 16) for v in window["file_range"])
		require(sha(source[start:end]) == window["sha256"], "Handler evidence window mismatch")
	ledger = [dict(offset=hex(o["offset"]), old=o["old"].hex(" "), new=o["new"].hex(" "), role=o["role"]) for o in ops]
	require(ledger == evidence["operations"], "Patch operations differ from preflight")
	output = build(source, args.profile)
	name = args.output_name or "binky-rate-two-" + args.profile + "-" + uuid.uuid4().hex
	directory = fresh_directory(name)
	rom = directory / "binky_exchange_rate_two.gba"
	with rom.open("xb") as stream:
		require(stream.write(output) == size, "Short output write")
	readback = rom.read_bytes()
	require(readback == output, "Readback mismatch")
	verification = verify_output(source, readback, args.profile)
	after = protected()
	require(after.pop(str(rom.relative_to(ROOT)), None) == sha(readback), "New output inventory mismatch")
	require(after == before, "Protected files changed")
	manifest = dict(experiment="constant two Binkies for every successful full-AWE exchange",
		profile=args.profile, source=str(path), source_sha256=fingerprint, source_bytes=size,
		output=str(rom), output_sha256=sha(readback), output_bytes=len(readback),
		script_sha256=sha(Path(__file__).read_bytes()), evidence_sha256=sha(evidence_bytes),
		analysis_script_sha256=sha((ROOT / "tools/analyze/binky_exchange_rate.py").read_bytes()),
		operations=ledger, verification=verification, protected_before=before, protected_after=after,
		protected_unchanged=True, runtime_validation="untested; user-operated mGBA only")
	with (directory / "manifest.json").open("x", encoding="utf-8") as stream:
		stream.write(json.dumps(manifest, indent=2) + "\n")
	require(json.loads((directory / "manifest.json").read_text()) == manifest, "Manifest readback mismatch")
	print(json.dumps(dict(rom=str(rom), manifest=str(directory / "manifest.json"),
		sha256=sha(readback), changed_bytes=verification["changed_bytes"]), indent=2))


if __name__ == "__main__":
	main()
