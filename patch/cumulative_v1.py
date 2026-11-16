"""Offline cumulative build. Baseline only; exclusive outputs; no emulator access.

Usage: python -B tools/patch/cumulative_v1.py --output-dir NEW_DIRECTORY
Music is deliberately incomplete: only the proven map 001E is changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/patch'), str(ROOT / 'tools/analyze')]
import binky_exchange_rate_two as hawker
import kaizo_binky_100 as kaizo
import detector_rebalance as detector
import alessa_recruitment_wrapper as alessa

BASE_HASH = hawker.PROFILES['baseline'][1]


def sha(data):
	return hashlib.sha256(data).hexdigest()


def require(condition, message):
	if not condition:
		raise ValueError(message)


def write_json(path, value):
	with path.open('x', encoding='utf-8', newline='\n') as stream:
		json.dump(value, stream, indent=2)
		stream.write('\n')


def apply(source, operations):
	output = bytearray(source)
	occupied = set()
	for op in operations:
		a, old, new = op['offset'], bytes.fromhex(op['old']), bytes.fromhex(op['new'])
		require(len(old) == len(new) > 0 and 0 <= a <= len(source) - len(old), 'Invalid range')
		require(not occupied.intersection(range(a, a + len(old))), 'Overlapping operations')
		occupied.update(range(a, a + len(old)))
		require(source[a:a + len(old)] == old, 'Expected bytes mismatch at ' + hex(a))
		output[a:a + len(new)] = new
	return bytes(output)


def operations(source):
	require(len(source) == 0x800000 and sha(source) == BASE_HASH, 'Wrong English baseline')
	result = []
	def add(feature, offset, old, new, evidence):
		result.append(dict(feature=feature, offset=offset, bus=offset + 0x08000000,
			old=old.hex(' '), new=new.hex(' '), evidence=evidence))
	for op in hawker.validate_source(source, 'baseline'):
		add('hawker', op['offset'], op['old'], op['new'], 'binky_exchange_rate_two.py; ' + op['role'])
	plan = json.loads(kaizo.PLAN.read_bytes())
	for a, old, new in kaizo.validate_plan(plan):
		add('kaizo', a, old, new, 'kaizo_binky_100_proposal.json; approved_operations')
	for a, old, new, field in detector.OPERATIONS:
		add('detector', a, old, new, 'detector_rebalance.py; ' + field)
	for a, old, new in ((0x10D69B, 0x1B, 0x29), (0x111E48, 0x29, 0x1B)):
		require(source[a - 3:a + 2] == bytes([0xFD, 0x0B, 0x1C, old, 0]), 'Hanzo command mismatch')
		require(source[a + 2:a + 8] == bytes.fromhex('FD 2F 33 4B 12 08'), 'Acquisition call mismatch')
		add('hanzo', a, bytes([old]), bytes([new]), 'cumulative_v1_investigation.md; shared acquisition 08124B33')
	x, y = [0x62C250 + (i - 1) * 0x58 for i in (27, 41)]
	require(source[x + 0x23] == source[y + 0x23] == 45, 'Upgrade caps differ')
	require(source[x + 0x27] & 15 == source[y + 0x27] & 15 == 0, 'Unexpected auxiliary type')
	require(all(source[a + j] == 0 for a in (x, y) for j in range(0x29, 0x3A, 2)), 'Nonzero auxiliary byte')
	for delta in (0x22, *range(0x28, 0x3A, 2)):
		for a, b in ((x, y), (y, x)):
			add('attack', a + delta, source[a + delta:a + delta + 1], source[b + delta:b + delta + 1],
				'gimmick_difficulty_scaling.md M1/L1/U1/B1; base or unsigned percentage only')
	a = 0x62D3E4 + 0x1E * 0x1C + 5
	require(source[a] == 0x0D and source[0x62D3E4 + 0x48 * 0x1C + 5] & 63 == 7, 'Mayonen selector mismatch')
	add('music', a, source[a:a + 1], bytes([(source[a] & 0xC0) | 7]), 'mayonen_caverns_music.py; user-confirmed map 001E only')
	apply(source, result)
	return result


def ancestry(source):
	"""Reconstruct every ancestor; compare full binaries and reported hashes."""
	alessa.validate_source(source)
	wrapper = bytearray(source)
	wrapper[alessa.POINTER_OFFSET:alessa.POINTER_OFFSET + 4] = alessa.POINTER
	wrapper.extend(alessa.PAYLOAD + b'\xFF' * (alessa.OUTPUT_SIZE - len(source) - len(alessa.PAYLOAD)))
	paths = [hawker.PROFILES['recruitment-test'][0], kaizo.SOURCE, detector.SOURCE,
		ROOT / 'tools/patch/output/detector-hp120-mit25/detector_rebalance.gba']
	expected = [hawker.PROFILES['recruitment-test'][1], kaizo.SOURCE_SHA256,
		detector.SOURCE_SHA256, '124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0']
	stages = [bytes(wrapper)]
	stages.append(bytes(hawker.build(stages[-1], 'recruitment-test')))
	stages.append(kaizo.build(stages[-1], json.loads(kaizo.PLAN.read_bytes())))
	stages.append(detector.build(stages[-1]))
	records = []
	for path, fingerprint, rebuilt in zip(paths, expected, stages):
		data = path.read_bytes()
		require(sha(data) == fingerprint and data == rebuilt, 'Ancestry mismatch: ' + str(path))
		records.append(dict(path=str(path.relative_to(ROOT)), size=len(data), sha256=fingerprint, full_reproduction=True))
	return records


def variable(value):
	result = bytearray()
	while True:
		byte = value & 127
		value >>= 7
		if value == 0:
			result.append(byte | 128)
			return result
		result.append(byte)
		value -= 1


def bps(source, target):
	"""BPS1 SourceRead/TargetRead only; no source assets included beyond changes."""
	require(len(source) == len(target), 'BPS size mismatch')
	patch = bytearray(b'BPS1') + variable(len(source)) + variable(len(target)) + variable(0)
	i = 0
	while i < len(source):
		start = i
		equal = source[i] == target[i]
		while i < len(source) and (source[i] == target[i]) == equal:
			i += 1
		patch += variable(((i - start - 1) << 2) | (0 if equal else 1))
		if not equal:
			patch += target[start:i]
	patch += struct.pack('<II', zlib.crc32(source), zlib.crc32(target))
	patch += struct.pack('<I', zlib.crc32(patch))
	return bytes(patch)


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--input', type=Path, default=hawker.BASELINE)
	parser.add_argument('--output-dir', required=True, type=Path)
	args = parser.parse_args()
	source = args.input.read_bytes()
	ops = operations(source)
	history = ancestry(source)
	output = apply(source, ops)
	args.output_dir.mkdir(parents=True, exist_ok=False)
	rom = args.output_dir / 'tomato_cumulative_v1_INCOMPLETE.gba'
	with rom.open('xb') as stream:
		stream.write(output)
	require(rom.read_bytes() == output, 'Readback mismatch')
	ledger = [dict(file=i, bus=i + 0x08000000, old=a, new=b,
		feature=next(o['feature'] for o in ops if o['offset'] <= i < o['offset'] + len(bytes.fromhex(o['old']))))
		for i, (a, b) in enumerate(zip(source, output)) if a != b]
	write_json(args.output_dir / 'operations.json', ops)
	write_json(args.output_dir / 'changed_bytes.json', ledger)
	for feature in sorted({o['feature'] for o in ops}):
		write_json(args.output_dir / (feature + '_bytes.json'), [o for o in ledger if o['feature'] == feature])
	with (args.output_dir / 'tomato_cumulative_v1.bps').open('xb') as stream:
		stream.write(bps(source, output))
	write_json(args.output_dir / 'manifest.json', dict(status='INCOMPLETE / Experimental / Runtime Validation Pending',
		all_five_groups_complete=False, input_sha256=sha(source), output_sha256=sha(output), size=len(output),
		output_name=rom.name, changed_bytes=len(ledger), ancestry=history, alessa_wrapper_excluded=True,
		new_hawkers=False, music_scope='Only Mayonen Caverns 001E; other requested rooms unresolved',
		builder_sha256=sha(Path(__file__).read_bytes())))
	print(json.dumps(dict(rom=str(rom), sha256=sha(output), changed_bytes=len(ledger))))


if __name__ == '__main__':
	main()
