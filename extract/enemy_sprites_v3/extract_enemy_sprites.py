"""v3: scoped multipart OBJ profiles, null-record consumer evidence and RLE audit.

ROMs are read only. Outputs must be fresh and are created exclusively. The
strict v1/v2 compression decoders and all earlier mappings remain unchanged.
"""
import argparse
import collections
import importlib.util
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('sprites_v2', ROOT / 'tools/extract/enemy_sprites_v2/extract_enemy_sprites.py')
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)
v1 = v2.v1
BUS, TABLE, STRIDE = v2.BUS, v2.TABLE, v2.STRIDE
PRIOR = ROOT / 'reverse_engineering/exports/enemy_sprites_v2/final'
OUT = ROOT / 'reverse_engineering/exports/enemy_sprites_v3'
TARGETS = {int(r['enemy_id'],16) for r in v2.rows(PRIOR/'unresolved.csv')}
DISAGREEMENTS = {0x1D,0x2E,0x43,0x45,0x47,0x49}
NULLS = TARGETS - DISAGREEMENTS - {0x8C}
assert len(TARGETS)==32 and len(NULLS)==25
STATE_SCOPE = 'Confirmed static OBJ profile only; descriptor 0; palette set 0; all per-part actor flag states 0; encounter reachability and BG equivalence unproved'


def load_roms():
	rom=(ROOT/'Tomato Adventure (Japan) (patched).gba').read_bytes()
	jp=(ROOT/'Tomato Adventure (Japan).gba').read_bytes()
	if v1.sha(rom)!=v1.EN_SHA or v1.sha(jp)!=v1.JP_SHA:
		raise ValueError('Verified baseline ROMs required')
	return rom,jp


def null_classifications(rom):
	"""Search only the established formation descriptor interval, stride 0x28.

	Record links are accepted only in populated descriptor slots selected by the
	traced variant consumer, never through an untyped whole-ROM pointer search.
	"""
	links=collections.defaultdict(list)
	for descriptor in range(0x4559B4,0x456C00-0x28+1,0x28):
		header=v1.take(rom,descriptor,4)
		active=sum(b!=255 for b in header)
		if not active:continue
		for variant in range(active):
			fields=[descriptor+4,descriptor+8+variant*8,descriptor+12+variant*8]
			pointers=[struct.unpack('<I',v1.take(rom,f,4))[0] for f in fields]
			for slot,pointer in enumerate(pointers):
				if pointer < BUS+TABLE or (pointer-BUS-TABLE)%STRIDE:continue
				eid=(pointer-BUS-TABLE)//STRIDE
				if eid not in NULLS:continue
				root=pointers[0]-BUS
				if not header[0]&64 or slot not in (1,2):
					raise ValueError('Unexpected null-record renderer/slot; requires investigation')
				count=rom[root+0x2F]>>6
				if slot>=count:raise ValueError('Shared part index exceeds native count')
				spans=[(descriptor,0x28),(root+0x2D,3),(root+0x34,16)]
				states=v2.ptr(rom,root+0x3C,spans)
				state_links=[]
				for state in (0,1):
					parts=v2.ptr(rom,states+state*4,spans)
					frames=v2.ptr(rom,parts+slot*4,spans)
					state_links.append(dict(flag_state=state,part_table_file=v1.hx(parts),frame_table_file=v1.hx(frames)))
				links[eid].append(dict(descriptor_file=v1.hx(descriptor),header=header.hex(),variant=variant,
					pointer_field_file=v1.hx(fields[slot]),slot=slot,root_enemy_id=f'0x{(root-TABLE)//STRIDE:02X}',root_record_file=v1.hx(root),
					component_index=slot,upload_tiles=[12+slot*6,0,6,8],state_links=state_links,spans=sorted(set(spans))))
	result=[]
	for eid in sorted(NULLS):
		if not links[eid]:raise ValueError(f'No typed formation proof for null record {eid:02X}')
		result.append(dict(enemy_id=f'0x{eid:02X}',classification='shared_multipart_renderer_participant',classification_confidence='Confirmed (listed formation paths)',
			standalone_status='Unconfirmed; no standalone sprite mapping proved',alias_status='No whole-sprite alias proved',
			graphics_resolution='unresolved_standalone',reason='Root record owns composite graphics and palettes; child slot selects a root-owned component using its actor flag. No per-record standalone layout or palette established.',links=links[eid]))
	return result


def assemble(rom,eid,states=None,frame=0):
	if eid not in DISAGREEMENTS | {0x8C}:raise ValueError('Outside v3 owner scope')
	record=TABLE+eid*STRIDE;raw=v1.take(rom,record,STRIDE)
	parts,mode=raw[0x2F]>>6,raw[0x2F]>>4&3
	if parts not in (2,3) or mode not in (0,1):raise ValueError('Unsupported multipart header')
	states=[0]*parts if states is None else states
	if len(states)!=parts or any(s not in (0,1) for s in states):raise ValueError('Unsupported actor state selection')
	if not 0<=frame<(2 if mode==0 else 4):raise ValueError('Frame outside proven native cycle')
	spans=[(record+0x2D,3),(record+0x34,24)]
	palette_table=v2.ptr(rom,record+0x34,spans)
	pal=v2.ptr(rom,palette_table,spans)
	pb=v1.take(rom,pal,128);spans.append((pal,128))
	col=v2.colors(pb);palette={6+i:col[i*16:(i+1)*16] for i in range(4)}
	base=v2.ptr(rom,record+0x38,spans)
	state_table=v2.ptr(rom,record+0x3C,spans)
	requests=[(base+frame*4,0,12,8,'base',None)]
	for i,state in enumerate(states):
		part_table=v2.ptr(rom,state_table+state*4,spans)
		frame_table=v2.ptr(rom,part_table+i*4,spans)
		requests.append((frame_table+frame*4,12+i*6,6,8,f'part_{i}',state))
	atlas,sources={},[]
	for field,x,w,h,component,state in requests:
		source=v2.ptr(rom,field,spans)
		data,count=v1.decompress(rom,source,w*h*32)
		v2.upload(atlas,data,w,h,x)
		spans.append((source,count))
		sources.append(dict(component=component,actor_flag_state=state,field=field,source=source,consumed=count,
			format=f'0x{rom[source]:02X}',decoded_sha256=v1.sha(data),upload=[x,0,w,h]))
	tw,th=raw[0x2E]>>4,raw[0x2E]&15
	obj,proof=v2.object_render(rom,record,tw,th,atlas,palette,spans)
	layout=v2.ptr(rom,record+0x40,spans)
	lb=v1.take(rom,layout,tw*th*2);spans.append((layout,len(lb)))
	entries=struct.unpack('<'+'H'*(tw*th),lb)
	bg=v2.layout_render(atlas,entries,tw,th,palette)
	desc=int(proof['descriptor_file'],16)
	objects=[]
	for index,(a,b,c) in enumerate(struct.iter_unpack('<3H',v1.take(rom,desc+2,proof['count']*6))):
		objects.append(dict(index=index,attributes=[a,b,c],x=(b&511)-512 if b&256 else b&511,
			y=(a&255)-256 if a&128 else a&255,tile=c&1023,palette_bank=c>>12,hflip=bool(b&0x1000),vflip=bool(b&0x2000),priority=c>>10&3))
	differences=[]
	for p in range(0,len(obj),4):
		if obj[p+3]!=bg[p+3] or (obj[p+3] and obj[p:p+3]!=bg[p:p+3]):
			differences.append([p//4%(tw*8),p//4//(tw*8)])
	return dict(record=record,tw=tw,th=th,frame=frame,parts=parts,states=states,palette=pal,palette_table=palette_table,
		layout=layout,descriptor=desc,spans=sorted(set(spans)),sources=sources,atlas=atlas,colors=palette,
		pixels=obj,oam=proof,objects=objects,bg_pixels=bg,bg_obj_difference_count=len(differences),first_differences=differences[:16])


def strict_rle_ledger(rom,start):
	"""Independent token accounting; never truncates or produces accepted pixels."""
	header=v1.take(rom,start,4)
	if header[0]!=0x30:raise ValueError('Not RLE')
	size=int.from_bytes(header[1:],'little')
	if not 0<size<=0x8000:raise ValueError('RLE size outside analysis bound')
	q,n=start+4,0;tokens=[]
	while n<size:
		token=q;flag=v1.take(rom,q,1)[0];q+=1
		count=(flag&127)+(3 if flag&128 else 1)
		payload=1 if flag&128 else count
		data=v1.take(rom,q,payload);q+=payload
		tokens.append(dict(token_file=v1.hx(token),output_before=n,count=count,run=bool(flag&128),payload_hex=data.hex()))
		n+=count
	if n!=size:
		return dict(status='rejected',advertised=size,whole_token_output=n,overshoot=n-size,consumed=q-start,
			end_file_exclusive=v1.hx(q),last_tokens=tokens[-5:],token_count=len(tokens))
	return dict(status='exact',advertised=size,whole_token_output=n,overshoot=0,consumed=q-start,end_file_exclusive=v1.hx(q),last_tokens=tokens[-5:],token_count=len(tokens))


def build_evidence(rom,jp):
	nulls=null_classifications(rom)
	for entry in nulls:
		for link in entry['links']:
			link['spans']=[dict(file=v1.hx(p),size=n,sha256=v1.sha(v1.take(rom,p,n)),jp_english_equal=v1.take(rom,p,n)==v1.take(jp,p,n)) for p,n in link['spans']]
	owners=[]
	for eid in sorted(DISAGREEMENTS):
		frames=[];part_count=rom[TABLE+eid*STRIDE+0x2F]>>6
		# These are the exact states admitted by the native per-actor selector;
		# state-one diagnostics are not a claim of encounter reachability.
		for state in (0,1):
			for fi in range(2):
				d=assemble(rom,eid,[state]*part_count,fi)
				if any(v1.take(rom,p,n)!=v1.take(jp,p,n) for p,n in d['spans']):raise ValueError('JP/EN evidence mismatch')
				frames.append(dict(frame_index=fi,part_states=d['states'],bg_obj_difference_count=d['bg_obj_difference_count'],first_differences=d['first_differences'],
					sources=d['sources'],oam=d['oam'],objects=d['objects'],obj_pixel_sha256=v1.sha(d['pixels']),bg_pixel_sha256=v1.sha(d['bg_pixels']),
					spans=[dict(file=v1.hx(p),size=n,sha256=v1.sha(v1.take(rom,p,n)),jp_english_equal=True) for p,n in d['spans']]))
		owners.append(dict(enemy_id=f'0x{eid:02X}',classification='verified_OBJ_profile; BG representation differs',confidence=STATE_SCOPE,diagnostics=frames))
	chekkit=strict_rle_ledger(rom,0x5D2BA8)
	chekkit.update(enemy_id='0x8C',confidence='Confirmed token accounting; BIOS boundary behavior Unconfirmed',source_file='0x005D2BA8',pointer_field_file='0x00634D94',
		jp_english_stream_equal=rom[0x5D2BA8:0x5D2BA8+chekkit['consumed']]==jp[0x5D2BA8:0x5D2BA8+chekkit['consumed']],
		next_pointer_field_file='0x00634D9C',next_stream_file=v1.hx(struct.unpack_from('<I',rom,0x634D9C)[0]-BUS),
		blocker='Final RLE token exceeds advertised size by 128 bytes. Native ROM delegates to BIOS SWI 0x14; BIOS implementation and actual boundary semantics not present in ROM evidence. No clipping, padding exemption or partial-cycle export enabled.')
	return dict(null_records=nulls,owners=owners,chekkit=chekkit)


def export(output,previews=True):
	rom,jp=load_roms()
	evidence=build_evidence(rom,jp)
	output.mkdir(parents=True,exist_ok=False)
	def write(name,data):
		with (output/name).open('xb') as f:f.write(data)
	write('.gitignore',b'*\n!.gitignore\n')
	# Earlier mappings are copied exactly, including their original confidence
	# and selected-state limitations. No investigation of accepted IDs here.
	for path in PRIOR.glob('*.png'):write(path.name,path.read_bytes())
	metadata=[dict(row,v3_scope='Preserved v2 values and selected-state limits',renderer_profile='inherited',components='') for row in v2.rows(PRIOR/'frames.csv')]
	catalog=[];classifications={e['enemy_id']:e for e in evidence['null_records']}
	for row in v2.rows(PRIOR/'enemies.csv'):
		eid=int(row['enemy_id'],16)
		if eid not in TARGETS:
			catalog.append(dict(row,v3_status='Preserved',classification='inherited_verified_mapping',classification_confidence=row['confidence']))
		elif eid in NULLS:
			e=classifications[row['enemy_id']]
			catalog.append(dict(row,reason=e['reason'],v3_status='Unresolved standalone; shared renderer classified',classification=e['classification'],classification_confidence=e['classification_confidence']))
		elif eid==0x8C:
			catalog.append(dict(row,reason=evidence['chekkit']['blocker'],v3_status='Unresolved',classification='RLE boundary unresolved',classification_confidence='Confirmed token accounting; decoding acceptance Unconfirmed'))
		else:
			catalog.append(dict(row,status='verified_OBJ_profile',reason='',confidence=STATE_SCOPE,v3_status='New OBJ profile',classification='multipart shared OBJ renderer',classification_confidence='Confirmed for specified profile'))
			for fi in range(2):
				d=assemble(rom,eid,frame=fi);w,h=d['tw']*8,d['th']*8
				name=f'enemy_{eid:02X}_OBJ_state0_frame{fi}.png';image=v1.png(w,h,d['pixels']);write(name,image)
				if previews:write(name.replace('.png','_4x.png'),v1.png(w*4,h*4,v1.enlarge(d['pixels'],w,h)))
				sources=d['sources']
				metadata.append(dict(enemy_id=row['enemy_id'],enemy_name=row['enemy_name'],record_file=v1.hx(d['record']),record_bus=v1.hx(BUS+d['record']),frame_index=fi,
					pointer_field_file='|'.join(v1.hx(s['field']) for s in sources),graphics_file='|'.join(v1.hx(s['source']) for s in sources),graphics_bus='|'.join(v1.hx(BUS+s['source']) for s in sources),
					compressed_end_exclusive_file='|'.join(v1.hx(s['source']+s['consumed']) for s in sources),width=w,height=h,size_selector=row['size_selector'],dimensions_file=v1.hx(d['record']+0x2E),
					palette_file=v1.hx(d['palette']),palette_bus=v1.hx(BUS+d['palette']),palette_provenance='root record +34 -> palette table[0] -> 128 raw BGR555 bytes, banks 6..9',
					layout_file=v1.hx(d['descriptor']),decoding_format='Native OBJ descriptors; multipart 4bpp 2D atlas; strict GBA RLE 0x30',confidence=STATE_SCOPE,
					jp_english_source_spans_equal=True,decoded_sha256='|'.join(s['decoded_sha256'] for s in sources),png_sha256=v1.sha(image),png=name,
					limitations='OBJ profile only, normalized native descriptor bounds; BG layout differs; all actor flag states 0, palette set 0; transitions/reachability/secondary overlays excluded',
					v2_mapping='v3 OBJ-specific addition',state=0,source_details=json.dumps(sources,separators=(',',':')),oam_proof=json.dumps(d['oam'],separators=(',',':')),
					v3_scope=STATE_SCOPE,renderer_profile='OBJ',components=json.dumps(d['objects'],separators=(',',':'))))
	v1.csv_new(output/'enemies.csv',catalog)
	v1.csv_new(output/'frames.csv',metadata)
	v1.csv_new(output/'unresolved.csv',[r for r in catalog if r['v3_status'].startswith('Unresolved')])
	v1.csv_new(output/'classifications.csv',[{k:e[k] for k in ('enemy_id','classification','classification_confidence','standalone_status','alias_status','graphics_resolution','reason')} for e in evidence['null_records']])
	write('evidence.json',(json.dumps(evidence,indent=2)+'\n').encode())
	summary=dict(records=182,preserved_records=150,new_OBJ_profiles=6,new_native_frames=12,verified_records_with_scoped_profiles=156,
		unresolved_standalone_records=26,shared_renderer_classified=25,RLE_unresolved=1,native_frames=326,preview_frames=326 if previews else 314)
	write('summary.json',(json.dumps(summary,indent=2)+'\n').encode())
	return summary


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
	args=p.parse_args();print(json.dumps(export(args.output),indent=2))
