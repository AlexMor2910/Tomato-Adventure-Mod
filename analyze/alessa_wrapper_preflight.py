"""Read-only Alessa wrapper preflight. Does not allocate space or write ROMs.

Run: python -B tools/analyze/alessa_wrapper_preflight.py
Pointer-shaped values are candidates, not established references.
"""
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
	"Tomato Adventure (Japan).gba": "0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12",
	"Tomato Adventure (Japan) (patched).gba": "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde",
	"entry-stop.ss0": "d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29",
}


def fingerprint(path):
	return hashlib.sha256(path.read_bytes()).hexdigest()


def protected():
	return {str(p.relative_to(ROOT)): fingerprint(p) for p in ROOT.rglob("*")
		if p.is_file() and (p.suffix.lower() in (".gba", ".sav")
		or (p.suffix.lower().startswith(".ss") and p.suffix[3:4].isdigit()))}


def main():
	before = protected()
	for name, expected in EXPECTED.items():
		if before.get(name) != expected:
			raise ValueError("Protected fingerprint mismatch: " + name)
	r = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	j = (ROOT / "Tomato Adventure (Japan).gba").read_bytes()
	assert len(r) == len(j) == 0x800000
	checks = {0x10D693: "FD 0B 1A 83 00 FD 0B 1C 1B 00 FD 2F 33 4B 12 08",
		0x127326: "FD 49 17 01 FE 49 FE 53 6B", 0x124BF0: "FD 7C"}
	for offset, value in checks.items():
		expected = bytes.fromhex(value)
		assert r[offset:offset + len(expected)] == expected
	dispatch = {}
	for family, base, ops in (("FD", 0x62BC30, (0x2F, 0x30, 0x7C)),
		("FE", 0x62B8B4, (0x49, 0x53))):
		for op in ops:
			dispatch[f"{family} {op:02X}"] = f"0x{struct.unpack_from('<I', r, base + 4 * op)[0]:08X}"
	refs = []
	for offset in range(len(r) - 3):
		value = struct.unpack_from("<I", r, offset)[0]
		if any(base + 0x7F1BE0 <= value < base + len(r)
			for base in (0x08000000, 0x0A000000, 0x0C000000)):
			refs.append({"file_offset": f"0x{offset:08X}", "value": f"0x{value:08X}"})
	data = (ROOT / "entry-stop.ss0").read_bytes()
	p, state = 8, None
	while p < len(data):
		n = struct.unpack_from(">I", data, p)[0]
		if data[p + 4:p + 8] == b"gbAs":
			state = zlib.decompress(data[p + 8:p + 8 + n])
		p += n + 12
	assert state is not None and len(state) == 0x61000
	iw = state[0x19000:0x21000]
	after = protected()
	assert before == after, "Protected files changed during preflight"
	print(json.dumps({
		"status": "STOPPED: safe payload allocation not established; no patch constructed",
		"protected_file_count": len(before), "protected_before": before,
		"protected_after_equal": True, "baseline_sha256": EXPECTED,
		"commands": {f"0x{k:08X}": v for k, v in checks.items()},
		"dispatch_thumb_pointers": dispatch,
		"checkpoint_saved_bytes": {f"0x{0x03000000 + a:08X}": iw[a]
			for a in (0x1AB4, 0x35F0, 0x1F43, 0x196E)},
		"alessa_saved_name_record_prefix": iw[0x1F3C:0x1F43].hex(" "),
		"tail": {"start": "0x007F1BE0", "end_exclusive": "0x00800000",
			"english_all_ff": all(v == 255 for v in r[0x7F1BE0:]),
			"japanese_all_ff": all(v == 255 for v in j[0x7F1BE0:]),
			"confidence": "Candidate only; no allocation ownership proof",
			"pointer_shaped_candidates": refs},
		"output_rom": None, "modified_rom_offsets": [], "runtime_tested": False,
	}, indent=2))


if __name__ == "__main__":
	main()
