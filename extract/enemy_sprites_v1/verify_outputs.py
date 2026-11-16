"""Read-only audit of protected artifacts and independently cross-check exports."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import extract_enemy_sprites as ex


def main():
	out = ex.ROOT / 'reverse_engineering/exports/enemy_sprites_v1'
	baseline = json.loads((out / 'protected_baseline_v1.json').read_text())
	changed = []
	for relative, expected in baseline.items():
		p = ex.ROOT / relative
		with p.open('rb') as stream:
			actual = hashlib.file_digest(stream, 'sha256').hexdigest()
		if actual != expected:
			changed.append(relative)
	assets = out / 'assets'
	with (assets / 'enemies.csv').open(encoding='utf-8') as stream:
		catalog = list(csv.DictReader(stream))
	with (assets / 'frames.csv').open(encoding='utf-8') as stream:
		frames = list(csv.DictReader(stream))
	assert len(catalog) == 182 and len({r['enemy_id'] for r in catalog}) == 182
	counts = Counter(r['status'] for r in catalog)
	assert counts == {'verified_base_frames': 127, 'unresolved': 55}
	assert len(frames) == 254
	assert {r['enemy_id'] for r in frames} == {r['enemy_id'] for r in catalog if r['status'] == 'verified_base_frames'}
	assert all(Counter(r['frame_index'] for r in frames if r['enemy_id'] == eid) == {'0': 1, '1': 1} for eid in {r['enemy_id'] for r in frames})
	assert not any((assets / f"enemy_{int(r['enemy_id'], 16):02X}_frame0.png").exists() for r in catalog if r['status'] == 'unresolved')
	results = []
	for arguments in ([str(Path(__file__).with_name('test_enemy_sprites.py'))], ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_extract_field_maps.py', '-v']):
		p = subprocess.run([sys.executable, '-B', *arguments], cwd=ex.ROOT, capture_output=True, text=True)
		results.append(dict(command=[sys.executable, '-B', *arguments], returncode=p.returncode, output=p.stdout + p.stderr))
	assert not changed and all(r['returncode'] == 0 for r in results)
	cumulative = 'tools/patch/output/detector-hp120-mit25/detector_rebalance.gba'
	assert baseline[cumulative] == '124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0'
	report = dict(protected_count=len(baseline), changed=changed,
		protected_extensions=dict(Counter(Path(p).suffix.lower() for p in baseline)),
		catalog_counts=dict(counts), frames=len(frames), native_pngs=len(list(assets.glob('*frame[01].png'))),
		preview_pngs=len(list(assets.glob('*_4x.png'))), tests=results,
		cumulative_sha256=baseline[cumulative],
		audit_scope='Existing ROM/save/savestate/PNG/report/CSV/source/config artifacts; installed Ghidra libraries excluded. Baseline completed after first exports; all session writes confined to new versioned directories.')
	with (out / 'verification_v1.json').open('x', encoding='utf-8') as stream:
		json.dump(report, stream, indent=2)
		stream.write('\n')
	print(json.dumps({k: v for k, v in report.items() if k != 'tests'}, indent=2))


if __name__ == '__main__':
	main()
