"""Read-only, bounded actor-registration audit. JSON stdout; no ROM writes.

Run with python -B. Native xrefs are candidates in an explicit code interval,
not an exhaustive executable-code or script-reachability proof.
"""
import hashlib
import json
import os
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED
from hawker_stage1 import native_function
from hawker_stage2 import commands, window
from thumb_inspect import decode

NEW = {"tools/analyze/hawker_stage2b.py", "reverse_engineering/hawker_stage2b.md",
	"reverse_engineering/hawker_stage2b_evidence.json"}
BUS = 0x08000000


def sha(b):
	return hashlib.sha256(b).hexdigest()


def snapshot():
	result = {}
	for directory, dirs, files in os.walk(ROOT):
		dirs[:] = sorted(set(dirs) - {".git", "__pycache__", "Ghidra", "mGBA"})
		for name in sorted(files):
			p = ROOT / directory / name
			rel = p.relative_to(ROOT).as_posix()
			keep = p.suffix.lower() in {".gba", ".sav", ".md", ".json", ".py",
				".asm", ".bat", ".txt", ".png", ".dat", ".bps", ".bin", ".bpp", ".pal"}
			keep = keep or p.suffix.lower().startswith(".ss") or "savestates" in p.parts
			if rel not in NEW and keep:
				result[rel] = sha(p.read_bytes())
	prior = json.loads((ROOT / "reverse_engineering/hawker_stage2_evidence.json").read_text())
	for name in prior["protected_after"]:
		if name not in result:
			result[name] = sha((ROOT / name).read_bytes())
	return result


def main():
	before = snapshot()
	old = json.loads((ROOT / "reverse_engineering/hawker_stage2_evidence.json").read_text())
	assert all(before[p] == h for p, h in old["protected_after"].items())
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED and len(r) == 0x1000000
	roots = {"operand_fetch": 0x22534, "bit_read": 0x69F60,
		"bit_set": 0x69F8C, "bit_clear": 0x69FBC,
		"actor_bit_read": 0x6AFB8, "actor_bit_set": 0x6B02C,
		"actor_bit_clear": 0x6B0B8, "FD53": 0x276E8, "FD54": 0x2770C,
		"FD5B": 0x27778, "FD5C": 0x277AC, "FD84": 0x28490,
		"FD84_prefix_length": 0x29A20, "FD84_dispatch": 0x299D0,
		"main_dispatch": 0x22AE8, "FD_dispatch": 0x247B4,
		"main2B": 0x23C74, "main_argument": 0x23AE8,
		"main5C": 0x24290,
		"actor_mode": 0x65E4C, "actor_activation": 0x65DC0,
		"actor_loader": 0x34244, "interaction": 0x6971C,
		"pickup_interaction": 0x69C0C, "deferred_actor_flag_set": 0x69D14,
		"reset": 0x32984}
	native = {n: native_function(r, a) for n, a in roots.items()}
	assert all(not v["unresolved_control_edges"] for v in native.values())
	assert struct.unpack_from("<I", r, 0x62B4FC + 4*0x2B)[0] == 0x08023C75
	assert r[0x63A01C:0x63A024] == bytes([1, 2, 4, 8, 16, 32, 64, 128])
	# Explicit native-code search domain. Data can decode as instructions: these
	# candidates do not prove absence of indirect/native/bulk writers elsewhere.
	targets = {BUS + a for n, a in roots.items() if n.startswith("actor_bit") or n.startswith("bit_")}
	xrefs, literals = [], []
	for p in range(0x21000, 0x72000, 2):
		h = int.from_bytes(r[p:p+2], "little")
		if h & 0xF800 not in (0xF000, 0x4800):
			continue
		i = decode(r, p)
		item = {"bus": hex(i.address), "bytes": i.raw.hex(" "), "text": i.text}
		if i.text.startswith("bl ") and i.target in targets:
			xrefs.append(item)
		if i.literal_value in (0x03003107, 0x03003286, 0x03003287):
			literals.append(item)
	# Bounded domain is the existing 494-entry map descriptor table only.
	actors, occurrences = [], {0xBFE: [], 0xBFF: []}
	for mid in range(494):
		b = struct.unpack_from("<I", r, 0x62D3E4 + 28*mid + 20)[0] - BUS
		assert 0 <= b < len(r)-0x170
		for k in range(15):
			a = b + 0x70 + 16*k
			if r[a] == 255:
				break
			ident = struct.unpack_from("<H", r, a+14)[0]
			actors.append(ident)
			if ident in occurrences:
				occurrences[ident].append({"map": hex(mid), "slot": k+1, "file": hex(a)})
	assert len(actors) == 2987
	template = r[0x14D4C4:0x14D4D4]
	assert template.hex(" ") == "28 03 32 00 00 00 cf 1f 10 08 27 2d 10 08 c9 05"
	manifest = []
	for m, slot, ident, gi, pi, xy, wrapper in (
		(old["maps"][0], 7, 0xBFE, 7, 7, (25, 5), 0x0880037C),
		(old["maps"][1], 8, 0xBFF, 5, 6, (14, 6), 0x088006E8)):
		b = int(m["actor_block_source_file"], 16)
		assert r[b:b+0x70].hex(" ") == m["header_expected_bytes"]
		for rec in m["original_actors"]:
			a = int(rec["file"], 16)
			assert r[a:a+16].hex(" ") == rec["bytes"]
		assert r[b+0x70+16*(slot-1)] == 255
		rec = bytearray(template)
		rec[1] = gi
		rec[2] = (pi << 4) | (rec[2] & 15)
		rec[3:5] = bytes(xy)
		struct.pack_into("<I", rec, 10, wrapper)
		struct.pack_into("<H", rec, 14, ident)
		dest = int(m["actor_block_destination_file"], 16)
		manifest.append({"map": m["map"], "slot": slot, "id": hex(ident),
			"status": "CONDITIONAL SPECIFICATION ONLY; ID OWNERSHIP UNPROVED; NOT APPROVED TO PATCH",
			"candidate_record_bytes": rec.hex(" "),
			"record_bus": hex(BUS+dest+0x70+16*(slot-1)),
			"runtime_actor_bus": hex(0x03001BDC+48*slot),
			"activation_byte_bus": hex(0x030028E1+slot),
			"occupancy_halfword_bus": hex(0x0300274C+4*slot),
			"interaction_position_bus": hex(0x03002820+4*slot),
			"persistent_byte": hex(0x03003107+(ident>>3)), "mask": hex(1<<(ident&7)),
			"decoded_save_byte_offset": hex(0x105+(ident>>3)),
			"map_pointer_edit": m["pointer_operation"],
			"graphics_header_edit": m["graphics_header_operation"],
			"palette_header_edit": m["palette_header_operation"],
			"original_actors": m["original_actors"],
			"original_header_bytes": m["header_expected_bytes"],
			"terminator_bus": hex(BUS+dest+0x70+16*slot),
			"terminator_proposed_bytes": "ff " + "00 "*14 + "00",
			"expected_destination_bytes": "ff repeated 16",
			"event_table_bus": hex(struct.unpack_from("<I", r, int(m["map_record_file"],16)+16)[0])})
	scripts = {n: [{"bus": hex(p+BUS), "bytes": raw.hex(" ")}
		for p, _, raw in commands(r, a, b)] for n, (a,b) in {
			"initializer": (0x101FCF, 0x101FD2),
			"Namp_default": (0x1149AB, 0x1149C5),
			"Mayonen_default": (0x12667C, 0x12669B)}.items()}
	assert scripts["initializer"] == [{"bus": "0x8101fcf", "bytes": "2b 01"},
		{"bus": "0x8101fd1", "bytes": "5c"}]
	after = snapshot()
	assert before == after
	return {"decision": "GATE B BLOCKED — SPECIFIC ACTOR DEPENDENCIES UNRESOLVED",
		"analyzer_sha256": sha((ROOT / "tools/analyze/hawker_stage2b.py").read_bytes()),
		"report_sha256": sha((ROOT / "reverse_engineering/hawker_stage2b.md").read_bytes()),
		"candidate_verdicts": {"0x0BFE": "UNPROVED", "0x0BFF": "UNPROVED"},
		"source": SOURCE.relative_to(ROOT).as_posix(), "source_sha256": sha(r),
		"address_domain": "Cumulative English ROM only; file = bus - 0x08000000",
		"native": native, "mask_table_bytes": r[0x63A01C:0x63A024].hex(" "),
		"native_candidate_xref_scope_file": ["0x21000", "0x72000"],
		"native_candidate_xrefs": xrefs, "bank_literal_candidate_xrefs": literals,
		"native_xref_limitation": "Halfword candidate search; not executable reachability or indirect-writer closure",
		"actor_record_inventory": {"maps": 494, "records": len(actors), "max_id": hex(max(actors)),
			"candidate_occurrences": {hex(k):v for k,v in occurrences.items()},
			"ownership_proved": False},
		"conditional_manifest": manifest, "bounded_scripts": scripts,
		"save_stage": window(r,0x2EF0E,0x2EF36),
		"save_load": window(r,0x2F490,0x2F4B4),
		"BIOS_fill_wrapper": window(r,0x942E0,0x942E4),
		"new_files": sorted(NEW), "protected_before": before, "protected_after": after,
		"protected_count": len(before), "stage2_protected_verified": len(old["protected_after"]),
		"protected_unchanged": True, "rom_writes": 0, "runtime_performed": False,
		"unresolved": ["FD53/54/5B/5C operand reachability including FD84 staging and script writers",
			"Existing-save ownership of final byte; reset invocation and bulk/native writer closure",
			"Room initializer scheduling and entry/exit callback lifecycle"]}


if __name__ == "__main__":
	json.dump(main(), sys.stdout, indent=2, ensure_ascii=True)
	print()
