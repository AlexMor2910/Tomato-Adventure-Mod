"""Standalone v3 BPS application. Requires adjacent verify_cumulative_v1.py.

python -B apply_cumulative_v3_bps.py INPUT.gba PATCH.bps NEW_DIRECTORY
"""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from verify_cumulative_v1 import decode_bps

INPUTS = {'8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde',
	'300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482'}
OUTPUT = '3f12082f97b640ef7fa09cc64c935cd18e7bbcb41ee6b99d4c0abb9c2995fbb9'


def main():
	if len(sys.argv) != 4:
		raise SystemExit(__doc__)
	source_path, patch_path, directory = map(Path, sys.argv[1:])
	source = source_path.read_bytes()
	if len(source) != 8388608 or hashlib.sha256(source).hexdigest() not in INPUTS:
		raise ValueError('Requires exact English baseline or v2; wrong/other experimental inputs rejected')
	target = decode_bps(patch_path.read_bytes(), source)
	if len(target) != len(source) or hashlib.sha256(target).hexdigest() != OUTPUT:
		raise ValueError('Wrong v3 patch/output identity')
	directory.mkdir(parents=True, exist_ok=False)
	rom = directory / 'tomato_cumulative_v3_INCOMPLETE.gba'
	with rom.open('xb') as f:
		f.write(target)
	if rom.read_bytes() != target or source_path.read_bytes() != source:
		raise ValueError('Output readback or input preservation failed')
	print(str(rom.resolve()))
	print(OUTPUT)


if __name__ == '__main__':
	main()
