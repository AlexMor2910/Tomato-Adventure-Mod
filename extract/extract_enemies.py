"""Read-only Tomato Adventure enemy export (English baseline only).

Uses the authoritative NAMES block in the translation ZIP to define IDs 0x00..0xB5.
ATK and susceptibility are deliberately not decoded without evidence.
"""
import argparse
import csv
import hashlib
import re
import os
import struct
import zipfile

EXPECTED_SHA256 = '8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde'
TABLE_OFFSET = 0x00634F50
STRIDE = 0x4C
LAST_ID = 0xB5


def parse_names(archive):
    candidates = [name for name in archive.namelist() if name.endswith('/ta_enemies_eng.txt') or name == 'ta_enemies_eng.txt']
    if len(candidates) != 1:
        raise ValueError('Exactly one ta_enemies_eng.txt is required in the ZIP')
    content = archive.read(candidates[0]).decode('utf-8-sig')
    section = content.split('NAMES:', 1)
    if len(section) != 2 or 'ATTACKS:' not in section[1]:
        raise ValueError('Missing NAMES or ATTACKS delimiter')
    names_part = section[1].split('ATTACKS:', 1)[0]
    pairs = re.findall(r'^([0-9A-Fa-f]{2})-E:(.*)$', names_part, re.MULTILINE)
    names = {}
    for key, value in pairs:
        enemy_id = int(key, 16)
        if enemy_id in names:
            raise ValueError(f'Duplicate enemy ID {key}')
        names[enemy_id] = value.strip()
    if set(names) != set(range(LAST_ID + 1)):
        raise ValueError('Enemy names are not contiguous from 00 to B5')
    if any(not value for value in names.values()):
        raise ValueError('Empty enemy name found')
    return names


def read_records(rom, names):
    minimum = TABLE_OFFSET + (LAST_ID + 1) * STRIDE
    if len(rom) < minimum:
        raise ValueError(f'ROM too short for last named enemy record: need at least {minimum:#x} bytes')
    rows = []
    raw_rows = []
    for enemy_id in range(LAST_ID + 1):
        offset = TABLE_OFFSET + enemy_id * STRIDE
        block = rom[offset:offset + STRIDE]
        hp_raw = struct.unpack_from('<H', block, 0x0A)[0]
        defense = struct.unpack_from('<H', block, 0x0E)[0]
        rows.append({'enemy_id': enemy_id, 'enemy_id_hex': f'0x{enemy_id:02X}', 'english_name': names[enemy_id], 'record_file_offset': f'0x{offset:08X}', 'record_bus_address': f'0x{offset + 0x08000000:08X}', 'hp': hp_raw & 0x7FFF, 'hp_high_bit': hp_raw >> 15, 'base_mitigation': defense, 'atk': '', 'susceptibility': '', 'atk_status': 'unresolved', 'susceptibility_status': 'unresolved'})
        raw = {'enemy_id': enemy_id, 'english_name': names[enemy_id], 'record_file_offset': f'0x{offset:08X}', 'record_hex': block.hex(' ')}
        raw.update({f'u8_{i:02X}': block[i] for i in range(STRIDE)})
        raw.update({f'u16le_{i:02X}': struct.unpack_from('<H', block, i)[0] for i in range(0, STRIDE, 2)})
        raw_rows.append(raw)
    return rows, raw_rows


def write_new_csv(path, rows):
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    with open(path, 'x', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, help='Unmodified English baseline .gba')
    parser.add_argument('--translation-zip', required=True, help='tomatotrans-1.1.1.zip')
    parser.add_argument('--output', required=True, help='New enemies.csv output path')
    parser.add_argument('--raw-output', help='Optional new enemies_raw.csv output path')
    args = parser.parse_args()
    output_paths = [args.output] + ([args.raw_output] if args.raw_output else [])
    if len({os.path.abspath(path) for path in output_paths}) != len(output_paths):
        parser.error('Output paths must be different')
    if any(os.path.exists(path) for path in output_paths):
        parser.error('Output file already exists; refusing to overwrite')
    with open(args.rom, 'rb') as stream:
        rom = stream.read()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED_SHA256:
        parser.error(f'ROM SHA-256 mismatch: {digest}; expected {EXPECTED_SHA256}')
    with zipfile.ZipFile(args.translation_zip) as archive:
        names = parse_names(archive)
    records, raw_records = read_records(rom, names)
    write_new_csv(args.output, records)
    if args.raw_output:
        write_new_csv(args.raw_output, raw_records)


if __name__ == '__main__':
    main()
