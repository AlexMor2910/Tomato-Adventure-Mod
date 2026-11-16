"""Export proven menu scaling from existing extracts; never opens a ROM.

See reverse_engineering/gimmick_difficulty_scaling.md for scope and evidence IDs.
Calculated attacks are conditional menu outputs at upgrade zero, not battle damage.
"""
import argparse
import csv
from pathlib import Path
import tempfile
import unittest

TABLE = 0x62C250
STRIDE = 0x58
COUNT = 50
OFFSETS = tuple(range(0x28, 0x3A, 2))


def number(value):
	return int(value, 16) if value.lower().startswith('0x') else int(value)


def decode_pair(word, record_type):
	if not 0 <= word <= 65535 or not 0 <= record_type <= 15:
		raise ValueError('Invalid pair or type')
	percent, auxiliary = word & 255, word >> 8
	if record_type in (1, 2):
		return percent, auxiliary & 15, auxiliary >> 4
	return percent, auxiliary & 127, 0


def menu_attack(base, upgrade, percent):
	if any(not 0 <= x <= 255 for x in (base, upgrade, percent)):
		raise ValueError('Expected unsigned bytes')
	return (base + upgrade) * percent // 100


def upgrade_after(current, increment, cap):
	if any(not 0 <= x <= 255 for x in (current, increment, cap)):
		raise ValueError('Expected unsigned bytes')
	return min((current + increment) & 255, cap)


def read_csv(path):
	with Path(path).open(encoding='utf-8-sig', newline='') as handle:
		reader = csv.DictReader(handle)
		if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
			raise ValueError('Missing or duplicate headers')
		rows = list(reader)
	if len(rows) != COUNT:
		raise ValueError('Expected exactly 50 rows')
	return rows


def build_rows(raw_rows, named_rows):
	if len(raw_rows) != COUNT or len(named_rows) != COUNT:
		raise ValueError('Expected exactly 50 rows in both inputs')
	results = []
	for index, (source, named) in enumerate(zip(raw_rows, named_rows)):
		gid, offset = index + 1, TABLE + index * STRIDE
		if number(source['gimmick_id']) != gid or number(named['gimmick_id']) != gid or number(source['record_index']) != index:
			raise ValueError('IDs must be unique and ordered 1..50')
		if number(source['rom_file_offset']) != offset or number(named['rom_file_offset']) != offset or number(source['rom_bus_address']) != offset + 0x08000000:
			raise ValueError(f'Address mismatch at {gid}')
		raw = bytes.fromhex(source['raw_hex'])
		if len(raw) != STRIDE:
			raise ValueError(f'Record length mismatch at {gid}')
		for p in range(STRIDE):
			if number(source[f'byte_{p:02X}']) != raw[p]:
				raise ValueError(f'Byte mismatch at {gid}:{p:02X}')
		for p in range(0, STRIDE, 2):
			if number(source[f'word_le_{p:02X}']) != int.from_bytes(raw[p:p+2], 'little'):
				raise ValueError(f'Word mismatch at {gid}:{p:02X}')
		if number(source['base_attack']) != raw[0x22] or number(named['base_attack']) != raw[0x22] or not named['name'].strip() or not named['name_source'].strip():
			raise ValueError(f'Base/name mismatch at {gid}')
		type_byte = raw[0x27] & 15
		row = dict(gimmick_id=gid, english_name=named['name'], name_source=named['name_source'],
			rom_file_offset=f'0x{offset:08X}', rom_bus_address=f'0x{offset+0x08000000:08X}',
			base_attack=raw[0x22], upgrade_cap=raw[0x23], record_type=type_byte,
			post_subtraction_gate_bit7=raw[0x27] >> 7)
		words = []
		for slot, p in enumerate(OFFSETS, 1):
			word = int.from_bytes(raw[p:p+2], 'little')
			if number(named[f'raw_word_{p:02X}']) != word:
				raise ValueError(f'Named/raw disagreement at {gid}:{p:02X}')
			words.append(word)
			percent, work72, work71 = decode_pair(word, type_byte)
			prefix = f'difficulty_{slot}' if slot <= 7 else f'slot_{slot}'
			row.update({f'{prefix}_raw_u16': word, f'{prefix}_percent': percent,
				f'{prefix}_aux_raw': word >> 8, f'{prefix}_loader_work72': work72,
				f'{prefix}_loader_work71': work71,
				f'{prefix}_menu_attack_upgrade0': menu_attack(raw[0x22], 0, percent)})
		row.update(auxiliary_decode='nibbles' if type_byte in (1, 2) else 'low7',
			auxiliary_gameplay_meaning='', slots_8_9_reachability='Unresolved',
			formula_class='M1_all_IDs; B1_conditional_path_only',
			upgrade_interaction='M1: base+upgrade before percent; U1: byte-wrap then cap; battle source unresolved',
			battle_damage='', confidence='Confirmed static',
			runtime_confirmation='Gear-Yo D1 U0 displayed 26 only' if gid == 1 else '',
			evidence_refs=f'T1;M1;L1;D1;B1;U1;R{gid:02d}' + (';GY1' if gid == 1 else ''))
		results.append(row)
	return results


def convert(input_path, names_path, output_path):
	rows = build_rows(read_csv(input_path), read_csv(names_path))
	# Exclusive creation also prevents aliases to either input from being overwritten.
	with Path(output_path).open('x', encoding='utf-8', newline='') as handle:
		writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
		writer.writeheader()
		writer.writerows(rows)
	return len(rows)


class SyntheticTests(unittest.TestCase):
	def test_packed_decoding(self):
		self.assertEqual(decode_pair(0xAB7C, 1), (124, 11, 10))
		self.assertEqual(decode_pair(0xAB7C, 2), (124, 11, 10))
		self.assertEqual(decode_pair(0xAB7C, 0), (124, 43, 0))
		self.assertEqual(decode_pair(0x007C, 0), (124, 0, 0))

	def test_scaling_and_upgrade(self):
		self.assertEqual(menu_attack(21, 0, 124), 26)
		self.assertEqual(menu_attack(21, 1, 124), 27)
		self.assertEqual(menu_attack(21, 3, 124), 29)
		self.assertEqual(menu_attack(255, 255, 255), 1300)
		self.assertEqual(upgrade_after(49, 5, 50), 50)
		self.assertEqual(upgrade_after(254, 5, 50), 3)
		with self.assertRaises(ValueError):
			decode_pair(65536, 0)

	def test_validation_and_exclusive_output(self):
		raw_rows, names = [], []
		for i in range(COUNT):
			raw = bytearray(STRIDE)
			raw[0x22], raw[0x28], raw[0x29] = 21, 124, 0xAB
			offset = TABLE + i * STRIDE
			source = dict(gimmick_id=str(i+1), record_index=str(i), rom_file_offset=str(offset),
				rom_bus_address=str(offset+0x08000000), base_attack='21', raw_hex=raw.hex())
			source.update({f'byte_{p:02X}': str(b) for p, b in enumerate(raw)})
			source.update({f'word_le_{p:02X}': str(int.from_bytes(raw[p:p+2], 'little')) for p in range(0, STRIDE, 2)})
			named = dict(gimmick_id=str(i+1), name=f'Synthetic {i+1}', name_source='synthetic', rom_file_offset=str(offset), base_attack='21')
			named.update({f'raw_word_{p:02X}': source[f'word_le_{p:02X}'] for p in OFFSETS})
			raw_rows.append(source)
			names.append(named)
		self.assertEqual(len(build_rows(raw_rows, names)), 50)
		for field, bad in [('gimmick_id', '2'), ('rom_file_offset', '0'), ('byte_28', '1'), ('word_le_28', '1'), ('base_attack', '0'), ('raw_hex', '00')]:
			with self.subTest(field=field):
				altered = [dict(row) for row in raw_rows]
				altered[0][field] = bad
				with self.assertRaises(ValueError):
					build_rows(altered, names)
		with self.assertRaises(ValueError):
			build_rows(raw_rows[:-1], names)
		with tempfile.TemporaryDirectory() as directory:
			paths = [Path(directory)/name for name in ('raw.csv', 'names.csv', 'out.csv')]
			for path, rows in zip(paths, (raw_rows, names)):
				with path.open('x', newline='', encoding='utf-8') as handle:
					writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
					writer.writeheader()
					writer.writerows(rows)
			self.assertEqual(convert(*paths), 50)
			before = paths[2].read_bytes()
			with self.assertRaises(FileExistsError):
				convert(*paths)
			self.assertEqual(paths[2].read_bytes(), before)


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--input', help='Existing gimmicks_raw.csv')
	parser.add_argument('--names', help='Existing gimmicks_named_complete.csv')
	parser.add_argument('--output', help='Fresh CSV path; parent must exist')
	parser.add_argument('--self-test', action='store_true')
	args = parser.parse_args()
	if args.self_test:
		result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticTests))
		raise SystemExit(0 if result.wasSuccessful() else 1)
	if not all((args.input, args.names, args.output)):
		parser.error('--input, --names and --output are required for conversion')
	print(f'Wrote {convert(args.input, args.names, args.output)} records; no ROM opened.')


if __name__ == '__main__':
	main()
