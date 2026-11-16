# Read-only ROM analysis

Run from the workspace root with Python 3.10 or later:

```powershell
python tools/analyze/verify_gimmick_roms.py
```

The script recursively discovers `.gba` inputs. If selection is ambiguous or filenames change, pass the located paths explicitly:

```powershell
python tools/analyze/verify_gimmick_roms.py --japanese 'path/to/japanese.gba' --english 'path/to/english.gba'
```

It reads input binaries, fingerprints both ROMs and the translation toolkit, compares the 50-record Gimmick window, checks loader literals/instructions against a limited ASM subset, and walks Choo-Choo RLE packet metadata without exporting graphics. It does not run the translation build or install packages.

Outputs:

- `reverse_engineering/rom_verification.md`: hashes, exact differences, source checks, hex/instruction listings and tooling observations.
- `reverse_engineering/data/gimmick_raw_fields.csv`: 100 rows, all 54 non-text bytes per record, little-endian word views, names annotated from the translation manifest, and difference metadata.

Byte-column names describe offsets rather than inferred power/difficulty meanings. Names and expected loader IDs are source annotations; they are not runtime observations.

`thumb_inspect.py` is an importable, limited ARMv4T Thumb instruction inspector used by the report generator. Call `inspect(rom_bytes, start_offset, end_offset, excluded_intervals)` to inspect another bounded region. The caller must distinguish code from literal pools/data. It is not a full ARM/GBA disassembler, emulator or control-flow analyser.

The scripts only write the report and CSV beneath `reverse_engineering/`, reject input/output aliases, and verify ROM hashes, sizes and modification timestamps plus the toolkit fingerprint after analysis. No third-party Python dependency is required. Generated data stays local; these scripts do not publish or commit ROM contents.
