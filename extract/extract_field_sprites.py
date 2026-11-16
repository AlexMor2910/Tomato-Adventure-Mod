"""Read-only field actor resource census and bounded 1D OBJ frame exporter.

Only initial map header/actor bindings are covered. Packed animation pointer-table
extent is structurally inferred and explicitly marked Probable; frame pointers,
OBJ attributes, raw tile lengths and palettes are independently bounds checked.
No enemy, battle-player, Gimmick, portrait or interface extraction is invoked.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import struct

import extract_field_maps as gba

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reverse_engineering/exports/field_sprites_v1/final_verified'
MAP_TABLE,MAP_COUNT,BUS=0x62D3E4,494,0x08000000
SIZES=(((8,8),(16,16),(32,32),(64,64)),((16,8),(32,8),(32,16),(64,32)),((8,16),(8,32),(16,32),(32,64)))


def sha(b):return hashlib.sha256(b).hexdigest()
def hx(n):return f'0x{n:08X}'
def pointer(rom,p):return gba.ptr(rom,p)


def load_roms():
	jp=(ROOT/'Tomato Adventure (Japan).gba').read_bytes()
	en=(ROOT/'Tomato Adventure (Japan) (patched).gba').read_bytes()
	if sha(jp)!=gba.JP_SHA or sha(en)!=gba.EN_SHA:raise ValueError('Verified baseline ROMs required')
	return en,jp


def discover(rom):
	resources=collections.defaultdict(list);bindings=collections.defaultdict(list);actors=[];unbound=[]
	for mid in range(MAP_COUNT):
		mr=MAP_TABLE+mid*28;block=pointer(rom,mr+20)
		header=block if int.from_bytes(gba.take(rom,block,4),'little') else 0x140180
		for slot in range(16):
			field=header+slot*4;value=int.from_bytes(gba.take(rom,field,4),'little')
			if value:
				g=pointer(rom,field);resources[g].append(dict(map_id=f'{mid:04X}',graphics_slot=slot,pointer_field_file=hx(field),actor_block_file=hx(block),effective_header_file=hx(header)))
		# Player uses graphics slot 0 and palette bank 0 on the ordinary path.
		g=pointer(rom,header);pal=pointer(rom,header+64)
		bindings[g,pal].append(dict(map_id=f'{mid:04X}',actor_slot=0,kind='default_field_player',record_file=None,graphics_slot=0,palette_slot=0))
		for slot in range(1,16):
			a=block+112+(slot-1)*16
			if gba.take(rom,a,1)[0]==255:break
			raw=gba.take(rom,a,16);gi=raw[1]&31;pi=raw[2]>>4
			ref=dict(map_id=f'{mid:04X}',actor_slot=slot,kind='registered_field_actor',record_file=hx(a),actor_identity=gba.u16(raw,14),
				graphics_slot=gi,palette_slot=pi,facing_selector=raw[2]&15,initial_alternate_frame=bool(raw[1]&32),
				flags=raw[0],pickup=bool(raw[1]&128),raw_hex=raw.hex())
			actors.append(ref)
			try:
				if gi>=16 or pi>=12:raise ValueError('Selector outside copied graphics/palette header')
				g=pointer(rom,header+gi*4);pal=pointer(rom,header+64+pi*4)
			except ValueError as error:unbound.append(dict(ref,reason=str(error)));continue
			bindings[g,pal].append(ref)
	if len(actors)!=2987:raise ValueError('Established actor census changed')
	return resources,bindings,actors,unbound


def descriptor(rom,resource,fi):
	tile_count=gba.take(rom,resource+3,1)[0]
	ft=pointer(rom,resource+12);field=ft+fi*4;d=pointer(rom,field);count=gba.u16(rom,d)
	if count>128:raise ValueError('OBJ count exceeds bounded hardware list')
	objects=[]
	for index,(a,b,c) in enumerate(struct.iter_unpack('<3H',gba.take(rom,d+2,count*6))):
		if not a&0x100 and a&0x200:continue # non-affine disabled OBJ
		if a&0x3D00 or a>>14==3:raise ValueError('Affine/mode/mosaic/8bpp/reserved OBJ unsupported')
		w,h=SIZES[a>>14][b>>14];tile=c&1023
		if tile+w*h//64>tile_count:raise ValueError('OBJ references tiles outside descriptor upload')
		x,y=b&511,a&255;x=x-512 if x>=256 else x;y=y-256 if y>=128 else y
		objects.append(dict(index=index,attributes=[a,b,c],x=x,y=y,width=w,height=h,tile=tile,
			hflip=bool(b&0x1000),vflip=bool(b&0x2000),priority=c>>10&3))
	bounds=None
	if objects:
		bounds=[min(o['x'] for o in objects),min(o['y'] for o in objects),max(o['x']+o['width'] for o in objects),max(o['y']+o['height'] for o in objects)]
		if not 0<(bounds[2]-bounds[0])*(bounds[3]-bounds[1])<=65536:raise ValueError('Unsupported canvas bounds')
	return dict(frame_index=fi,pointer_field_file=hx(field),descriptor_file=hx(d),object_count=count,objects=objects,bounds=bounds,
		spans=[(field,4),(d,2+count*6)])


def sequences(rom,resource):
	at=pointer(rom,resource+8);first=pointer(rom,at);extent=first-at
	if extent%4 or not 0<extent//4<=64:raise ValueError('Unsupported packed animation pointer prefix')
	result=[];frames={};errors={};spans=[(at,extent)]
	for si in range(extent//4):
		seq=dict(sequence_index=si,steps=[],status='supported',reason='',timing='Raw u16 threshold values; field counter rate and transitions not fully established')
		try:
			s=pointer(rom,at+si*4);seq['source_file']=hx(s)
			# A packed pointer prefix is accepted only if every pointer points at or
			# beyond the first script. Its extent remains structural, not a count field.
			if s<first:raise ValueError('Sequence overlaps inferred pointer prefix')
			for j in range(512):
				fi=gba.u16(rom,s+j*4)
				if fi==65535:spans.append((s,j*4+2));break
				threshold=gba.u16(rom,s+j*4+2)
				if fi not in frames and fi not in errors:
					try:frames[fi]=descriptor(rom,resource,fi)
					except ValueError as e:errors[fi]=str(e)
				seq['steps'].append(dict(position=j,frame=fi,threshold=threshold,frame_status='supported' if fi in frames else 'unsupported',reason=errors.get(fi,'')))
			else:raise ValueError('Sequence exceeds bounded 512 steps')
			if any(s['frame_status']=='unsupported' for s in seq['steps']):seq.update(status='partial',reason='One or more referenced frames rejected; exact reasons retained')
			if not seq['steps']:seq.update(status='unsupported',reason='Empty sequence starts with FFFF; no initial frame modeled')
		except ValueError as e:seq.update(status='unsupported',reason=str(e))
		result.append(seq)
	for f in frames.values():spans.extend(f['spans'])
	return result,frames,errors,spans


def palette(rom,start):
	colors=[gba.rgba555(c) for c in struct.unpack('<16H',gba.take(rom,start,32))]
	colors[0]=b'\0\0\0\0'
	return colors


def render(gfx,frame,colors):
	"""GBA 1D 4bpp OBJ assembly; palette is replaced by the actor bank."""
	if frame['bounds'] is None:return None
	l,t,r,b=frame['bounds'];w,h=r-l,b-t;out=bytearray(w*h*4)
	# Smaller priority first, then earlier OAM index wins; compose back-to-front.
	for obj in sorted(frame['objects'],key=lambda o:(o['priority'],o['index']),reverse=True):
		ow,oh=obj['width'],obj['height'];tiles={}
		for y in range(oh):
			for x in range(ow):
				sx=ow-1-x if obj['hflip'] else x;sy=oh-1-y if obj['vflip'] else y
				tile=obj['tile']+(sy//8)*(ow//8)+sx//8
				if tile not in tiles:tiles[tile]=gba.tile_pixels(gfx,tile,colors)
				p=((sy%8)*8+sx%8)*4;value=tiles[tile][p:p+4]
				if value[3]:
					q=((obj['y']-t+y)*w+obj['x']-l+x)*4;out[q:q+4]=value
	return bytes(out)


def csv_new(path,rows):
	if not rows:return
	keys=list(dict.fromkeys(k for row in rows for k in row))
	with path.open('x',encoding='utf-8',newline='') as f:
		w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
		w.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)


def export(output):
	en,jp=load_roms();resources,bindings,actors,unbound=discover(en)
	discovery_spans=[]
	for mid in range(MAP_COUNT):
		mr=MAP_TABLE+28*mid;block=pointer(en,mr+20)
		discovery_spans.extend([(mr,28),(block,112)])
	discovery_spans.append((0x140180,112))
	discovery_spans.extend((int(a['record_file'],16),16) for a in actors)
	if any(gba.take(en,p,n)!=gba.take(jp,p,n) for p,n in discovery_spans):raise ValueError('JP/English initial map/actor binding structures differ')
	output.mkdir(parents=True,exist_ok=False)
	def write(name,data):
		with (output/name).open('xb') as f:f.write(data)
	write('.gitignore',b'*\n!.gitignore\n')
	catalog=[];metadata=[];animations=[];proof=[]
	for resource in sorted(resources):
		rid=f'R_{resource:08X}';row=dict(resource_id=rid,descriptor_file=hx(resource),descriptor_bus=hx(resource+BUS),
			status='unsupported',confidence='Unsupported',reason='',identity=None,map_load_references=resources[resource],
			graphics_file=None,graphics_sha256=None,referenced_frame_count=0,exported_native_pngs=0,palette_variants=0)
		spans=[(resource,16)]
		try:
			gfx=pointer(en,resource+4);tile_count=en[resource+3];raw=gba.take(en,gfx,tile_count*32);spans.append((gfx,len(raw)))
			seq,frames,errors,ss=sequences(en,resource);spans.extend(ss)
			if any(gba.take(en,p,n)!=gba.take(jp,p,n) for p,n in spans):raise ValueError('JP/English structural or tile spans differ')
			row.update(graphics_file=hx(gfx),graphics_sha256=sha(raw),tile_count=tile_count,referenced_frame_count=len(frames),
				animation_table_file=hx(pointer(en,resource+8)),frame_table_file=hx(pointer(en,resource+12)),
				sequence_count=len(seq),sequence_extent_confidence='Probable; packed pointer prefix until first script',frame_errors=errors)
			animations.append(dict(resource_id=rid,sequences=seq,direction_selectors={str(k):en[0x631920+k] for k in (1,2,4,8)},
				association='Selector-to-sequence numeric mapping only; cardinal names and idle/walk transitions unproved'))
			variants=sorted((pal,refs) for (g,pal),refs in bindings.items() if g==resource)
			row['palette_variants']=len(variants)
			for pal,refs in variants:
				pb=gba.take(en,pal,32)
				if pb!=gba.take(jp,pal,32):raise ValueError('JP/English palette differs')
				spans.append((pal,32));colors=palette(en,pal);vid=f'{rid}_P_{pal:08X}';folder=output/vid;folder.mkdir()
				for fi,f in sorted(frames.items()):
					pixels=render(raw,f,colors)
					path=None;w=h=None
					if pixels is not None:
						l,t,r,b=f['bounds'];w,h=r-l,b-t;path=f'{vid}/frame_{fi:03d}.png';image=gba.png(w,h,pixels);write(path,image);row['exported_native_pngs']+=1
					associations=[dict(sequence=s['sequence_index'],positions=[x['position'] for x in s['steps'] if x['frame']==fi]) for s in seq if any(x['frame']==fi for x in s['steps'])]
					metadata.append(dict(resource_id=rid,variant_id=vid,identity=None,map_actor_references=refs,rom_descriptor_file=hx(resource),rom_graphics_file=hx(gfx),
						palette_file=hx(pal),palette_sha256=sha(pb),compression='raw 4bpp tile upload; no stream decompression',width=w,height=h,frame=fi,
						obj_descriptor_file=f['descriptor_file'],bounds=f['bounds'],objects=f['objects'],direction=None,animation_associations=associations,
						png=path,pixel_sha256=sha(pixels) if pixels is not None else None,png_sha256=sha(image) if pixels is not None else None,
						confidence='Confirmed static OBJ render; sequence extent Probable',unresolved='NPC name and runtime animation transitions unproved; no runtime recoloring/affine effects',
						graphics_resource_identity=hx(gfx)+':'+str(len(raw)),palette_resource_identity=hx(pal),frame_status='visible' if pixels is not None else 'zero/disabled objects; no image canvas'))
			if not variants:row.update(status='structurally decoded; palette unbound',confidence='Probable',reason='Loaded resource has no registered actor/player palette association')
			elif frames:row.update(status='partial' if errors or any(s['status']!='supported' for s in seq) else 'supported scoped frames',confidence='Confirmed frames; Probable sequence extent',reason='Failed sequences/frames retained' if errors else '')
			else:row['reason']='No supported referenced frames'
		except ValueError as error:row['reason']=str(error)
		catalog.append(row)
		proof.append(dict(resource_id=rid,spans=[dict(file=hx(p),bus=hx(p+BUS),size=n,sha256=sha(gba.take(en,p,n)),jp_english_equal=gba.take(en,p,n)==gba.take(jp,p,n)) for p,n in sorted(set(spans))]))
	# Field player slot 0 is structurally proved. Name binding to the protagonist
	# is Probable; no companion name is assigned from descriptor order/artwork.
	player_resources=sorted({g for (g,pal),refs in bindings.items() if any(r['kind']=='default_field_player' for r in refs)})
	default_resource=pointer(en,0x140180)
	playable=[dict(name='DeMille',status='Default fallback field-player resource exported; name association Probable',resources=[f'R_{default_resource:08X}'],
		confidence='Confirmed slot-0 binding; Probable named identity',blocker='Cardinal direction labels and complete idle/walk state transitions not established')]
	for name in ('Alessa','Sofoubi','Relleck'):
		playable.append(dict(name=name,status='Named field resource identity unresolved',resources=[],confidence='Unsupported identity binding',
			blocker='No static chain from character name/ID to map actor graphics descriptor established; anonymous resources are not assigned by order or appearance'))
	groups=collections.defaultdict(list)
	for c in catalog:
		if c['graphics_file']:groups[c['graphics_file']].append(c['resource_id'])
	summary=dict(map_records=494,registered_actors=len(actors),graphics_descriptors=len(catalog),observed_palette_bindings=len(bindings),
		unbound_actor_registrations=len(unbound),status_counts=dict(collections.Counter(c['status'] for c in catalog)),
		native_pngs=sum(r['png'] is not None for r in metadata),frame_metadata_rows=len(metadata),playable_named_binding_complete=False,
		complete_animations=False,scope='Initial field map header resources and registered actor palettes; battle/player graphics separate and unextracted')
	for name,obj in [('resources.json',catalog),('frames.json',metadata),('animations.json',animations),('evidence.json',proof),('actors.json',actors),
		('unbound_actors.json',unbound),('playable_coverage.json',playable),('shared_graphics.json',dict(groups)),('summary.json',summary),
		('player_slot_resources.json',dict(resources=[f'R_{g:08X}' for g in player_resources],note='Actor slot 0 is a role, not proof that every map variant depicts the same named character')),
		('discovery_evidence.json',[dict(file=hx(p),bus=hx(p+BUS),size=n,sha256=sha(gba.take(en,p,n)),jp_english_equal=True) for p,n in sorted(set(discovery_spans))])]:write(name,(json.dumps(obj,indent=2)+'\n').encode())
	csv_new(output/'resources.csv',catalog);csv_new(output/'frames.csv',metadata);csv_new(output/'unsupported.csv',[c for c in catalog if c['status']!='supported scoped frames'])
	if sha((ROOT/'Tomato Adventure (Japan).gba').read_bytes())!=gba.JP_SHA or sha((ROOT/'Tomato Adventure (Japan) (patched).gba').read_bytes())!=gba.EN_SHA:raise ValueError('Input changed during extraction')
	return summary


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
	a=p.parse_args();print(json.dumps(export(a.output),indent=2))
