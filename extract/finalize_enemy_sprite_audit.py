"""Recheck inherited static evidence, write new report, then audit protected files."""
import hashlib
import json
from pathlib import Path
import extract_enemy_sprites as ex

ROOT=ex.ROOT
OUT=ROOT/'reverse_engineering/exports/enemy_sprites_v4'


def main():
	rom,jp=ex.v3.load_roms()
	before=json.loads((OUT/'protected_before.json').read_text())
	static=json.loads((ROOT/'reverse_engineering/exports/enemy_sprites_v2/bounded_evidence_final.json').read_text())
	code=[]
	for w in static['code_windows']:
		a,b=int(w['start_file'],16),int(w['end_file_exclusive'],16)
		assert ex.v1.sha(rom[a:b])==w['sha256'] and rom[a:b]==jp[a:b]
		code.append(dict(w,confidence='Confirmed',purpose='Inherited bounded loader/initializer/OBJ/animation evidence, rehashed against both baselines'))
	old=json.loads((ROOT/'reverse_engineering/exports/enemy_sprites_v3/final/evidence.json').read_text())
	new=ex.v3.build_evidence(rom,jp)
	assert old==new
	summary=json.loads((OUT/'final/summary.json').read_text())
	coverage=json.loads((OUT/'final/coverage.json').read_text())
	frames=json.loads((OUT/'final/frames.json').read_text())
	unsupported=[r for r in coverage if r['graphics_resource'] is None]
	ledger=[
		('00634F50','00638558','v1.TABLE/STRIDE; toolkit text.cpp:EnemyInfoAddress','182 records, stride 4C; enemy ID selects record','Existing enemy mapping; extraction enumerates all records'),
		('00486548','00486560','v1.DIMS; v1.decode_record','Six upload width/height u16 pairs in tiles','Loader 0804C610..61A and 0804C674..684'),
		('00040014','00040064','extract_field_maps.decompress','Compression dispatch: 10 LZ77, 30 RLE','Inherited dispatcher evidence; strict stream sizes'),
		('0003FFA0','0004000A','v2.upload','Compact 4bpp rows uploaded to 32-tile VRAM pitch','Inherited native row-copy trace'),
		('0004C400','0004C4FC','v2.new_record; v3.assemble','Multipart two/four frame cycle and part state selector','Native XOR 1 or increment/reset 4; flag 0800 selects part state'),
		('0004C83C','0004C9DA','v2.new_record; v3.assemble','Multipart pointer graph and upload/palette loader','Rehashed bounded instruction window; exact decoded byte lengths'),
		('00040632','00040720','v2.object_render/layout_render','Animation descriptor selection and OBJ/BG dispatch','Rehashed bounded windows and parsed scripts/descriptors'),
		('004559B4','00456C00','v3.null_classifications','Formation descriptors stride 28; typed root/child links','Recomputed v3 evidence identical; participant slots and root tables validated'),
		('005D2BA8',None,'v3.strict_rle_ledger','Chekkit rejected stream','Advertises 3072 bytes; final complete token reaches 3200; exact consumed end in evidence')]
	addresses=[dict(file_start='0x'+a,file_end_exclusive='0x'+b if b else None,bus_start=ex.v1.hx(int(a,16)+ex.v1.BUS),
		bus_end_exclusive=ex.v1.hx(int(b,16)+ex.v1.BUS) if b else None,symbol=s,purpose=p,evidence=e,confidence='Confirmed' if b else 'Candidate') for a,b,s,p,e in ledger]
	evidence=dict(summary=summary,roms=dict(english_sha256=ex.v1.EN_SHA,japanese_sha256=ex.v1.JP_SHA),
		addresses=addresses,native_windows=code,inherited_v3_recomputed_equal=True,v3_evidence=new,
		metadata='exports/enemy_sprites_v4/final/frames.json',coverage=coverage,
		limitations=['Only palette set 0 and actor state 0 exported for multipart owners','Six OBJ-only profiles have different BG representations',
		'No whole-sprite aliases inferred for child actors','No BIOS boundary clipping enabled','No encounter reachability or full attack-animation reconstruction'],
		source_paths=[dict(path=p,sha256=ex.v1.sha((ROOT/p).read_bytes())) for p in [
		'tools/extract/extract_enemy_sprites.py','tools/extract/enemy_sprites_v1/extract_enemy_sprites.py',
		'tools/extract/enemy_sprites_v2/extract_enemy_sprites.py','tools/extract/enemy_sprites_v3/extract_enemy_sprites.py',
		'tools/extract/extract_field_maps.py','tools/analyze/extract_palace_enemy_sprites.py']])
	with (ROOT/'reverse_engineering/enemy_sprite_extraction_evidence.json').open('x',encoding='utf-8') as f:json.dump(evidence,f,indent=2);f.write('\n')
	lines=['# Enemy sprite extraction: audited v4 pipeline','',
		'2026-10-27. Read-only static extraction. Current workspace v1/v2/v3 artifacts supersede the older handoff. No ROM, save, savestate, gameplay, emulator, or Ghidra operation was performed. No assets were published or committed.','',
		'## Result','',
		'All 182 records accounted for: **123 successfully decoded distinct resources, 33 duplicate/shared resources, 25 structurally understood but unsupported standalone actors, 1 unresolved (Chekkit 8C)**. Thus 156 records have 326 native RGBA frames and 326 nearest-neighbor previews. This is bounded base-cycle coverage, not complete animation coverage.','',
		'Canonical output: `exports/enemy_sprites_v4/final/`. `frames.json` contains source pointers, compression, dimensions, frame count, resource identities, confidence and pixel/PNG hashes; `coverage.csv`/`coverage.json` enumerate all records. `unresolved.csv` is the exact unsupported list. `shared_resources.json` groups graphics+palette identities, palettes alone and duplicate names. The intermediate `assets/` run is retained; final additionally records both frame source spans for the six OBJ-only cases. Pixels are identical.','',
		'## Architecture and evidence','',
		'ROM bus = file offset + 08000000. The following ranges are file offsets with exclusive ends, unchanged between the fingerprinted Japanese and English baseline ROMs. English names use enemies_complete.csv; translated names are not interpreted as original inline name bytes. Every consumed graphics span is compared across baselines. Per-asset addresses are in final/evidence.json and frames.json; native instruction bytes and hashes are in enemy_sprite_extraction_evidence.json. Findings below are inherited static interpretations, rechecked by fresh decoding, source equality and bounded-window hashes.','',
		'| File range | Symbol / purpose | Evidence | Confidence |','|---|---|---|---|']
	for a in addresses:lines.append(f"| {a['file_start']}..{a['file_end_exclusive'] or 'see stream ledger'} | {a['symbol']}: {a['purpose']} | {a['evidence']} | {a['confidence']} |")
	lines += ['',
		'Enemy ID selects record `00634F50 + ID*4C`. Ordinary record +2F selects one of six upload dimensions: (5,5), (7,7), (10,5), (10,5), (12,5), (10,5) tiles. +34 is a direct 32-byte palette; +38/+3C are two compressed base-frame pointers; +40 is a BG tilemap; +44 and +48 lead to OBJ descriptor and animation tables. Ordinary tables have an extra indirection, implemented in v2.object_render. Upload dimensions can differ from displayed bounds: Pothead 17 uploads 80x40 but composes to 40x80; Brikkypress 9A composes to 48x72. No dimensions are inferred from nontransparent pixels.','',
		'Multipart record +2F top two bits count parts (implemented: 2 or 3); bits 4..5 select a two-frame or four-frame cycle (implemented modes 0/1). +2E high/low nibbles specify canvas tile dimensions. +34 -> palette-set table[0] -> 128 bytes, four banks 6..9. +38 -> base frame table (12x8 tiles per stream). +3C -> actor-state table[0] -> per-part table -> frame table (6x8 tiles per stream). Parts upload at x=12+6*i into the same 32-tile-pitch atlas. These streams replace compact reusable tile regions; no delta format has been established.','',
		'OBJ descriptors contain u16 count then count six-byte GBA attr0/attr1/attr2 entries. Shape/size bits choose hardware rectangles; signed coordinates, H/V flips, palette bank and 2D tile pitch determine composition. Lower OAM index wins at equal priority. The decoder rejects affine, mosaic, alternate depth/mode, mixed priority and unsupported bounds. Animation script entries are six bytes (descriptor index, duration, FFFF terminator); supported base loops select descriptor 0. This does not enumerate arbitrary effect scripts.','',
		'All accepted tiles are 8x8 4bpp, 32 bytes, low nibble then high nibble, compact row-major uploads. BG halfwords encode tile index, H/V flips and palette bank. Raw GBA BGR555 palettes use red bits 0..4, green 5..9, blue 10..14, expanded by (v<<3)|(v>>2); index 0 in each bank is transparent. RGB under transparency is retained for legacy direct-frame regression. No 8bpp enemy format is established.','',
		'Compression uses the existing strict field-map decoder for BIOS-style 10 LZ77 and 30 RLE. Direct accepted streams use LZ77; multipart streams use RLE. Overlapping LZ references are supported. Advertised size, exact output length and all pointers are bounded. Toolkit lz77.cpp, rle.cpp, tiles.cpp and images.cpp were inspected: rle.cpp clips output and has an apparent `< 16` size-expression typo; neither behavior was copied into the strict decoder.','',
		'## Special cases and sharing','',
		'Six roots 1D, 2E, 43, 45, 47, 49 export only the established OBJ profile (descriptor 0, palette set 0, actor flags 0). BG output differs; it is not substituted or declared equivalent. Mirrolick has an additional initializer layout at bus 085EA4F4 whose role remains outside this render profile. The 25 null-graphics records have typed formation links to root-owned multipart resources, recomputed from formation descriptor slots. They are renderer participants, not proven invisible/script-only actors and not whole-image duplicates. No standalone PNG is assigned to them.','',
		'33 records share the same ordered frame stream pointers and palette pointer/size with an earlier decoded record. All still receive ID-specific exports. Equal names alone never establish identity: resource and duplicate-name groups are separate in shared_resources.json. Other palette/actor states and alternate encounter forms are not exhaustively enumerated. Seven accepted owners have four base frames (1A,31,4B,5F,75,B0,B3); other accepted records have two.','',
		'## Exact unsupported / unresolved records','',
		'| ID | English name | Status / reason |','|---|---|---|']
	for r in unsupported:lines.append(f"| {r['enemy_id']} | {r['english_name']} | {r['status']}: {r['reason']} |")
	lines += ['',
		'For 8C the smallest blocker is the BIOS SWI 14 boundary semantics: the final token of stream file 005D2BA8 exceeds the 3072-byte header by 128 bytes. No clipping, padding exemption, guessed frame or partial cycle is exported. For the 25 participants the missing proof is an independently meaningful per-record palette/layout and crop; formation linkage alone supports root-renderer participation.','',
		'## Validation and reproduction','',
		'`python -B tools/extract/extract_enemy_sprites.py --output NEW_DIRECTORY --previews` regenerates the whole database. Add `--enemy A5` (repeatable hex ID) for selection. Existing output directories are rejected; files are created exclusively. Versioned v1/v2/v3 modules and their historical CSV support inventories are retained dependencies. No manually entered per-enemy offsets are introduced; six documented OBJ-only IDs select a scoped renderer exception. This is evidence-gated support, not a universal decoder promise.','',
		'Run `python -B tools/extract/test_extract_enemy_sprites.py`. Final captured results are in exports/enemy_sprites_v4/test_results.json: 8 new tests, 7 v1 tests, 8 v2 tests, 9 field-map tests pass (32 total). Checks cover strict compression, nibble/palette decoding, all regenerated pixel hashes and source spans, resource sharing, ordinary/large/noncanonical/four-frame/multipart examples, malformed/rejected inputs and overwrite refusal. A new test initially expected Watchman Kid at 40x40; the verified dimension selector gives 56x56 and the test was corrected.','',
		'All 326 generated native PNGs match prior v3 PNGs byte-for-byte. Detector A5 and Rattlin\' Dragon 9C additionally match all eight original native/4x palace PNGs and all four decompressed tile hashes. Pixel and PNG SHA-256 regression values are in final/summary.json and structured evidence. Native windows (20) rehash identically against both baseline ROMs, and the complete v3 evidence rebuild equals the preserved JSON. No new runtime or screenshot validation is claimed.','',
		'## Integrity and provenance','',
		'Before the first write, all 6,395 pre-existing workspace files in the established scope were SHA-256 hashed with zero read errors. Scope excludes .git, installed Ghidra, Python caches and generated api-classes/compile-libs directories. The final audit in exports/enemy_sprites_v4/integrity.json rehashes every protected path and checks missing files. Original ROMs, translated/cumulative ROMs, saves, earlier exports, reports and scripts are protected. New asset directories have local ignore files. No protected file was opened for writing.','',
		'## Next category','',
		'Recommend NPCs/player characters: the verified OBJ descriptor/animation helper and 4bpp atlas composition offer reusable primitives. First establish their actor-to-resource pointer chains; enemy-specific field layouts do not transfer automatically. That category was not started.','']
	with (ROOT/'reverse_engineering/enemy_sprite_extraction.md').open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
	changed=[];missing=[]
	for relative,expected in before['hashes'].items():
		try:
			with (ROOT/relative).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
		except FileNotFoundError:missing.append(relative);continue
		if actual!=expected:changed.append(relative)
	result=dict(protected_count=len(before['hashes']),scope=before['scope'],baseline_errors=before['errors'],changed=changed,missing=missing,
		passed=not(changed or missing),rom_writes=0,emulator_operations=0,native_windows_verified=len(code),v3_evidence_recomputed_equal=True)
	with (OUT/'integrity.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
	print(json.dumps(result,indent=2))
	if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
