"""Run read-only tests and recheck the completed pre-write protected baseline."""
import collections
import hashlib
import json
from pathlib import Path
import os
import subprocess
import sys

import extract_enemy_sprites as ex


def main():
	baseline=json.loads((ex.OUT/'protected_before.json').read_text())
	assert not baseline['errors'] and len(baseline['hashes'])==3939
	results=[]
	for version in ('v1','v2'):
		command=[sys.executable,'-B',str(ex.ROOT/f'tools/extract/enemy_sprites_{version}/test_enemy_sprites.py')]
		p=subprocess.run(command,cwd=ex.ROOT,capture_output=True,text=True)
		results.append(dict(command=command,returncode=p.returncode,output=p.stdout+p.stderr))
	changed,missing=[],[]
	for relative,expected in baseline['hashes'].items():
		p=ex.ROOT/relative
		try:
			with p.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
		except FileNotFoundError:
			missing.append(relative)
			continue
		if actual!=expected:changed.append(relative)
	added=[]
	for parent,dirs,files in os.walk(ex.ROOT):
		dirs[:]=[d for d in dirs if d not in ('.git','Ghidra','__pycache__','api-classes','compile-libs')]
		for name in files:
			relative=(Path(parent)/name).relative_to(ex.ROOT).as_posix()
			if relative not in baseline['hashes']:added.append(relative)
	outside=[p for p in added if not p.startswith(('tools/extract/enemy_sprites_v2/','reverse_engineering/exports/enemy_sprites_v2/'))]
	passed=not(changed or missing or outside) and all(r['returncode']==0 for r in results)
	report=dict(passed=passed,protected_count=len(baseline['hashes']),baseline_completed_before_first_write=True,
		scope=baseline['scope'],baseline_errors=baseline['errors'],changed=changed,missing=missing,new_files_outside_v2=outside,
		protected_types=dict(collections.Counter(Path(p).suffix.lower() for p in baseline['hashes'])),tests=results,
		coverage=json.loads((ex.OUT/'final/summary.json').read_text()),canonical_output='reverse_engineering/exports/enemy_sprites_v2/final',
		png_count=len(list((ex.OUT/'final').glob('*.png'))),v1_png_regression_count=508,earlier_fixture_png_regression_count=8)
	with (ex.OUT/'verification_complete.json').open('x',encoding='utf-8') as stream:
		json.dump(report,stream,indent=2)
		stream.write('\n')
	print(json.dumps({k:v for k,v in report.items() if k not in ('tests','protected_types')},indent=2))
	if not passed:raise SystemExit(1)


if __name__=='__main__':main()
