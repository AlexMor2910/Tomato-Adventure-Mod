"""Write a versioned bounded-static report and audit every protected input."""
import hashlib
import json
import os
from pathlib import Path

import finalize_enemy_sprites_v5 as ex
from thumb_inspect import inspect

ROOT=ex.ROOT
SESSION=ROOT/'reverse_engineering/exports/enemy_sprites_v5'
REPORT=ROOT/'reverse_engineering/enemy_sprite_finalization_v5.md'
EVIDENCE=ROOT/'reverse_engineering/enemy_sprite_finalization_v5_evidence.json'


def new_json(path,obj):
	with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


def main():
	rom,jp=ex.v3.load_roms()
	participants=json.loads((ex.OUT/'participants.json').read_text())
	frames=json.loads((ex.OUT/'frames.json').read_text())
	chekkit=json.loads((ex.OUT/'chekkit_evidence.json').read_text())
	summary=json.loads((ex.OUT/'summary.json').read_text())
	tests=json.loads((SESSION/'test_results.json').read_text())
	assert all(r['value']['exit_code']==0 for r in tests['results'])
	# Code intervals contain instructions only. Literal pools are excluded and
	# resolved literal words are retained separately by the existing inspector.
	windows=[(0x48196,0x4822E,'Multipart target bounds versus global renderer bounds'),
		(0x4831C,0x483AC,'Root palette/descriptor ownership and special initial child flags'),
		(0x4BDD0,0x4BDE6,'Formation bit 40 selects one multipart setup'),
		(0x4BDEC,0x4BE04,'Ordinary branch loops three separate actors'),
		(0x4BEA4,0x4BED2,'Multipart branch initializes global render state at target base+C4'),
		(0x4BEE4,0x4BEFC,'Global BG descriptor pointers'),
		(0x4BF04,0x4BF0C,'Global optional descriptor cleared'),
		(0x4C3D8,0x4C41A,'Animation draw call uses global 03000B04'),
		(0x4C424,0x4C4FC,'Two/four cycle, root frames and actor flag-selected component uploads'),
		(0x4C88A,0x4C9DC,'Root palette banks and 12x8/6x8 OBJ upload configuration'),
		(0x4068E,0x406DA,'Descriptor selected once, full OBJ descriptor passed to draw'),
		(0x3FFA0,0x4000E,'Compact source rows and explicit upload dimensions'),
		(0x40014,0x4006C,'Header size >>8, scratch allocation, SWI dispatch, upload, free'),
		(0x942FC,0x94300,'RLE WRAM SWI 14 wrapper'),
		(0x2CBDA,0x2CBF8,'Scratch allocator rounds requested bytes to words')]
	code=[]
	for a,b,purpose in windows:
		assert rom[a:b]==jp[a:b]
		code.append(dict(file_range_exclusive=[ex.v1.hx(a),ex.v1.hx(b)],bus_range_exclusive=[ex.v1.hx(a+ex.v1.BUS),ex.v1.hx(b+ex.v1.BUS)],
			purpose=purpose,symbol='thumb_inspect.inspect',confidence='Confirmed static instructions; interpretation limited to described path',
			sha256=ex.v1.sha(rom[a:b]),jp_english_equal=True,
			instructions=[dict(bus=ex.v1.hx(i.address),bytes=i.raw.hex(),text=i.text,literal_bus=i.literal_address,literal_value=i.literal_value) for i in inspect(rom,a,b)]))
	evidence=dict(summary=summary,roms=dict(japanese_sha256=ex.v1.JP_SHA,english_sha256=ex.v1.EN_SHA),
		address_convention='Bus = file + 08000000; relevant spans equal at same offsets in original Japanese and English baselines; name bytes excluded',
		participants=participants,chekkit=chekkit,native_windows=code,
		external_references=[dict(url='https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/bios.c#L783',
			kind='Primary emulator implementation inspected as source only',finding='The _unRl inner loops stop at remaining == 0; prefix is 3072 bytes',
			confidence='Confirmed source behavior, not original hardware proof'),
			dict(url='https://github.com/Cult-of-GBA/BIOS/blob/master/bios_calls/decompression/running_length.s#L40',
			kind='Primary BIOS implementation source inspected, assembly rather than pseudocode',
			finding='Assembly finishes each token before checking remaining length; same first 3072 bytes, 128 excess zeros for this stream',
			confidence='Corroborating implementation, not a supplied original BIOS fingerprint/disassembly')],
		boundary_conclusion='Original BIOS exact end/write side effects remain unverified. Only the common native-uploaded prefix is reconstructed; no ROM/header correction.',
		changed_existing_files=[],new_code=['tools/extract/finalize_enemy_sprites_v5.py','tools/extract/test_finalize_enemy_sprites_v5.py','tools/extract/audit_enemy_sprites_v5.py'],
		new_code_hashes={p:ex.v1.sha((ROOT/p).read_bytes()) for p in ['tools/extract/finalize_enemy_sprites_v5.py','tools/extract/test_finalize_enemy_sprites_v5.py','tools/extract/audit_enemy_sprites_v5.py']})
	new_json(EVIDENCE,evidence)
	lines=['# Enemy sprite finalization v5','',
		'2026-10-27. Bounded static follow-up to v4, restricted to the 25 multipart participants and Chekkit. No gameplay, NPC/player extraction, ROM writes, save/state writes, emulator execution, whole-ROM scanning or Ghidra analysis. All earlier files remain protected.','',
		'## Result and limits','',
		'**Newly supported: 8C Chekkit, four transparent 80x80 OBJ frames and four 4x previews.** The prior 156-record extraction was not rerun: all 652 existing PNGs (326 native plus previews) were copied byte-for-byte, and all 326 old frame metadata entries were retained exactly. Existing regression tests were rerun as validation.','',
		'Across all 182 records: **124 distinct decoded resources + 33 shared decoded records = 157 records with scoped base-frame output; 25 standalone reconstructions remain unsupported.** There are 330 native frames and 330 previews. Zero records remain without an evidence-backed classification; this does **not** mean all 182 are extracted. Chekkit is an OBJ-only render projection with actor flags 0, palette set 0, descriptor 0; animation effects, other palettes/states and runtime memory side effects are excluded.','',
		'Canonical output is `exports/enemy_sprites_v5/final_verified/`. The retained first run `final/` has identical PNGs but less complete participant pointer-span accounting. Use final_verified for metadata. `coverage.csv/json` accounts for all 182 records; `frames.json` retains earlier metadata and appends Chekkit; `participants.json` inventories all 25 unsupported cases; `chekkit_evidence.json` records every used span, token accounting, descriptor and output discrepancy.','',
		'## Multipart findings','',
		'ROM/file addresses below apply to both Japanese and English baselines. Bus = file + 08000000. Each per-record palette/table/stream/descriptor range, purpose-bearing field, source hash and JP/English equality is in participants.json. Original inline name bytes +0..7 differ and are excluded. All 25 participants have zero own graphics fields +34..4B, including +44 OBJ and +48 animation pointers. Their resource selection is through typed formation slots and the root record; no per-enemy offsets were guessed.','',
		'At bus 0804BDD0..0804BDE6 formation header bit 40 chooses multipart setup 0804BEA4, whereas the ordinary branch loops separate actors. Multipart setup places root +48 into global render state at target-base+C4 (03000B04); the root palette table initializes 0300091C and root +44 initializes 0300092C at 0804831C..0804833A. The generic draw helper receives that one root descriptor, not a descriptor assigned independently to the null-pointer child.','',
		'Root +3C -> state table[(target[slot].flags & 0800) != 0] -> part table[slot] -> frame table[cycle]. The loader at 0804C952..0804C99E reads each actor flag, increments target address by 38 and uploads a 6x8 block at x=12+6*slot, y=0 in a 32-tile-pitch atlas. The root base block is 12x8 at x=0, and part 0 belongs to root actor slot 0. Root +34 -> palette set 0 supplies four raw BGR555 banks 6..9. OBJ entries select the actual bank; bank identity is not necessarily component identity.','',
		'All 25 inventories now enumerate both actor states, their 164 compressed frame-stream references, 77 referencing OBJ entries, exact signed coordinates, shape/size, flips, priority, tiles, palette addresses, and component-reference bounds. Coordinates below are root descriptor coordinates before normalization. They describe a resource layer in the global sprite and do not establish a complete standalone child silhouette. All these OBJ rectangles reference tiles wholly within the indicated component; this proves their resource dependency, not that the component contains every pixel belonging semantically to that child.','',
		'In particular 1B uses banks 7/8, 33 uses 6/7/9, 4C uses 7/8, and arm/Binky cases also use mixed banks. Splitting by palette bank would omit valid component pixels. Conversely, splitting by uploaded block could omit constant child artwork stored in the base or another block; the traced draw path provides no child-to-descriptor-subset assignment. Formation target bounds at 08048196..0804822C are separate from the root OBJ canvas and are not a documented image crop.','',
		'The six established OBJ-only roots 1D,2E,43,45,47,49 were bounded references for descriptor format and global ownership. Their PNGs were preserved; no accepted sprite was corrected or re-extracted. Death Lilby 5F has initializer-specific child flag bits at 08048348..08048364, so enumerated state-0 resources are not claimed to be every encounter\'s initial state.','',
		'### Exact unsupported record inventory','',
		'Common remaining blocker for every row: a complete child silhouette and any base/other-block contribution lack a proved child-specific draw/crop rule. Own graphics/OBJ/animation pointers are all zero. No guessed standalone PNG or root-image alias is emitted. Detailed OBJ attributes and all frame pointers are in participants.json.','',
		'| ID | Root / part | Upload tile x | Base cycle | OBJ indices | Banks | Referencing-object bounds (left,top,right,bottom) |','|---|---|---|---:|---|---|---|']
	for p in participants:
		for l in p['links']:
			lines.append(f"| {p['enemy_id']} | {l['root_enemy_id']} / {l['slot']} | {12+6*l['slot']}..{17+6*l['slot']} | {l['base_cycle_frames']} | {','.join(str(o['index']) for o in l['objects'])} | {l['palette_banks_used']} | {l['component_object_bounds']} |")
	lines += ['',
		'## Chekkit: format and justified upload projection','',
		'Chekkit root record: file 006378E0, bus 086378E0. Its four-frame base table starts at file 00634D8C; frame-2 pointer field 00634D94 selects 005D2BA8. The source header is 30 00 0C 00: RLE type 30, declared length 000C00 = 3072. The game reads the 32-bit word then shifts right by 8 at 0804001A..0804001E, so there is no alternate size interpretation in this path. The scratch allocation uses that size, rounded to words; 3072 is already aligned. RLE dispatch calls bus 080942FC -> SWI 14 at 08040042..08040046.','',
		'The stream contains 96 tokens, consumes 654 bytes, and ends at file 005D2E36, before the next stream at 005D2E38. Its last token at 005D2E34 is FE 00: (FE & 7F)+3 = 129 zero bytes. It begins after output byte count 3071 and thus reaches 3200 bytes, 128 past the header length. The reason for the authoring anomaly is unknown; no claim of intentional padding or a corrected header is made. Full-token source SHA-256 is 0a45e52441dcf0e84a0aabbf1bdf96fc6748572a5b18cdc03942dcc36d17caf2.','',
		'Boundary references were inspected as source only. mGBA 0.10.5 `_unRl` stops an inner run at the remaining advertised byte count; it yields 3072 bytes here. This is emulator implementation evidence, not original-hardware proof. [Source](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/bios.c#L783).','',
		'The Cult-of-GBA BIOS assembly finishes a run before checking remaining length, yielding 3200 bytes for this stream. Its assembly, rather than inconsistent pseudocode comments, was inspected. It is corroborating implementation evidence; no supplied original BIOS fingerprint was analyzed. [Source](https://github.com/Cult-of-GBA/BIOS/blob/master/bios_calls/decompression/running_length.s#L40).','',
		'Both policies write the same first 3072 bytes. Crucially, the ROM independently configures a 12x8-tile upload with source coordinates (0,0) at 0804C900..0804C926. Row-copy routine 0803FFA0..0804000E reads eight source rows of 12*32=384 bytes and no later data: exactly source [0,3072). Destination pitch is 1024 bytes. Thus the image upload is invariant to the extra 128 bytes. Exact original BIOS overflow effects outside the upload remain unsupported; no runtime memory-safety or successful encounter execution is asserted.','',
		'New `exception_projection` is gated to this exact source, hash, pointer field and 3072-byte upload. It records the original header unchanged, obtains complete-token length from the existing ledger, and replays all tokens through the existing strict decoder using a temporary analysis-only length view. It records the 3200-byte replay hash and excess zeros, then explicitly selects the native upload range. This is an extraction projection, not a repaired stream or a relaxed general decoder. The existing field-map/strict RLE decoder remains unchanged and still rejects this stream.','',
		'All four Chekkit frames compose through 27 native non-affine 4bpp OBJ entries on an 80x80 canvas. BG and OBJ visible pixels agree for frames 0,1,3; frame 2 differs by 10 pixels. The four exported PNGs consistently use the OBJ path, following the earlier scoped OBJ-only precedent. That discrepancy remains explicit and is not fixed by selecting a more plausible picture. The enlarged frame-2 export was visually inspected as a secondary check; identity and composition rest on pointer/descriptor evidence.','',
		'## Bounded native evidence ledger','',
		'Each interval below is file [start,end), with instruction bytes, resolved literals, SHA-256, JP/English equality and confidence retained in enemy_sprite_finalization_v5_evidence.json. Individual asset ranges are listed separately in participants.json / chekkit_evidence.json.','',
		'| File range | Purpose | Confidence |','|---|---|---|']
	for c in code:lines.append(f"| {'..'.join(c['file_range_exclusive'])} | {c['purpose']} | Confirmed static, bounded path |")
	lines += ['',
		'## Tests, preservation and reproduction','',
		'All **32 existing tests and 7 focused new tests pass (39 total)**. New checks cover all 182 IDs; frozen 326 metadata entries and 652 old PNG bytes; Chekkit dimensions/object count/four pixel hashes and BG discrepancy; exact exception token/length/consumption and native row-read range; refusal of changed hashes/other sizes/sources; all 25 component graphs, states, attributes and source equality; refusal to overwrite and a fresh deterministic export. The 156 completed records are not re-extracted by the new pipeline, including its repeatability test.','',
		'Commands from workspace root:','',
		'```powershell','python -B tools/extract/finalize_enemy_sprites_v5.py --output NEW_DIRECTORY',
		'python -B tools/extract/test_finalize_enemy_sprites_v5.py','```','',
		'Keep the versioned prior decoder modules and v4 final exports as dependencies. No old script/report/test was modified. New code files: finalize_enemy_sprites_v5.py, test_finalize_enemy_sprites_v5.py, audit_enemy_sprites_v5.py under tools/extract/. New report/evidence: this file and enemy_sprite_finalization_v5_evidence.json. All new local PNGs/catalogs/manifests/test logs/integrity results live under exports/enemy_sprites_v5/. The exact added-file list is in changed_files.json; modified pre-existing file list is empty if integrity passes.','',
		'Before the first write, the established all-workspace scope hashed **7,723 files**, with zero read errors. Exclusions: .git, installed Ghidra, Python caches, generated api-classes/compile-libs. Final integrity.json rehashes every original path, compares earlier v4 integrity expectations, counts preserved PNGs, and detects missing/changed files. Asset output directories contain local ignore files; no files were committed or published. No NPC/player extraction was begun.','']
	with REPORT.open('x',encoding='utf-8') as f:f.write('\n'.join(lines))
	before=json.loads((SESSION/'protected_before.json').read_text());changed=[];missing=[]
	for name,expected in before['hashes'].items():
		try:
			with (ROOT/name).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
		except FileNotFoundError:missing.append(name);continue
		if actual!=expected:changed.append(name)
	oldbaseline=json.loads((ROOT/'reverse_engineering/exports/enemy_sprites_v4/protected_before.json').read_text())['hashes']
	old_differences=[p for p,h in oldbaseline.items() if before['hashes'].get(p)!=h]
	added=[]
	for parent,dirs,files in os.walk(ROOT):
		dirs[:]=[d for d in dirs if d not in ('.git','Ghidra','__pycache__','api-classes','compile-libs')]
		for name in files:
			rel=(Path(parent)/name).relative_to(ROOT).as_posix()
			if rel not in before['hashes']:added.append(rel)
	# Include audit manifests about to be exclusively created.
	added.extend(['reverse_engineering/exports/enemy_sprites_v5/changed_files.json','reverse_engineering/exports/enemy_sprites_v5/integrity.json'])
	new_json(SESSION/'changed_files.json',dict(modified=changed,missing=missing,added=sorted(added)))
	result=dict(passed=not(changed or missing or old_differences),protected_count=len(before['hashes']),baseline_errors=before['errors'],changed=changed,missing=missing,
		prior_v4_protected_count=len(oldbaseline),prior_v4_baseline_differences=old_differences,preserved_native_pngs=326,preserved_total_pngs=652,
		rom_writes=0,emulator_runs=0,whole_rom_analysis=False,tests_passed=39,native_windows=len(code),new_files=len(added))
	new_json(SESSION/'integrity.json',result);print(json.dumps(result,indent=2))
	if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
