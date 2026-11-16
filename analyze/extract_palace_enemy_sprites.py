"""Extract two traced enemy frame pairs; read ROM, exclusively create PNG/JSON outputs.

Uses Python standard library only. No emulator, ROM writes or guessed graphics search.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba"
EXPECTED = "7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2"


def lz77(rom, start, expected_size):
	assert rom[start] == 0x10
	assert int.from_bytes(rom[start + 1:start + 4], "little") == expected_size
	out, p = bytearray(), start + 4
	while len(out) < expected_size:
		flags = rom[p]
		p += 1
		for bit in range(7, -1, -1):
			if len(out) == expected_size:
				break
			if flags & (1 << bit):
				a, b = rom[p:p + 2]
				p += 2
				length, distance = (a >> 4) + 3, ((a & 15) << 8 | b) + 1
				assert distance <= len(out) and len(out) + length <= expected_size
				for _ in range(length):
					out.append(out[-distance])
			else:
				out.append(rom[p])
				p += 1
	assert len(out) == expected_size
	return bytes(out), p


def chunk(tag, data):
	return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def png(width, height, pixels):
	assert len(pixels) == width * height * 4
	scan = b"".join(b"\0" + pixels[y * width * 4:(y + 1) * width * 4] for y in range(height))
	return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(scan, 9)) + chunk(b"IEND", b"")


def render(tiles, tw, th, palette):
	pixels = bytearray(tw * th * 64 * 4)
	for ty in range(th):
		for tx in range(tw):
			for y in range(8):
				for x in range(8):
					v = tiles[(ty * tw + tx) * 32 + y * 4 + x // 2]
					index = (v >> (4 * (x & 1))) & 15
					p = ((ty * 8 + y) * tw * 8 + tx * 8 + x) * 4
					pixels[p:p + 4] = bytes(palette[index])
	return bytes(pixels)


def enlarge(pixels, w, h, scale=4):
	return b"".join(b"".join(pixels[(y * w + x) * 4:(y * w + x + 1) * 4] * scale for x in range(w)) * scale for y in range(h))


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--output", type=Path, default=ROOT / "reverse_engineering/exports/palace_enemy_sprites")
	args = parser.parse_args()
	r = ROM.read_bytes()
	assert hashlib.sha256(r).hexdigest() == EXPECTED
	args.output.mkdir(parents=True, exist_ok=False)
	result = {"rom": str(ROM.relative_to(ROOT)), "sha256": EXPECTED, "enemies": []}
	for eid, name in ((0xA5, "Detector"), (0x9C, "Rattlin' Dragon")):
		record = 0x634F50 + eid * 0x4C
		size_index = r[record + 0x2F]
		tw, th = struct.unpack_from("<HH", r, 0x486548 + size_index * 4)
		pal, frame0, frame1, layout = struct.unpack_from("<4I", r, record + 0x34)
		layout_values = struct.unpack_from("<" + "H" * (tw * th), r, layout - 0x8000000)
		assert list(layout_values) == [0x6200 + 32 * y + x for y in range(th) for x in range(tw)]
		palette = []
		for index, color in enumerate(struct.unpack_from("<16H", r, pal - 0x8000000)):
			channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
			palette.append(tuple((c << 3) | (c >> 2) for c in channels) + (255 if index else 0,))
		prefix = "detector_A5" if eid == 0xA5 else "rattlin_dragon_9C"
		entry = {"id": f"0x{eid:02X}", "name": name, "record_bus": f"0x{record + 0x8000000:08X}", "record_file": f"0x{record:08X}", "size_index": size_index, "dimensions_tiles": [tw, th], "dimensions_pixels": [tw * 8, th * 8], "palette_bus": f"0x{pal:08X}", "palette_file": f"0x{pal - 0x8000000:08X}", "layout_reference_bus": f"0x{layout:08X}", "frames": []}
		for fi, ptr in enumerate((frame0, frame1)):
			data, end = lz77(r, ptr - 0x8000000, tw * th * 32)
			pixels = render(data, tw, th, palette)
			outputs = []
			for scale in (1, 4):
				filename = f"{prefix}_frame{fi}" + ("_4x" if scale == 4 else "") + ".png"
				image = png(tw * 8 * scale, th * 8 * scale, pixels if scale == 1 else enlarge(pixels, tw * 8, th * 8))
				with (args.output / filename).open("xb") as f:
					f.write(image)
				outputs.append(filename)
			entry["frames"].append({"index": fi, "pointer_field_bus": f"0x{record + 0x38 + 4 * fi + 0x8000000:08X}", "compressed_bus": f"0x{ptr:08X}", "compressed_file": f"0x{ptr - 0x8000000:08X}", "compressed_end_exclusive_file": f"0x{end:08X}", "decompressed_bytes": len(data), "decompressed_sha256": hashlib.sha256(data).hexdigest(), "outputs": outputs})
		result["enemies"].append(entry)
	assert hashlib.sha256(ROM.read_bytes()).hexdigest() == EXPECTED
	with (args.output / "extraction.json").open("x", encoding="utf-8") as f:
		json.dump(result, f, indent=2)
		f.write("\n")
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()
