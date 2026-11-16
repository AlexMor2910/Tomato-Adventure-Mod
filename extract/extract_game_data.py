import argparse
import csv
import hashlib
import os
import struct

EXPECTED_SHA256 = "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde"
GIMMICK_TABLE_OFFSET = 0x0062C250
GIMMICK_COUNT = 50
GIMMICK_STRIDE = 0x58
BASE_ATTACK_OFFSET = 0x22


def extract_gimmicks(rom_path, output_path):
    with open(rom_path, "rb") as source:
        rom = source.read()

    actual_sha256 = hashlib.sha256(rom).hexdigest()
    if actual_sha256 != EXPECTED_SHA256:
        raise ValueError(f"Unexpected ROM SHA-256: {actual_sha256}. Expected the untouched English baseline. No CSV was written.")

    table_end = GIMMICK_TABLE_OFFSET + GIMMICK_COUNT * GIMMICK_STRIDE
    if len(rom) < table_end:
        raise ValueError(f"ROM is too small: needs at least {table_end} bytes; found {len(rom)}. No CSV was written.")

    columns = ["gimmick_id", "record_index", "rom_file_offset", "rom_bus_address", "base_attack", "raw_hex"]
    columns += [f"byte_{offset:02X}" for offset in range(GIMMICK_STRIDE)]
    columns += [f"word_le_{offset:02X}" for offset in range(0, GIMMICK_STRIDE, 2)]
    rows = []

    for index in range(GIMMICK_COUNT):
        offset = GIMMICK_TABLE_OFFSET + index * GIMMICK_STRIDE
        record = rom[offset:offset + GIMMICK_STRIDE]
        row = {"gimmick_id": index + 1, "record_index": index, "rom_file_offset": f"0x{offset:08X}", "rom_bus_address": f"0x{0x08000000 + offset:08X}", "base_attack": record[BASE_ATTACK_OFFSET], "raw_hex": record.hex(" ")}
        row.update({f"byte_{i:02X}": value for i, value in enumerate(record)})
        row.update({f"word_le_{i:02X}": struct.unpack_from("<H", record, i)[0] for i in range(0, GIMMICK_STRIDE, 2)})
        rows.append(row)

    output_directory = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_directory, exist_ok=True)
    if os.path.exists(output_path):
        raise FileExistsError(f"Output already exists: {output_path}. Choose a new path to prevent overwriting.")
    with open(output_path, "x", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), actual_sha256


def main():
    parser = argparse.ArgumentParser(description="Extract verified Gimmick records from the untouched English Tomato Adventure ROM.")
    parser.add_argument("--rom", required=True, help="Path to the unmodified English baseline .gba file")
    parser.add_argument("--output", default="extracted_data/gimmicks_raw.csv", help="Fresh output CSV path (must not already exist)")
    args = parser.parse_args()
    count, digest = extract_gimmicks(args.rom, args.output)
    print(f"Extracted {count} Gimmick records to {args.output}")
    print(f"Verified English baseline SHA-256: {digest}")


if __name__ == "__main__":
    main()