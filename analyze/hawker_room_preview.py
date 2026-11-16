"""Bounded static background previews for explicit map IDs; no ROM modifications.

Incomplete preview: omit unloaded animation/reserved tiles, do not infer collision
or actor availability from an image. Creates only new PNGs in output directory.
"""
import argparse
from pathlib import Path
import struct
from extract_palace_enemy_sprites import lz77, png, ROOT


def main():
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument("maps", nargs="+", type=lambda s: int(s, 16))
	args = p.parse_args()
	if len(args.maps) > 16 or any(not 0 <= m < 494 for m in args.maps):
		raise ValueError("Explicit bounded map list required")
	r = (ROOT / "tools/patch/output/detector-hp120-mit25/detector_rebalance.gba").read_bytes()
	out = ROOT / "reverse_engineering/exports/hawker_room_recon"
	out.mkdir(exist_ok=True)
	for m in args.maps:
		rec = 0x62D3E4 + m * 28
		w, h = r[rec + 3], r[rec + 4]
		source = struct.unpack_from("<I", r, 0x15BA3C + 4 * m)[0] - 0x8000000
		size = int.from_bytes(r[source + 1:source + 4], "little")
		if not 0 < size <= 0x8000:
			raise ValueError("Unexpected tileset size")
		if r[source] == 16:
			gfx, _ = lz77(r, source, size)
		elif r[source] == 48:
			gfx, q = bytearray(), source + 4
			while len(gfx) < size:
				v = r[q]
				q += 1
				count = (v & 127) + (3 if v & 128 else 1)
				if v & 128:
					gfx.extend(bytes([r[q]]) * count)
					q += 1
				else:
					gfx.extend(r[q:q + count])
					q += count
			gfx = bytes(gfx[:size])
		else:
			raise ValueError("Unknown graphics compression")
		pal = struct.unpack_from("<I", r, 0x255F00 + 4 * m)[0] - 0x8000000
		colors = [bytes([((c >> shift) & 31) * 255 // 31 for shift in (0, 5, 10)] + [255])
			for c in struct.unpack_from("<256H", r, pal)]
		pixels = bytearray(colors[0] * (w * h * 256))
		omitted = set()
		for layer in (2, 1, 0):
			mp = struct.unpack_from("<I", r, 0x26E358 + 12 * m + 4 * layer)[0] - 0x8000000
			cp = struct.unpack_from("<I", r, 0x31E7B4 + 12 * m + 4 * layer)[0] - 0x8000000
			if mp < 0 or cp < 0:
				continue
			for cy in range(h):
				for cx in range(w):
					chip = struct.unpack_from("<H", r, mp + 2 * (cy * w + cx))[0]
					for k in range(4):
						tile = struct.unpack_from("<H", r, cp + chip * 8 + k * 2)[0]
						tid, bank = tile & 1023, tile >> 12
						if tid * 32 >= len(gfx):
							omitted.add(tid)
							continue
						for y in range(8):
							for x in range(8):
								xx, yy = (7 - x if tile & 1024 else x), (7 - y if tile & 2048 else y)
								index = (gfx[tid * 32 + yy * 4 + xx // 2] >> (4 * (xx & 1))) & 15
								if index:
									pos = ((cy * 16 + (k // 2) * 8 + y) * w * 16 + cx * 16 + (k % 2) * 8 + x) * 4
									pixels[pos:pos + 4] = colors[bank * 16 + index]
		with (out / f"map_{m:04X}_background.png").open("xb") as f:
			f.write(png(w * 16, h * 16, bytes(pixels)))
		print(hex(m), w, h, "omitted reserved/animation tiles", sorted(omitted))


if __name__ == "__main__":
	main()
