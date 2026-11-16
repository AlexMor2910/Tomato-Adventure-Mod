# Gear-Yo Base Attack 22: Controlled Experiment

## Status and verified patch

2026-10-11. **Build verification passed; modification runtime-validated for the tested Gear-Yo conditions.** This is a proof of concept, not a finalized balance change. Only one data byte changes; no instructions, translation ASM/C++, other Gimmicks, saves or original checkpoints were modified.

Gear-Yo is record index **0**, runtime Gimmick ID **1**. Translation text `tomatotrans-1.1.1/ta_menus_eng.txt:1304` associates entry `00-E` with Gear-Yo. Prior loader/menu traces use ID minus one with stride `0x58`; the inspected Gear-Yo checkpoint's non-text work record uniquely matches original record 0. Original table remains at `0x0862C250` in the English ROM, although its display text is relocated. See [ROM verification](../rom_verification.md) and [battle trace](../battle_damage_candidates.md).

| Property | Verified value |
| --- | --- |
| Original record bus address | `0x0862C250` |
| Base Attack offset | `+0x22` |
| Patched bus address | `0x0862C272` |
| File offset (bus minus `0x08000000`) | `0x0062C272` |
| Original / experimental byte | `0x15` (21) / `0x16` (22) |
| ROM size, both versions | 8,388,608 bytes |
| Full-file differences | Exactly one, at `0x0062C272` |

Field evidence: menu calculation `0x08075970` reads original +0x22; battle `0x08048602..06` reads that byte and combines it with the battle additive input. Live baseline independently established menu Attack 26, battle pre-subtraction 26, target subtraction quantity 10, scratch 16, and HP 24→8. The quantity 10 is not named Defense. A separate byte-level read of both source ROMs confirmed `0x15` at the offset; a full output comparison independently confirmed the single difference.

| ROM | SHA-256 |
| --- | --- |
| Protected Japanese | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| Protected English / control A | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Experimental B | `5cd1cc5c70dce892476d5162d49e0e1552600d37087181f79d0cc4e3d8120a8f` |

## Reproducible build and isolated launch

From repository root:

```powershell
python tools/experiments/gearyo_attack_22.py
```

The standard-library script verifies both source hashes and the expected byte, changes a memory copy, checks exactly one difference, and exclusively creates a fresh UUID directory. It reads back each output and verifies protected ROM/save/state hashes and modification times. Existing outputs are never replaced. It copies the installed Qt executable, creates separate portable A/B configurations, and copies only the fingerprinted baseline checkpoints when available. It imports no battery save and launches no emulator during build. `verification.json` records results. Reruns produce identical ROM hashes in new directories.

Prepared directory: `reverse_engineering/experiments/testing/gearyo-281d1d7030904d5684c2ff29d3e90c1b/`. All generated files are excluded by `experiments/.gitignore` (`/testing/`); root `*.gba` exclusion also applies. Only script/documentation should be distributed.

Manual launches, one at a time:

```powershell
python reverse_engineering/experiments/testing/gearyo-281d1d7030904d5684c2ff29d3e90c1b/A/launch.py
python reverse_engineering/experiments/testing/gearyo-281d1d7030904d5684c2ff29d3e90c1b/B/launch.py
```

Each launch creates unique logs and verifies its session ROM before/after. Saves, states, screenshots, patches and cheats have separate A/B paths. `loadStateExtdata=9` excludes embedded savedata writeback; automatic patch/cheat directories are empty. Do not use the old baseline-only `start_session.py` for B: its hash gate intentionally accepts only the original English ROM.

## Checkpoint compatibility and limitations

Read-only inspection validates both baseline PNG states: menu SHA-256 `570e17c82b6d3592a0b003d991a33b6bf320c04ff7322a339e735f6c65280230`; battle `cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7`. The prepared A/B copies match. State version is `0x01000007`, title/code TOMATO_ADV/AGLJ. Original CRC32 is `a9bb7cd7`; experimental CRC32 is `3a0203f5`. Size, header, instruction bytes and memory layout are unchanged.

**Checkpoint reuse considerations:** [mGBA 0.10.5 serialization code](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/serialize.c) rejects incompatible game identity but only warns for a ROM CRC mismatch. It restores RAM. The expected different-version warning alone therefore does not require altering state headers or bypassing a loader. Stop if another load error appears. Loading a copied state does not make its cached RAM reflect the changed ROM.

Both checkpoints contain copied base 21 at `0x03003F56` and cached menu Attack 26 at `0x02014D02`. These are stale in B until producers run. Menu testing must close/reopen or otherwise refresh the menu and hit the calculation routine. The battle routine rereads original ROM +0x22, so the mid-minigame checkpoint is useful for a narrowly controlled damage comparison; display/work-copy data may remain stale. A later fresh battle should verify loader/UI consistency. Do not edit RAM or state files to refresh them.

## Controlled A/B procedure

1. Launch A, confirm its ROM path and isolated paths, pause and open the debugger. Use `listb`/`listw` and remove previous stops by actual IDs. Via **File → Load state file**, load A's copied `states/gimmick_menu.ss0`. Do not save over a copied checkpoint. Read `r/1 0x0862C272` (expect `0x15`).
2. Set `break 0x08075ABC`, `continue`, then close/reopen the Gear-Yo menu through normal input. At the hit record `status`, r0 (quotient), r5 (coefficient), r6 (ID), r7 (output pointer). Require difficulty 1, upgrade 0 and coefficient 124; step once and read the actual r7+0x0A. Resume a complete frame and record displayed Attack and a uniquely named screenshot. Baseline expectation: 26.
3. Remove that stop. Load A's copied battle checkpoint. Set `break 0x08048794`, continue and complete the minigame. Record r1 (26), r0 (10), target fields `0x03000A54`/+0x18 at `0x03000A58`, BAF byte `0x03000BAF`, record flag `0x0862C277`, and full status. Step twice; read `r/2 0x03000BF8` (16).
4. Delete the prior stop; set `break 0x08046E02` and continue. Record r4, r1, scratch, and HP at actual r4+0x0E before/after one step. Known target: `0x03000A40`, HP address `0x03000A4E`. Expected A: HP 24→8. Close A before launching B.
5. Repeat steps 1–4 in B using B's copied states. Capture the expected CRC warning. Require ROM read `0x16` and an actual fresh menu calculation hit; seeing the old cached 26 immediately after loading is not a failure. Keep selected ID/difficulty/upgrade, target, coefficient and action inputs matched. Record live battle inputs instead of assuming identical manual timing yields identical performance.
6. Predicted B menu: `floor(22*124/100)=27`. Predicted B battle, only with unchanged effective coefficient/additive inputs and target quantity 10: pre-subtraction 27, scratch/final damage 17, HP 24→7. Compare screenshots and raw register/memory captures. Record mismatches and stop; do not alter flags or registers to fit predictions.

For stronger comparability, optionally add a separate conditional stop at `0x08048754` to record the actual coefficient address/value and r2 unscaled input for both runs. Runtime success requires the changed ROM byte, fresh menu result/display, changed battle operand/scratch and corresponding HP delta. Repeat from a fresh loader/battle entry after the controlled replay. Save any new state under a new name inside its own A/B directory.

## Confirmed A/B results

**Confirmed (runtime), tested conditions only:** the user reports successful manual mGBA A/B testing of Gear-Yo at difficulty 1, upgrade 0, under the previously tested battle conditions. The one-byte change produced the predicted displayed Attack and battle damage. This is user-observed runtime evidence; no new raw console transcript, screenshots, coefficient-stage register dump or experimental HP before/after values were supplied in this report.

| Measurement | Original A | Experimental B | Status |
| --- | --- | --- | --- |
| Base / displayed Attack | 21 / 26 | 22 / 27 | Confirmed runtime by user |
| Battle damage | 16 | 17 | Confirmed runtime by user |
| ROM change | Original byte `0x15` | `0x16` at file `0x0062C272` | Exactly one changed byte, independently verified locally and reaffirmed by user |
| Battle pre-subtraction register | 26 confirmed in earlier baseline test | Not newly reported | Do not infer a captured register value from final damage |
| Target HP | 24 to 8 confirmed in earlier baseline test | 24 to 7 predicted, not newly reported | Experimental HP values remain uncaptured in this report |

The experiment is **runtime-validated for these tested conditions**. The displayed Attack increase from 26 to 27 and damage increase from 16 to 17 support the causal role of Gear-Yo's original-record +0x22 base byte in this menu/battle path. Existing patch script and ROM fingerprints remain unchanged. The build-time `verification.json` retains its original `untested` status as a historical artifact; this document records the subsequent live result.

## Limitations and follow-up

This validates the proof of concept, not a finalized balance recommendation. Other Gimmicks, difficulty levels, nonzero upgrades, minigame outcomes, enemies/targets, status effects, multiple-target actions, minimum-damage cases and knockout/clamp behavior remain untested. No RNG involvement or Defense interpretation is established. The observed damage increase does not guarantee every base-Attack increment adds one damage: integer rounding and conditional scaling can change the response.

Restored menu/work caches may still contain original values until refreshed. Fresh battle-entry/loader testing remains useful. The new report confirms displayed values and damage, but does not supply every intermediate operand or modifier branch. Preserve baseline and experimental states separately; collect named logs/screenshots on future tests. No further gameplay changes are authorized by this result.

## Proposed reusable CSV-driven patcher (design only)

Implement later as a standard-library tool separate from translation sources, for example `tools/experiments/patch_gimmicks.py`, with a CSV under `data/`. Neither file is created by this proposal. Start with the single supported field `base_attack`; add fields only after their address, width and evidence are documented. Keep ROM revision/layout definitions in a versioned profile, not arbitrary addresses supplied by CSV.

Suggested schema and illustrative row (not an executable change request):

```csv
record_index,gimmick_name,field,expected_original,new_value,evidence,reason
0,Gear-Yo,base_attack,21,22,reverse_engineering/experiments/gearyo_attack_22.md,Validated proof of concept
```

- **Identity and layout:** require the exact approved English input SHA-256 and size. Map zero-based index 0..49 through table file offset `0x0062C250`, stride `0x58`; the initial allowlist maps `base_attack` to +0x22, one unsigned byte. Cross-check names against a verified index/name map. Display runtime ID as index+1 in reports; reject unsupported indices or revisions.
- **Validation before output:** parse integers strictly, enforce 0..255, verify every expected original byte against the untouched input, reject unknown fields, duplicate/overlapping edits, missing evidence and no-op rows. Validate the entire CSV before applying any edit. Bounds are structural checks, not proof that all byte values are safe gameplay values.
- **Dry run first:** show index/name, field, bus address, file offset, old/new byte, evidence and intended change count. Default to dry run; an explicit apply option writes a new file only after validation. Never patch inputs or accept an existing output path; use exclusive creation and keep outputs Git-ignored.
- **Deterministic application:** apply validated changes to an in-memory copy of the fingerprinted baseline. Do not accept already patched inputs or silently stack experiments. Full-file comparison must equal the planned offset/value list exactly, with unchanged length. Read back the written output and verify its hash and differences.
- **Audit output:** write a collision-safe manifest containing profile/tool version, input/CSV/output SHA-256, exact edits, evidence links and protection checks. Preserve existing logs and artifacts. Equivalent profile/input/CSV should produce identical ROM bytes. Record build verification separately from runtime validation; never automatically mark a new combination validated because one constituent edit passed earlier.
- **Testing and rollout:** first reproduce this exact Gear-Yo one-byte artifact and hash. Verify refusal of wrong ROMs, stale expected bytes, unknown fields, duplicate rows, bad ranges and output collisions. Reuse isolated A/B sessions with state-cache precautions. Test one new Gimmick/change at a time; larger CSV batches need their own regression captures. Distribute CSV, tool and documentation rather than ROM images.

This proposal does not implement the reusable patcher, alter the existing experiment script, regenerate ROMs or change additional gameplay values.
