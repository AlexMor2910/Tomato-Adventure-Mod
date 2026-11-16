"""Local contact sheets for discovered slot-0 field resources; no identity guesses."""
import argparse
import json
from pathlib import Path
import struct
import zlib

import extract_field_sprites as ex


def read_png(path):
	data=path.read_bytes()
	if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
	p=8;parts=[];size=None
	while p<len(data):
		n=struct.unpack_from('>I',data,p)[0];tag=data[p+4:p+8];body=data[p+8:p+8+n]
		if zlib.crc32(tag+body)&0xFFFFFFFF!=struct.unpack_from('>I',data,p+8+n)[0]:raise ValueError('PNG CRC')
		if tag==b'IHDR':
			w,h,*fmt=struct.unpack('>2I5B',body)
			if fmt!=[8,6,0,0,0]:raise ValueError('Unsupported PNG format')
			size=w,h
		if tag==b'IDAT':parts.append(body)
		p+=12+n
	w,h=size;raw=zlib.decompress(b''.join(parts))
	if len(raw)!=(w*4+1)*h or any(raw[y*(w*4+1)] for y in range(h)):raise ValueError('Unsupported scanlines')
	return w,h,b''.join(raw[y*(w*4+1)+1:(y+1)*(w*4+1)] for y in range(h))


def export(output):
	frames=json.loads((ex.OUT/'frames.json').read_text());players=json.loads((ex.OUT/'player_slot_resources.json').read_text())['resources']
	output.mkdir(parents=True,exist_ok=False)
	(output/'.gitignore').write_text('*\n!.gitignore\n',encoding='utf-8')
	groups={r['variant_id']:[] for r in frames if r['resource_id'] in players and r['png']}
	for r in frames:
		if r['variant_id'] in groups and r['png']:groups[r['variant_id']].append(r)
	index=[]
	for vid,rows in sorted(groups.items()):
		rows=sorted(rows,key=lambda r:r['frame'])[:16]
		images=[read_png(ex.OUT/r['png']) for r in rows];cw=max(w for w,h,p in images)+4;ch=max(h for w,h,p in images)+4
		width=cw*4;height=ch*((len(images)+3)//4);canvas=bytearray(width*height*4);cells=[]
		for i,((w,h,pixels),row) in enumerate(zip(images,rows)):
			x=(i%4)*cw+2;y=(i//4)*ch+2
			for yy in range(h):canvas[((y+yy)*width+x)*4:((y+yy)*width+x+w)*4]=pixels[yy*w*4:(yy+1)*w*4]
			cells.append(dict(frame=row['frame'],source=row['png'],x=x,y=y,width=w,height=h))
		# Contact sheet is native pixels; preview is exactly 3x nearest neighbor.
		scaled=b''.join(b''.join(bytes(canvas[(y*width+x)*4:(y*width+x+1)*4])*3 for x in range(width))*3 for y in range(height))
		name=vid+'_sheet_3x.png'
		with (output/name).open('xb') as f:f.write(ex.gba.png(width*3,height*3,scaled))
		index.append(dict(variant_id=vid,png=name,scale=3,cells=cells,note='Resource/slot-role contact sheet; first 16 supported frames in numeric order, not an animation or named-character identification'))
	with (output/'sheets.json').open('x',encoding='utf-8') as f:json.dump(index,f,indent=2);f.write('\n')
	return len(index)


if __name__=='__main__':
	p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
	print(export(a.output),'local contact sheets')
