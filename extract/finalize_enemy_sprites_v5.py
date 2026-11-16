"""Bounded follow-up for 25 multipart participants and Chekkit only.

Preserves v4 files and metadata. Never invokes v4.export or decodes the completed
156-record set. Outputs require a new directory. ROMs are opened only for reading.
"""
import argparse
import collections
import json
from pathlib import Path
import struct

import extract_enemy_sprites as prior

ROOT=prior.ROOT
v1,v2,v3=prior.v1,prior.v2,prior.v3
OLD=ROOT/'reverse_engineering/exports/enemy_sprites_v4/final'
OUT=ROOT/'reverse_engineering/exports/enemy_sprites_v5/final_verified'
EXCEPTION_START=0x5D2BA8
EXCEPTION_END=0x5D2E36
EXCEPTION_SHA='0a45e52441dcf0e84a0aabbf1bdf96fc6748572a5b18cdc03942dcc36d17caf2'
SIZES=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))


def exception_projection(rom,start,expected):
	"""Replay whole tokens via the existing strict decoder, then model ROM upload.

	This changes no ROM/header. A temporary analysis view with a token-derived
	length lets the strict decoder replay ALL tokens, including the excess bytes.
	The declared length and the complete-token length remain separately recorded.
	Only the fingerprinted Chekkit frame-2 run token is admitted. No generic
	malformed-stream tolerance or arbitrary header rewriting is exposed.
	"""
	if start!=EXCEPTION_START or expected!=3072:
		raise ValueError('Outside established Chekkit upload exception')
	stream=v1.take(rom,start,EXCEPTION_END-start)
	if v1.sha(stream)!=EXCEPTION_SHA:raise ValueError('Chekkit exception fingerprint mismatch')
	ledger=v3.strict_rle_ledger(rom,start)
	last=ledger['last_tokens'][-1]
	if (ledger['advertised'],ledger['whole_token_output'],ledger['overshoot'],last['output_before'],last['count'],last['run'],last['payload_hex'])!=(3072,3200,128,3071,129,True,'00'):
		raise ValueError('Unexpected RLE boundary structure')
	analysis_view=b'\x30'+(3200).to_bytes(3,'little')+stream[4:]
	full,consumed=v1.decompress(analysis_view,0,3200)
	if consumed!=len(stream) or full[3072:]!=bytes(128):raise ValueError('Unexpected whole-token output')
	# Native 0804C910..926 configures 12x8 tiles; 0803FFDC..40004
	# uploads 384 bytes per source row, 8 rows = [0,3072), pitch 1024.
	projection=full[:3072]
	proof=dict(ledger,source_file=v1.hx(start),source_bus=v1.hx(start+v1.BUS),source_sha256=EXCEPTION_SHA,
		declared_header=stream[:4].hex(),analysis_replay_length=3200,full_token_sha256=v1.sha(full),
		upload_source_range=[0,3072],upload_sha256=v1.sha(projection),excess_sha256=v1.sha(full[3072:]),
		method='Whole-token replay plus explicit native 12x8 upload projection; original header not corrected',
		bios_semantics='Clipped and full-final-token models have identical uploaded prefix; hardware overflow side effects unverified')
	return projection,consumed,proof


def chekkit(rom,frame):
	if frame not in range(4):raise ValueError('Chekkit base cycle is four frames')
	record=v1.TABLE+0x8C*v1.STRIDE
	spans=[(record+0x2D,3),(record+0x34,24)]
	paltable=v2.ptr(rom,record+0x34,spans);pal=v2.ptr(rom,paltable,spans)
	pb=v1.take(rom,pal,128);spans.append((pal,128));colors=v2.colors(pb)
	palette={6+i:colors[16*i:16*(i+1)] for i in range(4)}
	base=v2.ptr(rom,record+0x38,spans);states=v2.ptr(rom,record+0x3C,spans)
	parts=v2.ptr(rom,states,spans)
	requests=[(base+4*frame,0,12,8)]
	for i in range(3):
		table=v2.ptr(rom,parts+4*i,spans);requests.append((table+4*frame,12+i*6,6,8))
	atlas={};sources=[];exception=None
	for field,x,w,h in requests:
		source=v2.ptr(rom,field,spans)
		if source==EXCEPTION_START:
			if field!=0x634D94 or frame!=2:raise ValueError('Unexpected exception pointer field')
			data,count,exception=exception_projection(rom,source,w*h*32)
		else:data,count=v1.decompress(rom,source,w*h*32)
		if len(data)!=w*h*32:raise ValueError('Upload size mismatch')
		v2.upload(atlas,data,w,h,x);spans.append((source,count))
		sources.append(dict(pointer_field_file=v1.hx(field),source_file=v1.hx(source),source_bus=v1.hx(source+v1.BUS),consumed=count,
			compression='0x30 RLE',upload=[x,0,w,h],decoded_sha256=v1.sha(data),boundary_projection=source==EXCEPTION_START))
	tw,th=rom[record+0x2E]>>4,rom[record+0x2E]&15
	obj,oam=v2.object_render(rom,record,tw,th,atlas,palette,spans)
	layout=v2.ptr(rom,record+0x40,spans);lb=v1.take(rom,layout,tw*th*2);spans.append((layout,len(lb)))
	bg=v2.layout_render(atlas,struct.unpack('<'+'H'*(tw*th),lb),tw,th,palette)
	diff=sum(obj[p+3]!=bg[p+3] or bool(obj[p+3] and obj[p:p+3]!=bg[p:p+3]) for p in range(0,len(obj),4))
	return dict(frame=frame,width=tw*8,height=th*8,pixels=obj,palette_file=v1.hx(pal),palette_table_file=v1.hx(paltable),
		layout_file=v1.hx(layout),sources=sources,oam=oam,bg_obj_difference_count=diff,exception=exception,spans=sorted(set(spans)))


def component_inventory(rom,jp):
	"""Inventory resources and every OBJ referencing the participant's upload.

	No descriptor subset is asserted to be a standalone enemy silhouette. These
	are references in one GLOBAL root descriptor, including mixed palette banks.
	"""
	results=[]
	for entry in v3.null_classifications(rom):
		eid=int(entry['enemy_id'],16);record=v1.TABLE+eid*v1.STRIDE
		if v1.take(rom,record+0x34,24)!=bytes(24):raise ValueError('Participant has unexpected own graphics fields')
		links=[]
		for link in entry['links']:
			root=int(link['root_record_file'],16);slot=link['slot'];spans=[(record+8,68),(root+0x2D,3),(root+0x34,24),(int(link['descriptor_file'],16),40)]
			spans.extend(link['spans'])
			count=2 if (rom[root+0x2F]>>4&3)==0 else 4
			paltable=v2.ptr(rom,root+0x34,spans);pal=v2.ptr(rom,paltable,spans);spans.append((pal,128))
			table=v2.ptr(rom,root+0x44,spans);desc=v2.ptr(rom,table,spans)
			n=struct.unpack('<H',v1.take(rom,desc,2))[0]
			if not 0<n<=128:raise ValueError('Unsupported global descriptor')
			raw=v1.take(rom,desc+2,n*6);spans.append((desc,2+n*6))
			script_table=v2.ptr(rom,root+0x48,spans);scripts=[]
			for fi in range(count):
				script=v2.ptr(rom,script_table+4*fi,spans);body=v1.take(rom,script,6);spans.append((script,6))
				index,duration,end=struct.unpack('<3H',body)
				if index!=0 or not 0<duration<256 or end!=65535:raise ValueError('Unproved descriptor selection')
				scripts.append(dict(frame=fi,file=v1.hx(script),descriptor_index=index,duration=duration))
			lo=12+6*slot;owned={512+y*32+x for y in range(8) for x in range(lo,lo+6)}
			objects=[]
			for i,(a,b,c) in enumerate(struct.iter_unpack('<3H',raw)):
				if a>>14>=3 or a&0x3F00:raise ValueError('Unsupported OBJ mode')
				w,h=SIZES[a>>14][b>>14];tiles={(c&1023)+y*32+x for y in range(h//8) for x in range(w//8)}
				if not tiles&owned:continue
				x,y=b&511,a&255;x=x-512 if x>=256 else x;y=y-256 if y>=128 else y
				bank=c>>12
				if not 6<=bank<=9:raise ValueError('OBJ references outside loaded palettes')
				objects.append(dict(index=i,attributes=[a,b,c],shape=a>>14,size=b>>14,x=x,y=y,width=w,height=h,
					hflip=bool(b&0x1000),vflip=bool(b&0x2000),priority=c>>10&3,tile=c&1023,
					palette_bank=bank,palette_file=v1.hx(pal+(bank-6)*32),
					all_tiles_in_component=tiles<=owned,component_tile_ids=sorted(tiles&owned)))
			if not objects:raise ValueError('Component has no OBJ references')
			streams=[]
			for state_link in link['state_links']:
				ft=int(state_link['frame_table_file'],16)
				spans.extend([(int(state_link['part_table_file'],16)+slot*4,4)])
				for fi in range(count):
					field=ft+4*fi;source=v2.ptr(rom,field,spans);data,consumed=v1.decompress(rom,source,1536)
					if len(data)!=1536:raise ValueError('Not a 6x8 component')
					spans.append((source,consumed))
					streams.append(dict(state=state_link['flag_state'],frame=fi,pointer_field_file=v1.hx(field),source_file=v1.hx(source),
						source_bus=v1.hx(source+v1.BUS),consumed=consumed,decoded_sha256=v1.sha(data),compression=f'0x{rom[source]:02X}'))
			if any(v1.take(rom,p,n)!=v1.take(jp,p,n) for p,n in spans):raise ValueError('JP/English participant evidence differs')
			bounds=[min(o['x'] for o in objects),min(o['y'] for o in objects),max(o['x']+o['width'] for o in objects),max(o['y']+o['height'] for o in objects)]
			links.append(dict(link,root_descriptor_file=v1.hx(desc),root_descriptor_bus=v1.hx(desc+v1.BUS),root_object_count=n,
				palette_table_file=v1.hx(paltable),palette_set0_file=v1.hx(pal),palette_banks_used=sorted({o['palette_bank'] for o in objects}),
				component_object_bounds=bounds,bounds_meaning='Bounds of root OBJ references to uploaded component, not a proven standalone crop',
				objects=objects,scripts=scripts,streams=streams,base_cycle_frames=count,
				spans=[dict(file=v1.hx(p),bus=v1.hx(p+v1.BUS),size=n,sha256=v1.sha(v1.take(rom,p,n)),jp_english_equal=True) for p,n in sorted(set(spans))]))
		results.append(dict(enemy_id=f'{eid:02X}',record_file=v1.hx(record),confidence='Confirmed resource/descriptor linkage; Unsupported standalone reconstruction',
			classification='root-owned component; standalone composition unsupported',links=links,
			reason=f"Root {links[0]['root_enemy_id']} owns one global OBJ descriptor {links[0]['root_descriptor_file']}; child slot {links[0]['slot']} selects upload x={12+6*links[0]['slot']}..{17+6*links[0]['slot']}. Own +34..4B are zero. Descriptor subsets select tile resources, not independently assigned child draw objects; full child silhouette/crop and contributions from base/other blocks are unproved."))
	return results


def export(output):
	rom,jp=v3.load_roms()
	participants=component_inventory(rom,jp)
	decoded=[chekkit(rom,i) for i in range(4)]
	for d in decoded:
		if any(v1.take(rom,p,n)!=v1.take(jp,p,n) for p,n in d['spans']):raise ValueError('JP/English Chekkit spans differ')
	output.mkdir(parents=True,exist_ok=False)
	def write(path,data):
		with (output/path).open('xb') as f:f.write(data)
	write('.gitignore',b'*\n!.gitignore\n')
	frames=json.loads((OLD/'frames.json').read_text());coverage=json.loads((OLD/'coverage.json').read_text())
	for row in frames:
		if v1.sha((OLD/row['png']).read_bytes())!=row['png_sha256']:raise ValueError('Preserved native PNG fingerprint mismatch')
	# Copy bytes, never re-extract the completed 156 records.
	preserved=[]
	for old in sorted(OLD.rglob('*.png')):
		rel=old.relative_to(OLD);(output/rel).parent.mkdir(parents=True,exist_ok=True)
		data=old.read_bytes();write(rel,data);preserved.append(dict(path=rel.as_posix(),sha256=v1.sha(data)))
	(output/'8C_Chekkit').mkdir()
	evidence=[]
	for d in decoded:
		fi=d['frame'];path=f'8C_Chekkit/frame_{fi:02d}.png';w,h=d['width'],d['height'];image=v1.png(w,h,d['pixels'])
		write(path,image);write(path.replace('.png','_4x.png'),v1.png(w*4,h*4,v1.enlarge(d['pixels'],w,h)))
		frames.append(dict(enemy_id='8C',english_name='Chekkit',record_file=v1.hx(v1.TABLE+0x8C*76),
			graphics_descriptor=v1.hx(v1.TABLE+0x8C*76+0x38),palette_descriptor=v1.hx(v1.TABLE+0x8C*76+0x34),
			palette_pointer=v1.hx(int(d['palette_file'],16)+v1.BUS),layout_pointer=v1.hx(int(d['layout_file'],16)+v1.BUS),
			tile_sources=d['sources'],compression=['0x30 RLE; explicit frame-2 upload projection'],width=w,height=h,frame_index=fi,frame_count=4,
			palette_resource=d['palette_file']+':128',graphics_resource='Chekkit root pointer graph; see evidence',png=path,
			pixel_sha256=v1.sha(d['pixels']),png_sha256=v1.sha(image),confidence='Confirmed scoped OBJ projection',
			notes='Descriptor 0; palette set 0; actor flags 0. Frame 2 BG differs by 10 visible pixels. BIOS overflow side effects unverified; complete-token replay followed by native upload range.'))
		evidence.append({k:v for k,v in d.items() if k not in ('pixels','spans')})
		evidence[-1]['spans']=[dict(file=v1.hx(p),bus=v1.hx(p+v1.BUS),size=n,sha256=v1.sha(v1.take(rom,p,n)),jp_english_equal=True) for p,n in d['spans']]
	byid={e['enemy_id']:e for e in participants}
	for row in coverage:
		if row['enemy_id'] in byid:row['reason']=byid[row['enemy_id']]['reason']
		if row['enemy_id']=='8C':row.update(status='successfully decoded',confidence='Confirmed scoped OBJ projection',reason=frames[-1]['notes'],frame_count=4,
			graphics_resource='Chekkit root pointer graph; see evidence',palette_resource=frames[-1]['palette_resource'])
	counts=dict(collections.Counter(r['status'] for r in coverage));counts.setdefault('unresolved',0)
	summary=dict(records=182,counts=counts,decoded_records=157,unsupported_standalone_records=25,newly_supported_ids=['8C'],
		new_native_frames=4,total_native_frames=len(frames),preserved_native_frames=326,preserved_png_files=len(preserved),
		scope='Base cycles and selected OBJ profiles only; not complete extraction of all records or battle animations')
	for name,obj in [('frames.json',frames),('coverage.json',coverage),('summary.json',summary),('participants.json',participants),('chekkit_evidence.json',evidence),('preserved_pngs.json',preserved)]:
		write(name,(json.dumps(obj,indent=2)+'\n').encode())
	v1.csv_new(output/'coverage.csv',coverage)
	v1.csv_new(output/'unsupported.csv',[r for r in coverage if r['enemy_id'] in byid])
	return summary


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
	a=p.parse_args();print(json.dumps(export(a.output),indent=2))
