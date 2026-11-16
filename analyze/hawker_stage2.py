"""Bounded Stage 2 specification audit. Never constructs a ROM or script copy.

Run: python -B tools/analyze/hawker_stage2.py
JSON goes to stdout; caller may save it to a NEW evidence file.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED
from hawker_stage1 import native_function
from thumb_inspect import decode

BUS = 0x08000000
START, END = 0x107E81, 0x1081DA


def sha(data):
	return hashlib.sha256(data).hexdigest()


def hx(n):
	return f"0x{n:08X}"


def load(name):
	return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))


def snapshot():
	# Include prior research/manifests/tool sources as well as all known game files.
	return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
		for p in sorted(ROOT.rglob("*")) if p.is_file()
		and ".git" not in p.parts and "__pycache__" not in p.parts
		and p.name not in {"hawker_stage2.md", "hawker_stage2_evidence.json"}
		and (p.suffix.lower() in {".gba", ".sav", ".py", ".md", ".json", ".asm", ".bat"}
			or re.fullmatch(r"\.ss\d.*", p.suffix.lower()) or "savestates" in p.parts)}


def window(r, start, end):
	ins, p = [], start
	while p < end:
		i = decode(r, p)
		assert p + i.size <= end
		ins.append({"bus": hx(i.address), "bytes": i.raw.hex(" "), "text": i.text})
		p += i.size
	return {"file_range_exclusive": [hx(start), hx(end)], "sha256": sha(r[start:end]),
		"instructions": ins, "confidence": "Confirmed static instructions"}


def commands(r, start, end):
	# Independent sequential decoder: use native length tables, no Stage 1C decoder.
	out, p = [], start
	while p < end:
		family = r[p]
		prefix = 2 if family in (0xFD, 0xFE) else 1
		op = r[p + 1] if prefix == 2 else family
		table = {0xFD: 0x62B815, 0xFE: 0x62B736}.get(family, 0x62B6C4)
		n = prefix + r[table + op]
		assert p + n <= end
		out.append((p, (family, op) if prefix == 2 else (0, op), r[p:p+n]))
		p += n
	assert p == end
	return out


def main():
	before = snapshot()
	prior = load("reverse_engineering/hawker_stage1c_evidence.json")
	assert all(before[p] == h for p, h in prior["protected_after"].items())
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED and len(r) == 0x1000000
	assert sha(r[START:END]) == prior["source_extent_sha256"]
	cs = commands(r, START, END)
	assert len(cs) == 164
	# Typed layouts independently transcribed from native argument contracts.
	local = {(0xFE, 1): 3, (0xFD, 0x30): 2, (0xFD, 0x35): 4,
		(0xFD, 0x3B): 4, (0xFD, 0x45): 2, (0xFE, 0x55): 4,
		(0xFE, 0x7A): 2, (0xFE, 0xB5): 2, (0xFE, 0xB6): 2, (0xFE, 0xB7): 2}
	external = {(0xFE, 0xBC): 2, (0xFE, 0xC8): 2, (0xFE, 0x66): 2}
	other = {(0, 0x2F), (0xFD, 0x84), (0xFD, 0), (0xFD, 0x1F),
		(0xFD, 0x7D), (0xFE, 0x31), (0xFE, 0x5C), (0xFE, 0xB0),
		(0xFE, 0xC0), (0xFE, 0xC1)}
	boundaries = {p for p, _, _ in cs}
	fields, actors, edges = [], [], {}
	for p, key, raw in cs:
		assert key in local or key in external or key in other
		if key in local or key in external:
			i = (local | external)[key]
			assert i + 4 == len(raw)
			v = int.from_bytes(raw[i:i+4], "little")
			assert (START + BUS <= v < END + BUS) == (key in local)
			if key in local:
				assert v - BUS in boundaries
			fields.append({"source_field_bus": hx(p + i + BUS), "source_field_file": hx(p+i),
				"field_offset": p + i - START, "original_bytes": raw[i:i+4].hex(" "),
				"original_target": hx(v), "internal": key in local,
				"target_offset": v - BUS - START if key in local else None})
		if key == (0xFE, 0x31):
			assert raw == bytes.fromhex("fe 31 03 01")
			actors.append({"source_field_bus": hx(p+2+BUS), "field_offset": p+2-START,
				"expected": "03"})
		if key in {(0xFD, 0x7D), (0, 0x2F)}:
			edges[p] = []
		elif key in local:
			v = int.from_bytes(raw[local[key]:], "little") - BUS
			edges[p] = [v] if key == (0xFD, 0x30) else [p+len(raw), v]
		else:
			edges[p] = [p+len(raw)]
	assert all(t in boundaries for ts in edges.values() for t in ts)
	assert sum(f["internal"] for f in fields) == 77 and len(fields) == 105 and len(actors) == 10
	old = {(int(f["field_bus"],16), int(f["original_target"],16)) for f in prior["pointer_fields"]}
	assert old == {(int(f["source_field_bus"],16), int(f["original_target"],16)) for f in fields}
	assert {f["field_offset"] for f in actors} == {f["operand_offset"] for f in prior["actor_operand_fields"]}
	assert [(p, raw.hex(" ")) for p, k, raw in cs if k == (0xFD, 0x84)] == [(0x107E88, "fd 84 00 36 06 08")]
	# Allocation ownership: actual expansion producer, pinned ancestor and descendant.
	adir = ROOT / "tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f"
	am = json.loads((adir / "manifest.json").read_text())
	ancestor = (adir / "alessa_recruitment_wrapper.gba").read_bytes()
	assert sha(ancestor) == am["output_sha256"]
	assert len(ancestor) == len(r) and am["expansion"]["reservation_bytes"] == 32
	builder = ROOT / "tools/patch/alessa_recruitment_wrapper.py"
	assert sha(builder.read_bytes()) == am["script_sha256"]
	assert ancestor[0x800020:] == b"\xff" * (len(ancestor)-0x800020)
	assert r[0x800020:] == ancestor[0x800020:]
	# All ranges half-open; storage chosen only for the unchanged candidate design.
	ranges = [("Namp_body",0x800020,0x800379),("Namp_body_padding",0x800379,0x80037C),
		("Namp_wrapper",0x80037C,0x80038C),("Mayonen_body",0x80038C,0x8006E5),
		("Mayonen_body_padding",0x8006E5,0x8006E8),("Mayonen_wrapper",0x8006E8,0x8006F8),
		("Namp_actor_block",0x8006F8,0x8007E8),("Mayonen_actor_block",0x8007E8,0x8008E8)]
	assert all(a % 4 == 0 for name, a, end in ranges if "padding" not in name)
	assert all(b == ranges[i+1][1] for i, (_,a,b) in enumerate(ranges[:-1]))
	alloc = [{"name": n,"file_range_exclusive":[hx(a),hx(b)],
		"bus_range_exclusive":[hx(a+BUS),hx(b+BUS)],"bytes":b-a,
		"expected_source": "ff repeated " + str(b-a), "expected_sha256":sha(r[a:b])}
		for n,a,b in ranges]
	instances, maps = [], []
	for mid, xy, slot, gi, pi, base, wrapper, dest, ident, x,y in (
		(0x5F,(25,5),7,7,7,0x800020,0x80037C,0x8006F8,0xBFE,407,111),
		(0x4D,(14,6),8,5,6,0x80038C,0x8006E8,0x8007E8,0xBFF,231,127)):
		manifest = []
		for f in fields:
			v = base + BUS + f["target_offset"] if f["internal"] else int(f["original_target"],16)
			manifest.append({**f, "destination_field_bus":hx(base+BUS+f["field_offset"]),
				"proposed_target":hx(v), "proposed_bytes":struct.pack("<I",v).hex(" ")})
		w = b"\xfd\x01" + struct.pack("<H",x) + b"\xfd\x02" + struct.pack("<H",y) + b"\xfd\x2f" + struct.pack("<I",base+BUS) + b"\xfd\x7d"
		instances.append({"map":hex(mid),"base_file":hx(base),"actor":slot,
			"pointer_manifest":manifest,"actor_manifest":[{**f,"destination_field_bus":hx(base+BUS+f["field_offset"]),"proposed":f"{slot:02x}"} for f in actors],
			"wrapper_file":hx(wrapper),"wrapper_proposed_bytes":w.hex(" "),
			"FE01_continuation_bus":hx(base+BUS+7),"FE01_body_bus":hx(base+BUS+15)})
		rec = 0x62D3E4+28*mid
		b = struct.unpack_from("<I",r,rec+20)[0]-BUS
		assert r[b+0x70+(slot-1)*16] == 255
		original = [{"slot":k+1,"file":hx(b+0x70+k*16),
			"bytes":r[b+0x70+k*16:b+0x80+k*16].hex(" ")} for k in range(slot-1)]
		assert struct.unpack_from("<I",r,b+4*gi)[0] == 0
		assert pi not in {r[b+0x72+k*16] >> 4 for k in range(slot-1)}
		cp = struct.unpack_from("<I",r,0x303950+4*mid)[0]-BUS
		width,height = r[rec+3:rec+5]
		neighborhood = [{"xy":[xx,yy],"base_collision":r[cp+yy*width+xx]}
			for yy in range(xy[1]-1,xy[1]+3) for xx in range(xy[0]-2,xy[0]+3)]
		maps.append({"map":hex(mid),"map_record_file":hx(rec),"map_record_bytes":r[rec:rec+28].hex(" "),
			"pointer_operation":{"file":hx(rec+20),"expected":r[rec+20:rec+24].hex(" "),"proposed":struct.pack("<I",dest+BUS).hex(" ")},
			"actor_block_source_file":hx(b),"actor_block_destination_file":hx(dest),
			"header_expected_bytes":r[b:b+0x70].hex(" "),"original_actors":original,
			"new_record_offset_in_block":0x70+(slot-1)*16,"terminator_offset_in_block":0x70+slot*16,
			"new_record_status":"BLOCKED: persistent ID ownership and initializer lifetime not certified",
			"candidate_persistent_id":hex(ident),"saved_flag_RAM":hx(0x3003107+(ident>>3)),"saved_flag_mask":hex(1<<(ident&7)),
			"graphics_header_operation":{"offset":4*gi,"expected":r[b+4*gi:b+4*gi+4].hex(" "),"proposed":"7c f7 13 08"},
			"palette_header_operation":{"offset":0x40+4*pi,"expected":r[b+0x40+4*pi:b+0x44+4*pi].hex(" "),"proposed":"cc c3 43 08"},
			"door_palette5_expected":r[b+0x54:b+0x58].hex(" ") if mid==0x4D else None,
			"dimensions":[width,height],"base_collision_neighborhood":neighborhood})
	# Exact native roots, selected from the open gates. Direct CFG only.
	roots = {"actor_loader":0x34244,"actor_id_read_wrapper":0x6AFB8,
		"bit_reader":0x69F60,"actor_flag_set_wrapper":0x6B02C,
		"actor_flag_clear_wrapper":0x6B0B8,"interaction_dispatch":0x6971C,
		"movement_scheduler":0x664A8,"collision_rectangles":0x3DF48,
		"FE06_deferred_actor_script":0x2A268,"FE89_completion":0x29E34,
		"main50_controller_parameters":0x23DB8,
		"FD53_actor_flag_set":0x276E8,"FD54_actor_flag_clear":0x2770C,
		"FD5B_actor_flag_branch":0x27778,"FD5C_actor_flag_branch":0x277AC}
	native = {n:native_function(r,a) for n,a in roots.items()}
	windows = {"actor_save_load":window(r,0x2F490,0x2F4B4),
		"actor_save_stage":window(r,0x2EF0E,0x2EF36),
		"actor_load_source":window(r,0x2F488,0x2F490),
		"actor_table_copy_capacity":window(r,0x34ED4,0x34F50)}
	scopes = {"Namp_blue_controller":(0x1130AF,0x1130CE),
		"Mayonen_default":(0x12667C,0x12669B),"Mayonen_deferred_controller":(0x128A95,0x128AB4),
		"Namp_default":(0x1149AB,0x1149C5),"Hawker_initializer":(0x101FCF,0x101FD2)}
	scripts = {n:[{"bus":hx(p+BUS),"bytes":raw.hex(" ")} for p,k,raw in commands(r,a,b)] for n,(a,b) in scopes.items()}
	# Baseline regression independently tied to retained manifests, not handoff prose.
	dm = load("tools/patch/output/detector-hp120-mit25/manifest.json")
	parent_path = ROOT / dm["source"]
	parent = parent_path.read_bytes()
	assert sha(parent) == dm["source_sha256"]
	diffs = [{"file":hx(i),"before":f"{a:02x}","after":f"{b:02x}"} for i,(a,b) in enumerate(zip(parent,r)) if a!=b]
	assert diffs == [{"file":"0x00638056","before":"87","after":"78"},{"file":"0x0063805A","before":"26","after":"19"}]
	km = json.loads((parent_path.parent / "manifest.json").read_text())
	assert all(r[int(op["file"],16)] == int(op["new"],16) for op in km["verification"]["differences"])
	stats = {n:[struct.unpack_from("<H",r,a)[0],struct.unpack_from("<H",r,b)[0]]
		for n,a,b in (("Detector",0x638056,0x63805A),("Rattlin_Dragon",0x637DAA,0x637DAE))}
	assert stats == {"Detector":[120,25],"Rattlin_Dragon":[262,54]}
	after = snapshot()
	assert before == after
	result = {"decision":"STAGE 2 BLOCKED — EXACT REMAINING GATES IDENTIFIED",
		"source":SOURCE.relative_to(ROOT).as_posix(),"source_sha256":EXPECTED,"source_bytes":len(r),
		"gates":{"A":"PASS","B":"BLOCKED","C":"BLOCKED","D":"BLOCKED","E":"BLOCKED"},
		"gate_scope":"A: allocation/relocation of specified candidate architecture. E structural exchange equivalence passes; complete regression gate depends on unresolved B/C/D integration safety.",
		"independent_script_audit":{"range_file_exclusive":[hx(START),hx(END)],"sha256":sha(r[START:END]),
			"commands":len(cs),"internal_pointers":77,"external_pointers":28,"actor_operands":10,
			"matches_stage1c":True,"all_bytes_decoded":True,"all_internal_targets_are_command_boundaries":True,
			"previous_graph_evidence_reused":prior["symbolic_projection_sha256"],
			"previous_reward_sites":prior["reward_sites"],"native_continuation_contract":prior["preserved_native_continuation_contract"]},
		"allocation":{"ranges":alloc,"origin_manifest":str((adir/"manifest.json").relative_to(ROOT)),
			"origin_rom_sha256":sha(ancestor),"producer_sha256":sha(builder.read_bytes()),
			"producer_matches_manifest":True,"origin_reserved_file_exclusive":[hx(0x800000),hx(0x800020)],
			"entire_expanded_suffix_matches_producer_owned_padding":True,"final_rom_size_unchanged":True,
			"limitations":"Ownership derives from pinned expansion producer and ancestor equality, not filler pattern. No pointer-shaped whole-ROM scan performed."},
		"instances":instances,"maps":maps,"native":native,"native_windows":windows,"bounded_scripts":scripts,
		"regression":{"parent_sha256":sha(parent),"parent_differences":diffs,"kaizo_ledger_bytes":len(km["verification"]["differences"]),
			"stats":stats,"header_complement_valid":r[0xBD]==(-sum(r[0xA0:0xBD])-0x19)&255},
		"protected_before":before,"protected_after":after,"protected_count":len(before),"protected_unchanged":True,
		"rom_writes":0,"runtime_performed":False,"generated_rom_or_private_script":False}
	json.dump(result,sys.stdout,indent=2,ensure_ascii=True)
	print()


if __name__ == "__main__":
	main()
