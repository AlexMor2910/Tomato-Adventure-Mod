"""Bounded native OBJ regression, structure and output integrity tests."""
import json
from pathlib import Path
import struct
import unittest

import extract_field_sprites as ex
from preview_field_sprites import read_png


class FieldSpriteTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.en,cls.jp=ex.load_roms()
		cls.frames=json.loads((ex.OUT/'frames.json').read_text())
		cls.resources=json.loads((ex.OUT/'resources.json').read_text())

	def test_map_actor_and_resource_census(self):
		resources,bindings,actors,unbound=ex.discover(self.en)
		self.assertEqual((len(resources),len(bindings),len(actors),len(unbound)),(371,522,2987,4))
		self.assertEqual(len(self.resources),371)
		self.assertEqual(sum(r['status']=='partial' for r in self.resources),29)
		self.assertEqual(sum('palette unbound' in r['status'] for r in self.resources),10)

	def test_known_native_pixel_fixtures(self):
		fixtures=[(0x13E58C,0x43B1EC,(16,24),'385476fa2f43667b70035b9c8d5ccd3553804dbe70efa093667abfcc66e2fbcc'),
			(0x13E67C,0x43C6EC,(16,16),'4a0e559e4cfb142f425057c806e9a3b2d175bf6a726ff9ecdd568c50ee492088'),
			(0x13F45C,0x43C86C,(24,32),'2b657bc95e353631f6a61dba3cef6124565b5c5f69d796ed2da611005ff5b835')]
		for resource,pal,dims,digest in fixtures:
			f=ex.descriptor(self.en,resource,0);gfx=ex.pointer(self.en,resource+4);n=self.en[resource+3]*32
			pixels=ex.render(self.en[gfx:gfx+n],f,ex.palette(self.en,pal))
			self.assertEqual(ex.sha(pixels),digest)
			self.assertEqual((f['bounds'][2]-f['bounds'][0],f['bounds'][3]-f['bounds'][1]),dims)

	def test_1d_tile_stride_flip_palette_override_and_priority(self):
		gfx=b''.join(bytes([i|(i<<4)])*32 for i in range(1,5))
		colors=[b'\0'*4]+[bytes([i,0,0,255]) for i in range(1,16)]
		obj=dict(index=0,x=-8,y=-16,width=16,height=16,tile=0,hflip=False,vflip=False,priority=2)
		frame=dict(bounds=[-8,-16,8,0],objects=[obj])
		p=ex.render(gfx,frame,colors)
		self.assertEqual([p[(y*16+x)*4] for x,y in ((0,0),(8,0),(0,8),(8,8))],[1,2,3,4])
		obj['hflip']=True;p=ex.render(gfx,frame,colors)
		self.assertEqual([p[(y*16+x)*4] for x,y in ((0,0),(8,0),(0,8),(8,8))],[2,1,4,3])
		obj['hflip']=False
		frame['objects'].append(dict(obj,index=1,tile=0,priority=3))
		self.assertEqual(ex.render(gfx,frame,colors),ex.render(gfx,dict(frame,objects=[obj]),colors))

	def test_all_png_crc_hash_dimensions_and_transparency(self):
		count=0
		for r in self.frames:
			if not r['png']:
				self.assertIsNone(r['bounds']);continue
			path=ex.OUT/r['png'];w,h,pixels=read_png(path)
			self.assertEqual((w,h),(r['width'],r['height']))
			self.assertEqual(ex.sha(pixels),r['pixel_sha256'])
			self.assertEqual(ex.sha(path.read_bytes()),r['png_sha256'])
			self.assertTrue(set(pixels[3::4])<={0,255});count+=1
		self.assertEqual((count,len(self.frames)),(4390,4412))

	def test_all_recorded_spans_match_both_baselines(self):
		for name in ('evidence.json','discovery_evidence.json'):
			rows=json.loads((ex.OUT/name).read_text());spans=rows if name.startswith('discovery') else [s for r in rows for s in r['spans']]
			for s in spans:
				p,n=int(s['file'],16),s['size']
				self.assertEqual(self.en[p:p+n],self.jp[p:p+n])
				self.assertEqual(ex.sha(self.en[p:p+n]),s['sha256'])

	def test_sequences_thresholds_and_explicit_rejections(self):
		seq,frames,errors,spans=ex.sequences(self.en,0x13E58C)
		self.assertEqual(len(seq),5)
		self.assertEqual([(s['frame'],s['threshold']) for s in seq[0]['steps']],[(0,10),(1,8),(0,10),(2,8)])
		self.assertEqual(len(frames),14)
		bad=bytearray(self.en);struct.pack_into('<I',bad,0x13E58C+4,0)
		with self.assertRaises(ValueError):ex.pointer(bad,0x13E58C+4)
		with self.assertRaises(ValueError):ex.descriptor(self.en,0x13E86C,14)
		bad=bytearray(self.en);bad[0x13E58C+3]=1
		with self.assertRaises(ValueError):ex.descriptor(bad,0x13E58C,0)

	def test_no_unproved_named_characters_or_directions(self):
		coverage=json.loads((ex.OUT/'playable_coverage.json').read_text())
		self.assertEqual([r['name'] for r in coverage],['DeMille','Alessa','Sofoubi','Relleck'])
		self.assertEqual(coverage[0]['resources'],['R_0013E58C'])
		for r in coverage[1:]:self.assertEqual(r['resources'],[])
		self.assertTrue(all(r['identity'] is None and r['direction'] is None for r in self.frames))

	def test_existing_output_refused_and_pixel_determinism(self):
		with self.assertRaises(FileExistsError):ex.export(ex.OUT)
		f=ex.descriptor(self.en,0x13E58C,0);g=ex.pointer(self.en,0x13E58C+4);gfx=self.en[g:g+66*32]
		p=ex.render(gfx,f,ex.palette(self.en,0x43B1EC))
		self.assertEqual(ex.gba.png(16,24,p),(ex.OUT/'R_0013E58C_P_0043B1EC/frame_000.png').read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)
