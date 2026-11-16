"""Bounded read-only Hawker placement dependency audit. Prints JSON only.

No emulator, ROM patching, state loading, or automatic code analysis.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

from pre_oystown_progression import decode_commands
from thumb_inspect import decode

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools/patch/output/detector-hp120-mit25/detector_rebalance.gba"
EXPECTED = "124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0"


def sha(data):
	return hashlib.sha256(data).hexdigest()


def audit():
	r = SOURCE.read_bytes()
	assert len(r) == 0x1000000 and sha(r) == EXPECTED
	result = {
		"status": "BLOCKED BEFORE PATCHING: actor context and graphics/footprint dependencies unresolved",
		"source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(r),
		"service": "Existing full eligible AWE gauge exchanged for two awarded Binkies; no Binky payment introduced",
		"native_windows": [], "maps": [], "scripts": [],
	}
	windows = (
		("FE31 handler argument resolution", 0x28ED0, 0x28EEE),
		("FE31 actor record state write", 0x65E4C, 0x65E76),
		("actor resolver literal/FF", 0x22798, 0x227A6),
		("actor resolver FE", 0x227B0, 0x227C8),
		("actor resolver FD", 0x227D0, 0x227DA),
		("actor resolver FC", 0x227E0, 0x227EC),
		("FD01 halfword scratch +6", 0x266F4, 0x26712),
		("FD02 halfword scratch +8", 0x2671C, 0x2673A),
		("FD84 scratch argument dispatch", 0x28490, 0x284EA),
		("FD84 two-byte argument continuation", 0x284F8, 0x28516),
		("main command36", 0x23CA4, 0x23D00),
		("command36 target comparison X", 0x663C0, 0x6640A),
		("actor loader index starts1", 0x3424C, 0x34292),
		("actor loader record state and graphics", 0x342D6, 0x343A4),
		("actor loader advances slot and record", 0x34696, 0x346B2),
		("FE01 entry and actor context", 0x2886C, 0x28928),
	)
	for role, start, end in windows:
		cursor, instructions = start, []
		while cursor < end:
			i = decode(r, cursor)
			assert cursor + i.size <= end
			instructions.append({"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "), "text": i.text})
			cursor += i.size
		result["native_windows"].append({"role": role, "file_start": f"0x{start:08X}",
			"file_end_exclusive": f"0x{end:08X}", "sha256": sha(r[start:end]), "instructions": instructions})
	for mid, xy in ((0x5F, (25, 5)), (0x4D, (14, 6))):
		p = 0x62D3E4 + 28 * mid
		block = struct.unpack_from("<I", r, p + 20)[0] - 0x08000000
		actors = []
		for slot in range(1, 16):
			a = block + 0x70 + (slot - 1) * 16
			if r[a] == 255:
				break
			actors.append({"slot": slot, "record_bus": f"0x{a + 0x08000000:08X}",
				"bytes": r[a:a + 16].hex(" "), "xy": list(r[a + 3:a + 5])})
		result["maps"].append({"map_id": f"0x{mid:04X}", "candidate_xy": xy,
			"record_bus": f"0x{p + 0x08000000:08X}", "record_bytes": r[p:p + 28].hex(" "),
			"actor_block_bus": f"0x{block + 0x08000000:08X}",
			"header_bytes": r[block:block + 0x70].hex(" "), "actors": actors})
	for role, start, end in (
		("Shared authoritative exchange", 0x107E81, 0x1081DA),
		("Oystown wrapper", 0x102D27, 0x102D37),
		("Map00D7 wrapper", 0x102D37, 0x102D47),
		("Map0149 wrapper", 0x102D47, 0x102D57),
		("Map015D wrapper", 0x102D57, 0x102D67),
	):
		commands, boundary = decode_commands(r, start, end)
		assert boundary == "exact scoped end"
		result["scripts"].append({"role": role, "start_bus": f"0x{start + 0x08000000:08X}",
			"sha256": sha(r[start:end]), "commands": commands})
	result["literal_actor3_state_commands"] = [c for c in result["scripts"][0]["commands"] if c["bytes"] == "fe 31 03 01"]
	result["existing_exchange_actor_bindings"] = []
	for mid, slot in ((0xD7, 4), (0x104, 3), (0x149, 3), (0x15D, 5)):
		block = struct.unpack_from("<I", r, 0x62D3E4 + 28 * mid + 20)[0] - 0x08000000
		a = block + 0x70 + (slot - 1) * 16
		gi, pi = r[a + 1] & 31, r[a + 2] >> 4
		gp = struct.unpack_from("<I", r, block + gi * 4)[0]
		pp = struct.unpack_from("<I", r, block + 0x40 + pi * 4)[0]
		result["existing_exchange_actor_bindings"].append({"map_id": f"0x{mid:04X}", "slot": slot,
			"actor_bus": f"0x{a + 0x08000000:08X}", "record_bytes": r[a:a + 16].hex(" "),
			"candidate_graphics_index": gi, "graphics_entry_bus": f"0x{block + gi * 4 + 0x08000000:08X}",
			"graphics_pointer": f"0x{gp:08X}", "graphics_descriptor_bytes": r[gp - 0x08000000:gp - 0x08000000 + 16].hex(" "),
			"candidate_palette_index": pi, "palette_entry_bus": f"0x{block + 0x40 + pi * 4 + 0x08000000:08X}",
			"palette_pointer": f"0x{pp:08X}",
			"confidence": "Confirmed bytes; binding interpretation Probable pending complete graphics loader trace"})
	result["accepted_stats"] = {"Detector": {"hp": struct.unpack_from("<H", r, 0x638056)[0],
		"base_mitigation": struct.unpack_from("<H", r, 0x63805A)[0]},
		"Rattlin_Dragon": {"hp": struct.unpack_from("<H", r, 0x637DAA)[0],
		"base_mitigation": struct.unpack_from("<H", r, 0x637DAE)[0]}}
	assert result["accepted_stats"] == {"Detector": {"hp": 120, "base_mitigation": 25},
		"Rattlin_Dragon": {"hp": 262, "base_mitigation": 54}}
	result["source_sha256_after_read"] = sha(SOURCE.read_bytes())
	assert result["source_sha256_after_read"] == EXPECTED
	return result


if __name__ == "__main__":
	json.dump(audit(), sys.stdout, indent=2)
	print()
