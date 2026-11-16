"""Independent readback verifier; never imports the cumulative builder.

python -B tools/analyze/verify_cumulative_v1.py OUTPUT_DIRECTORY
"""
import csv
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
BASE_HASH = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'


def require(value, message):
	if not value:
		raise ValueError(message)


def decode_bps(patch, source):
	require(patch[:4] == b'BPS1', 'BPS magic')
	require(zlib.crc32(patch[:-4]) == struct.unpack_from('<I', patch, len(patch) - 4)[0], 'BPS patch CRC')
	require(zlib.crc32(source) == struct.unpack_from('<I', patch, len(patch) - 12)[0], 'BPS source CRC')
	pos = 4
	def number():
		nonlocal pos
		n, shift = 0, 1
		while True:
			require(pos < len(patch) - 12, 'Truncated BPS')
			byte = patch[pos]
			pos += 1
			n += (byte & 127) * shift
			if byte & 128:
				return n
			shift <<= 7
			n += shift
	require(number() == len(source), 'BPS source size')
	size, metadata = number(), number()
	pos += metadata
	output = bytearray()
	while len(output) < size:
		action = number()
		length, mode = (action >> 2) + 1, action & 3
		require(len(output) + length <= size, 'BPS target overrun')
		if mode == 0:
			output.extend(source[len(output):len(output) + length])
		elif mode == 1:
			require(pos + length <= len(patch) - 12, 'BPS literal overrun')
			output.extend(patch[pos:pos + length])
			pos += length
		else:
			raise ValueError('Unexpected BPS action')
	require(pos == len(patch) - 12, 'Trailing BPS actions')
	require(zlib.crc32(output) == struct.unpack_from('<I', patch, pos + 4)[0], 'BPS target CRC')
	return bytes(output)


def verify(source, target, directory):
	require(len(source) == len(target) == 0x800000, 'Wrong ROM length')
	require(hashlib.sha256(source).hexdigest() == BASE_HASH, 'Wrong baseline')
	expected = {}
	def expect(a, old, new):
		require(len(old) == len(new), 'Width mismatch')
		require(source[a:a + len(old)] == old and target[a:a + len(new)] == new, 'Readback mismatch at ' + hex(a))
		for j, (x, y) in enumerate(zip(old, new)):
			if x != y:
				require(a + j not in expected, 'Duplicate expected change')
				expected[a + j] = (x, y)
	# Retained preflight ledger is independent of builder-generated operations.
	hawker = json.loads((ROOT / 'reverse_engineering/experiments/binky_exchange_rate_two_evidence.json').read_bytes())
	for row in hawker['operations']:
		expect(int(row['offset'], 16), bytes.fromhex(row['old']), bytes.fromhex(row['new']))
	plan = json.loads((ROOT / 'reverse_engineering/kaizo_binky_100_proposal.json').read_bytes())
	for row in plan['operations']:
		expect(int(row['file'], 16), bytes.fromhex(row['old']), bytes.fromhex(row['new']))
	thresholds = [2, 4, 6, 7, 9, 12, 14, 17, 21, 24, 28, 32, 36, 41, 45, 50, 55, 61, 66, 72, 78, 85, 92, 100]
	for row, threshold in zip(plan['thresholds'], thresholds):
		for field in ('display_file', 'compare_file'):
			require(struct.unpack_from('<H', target, int(row[field], 16))[0] == threshold, 'Kaizo threshold')
	for a, old, new in ((0x638056, b'\x87\0', b'\x78\0'), (0x63805A, b'\x26\0', b'\x19\0'),
		(0x10D69B, b'\x1B', b'\x29'), (0x111E48, b'\x29', b'\x1B'), (0x62D731, b'\x0D', b'\x07')):
		expect(a, old, new)
	require(target[0x637DAA:0x637DAC] == b'\x06\x01' and target[0x637DAE:0x637DB0] == b'\x36\0', 'Dragon changed')
	# Independent field allowlist: no complete records, caps or auxiliary bytes exchanged.
	bases = [0x62C250 + (i - 1) * 88 for i in (27, 41)]
	for a, b in (bases, bases[::-1]):
		for delta in [34] + [40 + 2 * j for j in range(9)]:
			expect(a + delta, source[a + delta:a + delta + 1], source[b + delta:b + delta + 1])
	rows = []
	for upgrade in range(256):
		for difficulty in range(1, 10):
			def attack(data, record):
				return ((data[record + 34] + upgrade) * data[record + 38 + difficulty * 2]) // 100
			old = [attack(source, b) for b in bases]
			new = [attack(target, b) for b in bases]
			require(new == old[::-1], 'Attack progression mismatch')
			if upgrade <= 45:
				rows.append(dict(upgrade=upgrade, difficulty=difficulty, erupter_original=old[0], dojo_original=old[1],
					erupter_patched=new[0], dojo_patched=new[1]))
	actual = {i: (a, b) for i, (a, b) in enumerate(zip(source, target)) if a != b}
	require(actual == expected, 'Unaccounted full-ROM differences')
	require(source[:0xC0] == target[:0xC0], 'Header changed')
	require(target[0xB2] == 0x96 and target[0xBD] == (-sum(target[0xA0:0xBD]) - 0x19) & 255, 'Invalid GBA header')
	require(target[0x10D69D:0x10D6A3] == bytes.fromhex('FD 2F 33 4B 12 08'), 'Alessa redirect retained')
	for a, b in ((0x124B33, 0x124BF2), (0x6ADA0, 0x6AE28), (0x1084CA, 0x1086F8),
		(0x80424, 0x805FC), (0x1271E9, 0x1275B6)):
		require(source[a:b] == target[a:b], 'Acquisition/tutorial/collection/recruitment code changed')
	# Every map byte except one approved selector remains identical, including all actors/events.
	for mid in range(494):
		a = 0x62D3E4 + mid * 28
		if mid != 30:
			require(source[a:a + 28] == target[a:a + 28], 'Unrequested map changed')
		else:
			require(source[a + 5] & 192 == target[a + 5] & 192, 'Metadata upper bits changed')
	require(decode_bps((directory / 'tomato_cumulative_v1.bps').read_bytes(), source) == target, 'BPS reproduction differs')
	manifest = json.loads((directory / 'manifest.json').read_bytes())
	require(hashlib.sha256(target).hexdigest() == manifest['output_sha256'], 'Output manifest identity')
	ledger = json.loads((directory / 'changed_bytes.json').read_bytes())
	require({r['file']: (r['old'], r['new']) for r in ledger} == actual and len(ledger) == len(actual), 'Ledger mismatch')
	return dict(result='PASS within implemented scope; music package INCOMPLETE', changed_bytes=len(actual),
		attack_cases=256 * 9, valid_upgrade_cases=46 * 9, upgrade_range='0..45 normal; 46..255 arithmetic robustness only',
		bps_reproduction=True, header_valid=True, alessa_excluded=True, no_new_actors=True,
		all_other_bytes_identical=True, music_event_override_coverage='Incomplete; no event override changes',
		runtime='UNTESTED final ROM; user-operated testing required'), rows


def main():
	directory = Path(sys.argv[1])
	source = (ROOT / 'Tomato Adventure (Japan) (patched).gba').read_bytes()
	target = (directory / 'tomato_cumulative_v1_INCOMPLETE.gba').read_bytes()
	result, rows = verify(source, target, directory)
	with (directory / 'independent_verification.json').open('x', encoding='utf-8') as f:
		json.dump(result, f, indent=2)
	with (directory / 'attack_comparisons.csv').open('x', encoding='utf-8', newline='') as f:
		writer = csv.DictWriter(f, fieldnames=list(rows[0]))
		writer.writeheader()
		writer.writerows(rows)
	print(json.dumps(result))


if __name__ == '__main__':
	main()
