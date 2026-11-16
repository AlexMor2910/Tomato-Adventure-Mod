"""Finalize local audit and distribution-safe v1 package; exclusive outputs."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'tools/patch/output/cumulative-v1-20261028'


def sha(path):
	return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, data):
	with (DIRECTORY / name).open('x', encoding='utf-8') as stream:
		json.dump(data, stream, indent=2)
		stream.write('\n')


def main():
	before = json.loads((DIRECTORY / 'preservation_before.json').read_bytes())
	changed = [p for p, h in before.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
	if changed:
		raise ValueError('Preservation failed: ' + str(changed))
	write('preservation_audit.json', dict(files_checked=len(before), changed=changed, passed=True,
		excluded=['Ghidra vendor', 'mGBA vendor', 'reverse_engineering/ghidra projects',
			'copied emulator directories', '.git', '__pycache__'],
		note='No writes to excluded trees; they are not hash-audited. New source files are outside baseline inventory.'))
	suites = [('python -B -m unittest discover -s tests -p test_binky_exchange_rate_two.py', 5),
		('python -B -m unittest discover -s tests -p test_kaizo_binky_100.py', 11),
		('python -B -m unittest discover -s tests -p test_gimmick_balance.py', 10),
		('python -B tools/extract/convert_gimmick_scaling.py --self-test', 3),
		('python -B -m unittest discover -s tests -p test_cumulative_v1.py', 5),
		('python -B -m unittest discover -s tests -p test_alessa_recruitment_wrapper.py', 4)]
	write('automated_tests.json', dict(record='Observed tool executions on 2026-10-28; no runtime simulation',
		suites=[dict(command=c, tests=n, exit_code=0, result='PASS') for c, n in suites], total_tests=38,
		independent_verifier='PASS implemented scope; music incomplete',
		new_tests_source_sha256=sha(ROOT / 'tests/test_cumulative_v1.py')))
	sources = ['tools/patch/cumulative_v1.py', 'tools/analyze/verify_cumulative_v1.py',
		'tools/analyze/cumulative_v1_evidence.py', 'tools/patch/apply_cumulative_v1_bps.py',
		'tools/patch/package_cumulative_v1.py', 'tests/test_cumulative_v1.py',
		'reverse_engineering/cumulative_v1_investigation.md']
	# Explicit allowlist: never add ROMs, original script dumps, saves or assets.
	files = {Path(p).name: ROOT / p for p in sources}
	files['README.md'] = DIRECTORY / 'README.md'
	for name in ['manifest.json', 'operations.json', 'changed_bytes.json', 'music_ledger.json',
		'attack_comparisons.csv', 'independent_verification.json', 'tomato_cumulative_v1.bps',
		'attack_bytes.json', 'detector_bytes.json', 'hanzo_bytes.json', 'hawker_bytes.json', 'kaizo_bytes.json', 'music_bytes.json']:
		files[name] = DIRECTORY / 'build' / name
	files['automated_tests.json'] = DIRECTORY / 'automated_tests.json'
	write('distribution_manifest.json', dict(files={n: sha(p) for n, p in files.items()},
		contains_rom=False, contains_extracted_assets=False, status='INCOMPLETE / Experimental / Runtime Validation Pending'))
	files['distribution_manifest.json'] = DIRECTORY / 'distribution_manifest.json'
	with zipfile.ZipFile(DIRECTORY / 'tomato_cumulative_v1_INCOMPLETE_patch.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
		for name, path in sorted(files.items()):
			if Path(name).suffix.lower() in ('.gba', '.sav', '.png'):
				raise ValueError('Forbidden distribution member')
			entry = zipfile.ZipInfo(name, date_time=(2026, 10, 28, 0, 0, 0))
			entry.compress_type = zipfile.ZIP_DEFLATED
			archive.writestr(entry, path.read_bytes())
	with zipfile.ZipFile(DIRECTORY / 'tomato_cumulative_v1_INCOMPLETE_patch.zip') as archive:
		if archive.testzip() is not None or set(archive.namelist()) != set(files):
			raise ValueError('ZIP verification failed')
		for name, path in files.items():
			if archive.read(name) != path.read_bytes():
				raise ValueError('ZIP readback failed')
	created = {str((ROOT / p).relative_to(ROOT)): sha(ROOT / p) for p in sources}
	created.update({str(p.relative_to(ROOT)): sha(p) for p in DIRECTORY.rglob('*') if p.is_file() and p.name != 'preservation_before.json'})
	write('created_files.json', dict(created=created, changed_preexisting_files=[],
		note='Inventory excludes itself and the preservation baseline; all other new artifacts listed.'))
	print(json.dumps(dict(protected_files=len(before), unchanged=True, tests=38, package_members=len(files),
		zip=str(DIRECTORY / 'tomato_cumulative_v1_INCOMPLETE_patch.zip'))))


if __name__ == '__main__':
	main()
