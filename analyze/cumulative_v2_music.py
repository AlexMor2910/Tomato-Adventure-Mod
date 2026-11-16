"""Bounded music/title/room audit from retained map records and script roots.

No emulator, new asset extraction, or ROM writes. Outputs are exclusive.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/analyze'), str(ROOT / 'tools/extract')]
from thumb_inspect import inspect
from extract_field_maps import png

BUS = 0x08000000
TABLE = 0x62D3E4
V1 = ROOT / 'tools/patch/output/cumulative-v1-20261028/build/tomato_cumulative_v1_INCOMPLETE.gba'
DIRECTORY = ROOT / 'tools/patch/output/cumulative-v2-20261028'
GROUPS = {
	'Dropper Village': [1, 2, 3, 4, 5, 6, 7, 0x1D],
	'Mayonen Caverns': list(range(0x1E, 0x2C)) + [0x2E],
	'Captain Grocko Ship': list(range(0xE2, 0xFB)) + list(range(0x99, 0x9D)),
	'Oyster Sewers': list(range(0x8F, 0x99)),
	'The Vault': [0x124] + list(range(0x125, 0x12C)) + list(range(0x150, 0x155)) + [0x158] + list(range(0x1E7, 0x1EB)),
}
TRACKS = {'Pokypine Forest': (13, [8, 12]), 'Mayonen': (7, [0x48]),
	'Namp Lagoon': (36, [0x60, 0x5F]), 'Oystown': (16, [0x104, 0x1EC]), 'Oops Mannor': (8, [0x38])}
DEST = dict(zip(GROUPS, TRACKS))


def sha(data):
	return hashlib.sha256(data).hexdigest()


def save(path, data):
	with path.open('x', encoding='utf-8') as f:
		json.dump(data, f, indent=2)
		f.write('\n')


def read_png(path):
	data = path.read_bytes()
	pos, packed = 8, b''
	while pos < len(data):
		size = struct.unpack_from('>I', data, pos)[0]
		tag, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + size]
		assert zlib.crc32(tag + body) == struct.unpack_from('>I', data, pos + size + 8)[0]
		if tag == b'IHDR':
			w, h = struct.unpack_from('>II', body)
		if tag == b'IDAT':
			packed += body
		pos += size + 12
	decoded = zlib.decompress(packed)
	assert all(decoded[y * (4 * w + 1)] == 0 for y in range(h))
	return w, h, b''.join(decoded[y * (4 * w + 1) + 1:(y + 1) * (4 * w + 1)] for y in range(h))


def review_sheets():
	for n, (area, ids) in enumerate(GROUPS.items()):
		width, height = 800, 128 * ((len(ids) + 3) // 4)
		out = bytearray(b'\x30\x30\x30\xff' * width * height)
		for i, mid in enumerate(ids):
			path = ROOT / 'reverse_engineering/exports/field_maps_v1' / f'map_{mid:04X}.png'
			if not path.exists():
				continue
			w, h, pixels = read_png(path)
			scale = min(196 / w, 124 / h, 1)
			nw, nh = int(w * scale), int(h * scale)
			for y in range(nh):
				for x in range(nw):
					q = (int(y / scale) * w + int(x / scale)) * 4
					p = (((i // 4) * 128 + y) * width + (i % 4) * 200 + x) * 4
					out[p:p + 4] = pixels[q:q + 4]
		path = DIRECTORY / f'review_{n}.png'
		with path.open('xb') as f:
			f.write(png(width, height, out))
		print(n, area, 'row-major', ' '.join(f'{m:04X}' for m in ids))


def roots(rom, mid):
	a = TABLE + mid * 28
	events = struct.unpack_from('<I', rom, a + 16)[0] - BUS
	result = [(struct.unpack_from('<I', rom, events)[0] - BUS, 'default', events)]
	for i in range(128):
		p = events + 4 + 8 * i
		if rom[p] == 255:
			break
		result.append((struct.unpack_from('<I', rom, p + 4)[0] - BUS, 'rectangle', p))
	else:
		raise ValueError('Rectangle limit')
	actors = struct.unpack_from('<I', rom, a + 20)[0] - BUS
	for i in range(15):
		p = actors + 112 + 16 * i
		if rom[p] == 255:
			break
		# Actor initialization and ordinary interaction are distinct contexts.
		result.append((struct.unpack_from('<I', rom, p + 6)[0] - BUS, 'actor_initializer', p))
		if not rom[p] & 128 and not rom[p + 1] & 128:
			result.append((struct.unpack_from('<I', rom, p + 10)[0] - BUS, 'actor_interaction', p))
	return sorted(set(result))


def walk(rom, entries, budget=10000):
	"""Conservative pointer closure, not a claim that every edge executes.

	All in-operand script-range pointers are overapproximated, retaining false
	paths. Native targets, FD84 dynamic entries and map changes are reported.
	"""
	queue = [p for p, kind, owner in entries if 0xF9000 <= p < 0x13D1EC]
	seen, commands, dynamic, transfers = set(), {}, [], []
	while queue and len(seen) < budget:
		p = queue.pop()
		if p in seen or not 0xF9000 <= p < 0x13D1EC - 16:
			continue
		seen.add(p)
		fam = rom[p]
		op = rom[p + 1] if fam in (0xFD, 0xFE) else fam
		table = {0xFD: 0x62B815, 0xFE: 0x62B736}.get(fam, 0x62B6C4)
		head = 2 if fam in (0xFD, 0xFE) else 1
		size = head + rom[table + op]
		raw = rom[p:p + size]
		commands[p] = raw
		if fam == 0xFD and op == 0x84:
			dynamic.append(p)
		if fam == 0xFE and op in (0x7C, 0x7D):
			transfers.append(p)
			continue
		if fam == 0xFD and op in (0x7C, 0x7D):
			continue
		if fam not in (0xFD, 0xFE) and op in (0x2F,):
			continue
		for delta in range(head, size - 3):
			q = struct.unpack_from('<I', raw, delta)[0] - BUS
			if 0xF9000 <= q < 0x13D1EC:
				queue.append(q)
		if not (fam == 0xFD and op == 0x30):
			queue.append(p + size)
	return commands, dict(visited=len(seen), budget_exhausted=bool(queue),
		dynamic_entries=sorted(set(dynamic)), transfers=sorted(set(transfers)))


def main():
	if len(sys.argv) > 1 and sys.argv[1] == 'review':
		review_sheets()
		return
	r = V1.read_bytes()
	assert len(r) == 0x800000 and sha(r) == '1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f'
	pointers = (ROOT / 'tomatotrans-1.1.1/pointers1.dat').read_text().splitlines()
	site_messages = {int(site, 16): i for i, line in enumerate(pointers) for site in line.split() if site != 'FFFFFFFF'}
	text = (ROOT / 'tomatotrans-1.1.1/ta_script_eng.txt').read_text(encoding='utf-8-sig')
	texts = {int(mid, 16): value for mid, value in re.findall(r'(?ms)^([0-9A-F]{3})-E:(.*?)(?=\n\n[0-9A-F]{3}-E:|\Z)', text)}
	output = []
	for area, mids in GROUPS.items():
		for mid in mids:
			entries = roots(r, mid)
			commands, status = walk(r, entries)
			messages = sorted({site_messages[p + d] for p, raw in commands.items() for d in range(len(raw) - 3) if p + d in site_messages})
			a = TABLE + mid * 28
			resource = struct.unpack_from('<H', r, a)[0]
			output.append(dict(area=area, map_id=mid, raw_record=r[a:a + 28].hex(' '),
				title_field=r[a + 2], title_index=r[a + 2] >> 2, selector=r[a + 5] & 63,
				resource=resource, palette=hex(struct.unpack_from('<I', r, 0x255F00 + resource * 4)[0]),
				tileset=hex(struct.unpack_from('<I', r, 0x15BA3C + resource * 4)[0]),
				roots=entries, traversal=status,
				overrides=[dict(file=p, bytes=raw.hex(' ')) for p, raw in sorted(commands.items()) if raw[:2] in [b'\xfe\xa7', b'\xfe\xa8', b'\xfe\xa9', b'\xfe\xab']],
				messages=[dict(id=hex(i), text=texts.get(i, '')) for i in messages],
				command_count=len(commands)))
	save(DIRECTORY / 'bounded_script_audit.json', output)
	for area in GROUPS:
		rows = [x for x in output if x['area'] == area]
		print(area, 'rooms', len(rows), 'overrides', sorted({(hex(o['file']), o['bytes']) for row in rows for o in row['overrides']}))
		for row in rows:
			print(f"{row['map_id']:04X}", row['palette'], row['tileset'], row['traversal'],
				[(x['id'], x['text'][:95].replace('\n', ' ')) for x in row['messages'] if re.search('Garco|Diary|[Ss]ewer|[Ss]afe|[Mm]ayo|[Ss]pillage|[Cc]avern', x['text'])])


if __name__ == '__main__':
	main()
