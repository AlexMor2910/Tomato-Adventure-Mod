"""Read-only inventory and bounded completion evidence; prints JSON only."""
import json
import struct
import zlib

from awe_initialization import EXPECTED, RECRUITMENT, ROOT, protected
from pre_oystown_foundation import audit, checkpoint
from pre_oystown_progression import decode_commands
from thumb_inspect import inspect


def state_bytes(path):
	data, pos, state = path.read_bytes(), 8, None
	while pos < len(data):
		length = struct.unpack_from(">I", data, pos)[0]
		tag, value = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
		if tag == b"gbAs":
			state = zlib.decompress(value)
		if tag == b"gbAx":
			kind, size = struct.unpack_from("<II", value)
			decoder = zlib.decompressobj()
			decoded = decoder.decompress(value[8:], 0x61001)
			if len(decoded) != size or not decoder.eof or decoder.unused_data:
				raise ValueError("Invalid extended metadata stream")
		pos += length + 12
	if state is None:
		raise ValueError("Missing checked state chunk")
	return state


def main():
	before = protected()
	prior = json.loads((ROOT / "reverse_engineering/experiments/oystown_shortcut_evidence.json").read_text(encoding="utf-8"))
	for name, expected in prior["protected_after"].items():
		if before.get(name) != expected:
			raise ValueError("Previously protected artifact changed: " + name)
	all_states = audit()
	if all_states["inspection_errors"]:
		raise ValueError("Resolve checkpoint inspection errors")
	rom = RECRUITMENT.read_bytes()
	baseline = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	identity = {(zlib.crc32(rom) & 0xFFFFFFFF, rom[0xA0:0xB0])}
	paths = [ROOT / "before_oystown.ss0", ROOT / "after_exchange_oystown.ss0",
		ROOT / "reverse_engineering/experiments/testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/captures/post-recruitment.ss0"]
	states, raw = [], []
	for path in paths:
		entry = dict(path=str(path.relative_to(ROOT)), **checkpoint(path, identity))
		state = state_bytes(path)
		iw = state[0x19000:0x21000]
		entry.update(cached_overworld_node=iw[0x35F4], route_byte=hex(iw[0x32EB]),
			toy_parts=hex(iw[0x1AB6]), byte_variable_3C=hex(iw[0x32C3]),
			acquisition_difficulty=iw[0x196E], scheduler_bitmap=iw[0x39C1:0x39C5].hex(" "),
			cpu_pc=hex(struct.unpack_from("<I", state, 0x5C)[0]), flags=[])
		for flag in (0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x117, 0x171, 0x1C0, 0x1F4, 0x20A, 0x227, 0x228, 0x229, 0x22A, 0x257, 0x271, 0x272):
			address, mask = 0x32E7 + (flag >> 3), 1 << (flag & 7)
			entry["flags"].append(dict(flag=hex(flag), address=hex(0x03000000 + address), mask=hex(mask), set=bool(iw[address] & mask)))
		states.append(entry)
		raw.append(iw)
	scripts = []
	for role, start, end in (("Lab2 original reward event", 0x111CE6, 0x111E8D),
		("Lab3 original reward event", 0x112090, 0x112234),
		("Binky selection/transaction span", 0x107FC0, 0x1081C0)):
		commands, boundary = decode_commands(rom, start, end)
		scripts.append(dict(role=role, start=hex(start + 0x08000000), end=hex(end + 0x08000000),
			commands=commands, boundary=boundary,
			classification="confirmed static command inventory, not complete path/context proof"))
	windows = []
	for role, start, end, pools in (("FE53 grant", 0x25624, 0x25632, ()),
		("packed owner/ID grant", 0x2927C, 0x292AC, ()),
		("inventory/usage/equipment", 0x6ADA0, 0x6AE2A, ((0x6AE00, 0x6AE14),)),
		("FE C0 persistent-charge read", 0x29BB8, 0x29BDC, ()),
		("FE C1 persistent-charge/readiness clear", 0x29BEC, 0x29C18, ())):
		if rom[start:end] != baseline[start:end]:
			raise ValueError("Derivative changed bounded handler window")
		windows.append(dict(role=role, instructions=[dict(bus=hex(i.address), bytes=i.raw.hex(" "), text=i.text)
			for i in inspect(rom, start, end, pools)]))
	after = protected()
	if before != after:
		raise RuntimeError("Protected artifact changed")
	print(json.dumps(dict(scope="read-only completion evidence; no state/ROM outputs", relevant_states=states,
		all_checkpoint_groups=all_states["checkpoints"], script_scopes=scripts, native_windows=windows,
		fe_dispatch={hex(op): hex(struct.unpack_from("<I", rom, 0x62B8B4 + op * 4)[0]) for op in (0x53, 0x54, 0xC0, 0xC1)},
		lab3_exterior_exits=dict(descriptor="0x0862EC48", pointer="0x0813BD08",
			raw=rom[0x13BD08:0x13BD1C].hex(" "),
			meaning="first exit destination8008 returns to overworld node7; second enters Lab3 map0032"),
		pre_post_main_flag_byte_differences=[dict(address=hex(0x03000000 + a), before=hex(raw[0][a]), after=hex(raw[1][a]))
			for a in range(0x32E7, 0x3347) if raw[0][a] != raw[1][a]],
		classification_of_diff="endpoint differences across travel/introduction/manual charge/exchange; not transaction attribution",
		protected_count=len(before), protected_before=before, protected_after=after, protected_unchanged=True,
		limitations=["Binky field not identified", "No exact transaction before/after capture", "Optional Gimmick IDs/availability unresolved", "Save/reload not executed"]), indent=2))


if __name__ == "__main__":
	main()
