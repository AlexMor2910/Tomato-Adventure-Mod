"""Apply the v1 INCOMPLETE experimental patch to a user-owned English baseline.

python apply_cumulative_v1_bps.py BASELINE.gba PATCH.bps NEW_OUTPUT_DIRECTORY
"""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analyze'))
from verify_cumulative_v1 import decode_bps

SOURCE = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
TARGET = '1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f'


def main():
	if len(sys.argv) != 4:
		raise SystemExit(__doc__)
	baseline, patch, directory = map(Path, sys.argv[1:])
	source = baseline.read_bytes()
	if len(source) != 0x800000 or hashlib.sha256(source).hexdigest() != SOURCE:
		raise ValueError('Requires the untouched English baseline; Japanese and experimental inputs rejected')
	target = decode_bps(patch.read_bytes(), source)
	if len(target) != len(source) or hashlib.sha256(target).hexdigest() != TARGET:
		raise ValueError('Wrong patch/output identity')
	directory.mkdir(parents=True, exist_ok=False)
	output = directory / 'tomato_cumulative_v1_INCOMPLETE.gba'
	with output.open('xb') as f:
		f.write(target)
	if output.read_bytes() != target or baseline.read_bytes() != source:
		raise ValueError('Output readback/input preservation mismatch')
	print(str(output.resolve()))
	print(TARGET)


if __name__ == '__main__':
	main()
