import argparse
import csv
import re
import zipfile
from pathlib import Path

TRANSLATION_MEMBER = 'tomatotrans-1.1.1/ta_menus_eng.txt'
BLOCK_HEADER = 'RESTRUCT 62C250 08 58 7F001E 10 40 32'
NAME_LINE = re.compile(r'^([0-9A-Fa-f]{2})-E:(.*)$')


def load_names(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        lines = archive.read(TRANSLATION_MEMBER).decode('utf-8-sig').splitlines()
    headers = [i for i, line in enumerate(lines) if line.strip().upper() == BLOCK_HEADER]
    if len(headers) != 1:
        raise ValueError(f'Expected one Gimmick name table, found {len(headers)}')
    names = {}
    for line in lines[headers[0] + 1:]:
        if not line.strip():
            continue
        match = NAME_LINE.fullmatch(line.strip())
        if not match:
            break
        gimmick_id = int(match.group(1), 16) + 1
        if gimmick_id in names:
            raise ValueError(f'Duplicate ID: {gimmick_id}')
        names[gimmick_id] = match.group(2).strip()
    if set(names) != set(range(1, 51)) or any(not name for name in names.values()):
        raise ValueError('Translation name table does not contain 50 nonempty consecutive names')
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--translation-zip', required=True)
    parser.add_argument('--source-csv', required=True)
    parser.add_argument('--output-csv', default='gimmicks_named_complete.csv')
    args = parser.parse_args()
    names = load_names(args.translation_zip)
    with open(args.source_csv, newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        fields = reader.fieldnames
        if not fields or 'gimmick_id' not in fields or 'name' not in fields:
            raise ValueError('Source CSV requires gimmick_id and name columns')
        rows = list(reader)
    if len(rows) != 50 or {int(row['gimmick_id']) for row in rows} != set(range(1, 51)):
        raise ValueError('Source CSV must have exactly the 50 unique Gimmick IDs')
    for row in rows:
        gimmick_id = int(row['gimmick_id'])
        old_name = row['name'].strip()
        if old_name and old_name != names[gimmick_id]:
            raise ValueError(f'Existing name conflict at ID {gimmick_id}: {old_name} vs {names[gimmick_id]}')
        row['name'] = names[gimmick_id]
        if 'name_source' in row:
            row['name_source'] = 'English translation: ta_menus_eng.txt RESTRUCT 62C250 (ID=index+1)'
    output = Path(args.output_csv)
    with output.open('x', newline='', encoding='utf-8-sig') as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} named Gimmicks to {output}')


if __name__ == '__main__':
    main()