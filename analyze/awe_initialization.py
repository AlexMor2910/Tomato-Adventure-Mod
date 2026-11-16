"""Bounded read-only AWE inspection. Prints JSON; never writes runtime artifacts.

Run: python -B tools/analyze/awe_initialization.py
Instruction observations exclude known literal pools and are not emulation.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from thumb_inspect import inspect

ROOT = Path(__file__).resolve().parents[2]
RECRUITMENT = ROOT / "tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f/alessa_recruitment_wrapper.gba"
EXPECTED = {
	ROOT / "Tomato Adventure (Japan).gba": "0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12",
	ROOT / "Tomato Adventure (Japan) (patched).gba": "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde",
	RECRUITMENT: "3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6",
	ROOT / "entry-stop.ss0": "d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29",
}
# File offsets; half-open intervals. These are selected from existing findings.
WINDOWS = (
	("battle character initialization", 0x47CFC, 0x480BC, ()),
	("AWE menu gate", 0x4DD10, 0x4DD64, ((0x4DD54, 0x4DD5C),)),
	("menu gate caller", 0x4DC86, 0x4DCC6, ()),
	("charge gain state machine", 0x42A1C, 0x42BC6,
		((0x42A58, 0x42A6C), (0x42A94, 0x42A98), (0x42B00, 0x42B0C),
		(0x42B40, 0x42B50), (0x42B58, 0x42B5C))),
	("AWE action consumption", 0x501D4, 0x5027C, ((0x501F8, 0x501FC), (0x50230, 0x5023C))),
	("battle exit copyback", 0x3FE42, 0x3FE9C, ()),
	("persistent initializer clear", 0x32E06, 0x32E44, ()),
	("tutorial flag branch", 0x29F58, 0x29FF0,
		((0x29F68, 0x29F6C), (0x29F88, 0x29F90), (0x29FD0, 0x29FDC))),
	("tutorial flag set", 0x29FF0, 0x2A000, ()),
	("flag operation", 0x274A4, 0x274FA, ((0x274E4, 0x274F0),)),
	("tutorial battle entry", 0x24FC8, 0x2502A, ()),
	("tutorial control mode", 0x25D94, 0x25E0A, ((0x25DE8, 0x25DF8),)),
	("tutorial menu flag parameters", 0x29698, 0x296F0, ()),
	("tutorial camera parameters", 0x66168, 0x661EE, ((0x661AC, 0x661D4),)),
	("tutorial camera wait", 0x25FC0, 0x25FF2, ()),
	("tutorial scheduler pause", 0x29E34, 0x29E74, ()),
	("tutorial sound command", 0x28C1C, 0x28C40, ()),
)


def digest(data):
	return hashlib.sha256(data).hexdigest()


def protected():
	return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in ROOT.rglob("*")
		if p.is_file() and (p.suffix.lower() in (".gba", ".sav")
		or re.fullmatch(r"\.ss\d.*", p.suffix.lower()))}


def main():
	before = protected()
	for path, expected in EXPECTED.items():
		if before.get(str(path.relative_to(ROOT))) != expected:
			raise ValueError("Protected input fingerprint mismatch: " + str(path))
	r = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	j = (ROOT / "Tomato Adventure (Japan).gba").read_bytes()
	w = RECRUITMENT.read_bytes()
	observations = []
	for label, start, end, excluded in WINDOWS:
		if w[start:end] != r[start:end]:
			raise ValueError("Recruitment derivative differs in AWE window: " + label)
		observations.append({"role": label, "file_range": [f"0x{start:08X}", f"0x{end:08X}"],
			"english_sha256": digest(r[start:end]), "japanese_identical": j[start:end] == r[start:end],
			"recruitment_identical": True,
			"instructions": [{"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "), "text": i.text}
				for i in inspect(r, start, end, excluded)]})
	commands, cursor = [], 0x128D5A
	while cursor < 0x128F48:
		family = r[cursor]
		op = r[cursor + 1] if family in (0xFD, 0xFE) else family
		table = {0xFD: 0x62B815, 0xFE: 0x62B736}.get(family, 0x62B6C4)
		end = cursor + (2 if family in (0xFD, 0xFE) else 1) + r[table + op]
		if end > 0x128F48:
			raise ValueError("Tutorial command crosses bounded end")
		commands.append({"bus": f"0x{cursor + 0x08000000:08X}", "bytes": r[cursor:end].hex(" ")})
		cursor = end
	thresholds = {f"0x{0x08000000 + a:08X}": r[a] for a in (0x6397A6, 0x6397D2)}
	if w[0x128D5A:0x128F48] != r[0x128D5A:0x128F48]:
		raise ValueError("Recruitment derivative tutorial differs")
	after = protected()
	if before != after:
		raise ValueError("Protected file inventory/hashes changed during analysis")
	print(json.dumps({"mode": "bounded read-only static AWE analysis; runtime untested",
		"protected_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "verified_inputs": {str(p.relative_to(ROOT)): h for p, h in EXPECTED.items()},
		"alessa_thresholds": thresholds,
		"tutorial_commands": commands,
		"tutorial_japanese_identical": j[0x128D5A:0x128F48] == r[0x128D5A:0x128F48],
		"tutorial_recruitment_identical": True, "scoped_instruction_observations": observations,
		"predicted_readiness_from_zero": [{"charge": c,
			"ready_low_bits": (1 if c >= r[0x6397A6] else 0) | (2 if c >= r[0x6397D2] else 0)}
			for c in (0, 39, 40, 63, 64)],
		"runtime_tested_by_codex": False}, indent=2))


if __name__ == "__main__":
	main()
