"""Bounded evidence inventory: only v1's 55 unresolved enemy records."""
import collections
import json
import struct

import extract_enemy_sprites as ex


def main():
	rom = (ex.ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	jp = (ex.ROOT / 'Tomato Adventure (Japan).gba').read_bytes()
	assert ex.v1.sha(rom) == ex.v1.EN_SHA and ex.v1.sha(jp) == ex.v1.JP_SHA
	result = []
	for eid in sorted(ex.TARGETS):
		p = ex.TABLE + eid * ex.STRIDE
		raw = ex.v1.take(rom,p,ex.STRIDE)
		entry = dict(enemy_id=f'0x{eid:02X}', record_file=ex.v1.hx(p), graphics_fields_hex=raw[0x2D:0x30].hex(),
			pointers={f'+{off:02X}':ex.v1.hx(struct.unpack_from('<I',raw,off)[0]) for off in range(0x34,0x4C,4)})
		try:
			d = ex.new_record(rom,eid)
			entry.update(confidence='Confirmed',dimensions_tiles=[d['tw'],d['th']],mapping=d['kind'],frame_count=len(d['frames']))
		except ValueError as error:
			entry.update(confidence='Unconfirmed',blocker=str(error))
		if raw[0x2F] >= 6 and raw[0x34:0x44] != bytes(16):
			# Trace the exact candidate pointer graph without exporting candidate art.
			spans = []
			parts, mode = raw[0x2F] >> 6, raw[0x2F] >> 4 & 3
			palette_table = ex.ptr(rom,p+0x34,spans)
			base = ex.ptr(rom,p+0x38,spans)
			states = ex.ptr(rom,p+0x3C,spans)
			candidate = dict(confidence='Candidate' if entry['confidence']!='Confirmed' else 'Confirmed',
				canvas_tiles=[raw[0x2E]>>4,raw[0x2E]&15],frame_mode=mode,
				cycle_length=2 if mode==0 else 4,parts=parts,
				palette_table_file=ex.v1.hx(palette_table),palette_set0_file=ex.v1.hx(ex.ptr(rom,palette_table,spans)),
				base_table_file=ex.v1.hx(base),part_state_table_file=ex.v1.hx(states),streams=[])
			candidate['base_streams']=[]
			for fi in range(candidate['cycle_length']):
				source=ex.ptr(rom,base+4*fi,spans)
				s=dict(frame_index=fi,field_file=ex.v1.hx(base+4*fi),source_file=ex.v1.hx(source),header=rom[source:source+4].hex())
				try:
					data,consumed=ex.v1.decompress(rom,source,3072)
					if len(data)!=3072:raise ValueError('Not a 12x8 upload')
					s.update(decoded_size=len(data),consumed=consumed,sha256=ex.v1.sha(data))
				except ValueError as error:s['blocker']=str(error)
				candidate['base_streams'].append(s)
			for state in range(2):
				pt = ex.ptr(rom,states+state*4,spans)
				for part in range(parts):
					ft = ex.ptr(rom,pt+part*4,spans)
					for fi in range(candidate['cycle_length']):
						field = ft + fi*4
						source = ex.ptr(rom,field,spans)
						s = dict(actor_flag_state=state,part_index=part,frame_index=fi,field_file=ex.v1.hx(field),source_file=ex.v1.hx(source),header=rom[source:source+4].hex())
						try:
							data,consumed=ex.v1.decompress(rom,source,1536)
							if len(data)!=1536:raise ValueError('Not a 6x8 upload')
							s.update(decoded_size=len(data),consumed=consumed,sha256=ex.v1.sha(data))
						except ValueError as error:s['blocker']=str(error)
						candidate['streams'].append(s)
			entry['multipart_graph']=candidate
		result.append(entry)
	# Only the loader, its directly referenced initializer/animation/draw helpers,
	# and literal tables relevant to these records. No whole-ROM disassembly.
	windows=[(0x480E0,0x48100),(0x481BA,0x48230),(0x48234,0x48270),(0x4831C,0x483A0),
		(0x4BE04,0x4BE20),(0x4BE2C,0x4BE82),(0x4BE90,0x4BED2),(0x4BEE4,0x4BEFC),(0x4BF04,0x4BF0C),
		(0x4C0C2,0x4C0F6),(0x4C3D8,0x4C41A),(0x4C424,0x4C4FC),
		(0x4C600,0x4C61C),(0x4C674,0x4C73E),(0x4C83C,0x4C9DA),
		(0x40632,0x4067C),(0x406AE,0x406DA),(0x406DA,0x40720),
		(0x401C4,0x402A0),(0x402A8,0x4035E)]
	code=[]
	for start,end in windows:
		p=start; instructions=[]
		while p<end:
			i=ex.decode(rom,p)
			instructions.append(dict(bus=ex.v1.hx(i.address),raw=i.raw.hex(),text=i.text))
			p+=i.size
		code.append(dict(start_file=ex.v1.hx(start),end_file_exclusive=ex.v1.hx(end),sha256=ex.v1.sha(rom[start:end]),jp_english_equal=rom[start:end]==jp[start:end],instructions=instructions))
	with (ex.OUT/'bounded_evidence_final.json').open('x',encoding='utf-8') as stream:
		json.dump(dict(enemies=result,code_windows=code,rom_sha256=ex.v1.EN_SHA,jp_sha256=ex.v1.JP_SHA),stream,indent=2)
	print('55 record inventories; bounded code windows:',len(code))


if __name__=='__main__':main()
