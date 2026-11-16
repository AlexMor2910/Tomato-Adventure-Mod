"""Compare manually observed values with ROM fields. Does not emulate gameplay."""
import argparse
import json
from pathlib import Path
from prepare_session import EXPECTED, ROOT, digest


def number(value):
	return int(value, 0)


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--id", type=number, required=True)
	parser.add_argument("--selector", type=number, required=True)
	parser.add_argument("--upgrade", type=number, required=True)
	parser.add_argument("--observed-unscaled", type=number, required=True)
	parser.add_argument("--observed-scaled", type=number, required=True)
	args = parser.parse_args()
	if not 1 <= args.id <= 50 or not 1 <= args.selector <= 9 or not 0 <= args.upgrade <= 255:
		raise SystemExit("Capture outside the documented record/selector/byte domain")
	rom_path = ROOT / "Tomato Adventure (Japan) (patched).gba"
	if digest(rom_path) != EXPECTED[rom_path.name]:
		raise SystemExit("Unexpected English ROM fingerprint")
	rom = rom_path.read_bytes()
	file_offset = 0x62C250 + (args.id - 1) * 0x58
	record = rom[file_offset:file_offset + 0x58]
	coefficient_offset = 0x28 + 2 * (args.selector - 1)
	unscaled = record[0x22] + args.upgrade
	scaled = unscaled * record[coefficient_offset] // 100
	result = dict(scope="comparison of user-supplied observations; not an automatic runtime verification",
		id=args.id, selector=args.selector, upgrade=args.upgrade,
		record_bus_address=hex(0x08000000 + file_offset), field_22=record[0x22], field_23=record[0x23],
		coefficient_bus_address=hex(0x08000000 + file_offset + coefficient_offset), coefficient=record[coefficient_offset],
		expected_unscaled=unscaled, expected_scaled=scaled,
		observed_unscaled=args.observed_unscaled, observed_scaled=args.observed_scaled,
		match=unscaled == args.observed_unscaled and scaled == args.observed_scaled)
	print(json.dumps(result, indent=2))


if __name__ == "__main__":
	main()
