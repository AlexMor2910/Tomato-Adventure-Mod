"""Bounded static field-background renderer and directed map graph exporter.

No ROM writes. Output files must not exist. Backgrounds are initial graphics
resources without actors, script overlays, animation playback, or screen effects.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zlib

from extract_binky_locations import JP_SHA, EN_SHA, MAP_TABLE, MAP_COUNT, BUS, node_names
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from thumb_inspect import inspect

REPRESENTATIVES = (0x4D, 0x5F, 0x104, 0x173)
MAX_PIXELS = 4_194_304


def hx(n):
	return f'0x{n:08X}'


def mid(n):
	return f'0x{n:04X}'


def sha(data):
	return hashlib.sha256(data).hexdigest()


def take(data, p, count):
	if p < 0 or count < 0 or p + count > len(data):
		raise ValueError(f'Out-of-bounds data at {hx(p)} size {count}')
	return data[p:p + count]


def u16(data, p):
	return int.from_bytes(take(data,p,2),'little')


def ptr(data, p, nullable=False):
	n = int.from_bytes(take(data,p,4),'little')
	if n == 0 and nullable:
		return None
	result = n - BUS
	take(data,result,1)
	return result


def decompress(data, start, limit=0x8000):
	"""Strict GBA 0x10 LZ77 / 0x30 RL, with bounded advertised size."""
	header = take(data,start,4)
	size = int.from_bytes(header[1:],'little')
	if header[0] not in (0x10,0x30) or not 0 < size <= limit:
		raise ValueError('Unsupported compression or advertised size')
	output, cursor = bytearray(), start + 4
	def read(n):
		nonlocal cursor
		value = take(data,cursor,n)
		cursor += n
		return value
	while len(output) < size:
		flag = read(1)[0]
		if header[0] == 0x30:
			count = (flag & 127) + (3 if flag & 128 else 1)
			if len(output) + count > size:
				raise ValueError('RL token exceeds advertised output')
			output.extend(read(1)*count if flag & 128 else read(count))
		else:
			for bit in range(7,-1,-1):
				if len(output) == size:
					break
				if flag & (1 << bit):
					a,b = read(2)
					count, distance = (a >> 4)+3, ((a & 15)<<8)+b+1
					if distance > len(output) or len(output)+count > size:
						raise ValueError('Invalid LZ backreference')
					for _ in range(count):
						output.append(output[-distance])
				else:
					output.extend(read(1))
	return bytes(output), cursor-start


def rgba555(color):
	return bytes([((color >> shift)&31)*8 + (((color >> shift)&31)>>2) for shift in (0,5,10)] + [255])


def png(width,height,pixels):
	if not 0 < width*height <= MAX_PIXELS or len(pixels) != width*height*4:
		raise ValueError('Invalid PNG dimensions/pixels')
	def chunk(tag,body):
		return struct.pack('>I',len(body))+tag+body+struct.pack('>I',zlib.crc32(tag+body)&0xFFFFFFFF)
	raw = b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
	return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')


def tile_pixels(gfx, entry, colors):
	tile, bank = entry & 1023, entry >> 12
	raw = take(gfx,tile*32,32)
	result = bytearray(256)
	for y in range(8):
		for x in range(8):
			sx,sy = (7-x if entry & 0x400 else x),(7-y if entry & 0x800 else y)
			n = (raw[sy*4+sx//2] >> ((sx&1)*4))&15
			if n:
				if bank*16+n >= len(colors):
					raise ValueError('Opaque tile references unloaded palette bank')
				result[(y*8+x)*4:(y*8+x+1)*4] = colors[bank*16+n]
	return bytes(result)


def resources(rom, m):
	if not 0 <= m < MAP_COUNT:
		raise ValueError('Field map ID outside established catalog')
	record = MAP_TABLE + m*28
	r = take(rom,record,28)
	resource_id = u16(r,0)
	if resource_id >= MAP_COUNT:
		raise ValueError('Unsupported resource index')
	w,h = r[3],r[4]
	if not 0 < w*h*256 <= MAX_PIXELS:
		raise ValueError('Invalid or oversized layout dimensions')
	palette = ptr(rom,0x255F00+4*resource_id)
	layouts = [ptr(rom,0x26E358+12*resource_id+4*k,True) for k in range(3)]
	chipsets = [ptr(rom,0x31E7B4+12*resource_id+4*k,True) for k in range(3)]
	return dict(map_id=mid(m),map_record_offset=hx(record),map_record_bus=hx(BUS+record),
		width_tiles=w*2,height_tiles=h*2,width_cells=w,height_cells=h,tileset_id=resource_id,palette_id=resource_id,
		layout_pointer='|'.join(hx(BUS+p) if p is not None else '' for p in layouts),
		collision_pointer=hx(BUS+ptr(rom,0x303950+4*resource_id)),
		event_pointer=hx(BUS+ptr(rom,record+16)),actor_pointer=hx(BUS+ptr(rom,record+20)),
		palette_pointer=hx(BUS+palette),music_selector=r[5]&63,auxiliary_graphics_id=r[7],
		layer_priorities='|'.join(str((rom[0x6309EC+m]>>(2*k))&3) for k in range(3)),
		render_status='not_requested',confidence='Confirmed static',evidence_reference='LOADER;CHIPS;GRAPHICS;PRIORITY',
		limitations='Initial field background only; actors, script changes and runtime effects excluded'),layouts,chipsets,palette


def graphics(rom,m,resource_id):
	source = ptr(rom,0x15BA3C+4*resource_id)
	header = take(rom,source,4)
	if header[0] in (0x10,0x30):
		base,consumed = decompress(rom,source)
	elif header[0] == 0:
		size = rom[0x15B84C+resource_id]*512
		if not 0 < size <= 0x8000:
			raise ValueError('Uncompressed tileset size out of bounds')
		base,consumed = take(rom,source+4,size),size+4
	else:
		raise ValueError('Unsupported graphics header')
	if len(base)%32:
		raise ValueError('Tileset is not a whole number of tiles')
	gfx, valid = bytearray(0x8000), set(range(len(base)//32)) | {1023}
	gfx[:len(base)] = base
	aux = rom[MAP_TABLE+m*28+7]
	uploads=[]
	if aux:
		cursor = ptr(rom,0x13D1EC+4*(aux-1))
		for _ in range(128):
			if take(rom,cursor,1)[0] == 255:
				break
			rec = take(rom,cursor,10)
			count,frames = rec[5]+1,rec[4]
			first = ptr(rom,cursor+6)
			size = count*32
			take(rom,first,size)
			if rec[1] == 0:  # native destination 06000000; map char base 06008000
				destination = u16(rec,2)*32-0x8000
				if not 0 <= destination <= 0x8000-size:
					raise ValueError('Supplemental BG upload outside mapped character block')
				gfx[destination:destination+size] = rom[first:first+size]
				valid.update(range(destination//32,(destination+size)//32))
				uploads.append(dict(record_bus=hx(BUS+cursor),source_bus=hx(BUS+first),first_tile=destination//32,tile_count=count))
			take(rom,cursor,10+frames*4)
			cursor += 10+frames*4
		else:
			raise ValueError('Supplemental graphics list exceeds analysis bound')
	return bytes(gfx),valid,dict(tileset_bus=hx(BUS+source),compression=header[0],compressed_consumed=consumed,decompressed_bytes=len(base),initial_uploads=uploads)


def render(rom,m):
	row,layouts,chipsets,palette = resources(rom,m)
	w,h = row['width_cells'],row['height_cells']
	gfx,valid,metadata = graphics(rom,m,row['tileset_id'])
	colors = [rgba555(u16(rom,palette+2*k)) for k in range(240)]
	layers,cache = [],{}
	for index in range(3):
		pixels = bytearray(w*h*256*4)
		if layouts[index] is None:
			layers.append(bytes(pixels))
			continue
		if chipsets[index] is None:
			raise ValueError('Layout has no chipset')
		layout = take(rom,layouts[index],w*h*2)
		for cy in range(h):
			for cx in range(w):
				chip = u16(layout,2*(cy*w+cx))
				entries = take(rom,chipsets[index]+chip*8,8)
				for k in range(4):
					entry = u16(entries,k*2)
					if entry&1023 not in valid:
						raise ValueError(f'Unloaded tile {entry&1023} in layer {index+1}')
					if entry not in cache:
						cache[entry] = tile_pixels(gfx,entry,colors)
					tile = cache[entry]
					for y in range(8):
						position = ((cy*16+(k//2)*8+y)*w*16+cx*16+(k%2)*8)*4
						pixels[position:position+32] = tile[y*32:(y+1)*32]
		layers.append(bytes(pixels))
	priorities = [int(n) for n in row['layer_priorities'].split('|')]
	combined = bytearray(colors[0]*(w*h*256))
	# Lower numeric priority wins; lower BG number wins ties.
	for layer in sorted(range(3),key=lambda k:(priorities[k],k),reverse=True):
		pixels = layers[layer]
		for p in range(0,len(pixels),4):
			if pixels[p+3]:
				combined[p:p+4] = pixels[p:p+4]
	row['render_status']='supported_initial_background'
	return row,[png(w*16,h*16,p) for p in layers]+[png(w*16,h*16,bytes(combined))],metadata


def edge(source='',destination='',**values):
	row=dict(source_map_id=source,source_x='',source_y='',source_x_end='',source_y_end='',
		destination_map_id=destination,destination_x='',destination_y='',destination_node_id='',source_node_id='',
		transition_type='',required_flag='',event_script_address='',record_address='',confidence='Confirmed static',
		evidence_reference='',limitations='')
	row.update(values)
	return row


def transitions(rom, prior):
	result=[]
	for e in prior['exits']:
		p=int(e['address'],16)-BUS
		raw=take(rom,p,10)
		if raw.hex(' ')!=e['raw_hex']:
			raise ValueError('Prior exit evidence differs from source ROM')
		dest=u16(raw,4)
		result.append(edge(e['map_id'],mid(dest) if not dest&0x8000 else '',
			source_x=raw[0],source_y=raw[1],source_x_end=raw[2],source_y_end=raw[3],
			destination_x=raw[7]&127 if not dest&0x8000 else '',destination_y=raw[8]&127 if not dest&0x8000 else '',
			destination_node_id=f'0x{(dest&255)-1:02X}' if dest&0x8000 else '',
			transition_type='overworld_return' if dest&0x8000 else 'ordinary_exit_rectangle',
			record_address=e['address'],evidence_reference='prior exit registration; EXIT_DEST',
			limitations='Door versus map-edge appearance unresolved; source is inclusive rectangle; destination subcell nibbles omitted; no reverse edge implied'))
	for arrival in prior['arrivals']:
		if not arrival['map_id']:
			continue
		p=int(arrival['script_bus'],16)-BUS
		raw=take(rom,p,7)
		if raw[:2] not in (b'\xfe\x7c',b'\xfe\x7d') or mid(u16(raw,2))!=arrival['map_id']:
			raise ValueError('Prior arrival differs from ROM')
		result.append(edge(destination=arrival['map_id'],destination_x=raw[4],destination_y=raw[5],
			source_node_id=arrival['node_id'],transition_type='overworld_arrival',event_script_address=arrival['script_bus'],
			evidence_reference='prior arrival dispatch; TRANSFER'))
	# Source-map roots are actual default, rectangle-event and ordinary actor interaction pointers.
	# No all-byte transfer scan. Stop at unknown opcodes, calls or dynamic construction.
	rootsets=collections.defaultdict(set)
	for m in range(MAP_COUNT):
		rec=MAP_TABLE+28*m
		events=ptr(rom,rec+16)
		rootsets[m].add(int.from_bytes(take(rom,events,4),'little')-BUS)
		for k in range(128):
			p=events+4+8*k
			if take(rom,p,1)[0]==255:
				break
			rootsets[m].add(int.from_bytes(take(rom,p+4,4),'little')-BUS)
		else:
			raise ValueError('Event rectangle analysis limit exceeded')
		actors=ptr(rom,rec+20)+112
		for k in range(15):
			p=actors+16*k
			if rom[p]==255:
				break
			if not rom[p]&128 and not rom[p+1]&128:
				rootsets[m].add(int.from_bytes(take(rom,p+10,4),'little')-BUS)
	stops=[]
	for m in sorted(rootsets):
		for root in sorted(rootsets[m]):
			if not 0xF9000<=root<0x15BA3C:
				continue
			queue,seen,budget=[(root,'')],set(),0
			while queue and budget<128:
				p,condition=queue.pop()
				if p in seen:
					continue
				seen.add(p);budget+=1
				if not 0xF9000<=p<0x15BA3C-16:
					continue
				op=rom[p:p+2]
				if op in (b'\xfe\x7c',b'\xfe\x7d'):
					dest=u16(rom,p+2)
					if dest<MAP_COUNT:
						result.append(edge(mid(m),mid(dest),destination_x=rom[p+4],destination_y=rom[p+5],
							transition_type='conditional_scripted_transfer' if condition else 'scripted_transfer',
							required_flag=condition,event_script_address=hx(BUS+p),record_address=hx(BUS+root),
							evidence_reference='registered script root; TRANSFER; typed bounded prefix',
							limitations='Registered event/interaction availability still depends on runtime; prefix traversal stops at unknown operations'))
				elif op==b'\xfd\x30':
					queue.append((int.from_bytes(rom[p+2:p+6],'little')-BUS,condition))
				elif op in (b'\xfd\x35',b'\xfd\x3b'):
					flag=u16(rom,p+2)
					polarity='set' if op[1]==0x35 else 'clear'
					queue.append((int.from_bytes(rom[p+4:p+8],'little')-BUS,condition+f'flag {flag:04X} {polarity};'))
					queue.append((p+8,condition+f'flag {flag:04X} not {polarity};'))
				elif op in (b'\xfd\x7c',b'\xfd\x7d'):
					pass
				else:
					stops.append(dict(source_map_id=mid(m),root_bus=hx(BUS+root),stop_bus=hx(BUS+p),
						opcode_hex=op.hex(' '),reason='Unsupported prefix/control operation; no guessed downstream edges'))
			if queue:
				stops.append(dict(source_map_id=mid(m),root_bus=hx(BUS+root),stop_bus='',opcode_hex='',reason='128-command root budget'))
	unique={json.dumps(r,sort_keys=True):r for r in result}
	return sorted(unique.values(),key=lambda r:(r['source_map_id'],r['source_node_id'],r['record_address'],r['event_script_address'],r['required_flag'])),stops


def reachability(edges):
	graph=collections.defaultdict(set)
	starts=collections.defaultdict(set)
	for e in edges:
		if e['source_map_id'] and e['destination_map_id']:
			graph[e['source_map_id']].add(e['destination_map_id'])
		if e['source_node_id'] and e['destination_map_id']:
			starts[e['source_node_id']].add(e['destination_map_id'])
	result=collections.defaultdict(dict)
	for node,roots in sorted(starts.items()):
		queue=collections.deque((m,0) for m in sorted(roots));seen=set()
		while queue:
			m,d=queue.popleft()
			if m in seen:
				continue
			seen.add(m);result[m][node]=d
			queue.extend((n,d+1) for n in sorted(graph[m]) if n not in seen)
	return result


def assignments(edges,names):
	reach=reachability(edges)
	direct=collections.defaultdict(set)
	for e in edges:
		if e['source_node_id']:
			direct[e['destination_map_id']].add(e['source_node_id'])
		if e['destination_node_id']:
			direct[e['source_map_id']].add(e['destination_node_id'])
	rows=[]
	for m in range(MAP_COUNT):
		key=mid(m);choices=set(reach[key])|direct[key]
		only=next(iter(choices)) if len(choices)==1 else ''
		association=only if only in direct[key] else ''
		rows.append(dict(map_id=key,node_id=association,node_name=names[int(association,16)] if association else '',
			association_method='direct arrival/return association' if association else 'reachability candidates only',
			graph_distance_from_arrival=reach[key].get(association,'') if association else '',
			confidence='Confirmed static' if association else ('Candidate' if choices else 'Unresolved'),
			ambiguity_notes='Association does not establish exclusive ownership; script graph is partial',
			reachable_nodes='|'.join(sorted(reach[key])),direct_nodes='|'.join(sorted(direct[key])),
			candidate_distances='|'.join(f'{n}:{d}' for n,d in sorted(reach[key].items())),
			evidence_reference='directed map_transitions.csv; registered arrival/return records'))
	return rows


def binky_v2(old,mapping,names):
	if len(old)!=74 or len({r['binky_id'] for r in old})!=74 or sum(int(r['quantity']) for r in old)!=74:
		raise ValueError('Authoritative Binky identities/quantities mismatch')
	flags=[r['collection_flag'] for r in old if r.get('collection_flag')]
	if len(flags)!=len(set(flags)):
		raise ValueError('Duplicate Binky collection flags')
	by_map={r['map_id']:r for r in mapping};updated=[]
	for oldrow in old:
		row=dict(oldrow);assignment=by_map[row['map_id']]
		row.update(graph_reachable_nodes=assignment['reachable_nodes'],graph_candidate_distances=assignment['candidate_distances'],
			v2_change='unchanged',v2_evidence_reference='map_transitions.csv; map_node_assignments.csv',
			v2_limitations='Prior probable association retained; new reachability is not exclusive ownership')
		if not row['node_id'] and assignment['node_id']:
			row.update(node_id=assignment['node_id'],node_name=assignment['node_name'],node_confidence='Probable',
				v2_change='new direct association',v2_limitations='Direct relationship established; exclusive ownership not proved')
		updated.append(row)
	totals=[]
	for node in [f'0x{n:02X}' for n in range(17)]+['']:
		rows=[r for r in updated if r['node_id']==node]
		totals.append(dict(node_id=node,node_name=names[int(node,16)] if node else 'Unassigned pool (not a node)',
			fixed_binky_pickups=len(rows),fixed_binky_quantity=sum(int(r['quantity']) for r in rows),
			complete_total_quantity='',conditional_binky_quantity='',confidence='Probable' if node else 'Unresolved',
			coverage='Partial registered-actor subtotal; unresolved reward candidates excluded',evidence_reference='binky_map_nodes_v2.csv'))
	return updated,totals


NATIVE = {
	'LOADER':[(0x33CB6,0x33CCA),(0x33D2A,0x33D64),(0x33DA6,0x33E2A)],
	'GRAPHICS':[(0x34D48,0x34D6C),(0x34D78,0x34D86),(0x34D8C,0x34DA8),(0x34DF0,0x34E02),(0x34E20,0x34E90)],
	'BLANK':[(0x31AAA,0x31AC0),(0x31AEC,0x31B08)],
	'CHIPS':[(0x34C88,0x34CAC),(0x34CBA,0x34CD8)],
	'COLLISION':[(0x34AB0,0x34ADC)],
	'PRIORITY':[(0x33C92,0x33CB6),(0x34F58,0x34F96)],
	'EXIT_DEST':[(0x69AA6,0x69B1A)],
	'TRANSFER':[(0x2A0A0,0x2A0CC),(0x2A134,0x2A160)],
}

FORMAT = {
	'confidence':'Confirmed static',
	'map_record':{'file_base':'0x0062D3E4','bus_base':'0x0862D3E4','stride':28,'count':494,
		'fields':[
			{'relative':'0x00','width':'u16le','purpose':'graphics resource lookup index','reader_bus':'0x08033D3E'},
			{'relative':'0x02','width':'u8 flags','purpose':'unresolved outside observed loader operations'},
			{'relative':'0x03','width':'u8','purpose':'width in 16-pixel cells; 8-pixel tile width=2*value','reader_bus':'0x08033D5A'},
			{'relative':'0x04','width':'u8','purpose':'height in 16-pixel cells; 8-pixel tile height=2*value','reader_bus':'0x08033D4E'},
			{'relative':'0x05','width':'u8 packed','purpose':'low6 music selector (prior established knowledge); high2 separate state'},
			{'relative':'0x06','width':'u8','purpose':'unresolved; no rendering interpretation assigned'},
			{'relative':'0x07','width':'u8 one-based selector, zero=none','purpose':'supplemental initial graphics/animation definition','reader_bus':'0x08034DA0'},
			{'relative':'0x08','width':'u8','purpose':'additional runtime definition selector at table 0x083DDD44; effects not reconstructed'},
			{'relative':'0x0C','width':'u32le bus pointer','purpose':'room exit records','reader_bus':'0x08033CC6'},
			{'relative':'0x10','width':'u32le bus pointer','purpose':'default and rectangle event table','reader_bus':'0x08033E22'},
			{'relative':'0x14','width':'u32le bus pointer','purpose':'actor block; registrations start +0x70','reader_bus':'0x08033E30'},
			{'relative':'0x18','width':'u32le','purpose':'runtime pointer copied at 0x08033E66; meaning unresolved'}]},
	'resource_tables':{'palette':'file 0x00255F00 + 4*resource_id; 240 RGB555 halfwords',
		'tileset':'file 0x0015BA3C + 4*resource_id; GBA LZ77/RL or type00 raw payload',
		'raw_tileset_size':'ROM.u8[0x0015B84C+resource_id]*512',
		'layouts':'file 0x0026E358 + 12*resource_id + 4*layer; row-major u16 chip indices',
		'chipsets':'file 0x0031E7B4 + 12*resource_id + 4*layer; four u16 tiles per chip, TL/TR/BL/BR',
		'collision':'file 0x00303950 + 4*resource_id; width_cells*height_cells unsigned bytes; bit meanings unresolved',
		'priority':'file 0x006309EC + field_map_id; three 2-bit fields, lower wins; lower BG number wins ties'},
	'tile_entry':'bits0..9 tile index; bit10 H flip; bit11 V flip; bits12..15 palette bank; low nibble first in 4bpp byte; color index0 transparent',
	'supplemental_record':'10+4*frame_count bytes; +1 BG/OBJ selector; +2 u16 destination tile relative to 06000000; +4 frame_count; +5 tile_count_minus1; +6 u32 first raw frame pointer; FF record terminator',
	'initial_BG_upload':'destination byte offset=u16(+2)*32-0x8000; size=(u8(+5)+1)*32; OBJ uploads not rendered',
	'blank_tile':'1023 cleared by full field setup at 0x08031AFC..0x08031B04; loaded base/supplemental bytes override it',
	'compression_limits':{'max_decompressed':32768,'max_pixels':MAX_PIXELS,'max_supplemental_records':128},
	'render_scope':'Registered full background layout using base palette and first graphics frames, without event effects or actors; not a complete runtime scene',
}


def csv_text(rows):
	stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
	writer.writeheader();writer.writerows(rows)
	return stream.getvalue()


def main():
	parser=argparse.ArgumentParser(description=__doc__)
	for name in ('rom','menus','binky-evidence','binky-locations','output-dir','image-dir','evidence-output'):
		parser.add_argument('--'+name,type=Path,required=True)
	parser.add_argument('--all',action='store_true',help='Extend rendering after four-map preflight to all 494 known records')
	args=parser.parse_args()
	inputs=[args.rom,args.menus,args.binky_evidence,args.binky_locations]
	before={p:sha(p.read_bytes()) for p in inputs}
	rom=args.rom.read_bytes()
	if len(rom)!=0x800000 or sha(rom) not in (JP_SHA,EN_SHA):
		parser.error('Unrecognized baseline ROM')
	prior=json.loads(args.binky_evidence.read_text(encoding='utf-8-sig'))
	if prior['rom_sha256']!=JP_SHA or prior['fixed_actor_quantity']!=74:
		parser.error('Unexpected authoritative Binky evidence')
	names=node_names(args.menus.read_text(encoding='utf-8-sig'))
	with args.binky_locations.open(encoding='utf-8-sig',newline='') as stream:
		old=list(csv.DictReader(stream))
	verified={r['binky_id']:r for r in prior['locations']}
	for row in old:
		if row['binky_id'] not in verified or any(str(row[k])!=str(verified[row['binky_id']][k]) for k in ('quantity','map_id','collection_flag','node_id')):
			parser.error('Binky CSV does not match authoritative evidence')
	filenames=['maps.csv','map_transitions.csv','map_node_assignments.csv','binky_map_nodes_v2.csv','binkies_per_node_v2.csv']
	outputs=[args.output_dir/name for name in filenames]+[args.evidence_output]
	selected=list(range(MAP_COUNT)) if args.all else list(REPRESENTATIVES)
	image_paths=[args.image_dir/f'map_{m:04X}{suffix}.png' for m in selected for suffix in ('_layer1','_layer2','_layer3','')]
	ignore=args.image_dir/'.gitignore'
	allpaths=outputs+image_paths+[ignore]
	if len({p.resolve() for p in allpaths})!=len(allpaths) or any(p.exists() or p.resolve() in {q.resolve() for q in inputs} for p in allpaths):
		parser.error('All destinations must be new; refusing to overwrite')
	# Prove the common path on the requested representatives before extension.
	preflight={m:render(rom,m) for m in REPRESENTATIVES}
	edges,stops=transitions(rom,prior)
	mapping=assignments(edges,names)
	v2,node_totals=binky_v2(old,mapping,names)
	args.image_dir.mkdir(parents=True,exist_ok=True)
	with ignore.open('x',encoding='utf-8') as stream:
		stream.write('*\n!.gitignore\n')
	catalog,render_evidence,errors=[],[],[]
	for m in range(MAP_COUNT):
		try:
			row=resources(rom,m)[0]
			if m in selected:
				row,images,metadata=preflight[m] if m in preflight else render(rom,m)
				metadata.update(map_id=mid(m),png_sha256=[sha(p) for p in images])
				render_evidence.append(metadata)
				for suffix,data in zip(('_layer1','_layer2','_layer3',''),images):
					with (args.image_dir/f'map_{m:04X}{suffix}.png').open('xb') as stream:
						stream.write(data)
		except ValueError as error:
			row=resources(rom,m)[0]  # dimensions/resource table errors fail rather than inventing a catalog row
			row.update(render_status='unsupported',limitations=str(error))
			errors.append(dict(map_id=mid(m),reason=str(error)))
		catalog.append(row)
		if m%50==0:
			print(f'Catalogued {m+1}/494',flush=True)
	evidence=dict(schema_version=1,rom_sha256=sha(rom),scope='Known field resources and bounded registered script prefixes',
		format=FORMAT,png_encoder=dict(color_type='RGBA8',filter=0,zlib_version=zlib.ZLIB_VERSION,compression_level=9),
		sources=[dict(path=p.as_posix(),sha256=d) for p,d in before.items()],
		address_convention='ROM bus=file+08000000; RAM has no ROM offset',
		representative_preflight=[mid(m) for m in REPRESENTATIVES],rendered_maps=len(render_evidence),unsupported_maps=errors,
		rendered=render_evidence,transition_count=len(edges),script_prefix_stops=stops,
		binky_identity_count=len(v2),binky_quantity=sum(int(r['quantity']) for r in v2),binky_changes=[r['binky_id'] for r in v2 if r['v2_change']!='unchanged'],
		limitations=['Initial backgrounds, not runtime screenshots','Script transition closure incomplete','Reachability is not exclusive node ownership','No candidate reward promoted'],native_windows=[])
	for label,windows in NATIVE.items():
		for a,b in windows:
			evidence['native_windows'].append(dict(label=label,file_start=hx(a),file_end_exclusive=hx(b),sha256=sha(rom[a:b]),
				instructions=[dict(bus=hx(i.address),file_offset=hx(i.address-BUS),bytes=i.raw.hex(' '),text=i.text) for i in inspect(rom,a,b)]))
	for path,content in zip(outputs,[csv_text(rows) for rows in (catalog,edges,mapping,v2,node_totals)]+[json.dumps(evidence,indent=2)+'\n']):
		path.parent.mkdir(parents=True,exist_ok=True)
		with path.open('x',encoding='utf-8',newline='') as stream:
			stream.write(content)
	if any(sha(p.read_bytes())!=d for p,d in before.items()):
		raise RuntimeError('Source input changed')
	print(f'Rendered {len(render_evidence)} maps; {len(errors)} unsupported; {len(edges)} directed transitions; Binkies preserved 74/74',flush=True)


if __name__=='__main__':
	main()
