"""Read-only, evidence-gated enemy exporter. Regenerates pixels, never copies assets.

Retains the audited v1/v2/v3 modules as versioned dependencies. Their historical
CSV inventories gate supported classes; they supply no manually entered offsets.
Only baseline JP/English ROMs are accepted. No runtime animation claim is made.
"""
import argparse
import collections
import csv
import importlib.util
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('enemy_v3', ROOT/'tools/extract/enemy_sprites_v3/extract_enemy_sprites.py')
v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v3)
v2, v1 = v3.v2, v3.v1
DEFAULT = ROOT/'reverse_engineering/exports/enemy_sprites_v4/assets'


def decode(rom, eid):
	if not 0 <= eid < 182:
		raise ValueError('Enemy ID outside 00..B5')
	record = v1.TABLE + eid*v1.STRIDE
	if rom[record+0x34:record+0x44] == bytes(16):
		raise ValueError('Shared renderer participant; standalone palette/layout not established')
	if eid in v3.DISAGREEMENTS:
		frames = []
		all_spans = []
		for fi in range(2):
			d = v3.assemble(rom, eid, frame=fi)
			all_spans.extend(d['spans'])
			frames.append(dict(index=fi,pixels=d['pixels'],sources=d['sources'],oam=d['oam']))
		d.update(frames=frames,spans=sorted(set(all_spans)),kind='Multipart OBJ profile; BG differs',palette_bytes=128)
		return d
	try:
		d = v1.decode_record(rom,eid)
	except ValueError:
		return v2.new_record(rom,eid)
	spans = [(record+0x2F,1),(record+0x34,16),(v1.DIMS+d['size_index']*4,4),
		(d['palette'],32),(d['layout'],len(d['layout_bytes']))]
	for f in d['frames']:
		spans.append((f['source'],f['consumed']))
		f['sources'] = [dict(field=record+0x38+4*f['index'],source=f['source'],consumed=f['consumed'],
			format=f"0x{rom[f['source']]:02X}",decoded_sha256=v1.sha(f['data']),upload=[0,0,d['tw'],d['th']])]
	d.update(spans=spans,kind='Direct compact 4bpp canonical rectangle',palette_bytes=32)
	return d


def export(output, ids=None, previews=False):
	rom,jp = v3.load_roms()
	selected = list(range(182)) if ids is None else sorted(set(ids))
	if any(not 0 <= n < 182 for n in selected):
		raise ValueError('Enemy ID outside 00..B5')
	names = {int(r['enemy_id']):r['english_name'] for r in v2.rows(ROOT/'tools/extract/extracted_data/enemies_complete.csv')}
	assert set(names)==set(range(182))
	nulls = {int(e['enemy_id'],16):e for e in v3.null_classifications(rom)}
	output.mkdir(parents=True,exist_ok=False)
	def write(path,data):
		with (output/path).open('xb') as f:f.write(data)
	write('.gitignore',b'*\n!.gitignore\n')
	catalog,metadata,proofs,regression=[],[],[],[]
	for eid in selected:
		record=v1.TABLE+eid*v1.STRIDE
		row=dict(enemy_id=f'{eid:02X}',english_name=names[eid],record_file=v1.hx(record),record_bus=v1.hx(record+v1.BUS),
			status='unresolved',confidence='Unsupported',reason='',frame_count=None,graphics_resource=None,palette_resource=None)
		if eid in nulls:
			row.update(status='structurally understood but unsupported',reason=nulls[eid]['reason'])
			proofs.append(nulls[eid]);catalog.append(row);continue
		try:
			d=decode(rom,eid)
			for p,n in d['spans']:
				if v1.take(rom,p,n)!=v1.take(jp,p,n):raise ValueError('JP/English source span differs')
		except ValueError as error:
			row['reason']=str(error);catalog.append(row);continue
		folder=f'{eid:02X}_'+re.sub(r'[^A-Za-z0-9]+','_',names[eid]).strip('_')
		(output/folder).mkdir()
		resource=';'.join(','.join(v1.hx(s['source']) for s in f['sources']) for f in d['frames'])
		pal=v1.hx(d['palette'])+f":{d['palette_bytes']}"
		row.update(status='successfully decoded',confidence='Confirmed',frame_count=len(d['frames']),graphics_resource=resource,palette_resource=pal,
			reason='Base cycle only; palette set 0 and actor flags 0 for multipart; runtime reachability/effects excluded')
		if eid in v3.DISAGREEMENTS:row['reason']+='; OBJ profile only, BG differs'
		catalog.append(row)
		proofs.append(dict(enemy_id=row['enemy_id'],kind=d['kind'],spans=[dict(file=v1.hx(p),bus=v1.hx(p+v1.BUS),size=n,
			sha256=v1.sha(v1.take(rom,p,n)),jp_english_equal=True) for p,n in sorted(set(d['spans']))],
			oam=[f.get('oam') for f in d['frames']]))
		for f in d['frames']:
			w,h=d['tw']*8,d['th']*8
			path=f"{folder}/frame_{f['index']:02d}.png"
			image=v1.png(w,h,f['pixels']);write(path,image)
			if previews:write(path.replace('.png','_4x.png'),v1.png(w*4,h*4,v1.enlarge(f['pixels'],w,h)))
			old=ROOT/'reverse_engineering/exports/enemy_sprites_v3/final'/f"enemy_{eid:02X}_{'OBJ_state0_' if eid in v3.DISAGREEMENTS else ''}frame{f['index']}.png"
			if image!=old.read_bytes():raise ValueError('Historical PNG regression '+str(old))
			metadata.append(dict(enemy_id=row['enemy_id'],english_name=names[eid],record_file=row['record_file'],
				graphics_descriptor=v1.hx(record+0x38),palette_descriptor=v1.hx(record+0x34),palette_pointer=v1.hx(d['palette']+v1.BUS),
				layout_pointer=v1.hx(d['layout']+v1.BUS),tile_sources=[dict(s,file=v1.hx(s['source']),bus=v1.hx(s['source']+v1.BUS)) for s in f['sources']],
				compression=sorted({s['format'] for s in f['sources']}),width=w,height=h,frame_index=f['index'],frame_count=len(d['frames']),
				palette_resource=pal,graphics_resource=resource,png=path,pixel_sha256=v1.sha(f['pixels']),png_sha256=v1.sha(image),confidence='Confirmed',notes=row['reason']))
			if eid in (0xA5,0x9C):
				prefix='detector_A5' if eid==0xA5 else 'rattlin_dragon_9C'
				prior=ROOT/'reverse_engineering/exports/palace_enemy_sprites'/f"{prefix}_frame{f['index']}.png"
				assert image==prior.read_bytes()
				regression.append(dict(enemy_id=row['enemy_id'],frame=f['index'],pixel_sha256=v1.sha(f['pixels']),png_sha256=v1.sha(image),prior_png_byte_identical=True))
	groups=collections.defaultdict(list)
	for row in catalog:
		if row['graphics_resource'] is not None:groups[(row['graphics_resource'],row['palette_resource'])].append(row['enemy_id'])
	for group in groups.values():
		for row in catalog:
			if row['enemy_id'] in group[1:]:row.update(status='duplicate/shared resource of another decoded enemy',shared_with=group[0])
	# Normalize CSV keys; JSON retains nulls and structured source lists.
	for row in catalog:row.setdefault('shared_with',None)
	v1.csv_new(output/'coverage.csv',catalog)
	v1.csv_new(output/'unresolved.csv',[r for r in catalog if r['graphics_resource'] is None])
	counts=dict(collections.Counter(r['status'] for r in catalog))
	for status in ('successfully decoded','duplicate/shared resource of another decoded enemy','structurally understood but unsupported','unresolved'):counts.setdefault(status,0)
	summary=dict(records=len(catalog),counts=counts,decoded_records=sum(r['graphics_resource'] is not None for r in catalog),native_frames=len(metadata),
		unique_graphics_and_palette_resources=len(groups),scope='Bounded base cycles; not complete battle animations',fixture_regressions=regression)
	for path,data in [('frames.json',metadata),('coverage.json',catalog),('evidence.json',proofs),('summary.json',summary),
		('shared_resources.json',dict(graphics_palette_groups=list(groups.values()),palette_groups=dict((p,[r['enemy_id'] for r in catalog if r['palette_resource']==p]) for p in sorted({r['palette_resource'] for r in catalog if r['palette_resource']})),
		duplicate_names={name:[r['enemy_id'] for r in catalog if r['english_name']==name] for name in sorted(set(names.values())) if sum(r['english_name']==name for r in catalog)>1}))]:
		write(path,(json.dumps(data,indent=2)+'\n').encode())
	assert v1.sha((ROOT/'Tomato Adventure (Japan) (patched).gba').read_bytes())==v1.EN_SHA
	assert v1.sha((ROOT/'Tomato Adventure (Japan).gba').read_bytes())==v1.JP_SHA
	return summary


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__)
	p.add_argument('--output',type=Path,required=True)
	p.add_argument('--enemy',action='append',type=lambda s:int(s,16),help='Hex enemy ID, repeatable; omitted means all 182')
	p.add_argument('--previews',action='store_true')
	a=p.parse_args();print(json.dumps(export(a.output,a.enemy,a.previews),indent=2))
