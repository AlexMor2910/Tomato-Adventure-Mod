"""Synthetic map-format tests plus read-only generated-artifact checks."""
import csv
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/extract'))
import extract_field_maps as maps


def png_pixels(data):
	cursor=8;compressed=b'';dimensions=None
	while cursor<len(data):
		size=struct.unpack_from('>I',data,cursor)[0]
		tag=data[cursor+4:cursor+8];body=data[cursor+8:cursor+8+size]
		if zlib.crc32(tag+body)&0xFFFFFFFF != struct.unpack_from('>I',data,cursor+8+size)[0]:
			raise ValueError('PNG CRC mismatch')
		if tag==b'IHDR':dimensions=struct.unpack_from('>II',body)
		if tag==b'IDAT':compressed+=body
		cursor+=size+12
	width,height=dimensions
	raw=zlib.decompress(compressed)
	if len(raw)!=(width*4+1)*height:
		raise ValueError('PNG scanline size mismatch')
	return dimensions,b''.join(raw[y*(width*4+1)+1:(y+1)*(width*4+1)] for y in range(height))


class FormatTests(unittest.TestCase):
	def test_rgb555_and_4bpp(self):
		self.assertEqual(maps.rgba555(31),b'\xff\0\0\xff')
		self.assertEqual(maps.rgba555(31<<5),b'\0\xff\0\xff')
		colors=[b'\0\0\0\xff',b'\xff\0\0\xff',b'\0\xff\0\xff']+[b'\0\0\0\xff']*29
		colors[17]=b'\0\0\xff\xff'
		tile=bytes([0x21])+bytes(31)
		decoded=maps.tile_pixels(tile,0,colors)
		self.assertEqual(decoded[:8],colors[1]+colors[2])
		self.assertEqual(decoded[8:12],bytes(4))
		flipped=maps.tile_pixels(tile,0x400,colors)
		self.assertEqual(flipped[24:32],colors[2]+colors[1])
		vertical=maps.tile_pixels(tile,0x800,colors)
		self.assertEqual(vertical[224:232],colors[1]+colors[2])
		self.assertEqual(maps.tile_pixels(tile,0x1000,colors)[:4],colors[17])

	def test_compression_and_malformed_streams(self):
		self.assertEqual(maps.decompress(bytes.fromhex('30 04 00 00 81 aa'),0)[0],b'\xaa'*4)
		self.assertEqual(maps.decompress(bytes.fromhex('10 06 00 00 40 41 20 00'),0)[0],b'AAAAAA')
		for stream in ('10 03 00 00 80 00 00','30 02 00 00 80 aa','30 04 00 00 81','10 ff ff ff'):
			with self.assertRaises(ValueError):maps.decompress(bytes.fromhex(stream),0)

	def test_synthetic_layout_and_deterministic_png(self):
		rom=bytearray(0x640000)
		def pointer(slot,value):struct.pack_into('<I',rom,slot,maps.BUS+value)
		rom[maps.MAP_TABLE+3:maps.MAP_TABLE+5]=b'\1\1'
		for slot,target in [(0x255F00,0x1000),(0x15BA3C,0x2000),(0x26E358,0x3000),(0x31E7B4,0x4000),(0x303950,0x5000),
			(maps.MAP_TABLE+16,0x6000),(maps.MAP_TABLE+20,0x7000)]:pointer(slot,target)
		rom[0x1002:0x1004]=b'\x1f\0'
		rom[0x2000:0x2006]=bytes.fromhex('30 20 00 00 9d 11')
		rom[0x6309EC]=0x39
		row,images,_=maps.render(bytes(rom),0)
		self.assertEqual((row['width_tiles'],row['height_tiles']),(2,2))
		dimensions,pixels=png_pixels(images[3])
		self.assertEqual(dimensions,(16,16))
		self.assertEqual(pixels,b'\xff\0\0\xff'*256)
		self.assertEqual(images,maps.render(bytes(rom),0)[1])
		# A second opaque layer wins by the actual per-map priority, then loses ties.
		rom[0x1004:0x1006]=b'\xe0\x03'
		rom[0x2000:0x2008]=bytes.fromhex('30 40 00 00 9d 11 9d 22')
		pointer(0x26E35C,0x3000);pointer(0x31E7B8,0x4010)
		rom[0x4010:0x4018]=b'\1\0'*4
		rom[0x6309EC]=0x36
		self.assertEqual(png_pixels(maps.render(bytes(rom),0)[1][3])[1],b'\0\xff\0\xff'*256)
		rom[0x6309EC]=0x35
		self.assertEqual(png_pixels(maps.render(bytes(rom),0)[1][3])[1],b'\xff\0\0\xff'*256)

	def test_directed_reachability_and_shared_room(self):
		edges=[maps.edge(destination='0x0001',source_node_id='0x00'),maps.edge(destination='0x0003',source_node_id='0x01'),
			maps.edge('0x0001','0x0002'),maps.edge('0x0003','0x0002')]
		reach=maps.reachability(edges)
		self.assertEqual(reach['0x0002'],{'0x00':1,'0x01':1})
		self.assertEqual(reach['0x0001'],{'0x00':0})
		assignment=maps.assignments(edges,{n:str(n) for n in range(17)})
		self.assertEqual(assignment[2]['node_id'],'')
		self.assertEqual(assignment[2]['reachable_nodes'],'0x00|0x01')
		self.assertEqual(assignment[1]['node_id'],'0x00')

	def test_binky_identity_aggregation_and_no_reachability_promotion(self):
		old=[dict(binky_id=f'flag-{n}',quantity='1',map_id='0x0002',node_id='',node_name='',node_confidence='Unresolved') for n in range(74)]
		mapping=maps.assignments([maps.edge(destination='0x0001',source_node_id='0x00'),maps.edge('0x0001','0x0002')],{n:str(n) for n in range(17)})
		updated,totals=maps.binky_v2(old,mapping,{n:str(n) for n in range(17)})
		self.assertTrue(all(r['node_id']=='' for r in updated))
		self.assertEqual(sum(r['fixed_binky_quantity'] for r in totals),74)
		with self.assertRaises(ValueError):maps.binky_v2(old+old[:1],mapping,{})
		bad=[dict(r,collection_flag='0x0015') for r in old]
		with self.assertRaises(ValueError):maps.binky_v2(bad,mapping,{})


class ArtifactTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.rom=(ROOT/'Tomato Adventure (Japan).gba').read_bytes()
		cls.evidence=json.loads((ROOT/'reverse_engineering/map_extraction_evidence.json').read_text(encoding='utf-8'))

	def test_representatives_and_png_hashes(self):
		for m in maps.REPRESENTATIVES:
			row,images,_=maps.render(self.rom,m)
			for suffix,image in zip(('_layer1','_layer2','_layer3',''),images):
				self.assertEqual((ROOT/f'reverse_engineering/exports/field_maps_v1/map_{m:04X}{suffix}.png').read_bytes(),image)
				self.assertEqual(png_pixels(image)[0],(row['width_tiles']*8,row['height_tiles']*8))
		for rendered in self.evidence['rendered']:
			m=int(rendered['map_id'],16)
			for suffix,digest in zip(('_layer1','_layer2','_layer3',''),rendered['png_sha256']):
				self.assertEqual(maps.sha((ROOT/f'reverse_engineering/exports/field_maps_v1/map_{m:04X}{suffix}.png').read_bytes()),digest)

	def test_catalog_graph_and_binkies(self):
		def read(name):
			with (ROOT/'tools/extract/extracted_data'/name).open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))
		catalog=read('maps.csv');edges=read('map_transitions.csv')
		self.assertEqual(len(catalog),494)
		self.assertEqual(len(edges),self.evidence['transition_count'])
		for row in catalog:
			expected=maps.resources(self.rom,int(row['map_id'],16))[0]
			self.assertEqual(row['tileset_id'],str(expected['tileset_id']))
			self.assertEqual(row['width_tiles'],str(expected['width_tiles']))
		old=read('binky_locations.csv');new=read('binky_map_nodes_v2.csv')
		self.assertEqual([(r['binky_id'],r['quantity']) for r in old],[(r['binky_id'],r['quantity']) for r in new])
		self.assertEqual(sum(int(r['fixed_binky_quantity']) for r in read('binkies_per_node_v2.csv')),74)
		self.assertEqual(maps.sha(self.rom),maps.JP_SHA)

	def test_output_overwrite_refused(self):
		catalog=ROOT/'tools/extract/extracted_data/maps.csv'
		before=catalog.read_bytes()
		command=[sys.executable,'-B',str(ROOT/'tools/extract/extract_field_maps.py'),
			'--rom',str(ROOT/'Tomato Adventure (Japan).gba'),'--menus',str(ROOT/'tomatotrans-1.1.1/ta_menus_eng.txt'),
			'--binky-evidence',str(ROOT/'reverse_engineering/binky_location_extraction_evidence.json'),
			'--binky-locations',str(ROOT/'tools/extract/extracted_data/binky_locations.csv'),
			'--output-dir',str(catalog.parent),'--image-dir',str(ROOT/'reverse_engineering/exports/field_maps_v1'),
			'--evidence-output',str(ROOT/'reverse_engineering/map_extraction_evidence.json')]
		result=subprocess.run(command,capture_output=True,text=True)
		self.assertNotEqual(result.returncode,0)
		self.assertIn('refusing to overwrite',result.stderr)
		self.assertEqual(catalog.read_bytes(),before)

	def test_fresh_cli_reproduction(self):
		with tempfile.TemporaryDirectory() as temporary:
			out=Path(temporary)
			command=[sys.executable,'-B',str(ROOT/'tools/extract/extract_field_maps.py'),
				'--rom',str(ROOT/'Tomato Adventure (Japan).gba'),'--menus',str(ROOT/'tomatotrans-1.1.1/ta_menus_eng.txt'),
				'--binky-evidence',str(ROOT/'reverse_engineering/binky_location_extraction_evidence.json'),
				'--binky-locations',str(ROOT/'tools/extract/extracted_data/binky_locations.csv'),
				'--output-dir',str(out/'csv'),'--image-dir',str(out/'png'),'--evidence-output',str(out/'evidence.json')]
			result=subprocess.run(command,capture_output=True,text=True)
			self.assertEqual(result.returncode,0,result.stderr)
			self.assertEqual(len(list((out/'png').glob('*.png'))),16)
			for m in maps.REPRESENTATIVES:
				self.assertEqual((out/f'png/map_{m:04X}.png').read_bytes(),(ROOT/f'reverse_engineering/exports/field_maps_v1/map_{m:04X}.png').read_bytes())
			for name in ('map_transitions.csv','map_node_assignments.csv','binky_map_nodes_v2.csv','binkies_per_node_v2.csv'):
				self.assertEqual((out/'csv'/name).read_bytes(),(ROOT/'tools/extract/extracted_data'/name).read_bytes())


if __name__=='__main__':unittest.main()
