"""Static structural, hash, composition and regression checks; ROMs read only."""
import json
import struct
import unittest
import extract_enemy_sprites as ex


class EnemyTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.rom,cls.jp=ex.v3.load_roms()
		cls.out=ex.ROOT/'reverse_engineering/exports/enemy_sprites_v4/final'
		cls.frames=json.loads((cls.out/'frames.json').read_text())

	def test_all_182_and_resource_accounting(self):
		rows=json.loads((self.out/'coverage.json').read_text())
		self.assertEqual([int(r['enemy_id'],16) for r in rows],list(range(182)))
		s=json.loads((self.out/'summary.json').read_text())
		self.assertEqual(list(s['counts'].values()),[123,33,25,1])
		self.assertEqual(len(self.frames),326)

	def test_all_pixels_and_source_spans(self):
		for eid in sorted({int(f['enemy_id'],16) for f in self.frames}):
			d=ex.decode(self.rom,eid)
			for start,n in d['spans']:self.assertEqual(self.rom[start:start+n],self.jp[start:start+n])
			for f in d['frames']:
				row=next(r for r in self.frames if int(r['enemy_id'],16)==eid and r['frame_index']==f['index'])
				self.assertEqual(ex.v1.sha(f['pixels']),row['pixel_sha256'])
				self.assertEqual(ex.v1.png(d['tw']*8,d['th']*8,f['pixels']),(self.out/row['png']).read_bytes())

	def test_detector_dragon_original_png_and_tile_hashes(self):
		prior=ex.ROOT/'reverse_engineering/exports/palace_enemy_sprites'
		manifest=json.loads((prior/'extraction.json').read_text())
		for eid,prefix,dims in ((0xA5,'detector_A5',(5,5)),(0x9C,'rattlin_dragon_9C',(10,5))):
			d=ex.decode(self.rom,eid);self.assertEqual((d['tw'],d['th']),dims)
			old=next(e for e in manifest['enemies'] if int(e['id'],16)==eid)
			for f in d['frames']:
				self.assertEqual(ex.v1.sha(f['data']),old['frames'][f['index']]['decompressed_sha256'])
				for scale in (1,4):
					w,h=d['tw']*8,d['th']*8
					pixels=f['pixels'] if scale==1 else ex.v1.enlarge(f['pixels'],w,h)
					name=f"{prefix}_frame{f['index']}"+('_4x' if scale==4 else '')+'.png'
					self.assertEqual(ex.v1.png(w*scale,h*scale,pixels),(prior/name).read_bytes())

	def test_structurally_different_profiles(self):
		for eid,dims in ((0x02,(7,7)),(0x17,(5,10)),(0x9A,(6,9)),(0x1A,(10,10))):
			d=ex.decode(self.rom,eid);self.assertEqual((d['tw'],d['th']),dims)
		self.assertTrue(any(len(ex.decode(self.rom,eid)['frames'])==4 for eid in range(182) if eid in ex.v2.TARGETS and eid not in ex.v3.TARGETS))
		for eid in ex.v3.DISAGREEMENTS:
			d=ex.decode(self.rom,eid);self.assertEqual(len(d['frames']),2)
			self.assertIn('BG differs',d['kind'])

	def test_sharing_is_source_identity(self):
		rows=json.loads((self.out/'coverage.json').read_text());byid={r['enemy_id']:r for r in rows}
		for r in rows:
			if r['shared_with']:
				owner=byid[r['shared_with']]
				self.assertEqual((r['graphics_resource'],r['palette_resource']),(owner['graphics_resource'],owner['palette_resource']))

	def test_strict_compression_palette_and_tile_order(self):
		self.assertEqual(ex.v1.decompress(bytes.fromhex('30 03 00 00 80 12'),0)[0],b'\x12'*3)
		self.assertEqual(ex.v1.decompress(bytes.fromhex('10 04 00 00 40 12 00 00'),0)[0],b'\x12'*4)
		for data in ('30 02 00 00 80 01','10 03 00 00 80 00 00','10 04 00 00 00 01'):
			with self.assertRaises(ValueError):ex.v1.decompress(bytes.fromhex(data),0)
		palette=ex.v2.colors(struct.pack('<16H',0,*range(1,16)))
		self.assertEqual(palette[0][3],0);self.assertEqual(palette[1],(8,0,0,255))
		pixels=ex.v1.render(bytes([0x21])*32,1,1,palette)
		self.assertEqual(pixels[:8],bytes(palette[1])+bytes(palette[2]))

	def test_unsupported_and_rle_blocker(self):
		for eid in (-1,182,0x1B,0x8C):
			with self.assertRaises(ValueError):ex.decode(self.rom,eid)
		ledger=ex.v3.strict_rle_ledger(self.rom,0x5D2BA8)
		self.assertEqual((ledger['advertised'],ledger['overshoot']),(3072,128))
		self.assertEqual(len(ex.v3.null_classifications(self.rom)),25)

	def test_existing_output_refused(self):
		with self.assertRaises(FileExistsError):ex.export(self.out)


if __name__=='__main__':unittest.main(verbosity=2)
