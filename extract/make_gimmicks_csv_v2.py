import argparse
import csv
import os

TABLE_OFFSET = 0x0062C250
STRIDE = 0x58
COUNT = 50
WORD_OFFSETS = tuple(range(0x28, 0x3A, 2))

# Confirmed/documented name-to-ID mappings in session handoffs 3 and 6.
KNOWN_NAMES = {
    0x01: "Gear-Yo", 0x03: "Chomper", 0x05: "Shell Fist",
    0x09: "Cupid Bow", 0x0B: "Electric Eel", 0x0D: "Seed Bomb",
    0x11: "Tail Wag", 0x13: "Fumigator", 0x15: "Super Fan",
    0x17: "Zap Drum", 0x19: "Yokozuna", 0x1B: "Erupter",
    0x21: "Spider Gun", 0x23: "Sun Beam", 0x27: "NanaBoard",
    0x29: "Dojo Pup", 0x2B: "Pop Horn", 0x2D: "Love Song",
    0x2F: "Hotafant",
}


def parse_int(value):
    return int(value, 0) if value.lower().startswith("0x") else int(value)


def convert(source_path, output_path):
    with open(source_path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"gimmick_id", "record_index", "rom_file_offset", "base_attack", "raw_hex"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing columns: {sorted(required - set(reader.fieldnames or []))}")
        records = list(reader)
    if len(records) != COUNT:
        raise ValueError(f"Expected {COUNT} rows; received {len(records)}")

    rows = []
    for i, source in enumerate(records):
        gimmick_id = parse_int(source["gimmick_id"])
        offset = TABLE_OFFSET + i * STRIDE
        raw = bytes.fromhex(source["raw_hex"])
        if gimmick_id != i + 1 or parse_int(source["record_index"]) != i or parse_int(source["rom_file_offset"]) != offset or len(raw) != STRIDE:
            raise ValueError(f"ID, offset, or raw length mismatch at row {i + 1}")
        if parse_int(source["base_attack"]) != raw[0x22]:
            raise ValueError(f"Base attack mismatch at ID {gimmick_id}")
        words = [int.from_bytes(raw[p:p + 2], "little") for p in WORD_OFFSETS]
        plausible = all(100 <= x <= 300 for x in words)
        row = {
            "gimmick_id": gimmick_id,
            "name": KNOWN_NAMES.get(gimmick_id, ""),
            "name_source": "documented session handoff" if gimmick_id in KNOWN_NAMES else "unmapped",
            "rom_file_offset": f"0x{offset:08X}",
            "base_attack": raw[0x22],
            "max_attack": "",
            "difficulty_interpretation": "percentage-like candidate (unverified)" if plausible else "non-percentage-like encoding (unresolved)",
            "first_coefficient_runtime_verified": "yes (Gear-Yo, difficulty 1 / upgrade 0)" if gimmick_id == 1 and words[0] == 124 else "no",
        }
        row.update({f"raw_word_{p:02X}": value for p, value in zip(WORD_OFFSETS, words)})
        rows.append(row)

    output_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(output_dir, exist_ok=True)
    fields = list(rows[0])
    with open(output_path, "x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows), sum(bool(row["name"]) for row in rows), sum(row["difficulty_interpretation"].startswith("percentage-like") for row in rows)


def main():
    parser = argparse.ArgumentParser(description="Generate a sourced Gimmick statistics CSV from extracted raw records.")
    parser.add_argument("--input", default="extracted_data/gimmicks_raw.csv")
    parser.add_argument("--output", default="extracted_data/gimmicks_v2.csv")
    args = parser.parse_args()
    count, named, plausible = convert(args.input, args.output)
    print(f"Exported {count} records; {named} names documented; {plausible} percentage-like candidates. No ROM modified.")


if __name__ == "__main__":
    main()
