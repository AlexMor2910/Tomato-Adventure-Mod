"""Apply a v2 BPS to the exact English baseline or verified v1; fresh output only.

python -B apply_cumulative_v2_bps.py INPUT.gba PATCH.bps NEW_DIRECTORY
Keep verify_cumulative_v1.py beside this file in the standalone package.
"""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from verify_cumulative_v1 import decode_bps

INPUTS = {'8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde',
	'1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f'}
TARGET = '300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482'


def main():
	if len(sys.argv) != 4:
		raise SystemExit(__doc__)
	source_path, patch_path, directory = map(Path, sys.argv[1:])
	source = source_path.read_bytes()
	if len(source) != 8388608 or hashlib.sha256(source).hexdigest() not in INPUTS:
		raise ValueError('Unexpected input ROM; Japanese and other experiments rejected')
	target = decode_bps(patch_path.read_bytes(), source)
	if len(target) != len(source) or hashlib.sha256(target).hexdigest() != TARGET:
		raise ValueError('Wrong v2 patch/output identity')
	directory.mkdir(parents=True, exist_ok=False)
	path = directory / 'tomato_cumulative_v2_INCOMPLETE.gba'
	with path.open('xb') as f:
		f.write(target)
	if path.read_bytes() != target or source_path.read_bytes() != source:
		raise ValueError('Readback or source preservation failed')
	print(str(path.resolve()))
	print(TARGET)


if __name__ == '__main__':
	main()
