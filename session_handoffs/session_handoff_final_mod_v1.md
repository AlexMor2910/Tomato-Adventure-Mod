# Tomato Adventure — Final Mod Session Handoff v1

**Handoff date:** 2026-10-28  
**Filename:** `session_handoff_final_mod_v1.m` (extension retained exactly as requested)  
**Status:** Cumulative v3 **INCOMPLETE EXPERIMENTAL BUILD**; offline/static verification reported PASS; **no v3 runtime testing performed**.  
**Purpose:** Preserve the final cumulative mod status, evidence limits, and next safe steps for a future Codex / user-operated mGBA session.

> **Evidence boundary:** This handoff is based on the user's pasted Codex completion reports for cumulative v1, v2, and v3, plus uploaded prior handoffs and `AGENTS.md`. The active Windows repository, ROM binaries, manifests, BPS files, and new v1–v3 reports have **not been directly inspected here**. All new hashes, byte counts, audit totals and test results below are **Codex-reported**, not independently reproduced by this handoff. This document does not authorize emulator operation or new ROM edits.

## 1. Current authoritative build

**Cumulative v3 ROM (local test artifact):**

`tools/patch/output/cumulative-v3-20261028/build/tomato_cumulative_v3_INCOMPLETE.gba`

- **Size:** 8,388,608 bytes (8 MiB)
- **SHA-256:** `3f12082f97b640ef7fa09cc64c935cd18e7bbcb41ee6b99d4c0abb9c2995fbb9`
- **Relative to English baseline:** 282 changed bytes, independently accounted for per Codex report
- **Relative to v2:** exactly **one** changed byte, for sewer map `0x016D` music `0x0E → 0x10`
- **Construction:** baseline-to-v3 canonical build and v2-to-v3 incremental build matched byte-for-byte
- **Automated verification:** 52 tests passed; both BPS patches reproduce v3; header and full-file difference checks passed
- **Runtime:** not tested in mGBA on this v3 output
- **Status label must remain:** **Tomato Adventure — Cumulative v3 Incomplete Experimental Build**

**Distribution package (no copyrighted ROM or extracted assets):**

`tools/patch/output/cumulative-v3-20261028/tomato_cumulative_v3_INCOMPLETE_patch.zip`

ZIP SHA-256: `ea460d373c09561335ff41a09bef4d1b6591e35e1c3dcf579b120ec25bf575ca`

**Artifact index / build instructions:**

`tools/patch/output/cumulative-v3-20261028/README.md`

**Three-map resolution evidence:**

`reverse_engineering/cumulative_v3_music_resolution.md`

The v3 delivery reportedly includes the corrected three-map ledger, single-byte v2→v3 ledger, full cumulative ledger, both BPS patches, source scripts, tests and a user-operated manual route through `0x016C ↔ 0x016D`. Obtain exact script/manifest names from the README; do not invent them.

## 2. What the final mod is intended to contain

Five feature groups were requested:

1. **Music:** Dropper Village → Pokypine Forest; Mayonen Caverns → Mayonen; Captain Grocko Ship → Namp Lagoon; Oyster Sewers → Oystown; the Vault → Oops Mannor (retain user-requested naming; location/track aliases documented in the v2 plan).
2. **Hanzo / Attack:** Lab 1 awards **Dojo Pup** instead of Erupter; Lab 2 awards **Erupter** instead of Dojo Pup; swap their **displayed Attack progression at every difficulty/validated upgrade state**, without swapping unrelated Gimmick properties.
3. **Kaizo:** Preserve the 24 original rewards/prerequisites while replacing cumulative 180-Binky threshold progression with an ending threshold of **100**.
4. **Existing Hawkers:** Exactly **two Binkies** per qualifying full AWE gauge for the supported characters/story branches, preserving original transaction semantics and Oystown tutorial. **Do not add new Hawker NPCs.**
5. **Detector:** HP **120**, base mitigation **25**; leave Rattlin' Dragon HP **262**, mitigation **54**.

The experimental Alessa recruitment shortcut is **excluded** from the 8-MiB baseline-derived v1/v2/v3 cumulative builds. Do not reintroduce it. No new Hawker NPCs or unrelated balance changes were added.

### Implemented music rooms in v3

| Area | Confirmed patched rooms | Target selector | Status |
|---|---:|---|---|
| Dropper Village | 8 | `0x0D` | Confirmed set implemented; alternative `0x012C` unresolved |
| Mayonen Caverns | 15 | `0x07` | Confirmed component implemented; AWE lesson music-restore fix retained |
| Captain Grocko Ship | 29 | `0x24` | Confirmed ship set implemented; disco cue preserved |
| Oyster Sewers | 15 | `0x10` | Includes newly confirmed `0x016D` |
| The Vault | 21 | `0x08` | Confirmed set implemented; alternative `0x0158` unresolved |
| **Total** | **88** | | **Exhaustive global/event coverage not proven** |

**Music support:** map record table starts at file `0x0062D3E4`, stride `0x1C`; selector occupies the low six bits of byte `+5`, and upper bits must be retained. Previous analysis identified ordinary playback as selector + 200 and event commands `FE A7`, `FE A8`, `FE A9`, `FE AB` as possible music overrides. See v2 music plan for precise validated ledger and event coverage; these facts do not authorize new substitutions by themselves.

**v2 music plan (reported):** `reverse_engineering/cumulative_v2_music_plan.md` and matching JSON. Preserve 87 prior room changes and AWE restore exactly, plus v3's single confirmed sewer byte change.

## 3. Three-map investigation — latest definitive decisions

| Map | Latest evidence and conclusion | v3 action | Remaining gap |
|---|---|---|---|
| `0x012C` | Village-looking copy; **normal incoming path and region ownership not established** | Leave original selector `0x0E` | Prove active entry context and whether village, Vault copy or another region |
| `0x0158` | Possible Vault copy; investigation corrected prior assumption: map `0x0127` actually selects **`0x0157`**, not `0x0158` | Leave original selector `0x0E` | Prove an active incoming path and actual region membership |
| `0x016D` | Confirmed Oyster Sewers side channel, linked with `0x016C`; actual ROM exits, native transition handling, Oystown entry scripts and matching resources corroborate identity | Patch `0x0E → 0x10` | User-operated gameplay validation pending |

**Important correction:** v2 missed the `0x016C ↔ 0x016D` edges already present in the retained CSV. Do not continue treating `0x016D` as statically unresolved. Conversely, do not patch `0x012C` or `0x0158` simply because they look similar to other rooms. Conditional map-controller selections do not prove either record is normally reachable.

Conservative event traversal still does **not** prove every global/native continuation context. Even if `0x012C` and `0x0158` were resolved, exhaustive music-area coverage would require separately supported evidence. Keep the incomplete label until the evidence warrants changing it.

## 4. Existing four feature groups — keep unchanged

### Hanzo and Attack

- Lab 1 reward command at bus `0x0810D698`: `FD 0B 1C 1B 00`, reward-ID operand file `0x0010D69B`; Erupter ID `0x1B` (27) → Dojo Pup ID `0x29` (41). Prior **standalone** Lab 1 experiment was user-tested for reward/menu/battle usability.
- Lab 2 reward was mapped and patched during v1, according to Codex; exact verified offset belongs in the v1 manifest and should not be guessed from the historical handoffs.
- All **2,304** Attack progression comparisons passed in v1 and were preserved through v3. This is **static/menu equivalence**, not proof of identical real battle damage.
- Original Gimmick table begins at file `0x0062C250`, 50 records, stride `0x58`, Attack field `+0x22`; scaling metadata requires preserving the existing validated patch rather than swapping entire records.
- **v3 runtime:** no tests. Lab 2, full Attack differences/upgrades and ordinary progression still require user gameplay validation.

### Kaizo

Approved thresholds, in order:

`2, 4, 6, 7, 9, 12, 14, 17, 21, 24, 28, 32, 36, 41, 45, 50, 55, 61, 66, 72, 78, 85, 92, 100`

- All original 24 rewards and original prerequisites/flags preserved.
- Prior Kaizo experimental ROM had **24/24 user-confirmed reward acquisitions and functionality**; a separate final donation counter readback of exactly 100 was not supplied.
- The old whole-stack donation behavior remains: if the count is 99 and five are donated, all five are taken but only one is credited toward 100; preserve this accepted rule.
- **v3 runtime:** untested; do not equate prior experiment with this ROM.

### Two-Binky Hawkers

- Prior user-confirmed successful scenarios: **Alessa early/intermediate/late, Sofoubi early/late, Relleck applicable late** (six cases), each awarding two Binkies and consuming the selected qualifying full AWE gauge.
- Existing Hawkers only; no new Mayonen/Namp NPCs. Early Hawker placement is a paused, separate objective and remains unimplemented.
- Negative-path regressions still pending: cancellation/refusal, partial gauge, capacity 97/98/99, nonselected full gauge, save/reload, broader normal-story availability.
- **v3 runtime:** untested.

### Detector

- Enemy ID `0xA5`, HP at file `0x00638056`: `87 00` (135) → `78 00` (120).
- Base mitigation at file `0x0063805A`: `26 00` (38) → `19 00` (25).
- Rattlin' Dragon ID `0x9C` remains HP 262 / mitigation 54; other enemy records unchanged per previous static verification.
- **No Detector live battle test was reported**, including on v3.

## 5. Version history / source fingerprints

| Artifact | Reported SHA-256 | Role |
|---|---|---|
| Japanese original | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` | Protected source |
| English baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` | Protected English source; canonical rebuild base |
| Historical 16-MiB Kaizo experimental | `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2` | Separate historical ancestry with Alessa wrapper |
| Historical 16-MiB Detector experimental | `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0` | Old cumulative candidate; not final release input |
| v1 8-MiB incomplete | `1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f` | 194 changes from English baseline; Caverns `0x001E` only |
| v2 8-MiB incomplete | `300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482` | 281 changed bytes; 87 music rooms + AWE restore |
| **v3 8-MiB incomplete** | **`3f12082f97b640ef7fa09cc64c935cd18e7bbcb41ee6b99d4c0abb9c2995fbb9`** | **Current candidate; 282 changed bytes, 88 music rooms** |

Reported v1 output:
`tools/patch/output/cumulative-v1-20261028/build/tomato_cumulative_v1_INCOMPLETE.gba`

Reported v2 output:
`tools/patch/output/cumulative-v2-20261028/build/tomato_cumulative_v2_INCOMPLETE.gba`

v2 and v3 should not be overwritten or casually replaced. Historical 16-MiB Alessa-based experiments are not equivalent to the clean 8-MiB release ancestry.

## 6. Preservation, reproducibility and confidence

**Latest v3 Codex report:**

- 52 automated tests PASS; no reported failures.
- 282 baseline-relative changed bytes accounted for; precisely one new v2-relative music change.
- Canonical rebuild and incremental build match exactly.
- Both BPS patches reproduce the exact v3 ROM.
- ROM header and full-file difference checks PASS.
- All **17,472 inventoried preexisting files** retained hashes; **zero inventoried preexisting files changed**. This included historical v2 inventory.
- Distribution ZIP contains no ROMs or extracted assets. Vendor installations, generated Ghidra projects and caches were outside the hash audit.

These checks support offline consistency only, not game-play correctness or complete area coverage. Verify the actual local files, hashes and manifests before a new construction or release decision.

**Repository rules:** Read `AGENTS.md` and `tomato_adventure_modding_plan.md`. Never overwrite Japanese/English originals, previous experimental ROMs, reports, manifests, saves/savestates or extracted assets. Prefer isolated versioned outputs, exact-byte guards, hashes, independent verification, reproducible scripts and clear uncertainty labels. Do not distribute copyrighted ROMs/assets. The **user alone operates mGBA**; Codex must not launch/control it or change live RAM/states. Avoid unbounded Ghidra or whole-ROM analysis.

## 7. Next action: user-operated mGBA validation (priority)

**Recommendation:** Stop broad static music research for now. Prepare an isolated mGBA v3 testing environment *offline only* and let the user perform manual tests. Do not assume old experimental savestates are safe for v3; use new isolated save/state locations and validate identity before any reuse. Codex may prepare instructions and copied nonprotected configurations only with authorization, but must never run the emulator.

### First targeted test: Oyster Sewers `0x016D`

1. Load the v3 ROM in user-operated mGBA with an isolated save environment.
2. Reach Oystown map **`0x010F`** through normal gameplay/test conditions.
3. Enter sewer map **`0x016C`** normally from `0x010F`.
4. Cross `0x016C`'s **left boundary** at tile **x=0, y=3–4** into **`0x016D`**.
5. Confirm **Oystown music** plays in `0x016D`, and verify ordinary movement and available NPC interaction.
6. Return from `0x016D` through its **right boundary** at **x=14, y=3–4** into `0x016C`.
7. Check re-entry, battle/return where available, exit/re-entry and normal save/reload; note any silence, music reset, wrong cue or transition problem.
8. Record ROM SHA-256, emulator version, save isolation, observed map IDs/music, exact actions, screenshots and any failure.

### Remaining regression checklist

- Test representative and then all feasible patched rooms in Dropper Village (8), Mayonen Caverns (15), Captain Grocko Ship (29), Oyster Sewers (15), Vault (21). Include first entry, internal transitions, battles, exit/re-entry, special event cues and AWE lesson music restoration.
- Test Hanzo Lab 1 → Dojo Pup and Hanzo Lab 2 → Erupter via normal paths, inventory/equipping/battle use and save/reload.
- Compare displayed Attack for Erupter and Dojo Pup across levels/upgrades; measure actual damage separately rather than inferring it from menu values.
- Test Kaizo donation boundaries, original story gates, reward functionality and save/reload in v3; preserve existing 24/24 historical evidence as prior-run only.
- Test Hawker successful exchanges and pending cancellation, partial charge, capacity, nonselected gauge and persistence cases.
- Test Detector encounter, HP/mitigation effects and unchanged Rattlin' Dragon.
- Observe normal progression, NPC/doors, dialogue and saving for unrelated regressions.

## 8. Open questions and acceptable future research

1. `0x012C`: find a **normal active incoming context** and prove village/Vault-copy/other ownership before changing music.
2. `0x0158`: find a **normal active incoming path**; do not repeat the disproved assumption that `0x0127` selects `0x0158` (it selects `0x0157`).
3. Broader event-coverage caveat: conservative traversal does not prove every global/native continuation. Any exhaustive five-area completeness claim needs additional grounded support.
4. Final v3 gameplay runtime tests remain pending across **all five** feature groups.

Future Codex research should begin with exact evidence from v3 reports and ideally a user-supplied targeted mGBA observation, rather than reopening wide exploratory searches. If unproved room identity remains, **leave its byte unchanged** and keep the experimental label.

## 9. Short recovery prompt for the next Codex session

> **Tomato Adventure — v3 runtime-test preparation.** Read `AGENTS.md`, `tomato_adventure_modding_plan.md`, this handoff, the v3 README, `reverse_engineering/cumulative_v3_music_resolution.md`, the v2 music plan, and the existing v3 manifests/ledgers. Independently verify the reported v3 ROM hash `3f12082f97b640ef7fa09cc64c935cd18e7bbcb41ee6b99d4c0abb9c2995fbb9` and protected-file status before proceeding. The current build is an **INCOMPLETE EXPERIMENTAL** 8-MiB English ROM with 88 confirmed patched music rooms, including the newly confirmed sewer map `0x016D` (`0x0E→0x10`). Maps `0x012C` and `0x0158` remain unchanged and unproved. All four other mod feature groups are statically preserved and v3 itself has not been runtime-tested. Prepare an isolated **user-operated** mGBA validation plan, beginning with `0x010F → 0x016C ↔ 0x016D`, and the remaining music/Hanzo/Attack/Kaizo/Hawker/Detector checklist. **Do not operate mGBA, alter live RAM/saves, modify ROMs, resume sprite extraction or new Hawker placement, or claim full area coverage.** Preserve all preexisting source and experimental artifacts. If further investigation is separately requested, keep it bounded to exact unresolved map-entry or event-context evidence.

## 10. Exact stopping state

- **Current ROM:** Cumulative v3 incomplete experimental; SHA-256 `3f12082f97b640ef7fa09cc64c935cd18e7bbcb41ee6b99d4c0abb9c2995fbb9`.
- **Music:** 88 patched confirmed rooms; `0x016D` newly resolved; `0x012C` / `0x0158` unresolved and untouched; global/native continuation coverage non-exhaustive.
- **Hanzo/Attack:** both rewards swapped and 2,304 static comparisons PASS; v3 gameplay tests pending.
- **Kaizo:** approved thresholds and 24 original rewards preserved, historical 24/24 user-confirmed; v3 gameplay tests pending.
- **Hawkers:** existing two-Binky rate retained; six historical successful scenarios; no new NPCs; v3 gameplay tests pending.
- **Detector:** 120 HP / 25 base mitigation, Rattlin' Dragon 262 / 54, static only.
- **Alessa test-only shortcut:** excluded.
- **Preservation:** 17,472 inventoried preexisting files unchanged (Codex-reported).
- **Next milestone:** isolated **user-operated mGBA validation**, beginning with `0x016D`; no new ROM construction authorized by this handoff alone.
