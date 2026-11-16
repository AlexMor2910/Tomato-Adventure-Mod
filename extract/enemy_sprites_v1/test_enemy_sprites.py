"""Regression, rejection and PNG integrity checks; no writes to existing assets."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import extract_enemy_sprites as ex


class EnemySpritesTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.rom = (ex.ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()

	def test_prior_fixtures_byte_identical(self):
		old = ex.ROOT / 'reverse_engineering/exports/palace_enemy_sprites'
		manifest = json.loads((old / 'extraction.json').read_text())
		for eid, prefix in ((0xA5, 'detector_A5'), (0x9C, 'rattlin_dragon_9C')):
			d = ex.decode_record(self.rom, eid)
			prior = next(e for e in manifest['enemies'] if int(e['id'], 16) == eid)
			for frame in d['frames']:
				self.assertEqual(ex.sha(frame['data']), prior['frames'][frame['index']]['decompressed_sha256'])
				for scale in (1, 4):
					w, h = d['tw'] * 8, d['th'] * 8
					pixels = frame['pixels'] if scale == 1 else ex.enlarge(frame['pixels'], w, h)
					filename = f"{prefix}_frame{frame['index']}" + ('_4x' if scale == 4 else '') + '.png'
					self.assertEqual(ex.png(w * scale, h * scale, pixels), (old / filename).read_bytes())

	def test_reject_unknown_dimensions_and_layout(self):
		for eid in (0x1A, 0x17):
			with self.assertRaises(ValueError):
				ex.decode_record(self.rom, eid)

	def test_reject_invalid_pointer(self):
		rom = bytearray(self.rom)
		struct.pack_into('<I', rom, ex.TABLE + 0xA5 * ex.STRIDE + 0x34, 0)
		with self.assertRaises(ValueError):
			ex.decode_record(rom, 0xA5)

	def test_reject_malformed_lz_and_rle(self):
		for data in (bytes.fromhex('10 03 00 00 80 00 00'), bytes.fromhex('30 02 00 00 80 01'), bytes.fromhex('10 04 00 00 00 01')):
			with self.assertRaises(ValueError):
				ex.decompress(data, 0)

	def test_supported_rle_and_overlapping_lz(self):
		self.assertEqual(ex.decompress(bytes.fromhex('30 03 00 00 80 12'), 0)[0], b'\x12' * 3)
		self.assertEqual(ex.decompress(bytes.fromhex('10 04 00 00 40 12 00 00'), 0)[0], b'\x12' * 4)

	def test_existing_output_refused(self):
		with tempfile.TemporaryDirectory() as directory:
			with self.assertRaises(FileExistsError):
				ex.export(ex.ROOT / 'Tomato Adventure (Japan) (patched).gba', ex.ROOT / 'Tomato Adventure (Japan).gba', Path(directory))

	def test_exported_png_integrity_and_alpha(self):
		folder = ex.ROOT / 'reverse_engineering/exports/enemy_sprites_v1/assets'
		import csv
		with (folder / 'frames.csv').open(encoding='utf-8') as stream:
			rows = list(csv.DictReader(stream))
		self.assertEqual(len(rows), 254)
		for row in rows:
			data = (folder / row['png']).read_bytes()
			self.assertEqual(ex.sha(data), row['png_sha256'])
			self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
			p, compressed = 8, bytearray()
			while p < len(data):
				n = struct.unpack_from('>I', data, p)[0]
				tag, body = data[p+4:p+8], data[p+8:p+8+n]
				self.assertEqual(zlib.crc32(tag + body) & 0xFFFFFFFF, struct.unpack_from('>I', data, p+8+n)[0])
				if tag == b'IHDR':
					self.assertEqual(struct.unpack('>2I5B', body), (int(row['width']), int(row['height']), 8, 6, 0, 0, 0))
				if tag == b'IDAT':
					compressed.extend(body)
				p += 12 + n
			raw = zlib.decompress(compressed)
			w, h = int(row['width']), int(row['height'])
			self.assertEqual(len(raw), h * (w * 4 + 1))
			alpha = set()
			for y in range(h):
				scan = raw[y*(w*4+1):(y+1)*(w*4+1)]
				self.assertEqual(scan[0], 0)
				alpha.update(scan[4::4])
			self.assertTrue(alpha <= {0, 255})
			self.assertIn(0, alpha)


if __name__ == '__main__':
	unittest.main(verbosity=2)
