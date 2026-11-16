# Tomato Adventure — Session Handoff 4

**Session date:** 2026-10-13  
**Status:** Session closeout / documentation only; does not authorize new ROM modifications, emulator operation, RAM changes, checkpoint changes, or commits.  
**Scope:** Validated Alessa recruitment and AWE, Oystown shortcut, patched two-Binky exchanges, and the next three modding objectives.

## 1. Read first and preserve the working method

Read `AGENTS.md`, `SESSION_HANDOFF.md`, `SESSION_HANDOFF_2.md`, `SESSION_HANDOFF_3.md`, `SESSION_HANDOFF_4.md`, and `tomato_adventure_modding_plan.md`. Also consult the latest workspace copies of:

- `reverse_engineering/experiments/alessa_recruitment_wrapper.md`
- `reverse_engineering/awe_initialization.md`
- `reverse_engineering/pre_oystown_progression.md`
- `reverse_engineering/experiments/oystown_shortcut.md`
- `reverse_engineering/experiments/oystown_binky_exchange.md`
- `reverse_engineering/experiments/binky_exchange_rate_two.md`
- `reverse_engineering/experiments/binky_remaining_character_tests.md`
- Their evidence JSON files, relevant analysis/patch scripts, and the newest checkpoint manifests.

**Preservation:** Never overwrite the original Japanese or English ROM, existing experimental ROMs, original saves, or checkpoints. Use fresh isolated outputs and disposable copies; record SHA-256 values and full-file differences. Do not distribute ROMs. The user operates mGBA and reports actual behavior; Codex performs bounded static analysis, creates reproducible patches only on explicit authorization, and supplies one debugger action at a time. Do not autonomously operate mGBA, edit live RAM, launch Ghidra, or run whole-ROM analysis. Distinguish user-confirmed runtime evidence from Codex-reported static analysis and untested expectations.

## 2. Protected ROM identities and active patch outputs

| Artifact | SHA-256 | Status |
|---|---|---|
| Original Japanese ROM | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` | Protected |
| English translation baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` | Protected |
| Alessa recruitment wrapper (16 MiB) | `3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6` | Experimental, protected |
| Binky rate-two + recruitment (16 MiB) | `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3` | Active runtime test ROM, protected |
| Binky rate-two standalone (8 MiB) | `b9967b15193b5aec701032742d322a1040373e76b176b1aeb1e65ce2c06078b6` | Statically verified, runtime untested |

Codex reported that the Binky patch changes exactly **118 bytes** in each respective source ROM; five static tests and full-file comparisons passed. The most recent Codex audit reported **90 protected artifacts unchanged** at that time. This handoff does not independently repeat any hash audit.

Relevant paths:

- `tools/patch/alessa_recruitment_wrapper.py`
- `tools/patch/binky_exchange_rate_two.py`
- `tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`
- `tools/patch/output/binky-rate-two-baseline-c4ec3611142c49cf93d891cbfc10f056/binky_exchange_rate_two.gba`

## 3. Completed milestones and exact evidence limits

### 3.1 Alessa recruitment — user-confirmed runtime

A controlled wrapper redirected Hanzo's first reward call to the normal interpreter commands `FE 49` and `FE 53 6B`, then returned to Hanzo's original Erupter reward block. The user confirmed:

- Party membership `0x03001AB4 = 0x31` (DeMille and Alessa).
- Alessa's inventory count `0x03001F43 = 0x01`, entry at `0x03001F44` = `2B 01 00` (Pop Horn).
- DeMille received Erupter; both characters appeared in menus and battle; Gimmicks, movement, battle completion, and subsequent story progression worked in the tested session.

This does **not** prove that the wrapper reproduces all of Alessa's original recruitment story effects. The user's selected shortcut workflow will **not revisit Mayonen's original recruitment event**.

### 3.2 AWE — user-confirmed runtime

- Alessa persistent charge `0x03001F94` read `0x01` after battle; persistent readiness at `0x03001F95` read `0x00`.
- In a disposable session, writing `0x03001F94 = 0x40` enabled full AWE in an ordinary battle without editing readiness or tutorial flags. The user confirmed AWE worked.
- After using AWE and gaining some charge during battle, the persistent value was `0x05`. This supports consumption/copyback but does **not** measure exact consumption.
- Tutorial flag `0x171` is **not** proven to mean completed tutorial and is not a direct AWE battle-menu gate.

### 3.3 Shortcut to Oystown — user-confirmed runtime

- From Mayonen outdoor first-screen map `0x0048`, overworld node `0x04`, the route flags `0x24–0x27` in RAM byte `0x030032EB` were enabled with mask `0xF0`. User confirmed transition `0xCB → 0xFB` after earlier `0x0B → 0xCB` edits.
- Normal overworld navigation succeeded via Hanzo Lab 3 to Oystown; a **pre-entry** savestate was captured.
- Oystown loaded normally; its first-introduction and Binky exchange introduction played; no visible errors were reported.
- Flag `0x1F4` was documented as a first-introduction guard, but is not proof of all first-visit side effects.
- These observations do not establish every earlier story prerequisite or the full optional Gimmick inventory. Completing those is **not the current priority**.

### 3.4 Original and patched Binky exchange — user-confirmed runtime

- Original early-Alessa full-gauge exchange: **1 Binky**, AWE gauge reset, no visible error.
- Patched early-Alessa exchange: **2 Binkies**, gauge reset, event completed normally.
- Patched intermediate-Alessa progression test: flag `0x1C4`, RAM `0x0300331F`, mask `0x10`; user reported successful 2-Binky exchange. The test used a controlled disposable live session.
- Patched late-Alessa progression test: flag `0xBA`, RAM `0x030032FE`, mask `0x04`; user verified the byte changed `0x00 → 0x04`, then reported successful 2-Binky exchange after refilling AWE.
- **All three tested Alessa reward tiers now have user-reported runtime success.** This does not by itself validate Sofoubi or Relleck.
- Codex reported the patched routine covers five successful exchange paths statically and preserves full-AWE requirements, character selection, gauge reset, and capacity protection. Exact branch mapping should be read from `binky_exchange_rate_two.md`, not reconstructed from guesses.

### 3.5 Checkpoints

Codex reported these existing checkpoints and their contents:

- `before_oystown.ss0`: Hanzo Lab 3 exterior, party `0x31`, routes enabled, Oystown intro pending, AWE `0x05`. Preferred **pre-entry** foundation.
- `after_exchange_oystown.ss0`: Oystown after original exchange, intro consumed, AWE `0x00`, existing inventories preserved.
- `after_exchange_oystown_alessa_test.ss0`: confirmed to exist and match the **patched** 16 MiB ROM; preferred post-test foundation for further exchange-branch testing.

Consult manifests/reports for **actual paths, hashes and ROM identities**. Do not infer that a savestate made under one ROM is compatible with another without explicit validation. Whether new saves were made following the intermediate and late Alessa tests was not established here.

## 4. New primary objectives (priority order)

### Objective A — Exactly two Binkies for Sofoubi and Relleck at every game stage

**Desired gameplay behavior:** A successful exchange of one full AWE gauge always awards **exactly 2 Binkies** for **Alessa, Sofoubi, and Relleck**, independent of story stage. Alessa's early, intermediate and late scenarios have already been tested successfully. Next validate **Sofoubi's early/later paths** and **Relleck's path** at runtime.

- Codex's previous analysis reportedly identified Sofoubi/Relleck initialization branches, but no safe, runtime-validated initialized checkpoint or event carrier is yet established.
- Investigate original character initialization, membership, charge, character selection, and required event context before constructing a disposable test state.
- Do **not** merely set membership bits or copy Alessa's character records into other slots.
- Reuse the existing two-Binky patch unchanged unless test evidence shows a defect. Record exact pre/post Binky counts and AWE reset; preserve capacity behavior.
- The user should not be required to play the entire intervening story merely to test these branches. Prefer small evidence-backed controlled scenarios.

**Acceptance:** Each supported Sofoubi and Relleck exchange path yields 2 Binkies for one full gauge, with normal eligibility, consumption, and event completion. Until tested, their behavior is **statically verified / runtime untested**.

### Objective B — Kaizo's laboratory: Binky requirements for gifted Gimmicks

**Story position:** The user is about to enter **Kaizo's laboratory**. Do not presume Kaizo's dialogue or mechanics have been traced yet.

Investigate, separately and precisely:

1. How Kaizo's dialogue/event checks the player's current number of Binkies; identify inventory storage, comparison logic, and relevant event interpreter commands/functions.
2. The story/event flags that determine whether Kaizo can offer/gift each Gimmick, whether a gift has already been claimed, and whether an offer appears at all.
3. The **Binky cost/threshold required for each Gimmick** (and whether Binkies are spent, merely counted, or checked against cumulative totals).
4. Any special character, chapter, inventory-capacity, or prerequisite behavior; identify relevant dialogue and displayed requirements.
5. The narrowest reproducible modification that changes **the numerical Binky requirements only** while preserving the flags and their original meanings.

**Critical design rule: change cost/threshold values, NOT story flags or unlock/completion flags.** Do not assume the Binky amount is a consumed currency, and do not guess numeric costs or desired replacement numbers. Research the original per-Gimmick requirements first and present a table of original values, exact locations, and safe patch options for the user's decision. Preserve checks, reward IDs, ownership, and acquisition logic unless explicitly approved otherwise.

**Acceptance for the research phase:** A complete evidence-backed table of Kaizo gifts, original Binky thresholds/costs, relevant gating flags and exact patchable data/instructions, with unverified items marked as such. Actual replacement values are **not yet specified**.

### Objective C — Add Binky exchange NPC to early areas

**Desired placements:**

- **Mayonen:** first screen/outdoor arrival map; earlier user-confirmed map ID `0x0048`.
- **Namp Lagoon:** **second screen** (not the first); exact map ID and placement must be located and verified before editing.

Place or reproduce **the Binky exchange NPC's sprite/graphics and functional agent/event interaction** in both locations so the exchange is accessible earlier in the game.

Investigate original Oystown NPC event/actor definitions, graphics/sprite reference, map object or actor table format, triggers, and the script's dependencies on Oystown-specific actors, flags, or context. The implementation should use the original functional exchange routine (or a verified equivalent), not just show a decorative sprite. Verify placement, collisions, facing/interactions, map object capacity, pointer/table relocation, and saved-state behavior. Avoid unintentionally triggering Oystown's first-visit event or unrelated map events. Ensure the NPC supports all eligible party characters and uses the **constant-two-Binky patch**.

**Acceptance:** The NPC appears and can be interacted with on Mayonen's first screen and Namp Lagoon's second screen, and valid full-AWE exchange grants exactly 2 Binkies with normal gauge reset, without breaking either map. Exact coordinates, Namp second-screen ID, asset reuse strategy, and ROM patch design remain **to be verified**, not invented.

## 5. Recommended workflow for next session

1. Read the current workspace reports and preserve/verify all active ROMs and checkpoints; confirm whether mGBA is presently running, and whether the user is positioned before Kaizo's laboratory.
2. **Objective A:** Find a controlled initialized Sofoubi/Relleck test mechanism, prepare the smallest test, and obtain one manual runtime observation at a time. Record separate tests across their relevant progression states.
3. **Objective B:** Perform read-only targeted Kaizo script/threshold investigation. Present an original-cost table and gating analysis **before asking for the new costs** or patching. The user will choose target amounts.
4. **Objective C:** Map Oystown NPC assets/events and the two intended target screens. Plan a reproducible insertion/relocation patch, verify conflicts, and seek explicit implementation approval before patching.
5. Keep the balance patch, Kaizo cost changes, and early-NPC relocation as **separate reversible modifications** before testing a combined experimental ROM; do not overwrite the runtime-validated version.

Do not pursue full optional pre-Oystown Gimmick inventory, blanket story-flag completion, or recreation of Mayonen recruitment unless the user specifically reauthorizes such work.

## 6. Handoff integrity and evidence caveats

This handoff was prepared from the uploaded previous handoffs and the user's/Codex's reports in this conversation. It has **not** independently opened the user's current Windows workspace, its later reports, savestate files, ROM binaries, or exact patch byte ranges. The most recent protected-artifact count (**90**) is a historical Codex report, not a new audit performed here. No ROMs or checkpoints were modified by preparing this handoff. Future work requires fresh explicit authorization for runtime tests or patch construction.
