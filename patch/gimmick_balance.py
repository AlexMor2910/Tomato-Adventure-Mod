"""Strict CSV patcher for the fingerprinted English Tomato Adventure ROM."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
SOURCE_SHA256 = "8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde"
ROM_SIZE = 0x800000
TABLE = 0x62C250
STRIDE = 0x58
FIELDS = {"base_attack": 0x22}
COLUMNS = ["gimmick_id", "name", "field", "expected_original", "new_value"]
# Documented ID/name mapping: reverse_engineering/symbols.md, records 0..49.
NAMES = (
    "Gear-Yo", "Kendama", "Chomper", "Origami", "Shell Fist", "TwinDragon",
    "RabiShoes", "Bunny Hop", "Cupid Bow", "Judgment", "Electric Eel", "SlotZooka",
    "Seed Bomb", "Momotaro", "Mag-Mitt", "A-B Glove", "Tail Wag", "Dragonfire",
    "Fumigator", "Bee Gatling", "Super Fan", "Cyclooka", "Zap Drum", "Popocon",
    "Yokozuna", "Flame Doll", "Erupter", "Pyramet", "SneaKar", "Choo-Choo",
    "Puffer", "UFO-Cast", "Spider Gun", "Rocket Pak", "Sun Beam", "Bouncer",
    "Firehog", "SesameTop", "NanaBoard", "BowlingRice", "Dojo Pup", "Lucky Cat",
    "Pop Horn", "Fart Horn", "Love Song", "StarScope", "Hotafant", "Mansnow",
    "ShuriGun", "Shadowreel",
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def integer(text):
    if not re.fullmatch(r"(?:[0-9]+|0[xX][0-9a-fA-F]+)", text):
        raise ValueError(f"Invalid unsigned integer: {text!r}")
    return int(text, 16 if text.lower().startswith("0x") else 10)


def parse_csv(data):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), strict=True)
    if reader.fieldnames != COLUMNS:
        raise ValueError(f"CSV header must be {','.join(COLUMNS)}")
    entries, offsets = [], set()
    for row in reader:
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise ValueError(f"Malformed CSV row {reader.line_num}")
        row = {k: v.strip() for k, v in row.items()}
        gid = integer(row["gimmick_id"])
        if not 1 <= gid <= 50 or row["name"] != NAMES[gid - 1]:
            raise ValueError(f"Invalid ID/name at row {reader.line_num}")
        field = row["field"]
        if field not in FIELDS:
            raise ValueError(f"Unsupported field: {field}")
        old, new = integer(row["expected_original"]), integer(row["new_value"])
        if not 0 <= old <= 255 or not 0 <= new <= 255 or old == new:
            raise ValueError("Values must be distinct unsigned bytes")
        offset = TABLE + (gid - 1) * STRIDE + FIELDS[field]
        if offset in offsets:
            raise ValueError(f"Duplicate/conflicting edit at {offset:#x}")
        offsets.add(offset)
        entries.append(dict(gimmick_id=gid, name=row["name"], field=field,
                            expected_original=old, new_value=new, file_offset=offset,
                            bus_address=offset + 0x08000000, record_index=gid - 1))
    if not entries:
        raise ValueError("CSV has no modifications")
    return sorted(entries, key=lambda e: e["file_offset"])


def verify_differences(source, output, entries):
    if len(source) != len(output):
        raise ValueError("Output size changed")
    actual = [i for i, (a, b) in enumerate(zip(source, output)) if a != b]
    expected = sorted(e["file_offset"] for e in entries)
    if actual != expected or any(output[e["file_offset"]] != e["new_value"] for e in entries):
        raise ValueError("Output differences do not match the patch plan")
    return actual


def apply_entries(source, entries):
    """Pure byte editing; caller must enforce the production ROM fingerprint."""
    seen = set()
    for e in entries:
        offset = e["file_offset"]
        gid = e["gimmick_id"]
        if (not 1 <= gid <= 50 or e["field"] not in FIELDS or
                offset != TABLE + (gid - 1) * STRIDE + FIELDS[e["field"]] or
                offset in seen or not 0 <= offset < len(source) or
                not 0 <= e["new_value"] <= 255 or e["expected_original"] == e["new_value"]):
            raise ValueError("Invalid or overlapping patch plan")
        seen.add(offset)
        if source[offset] != e["expected_original"]:
            raise ValueError(f"Expected byte mismatch at {offset:#x}")
    if not seen:
        raise ValueError("Empty patch plan")
    output = bytearray(source)
    for e in entries:
        output[e["file_offset"]] = e["new_value"]
    output = bytes(output)
    verify_differences(source, output, entries)
    return output


def plan(source, csv_data):
    if len(source) != ROM_SIZE or digest(source) != SOURCE_SHA256:
        raise ValueError("Input must match the established original English ROM size and SHA-256")
    entries = parse_csv(csv_data)
    output = apply_entries(source, entries)
    manifest = dict(schema_version=1, profile="tomato-english-1", source_sha256=digest(source),
                    csv_sha256=digest(csv_data), output_sha256=digest(output),
                    source_size=len(source), output_size=len(output), patch_entries=entries,
                    verification=dict(source_fingerprint=True, expected_bytes=True,
                                      exact_differences=True, difference_count=len(entries)),
                    runtime_status="not verified by this tool")
    return output, manifest


def write_outputs(source, output, manifest, directory):
    """Reserve a new directory; never reuse or overwrite an existing artifact."""
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "balanced.gba").open("xb") as f:
        f.write(output)
    readback = (directory / "balanced.gba").read_bytes()
    verify_differences(source, readback, manifest["patch_entries"])
    if digest(readback) != manifest["output_sha256"]:
        raise ValueError("Output readback hash mismatch")
    manifest = dict(manifest, output_readback_verified=True)
    with (directory / "manifest.json").open("x", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, default=ROOT / "Tomato Adventure (Japan) (patched).gba")
    parser.add_argument("--csv", type=Path, default=ROOT / "data/gimmick_balance.csv")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Default: validate and preview; create no files")
    mode.add_argument("--apply", action="store_true", help="Create a new ignored ROM and manifest")
    parser.add_argument("--output-name", help="New subdirectory name within tools/patch/output")
    args = parser.parse_args(argv)
    try:
        source = args.rom.read_bytes()
        output, manifest = plan(source, args.csv.read_bytes())
        print(f"Source SHA-256: {manifest['source_sha256']}")
        for e in manifest["patch_entries"]:
            print(f"ID {e['gimmick_id']} {e['name']} {e['field']}: {e['expected_original']} -> {e['new_value']} "
                  f"file {e['file_offset']:#010x}, bus {e['bus_address']:#010x}")
        print(f"Verified differences: {len(manifest['patch_entries'])}")
        print(f"Output SHA-256: {manifest['output_sha256']}")
        if args.apply:
            name = args.output_name or "balance-" + uuid.uuid4().hex
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
                raise ValueError("Output name must be a simple alphanumeric directory name")
            directory = OUTPUT_ROOT / name
            if digest(args.rom.read_bytes()) != manifest["source_sha256"]:
                raise ValueError("Input changed during validation")
            write_outputs(source, output, manifest, directory)
            print(f"Output directory: {directory}")
        else:
            print("DRY RUN: no files created")
        return 0
    except (OSError, ValueError, csv.Error, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
