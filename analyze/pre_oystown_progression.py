"""Bounded static event/route inventory. Prints evidence only; no runtime writes.

python -B tools/analyze/pre_oystown_progression.py
Linear script decoding inventories byte boundaries, not path reachability.
"""
import hashlib
import json
from pathlib import Path
import struct

from awe_initialization import protected
from thumb_inspect import inspect

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_SCOPES = (
	("Pokypine kidnapping map0015", 0x1251C6, 0x125889, False),
	("Palace briefing map001B secondary event", 0x10D1F0, 0x10D4C0, False),
	("Hanzo first reward continuation", 0x10D693, 0x10D6E0, False),
	("Mayonen boss candidate map003A", 0x10E53C, 0x10ECEF, False),
	("Hanzo Lab2 map0031", 0x111CE6, 0x111E8D, False),
	("Hanzo Lab3 map0032", 0x112090, 0x112234, False),
	("Namp boss candidate map008E", 0x116044, 0x1165B1, False),
	("Alessa original scene map001E", 0x1271E9, 0x1275B6, False),
	("AWE lesson and skip", 0x128D5A, 0x128F48, False),
	("Namp arrival setup", 0x1148EB, 0x1149A7, True),
	("Oystown arrival setup", 0x102491, 0x1025BD, False),
	("Oystown default prefix", 0x10C67A, 0x10C6E6, False),
	("Oystown first-visit candidate", 0x1084CA, 0x1086F8, False),
	("Toy Part announcement common block", 0x124E4A, 0x124EFC, False),
)
NATIVE_WINDOWS = (
	("Hanzo1 to Mayonen", 0x89210, 0x89226, ()),
	("Mayonen to Hanzo2", 0x88E98, 0x88EAA, ()),
	("Hanzo2 to Namp", 0x88EB0, 0x88EC2, ()),
	("Namp to Hanzo3", 0x89134, 0x89146, ()),
	("Hanzo3 to Oystown", 0x8914C, 0x8915E, ()),
	("Namp return to Hanzo2", 0x88FD8, 0x88FEA, ()),
	("Hanzo3 return to Namp", 0x88FF0, 0x89002, ()),
	("Oystown to Hanzo4", 0x89164, 0x89176, ()),
	("Hanzo4 to Oystown", 0x89244, 0x89256, ()),
	("FE7C map transition", 0x2A0A0, 0x2A11C, ()),
	("FE7D map transition", 0x2A134, 0x2A1B8, ()),
	("FD4D byte variables", 0x2A004, 0x2A030, ()),
	("FD54 second-bank clear", 0x2770C, 0x2772C, ()),
	("second bank wrapper", 0x6B0B8, 0x6B134, ()),
	("FE52 Toy Part bit", 0x255EC, 0x25600, ()),
	("FE43 battle entry", 0x250E4, 0x2514C, ()),
)


def digest(data):
	return hashlib.sha256(data).hexdigest()


def decode_commands(rom, start, limit, stop_at_return=False):
	commands, cursor = [], start
	while cursor < limit:
		family = rom[cursor]
		op = rom[cursor + 1] if family in (0xFD, 0xFE) else family
		table = {0xFD: 0x62B815, 0xFE: 0x62B736}.get(family, 0x62B6C4)
		end = cursor + (2 if family in (0xFD, 0xFE) else 1) + rom[table + op]
		if end > limit:
			return commands, f"bounded stop before command 0x{cursor + 0x08000000:08X} crossing limit"
		commands.append({"bus": f"0x{cursor + 0x08000000:08X}", "bytes": rom[cursor:end].hex(" ")})
		cursor = end
		if stop_at_return and family == 0xFD and op in (0x7C, 0x7D):
			return commands, "stopped at first recorded return command"
	return commands, "exact scoped end"


def main():
	before = protected()
	r = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	j = (ROOT / "Tomato Adventure (Japan).gba").read_bytes()
	if digest(r) != "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde":
		raise ValueError("Unexpected English baseline")
	scripts = []
	for label, start, end, stop in SCRIPT_SCOPES:
		commands, boundary = decode_commands(r, start, end, stop)
		scripts.append({"role": label, "file_range": [f"0x{start:08X}", f"0x{end:08X}"],
			"sha256": digest(r[start:end]), "japanese_identical": r[start:end] == j[start:end],
			"commands": commands, "boundary": boundary,
			"confidence": "Confirmed static byte inventory; reachability/transitive effects not certified"})
	native = []
	for label, start, end, exclusions in NATIVE_WINDOWS:
		native.append({"role": label, "file_range": [f"0x{start:08X}", f"0x{end:08X}"],
			"sha256": digest(r[start:end]), "japanese_identical": r[start:end] == j[start:end],
			"instructions": [{"bus": f"0x{i.address:08X}", "bytes": i.raw.hex(" "), "text": i.text}
				for i in inspect(r, start, end, exclusions)]})
	arrivals = []
	for node in range(3, 9):
		case = struct.unpack_from("<I", r, 0x88B04 + node * 4)[0] - 0x08000000
		# Each selected case loads its script literal at case+0xC.
		pointer = struct.unpack_from("<I", r, case + 0xC)[0]
		start = pointer - 0x08000000
		commands, boundary = decode_commands(r, start, start + 17, True)
		arrivals.append({"node": node, "native_case_bus": f"0x{case + 0x08000000:08X}",
			"script_bus": f"0x{pointer:08X}", "commands": commands, "boundary": boundary})
	maps = []
	for mid in (0x15, 0x1B, 0x24, 0x30, 0x31, 0x32, 0x38, 0x3A, 0x48, 0x1E, 0xDE, 0x60, 0xDF, 0x8B, 0x8E, 0x104):
		pos = 0x62D3E4 + mid * 28
		events = struct.unpack_from("<I", r, pos + 16)[0]
		default = struct.unpack_from("<I", r, events - 0x08000000)[0]
		maps.append({"map_id": f"0x{mid:04X}", "record_bus": f"0x{pos + 0x08000000:08X}",
			"event_table_bus": f"0x{events:08X}", "default_script_bus": f"0x{default:08X}",
			"raw_record": r[pos:pos + 28].hex(" ")})
	links = {"Palace briefing secondary pointer at 0x08159BD4":
		f"0x{struct.unpack_from('<I', r, 0x159BD4)[0]:08X}",
		"Alessa scene secondary pointer at 0x08159BEC":
		f"0x{struct.unpack_from('<I', r, 0x159BEC)[0]:08X}",
		"AWE lesson default pointer at 0x08159C5C":
		f"0x{struct.unpack_from('<I', r, 0x159C5C)[0]:08X}"}
	after = protected()
	if before != after:
		raise ValueError("Protected artifacts changed during static inventory")
	print(json.dumps({"scope": "bounded static pre-Oystown progression inventory; no runtime writes",
		"protected_count": len(before), "protected_before": before, "protected_after": after,
		"protected_unchanged": True, "english_sha256": digest(r), "japanese_sha256": digest(j),
		"script_scopes": scripts, "native_windows": native, "arrivals": arrivals, "map_records": maps,
		"specific_event_links": links,
		"limitations": ["Linear command inventory does not establish every branch is reachable",
			"No transitive whole-scene/whole-ROM analysis", "No complete optional Gimmick/shop inventory proof"]}, indent=2))


if __name__ == "__main__":
	main()
