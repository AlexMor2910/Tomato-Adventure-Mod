# Universal two-Binky exchange ? Session 5 closeout

Status: six character/stage reward tests passed, per the user's manual runtime observations. This closes the requested reward-rate milestone, not the pending regression suite. No emulator was operated for this audit. Documentation only was changed.

Validated ROM: `tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`, 16,777,216 bytes, SHA-256 `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3`, CRC32 `AB34C118`. Independent read-only full-file verification against its Alessa-recruitment source confirms the original 118 actual byte differences and all five transaction blocks. Existing patch scripts and historical manifests remain unchanged.

## Runtime results versus static branch interpretation

| Character | Stage | Selector conditions | Endpoint (bus / file) | User-confirmed result |
|---|---|---|---|---|
| Alessa | Early | BA clear; 1C4 clear | 08107F52 / 00107F52 | +2; reset; normal completion |
| Alessa | Intermediate | BA clear; 1C4 set | 0810812E / 0010812E | +2; reset; normal completion |
| Alessa | Late | BA set | 081080F7 / 001080F7 | +2; reset; normal completion |
| Sofoubi | Early | BA clear; 1C4 set | 08107F89 / 00107F89 | 4?6; reset; normal completion |
| Sofoubi | Late | BA set; retained checkpoint also has 1C4 set | 08107F89 / 00107F89 | +2; reset; normal completion; saved count 8 |
| Relleck | Applicable late | BA set; final checkpoint 1C4 clear | 08108165 / 00108165 | 4?6; reset; normal completion |

All successful tests used full charge 0x40. Endpoint assignment follows static control flow, not a user-supplied live cursor trace. Relleck has one applicable eligible reward endpoint; no early Relleck selector path was identified. BA has priority over 1C4. BA is RAM 030032FE mask04; 1C4 is 0300331F mask10; exhaustion 1FC is 03003326 mask10.

## Independently inspected checkpoint inventory

Every row below passed PNG chunk CRC, zlib/state-size/version and locally matched ROM CRC/title checks. Embedded identity is a CRC/title match to a separately SHA-256-verified ROM; the savestate does not embed a ROM SHA-256. All listed states are map0104, all four AWE charge/readiness pairs 00 00, active bitmap zero, all 32 slot flags zero, and all saved return cursors zero. These facts support idle post-event state, not a frame-by-frame proof of exchange behavior.

| Root checkpoint | Bytes | ROM CRC | Membership | BA / 1C4 / 1FC | Binkies | SHA-256 |
|---|---:|---|---|---|---:|---|
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\after_exchange_oystown.ss0` | 35239 | E9ACB98F | 0x31 | clear / clear / clear | 3 | `aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\after_exchange_oystown_alessa_test.ss0` | 34120 | AB34C118 | 0x31 | clear / clear / clear | 4 | `85110875375c28ab412e4413e986d9cb65eb81353d1214f3b86e6d7b7a02f1cf` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\after_exchange_oystown_alessa_test_three_tiers_passed.ss0` | 34732 | AB34C118 | 0x31 | set / set / clear | 8 | `ad5042fb906a2c8105325b04acd9eb611593f6c8a2484543192f01891bf47017` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\relleck_initialized_guarded.ss0` | 39629 | 83BCAD12 | 0xF1 | clear / clear / clear | 4 | `c3a01888ee451731f4d6f073a652d382c1e712ac1f3590622e54bec6654d3ba8` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\relleck_initialized_guarded_successful.ss0` | 26683 | AB34C118 | 0xF1 | set / clear / clear | 6 | `9de814b789f88989c1a4f0330ff024d4b0d81a7031e15d4c3c2c2bf55ec5ec9c` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\sofoubi_initialized_guarded.ss0` | 35310 | 44C01F96 | 0x71 | clear / clear / clear | 4 | `9abd5427393c027bfd25ac50395e7546337e7331114b2d1a70ba9dcdf3ceebcf` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\sofoubi_initialized_guarded_confirmed.ss0` | 24962 | AB34C118 | 0x71 | clear / clear / clear | 4 | `c7a1fb18eea144858fe2982fd5441a24a0758dc3579792a98431db8807cacd30` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\sofoubi_initialized_guarded_confirmed_first.ss0` | 35408 | AB34C118 | 0x71 | clear / set / clear | 6 | `4f63cd1d61486ad01f8004fc2141686c7819438e7c83c6d31d98267afe3f5f3a` |
| `C:\Users\gm347\Documents\NewerCat\Programas\Workspaces\TomatoAdventure\sofoubi_initialized_guarded_confirmed_full.ss0` | 35406 | AB34C118 | 0x71 | set / set / clear | 8 | `f51ec4a4b3bd8c05bd1af01d6a00a4e8d9c2c8b6f80ddc5de3a9d3deef06197d` |

`after_exchange_oystown.ss0` is the ORIGINAL-rate recruitment ROM (CRC E9ACB98F), not a rate-two pass. The Alessa three-tiers file is a final late-state snapshot with 8 Binkies; no separate intermediate snapshot was found in the relevant root inventory. It cannot independently reconstruct all three exchanges. No new checkpoint-specific manifests were found for the later root captures; the new evidence JSON inventories actual contents instead.

Guarded Sofoubi recruitment and replay protection were user-confirmed (31?71, one Super Fan). Guarded Relleck recruitment and replay protection were user-confirmed (71?F1, two working Gimmicks). Both initialize charge/readiness to00. The final Relleck state contains exactly `31 01 00` and `25 01 00`; Sofoubi retains exactly `15 01 00`. All four complete 0x60-byte character records in the final Relleck state equal the pre-exchange guarded Relleck state. DeMille, Alessa and Sofoubi records also equal the clean Sofoubi checkpoint. Embedded CRC AB34C118 and user-tested party behavior support completed cross-ROM transition to the unchanged rate-two ROM; this does not certify arbitrary future cross-ROM loading.

The unsafe unguarded Sofoubi experiment and its F1/five-Super-Fan session remain unsuitable. Guarded experiments are silent/non-atomic; interrupted initialization must be discarded, never repaired by guessed record or membership edits.

## Remaining regressions and scope

Cancellation, partial-gauge rejection, capacity protection (97 accepted to99; 98/99 rejected), multiple full gauges/nonselected gauge preservation, and a dedicated save/reload regression remain pending unless future user evidence explicitly covers them. Static coverage is not runtime confirmation. No Kaizo or early-NPC gameplay change is included in this milestone.

Machine-readable evidence: [binky_exchange_session5_evidence.json](binky_exchange_session5_evidence.json). Historical reports/manifests preserve their construction-time statuses; this closeout supersedes their untested labels for the six specified tests.

## Protection and reviewed sources

Final audit passed: all 388 preexisting protected ROM/save/checkpoint/script/manifest/prior-output artifacts have identical before/after SHA-256 fingerprints; no protected path was added or removed. This is a fresh audit for this documentation/static-analysis task. Read AGENTS, Handoffs1?4, modding plan, Alessa wrapper report, both Binky reports/evidence, existing patch scripts/manifests, checkpoint parsers and actual relevant root checkpoints. No missing required handoff content: Handoff1 is stored under `session_handoffs/SESSION_HANDOFF_1.md`; obsolete root spellings in older prose are not present.
