"""Conservative, read-only base-frame extraction for verified direct enemy records.

Python standard library only. Refuses existing output directories. No sprite scan,
palette inference, animation reconstruction, or special-record interpretation.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/extract'))
from extract_field_maps import decompress, take, png
sys.path.insert(0, str(ROOT / 'tools/analyze'))
from extract_palace_enemy_sprites import render, enlarge

BUS, TABLE, STRIDE, COUNT, DIMS = 0x08000000, 0x634F50, 0x4C, 182, 0x486548
EN_SHA = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
JP_SHA = '0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12'


def sha(data):
	return hashlib.sha256(data).hexdigest()


def hx(value):
	return f'0x{value:08X}'


def names():
	text = (ROOT / 'tomatotrans-1.1.1/ta_enemies_eng.txt').read_text(encoding='utf-8-sig')
	section = text.split('NAMES:', 1)[1].split('ATTACKS:', 1)[0]
	result = {int(k, 16): v.strip() for k, v in re.findall(r'^([0-9A-Fa-f]{2})-E:(.*)$', section, re.M)}
	if set(result) != set(range(COUNT)) or not all(result.values()):
		raise ValueError('Expected 182 named enemy records')
	return result


def decode_record(rom, eid):
	"""Accept only the six-entry dimension table and canonical bank-6 rectangle."""
	if not 0 <= eid < COUNT:
		raise ValueError('Enemy ID outside established table')
	record = TABLE + eid * STRIDE
	raw = take(rom, record, STRIDE)
	index = raw[0x2F]
	# 0804C610..61A copies exactly 24 bytes onto the loader's stack.
	if index >= 6:
		raise ValueError(f'Unsupported dimension selector 0x{index:02X}; only indices 0..5 verified')
	tw, th = struct.unpack('<HH', take(rom, DIMS + index * 4, 4))
	if not (1 <= tw <= 32 and 1 <= th <= 16):
		raise ValueError('Dimensions outside bounded direct rectangle')
	pointers = struct.unpack_from('<4I', raw, 0x34)
	pal, f0, f1, layout = [p - BUS for p in pointers]
	palette_bytes = take(rom, pal, 32)
	layout_bytes = take(rom, layout, tw * th * 2)
	actual = struct.unpack('<' + 'H' * (tw * th), layout_bytes)
	if list(actual) != [0x6200 + y * 32 + x for y in range(th) for x in range(tw)]:
		raise ValueError('Layout is not the verified bank-6 unflipped rectangle')
	palette = []
	for n, color in enumerate(struct.unpack('<16H', palette_bytes)):
		palette.append(tuple(((color >> s & 31) << 3) | ((color >> s & 31) >> 2) for s in (0, 5, 10)) + (255 if n else 0,))
	frames = []
	for fi, source in enumerate((f0, f1)):
		data, consumed = decompress(rom, source, limit=tw * th * 32)
		if len(data) != tw * th * 32:
			raise ValueError(f'Frame {fi} size does not match dimensions')
		frames.append(dict(index=fi, source=source, consumed=consumed, data=data,
			pixels=render(data, tw, th, palette), format=f'GBA 0x{rom[source]:02X}; compact row-major 4bpp'))
	return dict(record=record, size_index=index, tw=tw, th=th, palette=pal,
		layout=layout, frames=frames, palette_bytes=palette_bytes, layout_bytes=layout_bytes)


def csv_new(path, rows):
	with path.open('x', encoding='utf-8', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=list(rows[0]))
		writer.writeheader()
		writer.writerows(rows)


def export(rom_path, jp_path, output, previews=False):
	rom, jp = rom_path.read_bytes(), jp_path.read_bytes()
	if sha(rom) != EN_SHA or sha(jp) != JP_SHA:
		raise ValueError('Source fingerprint mismatch; only verified JP/English baselines accepted')
	output.mkdir(parents=True, exist_ok=False)
	(output / '.gitignore').write_text('*\n!.gitignore\n', encoding='utf-8')
	catalog, metadata = [], []
	for eid, name in names().items():
		row = dict(enemy_id=f'0x{eid:02X}', enemy_name=name,
			record_file=hx(TABLE + eid * STRIDE), size_selector=rom[TABLE + eid * STRIDE + 0x2F],
			status='unresolved', reason='', confidence='Unconfirmed')
		try:
			d = decode_record(rom, eid)
			# Compare only relevant graphics fields and referenced source ranges.
			spans = [(d['record'] + 0x2F, 1), (d['record'] + 0x34, 16),
				(DIMS + d['size_index'] * 4, 4), (d['palette'], 32),
				(d['layout'], len(d['layout_bytes']))]
			spans += [(f['source'], f['consumed']) for f in d['frames']]
			if any(take(rom, p, n) != take(jp, p, n) for p, n in spans):
				raise ValueError('JP/English graphics spans differ; relocation review required')
		except ValueError as error:
			row['reason'] = str(error)
			catalog.append(row)
			continue
		row.update(status='verified_base_frames', confidence='Confirmed static')
		catalog.append(row)
		for f in d['frames']:
			w, h = d['tw'] * 8, d['th'] * 8
			filename = f"enemy_{eid:02X}_frame{f['index']}.png"
			image = png(w, h, f['pixels'])
			(output / filename).write_bytes(image)
			if previews:
				(output / filename.replace('.png', '_4x.png')).write_bytes(png(w * 4, h * 4, enlarge(f['pixels'], w, h)))
			metadata.append(dict(enemy_id=f'0x{eid:02X}', enemy_name=name,
				record_file=hx(d['record']), record_bus=hx(d['record'] + BUS),
				frame_index=f['index'], pointer_field_file=hx(d['record'] + 0x38 + 4 * f['index']),
				graphics_file=hx(f['source']), graphics_bus=hx(f['source'] + BUS),
				compressed_end_exclusive_file=hx(f['source'] + f['consumed']),
				width=w, height=h, size_selector=d['size_index'], dimensions_file=hx(DIMS + d['size_index'] * 4),
				palette_file=hx(d['palette']), palette_bus=hx(d['palette'] + BUS),
				palette_provenance='record +0x34; raw 16 BGR555 colors; loader 0804C6F4..0804C708; index 0 transparent',
				layout_file=hx(d['layout']), decoding_format=f['format'], confidence='Confirmed static',
				jp_english_source_spans_equal=True, decoded_sha256=sha(f['data']), png_sha256=sha(image),
				png=filename, limitations='Two base pointer slots only; animation timing, overlays and runtime states unresolved'))
	csv_new(output / 'enemies.csv', catalog)
	if metadata:
		csv_new(output / 'frames.csv', metadata)
	csv_new(output / 'unresolved.csv', [r for r in catalog if r['status'] == 'unresolved'] or [dict(enemy_id='', reason='None')])
	summary = dict(rom=str(rom_path), rom_sha256=EN_SHA, jp_sha256=JP_SHA,
		records=COUNT, verified=sum(r['status'] == 'verified_base_frames' for r in catalog),
		unresolved=sum(r['status'] == 'unresolved' for r in catalog), frames=len(metadata))
	(output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
	return summary


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--rom', type=Path, default=ROOT / 'Tomato Adventure (Japan) (patched).gba')
	parser.add_argument('--jp-rom', type=Path, default=ROOT / 'Tomato Adventure (Japan).gba')
	parser.add_argument('--output', type=Path, required=True)
	parser.add_argument('--previews', action='store_true')
	args = parser.parse_args()
	print(json.dumps(export(args.rom, args.jp_rom, args.output, args.previews), indent=2))
