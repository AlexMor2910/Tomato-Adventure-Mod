"""Synthetic aggregation/mapping tests and read-only baseline integration."""
import csv
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('binky_extract', ROOT / 'tools/extract/extract_binky_locations.py')
binky = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(binky)


def reward(key='actor-flag-0015', quantity=1, source_type='fixed_actor_pickup', repeatable='false', map_id='0x0003'):
	return dict(binky_id=key, quantity=quantity, source_type=source_type, repeatable=repeatable,
		confidence='Confirmed static', map_id=map_id, node_id='0x00', node_name='Example',
		node_confidence='Probable', object_record_address='0x08140510')


class SyntheticTests(unittest.TestCase):
	def test_quantity_not_object_count(self):
		r = binky.totals([reward(quantity=3), reward(key='second', quantity=2)])
		self.assertEqual(r['fixed_binky_pickups'], 2)
		self.assertEqual(r['fixed_binky_quantity'], 5)
		self.assertEqual(r['complete_total_quantity'], '')

	def test_duplicate_identity(self):
		rows = binky.canonicalize([reward(quantity=3), reward(quantity=3)])
		self.assertEqual(binky.totals(rows)['fixed_binky_quantity'], 3)
		self.assertEqual(rows[0]['registration_count'], 2)
		with self.assertRaises(ValueError):
			binky.canonicalize([reward(quantity=3), reward(quantity=1)])

	def test_cross_map_alias_unassigned(self):
		rows = binky.canonicalize([reward(map_id='0x0003'), reward(map_id='0x0004')])
		self.assertEqual(rows[0]['map_id'], '')
		self.assertEqual(rows[0]['node_id'], '')
		self.assertEqual(rows[0]['possible_map_ids'], '0x0003|0x0004')
		self.assertEqual(binky.totals(rows)['fixed_binky_quantity'], 1)

	def test_conditional_and_repeatable_exclusion(self):
		r = binky.totals([reward(), reward(key='conditional',quantity=4,source_type='conditional_one_time_reward'),
			reward(key='renewable',quantity=99,repeatable='true')])
		self.assertEqual(r['fixed_binky_quantity'], 1)
		self.assertEqual(r['conditional_binky_quantity'], 4)
		self.assertEqual(binky.totals([])['conditional_binky_quantity'], '')

	def test_uncertain_nodes_and_non_numeric_grouping(self):
		graph = {1:{20}, 20:{1}, 21:set(), 22:set()}
		result = binky.node_components(graph, {1:{2},20:{3},22:{4}})
		self.assertEqual(result[1], [2,3])
		self.assertEqual(result[20], [2,3])
		self.assertEqual(result[21], [])
		self.assertEqual(result[22], [4])


class BaselineTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.jp = (ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
		cls.en = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
		cls.menus = (ROOT / 'tomatotrans-1.1.1/ta_menus_eng.txt').read_text(encoding='utf-8-sig')
		cls.result = binky.extract(cls.jp, cls.menus)

	def test_inventory_and_subtotals(self):
		locations, rooms, nodes, other, maps, unresolved, evidence = self.result
		self.assertEqual((len(locations),len(rooms),len(other),len(unresolved)), (74,494,5,7))
		self.assertEqual(len({r['collection_flag'] for r in locations}),74)
		self.assertEqual(evidence['fixed_actor_quantity'],74)
		self.assertEqual(sum(r['fixed_binky_quantity'] for r in rooms),74)
		self.assertEqual(sum(r['fixed_binky_quantity'] for r in nodes),74)
		first = next(r for r in locations if r['collection_flag']=='0x0015')
		self.assertEqual((first['map_id'],first['x'],first['y'],first['quantity']),('0x0003',10,6,1))
		self.assertEqual(first['collection_flag_ram'],'0x03003109')
		self.assertEqual(first['collection_flag_mask'],'0x20')
		self.assertEqual(sum(r['initializer_guard_offset']==5 for r in locations),4)
		self.assertEqual(evidence['arrivals'][15]['map_id'],'')

	def test_japanese_english_local_equivalence(self):
		english = binky.extract(self.en,self.menus)
		self.assertEqual(self.result[:-1],english[:-1])
		for window in self.result[-1]['native_windows']:
			start,stop=int(window['file_start'],16),int(window['file_end_exclusive'],16)
			self.assertEqual(self.jp[start:stop],self.en[start:stop],window['label'])

	def test_fingerprint_rejects_modified_rom(self):
		with self.assertRaises(ValueError):
			binky.extract(self.jp[:-1],self.menus)

	def test_published_csv_json_consistency(self):
		filenames = ['binky_locations.csv','binkies_per_room.csv','binkies_per_node.csv','binky_other_sources.csv','binky_map_nodes.csv','binky_unresolved.csv']
		for rows,name in zip(self.result[:-1],filenames):
			decoded=list(csv.DictReader(io.StringIO(binky.csv_text(rows))))
			with (ROOT/'tools/extract/extracted_data'/name).open(encoding='utf-8',newline='') as stream:
				self.assertEqual(decoded,list(csv.DictReader(stream)))
		published=json.loads((ROOT/'reverse_engineering/binky_location_extraction_evidence.json').read_text(encoding='utf-8'))
		self.assertEqual(self.result[-1],{k:v for k,v in published.items() if k!='sources'})

	def test_cli_no_overwrite(self):
		with tempfile.TemporaryDirectory() as temp:
			command=[sys.executable,'-B',str(ROOT/'tools/extract/extract_binky_locations.py'),
				'--rom',str(ROOT/'Tomato Adventure (Japan).gba'),'--menus',str(ROOT/'tomatotrans-1.1.1/ta_menus_eng.txt'),
				'--output-dir',temp,'--evidence-output',str(Path(temp)/'evidence.json')]
			first=subprocess.run(command,capture_output=True,text=True)
			self.assertEqual(first.returncode,0,first.stderr)
			before={p:p.read_bytes() for p in Path(temp).iterdir()}
			second=subprocess.run(command,capture_output=True,text=True)
			self.assertNotEqual(second.returncode,0)
			self.assertIn('refusing to overwrite',second.stderr)
			self.assertEqual(before,{p:p.read_bytes() for p in Path(temp).iterdir()})


if __name__=='__main__':
	unittest.main()
