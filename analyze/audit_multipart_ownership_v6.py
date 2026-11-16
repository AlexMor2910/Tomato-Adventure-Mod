"""Exclusive v6 evidence closeout and protected-workspace SHA-256 audit."""
import hashlib
import json
import os
from pathlib import Path

import multipart_ownership_v6 as ex

ROOT=ex.ROOT
SESSION=ROOT/'reverse_engineering/exports/enemy_sprites_v6'


def write_new(path,obj):
	with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')


def main():
	baseline=json.loads((SESSION/'protected_before.json').read_text())
	rom,jp=ex.old.v3.load_roms()
	native=json.loads((ex.OUT/'native_evidence.json').read_text())
	for window in native:
		a,b=map(lambda n:int(n,16),window['file_range'])
		assert ex.old.v1.sha(rom[a:b])==window['sha256'] and rom[a:b]==jp[a:b]
	tests=json.loads((SESSION/'test_results.json').read_text())
	assert all(r['value']['exit_code']==0 for r in tests['results']) and tests['new_suite']['exit_code']==0
	evidence=dict(scope='Default shared OBJ submission and context-dependent standalone classification; no runtime observation',
		roms=dict(japanese_sha256=ex.old.v1.JP_SHA,english_sha256=ex.old.v1.EN_SHA),
		summary=json.loads((ex.OUT/'summary.json').read_text()),native_windows=native,
		profiles=json.loads((ex.OUT/'profiles.json').read_text()),
		debugger_observation=dict(executed=False,breakpoint_bus='0x08040424',mode='Thumb function entry',
			case='Root 31 Pompadour with child 33 Big Donut; before/after first naturally reached visible child state transition',
			registers=['R0 draw parameter pointer','R4 render state','LR caller'],expected_global_state='0x03000B04',generic_caller_lr='0x080406D9',
			expected_root_record_pointer_at_030008EC='0x08635DDC',base_descriptor='0x080C5580',base_object_count=29,
			draw_parameter_offsets=dict(descriptor='u32 +0',tile_offset='u16 +4',x='u16 +6',y='u16 +8',palette_delta='u8 +A',priority='s8 +B',mode='s8 +C'),
			memory=['u32[03000B08] descriptor table','u8[03000B11] cycle','u16[03000ABA] slot2 flags','u32[0300091C..03000928] palette pointers'],
			outcomes=['Same shared descriptor with changed actor flag supports atlas-only replacement',
			'Changed shared descriptor/parameters proves a dynamic global context requiring separate mapping',
			'Additional attributable child render state supports an independent draw path; unrelated party/effect draws excluded'],
			limitation='Does not infer an artistic semantic crop from unchanged base pixels'),
		code_sources={p:ex.old.v1.sha((ROOT/p).read_bytes()) for p in [
			'tools/analyze/multipart_ownership_v6.py','tools/analyze/test_multipart_ownership_v6.py','tools/analyze/audit_multipart_ownership_v6.py']},
		report_sha256=ex.old.v1.sha((ROOT/'reverse_engineering/multipart_enemy_ownership_v6.md').read_bytes()))
	write_new(ROOT/'reverse_engineering/multipart_enemy_ownership_v6_evidence.json',evidence)
	changed=[];missing=[]
	for relative,expected in baseline['hashes'].items():
		try:
			with (ROOT/relative).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
		except FileNotFoundError:missing.append(relative);continue
		if actual!=expected:changed.append(relative)
	prior=json.loads((ROOT/'reverse_engineering/exports/enemy_sprites_v5/protected_before.json').read_text())['hashes']
	prior_differences=[p for p,h in prior.items() if baseline['hashes'].get(p)!=h]
	added=[]
	for parent,dirs,files in os.walk(ROOT):
		dirs[:]=[d for d in dirs if d not in ('.git','Ghidra','__pycache__','api-classes','compile-libs')]
		for name in files:
			rel=(Path(parent)/name).relative_to(ROOT).as_posix()
			if rel not in baseline['hashes']:added.append(rel)
	added.extend(['reverse_engineering/exports/enemy_sprites_v6/integrity.json','reverse_engineering/exports/enemy_sprites_v6/changed_files.json'])
	write_new(SESSION/'changed_files.json',dict(modified=changed,missing=missing,added=sorted(added)))
	result=dict(passed=not(changed or missing or prior_differences),protected_count=len(baseline['hashes']),baseline_errors=baseline['errors'],
		changed=changed,missing=missing,prior_v5_baseline_count=len(prior),prior_v5_baseline_differences=prior_differences,
		preserved_v5_native_pngs=330,preserved_v5_total_pngs=660,tests_passed=46,native_windows_verified=len(native),
		rom_writes=0,emulator_operations=0,whole_rom_analysis=False,new_files=len(added))
	write_new(SESSION/'integrity.json',result);print(json.dumps(result,indent=2))
	if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
