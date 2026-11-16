# Tomato Adventure — Session 10 Handoff

**Date:** 2026-10-17  
**Status:** Hawker Stage 2 and Stage 2B offline investigations completed; **Hawker placement remains BLOCKED and unimplemented**. Objective is intentionally paused at this checkpoint.  
**Authorization:** Documentation/closeout only. This handoff does **not** authorize further investigation, patch construction, ROM edits, mGBA operation, RAM changes, save/savestate modifications, or commits.

> **Evidence and provenance:** This handoff consolidates the user-provided Codex Stage 2 and Stage 2B result summaries and the attached Session 9 handoff. The new Stage 2/2B reports, JSON evidence, analyzers, manifests, actual ROMs, and active Windows workspace were **not independently inspected** while preparing this document. Classify these as *Codex-reported offline/static results* until checked against their underlying artifacts. An unresolved proof is not an observed gameplay defect.

## 1. Project objective and fixed placement requirements

The **remaining final major objective** is to add **two fully functional Hawkers** to the existing cumulative Tomato Adventure English mod, without disrupting any previously implemented behavior:

| Property | Namp Lagoon | Mayonen |
|---|---|---|
| Map | `0x005F` | `0x004D` |
| Desired tile/cell | `(25,5)` | `(14,6)` |
| Position context | Directly left of blue NPC `(26,5)` | Between upper door groups |
| Candidate actor/NPC slot | `7` | `8` |
| Candidate actor ID | `0x0BFE` **UNPROVED** | `0x0BFF` **UNPROVED** |
| Candidate graphics slot | `7` | `5` |
| Candidate palette slot | `7` | `6` |
| Candidate approach target (pixels) | `(407,111)` | `(231,127)` |

**Mayonen palette slot `5` belongs to door actors and must be preserved**; the proposed new Hawker palette slot there is `6`. Position/resource alternatives require documented evidence, not guesswork.

All Hawkers must preserve the authoritative **exactly two Binkies per qualifying full AWE gauge** exchange for supported characters/story branches: eligibility, costs, dialogue, rewards, cancellations/refusals, gauge consumption, inventory capacity, repeat protection, and shared transaction state. The existing first-screen **Oystown tutorial stays in Oystown**, without a new trigger in either added room. Original Hawkers, blue NPC, door groups, maps, and progression must be preserved.

## 2. Earlier accomplished objectives and protected cumulative input

- **Kaizo principal objective COMPLETE:** 24/24 rewards user-confirmed acquired and functional in tested gameplay. Do not reopen or change the approved 100-Binky thresholds/rewards. No final cumulative-donation counter readback of 100 was supplied; preserve that evidence distinction.
- **Universal two-Binky exchange:** successful exchanges user-confirmed for the six applicable character/story scenarios in prior sessions. Pending negative-path regressions are not claimed passed.
- **Detector experiment:** HP `135 → 120`, base mitigation `38 → 25`, independently **statically verified**; **no Detector runtime test** is reported.
- **Rattlin' Dragon:** intentionally unchanged: HP `262`, base mitigation `54`.
- **No Hawker placement ROM has been built**, and neither new Hawker has undergone gameplay testing.

**Current cumulative experimental input** (Codex-reported and rechecked by Stage 2B):

- Workspace-relative path: `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`
- SHA-256: `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`
- Detector HP file offset `0x00638056`: `87 00 → 78 00`.
- Detector mitigation file offset `0x0063805A`: `26 00 → 19 00`.

Do not overwrite this input or Japanese/English source ROMs, old cumulative outputs, evidence, patch scripts, saves, or savestates. Recheck fingerprints and cumulative patch content against the actual workspace before any future construction.

## 3. Hawker architecture inherited from Stage 1C

Stage 1C proposed a localized design that avoids the unproved RAM scratch-binding lifetime and global event-owner guards:

- **Two private Hawker interaction scripts**, emitted from **one parameterized generator/schema**, not independently hand-maintained forks.
- Relocate **77 internal pointers per private copy**.
- Replace **ten `FE31` actor operands per copy** with local actor slot `7` (Namp) or `8` (Mayonen).
- Keep shared/external transaction state, native continuation, offers/refusals, costs, rewards, and dialogue semantics unchanged.
- Room-specific movement wrappers and map-specific records as appropriate; no global `FE31` patch.

This is the current candidate architecture. A wrapper-only approach cannot fix the shared script's actor-specific `FE31` operations. Earlier global-guard proposals were not proved safe and should not be reopened without contradictory evidence.

## 4. Session 10 Stage 2 — construction-readiness result

Codex reported **`STAGE 2 BLOCKED — EXACT REMAINING GATES IDENTIFIED`**.

### Gate A — PASS (Codex-reported static)

- Script allocation/relocation plan located at **file offsets `0x00800020..0x008008E8`**. Confirm the precise interval convention, payload subdivisions and all pointer destinations from the Stage 2 manifest before patching; do not infer an allocation layout from the endpoints alone.
- All **77 internal pointers per copy** and **ten actor substitutions per copy** independently validated.
- Independent manifest checks and full analyzer replay passed.

These are patch-ready **specifications**, not an implemented ROM.

### Gates B, C, D, E — not all passed

| Gate | Current status at Session 10 closeout | Remaining issue |
|---|---|---|
| **A — Allocation/relocation** | **PASS (reported static)** | Preserve manifests; no repeated broad relocation investigation |
| **B — NPC registration / actor identity** | **BLOCKED** | Actor-bit ownership, operand provenance and default/lifecycle state not fully proved |
| **C — Approach/movement/collision** | **BLOCKED** | Active movement, dynamic occupancy, interaction path and control recovery proof incomplete |
| **D — Graphics/palette resource lifetime** | **BLOCKED** | Writer/resource ownership through room callbacks, conversation and re-entry unproved |
| **E — Exchange equivalence and regression** | **BLOCKED overall** | Script-level exchange equivalence passes statically; full NPC/door non-regression depends on B/C/D |

Stage 2 reported **671 protected files unchanged**, with no ROM modification.

**Stage 2 artifacts reportedly created:**

- `reverse_engineering/hawker_stage2.md`
- `reverse_engineering/hawker_stage2_evidence.json` (including exact patch manifests)
- `tools/analyze/hawker_stage2.py`

## 5. Session 10 Stage 2B — actor ID/registration proof

Codex reported **`GATE B BLOCKED — SPECIFIC ACTOR DEPENDENCIES UNRESOLVED`**.

### Findings

- Candidate IDs `0x0BFE` and `0x0BFF` remain **UNPROVED**, not demonstrated safe and not demonstrated unsafe.
- They index persistent RAM byte **`0x03003286`**, with masks **`0x40` and `0x80`**, respectively (per Codex report).
- **Initial activation of the proposed actor records is independent of the values of those bits.** This is a limited finding, **not** proof that the bits have no other writers, readers, effects, or ownership conflicts.
- Codex reported establishing decoder semantics, save mapping, actor-slot linkage, interaction dispatch, initializer behavior, and **additional flag writers**. Inspect the detailed Stage 2B evidence for handler-specific addresses and exact read/write/alias paths; none were provided in the brief user-shared result.
- The investigation also supplied occupancy initialization and initializer evidence relevant to C/D, **but did not prove active movement/collision safety or graphics/palette resource lifetime**.
- **No debugger observation is requested yet**; the next dependency remains addressable as a bounded offline/static investigation.

### Stage 2B preservation report

Codex reported **1,141 protected fingerprints verified**, including the previous 671, and verification of the expected cumulative input ROM SHA-256. No ROM was constructed or modified.

**Stage 2B artifacts reportedly created:**

- `reverse_engineering/hawker_stage2b.md`
- `reverse_engineering/hawker_stage2b_evidence.json`
- `tools/analyze/hawker_stage2b.py`

These artifacts are reported as local workspace paths, **not attached to this handoff**. Read them directly in the active project when resuming; do not fabricate their contents or assume their findings are independently reproduced here.

## 6. Precise remaining dependencies and recommended resumption order

**The user has chosen to pause the objective at this exact point. Do not perform these follow-ups automatically.** When the user separately authorizes resumption:

1. **Finish Gate B, bounded offline:** close **actor-bank operand provenance**, including `FD84` dynamic-entry paths; audit whether persistent masks `0x40/0x80` on `0x03003286` are owned or written by unrelated events under all relevant entry paths. Ground identity/default-state conclusions in actual handler behavior and map-specific registration, not mere unused-ID searches. Prioritize the reported `FD53/FD54/FD5B/FD5C` handlers and other writers identified by Stage 2B.
2. **Trace room callback lifecycle:** identify registration/occupancy transitions, deferred updates, and cleanup that affect dynamic movement/collision (Gate C), graphics/palette writers (Gate D), and neighboring Namp NPC / Mayonen door actors. Reuse B/2B initializer evidence; no broad re-investigation.
3. **Close Gate E only after B/C/D:** independently verify the scope of full NPC/door regression safety, while preserving the already reported script-level exchange equivalence result.
4. **Only after all critical gates pass, seek separate explicit offline construction authorization.** Build a new isolated cumulative experimental GBA ROM with reproducible patcher, exact changed-byte ledger, output hashes, independent readback and protected-artifact audit. **Never call static proof runtime success.**
5. **User-operated manual mGBA validation only after a safely constructed ROM and separate approval:** visibility, approach, interactions, blue NPC/doors, exchange branches, gauge and Binky counts, Oystown tutorial, room re-entry, persistence/save-reload, Kaizo/Detector and other regressions.

If a critical static dependency cannot be proved, stop and report the exact blocker; propose **one narrowly bounded user-operated debugger observation** only when offline evidence is genuinely insufficient. Codex must not operate mGBA, execute debugger commands, change RAM, or load saves on the user's behalf.

## 7. Operating restrictions and confidence labels

- Read `AGENTS.md`, `tomato_adventure_modding_plan.md`, Session 9 handoff, and Stage 2 / 2B artifacts before future work. Current reports supersede older *candidate architecture* recommendations where they provide more specific evidence.
- Preserve source Japanese and English ROMs, current and historical experimental ROMs, checkpoints/savestates, manifests and reports. Use fresh isolated paths and reproducible scripts for any separately approved patch.
- The user alone operates mGBA; Codex conducts bounded static analysis and only constructs offline ROM patches on explicit authorization.
- Distinguish **user-confirmed runtime**, **Codex-reported static**, **candidate**, and **unproved**. A PASS in Gate A does not imply a Hawker was placed; a BLOCKED gate does not mean a runtime failure occurred.
- No whole-ROM unrestricted analysis, arbitrary story-flag edits, or speculative ROM construction. Do not reopen completed Kaizo work.

## 8. Final checkpoint summary

**Kaizo:** principal objective complete.  
**Two-Binky exchange:** six success scenarios runtime confirmed, negative-path regressions still open.  
**Detector:** 120 HP / 25 mitigation, static only.  
**Rattlin' Dragon:** unchanged at 262 HP / 54 mitigation.  
**Hawker Stage 1C:** localized private-script architecture feasible.  
**Hawker Stage 2:** Gate A PASS, B/C/D/E BLOCKED overall.  
**Hawker Stage 2B:** actor IDs `0x0BFE`/`0x0BFF` still UNPROVED, Gate B BLOCKED; occupancy/initializer evidence advanced.  
**Hawker placement ROM:** **NOT BUILT; NO RUNTIME TEST**.  
**Integrity:** last Codex-reported Stage 2B audit **1,141 protected fingerprints unchanged**, cumulative ROM hash matched.  
**Next authorized action:** **NONE — objective paused by user.**

**When resuming by new user authorization:** perform the narrow **actor-bank operand provenance / `FD84` proof**, then room callback lifecycle analysis. Do not start with Stage 3 construction and do not repeat Stage 2's already validated Gate A work.
