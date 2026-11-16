"""Construct only the authorized expanded Alessa/Hanzo event experiment.

Run: python -B tools/patch/alessa_recruitment_wrapper.py
Optional --output-name selects a fresh directory below tools/patch/output.
No emulator execution or save/state writes. Existing destinations are rejected.
See reverse_engineering/experiments/alessa_recruitment_wrapper.md for evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "Tomato Adventure (Japan) (patched).gba"
BASELINE_SHA256 = "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde"
INPUT_SIZE = 0x00800000
OUTPUT_SIZE = 0x01000000
CALL_OFFSET = 0x0010D69D
POINTER_OFFSET = 0x0010D69F
ORIGINAL_CALL = bytes.fromhex("FD 2F 33 4B 12 08")
PAYLOAD_OFFSET = INPUT_SIZE
PAYLOAD_BUS = 0x08800000
RESERVATION_SIZE = 0x20
POINTER = struct.pack("<I", PAYLOAD_BUS)
PAYLOAD = bytes.fromhex("FE 49 FE 53 6B FD 0B 1A 83 00 FD 0B 1C 1B 00 FD 30 33 4B 12 08")
EVIDENCE_DIR = ROOT / "reverse_engineering/experiments"


def sha256(data):
	return hashlib.sha256(data).hexdigest()


def require(condition, message):
	if not condition:
		raise ValueError(message)


def snapshot_protected():
	return {str(p.relative_to(ROOT)): sha256(p.read_bytes()) for p in ROOT.rglob("*")
		if p.is_file() and (p.suffix.lower() in (".gba", ".sav")
		or re.fullmatch(r"\.ss\d.*", p.suffix.lower()))}


def validate_source(source):
	require(len(source) == INPUT_SIZE and sha256(source) == BASELINE_SHA256,
		"Input is not the protected unmodified English baseline")
	require(source[CALL_OFFSET:CALL_OFFSET + 6] == ORIGINAL_CALL, "Unexpected Hanzo call")
	require(struct.unpack("<I", source[POINTER_OFFSET:POINTER_OFFSET + 4])[0] == 0x08124B33,
		"Original event pointer encoding mismatch")
	require(PAYLOAD_BUS == 0x08000000 + PAYLOAD_OFFSET and POINTER == bytes.fromhex("00 00 80 08"),
		"Payload event pointer encoding mismatch")
	require(PAYLOAD_OFFSET == len(source) and PAYLOAD_OFFSET % 4 == 0
		and len(PAYLOAD) == 21 and len(PAYLOAD) <= RESERVATION_SIZE
		and PAYLOAD_OFFSET + RESERVATION_SIZE <= OUTPUT_SIZE <= 0x02000000,
		"Allocation bounds mismatch")
	require(source[0x127326:0x12732F] == bytes.fromhex("FD 49 17 01 FE 49 FE 53 6B")
		and source[0x124BF0:0x124BF2] == bytes.fromhex("FD 7C"),
		"Original recruitment or shared return bytes mismatch")


def verify_evidence(source, protected):
	evidence = {}
	for name in ("alessa_wrapper_preflight.json", "alessa_wrapper_allocation.json"):
		data = (EVIDENCE_DIR / name).read_bytes()
		evidence[name] = {"sha256": sha256(data), "data": json.loads(data.decode("utf-8-sig"))}
	preflight = evidence["alessa_wrapper_preflight.json"]["data"]
	for name, expected in preflight["protected_before"].items():
		require(protected.get(name) == expected, "Protected file differs from retained evidence: " + name)
	a = evidence["alessa_wrapper_allocation.json"]["data"]
	require(a["baseline_sha256"] == BASELINE_SHA256, "Allocation evidence baseline mismatch")
	require(a["candidate_expansion"]["final_size"] == f"0x{OUTPUT_SIZE:08X}"
		and a["candidate_expansion"]["payload_file_start"] == f"0x{PAYLOAD_OFFSET:08X}"
		and a["candidate_expansion"]["payload_bus_start"] == f"0x{PAYLOAD_BUS:08X}"
		and a["candidate_expansion"]["payload_end_exclusive"] == f"0x{PAYLOAD_OFFSET + len(PAYLOAD):08X}"
		and a["candidate_expansion"]["encoded_pointer"] == POINTER.hex(" ").upper(),
		"Allocation evidence contradicts authorized design")
	for window in a["scoped_instruction_observations"]:
		start, end = (int(v, 16) for v in window["file_range"])
		require(0 <= start < end <= len(source) and sha256(source[start:end]) == window["sha256"],
			"Instruction evidence window mismatch")
	require(a["command_operand_sizes"]["FD 2F"] == 4
		and a["command_operand_sizes"]["FD 30"] == 4
		and a["command_operand_sizes"]["FE 49"] == 0
		and a["command_operand_sizes"]["FE 53"] == 1,
		"Interpreter argument evidence mismatch")
	return {name: {"sha256": entry["sha256"]} for name, entry in evidence.items()}


def verify_output(source, output):
	validate_source(source)
	require(len(output) == OUTPUT_SIZE, "Incorrect output length")
	require(output[CALL_OFFSET:CALL_OFFSET + 6] == b"\xfd\x2f" + POINTER, "Patched call mismatch")
	changes = [i for i, (old, new) in enumerate(zip(source, output[:INPUT_SIZE])) if old != new]
	expected = [POINTER_OFFSET + i for i in range(4) if ORIGINAL_CALL[2 + i] != POINTER[i]]
	require(changes == expected, "Unintended prefix differences")
	require(output[:POINTER_OFFSET] == source[:POINTER_OFFSET]
		and output[POINTER_OFFSET + 4:INPUT_SIZE] == source[POINTER_OFFSET + 4:],
		"Unintended changes outside pointer operation")
	require(output[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(PAYLOAD)] == PAYLOAD, "Payload mismatch")
	padding = output[PAYLOAD_OFFSET + len(PAYLOAD):]
	require(padding == b"\xff" * len(padding), "Expanded padding differs from FF")
	require(output[:0xC0] == source[:0xC0], "Header changed")
	return {
		"full_file_comparison_passed": True,
		"prefix_compared_bytes": INPUT_SIZE,
		"prefix_actual_changed_bytes": len(changes),
		"prefix_actual_changes": [{"file_offset": f"0x{i:08X}",
			"old": f"{source[i]:02X}", "new": f"{output[i]:02X}"} for i in changes],
		"expanded_region_bytes": OUTPUT_SIZE - INPUT_SIZE,
		"payload_bytes": len(PAYLOAD), "ff_padding_bytes": len(padding),
		"header_preserved": True,
		"original_shared_reward_preserved": output[0x124B33:0x124BF2] == source[0x124B33:0x124BF2],
		"output_length_verified": OUTPUT_SIZE,
	}


def build(source):
	validate_source(source)
	output = bytearray(source)
	# Expansion operation has no existing input bytes to overwrite.
	require(len(output) == PAYLOAD_OFFSET, "Expansion does not start at original EOF")
	output.extend(b"\xff" * (OUTPUT_SIZE - len(output)))
	require(output[PAYLOAD_OFFSET:PAYLOAD_OFFSET + RESERVATION_SIZE] == b"\xff" * RESERVATION_SIZE,
		"Unexpected reservation bytes before insertion")
	output[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(PAYLOAD)] = PAYLOAD
	require(output[CALL_OFFSET:CALL_OFFSET + 6] == ORIGINAL_CALL,
		"Original call changed before pointer edit")
	output[POINTER_OFFSET:POINTER_OFFSET + 4] = POINTER
	verify_output(source, output)
	return output


def fresh_directory(name):
	require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,100}", name) is not None,
		"Output name must be a simple directory name")
	outdir = Path(__file__).resolve().parent / "output" / name
	outdir.mkdir(parents=True, exist_ok=False)
	return outdir


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--output-name", default="alessa-recruitment-wrapper-" + uuid.uuid4().hex)
	args = parser.parse_args()
	source = BASELINE.read_bytes()
	validate_source(source)
	before = snapshot_protected()
	evidence = verify_evidence(source, before)
	output = build(source)
	outdir = fresh_directory(args.output_name)
	outrom = outdir / "alessa_recruitment_wrapper.gba"
	with outrom.open("xb") as handle:
		require(handle.write(output) == OUTPUT_SIZE, "Short ROM write")
	readback = outrom.read_bytes()
	require(readback == output, "Written output differs from verified buffer")
	verification = verify_output(source, readback)
	after = snapshot_protected()
	require(after.pop(str(outrom.relative_to(ROOT)), None) == sha256(readback), "New ROM snapshot mismatch")
	require(before == after, "Protected file inventory/hashes changed")
	manifest = {
		"experiment": "Alessa recruitment and Pop Horn through first Hanzo reward",
		"schema_version": 1, "script_sha256": sha256(Path(__file__).read_bytes()),
		"source": str(BASELINE), "source_sha256": sha256(source), "source_size": INPUT_SIZE,
		"output": str(outrom), "output_sha256": sha256(readback), "output_size": OUTPUT_SIZE,
		"evidence": evidence,
		"pointer_operation": {"file_start": f"0x{POINTER_OFFSET:08X}",
			"file_end_exclusive": f"0x{POINTER_OFFSET + 4:08X}",
			"old": ORIGINAL_CALL[2:].hex(" ").upper(), "new": POINTER.hex(" ").upper(),
			"original_call": ORIGINAL_CALL.hex(" ").upper(),
			"replacement_call": readback[CALL_OFFSET:CALL_OFFSET + 6].hex(" ").upper()},
		"expansion": {"file_start": f"0x{INPUT_SIZE:08X}", "file_end_exclusive": f"0x{OUTPUT_SIZE:08X}",
			"payload_bus": f"0x{PAYLOAD_BUS:08X}", "reservation_bytes": RESERVATION_SIZE,
			"payload_file_end_exclusive": f"0x{PAYLOAD_OFFSET + len(PAYLOAD):08X}",
			"payload": PAYLOAD.hex(" ").upper(), "padding": "FF"},
		"output_prefix_sha256": sha256(readback[:INPUT_SIZE]),
		"expanded_region_sha256": sha256(readback[INPUT_SIZE:]),
		"verification": verification,
		"protected_file_count": len(before), "protected_files_before": before,
		"protected_files_after": after, "protected_integrity_passed": True,
		"runtime_tested": False,
	}
	manifest_path = outdir / "manifest.json"
	with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
		json.dump(manifest, handle, indent=2)
		handle.write("\n")
	loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
	require(loaded == manifest and loaded["output_sha256"] == sha256(outrom.read_bytes()),
		"Manifest readback mismatch")
	print(json.dumps({"output": str(outrom), "manifest": str(manifest_path),
		"source_sha256": sha256(source), "output_sha256": sha256(readback),
		"verification": verification, "protected_file_count": len(before),
		"runtime_tested": False}, indent=2))


if __name__ == "__main__":
	main()
