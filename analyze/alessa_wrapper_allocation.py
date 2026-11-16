"""Bounded read-only follow-up to the retained Alessa wrapper preflight.

Prints evidence JSON only. No ROM assembly, patch buffers, or emulator execution.
Run from repository root: python -B tools/analyze/alessa_wrapper_allocation.py
"""
import hashlib
import json
from pathlib import Path
import struct
import zlib

from thumb_inspect import inspect

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "reverse_engineering/experiments/alessa_wrapper_preflight.json"
# Half-open file ranges. Explicit exclusions are literal pools, not instructions.
WINDOWS = (
	(0x21F30, 0x21F70, ((0x21F48, 0x21F4C), (0x21F58, 0x21F5C), (0x21F6A, 0x21F70))),
	(0x22388, 0x22510, ()),
	(0x22534, 0x2256E, ()),
	(0x227F0, 0x22864, ()),
	(0x22874, 0x228F8, ()),
	(0x22A84, 0x22AD4, ()),
	(0x252F4, 0x2536C, ((0x25320, 0x2532C),)),
	(0x25624, 0x25632, ()),
	(0x2896C, 0x289B6, ()),
	(0x28A98, 0x28B0C, ((0x28AB8, 0x28AC0),)),
	(0x2900C, 0x290CA, ()),
	(0x290E4, 0x29122, ()),
	(0x29260, 0x29274, ()),
	(0x2927C, 0x292AC, ()),
	(0x29F2C, 0x29F4C, ()),
	(0x2A2F4, 0x2A312, ()),
	(0x2F97C, 0x2F9A0, ()),
	(0x2FEF0, 0x2FEF2, ()),
	(0x32BF0, 0x32C08, ()),
	(0x32CB8, 0x32E44, ((0x32DD8, 0x32DF4),)),
	(0x6A00C, 0x6A01E, ()),
	(0x6ADA0, 0x6AE2A, ((0x6AE00, 0x6AE14),)),
	(0x80424, 0x8054E, ((0x80444, 0x80450), (0x80458, 0x8045C),
		(0x804A4, 0x804A8), (0x804E0, 0x804E4), (0x8052C, 0x80534))),
	(0x8064C, 0x80800, ((0x80774, 0x80794), (0x807E8, 0x807F0))),
	(0x80800, 0x80874, ()),
	# Two retained pointer-shaped candidates crossing known instruction bytes.
	(0x7A42E, 0x7A43C, ()),
	(0x93AC6, 0x93AD8, ()),
)


def sha(data):
	return hashlib.sha256(data).hexdigest()


def verify_protected(retained):
	for name, expected in retained.items():
		if sha((ROOT / name).read_bytes()) != expected:
			raise ValueError("Protected file differs from preflight: " + name)


def main():
	audit = json.loads(AUDIT.read_text(encoding="utf-8-sig"))
	retained = audit["protected_before"]
	verify_protected(retained)
	rom = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	if len(rom) != 0x800000:
		raise ValueError("Unexpected baseline size")
	observations = []
	for start, end, excluded in WINDOWS:
		observations.append({
			"file_range": [f"0x{start:08X}", f"0x{end:08X}"],
			"sha256": sha(rom[start:end]),
			"instructions": [{"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "),
				"text": i.text} for i in inspect(rom, start, end, excluded)],
		})
	p, state = 8, None
	checkpoint = (ROOT / "entry-stop.ss0").read_bytes()
	while p < len(checkpoint):
		n = struct.unpack_from(">I", checkpoint, p)[0]
		if checkpoint[p + 4:p + 8] == b"gbAs":
			state = zlib.decompress(checkpoint[p + 8:p + 8 + n])
		p += n + 12
	if state is None or len(state) != 0x61000:
		raise ValueError("Unexpected checkpoint state size")
	iw = state[0x19000:0x21000]
	# Tables are scoped solely to commands used by the wrapper/shared reward.
	command_sizes = {}
	for family, base, ops in (("FD", 0x62B815, (0x0B, 0x15, 0x17, 0x2F, 0x30, 0x3C, 0x7C)),
		("FE", 0x62B736, (0, 0x16, 0x49, 0x53, 0x54))):
		for op in ops:
			command_sizes[f"{family} {op:02X}"] = rom[base + op]
	shared_commands, cursor = [], 0x124B33
	while cursor < 0x124BF2:
		family = rom[cursor]
		op = rom[cursor + 1] if family in (0xFD, 0xFE) else family
		table = {0xFD: 0x62B815, 0xFE: 0x62B736}.get(family, 0x62B6C4)
		end = cursor + (2 if family in (0xFD, 0xFE) else 1) + rom[table + op]
		if end > 0x124BF2:
			raise ValueError("Shared block command crosses scoped end")
		shared_commands.append({"bus": f"0x{cursor + 0x08000000:08X}",
			"bytes": rom[cursor:end].hex(" ")})
		cursor = end
	verify_protected(retained)
	print(json.dumps({
		"mode": "read-only static allocation/context evidence; no ROM output",
		"protected_file_count": len(retained), "all_protected_match_preflight_before_and_after": True,
		"baseline_sha256": sha(rom), "command_operand_sizes": command_sizes,
		"header_complement": {"stored": rom[0xBD], "calculated": (-sum(rom[0xA0:0xBD]) - 0x19) & 255},
		"candidate_expansion": {"final_size": "0x01000000", "payload_file_start": "0x00800000",
			"payload_bus_start": "0x08800000", "payload_end_exclusive": "0x00800015",
			"encoded_pointer": "00 00 80 08", "status": "proposed allocation design only"},
		"alessa_default_record_file": "0x00630BF8",
		"alessa_default_record_hex": rom[0x630BF8:0x630C14].hex(" "),
		"checkpoint_character_record_hex": iw[0x1F3C:0x1F9C].hex(" "),
		"checkpoint_general_inventory_prefix_hex": iw[0x1A6F:0x1A7B].hex(" "),
		"shared_reward_script_hex": rom[0x124B33:0x124BF2].hex(" "),
		"shared_reward_command_boundaries": shared_commands,
		"scoped_instruction_observations": observations,
		"runtime_tested": False,
	}, indent=2))


if __name__ == "__main__":
	main()
