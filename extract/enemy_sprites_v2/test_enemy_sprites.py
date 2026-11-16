"""Read-only regression and independent composition checks for final v2 exports."""
import collections
import json
import struct
import subprocess
import sys
import unittest
import zlib

import extract_enemy_sprites as ex


def read_png(path):
	data = path.read_bytes()
	if data[:8] != b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
	p, compressed, size = 8, bytearray(), None
	while p < len(data):
		n = struct.unpack_from('>I',data,p)[0]
		tag, body = data[p+4:p+8], data[p+8:p+8+n]
		if zlib.crc32(tag+body)&0xFFFFFFFF != struct.unpack_from('>I',data,p+8+n)[0]:raise ValueError('CRC')
		if tag == b'IHDR':
			w,h,depth,kind,compression,filtering,interlace=struct.unpack('>2I5B',body)
			if (depth,kind,compression,filtering,interlace)!=(8,6,0,0,0):raise ValueError('Not simple RGBA')
			size=w,h
		if tag==b'IDAT':compressed.extend(body)
		p+=n+12
	w,h=size; raw=zlib.decompress(compressed)
	if len(raw)!=(w*4+1)*h:raise ValueError('Scanline size')
	if any(raw[y*(w*4+1)] for y in range(h)):raise ValueError('Unexpected PNG filter')
	return w,h,b''.join(raw[y*(w*4+1)+1:(y+1)*(w*4+1)] for y in range(h))


class V2Tests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.rom=(ex.ROOT/'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.output=ex.OUT/'final'
		cls.catalog=ex.rows(cls.output/'enemies.csv')
		cls.frames=ex.rows(cls.output/'frames.csv')

	def test_complete_accounting_and_blockers(self):
		self.assertEqual(len(self.catalog),182)
		self.assertEqual({int(r['enemy_id'],16) for r in self.catalog},set(range(182)))
		self.assertEqual(collections.Counter(r['v2_result'] for r in self.catalog),{'Preserved v1':127,'Newly verified':23,'Unresolved':32})
		unresolved=ex.rows(self.output/'unresolved.csv')
		self.assertEqual(collections.Counter('null' if 'Null' in r['reason'] else 'mismatch' if 'disagrees' in r['reason'] else 'stream' for r in unresolved),{'null':25,'mismatch':6,'stream':1})
		self.assertEqual(len(self.frames),314)
		for r in unresolved:self.assertFalse((self.output/f"enemy_{int(r['enemy_id'],16):02X}_frame0.png").exists())

	def test_every_v1_png_and_metadata_preserved(self):
		for path in ex.OLD.glob('*.png'):
			self.assertEqual(path.read_bytes(),(self.output/path.name).read_bytes(),path.name)
		self.assertEqual(len(list(ex.OLD.glob('*.png'))),508)
		by_key={(r['enemy_id'],r['frame_index']):r for r in self.frames}
		for old in ex.rows(ex.OLD/'frames.csv'):
			new=by_key[(old['enemy_id'],old['frame_index'])]
			self.assertEqual(old,{k:new[k] for k in old})

	def test_eight_earlier_detector_dragon_images(self):
		prior=ex.ROOT/'reverse_engineering/exports/palace_enemy_sprites'
		for eid,prefix in ((0xA5,'detector_A5'),(0x9C,'rattlin_dragon_9C')):
			for fi in range(2):
				for suffix in ('','_4x'):
					self.assertEqual((prior/f'{prefix}_frame{fi}{suffix}.png').read_bytes(),(self.output/f'enemy_{eid:02X}_frame{fi}{suffix}.png').read_bytes())

	def test_new_dimensions_are_composition_not_upload(self):
		for eid,dims,upload in ((0x17,(5,10),(10,5)),(0x9A,(6,9),(12,5)),(0x1A,(10,10),(12,8))):
			d=ex.new_record(self.rom,eid)
			self.assertEqual((d['tw'],d['th']),dims)
			self.assertEqual(tuple(d['frames'][0]['sources'][0]['upload'][2:]),upload)

	def test_independent_proof_for_every_new_frame(self):
		jp=(ex.ROOT/'Tomato Adventure (Japan).gba').read_bytes()
		for r in self.catalog:
			if r['v2_result']!='Newly verified':continue
			d=ex.new_record(self.rom,int(r['enemy_id'],16))
			for start,n in d['spans']:self.assertEqual(self.rom[start:start+n],jp[start:start+n])
			for f in d['frames']:
				name=f"enemy_{int(r['enemy_id'],16):02X}_frame{f['index']}.png"
				self.assertEqual(read_png(self.output/name),(d['tw']*8,d['th']*8,f['pixels']))

	def test_invalid_and_unresolved_are_rejected(self):
		for eid in (0x1B,0x1D,0x2E,0x43,0x45,0x47,0x49,0x8C):
			with self.assertRaises(ValueError):ex.new_record(self.rom,eid)
		with self.assertRaises(ValueError):ex.new_record(self.rom,0xA5)
		bad=bytearray(self.rom)
		struct.pack_into('<I',bad,ex.TABLE+0x17*76+0x44,0)
		with self.assertRaises(ValueError):ex.new_record(bad,0x17)

	def test_all_png_integrity_transparency_and_previews(self):
		for row in self.frames:
			p=self.output/row['png']; w,h,pixels=read_png(p)
			self.assertEqual((w,h),(int(row['width']),int(row['height'])))
			self.assertEqual(ex.v1.sha(p.read_bytes()),row['png_sha256'])
			self.assertEqual(set(pixels[3::4]),{0,255})
			pw,ph,preview=read_png(p.with_name(p.stem+'_4x.png'))
			self.assertEqual((pw,ph),(w*4,h*4))
			self.assertEqual(preview,ex.v1.enlarge(pixels,w,h))

	def test_exclusive_output_and_repeatability(self):
		p=subprocess.run([sys.executable,'-B',str(ex.ROOT/'tools/extract/enemy_sprites_v2/extract_enemy_sprites.py'),'--output',str(self.output)],capture_output=True,text=True)
		self.assertNotEqual(p.returncode,0)
		self.assertIn('FileExistsError',p.stderr)
		for path in self.output.glob('*.png'):
			self.assertEqual(path.read_bytes(),(ex.OUT/'verified'/path.name).read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)
