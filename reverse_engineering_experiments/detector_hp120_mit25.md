# Detector HP 120 / base mitigation 25 experiment

Approved implementation, 2026-10-15. **Confirmed static build and independent
readback; runtime UNTESTED.** No emulator or Ghidra was launched. No saves,
savestates, RAM, translation sources, other enemy records or existing ROMs changed.

## Approved scope and rationale

Reduce Detector A5 durability to lessen ordinary-encounter fatigue while keeping
Annoying Siren and all other mechanics. Rattlin' Dragon 9C deliberately remains
262 HP / 54 base mitigation. Kaizo is complete and its existing bytes are preserved.
Mayonen/Namp Hawker placement remains deferred, the final major objective.

This changes the shared Detector species record, so it applies wherever enemy A5
is instantiated, not only when the current map is Gimmick Palace. No map-specific
condition, formation, placement or encounter-rate change is introduced.

## Source and new output

Preserved input:
`tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba`

Input SHA-256:
`7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`.

New experimental ROM:
`tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`

Output SHA-256:
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.

Both are 16,777,216 bytes. This is a separate derived gameplay ROM; it does not
overwrite or replace the preserved input. The output directory is ignored by the
existing patch-output policy. No copyrighted ROM is committed or distributed.

## Exact verified changes

| Detector field | Record offset | ROM bus | File offset | Retail/source LE bytes | Experimental LE bytes | Decimal |
|---|---|---|---|---|---|---|
| Maximum HP | +0A | `08638056` | `00638056` | `87 00` | `78 00` | 135 -> 120 |
| Base defense/mitigation | +0E | `0863805A` | `0063805A` | `26 00` | `19 00` | 38 -> 25 |

Both are uint16 little-endian fields in Detector's record at bus `0863804C`,
file `0063804C` (`08634F50 + A5*4C`). The upper bytes remain zero: exactly
**two actual bytes differ**, although the reproducible patch writes two complete
halfword fields. HP flag bit 8000 remains clear.

Evidence: `gimmick_palace_enemy_research.md` and
`gimmick_palace_enemy_evidence.json` retain the original stat values and verified
field addresses. `080482CC-080482DC` reads record +0A, masks 7FFF and initializes
current/maximum battle HP. `080482E4-080482E8` reads record +0E and stores battle
target +14. The builder verifies the exact source loader instructions as context.
The earlier damage trace establishes this as base mitigation for its subtraction
path; dynamic modifiers or other Gimmick paths may produce different effective
defense. This does not claim a universal scalar defense calculation.

Rattlin' Dragon's **entire 4C-byte record** at bus `08637DA0` / file `00637DA0`
matches the input. Its HP field `08637DAA` is `06 01` = 262; mitigation field
`08637DAE` is `36 00` = 54. All 181 other known enemy records match the source.

## Verification results

- Source SHA-256, size, original field bytes, research row and loader context: PASS.
- Full 16 MiB before/after comparison: PASS; only files 00638056 and 0063805A differ.
- Independent verifier used fresh file reads and standard-library code without
  importing the patcher: HP 120, mitigation 25, exact two-byte diff, output hash PASS.
- All other Detector bytes, including attacks, AI pointers, palette/graphics,
  rewards and other statistics: unchanged by exhaustive full-file diff.
- Every other byte, including all formations, placements, scripts, original
  translation, existing gameplay changes and Rattlin' Dragon: unchanged.
- GBA header bytes 00000000..000000BF: identical. Header complement calculated as
  `(-sum(bytes[A0:BD])-19)&FF` remains valid at C4. Neither field is in the header
  checksum region; **no checksum adjustment was necessary or made**. External
  SHA-256 necessarily changes and is recorded above.
- All 42 selected preexisting ROM/save/checkpoint artifacts in the build's
  protection inventory retain their hashes. This is a scoped protection audit,
  not a claim to have inventoried every workspace artifact.
- Three rejection checks PASS: wrong ROM size, wrong source hash, unexpected
  additional output byte. New output directories and files use exclusive creation.

Build manifest and independent evidence are adjacent to the new ROM:
`manifest.json`, `independent_verification.json`. Historical construction and
research ledgers are not retroactively presented as runtime evidence.

## Reproduction and limits

Read-only preflight:
`python -B tools/patch/detector_rebalance.py`

Create the same bytes in a fresh directory:
`python -B tools/patch/detector_rebalance.py --apply`

Optional `--output-name NEW_NAME` accepts only a plain safe directory name and
refuses an existing directory. The source hash cannot be overridden. No manual
hex edit or translation rebuild is required. The patcher never operates an emulator.

Runtime combat pacing, HP initialization in an actual battle, effective damage,
Annoying Siren behavior, battle completion and save/reload are **UNTESTED** for
this new ROM. Any later user-operated check should enter a fresh battle: a state
captured during an existing battle can retain previously initialized HP/mitigation.
Do not edit a state or live RAM to make it match the ROM. Preserve checkpoint/save
isolation and use the user-operated debugger workflow if later requested.
