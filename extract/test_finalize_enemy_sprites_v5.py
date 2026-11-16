"""Focused follow-up tests; completed 156 records are checked as frozen files."""
import json
from pathlib import Path
import tempfile
import unittest

import finalize_enemy_sprites_v5 as ex


class FinalizationTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.rom,cls.jp=ex.v3.load_roms()
		cls.frames=json.loads((ex.OUT/'frames.json').read_text())
		cls.participants=json.loads((ex.OUT/'participants.json').read_text())

	def test_182_record_reconciliation(self):
		rows=json.loads((ex.OUT/'coverage.json').read_text())
		self.assertEqual([int(r['enemy_id'],16) for r in rows],list(range(182)))
		s=json.loads((ex.OUT/'summary.json').read_text())
		self.assertEqual((s['decoded_records'],s['unsupported_standalone_records'],s['total_native_frames']),(157,25,330))
		self.assertEqual(s['counts'],{'successfully decoded':124,'duplicate/shared resource of another decoded enemy':33,'structurally understood but unsupported':25,'unresolved':0})

	def test_326_native_and_all_652_pngs_preserved(self):
		oldframes=json.loads((ex.OLD/'frames.json').read_text())
		self.assertEqual(self.frames[:326],oldframes)
		old=list(ex.OLD.rglob('*.png'));self.assertEqual(len(old),652)
		for path in old:self.assertEqual(path.read_bytes(),(ex.OUT/path.relative_to(ex.OLD)).read_bytes())

	def test_chekkit_obj_pixel_regressions_and_bg_difference(self):
		hashes=['72cd3bbad89cbd10003813b56e0a7e9a556b4e872cfa3ba5101b0768e8420e88',
			'39d2a27f05263e2562bf21c08fa85da056f59f4f2b322ca1610b11c28ba9d9c8',
			'a8039e28b4f3a90c2a7caf91883d19467a7dbc5cad03f5cac19f40d5e4dceed8',
			'39d2a27f05263e2562bf21c08fa85da056f59f4f2b322ca1610b11c28ba9d9c8']
		for fi in range(4):
			d=ex.chekkit(self.rom,fi)
			self.assertEqual((d['width'],d['height'],d['oam']['count']),(80,80,27))
			self.assertEqual(ex.v1.sha(d['pixels']),hashes[fi])
			self.assertEqual(d['bg_obj_difference_count'],10 if fi==2 else 0)
			self.assertEqual(ex.v1.png(80,80,d['pixels']),(ex.OUT/f'8C_Chekkit/frame_{fi:02d}.png').read_bytes())
			self.assertEqual(ex.v1.png(320,320,ex.v1.enlarge(d['pixels'],80,80)),(ex.OUT/f'8C_Chekkit/frame_{fi:02d}_4x.png').read_bytes())
			for p,n in d['spans']:self.assertEqual(self.rom[p:p+n],self.jp[p:p+n])

	def test_exception_is_complete_token_replay_not_header_correction(self):
		data,consumed,proof=ex.exception_projection(self.rom,ex.EXCEPTION_START,3072)
		self.assertEqual((len(data),consumed),(3072,654))
		self.assertEqual((proof['declared_header'],proof['analysis_replay_length'],proof['overshoot']),('30000c00',3200,128))
		self.assertEqual(proof['last_tokens'][-1]['output_before'],3071)
		# Both possible final-token boundary policies give the same upload source.
		self.assertEqual(data[-1],0)
		self.assertEqual(proof['excess_sha256'],ex.v1.sha(bytes(128)))
		# Source row pitch/copy width 12 tiles, 8 rows cover exactly these bytes.
		reads=[p for y in range(8) for p in range(y*384,(y+1)*384)]
		self.assertEqual(reads,list(range(3072)))
		with self.assertRaises(ValueError):ex.v1.decompress(self.rom,ex.EXCEPTION_START,3072)

	def test_exception_refuses_other_source_size_or_mutation(self):
		for start,size in ((ex.EXCEPTION_START+4,3072),(ex.EXCEPTION_START,3200)):
			with self.assertRaises(ValueError):ex.exception_projection(self.rom,start,size)
		bad=bytearray(self.rom);bad[ex.EXCEPTION_END-1]=1
		with self.assertRaises(ValueError):ex.exception_projection(bad,ex.EXCEPTION_START,3072)
		with self.assertRaises(ValueError):ex.chekkit(self.rom,4)

	def test_all_participant_links_states_and_obj_attributes(self):
		self.assertEqual({int(p['enemy_id'],16) for p in self.participants},ex.v3.NULLS)
		rebuilt=ex.component_inventory(self.rom,self.jp)
		self.assertEqual(rebuilt,self.participants)
		for p in rebuilt:
			self.assertFalse((ex.OUT/(p['enemy_id']+'_standalone.png')).exists())
			for link in p['links']:
				self.assertEqual(len(link['streams']),2*link['base_cycle_frames'])
				self.assertEqual({s['state'] for s in link['streams']},{0,1})
				self.assertTrue(link['objects'])
				for o in link['objects']:
					self.assertEqual(ex.SIZES[o['shape']][o['size']],(o['width'],o['height']))
					self.assertTrue(o['all_tiles_in_component'])
					self.assertIn(o['palette_bank'],range(6,10))
		# Mixed palette banks make a bank-only child crop invalid.
		mixed=next(p for p in rebuilt if p['enemy_id']=='1B')['links'][0]
		self.assertEqual(mixed['palette_banks_used'],[7,8])

	def test_refuses_existing_output_and_deterministic_new_export(self):
		with self.assertRaises(FileExistsError):ex.export(ex.OUT)
		with tempfile.TemporaryDirectory() as tmp:
			out=Path(tmp)/'new';ex.export(out)
			for p in ex.OUT.rglob('*'):
				if p.is_file():self.assertEqual(p.read_bytes(),(out/p.relative_to(ex.OUT)).read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)
