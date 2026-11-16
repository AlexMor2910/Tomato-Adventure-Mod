"""Bounded static actor/animation/movement audit; JSON stdout, no ROM writes."""
import json
import struct
import sys

from hawker_placement_safety import ROOT, SOURCE, EXPECTED, sha
from pre_oystown_progression import decode_commands
from thumb_inspect import decode

SIZES = (((8, 8), (16, 16), (32, 32), (64, 64)),
	((16, 8), (32, 8), (32, 16), (64, 32)),
	((8, 16), (8, 32), (16, 32), (32, 64)))
WINDOWS = (
	("animation mode dispatch", 0x35D98, 0x35DBC),
	("mode1 movement flag", 0x35DE8, 0x35E0C),
	("mode1 select directional animation", 0x35E3C, 0x35E4E),
	("mode1 advance animation", 0x35E5C, 0x35E66),
	("animation selection", 0x3310C, 0x3318E),
	("animation timer advance", 0x33218, 0x33272),
	("animation frame pointer advance", 0x33288, 0x332D2),
	("interaction source record and script", 0x6974A, 0x6978C),
	("interaction stores clicked NPC and starts event", 0x697C8, 0x697F0),
	("interaction exclusion gates", 0x6971C, 0x6974A),
	("interaction lock", 0x69D60, 0x69D7E),
	("FE01 continuation transfer", 0x2886C, 0x28928),
	("VM command predecode and cursor update", 0x223BA, 0x2250E),
	("VM dispatch after predecode", 0x21F30, 0x21F48),
	("movement command36 arguments", 0x23CA4, 0x23D00),
	("movement halfword Y", 0x663C0, 0x6640A),
	("movement halfword X", 0x66434, 0x66476),
	("tile Y to pixel Y", 0x33820, 0x33858),
	("tile X to pixel X and offsets", 0x33858, 0x33908),
	("VRAM resource copy and allocation", 0x340C0, 0x34102),
	("graphics loader 16 descriptors", 0x3412C, 0x34208),
	("palette loader 12 banks", 0x34208, 0x34242),
	("actor dimensions and animation pointers", 0x345D8, 0x3461E),
	("frame OAM part count", 0x332FA, 0x33310),
	("frame OAM palette and tile assignment", 0x33310, 0x33390),
	("collision dimensions", 0x3DF48, 0x3DFA0),
	("collision rectangle tests", 0x3DFAC, 0x3E02E),
	("main2F facing argument", 0x23D80, 0x23DA8),
	("main2F direction and animation update", 0x3E4DA, 0x3E51A),
)


def analyze():
	r = SOURCE.read_bytes()
	assert sha(r) == EXPECTED
	d = {"source": str(SOURCE.relative_to(ROOT)), "sha256": sha(r),
		"status": "Research only; no placement patch created", "native": [], "frames": [], "maps": []}
	for name, start, end in WINDOWS:
		a, ins = start, []
		while a < end:
			i = decode(r, a)
			assert a + i.size <= end
			ins.append({"bus": f"0x{i.address:08X}", "raw": i.raw.hex(" "), "text": i.text})
			a += i.size
		d["native"].append({"name": name, "file_start": hex(start), "file_end_exclusive": hex(end),
			"sha256": sha(r[start:end]), "instructions": ins})
	d["animation_dispatch"] = [f"0x{x:08X}" for x in struct.unpack_from("<8I", r, 0x35DC8)]
	for frame in range(11):
		p = struct.unpack_from("<I", r, 0x444860 + 4 * frame)[0] - 0x08000000
		n = struct.unpack_from("<H", r, p)[0]
		parts = []
		for idx in range(n):
			a0, a1, a2 = struct.unpack_from("<3H", r, p + 2 + 6 * idx)
			x, y = a1 & 511, a0 & 255
			x, y = x - 512 if x >= 256 else x, y - 256 if y >= 128 else y
			w, h = SIZES[a0 >> 14][a1 >> 14]
			parts.append({"xywh": [x, y, w, h], "tile": a2 & 1023,
				"raw_oam": [hex(a0), hex(a1), hex(a2)]})
		d["frames"].append({"frame": frame, "file": hex(p), "parts": parts,
			"bounds_exclusive": [min(z["xywh"][0] for z in parts), min(z["xywh"][1] for z in parts),
				max(z["xywh"][0] + z["xywh"][2] for z in parts), max(z["xywh"][1] + z["xywh"][3] for z in parts)]})
	d["animation_sequences"] = []
	for idx in range(4):
		p = struct.unpack_from("<I", r, 0x451E78 + 4 * idx)[0] - 0x08000000
		frames = []
		for off in range(0, 64, 4):
			f = struct.unpack_from("<H", r, p + off)[0]
			if f == 0xFFFF:
				break
			assert f < 11
			frames.append([f, struct.unpack_from("<H", r, p + off + 2)[0]])
		else:
			raise ValueError("Animation did not terminate within bound")
		d["animation_sequences"].append({"index": idx, "file": hex(p), "frame_duration_pairs": frames})
	for mid, xy, newslot, gi, pi in ((0x5F, (25, 5), 7, 7, 7), (0x4D, (14, 6), 8, 5, 6)):
		b = struct.unpack_from("<I", r, 0x62D3E4 + 28 * mid + 20)[0] - 0x08000000
		resources, total = [], 0
		for idx in range(16):
			p = struct.unpack_from("<I", r, b + idx * 4)[0]
			if p:
				tiles = r[p - 0x08000000 + 3]
				total += tiles
				resources.append({"slot": idx, "descriptor": hex(p), "tiles": tiles})
		used_palettes = sorted({r[b + 0x70 + k * 16 + 2] >> 4 for k in range(newslot - 1)})
		assert pi not in used_palettes and struct.unpack_from("<I", r, b + 4 * gi)[0] == 0
		collision = struct.unpack_from("<I", r, 0x303950 + 4 * mid)[0] - 0x08000000
		width = r[0x62D3E4 + 28 * mid + 3]
		neighbors = [{"xy": [x, y], "file": hex(collision + y * width + x), "byte": r[collision + y * width + x]}
			for y in range(xy[1] - 1, xy[1] + 3) for x in range(xy[0] - 1, xy[0] + 2)]
		d["maps"].append({"map": hex(mid), "candidate_xy": xy, "new_actor_slot": newslot,
			"free_graphics_slot": gi, "free_palette_slot": pi, "palettes_referenced_by_original_actors": used_palettes,
			"resources": resources, "tiles_before": total, "tiles_after_one_Hawker": total + 51,
			"standing_pixel_XY": [16 * xy[0] + 7, 16 * xy[1] + 15],
			"south_approach_pixel_XY": [16 * xy[0] + 7, 16 * (xy[1] + 1) + 15],
			"base_collision_neighborhood": neighbors})
	commands, boundary = decode_commands(r, 0x107E81, 0x1081DA)
	assert boundary == "exact scoped end"
	d["exchange_commands"] = commands
	ids = []
	for mid in range(494):
		b = struct.unpack_from("<I", r, 0x62D3E4 + 28 * mid + 20)[0] - 0x08000000
		assert 0 <= b < len(r) - 0x170
		for slot in range(15):
			a = b + 0x70 + slot * 16
			if r[a] == 0xFF:
				break
			ids.append(struct.unpack_from("<H", r, a + 14)[0])
	d["actor_id_inventory"] = {"map_count": 494, "actor_count": len(ids), "max_id": hex(max(ids)),
		"BFE_absent_from_actor_records": 0xBFE not in ids, "BFF_absent_from_actor_records": 0xBFF not in ids,
		"limitation": "Record inventory alone does not prove absence of script references or saved flag use"}
	assert sha(SOURCE.read_bytes()) == EXPECTED
	return d


if __name__ == "__main__":
	json.dump(analyze(), sys.stdout, indent=2)
	print()
