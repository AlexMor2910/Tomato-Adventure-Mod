"""Read-only event ownership follow-up. JSON stdout; no ROM/patch construction.

Reuses prior CFG evidence and examines explicit lifecycle and alias dependencies.
Pointer searches are bounded to the known event-script/actor-record region.
"""
import json
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha
from hawker_stage1 import native_function


NEW_ROOTS = {
	"FD31_second_return_writer": 0x2A3B4,
	"FD0B_indirect_halfword_store": 0x2A2F4,
	"event_constructor": 0x6AAA0,
	"linked_context_completion": 0x226AC,
	"event_bit_read": 0x6A4F8,
	"scheduler_delay_update": 0x2224C,
	"queued_event_start": 0x21F70,
	"event_table_start": 0x71D2C,
	"FE55_capacity_continuation": 0x291D4,
	"item55_args": 0x25634,
	"item5C_args": 0x257C4,
	"item66_args": 0x29D98,
	"FD84_frontend": 0x28490,
	"FD84_size_decode": 0x29A20,
	"indirect_opcode_dispatch": 0x299D0,
	"menu_alt_dispatch": 0x6D51C,
	"menu_alt_prepare": 0x6D718,
	"menu_alt_poll": 0x6D544,
	"menu_alt_buffer": 0x6D600,
	"dialogue_buffer_shift": 0x6E68C,
	"dialogue_buffer_clear": 0x6E700,
	"dialogue_cursor_reset": 0x6E744,
	"dialogue_break": 0x6D030,
	"dialogue_break_prepare": 0x6D054,
	"dialogue_wait_update": 0x6D124,
	"dialogue_number_width": 0x6E93C,
	"dialogue_number_fallback": 0x6E998,
	"dialogue_name_copy": 0x2D34A,
	"dialogue_item_width": 0x2B1E0,
}


def load_evidence():
	a = json.loads((ROOT / "reverse_engineering/hawker_stage1_evidence.json").read_text(encoding="utf-8"))
	b = json.loads((ROOT / "reverse_engineering/hawker_stage1_dialogue_evidence.json").read_text(encoding="utf-8"))
	return a, b


def main():
	prior, dialogue = load_evidence()
	gate = json.loads((ROOT / "reverse_engineering/hawker_final_gate_evidence.json").read_text(encoding="utf-8"))
	paths = {ROOT / p for p in gate["protected_after"]}
	paths.update(ROOT / p for p in prior["protected_after"])
	for name in ("tools", "reverse_engineering", "session_handoffs"):
		paths.update(p for p in (ROOT / name).rglob("*") if p.is_file() and
			p.suffix.lower() in {".py", ".asm", ".md", ".json", ".bat"} and
			p.name not in {"hawker_stage1b_evidence.json", "hawker_stage1b.md"})
	before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}
	assert all(before[p] == h for p, h in gate["protected_after"].items())
	assert all(before[p] == h for p, h in prior["protected_after"].items())
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED
	traces = {name: native_function(r, off) for name, off in NEW_ROOTS.items()}
	# Decoder byte evidence must agree with both previous datasets, without rerunning
	# the already completed function inventories.
	for trace in list(prior["native_functions"].values()) + list(dialogue["menu_and_wait_helpers"].values()):
		for i in trace["instructions"]:
			a = int(i["bus"], 16) - 0x08000000
			b = bytes.fromhex(i["bytes"])
			assert r[a:a+len(b)] == b
	dispatch = {}
	for family, base, count in (("FD", 0x62BC30, 256), ("FE", 0x62B8B4, 223)):
		for op in range(count):
			p = struct.unpack_from("<I", r, base+4*op)[0]
			if p in {0x0802A3B5, 0x0802A2F5, 0x0802896D}:
				dispatch[f"{family}{op:02X}"] = {"slot_bus": hex(base+4*op+0x08000000), "value": hex(p)}
	assert set(dispatch) == {"FD0B", "FD2F", "FD31"}
	refs = {}
	for target in (0x08107E81, 0x08107E90, 0x08102D27, 0x08102D37, 0x08102D47, 0x08102D57):
		needle, positions, cursor = struct.pack("<I", target), [], 0xFC000
		while True:
			cursor = r.find(needle, cursor, 0x159C00)
			if cursor < 0:
				break
			positions.append(hex(cursor+0x08000000))
			cursor += 1
		refs[hex(target)] = positions
	assert len(refs[hex(0x08107E81)]) == 4
	assert all(len(refs[hex(p)]) == 1 for p in (0x08107E90, 0x08102D27, 0x08102D37, 0x08102D47, 0x08102D57))
	after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}
	assert before == after and sha(SOURCE.read_bytes()) == EXPECTED
	print(json.dumps({
		"source_sha256": EXPECTED, "native_functions": traces, "dispatch_identity": dispatch,
		"pointer_search_file_bounds_exclusive": ["0x000FC000", "0x00159C00"],
		"scoped_pointer_references": refs,
		"pointer_search_limitation": "Literal pointer occurrences only; not a complete dynamic-entry call graph",
		"saved_return": {"address": "0x03003ADC + 0x1C*context", "depth": 1,
			"writers": ["FD2F", "FD31", "event-record clear"],
			"writer_inventory_complete": False,
			"reader": "FD7C flag40 return path", "reader_clears_word": False,
			"ownership_conclusion": "Not an immutable NPC identity; rejected as a sufficient actor-ownership guard"},
		"scratch_alias_counterexample": {"script_bytes": "FD 0B 0E 00 00",
			"effect": "native FD0B can store halfword 0 at scratch+0E = 03003A32",
			"executed": False, "observed_in_live_Hawker_path": False,
			"meaning": "Refutes an engine-wide per-context preservation guarantee; not an observed gameplay failure"},
		"scratch_pointer_upper_bound": "03003A24 + 7F = 03003AA3; bounded-width access remains below 03003AD4",
		"static_dependency": "Reachable cross-context replacement/alias writes during a live exchange are not excluded",
		"status": "STAGE 1B BLOCKED — SPECIFIC STATIC DEPENDENCY REMAINS",
		"protected_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "ROM_writes": 0, "runtime_performed": False}, indent=2))


if __name__ == "__main__":
	main()
