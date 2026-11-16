"""Create the asset-free v3 patch package and final identity/inventory exclusively."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'tools/patch/output/cumulative-v3-20261028'


def sha(path):
	return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
	with path.open('x', encoding='utf-8') as f:
		json.dump(data, f, indent=2)
		f.write('\n')


def main():
	audit = json.loads((DIRECTORY / 'preservation_audit.json').read_bytes())
	if not audit['passed'] or audit['changed']:
		raise ValueError('Protected-file audit failed')
	sources = ['tools/analyze/cumulative_v3_music_resolution.py', 'tools/analyze/verify_cumulative_v3_music_resolution.py',
		'tools/patch/cumulative_v3.py', 'tools/patch/apply_cumulative_v3_bps.py', 'tools/patch/package_cumulative_v3.py',
		'tests/test_cumulative_v3_music_resolution.py', 'reverse_engineering/cumulative_v3_music_resolution.md',
		'reverse_engineering/cumulative_v3_music_resolution.json']
	files = {Path(p).name: ROOT / p for p in sources}
	files['verify_cumulative_v1.py'] = ROOT / 'tools/analyze/verify_cumulative_v1.py'
	for name in ('README.md', 'automated_tests.json', 'independent_verification.json', 'music_rooms.json'):
		files[name] = DIRECTORY / name
	for name in ('manifest.json', 'operations.json', 'changed_bytes.json', 'v2_to_v3_bytes.json',
		'attack_bytes.json', 'hanzo_bytes.json', 'hawker_bytes.json', 'kaizo_bytes.json', 'detector_bytes.json',
		'music_bytes.json', 'tomato_cumulative_v3.bps', 'v2_to_v3.bps'):
		files[name] = DIRECTORY / 'build' / name
	write(DIRECTORY / 'distribution_manifest.json', dict(files={n: sha(p) for n, p in files.items()},
		contains_rom=False, contains_extracted_assets=False,
		status='Tomato Adventure — Cumulative v3 Incomplete Experimental Build',
		excluded_local_artifacts=['native/script evidence dumps', 'initial draft resolution', 'ROMs', 'saves/states/assets']))
	files['distribution_manifest.json'] = DIRECTORY / 'distribution_manifest.json'
	archive_path = DIRECTORY / 'tomato_cumulative_v3_INCOMPLETE_patch.zip'
	with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
		for name, path in sorted(files.items()):
			if path.suffix.lower() not in ('.py', '.md', '.json', '.bps'):
				raise ValueError('Unapproved distribution member')
			entry = zipfile.ZipInfo(name, (2026, 10, 28, 0, 0, 0))
			entry.compress_type = zipfile.ZIP_DEFLATED
			archive.writestr(entry, path.read_bytes())
	with zipfile.ZipFile(archive_path) as archive:
		if archive.testzip() or set(archive.namelist()) != set(files):
			raise ValueError('ZIP failed verification')
		if any(archive.read(n) != p.read_bytes() for n, p in files.items()):
			raise ValueError('ZIP readback differs')
	manifest = json.loads((DIRECTORY / 'build/manifest.json').read_bytes())
	write(DIRECTORY / 'release_identity.json', dict(rom_sha256=manifest['output_sha256'], bytes=manifest['size'],
		baseline_sha256=manifest['baseline_sha256'], v2_sha256=manifest['v2_sha256'],
		bps_sha256=manifest['bps_sha256'], incremental_bps_sha256=manifest['incremental_bps_sha256'],
		zip_sha256=sha(archive_path), zip_size=archive_path.stat().st_size, zip_members=len(files),
		canonical_incremental_equal=True, status=manifest['status']))
	created = {p: sha(ROOT / p) for p in sources}
	created.update({str(p.relative_to(ROOT)): sha(p) for p in DIRECTORY.rglob('*') if p.is_file()})
	write(DIRECTORY / 'created_files.json', dict(created=created, changed_preexisting=[],
		note='Inventory excludes itself. Initial new-session draft retained; final correction documented.'))
	print(json.dumps(json.loads((DIRECTORY / 'release_identity.json').read_bytes())))


if __name__ == '__main__':
	main()
