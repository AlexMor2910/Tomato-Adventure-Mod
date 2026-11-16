"""Bounded read-only checkpoint/route inspection; prints JSON, no runtime writes."""
import json
import struct
import zlib

from awe_initialization import EXPECTED, RECRUITMENT, ROOT, protected
from pre_oystown_foundation import checkpoint
from pre_oystown_progression import decode_commands
from thumb_inspect import inspect

CAPTURE = ROOT / "reverse_engineering/experiments/testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/captures/post-recruitment.ss0"
CAPTURE_HASH = "4eb81a006e852955556664f8c76c4526458048dab644dfa6f36a4b20d352946f"


def main():
	before = protected()
	for path, expected in {**EXPECTED, CAPTURE: CAPTURE_HASH}.items():
		if before.get(str(path.relative_to(ROOT))) != expected:
			raise ValueError("Protected input mismatch: " + str(path))
	rom = RECRUITMENT.read_bytes()
	baseline = (ROOT / "Tomato Adventure (Japan) (patched).gba").read_bytes()
	identity = (zlib.crc32(rom) & 0xFFFFFFFF, rom[0xA0:0xB0])
	snapshot = checkpoint(CAPTURE, {identity})
	data, p, state, extras = CAPTURE.read_bytes(), 8, None, []
	while p < len(data):
		n = struct.unpack_from(">I", data, p)[0]
		tag, value = data[p + 4:p + 8], data[p + 8:p + 8 + n]
		if tag == b"gbAs":
			state = zlib.decompress(value)
		if tag == b"gbAx":
			kind, size = struct.unpack_from("<II", value)
			decoder = zlib.decompressobj()
			decoded = decoder.decompress(value[8:], 0x61001)
			if len(decoded) != size or not decoder.eof or decoder.unused_data:
				raise ValueError("Invalid extended metadata stream")
			extras.append(dict(kind=hex(kind), bytes=size))
		p += n + 12
	iw = state[0x19000:0x21000]
	flags = []
	for flag in (0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x105, 0x108, 0x114, 0x117, 0x171, 0x1C0, 0x1F4, 0x20A):
		address, mask = 0x32E7 + (flag >> 3), 1 << (flag & 7)
		flags.append(dict(flag=hex(flag), address=hex(0x03000000 + address),
			mask=hex(mask), byte=hex(iw[address]), set=bool(iw[address] & mask)))
	windows = []
	for role, start, end in (("node4 up to5", 0x88E98, 0x88EAA),
		("node5 up to6", 0x88EB0, 0x88EC2), ("node6 left to7", 0x89134, 0x89146),
		("node7 left to8", 0x8914C, 0x8915E)):
		if rom[start:end] != baseline[start:end]:
			raise ValueError("Derivative differs in route window")
		windows.append(dict(role=role, instructions=[dict(bus=hex(i.address), bytes=i.raw.hex(" "), text=i.text)
			for i in inspect(rom, start, end, ())]))
	maps = []
	for mid in (0x1F, 0x1E, 0x20, 0x21, 0x22, 0x2A, 0x2B, 0x2E):
		record = 0x62D3E4 + mid * 28
		pointer = struct.unpack_from("<I", rom, record + 12)[0]
		exits = []
		for slot in range(12):
			offset = pointer - 0x08000000 + slot * 10
			if rom[offset] == 0xFF:
				break
			value = rom[offset:offset + 10]
			exits.append(dict(bus=hex(offset + 0x08000000), raw=value.hex(" "),
				rectangle=list(value[:4]), destination=hex(struct.unpack_from("<H", value, 4)[0])))
		else:
			raise ValueError("Exit table exceeds bounded scope")
		maps.append(dict(map=hex(mid), descriptor=hex(record + 0x08000000), exit_pointer=hex(pointer), exits=exits))
	contexts = []
	for slot in range(32):
		base = 0x3AD4 + slot * 28
		if any(iw[base:base + 28]):
			contexts.append(dict(slot=slot, raw=iw[base:base + 28].hex(" "),
				cursor=hex(struct.unpack_from("<I", iw, base + 4)[0])))
	after = protected()
	if before != after:
		raise RuntimeError("Protected artifact changed during inspection")
	print(json.dumps(dict(checkpoint=snapshot, extended_metadata=extras,
		cpu=dict(raw_r15=hex(struct.unpack_from("<I", state, 0x5C)[0]),
			cpsr=hex(struct.unpack_from("<I", state, 0x60)[0]), lr=hex(struct.unpack_from("<I", state, 0x58)[0])),
		cached_overworld_node=iw[0x35F4], route_byte=hex(iw[0x32EB]), flags=flags,
		scheduling_bitmap=iw[0x39C1:0x39C5].hex(" "), retained_contexts=contexts,
		transition_gates={hex(0x03000000 + a): iw[a] for a in (0x1904, 0x1908, 0x1909, 0x190C, 0x1B4A)},
		saved_map_pointers={hex(0x03000000 + a): hex(struct.unpack_from("<I", iw, a)[0]) for a in (0x1938, 0x193C, 0x1944, 0x194C)},
		route_windows=windows, scoped_map_exits=maps,
		oystown_setup=decode_commands(rom, 0x102491, 0x1025BD)[0],
		oystown_intro=decode_commands(rom, 0x1084CA, 0x1086F8)[0],
		conditional_route_edit=dict(address="0x030032EB", before=hex(iw[0x32EB]),
			mask="0xF0", after=hex(iw[0x32EB] | 0xF0),
			status="candidate only after safe node4 overworld access and fresh live read; do not execute now"),
		protected_count=len(before), protected_before=before, protected_after=after,
		protected_unchanged=True, runtime_writes=0), indent=2))


if __name__ == "__main__":
	main()
