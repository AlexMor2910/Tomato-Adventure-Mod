"""Bounded renderer ownership model; reads ROMs, copies proven context PNGs.

No enemy tile streams are decompressed by this tool. It models the final OBJ
submission helper and classifies resource dependence without inventing semantic
standalone silhouettes. Historical v5 extraction is a frozen dependency.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/extract'))
import finalize_enemy_sprites_v5 as old
from thumb_inspect import inspect

BASE=ROOT/'reverse_engineering/exports/enemy_sprites_v5/final_verified'
OUT=ROOT/'reverse_engineering/exports/enemy_sprites_v6/final'
REPRESENTATIVES=('44','1B','33','60','B4')


def submit_obj_attributes(entries,tile_offset=0,x_offset=0,y_offset=0,palette_delta=0,priority=-1,mode=-1,capacity=128):
	"""Pure model of file 40468..40540 for non-affine descriptors.

	All entries are submitted in descriptor order; there is no actor argument or
	per-entry ownership filter. Mode changes attr0 bits 10..11, priority changes
	attr2 bits 10..11. Affine geometry is outside the validated profile.
	"""
	if priority not in (-1,0,1,2,3) or mode not in (-1,0,1,2,3) or not 0<=capacity<=128:
		raise ValueError('Unsupported submission parameters')
	result=[]
	for a,b,c in entries[:capacity]:
		if a&0x3F00 or a>>14==3:raise ValueError('Outside non-affine 4bpp descriptor profile')
		if mode!=-1:a=(a&0xF3FF)|(mode<<10)
		a=(a&0xFF00)|((a+y_offset)&255)
		b=(b&0xFE00)|(((b&511)+x_offset)&511)
		c=(c&0xFC00)|(((c&1023)+tile_offset)&1023)
		c=(c&0x0FFF)|(((((c>>12)+palette_delta)&15))<<12)
		if priority!=-1:c=(c&0xF3FF)|(priority<<10)
		result.append((a,b,c))
	return result


def resource_dependence(entries,parts):
	"""Map every source tile to uploaded blocks, not to semantic actor ownership."""
	result=[]
	for i,(a,b,c) in enumerate(entries):
		if a&0x3F00 or a>>14==3:raise ValueError('Outside static non-affine 4bpp profile')
		w,h=old.SIZES[a>>14][b>>14];tiles=[(c&1023)+y*32+x for y in range(h//8) for x in range(w//8)]
		resources=set()
		for tile in tiles:
			y,x=divmod(tile-512,32)
			if not 0<=y<8 or not 0<=x<12+6*parts:raise ValueError('References a tile outside established uploads')
			resources.add('base' if x<12 else f'part_{(x-12)//6}')
		x,y=b&511,a&255;x=x-512 if x>=256 else x;y=y-256 if y>=128 else y
		result.append(dict(index=i,attributes=[a,b,c],x=x,y=y,width=w,height=h,palette_bank=c>>12,priority=c>>10&3,
			hflip=bool(b&0x1000),vflip=bool(b&0x2000),affine=False,tiles=tiles,resources=sorted(resources)))
	return result


def profile(rom,participant):
	link=participant['links'][0];record=int(link['root_record_file'],16);desc=int(link['root_descriptor_file'],16)
	n=struct.unpack('<H',old.v1.take(rom,desc,2))[0]
	if not 0<n<=128:raise ValueError('Affine trailer/count outside supported profile')
	entries=list(struct.iter_unpack('<3H',old.v1.take(rom,desc+2,n*6)))
	parts=rom[record+0x2F]>>6
	objects=resource_dependence(entries,parts)
	anchor_x=(rom[record+0x2D]>>4)*8+(rom[record+0x2E]>>4)*4
	anchor_y=((rom[record+0x2D]&15)+(rom[record+0x2E]&15))*8
	actual=submit_obj_attributes(entries,x_offset=anchor_x,y_offset=anchor_y)
	return dict(child_id=participant['enemy_id'],root_id=f'{(record-old.v1.TABLE)//76:02X}',
		root_record_file=old.v1.hx(record),formation_file=link['descriptor_file'],slot=link['slot'],
		descriptor_file=old.v1.hx(desc),descriptor_bus=old.v1.hx(desc+old.v1.BUS),object_count=n,
		common_anchor=[anchor_x,anchor_y],tile_offset=0,palette_delta=0,priority_override=-1,mode_override=-1,
		state='Base profile, palette set 0, all actor-state selectors 0; not claimed initial/reachable in every encounter',
		objects=objects,submitted_attributes=actual,
		base_object_indices=[o['index'] for o in objects if 'base' in o['resources']],
		child_dependent_object_indices=[o['index'] for o in objects if f"part_{link['slot']}" in o['resources']],
		classification='Context-dependent shared-renderer participant; standalone silhouette partition unsupported',
		confidence='Confirmed default OBJ submission/resource dependence; semantic standalone ownership unproved')


def run(output):
	rom,jp=old.v3.load_roms()
	participants=json.loads((BASE/'participants.json').read_text())
	frames=json.loads((BASE/'frames.json').read_text())
	# Representatives are evaluated first; other IDs only after validating their
	# same helper path, descriptor shape and typed formation linkage.
	ordered=sorted(participants,key=lambda p:(p['enemy_id'] not in REPRESENTATIVES,p['enemy_id']))
	profiles=[]
	for p in ordered:
		for link in p['links']:
			for span in link['spans']:
				a,n=int(span['file'],16),span['size']
				if old.v1.take(rom,a,n)!=old.v1.take(jp,a,n) or old.v1.sha(old.v1.take(rom,a,n))!=span['sha256']:
					raise ValueError('Frozen v5 source span changed')
		profiles.append(profile(rom,p))
	profiles.sort(key=lambda p:p['child_id'])
	# Narrow code windows exclude literal pools. Known pools are represented by
	# resolved literals, not decoded as instructions.
	windows=[(0x40424,0x40542,'Final OBJ submission loop; no actor/subset filter'),
		(0x40542,0x405E6,'Optional affine trailer branch; absent in all selected root descriptors'),
		(0x4068E,0x406DA,'Global render state -> descriptor and uniform parameters'),
		(0x481BA,0x4822E,'Root common anchor and global render state initialization'),
		(0x4831C,0x48366,'Root palette/descriptor setup; Death Lilby child-state exception'),
		(0x4BEA4,0x4BED2,'Multipart root animation and OBJ table binding'),
		(0x4C3D8,0x4C41A,'Draw through global state; cycle dispatch'),
		(0x4C424,0x4C4FC,'Cycle advancement and per-actor-flag tile upload'),
		(0x41EF0,0x41F32,'Stream-supplied global descriptor replacement'),
		(0x41F40,0x41F6C,'Fixed alternate global descriptor/layout selection'),
		(0x41F88,0x41FB4,'Another fixed global descriptor/layout selection'),
		(0x41D10,0x41D56,'Script palette pointer/selector parsing and bank-0 write'),
		(0x41D64,0x41D74,'Palette bank-1 write'),(0x41D80,0x41D90,'Palette bank-2 write'),
		(0x41D9C,0x41DB4,'Palette bank-3 write and DMA'),
		(0x4C560,0x4C574,'Temporary actor palette source from alternate palette set')]
	code=[]
	for a,b,purpose in windows:
		if rom[a:b]!=jp[a:b]:raise ValueError('Native code differs between baselines')
		code.append(dict(file_range=[old.v1.hx(a),old.v1.hx(b)],bus_range=[old.v1.hx(a+old.v1.BUS),old.v1.hx(b+old.v1.BUS)],
			purpose=purpose,symbol='thumb_inspect.inspect',confidence='Confirmed static within bounded path',sha256=old.v1.sha(rom[a:b]),
			instructions=[dict(bus=old.v1.hx(i.address),bytes=i.raw.hex(),text=i.text) for i in inspect(rom,a,b)]))
	output.mkdir(parents=True,exist_ok=False)
	def write(path,data):
		with (output/path).open('xb') as f:f.write(data)
	write('.gitignore',b'*\n!.gitignore\n')
	composites=[]
	for child in REPRESENTATIVES:
		p=next(p for p in profiles if p['child_id']==child);root=p['root_id']
		folder=output/f'root_{root}_shared_composite';folder.mkdir()
		for row in (r for r in frames if r['enemy_id']==root):
			png=(BASE/row['png']).read_bytes()
			if old.v1.sha(png)!=row['png_sha256']:raise ValueError('Frozen context PNG mismatch')
			name=f"root_{root}_shared_composite/frame_{row['frame_index']:02d}.png";write(name,png)
			composites.append(dict(root_id=root,representative_child=child,frame=row['frame_index'],width=row['width'],height=row['height'],
				png=name,png_sha256=row['png_sha256'],source_png=row['png'],pixel_sha256=row['pixel_sha256'],
				kind='Root-level shared OBJ composite; not a standalone child sprite',state=p['state'],
				common_anchor=p['common_anchor'],descriptor_file=p['descriptor_file'],objects=p['objects'],prior_limits=row['notes']))
	coverage=json.loads((BASE/'coverage.json').read_text())
	byid={p['child_id']:p for p in profiles}
	for row in coverage:
		if row['enemy_id'] in byid:
			p=byid[row['enemy_id']]
			row.update(status='context-dependent composite participant; standalone unsupported',
				reason=f"Root {p['root_id']} submits all {p['object_count']} OBJ entries through one shared render state. Actor slot {p['slot']} selects part tile data, not a draw-entry subset. Global descriptor/palette replacement is possible; script reachability and semantic child crop unproved.")
	for name,obj in [('profiles.json',profiles),('composites.json',composites),('native_evidence.json',code),('coverage.json',coverage)]:
		write(name,(json.dumps(obj,indent=2)+'\n').encode())
	old.v1.csv_new(output/'coverage.csv',coverage)
	old.v1.csv_new(output/'remaining25.csv',[r for r in coverage if r['enemy_id'] in byid])
	summary=dict(records=182,existing_scoped_sprite_records=157,standalone_new=0,context_dependent_participants=25,
		representatives=list(REPRESENTATIVES),shared_composite_profiles=5,copied_native_composite_frames=len(composites),native_windows=len(code),
		prior_extraction_repeated=False,completed_extraction=False)
	write('summary.json',(json.dumps(summary,indent=2)+'\n').encode())
	return summary


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
	a=p.parse_args();print(json.dumps(run(a.output),indent=2))
