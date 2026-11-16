"""Exclusive v2 distribution package; explicit asset-free allowlist."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'tools/patch/output/cumulative-v2-20261028'


def sha(path):
	return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
	with path.open('x', encoding='utf-8') as f:
		json.dump(value, f, indent=2)
		f.write('\n')


def main():
	audit = json.loads((DIRECTORY / 'preservation_audit.json').read_bytes())
	if not audit['passed'] or audit['changed']:
		raise ValueError('Protected-file audit did not pass')
	sources = ['tools/analyze/cumulative_v2_music.py', 'tools/analyze/plan_cumulative_v2_music.py',
		'tools/analyze/verify_cumulative_v2.py', 'tools/patch/cumulative_v2.py',
		'tools/patch/apply_cumulative_v2_bps.py', 'tools/patch/package_cumulative_v2.py',
		'tests/test_cumulative_v2_music.py', 'reverse_engineering/cumulative_v2_music_tracks.csv',
		'reverse_engineering/cumulative_v2_music_rooms.csv', 'reverse_engineering/cumulative_v2_music_plan.json',
		'reverse_engineering/cumulative_v2_music_plan.md']
	files = {Path(p).name: ROOT / p for p in sources}
	# Existing decoder copy needed by the standalone applicator; source stays intact.
	files['verify_cumulative_v1.py'] = ROOT / 'tools/analyze/verify_cumulative_v1.py'
	files['README.md'] = DIRECTORY / 'README.md'
	files['automated_tests.json'] = DIRECTORY / 'automated_tests.json'
	for name in ['manifest.json', 'operations.json', 'incremental_operations.json', 'changed_bytes.json',
		'attack_bytes.json', 'hanzo_bytes.json', 'hawker_bytes.json', 'kaizo_bytes.json', 'detector_bytes.json',
		'music_bytes.json', 'independent_verification.json', 'tomato_cumulative_v2.bps', 'v1_to_v2.bps']:
		files[name] = DIRECTORY / 'build' / name
	write(DIRECTORY / 'distribution_manifest.json', dict(status='Cumulative v2 — Incomplete Experimental Build',
		files={n: sha(p) for n, p in files.items()}, contains_rom=False, contains_extracted_assets=False,
		local_evidence_excluded=['review PNGs', 'bounded_script_audit.json', 'music_evidence.json']))
	files['distribution_manifest.json'] = DIRECTORY / 'distribution_manifest.json'
	archive_path = DIRECTORY / 'tomato_cumulative_v2_INCOMPLETE_patch.zip'
	with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
		for name, path in sorted(files.items()):
			if path.suffix.lower() not in {'.py', '.md', '.csv', '.json', '.bps'}:
				raise ValueError('Forbidden distribution asset')
			info = zipfile.ZipInfo(name, (2026, 10, 28, 0, 0, 0))
			info.compress_type = zipfile.ZIP_DEFLATED
			archive.writestr(info, path.read_bytes())
	with zipfile.ZipFile(archive_path) as archive:
		if archive.testzip() or set(archive.namelist()) != set(files):
			raise ValueError('ZIP integrity/member mismatch')
		for name, path in files.items():
			if archive.read(name) != path.read_bytes():
				raise ValueError('ZIP readback mismatch')
	manifest = json.loads((DIRECTORY / 'build/manifest.json').read_bytes())
	write(DIRECTORY / 'release_identity.json', dict(rom_sha256=manifest['output_sha256'], rom_size=manifest['size'],
		baseline_sha256=manifest['baseline_sha256'], v1_sha256=manifest['v1_sha256'],
		bps_sha256=manifest['bps_sha256'], incremental_bps_sha256=manifest['incremental_bps_sha256'],
		zip_sha256=sha(archive_path), zip_bytes=archive_path.stat().st_size, zip_members=len(files),
		canonical_incremental_equal=True, status=manifest['status']))
	created = {p: sha(ROOT / p) for p in sources}
	created.update({str(p.relative_to(ROOT)): sha(p) for p in DIRECTORY.rglob('*') if p.is_file()})
	write(DIRECTORY / 'created_files.json', dict(created=created, changed_preexisting=[],
		note='Inventory excludes itself; local review images are copyrighted and excluded from ZIP.'))
	print(json.dumps(json.loads((DIRECTORY / 'release_identity.json').read_bytes())))


if __name__ == '__main__':
	main()
