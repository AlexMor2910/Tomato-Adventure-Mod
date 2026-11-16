"""Read-only inspection of mGBA 0.10.5 PNG GBA checkpoints; no emulator load."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path
from prepare_session import EXPECTED, ROOT, digest


def inspect(path):
	before = (digest(path), path.stat().st_mtime_ns)
	data = path.read_bytes()
	if data[:8] != b"\x89PNG\r\n\x1a\n":
		raise ValueError("Expected PNG-format mGBA checkpoint")
	p, state, extras, dimensions = 8, None, {}, None
	while p < len(data):
		length = struct.unpack_from(">I", data, p)[0]
		if p + length + 12 > len(data):
			raise ValueError("Truncated PNG chunk")
		tag = data[p + 4:p + 8]
		payload = data[p + 8:p + 8 + length]
		crc = struct.unpack_from(">I", data, p + 8 + length)[0]
		if zlib.crc32(tag + payload) & 0xFFFFFFFF != crc:
			raise ValueError("PNG chunk CRC mismatch")
		if tag == b"IHDR":
			dimensions = struct.unpack_from(">II", payload)
		if tag == b"gbAs":
			if state is not None:
				raise ValueError("Duplicate state chunk")
			decoder = zlib.decompressobj()
			state = decoder.decompress(payload, 0x61001)
			if len(state) != 0x61000 or not decoder.eof:
				raise ValueError("Unexpected serialized GBA state size")
		if tag == b"gbAx":
			kind, size = struct.unpack_from("<II", payload)
			decoder = zlib.decompressobj()
			value = decoder.decompress(payload[8:], min(size, 0x61000) + 1)
			if len(value) != size or not decoder.eof:
				raise ValueError("Invalid extended data")
			extras[kind] = value
		p += length + 12
		if tag == b"IEND":
			break
	if p != len(data) or state is None or dimensions != (240, 160):
		raise ValueError("Incomplete or unexpected GBA PNG checkpoint")
	rom_path = ROOT / "Tomato Adventure (Japan) (patched).gba"
	if digest(rom_path) != EXPECTED[rom_path.name]:
		raise ValueError("Unexpected English ROM")
	rom = rom_path.read_bytes()
	magic, bios, crc = struct.unpack_from("<III", state)
	if magic != 0x01000007 or crc != zlib.crc32(rom) & 0xFFFFFFFF or state[0x10:0x20] != rom[0xA0:0xB0]:
		raise ValueError("Checkpoint version or ROM identity mismatch")
	result = dict(path=str(path.resolve()), bytes=len(data), sha256=before[0], dimensions=list(dimensions),
		state_magic=hex(magic), state_bytes=len(state), rom_crc32=f"{crc:08x}",
		rom_sha256=digest(rom_path), title=state[0x10:0x1C].rstrip(b"\0").decode("ascii"),
		game_code=state[0x1C:0x20].decode("ascii"),
		creator=extras.get(0x102, b"").rstrip(b"\0").decode("ascii"),
		embedded_savedata_bytes=len(extras.get(2, b"")),
		embedded_savedata_sha256=hashlib.sha256(extras[2]).hexdigest() if 2 in extras else None,
		embedded_savedata_unique_bytes=sorted(set(extras.get(2, b""))),
		validation="structure/identity checks passed; actual emulator load not tested")
	iwram, ewram = state[0x19000:0x21000], state[0x21000:0x61000]
	work = iwram[0x3F34:0x3F34 + 0x58]
	result["saved_gimmick_work"] = dict(
		base="0x03003f34", first_word=hex(int.from_bytes(work[:4], "little")),
		field_22_address="0x03003f56", field_22=work[0x22],
		first_pair_even_address="0x03003f5c", first_pair_even=work[0x28],
		selected_pair_even_address="0x03003f9d", selected_pair_even=iwram[0x3F34 + 0x69],
		nontext_matching_ids=[g for g in range(1, 51) if work[0x22:0x58] == rom[0x62C250 + (g - 1) * 0x58 + 0x22:0x62C250 + g * 0x58]],
		scope="saved bytes and ROM comparison only; not a live battle consumer trace")
	base = struct.unpack_from("<I", iwram, 0x5000)[0]
	out = base + 0x5AE8
	if 0x02000000 <= out <= 0x02040000 - 17:
		raw = ewram[out - 0x02000000:out - 0x02000000 + 17]
		result["saved_menu_cache"] = dict(base=hex(base), output=hex(out), raw_hex=raw.hex(" "), halfwords=list(struct.unpack_from("<7H", raw)))
	# Snapshot selection is not a live r0 capture or a producer trace.
	owner, slot = iwram[0x500C], iwram[0x500F]
	if owner < 4 and slot < 20:
		entry_offset = 0x1EE4 + owner * 0x60 + slot * 3
		g, d, b = iwram[entry_offset:entry_offset + 3]
		if 1 <= g <= 50 and 1 <= d <= 9:
			record = 0x62C250 + (g - 1) * 0x58
			coefficient = record + 0x28 + 2 * (d - 1)
			a, cap, c = rom[record + 0x22], rom[record + 0x23], rom[coefficient]
			result["saved_selection"] = dict(state_address=hex(0x03000000 + entry_offset), raw_hex=iwram[entry_offset:entry_offset + 3].hex(" "),
				id=g, selector=d, upgrade=b, record_address=hex(record + 0x08000000),
				field_22=a, field_23=cap, coefficient_address=hex(coefficient + 0x08000000), coefficient=c,
				expected_unscaled=a + b, expected_scaled=(a + b) * c // 100,
				scope="checkpoint snapshot; not a live calculation breakpoint capture")
	if before != (digest(path), path.stat().st_mtime_ns):
		raise RuntimeError("Checkpoint changed while being inspected")
	return result


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("checkpoint", type=Path)
	args = parser.parse_args()
	print(json.dumps(inspect(args.checkpoint), indent=2))
