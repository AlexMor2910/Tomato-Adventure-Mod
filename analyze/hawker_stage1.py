"""Bounded read-only Hawker scratch/context analysis. JSON stdout; no game writes.

Follows direct branches within explicit native functions, not transitive calls.
Indirect edges and unvisited callees remain explicit proof gaps. No emulator.
"""
import json
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha
from thumb_inspect import decode


# Explicit roots selected from the dialogue/context/FE31 traces, file offsets.
ROOTS = {
	"dialogue_root": 0x28C48, "FE_C8": 0x29E20, "FE66": 0x29D98,
	"dialogue_bridge": 0x29DAC, "dialogue_arguments": 0x29DC8,
	"dialogue_submit": 0x29E04, "dialogue_schedule": 0x6A804,
	"dialogue_start": 0x71B0C, "dialogue_setup": 0x6ECC8,
	"dialogue_initialize": 0x6BD94, "dialogue_open": 0x6C904,
	"dialogue_tick": 0x6BC98, "dialogue_prepare": 0x6BEB4,
	"dialogue_render_tick": 0x6CB10, "dialogue_read": 0x6DF08,
	"dialogue_character_dispatch": 0x6DE00,
	"dialogue_wait_dispatch": 0x6CBE4, "dialogue_wait_begin": 0x6CC1C,
	"dialogue_wait_continue": 0x6CCBC, "dialogue_wait_flag": 0x6CCF4,
	"dialogue_wait_done": 0x6CCA4, "dialogue_wait_state": 0x6CD08,
	"dialogue_end": 0x71BD0, "dialogue_completion": 0x71D84,
	"argument_byte": 0x22534, "argument_u16": 0x227F0,
	"argument_u32": 0x22874, "actor_resolver": 0x22798,
	"scratch_pointer_resolver": 0x22A84, "FE31": 0x28ED0,
	"actor_mode_write": 0x65E4C, "FE_dispatch": 0x2478C,
	"indirect_call_trampoline": 0xF7ACC, "VM_predecode": 0x22388,
	"FD2F": 0x2896C, "FE01": 0x2885C, "FE01_transfer": 0x2886C,
	"FD7C": 0x28A98, "FD7D": 0x2A03C,
	"event_end": 0x22908, "event_end_links": 0x2297C,
	"event_record_clear": 0x71C58, "byte_fill": 0x2F950,
	"event_bit_set": 0x6A540, "event_bit_clear": 0x6A5A0,
	"bit_set_core": 0x69EF0, "bit_clear_core": 0x69F28,
	"FEBC": 0x29434, "FEBC_bridge": 0x29470,
	"choice_branch": 0x25F1C, "FD30": 0x29F2C,
}


def native_function(r, start):
	"""Conservative direct CFG inventory; no claims about indirect targets."""
	queue, found, exits = [start], {}, []
	while queue:
		a = queue.pop()
		if a in found:
			continue
		if not start <= a < start + 0x1000:
			exits.append({"kind": "outside_explicit_function_bound", "bus": hex(a + 0x08000000)})
			continue
		i = decode(r, a)
		h = int.from_bytes(i.raw[:2], "little")
		found[a] = {"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "), "text": i.text}
		if i.text.startswith(".hword"):
			exits.append({"kind": "unsupported_instruction", "bus": hex(i.address)})
			continue
		if i.text.startswith("bx ") or (i.text.startswith("pop ") and "pc}" in i.text):
			continue
		if i.text.startswith("mov r15,"):
			exits.append({"kind": "indirect_PC_write", "bus": hex(i.address)})
			continue
		if h & 0xF800 == 0xE000:
			queue.append(i.target - 0x08000000)
		elif h & 0xF000 == 0xD000:
			assert i.target is not None
			queue.extend([a + i.size, i.target - 0x08000000])
		else:
			queue.append(a + i.size)
	instructions = [found[a] for a in sorted(found)]
	calls = sorted({int(x["text"].split()[-1], 16) for x in instructions if x["text"].startswith("bl ")})
	return {"entry_bus": hex(start + 0x08000000), "instructions": instructions,
		"direct_call_targets": [hex(x) for x in calls], "unresolved_control_edges": exits,
		"instruction_bytes_sha256": sha(b"".join(bytes.fromhex(x["bytes"]) for x in instructions)),
		"scope": "Direct CFG only; callees are separate evidence, not automatically certified"}


def main():
	prior_gate = json.loads((ROOT / "reverse_engineering/hawker_final_gate_evidence.json").read_text(encoding="utf-8"))
	prior_dep = json.loads((ROOT / "reverse_engineering/hawker_dependency_resolution_evidence.json").read_text(encoding="utf-8"))
	protected = {ROOT / p for p in prior_gate["protected_after"]}
	# Preserve existing research, scripts and manifests as well as game artifacts.
	for folder in ("tools", "reverse_engineering", "session_handoffs", "tomatotrans-1.1.1/asm"):
		protected.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and
			p.suffix.lower() in {".py", ".asm", ".json", ".md", ".bat"} and
			p.name not in {"hawker_stage1_evidence.json", "hawker_stage1.md"})
	before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(protected)}
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED
	assert all(before[p.replace("\\", "/")] == digest for p, digest in prior_gate["protected_after"].items())
	traces = {name: native_function(r, start) for name, start in ROOTS.items()}
	# Exact staged-argument and return-slot witnesses; offsets are file offsets.
	witnesses = {
		"clicked_slot_store": (0x697C8, "0d 48  c6 81"),
		"fetch_staged_cursor": (0x2254C, "c8 6a d8 60 05 78 0d 76 01 30 d8 60 c8 62"),
		"predecode_argument_cursor": (0x2248C, "41 46 cc 62"),
		"FD2F_save_return": (0x2898C, "00 68 08 60"),
		"record_clear_length": (0x71CA0, "1c 20 70 60"),
	}
	# Report these bytes directly; do not silently trust expected mnemonics.
	witness_data = []
	for name, (offset, expected) in witnesses.items():
		n = len(bytes.fromhex(expected))
		actual = r[offset:offset+n]
		witness_data.append({"name": name, "bus": hex(0x08000000+offset), "actual_bytes": actual.hex(" "),
			"expected_bytes": expected, "matches": actual == bytes.fromhex(expected)})
	assert all(x["matches"] for x in witness_data)
	shared = prior_dep["exchange_commands"]
	sites = [int(c["bus"], 16) for c in shared if c["bytes"] == "fe 31 03 01"]
	assert len(sites) == 10
	assert all(r[p-0x08000000:p-0x08000000+4] == bytes.fromhex("fe 31 03 01") for p in sites)
	assert not any(c["bytes"].startswith("fd 2f ") for c in shared)
	after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(protected)}
	assert before == after
	print(json.dumps({"source": SOURCE.relative_to(ROOT).as_posix(), "sha256": EXPECTED,
		"address_domain": "English cumulative ROM; RAM addresses explicitly distinguished",
		"native_functions": traces, "exact_witnesses": witness_data,
		"FE31_sites": [hex(x) for x in sites], "next_ROM_PC_guards": [hex(x+4) for x in sites],
		"shared_contains_nested_FD2F": False,
		"staged_cursor_before_fetch": "0x030039D9", "after_first_fetch": "0x030039DA",
		"after_second_fetch": "0x030039DB", "active_event_PC": "u32(0x03003AD8 + 28*context)",
		"candidate_saved_return": "u32(0x03003ADC + 28*context)",
		"scratch_status": "BLOCKED: deferred callback and concurrent-event alias closure incomplete",
		"adapter_status": "BLOCKED: saved-return ownership design identified; transitive lifetime unclosed",
		"protected_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "ROM_writes": 0, "runtime_performed": False}, indent=2))


if __name__ == "__main__":
	main()
