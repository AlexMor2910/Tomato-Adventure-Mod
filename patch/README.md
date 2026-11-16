# CSV Gimmick Balancing Patcher

Run from the repository root using Python's standard library. This tool is independent of the translation toolkit; it does not run its build or modify its sources.

```powershell
python tools/patch/gimmick_balance.py --dry-run
python tools/patch/gimmick_balance.py --apply
python -m unittest discover -s tests -p test_gimmick_balance.py
```

Dry run is the default and creates no files. `--apply` creates `balanced.gba` and `manifest.json` in a new UUID directory under Git-ignored `tools/patch/output/`. Use `--output-name my-experiment` for a reproducible directory name; an existing directory is rejected, never overwritten. Names cannot contain paths. `--rom PATH` and `--csv PATH` select inputs; the ROM fingerprint gate cannot be disabled through the command line. Outputs do not configure or launch mGBA.

## CSV and address convention

[gimmick_balance.csv](../../data/gimmick_balance.csv) contains only the validated Gear-Yo example:

```csv
gimmick_id,name,field,expected_original,new_value
1,Gear-Yo,base_attack,21,22
```

IDs are **one-based runtime IDs 1..50**, not zero-based record indices. Gear-Yo ID 1 maps to record index 0. The tool supports the 50 ID/name mappings documented in `reverse_engineering/symbols.md`; it rejects mismatched names. Supporting an ID is not runtime validation of that Gimmick's balance.

The only allowed field is `base_attack`, a one-byte unsigned value at +0x22. File offset is `0x0062C250 + (gimmick_id-1)*0x58 + 0x22`; bus address adds `0x08000000`. Integers accept decimal or explicit `0x` hexadecimal. Values must be 0..255; this structural range is not a gameplay safety guarantee. Header order is exact. Duplicate/conflicting edits, unknown fields, bad IDs/names, missing/extra cells, empty plans, no-op rows and unexpected original bytes are rejected before creating any output.

## Verification and reproducibility

The input must be the 8,388,608-byte English ROM with SHA-256 `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`. Already patched inputs are rejected. All rows are validated against the untouched source, sorted by offset, then applied to a memory copy. A full comparison verifies unchanged length and exactly the planned offsets/new values. Written output is read back and checked again.

The manifest records profile/schema version, source/CSV/output hashes and sizes, ID/name/field, old/new values, record index, file/bus addresses, and verification results. No timestamps or UUIDs affect ROM bytes; identical inputs produce identical output and manifest content. CSV row ordering does not affect ROM bytes, though it changes the CSV hash. Failed writes may leave a partial new directory; it will not be reused or labeled verified. Choose another fresh name after resolving an error.

Synthetic tests exercise all 50 addresses, rejection paths, expected-byte assertions, exact-difference checks, deterministic results, output collisions and dry-run isolation. Test-only overrides of the synthetic size/hash are never exposed by the production CLI. The real-ROM validation reproduces the existing Gear-Yo experiment byte-for-byte; see [the recorded dry run](../../reverse_engineering/experiments/gimmick_balance_dry_run.md).

## Extending safely

Before adding a field, document its offset, width, signedness, encoding, original/English layout and actual consumers through bounded disassembly and runtime tests. Add it to a reviewed field allowlist with field-specific constraints and overlap detection; do not accept arbitrary CSV addresses. Wider/packed fields require explicit endian encoding or masks that preserve unrelated bits, plus corresponding tests. Keep pointers/text/relocated assets outside this initial balance tool. Add ROM profiles only for independently fingerprinted layouts.

Introduce one evidence-backed change at a time, using separate A/B outputs, logs, saves and checkpoint copies. Recalculate restored caches before comparing menus. Validate other difficulties, upgrades, minigame outcomes, targets/status effects and clamps before combining changes. The tool verifies bytes, not gameplay safety or runtime success. No changes beyond Gear-Yo 21→22 are included.
