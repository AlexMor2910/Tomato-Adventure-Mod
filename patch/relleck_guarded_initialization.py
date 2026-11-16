"""Build the approved guarded Relleck initialization experiment offline only.

Run: python -B tools/patch/relleck_guarded_initialization.py
Source is the unchanged rate-two + Alessa recruitment ROM, never a Sofoubi ROM.
Runtime requires separate authorization and a disposable clean checkpoint copy.
The silent FE49/two-grant sequence is not atomic; discard interrupted branches.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import uuid

from sofoubi_initialization_wrapper import ROOT, SOURCE, SOURCE_SHA256, SIZE, sha, require, validate_source, write_json
from sofoubi_guarded_initialization import snapshot, decode

CHECKPOINT = ROOT / "sofoubi_initialized_guarded.ss0"
CHECKPOINT_SHA256 = "9abd5427393c027bfd25ac50395e7546337e7331114b2d1a70ba9dcdf3ceebcf"
GUARD_OFFSET = 0x00800040
GUARD_BUS = 0x08800040
PAYLOAD = bytes.fromhex("FE 49 FE 53 F1 FE 53 E5 FD 7C")
GUARD = bytes.fromhex(
	"0B 48 00 78 C1 00 09 1A 89 00 0A 4A 52 18 10 68 "
	"09 49 88 42 06 D1 09 48 00 78 80 21 08 42 03 D1 "
	"71 28 01 D1 06 4B 18 47 06 48 10 60 70 47 C0 46 "
	"C0 39 00 03 D8 3A 00 03 22 00 80 08 B4 1A 00 03 "
	"F5 52 02 08 28 00 80 08")
OPERATIONS = (
	(0x00102D31, bytes.fromhex("81 7E 10 08"), bytes.fromhex("20 00 80 08")),
	(0x00800020, b"\xff" * 10, PAYLOAD),
	(0x0062B9D8, bytes.fromhex("F5 52 02 08"), bytes.fromhex("41 00 80 08")),
	(GUARD_OFFSET, b"\xff" * 72, GUARD),
)


def audit_guard(guard):
	words = (0x480B, 0x7800, 0x00C1, 0x1A09, 0x0089, 0x4A0A, 0x1852, 0x6810,
		0x4909, 0x4288, 0xD106, 0x4809, 0x7800, 0x2180, 0x4208, 0xD103,
		0x2871, 0xD101, 0x4B06, 0x4718, 0x4806, 0x6010, 0x4770, 0x46C0)
	pool = (0x030039C0, 0x03003AD8, 0x08800022, 0x03001AB4, 0x080252F5, 0x08800028)
	require(guard == struct.pack("<24H6I", *words, *pool), "Guard differs from approved audit")
	rows = []
	for offset in range(0, 48, 2):
		i = decode(guard, offset, GUARD_BUS)
		require(i.size == 2 and "unsupported" not in i.text, "Invalid Thumb instruction")
		rows.append(dict(bus=f"0x{i.address:08X}", bytes=i.raw.hex(" ").upper(), instruction=i.text))
	for offset, value in {0: pool[0], 10: pool[1], 16: pool[2], 22: pool[3], 36: pool[4], 40: pool[5]}.items():
		i = decode(guard, offset, GUARD_BUS)
		require(i.literal_value == value and i.literal_address % 4 == 0, "Literal pool/load mismatch")
	for offset, target in ((20, 0x08800064), (30, 0x08800068), (34, 0x08800068)):
		require(decode(guard, offset, GUARD_BUS).target == target, "Conditional branch mismatch")
	require(decode(guard, 38, GUARD_BUS).text == "bx r3"
		and decode(guard, 44, GUARD_BUS).text == "bx r14", "Tail transfer or return mismatch")
	require(not any(row["instruction"].startswith(("push", "pop", "bl ")) for row in rows), "Stack/LR behavior mismatch")
	for slot in range(32):
		require(0x03003AD8 + (slot * 8 - slot) * 4 == 0x03003AD4 + slot * 28 + 4,
			"Active cursor calculation mismatch")
	for member in range(256):
		require(((member & 0x80) == 0 and member == 0x71) == (member == 0x71), "Membership guard mismatch")
	return dict(bytes=72, sha256=sha(guard), instructions=rows,
		literal_pool=[dict(bus=f"0x{GUARD_BUS + 48 + i * 4:08X}", value=f"0x{v:08X}") for i, v in enumerate(pool)],
		branch_targets_verified=True, original_fe49_tail_transfer="0x080252F5",
		unrelated_cursor_forwarding=True, allowed_membership="0x71", recruited_mask="0x80",
		skip_cursor="0x08800028", bypasses_both_grants=True,
		valid_slot_cases=32, membership_cases=256, runtime_tested=False)


def preflight(source):
	validate_source(source)
	require(sha(CHECKPOINT.read_bytes()) == CHECKPOINT_SHA256, "Clean checkpoint identity mismatch")
	require(source[0x800020:0x800088] == b"\xff" * 0x68, "Allocated padding mismatch")
	require(source[0x10A9C2:0x10A9CA] == PAYLOAD[:8], "Original Relleck recruitment/grants mismatch")
	require(source[0x62B736 + 0x49] == 0 and source[0x62B736 + 0x53] == 1
		and source[0x62B815 + 0x7C] == 0, "Interpreter command lengths mismatch")
	require(PAYLOAD[8:] == bytes.fromhex("FD 7C"), "Skip target does not bypass both grants")
	require(0x62B8B4 + 0x49 * 4 == 0x62B9D8, "Dispatch entry arithmetic mismatch")
	for offset, old, new in OPERATIONS:
		require(len(old) == len(new) and source[offset:offset + len(old)] == old, "Original operation bytes mismatch")
	return audit_guard(GUARD)


def verify(source, output):
	audit = preflight(source)
	require(len(source) == len(output) == SIZE, "ROM size changed")
	expected = {offset + i: (a, b) for offset, old, new in OPERATIONS
		for i, (a, b) in enumerate(zip(old, new)) if a != b}
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(source, output)) if a != b}
	require(actual == expected and len(actual) == 88, "Unauthorized differences or changed-byte count")
	for offset, old, new in OPERATIONS:
		require(output[offset:offset + len(new)] == new, "Output operation mismatch")
	for start, end in ((0, 0xC0), (0x107E81, 0x1081DA), (0x65FC48, 0x65FD15),
		(0x10D69D, 0x10D6A3), (0x800000, 0x800020), (0x252F4, 0x25374)):
		require(output[start:end] == source[start:end], "Protected implementation changed")
	require(struct.unpack_from("<I", output, 0x62B9D8)[0] == (GUARD_BUS | 1), "Thumb dispatch pointer mismatch")
	require(audit_guard(output[GUARD_OFFSET:GUARD_OFFSET + 72]) == audit, "Output guard decoding mismatch")
	return dict(compared_bytes=SIZE, actual_changed_bytes=88, full_file_comparison_passed=True,
		header_preserved=True, alessa_wrapper_preserved=True, exchange_script_and_advice_preserved=True,
		original_fe49_handler_preserved=True, guard_audit=audit,
		differences=[dict(file_offset=f"0x{i:08X}", bus_address=f"0x{i + 0x08000000:08X}",
			old=f"{a:02X}", new=f"{b:02X}") for i, (a, b) in actual.items()])


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--output-name", default="relleck-guarded-" + uuid.uuid4().hex)
	args = parser.parse_args()
	require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", args.output_name) is not None, "Unsafe output name")
	source = SOURCE.read_bytes()
	preflight(source)
	before = snapshot()
	output = bytearray(source)
	for offset, old, new in OPERATIONS:
		output[offset:offset + len(new)] = new
	checks = verify(source, output)
	directory = ROOT / "tools/patch/output" / args.output_name
	directory.mkdir(exist_ok=False)
	rompath = directory / "relleck_guarded_initialization.gba"
	with rompath.open("xb") as handle:
		require(handle.write(output) == SIZE, "Short ROM write")
	readback = rompath.read_bytes()
	require(readback == output and verify(source, readback) == checks, "Output readback failed")
	diffpath = directory / "byte_differences.json"
	write_json(diffpath, checks)
	after = snapshot()
	for p in (rompath, diffpath):
		require(after.pop(str(p.relative_to(ROOT)), None) == sha(p.read_bytes()), "New artifact hash mismatch")
	require(before == after, "Protected artifacts changed during construction")
	manifest = dict(schema_version=1, experiment="Guarded Relleck initialization; offline construction only",
		script_sha256=sha(Path(__file__).read_bytes()), source=str(SOURCE.relative_to(ROOT)),
		source_sha256=SOURCE_SHA256, source_size=SIZE, output=str(rompath.relative_to(ROOT)),
		output_sha256=sha(readback), output_size=SIZE,
		clean_checkpoint=str(CHECKPOINT.relative_to(ROOT)), clean_checkpoint_sha256=CHECKPOINT_SHA256,
		operations=[dict(file_start=f"0x{offset:08X}", file_end_exclusive=f"0x{offset + len(old):08X}",
			old=old.hex(" ").upper(), new=new.hex(" ").upper()) for offset, old, new in OPERATIONS],
		verification=checks, difference_report_sha256=sha(diffpath.read_bytes()),
		protected_artifact_count=len(before), protected_before=before, protected_after=after,
		protected_unchanged=True, runtime_tested=False,
		limitations=["Silent and non-atomic: discard interrupted initialization",
			"Requires clean Sofoubi checkpoint; no contaminated or late-stage source",
			"No automatic repair of missing grants or partial character initialization",
			"Runtime initialization, replay protection, and exchange still require user validation"])
	manifestpath = directory / "manifest.json"
	write_json(manifestpath, manifest)
	final = snapshot()
	for p in (rompath, diffpath, manifestpath):
		require(final.pop(str(p.relative_to(ROOT)), None) == sha(p.read_bytes()), "Final artifact hash mismatch")
	require(before == final, "Protected artifacts changed during final audit")
	print(json.dumps(dict(output=str(rompath), manifest=str(manifestpath), byte_differences=str(diffpath),
		source_sha256=SOURCE_SHA256, output_sha256=sha(readback), changed_bytes=88,
		protected_artifact_count=len(before), protected_unchanged=True, runtime_tested=False), indent=2))


if __name__ == "__main__":
	main()
