import argparse
import csv
import os

COUNT = 50
STRIDE = 0x58
TABLE_OFFSET = 0x0062C250
COEFFICIENT_OFFSETS = tuple(range(0x28, 0x3A, 2))


def to_integer(value, description):
    try:
        return int(value, 0) if value.lower().startswith("0x") else int(value)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid {description}: {value!r}") from exc


def convert(source_csv, destination_csv):
    with open(source_csv, "r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"gimmick_id", "record_index", "rom_file_offset", "rom_bus_address", "base_attack", "raw_hex"}
        required.update(f"byte_{i:02X}" for i in range(STRIDE))
        required.update(f"word_le_{i:02X}" for i in COEFFICIENT_OFFSETS)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required raw CSV columns: {sorted(missing)}")
        source_rows = list(reader)

    if len(source_rows) != COUNT:
        raise ValueError(f"Expected {COUNT} Gimmick records, received {len(source_rows)}")

    results = []
    for index, record in enumerate(source_rows):
        gimmick_id = to_integer(record["gimmick_id"], "Gimmick ID")
        rom_offset = TABLE_OFFSET + index * STRIDE
        if gimmick_id != index + 1 or to_integer(record["record_index"], "record index") != index:
            raise ValueError(f"Incorrect ordering or identifier in source row {index + 1}")
        if to_integer(record["rom_file_offset"], "ROM file offset") != rom_offset or to_integer(record["rom_bus_address"], "ROM bus address") != 0x08000000 + rom_offset:
            raise ValueError(f"Incorrect addresses for Gimmick {gimmick_id}")
        try:
            raw = bytes.fromhex(record["raw_hex"])
        except ValueError as exc:
            raise ValueError(f"Invalid raw hex for Gimmick {gimmick_id}") from exc
        if len(raw) != STRIDE:
            raise ValueError(f"Incorrect raw record length for Gimmick {gimmick_id}")
        for byte_index, byte_value in enumerate(raw):
            if to_integer(record[f"byte_{byte_index:02X}"], "byte") != byte_value:
                raise ValueError(f"Raw/byte mismatch at Gimmick {gimmick_id}, +0x{byte_index:02X}")
        if to_integer(record["base_attack"], "base attack") != raw[0x22]:
            raise ValueError(f"Attack mismatch for Gimmick {gimmick_id}")

        row = {"gimmick_id": gimmick_id, "name": "Gear-Yo" if gimmick_id == 1 else "", "rom_file_offset": f"0x{rom_offset:08X}", "base_attack": raw[0x22], "confirmed_max_attack": "", "difficulty_scaling_status": "candidate; see notes"}
        for j, offset in enumerate(COEFFICIENT_OFFSETS, start=1):
            value = int.from_bytes(raw[offset:offset + 2], "little")
            if to_integer(record[f"word_le_{offset:02X}"], "scaling coefficient") != value:
                raise ValueError(f"Word mismatch for Gimmick {gimmick_id}, +0x{offset:02X}")
            row[f"candidate_coefficient_{j}"] = value
        if gimmick_id == 1 and row["candidate_coefficient_1"] != 124:
            raise ValueError("Gear-Yo control value does not match known coefficient 124")
        results.append(row)

    columns = ["gimmick_id", "name", "rom_file_offset", "base_attack", "confirmed_max_attack", "difficulty_scaling_status"]
    columns += [f"candidate_coefficient_{j}" for j in range(1, len(COEFFICIENT_OFFSETS) + 1)]
    destination_directory = os.path.dirname(os.path.abspath(destination_csv))
    os.makedirs(destination_directory, exist_ok=True)
    with open(destination_csv, "x", encoding="utf-8-sig", newline="") as dest:
        writer = csv.DictWriter(dest, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    return len(results)


def main():
    parser = argparse.ArgumentParser(description="Convert an existing raw Gimmick CSV into a concise CSV without modifying ROMs.")
    parser.add_argument("--input", default="extracted_data/gimmicks_raw.csv", help="Existing raw CSV path")
    parser.add_argument("--output", default="extracted_data/gimmicks.csv", help="New CSV path; refuses overwrite")
    args = parser.parse_args()
    count = convert(args.input, args.output)
    print(f"Wrote {count} rows to {args.output}; coefficient columns remain candidates.")


if __name__ == "__main__":
    main()
