"""Tests final OBJ attribute model and frozen context composition evidence."""
import json
from pathlib import Path
import tempfile
import unittest

import multipart_ownership_v6 as ex


class OwnershipTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.profiles=json.loads((ex.OUT/'profiles.json').read_text())
		cls.composites=json.loads((ex.OUT/'composites.json').read_text())

	def test_all25_are_context_not_standalone(self):
		self.assertEqual({int(p['child_id'],16) for p in self.profiles},ex.old.v3.NULLS)
		rows=json.loads((ex.OUT/'coverage.json').read_text())
		self.assertEqual({int(r['enemy_id'],16) for r in rows},set(range(182)))
		self.assertEqual(sum(r['status'].startswith('context-dependent') for r in rows),25)
		self.assertEqual(sum(r['frame_count'] is not None for r in rows),157)

	def test_submission_wrap_preserves_shape_flip_and_priority(self):
		entry=(0x80FC,0xD1FE,0xF9FF)
		self.assertEqual(ex.submit_obj_attributes([entry],tile_offset=2,x_offset=3,y_offset=5,palette_delta=2),[(0x8001,0xD001,0x1A01)])
		# Overrides affect the documented fields only.
		self.assertEqual(ex.submit_obj_attributes([entry],priority=0,mode=1),[(0x84FC,0xD1FE,0xF1FF)])

	def test_descriptor_order_and_capacity(self):
		entries=[(0,0,512+i) for i in range(5)]
		self.assertEqual(ex.submit_obj_attributes(entries),entries)
		self.assertEqual(ex.submit_obj_attributes(entries,capacity=2),entries[:2])
		self.assertEqual(ex.submit_obj_attributes(entries,capacity=0),[])
		for kw in ({'capacity':129},{'priority':4},{'mode':4}):
			with self.assertRaises(ValueError):ex.submit_obj_attributes(entries,**kw)
		with self.assertRaises(ValueError):ex.submit_obj_attributes([(0x0100,0,512)])

	def test_no_child_filter_and_uniform_anchor_for_every_profile(self):
		for p in self.profiles:
			entries=[tuple(o['attributes']) for o in p['objects']]
			self.assertEqual(len(entries),p['object_count'])
			self.assertTrue(p['base_object_indices'])
			self.assertTrue(p['child_dependent_object_indices'])
			x,y=p['common_anchor']
			actual=ex.submit_obj_attributes(entries,x_offset=x,y_offset=y)
			self.assertEqual([list(a) for a in actual],p['submitted_attributes'])
			for original,submitted in zip(entries,actual):
				self.assertEqual(original[2],submitted[2])
				self.assertEqual((submitted[0]-original[0])&255,y&255)
				self.assertEqual((submitted[1]-original[1])&511,x&511)

	def test_resource_identity_is_not_palette_identity(self):
		p=next(p for p in self.profiles if p['child_id']=='33')
		objects=[o for o in p['objects'] if o['index'] in p['child_dependent_object_indices']]
		self.assertEqual({o['palette_bank'] for o in objects},{6,7,9})
		self.assertEqual({tuple(o['resources']) for o in objects},{('part_2',)})
		with self.assertRaises(ValueError):ex.resource_dependence([(0,0,511)],3)

	def test_context_dimensions_component_coordinates_and_frozen_pixels(self):
		self.assertEqual(len(self.composites),18)
		for c in self.composites:
			self.assertEqual((ex.OUT/c['png']).read_bytes(),(ex.BASE/c['source_png']).read_bytes())
			self.assertEqual(ex.old.v1.sha((ex.OUT/c['png']).read_bytes()),c['png_sha256'])
			objects=c['objects'];left=min(o['x'] for o in objects);top=min(o['y'] for o in objects)
			right=max(o['x']+o['width'] for o in objects);bottom=max(o['y']+o['height'] for o in objects)
			self.assertEqual((right-left,bottom-top),(c['width'],c['height']))
			self.assertTrue(all(not o['affine'] and o['palette_bank'] in range(6,10) for o in objects))
			self.assertEqual(len({o['priority'] for o in objects}),1)

	def test_new_output_deterministic_and_existing_refused(self):
		with self.assertRaises(FileExistsError):ex.run(ex.OUT)
		with tempfile.TemporaryDirectory() as tmp:
			out=Path(tmp)/'new';ex.run(out)
			for p in ex.OUT.rglob('*'):
				if p.is_file():self.assertEqual(p.read_bytes(),(out/p.relative_to(ex.OUT)).read_bytes())


if __name__=='__main__':unittest.main(verbosity=2)
