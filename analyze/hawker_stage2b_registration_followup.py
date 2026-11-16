"""Read-only, bounded actor identity/registration audit; JSON stdout only.

No Gate A replay, ROM construction, save mutation, or emulator operation.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

from hawker_placement_safety import ROOT, SOURCE, EXPECTED
from hawker_stage1 import native_function
from hawker_stage2 import commands, window
from thumb_inspect import decode

BUS = 0x08000000
NATIVE_SCOPES = ((0, 0xF9000), (0x7F0000, 0x800000))
EVENT_SCOPE = (0xF9000, 0x15BA3C)


def sha(b):
	return hashlib.sha256(b).hexdigest()


def hx(n):
	return f"0x{n:08X}"


def snapshot():
	return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
		for p in sorted(ROOT.rglob("*")) if p.is_file()
		and ".git" not in p.parts and "__pycache__" not in p.parts
		and p.name not in {"hawker_stage2b_registration_followup.md", "hawker_stage2b_registration_followup_evidence.json"}
		and (p.suffix.lower() in {".gba", ".sav", ".py", ".md", ".json", ".asm", ".inc", ".bat"}
			or re.fullmatch(r"\.ss\d.*", p.suffix.lower()) or "savestates" in p.parts)}


def occurrences(r, needle, start, end):
	p, result = start, []
	while True:
		p = r.find(needle, p, end)
		if p < 0:
			return result
		result.append(p)
		p += 1


def checkpoint_tail(path):
	b = path.read_bytes()
	assert b[:8] == b"\x89PNG\r\n\x1a\n"
	p, state = 8, None
	while p < len(b):
		n = struct.unpack_from(">I", b, p)[0]
		tag, payload = b[p+4:p+8], b[p+8:p+8+n]
		assert zlib.crc32(tag+payload) & 0xFFFFFFFF == struct.unpack_from(">I", b, p+8+n)[0]
		if tag == b"gbAs":
			state = zlib.decompress(payload)
		p += n + 12
	assert state is not None and len(state) == 0x61000
	assert struct.unpack_from("<I",state)[0] == 0x01000007
	return {"path":path.relative_to(ROOT).as_posix(),"sha256":sha(b),
		"bank_tail_03003280_through_3286":state[0x1C280:0x1C287].hex(" "),
		"candidate_bits":state[0x1C286] & 0xC0,
		"scope":"Existing serialized IWRAM snapshot, not gameplay or an emulator load"}


def audit():
	before = snapshot()
	previous_b = json.loads((ROOT/"reverse_engineering/hawker_stage2b_evidence.json").read_text(encoding="utf-8-sig"))
	for p,h in previous_b["protected_after"].items():
		assert sha((ROOT/p).read_bytes()) == h
		before[p] = h
	assert sha((ROOT/"tools/analyze/hawker_stage2b.py").read_bytes()) == previous_b["analyzer_sha256"]
	assert sha((ROOT/"reverse_engineering/hawker_stage2b.md").read_bytes()) == previous_b["report_sha256"]
	prior = json.loads((ROOT/"reverse_engineering/hawker_stage2_evidence.json").read_text(encoding="utf-8"))
	assert prior["gates"]["A"] == "PASS"
	assert all(before[p] == h for p,h in prior["protected_after"].items())
	r = SOURCE.read_bytes()
	assert len(r) == 0x1000000 and sha(r) == EXPECTED
	# Revalidate only registration/flag instructions used from the prior evidence.
	for name in ("actor_loader", "actor_id_read_wrapper", "bit_reader", "actor_flag_set_wrapper",
		"actor_flag_clear_wrapper", "interaction_dispatch", "FD53_actor_flag_set",
		"FD54_actor_flag_clear", "FD5B_actor_flag_branch", "FD5C_actor_flag_branch"):
		for ins in prior["native"][name]["instructions"]:
			a = int(ins["bus"],16)-BUS
			assert r[a:a+len(bytes.fromhex(ins["bytes"]))] == bytes.fromhex(ins["bytes"])
	# Fixed mutator entry points; census is bounded to native code and translated pool.
	targets = {0x0806AFB8,0x0806B02C,0x0806B0B8}
	calls = []
	for a,b in NATIVE_SCOPES:
		for p in range(a,b-3,2):
			if struct.unpack_from("<H",r,p)[0] & 0xF800 == 0xF000:
				i = decode(r,p)
				if i.target in targets:
					calls.append({"file":hx(p),"bus":hx(p+BUS),"target":hx(i.target),"bytes":i.raw.hex(" ")})
	assert [int(c["file"],16) for c in calls] == [0x276FC,0x27720,0x2778C,0x277C0,0x344A8,0x69C22,0x69CAA,0x69D42]
	bank_literals = [p for a,b in NATIVE_SCOPES for p in occurrences(r,struct.pack("<I",0x03003107),a,b)]
	assert bank_literals == [0x2F120,0x2F62C,0x32AD0,0x6B028,0x6B0B4,0x6B140,0x75FA0,0x762D8]
	# Close the generic bit-core callers as well: a different wrapper could otherwise
	# reach the actor bank without calling one of the three actor-bank wrappers.
	core_calls = []
	for a,b in NATIVE_SCOPES:
		for p in range(a,b-3,2):
			if struct.unpack_from("<H",r,p)[0] & 0xF800 == 0xF000:
				i = decode(r,p)
				if i.target in {0x08069F60,0x08069F8C,0x08069FBC}:
					core_calls.append({"bus":hx(p+BUS),"target":hx(i.target)})
	core_bases = {0x2853E:0x03003A0D,0x2857A:0x03003A0D,
		0x29CF2:0x0200EF6C,0x4EAA2:0x0200EF6C,0x6993C:0x03003E71,
		0x6AE5E:0x030032E7,0x6AEDE:0x030032E7,0x6AF6A:0x030032E7,
		0x6AFEA:0x03003107,0x6B06A:0x03003107,0x6B0F6:0x03003107,
		0x75AC6:0x0200EF6C}
	assert {int(c["bus"],16)-BUS for c in core_calls} == set(core_bases)
	for c in core_calls:
		base = core_bases[int(c["bus"],16)-BUS]
		c["base"] = hx(base)
		c["possible_byte_range_exclusive"] = [hx(base),hx(base+0x2000)]
		assert base == 0x03003107 or not base <= 0x03003286 < base+0x2000
	function_pointer_census = {}
	for target in (*targets,0x08069F60,0x08069F8C,0x08069FBC):
		ps = [p for a,b in (*NATIVE_SCOPES,EVENT_SCOPE,(0x62B4FC,0x62C250))
			for p in occurrences(r,struct.pack("<I",target|1),a,b)]
		assert not ps
		function_pointer_census[hx(target|1)] = ps
	# Conservative all-byte opcode census: negative findings do not depend on a
	# possibly incomplete instruction-boundary parser. The domain is event scripts,
	# actor records and event tables, ending before the tileset-pointer table.
	flag_sites = {}
	for op in (0x53,0x54,0x5B,0x5C):
		sites = [{"bus":hx(p+BUS),"file":hx(p),"id":hex(struct.unpack_from("<H",r,p+2)[0]),
			"bytes":r[p:p+4].hex(" ")}
			for p in occurrences(r,bytes((0xFD,op)),*EVENT_SCOPE)]
		assert all(int(s["id"],16) < 0xB9C for s in sites)
		flag_sites[f"FD{op:02X}"] = sites
	assert [len(flag_sites[k]) for k in ("FD53","FD54","FD5B","FD5C")] == [5,425,80,0]
	indirect = [{"bus":hx(p+BUS),"bytes":r[p:p+6].hex(" "),
		"family":r[p+2],"command":r[p+3]}
		for p in occurrences(r,b"\xfd\x84",*EVENT_SCOPE)]
	assert len(indirect) == 25 and all(s["family"] == 0 for s in indirect)
	# Established cumulative addition is bytecode, not native code. It has no actor
	# bank command; scratch writes are bounded by the native scratch resolver.
	assert r[0x800000:0x800015] == bytes.fromhex("fe 49 fe 53 6b fd 0b 1a 83 00 fd 0b 1c 1b 00 fd 30 33 4b 12 08")
	# Reuse the whole-ROM fingerprint; do not repeat allocation/relocation research.
	ids, actor_rows, init_pointers, defaults = [], [], set(), []
	for mid in range(494):
		rec = 0x62D3E4+28*mid
		b = struct.unpack_from("<I",r,rec+20)[0]-BUS
		ep = struct.unpack_from("<I",r,rec+16)[0]-BUS
		default = struct.unpack_from("<I",r,ep)[0]
		defaults.append(default)
		for k in range(15):
			a = b+0x70+16*k
			if r[a] == 255:
				break
			ident = struct.unpack_from("<H",r,a+14)[0]
			init = struct.unpack_from("<I",r,a+6)[0]
			ids.append(ident)
			if init:
				init_pointers.add(init)
			actor_rows.append({"map":hex(mid),"slot":k+1,"id":hex(ident),"file":hx(a)})
	assert len(ids) == 2987 and max(ids) == 0xB9B
	assert not {0xBFE,0xBFF}.intersection(ids)
	assert all(BUS+EVENT_SCOPE[0] <= p < BUS+EVENT_SCOPE[1] for p in init_pointers)
	assert all(p == 0 or BUS+EVENT_SCOPE[0] <= p < BUS+EVENT_SCOPE[1] for p in defaults)
	dups = Counter(ids)
	duplicate_examples = [{"id":hex(i),"records":[a for a in actor_rows if int(a["id"],16)==i]}
		for i in sorted(dups) if dups[i]>1][:3]
	roots = {"FD53":0x276E8,"FD54":0x2770C,"FD5B":0x27778,"FD5C":0x277AC,
		"flag_read":0x6AFB8,"flag_set":0x6B02C,"flag_clear":0x6B0B8,
		"bit_read":0x69F60,"bit_set":0x69F8C,"bit_clear":0x69FBC,
		"pickup_interaction":0x69C0C,"battle_actor_claim":0x69D14,
		"contact_interaction":0x69810,"ordinary_interaction":0x6971C,
		"new_game_clear":0x32984,"actor_loader":0x3411C,
		"room_descriptor_binding":0x3F8A4,"actor_initializer_registration":0x3F990,
		"visibility_helper":0x65DC0,"event_constructor":0x6AAA0,
		"event_clear":0x71C58,"event_reset_all":0x694D4,
		"event_reset_bridge":0x71C04,"map_transition":0x2C1F0,
		"normal_map_entry":0x31A88,"actor_runtime_reset":0x35148,
		"map_special_entry":0x37054,"initializer_mode":0x23C74,
		"initializer_marker_5C":0x24290,"FD84":0x28490}
	roots.update({"non_actor_flags_set":0x28518,"non_actor_flags_clear":0x28554,
		"main_flag_read":0x6AE2C,"main_flag_set":0x6AEA0,"main_flag_clear":0x6AF2C})
	native = {n:native_function(r,p) for n,p in roots.items()}
	windows = {"actor_bank_save":window(r,0x2EF0E,0x2EF36),
		"actor_bank_load":window(r,0x2F48A,0x2F4B4),
		"actor_bank_backup":window(r,0x75D92,0x75DBE),
		"actor_bank_restore":window(r,0x7612E,0x76158),
		"zero_source_r8":window(r,0x3298C,0x329A4),
		"zero_bank_and_neighbor":window(r,0x32A12,0x32A3E),
		"CpuFastSet_trampoline":window(r,0x942E0,0x942E4)}
	windows.update({"other_bit_set_base":window(r,0x4EA98,0x4EAA6),
		"other_bit_read_base":window(r,0x29CD8,0x29CF6),
		"contact_bit_read_base":window(r,0x69932,0x69940),
		"menu_bit_read_base":window(r,0x75ABE,0x75ACA)})
	init_commands = commands(r,0x101FCF,0x102004)
	assert init_commands[-1][2] == bytes.fromhex("fd 30 d2 1f 10 08")
	assert set(k for p,k,b in init_commands) == {(0,0x2B),(0,0x5C),(0xFD,0x29),
		(0xFD,0x15),(0,0x0C),(0,0x2E),(0,0x33),(0xFD,0x30)}
	registrations = []
	for mid, slot, ident, xy, gi, pi, block, wrapper in (
		(0x5F,7,0xBFE,(25,5),7,7,0x8006F8,0x80037C),
		(0x4D,8,0xBFF,(14,6),5,6,0x8007E8,0x8006E8)):
		old = next(m for m in prior["maps"] if int(m["map"],16)==mid)
		for row in old["original_actors"]:
			a = int(row["file"],16)
			assert r[a:a+16] == bytes.fromhex(row["bytes"])
		# Manifest record, not an inserted payload or a generated ROM.
		proposed = bytes((0x29,gi,(pi<<4)|2,*xy,0))+struct.pack("<IIH",0x08101FCF,wrapper+BUS,ident)
		assert len(proposed) == 16
		registrations.append({"map":hex(mid),"slot":slot,"id":hex(ident),
			"candidate_id_status":"SAFE_FOR_SPECIFIED_ORDINARY_NPC_REGISTRATION",
			"record_file":hx(block+0x70+16*(slot-1)),"record_bus":hx(block+BUS+0x70+16*(slot-1)),
			"expected_destination":"ff repeated 16","candidate_record_bytes":proposed.hex(" "),
			"record_status":"Statically specified registration; construction remains separately authorized and gated by C/D",
			"required_control_correction":{"template":"28","candidate":"29","reason":"bit0 must be set for initial visible/active registration"},
			"runtime_actor_RAM":hx(0x03001BDC+48*slot),"event_context_RAM":hx(0x03003AD4+28*slot),
			"persistent_RAM":"0x03003286","mask":hex(1<<(ident&7)),"decoded_save_offset":"0x284",
			"initializer_bus":"0x08101FCF","interaction_bus":hx(wrapper+BUS),
			"graphics_slot":gi,"palette_slot":pi,"map_pointer_operation":old["pointer_operation"],
			"header_graphics_operation":old["graphics_header_operation"],"header_palette_operation":old["palette_header_operation"],
			"existing_actors":old["original_actors"],"existing_header":old["header_expected_bytes"]})
	tails = [checkpoint_tail(ROOT/p) for p in ("savestates/after_kaizo_100_complete.ss0","savestates/before_oystown.ss0")]
	assert all(t["candidate_bits"] == 0 for t in tails)
	after = snapshot()
	for p in previous_b["protected_after"]:
		after[p] = sha((ROOT/p).read_bytes())
	assert before == after
	return {"decision":"GATE B PASS — ACTOR REGISTRATION SAFE",
		"previous_stage2b_preserved":True,
		"previous_stage2b_evidence_sha256":sha((ROOT/"reverse_engineering/hawker_stage2b_evidence.json").read_bytes()),
		"analyzer_path":Path(__file__).relative_to(ROOT).as_posix(),"analyzer_sha256":sha(Path(__file__).read_bytes()),
		"preservation_incident":"An initial analyzer-path collision was recovered from its creation/edit log and restored to the exact prior evidence hash. Earlier report/evidence were not overwritten. New work uses distinct follow-up paths.",
		"source":SOURCE.relative_to(ROOT).as_posix(),"source_sha256":EXPECTED,
		"scope":"Actor flag interpretation, explicit mutators, reset/save mapping and registration lifecycle. Gate A not replayed.",
		"native_search_scopes_file_exclusive":[[hx(a),hx(b)] for a,b in NATIVE_SCOPES],
		"script_and_registration_search_scope_file_exclusive":[hx(x) for x in EVENT_SCOPE],
		"search_limitation":"Conservative opcode census includes data false positives. Combined with fixed immediate operand decoding, FD84 family classification, explicit native core callers, source-record inventory and reset/save data flow. Excludes corrupt scripts, arbitrary PC/RAM corruption and edited save files; not runtime verification. No whole-ROM scan.",
		"bank_wrapper_direct_calls":calls,"bank_base_literal_slots":[hx(x+BUS) for x in bank_literals],
		"generic_bit_core_calls":core_calls,"thumb_function_pointer_census":function_pointer_census,
		"flag_sites":flag_sites,"FD84_sites":indirect,
		"actor_inventory":{"map_count":494,"actor_count":len(ids),"max_id":hex(max(ids)),
			"BFE_absent":True,"BFF_absent":True,"initializer_roots_in_scoped_bank":True,
			"map_default_roots_in_scoped_bank":True,"duplicate_id_examples":duplicate_examples},
		"native":native,"native_windows":windows,
		"initializer":{"file_range_exclusive":["0x00101FCF","0x00102004"],"sha256":sha(r[0x101FCF:0x102004]),
			"commands":[{"bus":hx(p+BUS),"bytes":raw.hex(" ")} for p,k,raw in init_commands],
			"loop_target":"0x08101FD2","5C_is_not_termination":True},
		"new_game_zero":{"actor_clear_nominal_destination":"0x03003107","control":"0x01000060",
			"next_variable_clear_nominal_destination":"0x03003287","control_next":"0x01000018",
			"word_aligned_effective_ranges_exclusive":[["0x03003104","0x03003284"],["0x03003284","0x030032E4"]],
			"candidate_byte_zeroed_by_neighbor_clear":True,
			"external_primary_source":"https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/hle-bios.s#L243-L270",
			"alignment_primary_source":"https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/memory.c#L1500-L1530"},
		"existing_snapshot_samples":tails,"registration_manifest":registrations,
		"ownership_argument":["All original actor IDs are below 0B9C; scripted actor-bank operands in the bounded event/registration domain are also below 0B9C.",
			"All 25 FD84 sites in that domain dispatch family00, so none dynamically supplies FD53/54/5B/5C operands.",
			"Additional native setters use the selected pickup/battle record ID; proposed ordinary records have both relevant class bits clear and neither their initializer nor exchange initiates pickup/battle registration.",
			"All generic bit-core direct callers select the actor bank through the three known wrappers or a provably disjoint base, even with the full unsigned16-bit ID range.",
			"New-game clears establish zero; ordinary save/load and temporary backup/restore preserve the entire byte. Masked operations on other IDs preserve the two chosen bits."],
		"remaining_gate_B_blocker":None,
		"gate_C_resolved":"slot/index capacity, initial hidden-state correction, per-actor initializer binding, normal entry runtime reset and transition event reset",
		"gate_D_resolved":"record graphics/palette bindings and normal entry resource-header reload; initializer extent/loop clarified",
		"protected_before":before,"protected_after":after,"protected_count":len(before),"protected_unchanged":True,
		"ROM_writes":0,"runtime_performed":False,"generated_ROM":False}


if __name__ == "__main__":
	json.dump(audit(),sys.stdout,indent=2)
	print()
