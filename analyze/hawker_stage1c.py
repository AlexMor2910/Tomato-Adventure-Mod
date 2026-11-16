"""Read-only symbolic relocation audit of the bounded Hawker interaction.

No ROM mutation, payload byte generation, placement address selection or emulator.
Compares parameterized command graphs, not constructed ROMs or runtime behavior.
"""
from collections import Counter
from functools import lru_cache
import json
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha
from pre_oystown_progression import decode_commands
from hawker_stage1 import native_function

START, END = 0x08107E81, 0x081081DA
# Opcode-typed pointer fields, measured from the start of each command.
CODE_POINTERS = {
	(0xFE, 0x01): 3, (0xFD, 0x30): 2, (0xFD, 0x35): 4,
	(0xFD, 0x3B): 4, (0xFD, 0x45): 2, (0xFE, 0x55): 4,
	(0xFE, 0x7A): 2, (0xFE, 0xB5): 2, (0xFE, 0xB6): 2, (0xFE, 0xB7): 2,
}
DATA_POINTERS = {(0xFE, 0xBC): 2, (0xFE, 0xC8): 2, (0xFE, 0x66): 2}
OTHER_OPS = {(0, 0x2F), (0xFD, 0x84), (0xFD, 0x00), (0xFD, 0x1F),
	(0xFD, 0x7D), (0xFE, 0x31), (0xFE, 0x5C), (0xFE, 0xB0),
	(0xFE, 0xC0), (0xFE, 0xC1)}


def family_op(raw):
	return (raw[0], raw[1]) if raw[0] in (0xFD, 0xFE) else (0, raw[0])


def audit():
	prior = {}
	for name in ("hawker_stage1_evidence", "hawker_stage1_dialogue_evidence", "hawker_stage1b_evidence"):
		prior[name] = json.loads((ROOT / "reverse_engineering" / (name+".json")).read_text(encoding="utf-8"))
	paths = {ROOT / p for p in prior["hawker_stage1b_evidence"]["protected_after"]}
	for folder in ("tools", "reverse_engineering", "session_handoffs"):
		paths.update(p for p in (ROOT / folder).rglob("*") if p.is_file() and
			p.suffix.lower() in {".py", ".asm", ".md", ".json", ".bat"} and
			p.name not in {"hawker_stage1c.md", "hawker_stage1c_evidence.json"})
	before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}
	assert all(before[p] == h for p, h in prior["hawker_stage1b_evidence"]["protected_after"].items())
	r = SOURCE.read_bytes()
	assert len(r) == 0x1000000 and sha(r) == EXPECTED
	commands, boundary = decode_commands(r, START-0x08000000, END-0x08000000)
	assert boundary == "exact scoped end"
	known = json.loads((ROOT / "reverse_engineering/hawker_dependency_resolution_evidence.json").read_text())
	assert commands == known["exchange_commands"] and len(commands) == 164
	nodes, pointer_fields, edges, actors, exits = {}, [], {}, [], []
	for c in commands:
		address, raw = int(c["bus"], 16), bytes.fromhex(c["bytes"])
		key = family_op(raw)
		assert key in CODE_POINTERS or key in DATA_POINTERS or key in OTHER_OPS, key
		off = address-START
		nodes[off] = {"opcode": list(key), "bytes": raw.hex(" "), "length": len(raw)}
		if key in CODE_POINTERS or key in DATA_POINTERS:
			pos = (CODE_POINTERS | DATA_POINTERS)[key]
			assert pos+4 == len(raw)
			p = int.from_bytes(raw[pos:pos+4], "little")
			kind = "internal_code" if key in CODE_POINTERS else "external_dialogue_data"
			assert (START <= p < END) == (kind == "internal_code")
			pointer_fields.append({"command_bus": c["bus"], "command_offset": off,
				"field_byte": pos, "field_bus": hex(address+pos), "kind": kind,
				"original_target": hex(p), "target_offset": p-START if kind == "internal_code" else None})
		if key == (0xFE, 0x31):
			assert raw == bytes.fromhex("fe 31 03 01")
			actors.append({"command_bus": c["bus"], "operand_offset": off+2})
		if key == (0xFD, 0x7D):
			edges[off] = []
			exits.append({"offset": off, "kind": "native_FD7D_end_or_external_continuation"})
		elif key == (0, 0x2F):
			assert address == 0x08107E8E and raw == bytes.fromhex("2f 00")
			edges[off] = []
			exits.append({"offset": off, "kind": "player_continuation_reaches_FE01_boundary"})
		elif key in CODE_POINTERS:
			pos = CODE_POINTERS[key]
			target = int.from_bytes(raw[pos:pos+4], "little")-START
			edges[off] = [target] if key == (0xFD, 0x30) else [off+len(raw), target]
		else:
			edges[off] = [off+len(raw)]
	assert len(actors) == 10
	assert Counter(p["kind"] for p in pointer_fields) == {"internal_code": 77, "external_dialogue_data": 28}
	assert all(q in nodes for successors in edges.values() for q in successors)
	seen, todo = set(), [0]
	while todo:
		p = todo.pop()
		if p not in seen:
			seen.add(p)
			todo.extend(edges[p])
	unreached = sorted(set(nodes)-seen)
	assert [START+p for p in unreached] == [0x081081A8, 0x081081AC, 0x081081B2]
	# Detect bytecode cycles and count conservative paths. Conditions are independent
	# nondeterministic edges, deliberately overapproximating attainable game states.
	visiting = set()
	@lru_cache(None)
	def path_counts(p):
		assert p not in visiting, "Cycle requires a different path proof"
		visiting.add(p)
		counts = Counter()
		if not edges[p]:
			counts[0] = 1
		else:
			for q in edges[p]:
				counts.update(path_counts(q))
		visiting.remove(p)
		attempt = nodes[p]["opcode"] == [0xFE, 0x55]
		return Counter({n+int(attempt): count for n, count in counts.items()})
	paths_by_award_attempt = path_counts(0)
	assert max(paths_by_award_attempt) == 1
	for p in nodes:
		path_counts(p)  # Also classify retained blocks without a local inbound edge.
	# Symbolic projection covers every source byte. Only typed pointer fields and
	# the ten actor operands become parameters. No relocated binary is generated.
	ptr_by_off = {p["command_offset"]: p for p in pointer_fields}
	def normalized_view(actor):
		result = []
		for off, n in sorted(nodes.items()):
			fields = list(bytes.fromhex(n["bytes"]))
			if off in ptr_by_off:
				p = ptr_by_off[off]
				value = ["LOCAL", p["target_offset"]] if p["kind"] == "internal_code" else ["DATA", p["original_target"]]
				fields[p["field_byte"]:p["field_byte"]+4] = [value]*4
			if n["opcode"] == [0xFE, 0x31]:
				assert fields[2] == 3
				# Relate the one intended actor substitution to its canonical symbol.
				fields[2] = ["INSTANCE_ACTOR", actor]
			result.append([off, fields, edges[off]])
		return result
	views = {str(actor): normalized_view(actor) for actor in (3, 7, 8)}
	canonical = json.dumps(views["3"], sort_keys=True).replace('["INSTANCE_ACTOR", 3]', '["INSTANCE_ACTOR", "S"]')
	for actor in (7, 8):
		assert json.dumps(views[str(actor)], sort_keys=True).replace(f'["INSTANCE_ACTOR", {actor}]', '["INSTANCE_ACTOR", "S"]') == canonical
	indirect = [c for c in commands if c["bytes"].startswith("fd 84")]
	assert indirect == [{"bus": "0x08107E88", "bytes": "fd 84 00 36 06 08"}]
	assert not any(family_op(bytes.fromhex(c["bytes"])) in {(0xFD, 0x2F), (0xFD, 0x31), (0xFD, 0x75), (0xFD, 0x7C)} for c in commands)
	rewards = []
	for idx, c in enumerate(commands):
		raw = bytes.fromhex(c["bytes"])
		if raw[:2] == b"\xfe\x55":
			assert raw[2:4] == b"\x37\x02"
			tail = commands[idx+1:idx+5]
			assert [bytes.fromhex(t["bytes"])[:2] for t in tail] == [b"\xfe\xb0", b"\xfe\x66", b"\xfe\xc1", b"\xfd\x7d"]
			rewards.append({"bus": c["bus"], "item": 0x37, "quantity": 2,
				"native_nonzero_status_target": hex(int.from_bytes(raw[4:8], "little")),
				"fallthrough_gauge_reset_character": bytes.fromhex(tail[2]["bytes"])[2]})
	assert len(rewards) == 5
	wrappers = []
	for start in (0x102D27, 0x102D37, 0x102D47, 0x102D57):
		cs, end = decode_commands(r, start, start+16)
		assert end == "exact scoped end" and len(cs) == 4
		assert bytes.fromhex(cs[2]["bytes"]) == b"\xfd\x2f" + struct.pack("<I", START)
		assert cs[3]["bytes"] == "fd 7d"
		wrappers.append({"bus": hex(start+0x08000000), "bytes": r[start:start+16].hex(" ")})
	# Read only the existing allocation manifest. Do not designate any new space.
	am_path = ROOT / "tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f/manifest.json"
	am = json.loads(am_path.read_text())
	expansion = am["expansion"]
	assert expansion["reservation_bytes"] == 32
	payload = bytes.fromhex(expansion["payload"])
	assert r[0x800000:0x800000+len(payload)] == payload
	native = {}
	for name, start in {"FD35_condition_core": 0x29F90, "FD3B_condition": 0x2A43C,
		"FD45_condition": 0x2984C, "choice_condition": 0x25F1C,
		"FD75_external_resume_writer": 0x27E50}.items():
		native[name] = native_function(r, start)
	after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}
	assert before == after and sha(SOURCE.read_bytes()) == EXPECTED
	return {
		"status": "STAGE 1C — LOCALIZED IMPLEMENTATION FEASIBLE",
		"scope": "Symbolic command-graph feasibility; no payload or ROM constructed; runtime untested",
		"source": SOURCE.relative_to(ROOT).as_posix(), "source_sha256": EXPECTED,
		"source_extent_bus_exclusive": [hex(START), hex(END)], "source_extent_sha256": sha(r[START-0x08000000:END-0x08000000]),
		"source_bytes": END-START, "command_count": len(commands), "reachable_command_count": len(seen),
		"retained_without_local_inbound_edge": [hex(START+p) for p in unreached],
		"pointer_fields": pointer_fields, "actor_operand_fields": actors,
		"graph": [{"offset": p, "opcode": n["opcode"], "successors": edges[p]} for p,n in nodes.items()],
		"native_exits": exits, "bytecode_graph_acyclic": True,
		"conservative_paths_by_native_award_attempt_count": dict(paths_by_award_attempt),
		"symbolic_projection_sha256": sha(canonical.encode()), "normalized_symbolic_views_equal": True,
		"symbolic_relocation_rule": "For each typed internal pointer P, emit B+(P-08107E81); external data pointers unchanged",
		"proposed_instances": [{"map": "005F", "slot": 7, "FD01_X": 407, "FD02_Y": 111},
			{"map": "004D", "slot": 8, "FD01_X": 231, "FD02_Y": 127}],
		"existing_wrappers": wrappers, "fixed_indirect_command": indirect[0], "reward_sites": rewards,
		"native_evidence": native,
		"allocation": {"new_addresses_selected": False, "body_bytes_each": 857, "wrapper_bytes_each": 16,
			"two_instances_raw_bytes": 1746, "four_byte_padded_budget": 1752,
			"existing_Alessa_reservation_file_exclusive": ["0x00800000", "0x00800020"],
			"new_space_ownership_status": "NOT ALLOCATED; must be validated before construction"},
		"preserved_native_continuation_contract": "FD7D may end a general event or transfer through global 03003A20; not assumed always zero",
		"protected_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "ROM_writes": 0, "runtime_performed": False,
	}


if __name__ == "__main__":
	json.dump(audit(), sys.stdout, indent=2)
	print()
