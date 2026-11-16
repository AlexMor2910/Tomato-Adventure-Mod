"""Read-only inventory of Hawker-specific text callbacks; no extracted text output."""
import json
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha
from hawker_stage1 import native_function


def main():
	gate = json.loads((ROOT / "reverse_engineering/hawker_final_gate_evidence.json").read_text(encoding="utf-8"))
	before = {p: sha((ROOT / p).read_bytes()) for p in gate["protected_after"]}
	assert before == gate["protected_after"]
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED
	d = json.loads((ROOT / "reverse_engineering/hawker_dependency_resolution_evidence.json").read_text(encoding="utf-8"))
	ptrs = set()
	for c in d["exchange_commands"]:
		b = bytes.fromhex(c["bytes"])
		if b[:2] in (b"\xfe\xbc", b"\xfe\xc8", b"\xfe\x66"):
			ptrs.add(int.from_bytes(b[2:6], "little"))
	messages, controls = [], set()
	# All controls actually encountered here are parameterless. Fail if new ones appear.
	allowed = {0, 1, 2, 5, 0x12, 0x26, 0x30, 0x32, 0x40, 0x41, 0x42, 0x43, 0x80, 0x82, 0x83, 0x84}
	for p in sorted(ptrs):
		a, codes = p - 0x08000000, []
		start = a
		while a < start + 1024:
			v = r[a]
			a += 1
			assert v != 0xFE, "Unexpected kanji lead in scoped English message"
			if v == 0xFF:
				op = r[a]
				a += 1
				assert op in allowed
				codes.append(f"FF {op:02X}")
				controls.add(op)
				if op == 0:
					break
		else:
			raise ValueError("Scoped message did not terminate")
		messages.append({"bus": hex(p), "bytes": a-start, "sha256": sha(r[start:a]), "controls": codes})
	callbacks = []
	for idx in range(41):
		a = 0x649F70 + idx * 12
		code = r[a]
		if code == 0xFF:
			break
		if code in controls:
			pointer = struct.unpack_from("<I", r, a+4)[0]
			callbacks.append({"control": f"FF {code:02X}", "record_bus": hex(a+0x08000000),
				"record_bytes": r[a:a+12].hex(" "), "callback": hex(pointer),
				"native": native_function(r, (pointer & ~1)-0x08000000)})
	assert len(callbacks) == len(controls) == 16 and len(messages) == 15
	extra = {hex(p+0x08000000): native_function(r, p) for p in (
		0x6D2BC, 0x6D448, 0x6D4CC, 0x6CD44, 0x6CD58, 0x6D144, 0x6CE80,
		0x6D388, 0x6D3CC, 0x6D174, 0x6CD34, 0x6D0EC, 0x6CEB0, 0x6D1D4, 0x6D234,
		0x6DEA0, 0x6DA40, 0x6D830, 0x6DD40, 0x6E80C, 0x2FEF0,
	)}
	all_traces = [x["native"] for x in callbacks] + list(extra.values())
	known = {int(x["entry_bus"], 16) for x in all_traces}
	frontier = sorted({p for x in all_traces for p in x["direct_call_targets"] if int(p, 16) not in known})
	after = {p: sha((ROOT / p).read_bytes()) for p in before}
	assert before == after
	print(json.dumps({"source_sha256": EXPECTED, "messages": messages,
		"callback_records": callbacks, "menu_and_wait_helpers": extra,
		"direct_callee_frontier_not_certified": frontier,
		"conclusion": "Indirect callback table identified for all 15 messages; no complete alias/write closure claimed",
		"protected_game_artifacts": len(before), "protected_unchanged": True,
		"ROM_writes": 0, "runtime_performed": False}, indent=2))


if __name__ == "__main__":
	main()
