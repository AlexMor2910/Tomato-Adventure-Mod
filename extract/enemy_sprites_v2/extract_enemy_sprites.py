"""Evidence-gated v2 extension; read-only ROM input and exclusive new outputs."""
import argparse
import collections
import csv
import importlib.util
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('enemy_v1', ROOT / 'tools/extract/enemy_sprites_v1/extract_enemy_sprites.py')
v1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from thumb_inspect import decode

BUS, TABLE, STRIDE = v1.BUS, v1.TABLE, v1.STRIDE
OLD = ROOT / 'reverse_engineering/exports/enemy_sprites_v1/assets'
OUT = ROOT / 'reverse_engineering/exports/enemy_sprites_v2'


def rows(path):
	with path.open(encoding='utf-8') as stream:
		return list(csv.DictReader(stream))


OLD_IDS = {int(r['enemy_id'], 16) for r in rows(OLD / 'frames.csv')}
TARGETS = {int(r['enemy_id'], 16) for r in rows(OLD / 'unresolved.csv')}
assert len(OLD_IDS) == 127 and len(TARGETS) == 55 and not OLD_IDS & TARGETS


def ptr(rom, field, spans):
	value = struct.unpack('<I', v1.take(rom, field, 4))[0] - BUS
	v1.take(rom, value, 1)
	spans.append((field, 4))
	return value


def colors(data):
	return [tuple(((c >> s & 31) << 3) | ((c >> s & 31) >> 2) for s in (0, 5, 10)) + (255 if i % 16 else 0,)
		for i, c in enumerate(struct.unpack('<' + 'H' * (len(data) // 2), data))]


def pixel(atlas, tile, x, y, palette, bank):
	if tile not in atlas:
		raise ValueError(f'Layout/OAM references unloaded tile 0x{tile:03X}')
	if bank not in palette:
		raise ValueError(f'Layout/OAM references unloaded palette bank {bank}')
	raw = atlas[tile]
	n = raw[y * 4 + x // 2] >> (4 * (x & 1)) & 15
	return bytes(palette[bank][n])


def layout_render(atlas, entries, tw, th, palette):
	result = bytearray(tw * th * 256)
	for y in range(th * 8):
		for x in range(tw * 8):
			e = entries[(y // 8) * tw + x // 8]
			sx, sy = x % 8, y % 8
			if e & 0x400:
				sx = 7 - sx
			if e & 0x800:
				sy = 7 - sy
			p = (y * tw * 8 + x) * 4
			result[p:p+4] = pixel(atlas, e & 1023, sx, sy, palette, e >> 12)
	return bytes(result)


def object_render(rom, record, tw, th, atlas, palette, spans):
	"""Independent OBJ reconstruction: first descriptor frame, 2D tile pitch 32.

	Validate the raw-pixel canvas using hardware OBJ shape/size fields. Reject
	affine, mosaic, special modes, off-canvas objects and incompatible dimensions.
	"""
	# The generic draw helper obtains the descriptor index from these scripts.
	# Prove descriptor 0 is selected through the supported base cycle, rather
	# than assuming the first descriptor happens to be the active one.
	script_table = ptr(rom, record + 0x48, spans)
	if rom[record + 0x2F] < 6:
		script_table = ptr(rom, script_table, spans)
		script_count = 1
	else:
		script_count = 2 if (rom[record + 0x2F] >> 4 & 3) == 0 else 4
	scripts = []
	for fi in range(script_count):
		script = ptr(rom, script_table + fi * 4, spans)
		data = v1.take(rom, script, 6)
		spans.append((script, 6))
		index, duration, end = struct.unpack('<3H', data)
		if index != 0 or not 0 < duration < 256 or end != 0xFFFF:
			raise ValueError('Descriptor selection script is not the verified one-entry loop')
		scripts.append(dict(file=v1.hx(script),descriptor_index=index,duration=duration))
	table = ptr(rom, record + 0x44, spans)
	if rom[record + 0x2F] < 6:
		# Ordinary actor setup dereferences record +44 once (0804BE7C..7E).
		table = ptr(rom, table, spans)
	descriptor = ptr(rom, table, spans)
	n = struct.unpack('<H', v1.take(rom, descriptor, 2))[0]
	if not 0 < n <= 128:
		raise ValueError('Unsupported OAM object count/format')
	raw = v1.take(rom, descriptor + 2, n * 6)
	spans.append((descriptor, 2 + n * 6))
	sizes = (((8,8),(16,16),(32,32),(64,64)), ((16,8),(32,8),(32,16),(64,32)), ((8,16),(8,32),(16,32),(32,64)))
	objects = []
	for a, b, c in struct.iter_unpack('<3H', raw):
		shape, size = a >> 14, b >> 14
		if shape >= 3 or a & 0x3F00:
			raise ValueError('Unsupported OBJ affine/mode/mosaic/depth')
		w, h = sizes[shape][size]
		x, y = b & 511, a & 255
		x = x - 512 if x >= 256 else x
		y = y - 256 if y >= 128 else y
		objects.append((x, y, w, h, b, c))
	left, top = min(o[0] for o in objects), min(o[1] for o in objects)
	right, bottom = max(o[0] + o[2] for o in objects), max(o[1] + o[3] for o in objects)
	if tw is not None and (right - left, bottom - top) != (tw * 8, th * 8):
		raise ValueError(f'OAM bounds {right-left}x{bottom-top} differ from declared {tw*8}x{th*8}')
	if (right-left) % 8 or (bottom-top) % 8 or not 0 < (right-left)*(bottom-top) <= 128*128:
		raise ValueError('Unsupported object canvas bounds')
	tw, th = (right-left)//8, (bottom-top)//8
	result = bytearray(tw * th * 256)
	# Lower OAM index wins at equal priority. All tested lists have common priority.
	if len({o[5] >> 10 & 3 for o in objects}) != 1:
		raise ValueError('Mixed OBJ priority requires separate proof')
	for ox, oy, w, h, flags, attr in reversed(objects):
		for y in range(h):
			for x in range(w):
				sx = w - 1 - x if flags & 0x1000 else x
				sy = h - 1 - y if flags & 0x2000 else y
				tile = (attr & 1023) + sy // 8 * 32 + sx // 8
				value = pixel(atlas, tile, sx % 8, sy % 8, palette, attr >> 12)
				if value[3]:
					p = ((oy - top + y) * tw * 8 + ox - left + x) * 4
					result[p:p+4] = value
	return bytes(result), dict(table_file=v1.hx(table), descriptor_file=v1.hx(descriptor), count=n, bounds=[left, top, right, bottom], dimensions_tiles=[tw,th], scripts=scripts)


def visible_equal(a, b):
	# Unwritten OBJ pixels contain zero RGB; the legacy tile renderer preserves
	# palette-zero RGB. Compare alpha and visible RGB, never discard opaque pixels.
	return len(a) == len(b) and all(a[p+3] == b[p+3] and (not a[p+3] or a[p:p+3] == b[p:p+3]) for p in range(0, len(a), 4))


def upload(atlas, data, tw, th, x):
	if len(data) != tw * th * 32 or x + tw > 32:
		raise ValueError('Invalid compact upload dimensions')
	for y in range(th):
		for tx in range(tw):
			atlas[512 + y * 32 + x + tx] = data[(y * tw + tx) * 32:(y * tw + tx + 1) * 32]


def new_record(rom, eid):
	if eid not in TARGETS:
		raise ValueError('v2 investigation is restricted to the 55 unresolved IDs')
	record = TABLE + eid * STRIDE
	raw = v1.take(rom, record, STRIDE)
	spans = [(record + 0x2D, 3), (record + 0x34, 24)]
	if raw[0x34:0x44] == bytes(16):
		raise ValueError('Null graphics/palette/layout pointers; shared-owner linkage not proved')
	index = raw[0x2F]
	frames = []
	if index < 6:
		uw, uh = struct.unpack('<HH', v1.take(rom, v1.DIMS + index * 4, 4))
		spans.append((v1.DIMS + index * 4, 4))
		pal = ptr(rom, record + 0x34, spans)
		pb = v1.take(rom, pal, 32)
		spans.append((pal, 32))
		palette = {6: colors(pb)}
		layout = ptr(rom, record + 0x40, spans)
		for fi in range(2):
			field = record + 0x38 + 4 * fi
			source = ptr(rom, field, spans)
			data, count = v1.decompress(rom, source, uw * uh * 32)
			spans.append((source, count))
			atlas = {}
			upload(atlas, data, uw, uh, 0)
			obj, proof = object_render(rom, record, None, None, atlas, palette, spans)
			tw, th = proof['dimensions_tiles']
			lb = v1.take(rom, layout, tw * th * 2)
			spans.append((layout, len(lb)))
			entries = struct.unpack('<' + 'H' * (tw * th), lb)
			pixels = layout_render(atlas, entries, tw, th, palette)
			if not visible_equal(pixels, obj):
				raise ValueError('Direct tilemap image disagrees with independent OAM composition')
			frames.append(dict(index=fi, pixels=pixels, sources=[dict(field=field, source=source, consumed=count, format=f'0x{rom[source]:02X}', decoded_sha256=v1.sha(data), upload=[0,0,uw,uh])], oam=proof))
		kind, dims = 'direct compact 4bpp upload; descriptor-bounded tilemap; independent OAM match', proof['descriptor_file']
		palette_table = ''
	else:
		parts, mode = index >> 6, index >> 4 & 3
		if parts not in (2, 3) or mode not in (0, 1):
			raise ValueError('Unsupported multipart count/frame mode')
		tw, th = raw[0x2E] >> 4, raw[0x2E] & 15
		if not (1 <= tw <= 15 and 1 <= th <= 15):
			raise ValueError('Invalid multipart canvas')
		palette_table = ptr(rom, record + 0x34, spans)
		pal = ptr(rom, palette_table, spans)
		pb = v1.take(rom, pal, 128)
		spans.append((pal, 128))
		all_colors = colors(pb)
		palette = {6 + b: all_colors[b*16:(b+1)*16] for b in range(4)}
		layout = ptr(rom, record + 0x40, spans)
		lb = v1.take(rom, layout, tw * th * 2)
		spans.append((layout, len(lb)))
		entries = struct.unpack('<' + 'H' * (tw * th), lb)
		base_table = ptr(rom, record + 0x38, spans)
		state_table = ptr(rom, record + 0x3C, spans)
		# Only initial flag state zero; no speculative combinations of actor state.
		part_table = ptr(rom, state_table, spans)
		part_frames = [ptr(rom, part_table + 4 * i, spans) for i in range(parts)]
		for fi in range(2 if mode == 0 else 4):
			atlas, sources = {}, []
			for field, uw, uh, x in [(base_table + 4*fi, 12, 8, 0)] + [(t + 4*fi, 6, 8, 12 + i*6) for i,t in enumerate(part_frames)]:
				source = ptr(rom, field, spans)
				data, count = v1.decompress(rom, source, uw * uh * 32)
				spans.append((source, count))
				upload(atlas, data, uw, uh, x)
				sources.append(dict(field=field, source=source, consumed=count, format=f'0x{rom[source]:02X}', decoded_sha256=v1.sha(data), upload=[x,0,uw,uh]))
			pixels = layout_render(atlas, entries, tw, th, palette)
			obj, proof = object_render(rom, record, tw, th, atlas, palette, spans)
			if not visible_equal(pixels, obj):
				raise ValueError('Multipart tilemap disagrees with independent OAM composition')
			frames.append(dict(index=fi, pixels=pixels, sources=sources, oam=proof))
		kind, dims = 'multipart 4bpp VRAM atlas; row-major tilemap; independent OAM match', v1.hx(record + 0x2E)
	return dict(record=record, tw=tw, th=th, palette=pal, palette_table=palette_table,
		palette_bytes=len(pb), layout=layout, dimensions_file=dims, kind=kind,
		spans=sorted(set(spans)), frames=frames, state=0)


def main():
	p = argparse.ArgumentParser(description=__doc__)
	p.add_argument('--output', type=Path, required=True)
	p.add_argument('--previews', action='store_true')
	args = p.parse_args()
	rom = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	jp = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
	if v1.sha(rom) != v1.EN_SHA or v1.sha(jp) != v1.JP_SHA:
		raise ValueError('ROM fingerprints do not match verified baselines')
	args.output.mkdir(parents=True, exist_ok=False)
	def write(name, data):
		with (args.output / name).open('xb') as stream:
			stream.write(data)
	write('.gitignore', b'*\n!.gitignore\n')
	catalog, metadata, evidence = [], [], []
	old_frames = rows(OLD / 'frames.csv')
	for row in rows(OLD / 'enemies.csv'):
		eid = int(row['enemy_id'], 16)
		if eid in OLD_IDS:
			# No new static investigation of these records: frozen decoder regression.
			d = v1.decode_record(rom, eid)
			for f in d['frames']:
				for scale in ((1,4) if args.previews else (1,)):
					w,h = d['tw']*8,d['th']*8
					image = v1.png(w*scale,h*scale,f['pixels'] if scale == 1 else v1.enlarge(f['pixels'],w,h))
					name = f"enemy_{eid:02X}_frame{f['index']}" + ('_4x' if scale == 4 else '') + '.png'
					if image != (OLD / name).read_bytes():
						raise ValueError('v1 PNG regression mismatch: ' + name)
					write(name, image)
			for old in (f for f in old_frames if int(f['enemy_id'],16) == eid):
				metadata.append(dict(old, v2_mapping='Preserved v1', state='v1', source_details='', oam_proof=''))
			catalog.append(dict(row, v2_result='Preserved v1'))
			continue
		try:
			d = new_record(rom, eid)
			if any(v1.take(rom,a,n) != v1.take(jp,a,n) for a,n in d['spans']):
				raise ValueError('Japanese/English evidence spans differ')
		except ValueError as error:
			catalog.append(dict(row, reason=str(error), v2_result='Unresolved'))
			evidence.append(dict(enemy_id=row['enemy_id'], confidence='Unconfirmed', blocker=str(error)))
			continue
		catalog.append(dict(row, status='verified_base_frames', reason='', confidence='Confirmed static', v2_result='Newly verified'))
		proof = dict(enemy_id=row['enemy_id'], confidence='Confirmed', kind=d['kind'], dimensions_tiles=[d['tw'],d['th']],
			palette_file=v1.hx(d['palette']), palette_table_file=v1.hx(d['palette_table']) if d['palette_table'] != '' else '',
			palette_bytes=d['palette_bytes'], layout_file=v1.hx(d['layout']),
			spans=[dict(file=v1.hx(a),size=n,sha256=v1.sha(v1.take(rom,a,n)),jp_english_equal=True) for a,n in d['spans']], frames=[])
		for f in d['frames']:
			w,h = d['tw']*8,d['th']*8
			filename = f"enemy_{eid:02X}_frame{f['index']}.png"
			image = v1.png(w,h,f['pixels'])
			write(filename,image)
			if args.previews:
				write(filename.replace('.png','_4x.png'),v1.png(w*4,h*4,v1.enlarge(f['pixels'],w,h)))
			sources = f['sources']
			fr = dict(index=f['index'], sources=sources, oam=f['oam'], oam_visible_pixels_equal=True, pixel_sha256=v1.sha(f['pixels']), png=filename, png_sha256=v1.sha(image))
			proof['frames'].append(fr)
			metadata.append(dict(enemy_id=row['enemy_id'],enemy_name=row['enemy_name'],record_file=v1.hx(d['record']),record_bus=v1.hx(d['record']+BUS),
				frame_index=f['index'],pointer_field_file='|'.join(v1.hx(s['field']) for s in sources),graphics_file='|'.join(v1.hx(s['source']) for s in sources),
				graphics_bus='|'.join(v1.hx(s['source']+BUS) for s in sources),compressed_end_exclusive_file='|'.join(v1.hx(s['source']+s['consumed']) for s in sources),
				width=w,height=h,size_selector=row['size_selector'],dimensions_file=d['dimensions_file'],palette_file=v1.hx(d['palette']),palette_bus=v1.hx(d['palette']+BUS),
				palette_provenance=('record +0x34 direct 16 colors' if d['palette_bytes']==32 else 'record +0x34 -> palette table[0] -> 4 consecutive BGR555 banks 6..9'),
				layout_file=v1.hx(d['layout']),decoding_format=d['kind']+'; GBA '+ '|'.join(sorted({s['format'] for s in sources})),confidence='Confirmed static',jp_english_source_spans_equal=True,
				decoded_sha256='|'.join(s['decoded_sha256'] for s in sources),png_sha256=v1.sha(image),png=filename,
				limitations='Palette set 0, per-part actor flag state 0, base frame cycle only; encounter reachability, other states, script effects and overlays unresolved',v2_mapping='Newly verified',state=0,
				source_details=json.dumps(sources,separators=(',',':')),oam_proof=json.dumps(f['oam'],separators=(',',':'))))
		evidence.append(proof)
	v1.csv_new(args.output/'enemies.csv',catalog)
	v1.csv_new(args.output/'frames.csv',metadata)
	v1.csv_new(args.output/'unresolved.csv',[r for r in catalog if r['v2_result']=='Unresolved'])
	write('evidence.json',(json.dumps(evidence,indent=2)+'\n').encode())
	summary=dict(records=182,preserved=127,newly_verified=sum(r['v2_result']=='Newly verified' for r in catalog),unresolved=sum(r['v2_result']=='Unresolved' for r in catalog),frames=len(metadata))
	write('summary.json',(json.dumps(summary,indent=2)+'\n').encode())
	print(json.dumps(summary,indent=2))


if __name__ == '__main__':
	main()
