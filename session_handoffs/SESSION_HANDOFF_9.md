# Tomato Adventure — Session 9 Handoff

**Date:** 2026-10-16  
**Status:** Hawker Stage 1C architectural investigation complete; **localized implementation feasible, not constructed or runtime tested**.  
**Next priority:** Prove allocation, actor registration, movement/collision, and graphics/palette lifetime safety; implement only after all critical checks pass.

> **Evidence/provenance:** This handoff consolidates the user's latest Codex Stage 1C report and the earlier supplied session handoff. The Stage 1/1B/1C workspace reports, analyzers, evidence JSON, ROMs and current repository were **not directly inspected** while authoring this document. Treat the Codex findings as reported results, and recheck the actual workspace artifacts before changing confidence levels or patching. This handoff itself authorizes no ROM modifications or emulator operation.

## 1. Project objective and status

The **final major modding objective** is to add two fully functional Hawker NPCs, while preserving all existing behavior and the cumulative experimental mod:

- **Namp Lagoon**, map `0x005F`, cell `(25,5)`, directly left of the existing blue NPC at `(26,5)`.
- **Mayonen**, map `0x004D`, cell `(14,6)`, between the upper door groups.
- Each added Hawker should use the same authoritative **two-Binky-per-full-AWE-gauge** exchange semantics, including costs, character eligibility, dialogue, rewards, refusal/cancellation, gauge consumption, capacity behavior, and shared state.
- The **Oystown first-screen tutorial must remain in its original place**, and all existing Hawkers/NPCs and map transitions must remain unaffected.

Earlier objectives: Kaizo's principal 24/24 rewards objective was reported complete with user-confirmed acquisition/functionality; the Detector experimental rebalance was implemented and independently **statically verified** (HP `135→120`, base mitigation `38→25`), but **runtime testing remains pending**. Rattlin' Dragon remains unchanged at HP `262`, mitigation `54`.

**Do not describe the Hawker placement as implemented:** no Hawker-placement ROM has yet been produced and no new Hawker was tested in game.

## 2. Verified cumulative experimental input (last Codex report)

- **ROM path:** `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`
- **SHA-256:** `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`
- Codex reported exactly two Detector-byte changes relative to its Kaizo parent: file `0x00638056` (HP `87 00→78 00`) and `0x0063805A` (mitigation `26 00→19 00`).
- Codex also reported preservation of the 51 Kaizo ledger bytes, existing English translation, Alessa wrapper, universal two-Binky exchange and Oystown tutorial code; GBA header complement passed.

Revalidate this input's fingerprint and cumulative patch contents **against the actual workspace** before future construction. Never overwrite the Japanese ROM, English baseline ROM, preceding experiments, saves, savestates, or evidence/manifest files.

## 3. Confirmed target-placement candidates

| Property | Namp Lagoon | Mayonen |
| --- | --- | --- |
| Map ID | `0x005F` | `0x004D` |
| Hawker tile/cell | `(25,5)` | `(14,6)` |
| Reserved NPC slot | `7` | `8` |
| Candidate graphics slot | `7` | `5` |
| Candidate palette slot | `7` | `6` |
| Candidate approach target | `(407,111)` pixels | `(231,127)` pixels |
| Placement detail | Left of blue NPC `(26,5)` | Between upper door groups |

The destination cells passed preliminary in-bounds/base-walkability checks, **not** full-path, dynamic collision or control-return proof. **Mayonen palette slot 5 belongs to door actors and must remain intact**; the proposed Hawker palette is slot 6. Any necessary coordinate/allocation change must be grounded and documented.

## 4. Hawker investigation chronology and architectural decision

### Original dependency findings

- The shared Hawker exchange includes **ten `FE31 03 01` occurrences** over five offer branches and five advice/refusal/exit branches; they are not ten animation writes per conversation.
- `FE31` operand `03` targets **actor slot 3**; `01` selects its normal directional animation controller. On Namp map `0x005F`, slot 3 belongs to the existing blue NPC. Blind script reuse could animate the wrong NPC.
- The interaction dispatcher stores a clicked actor slot at RAM `0x03003A32`, but full lifetime safety was never proved.
- `FD01` and `FD02` provide pixel X/Y; `FE01` transfers approach continuation to player actor 0.
- Hawker graphics were traced to 11 frames; nominal capacity was promising, but resource lifetime remained unverified.

### Final gate (before Stage 1 investigations)

Five checks were **BLOCKED due to missing proofs**, not observed gameplay failures: scratch-binding lifetime, scoped FE31 adaptation, movement/dynamic collisions, graphics/palette lifetime, and persistent actor IDs/event registration. The final-gate analysis created `tools/analyze/hawker_final_gate.py`, `reverse_engineering/hawker_final_gate_evidence.json`, and `reverse_engineering/hawker_final_gate.md`; **no ROM was modified**.

### Stage 1

Codex reported tracing 15 Hawker dialogue strings to 16 control handlers. Identified choice/termination writes did not overwrite `0x03003A32`, but transitive and concurrent-event alias preservation was not established. FE31 arguments are **staged in RAM**, invalidating a proposed guard based on the original ROM argument cursor. An existing per-event saved-return word looked promising but required lifetime proof.

Reported artifacts: `reverse_engineering/hawker_stage1.md`, related analysis helpers and JSON evidence (inspect actual workspace for filenames).

### Stage 1B

- The per-event saved-return word is a **single-slot** value, overwritten by `FD2F`/`FD31`, read by `FD7C`, and cleared on event reset. It was **rejected as a sufficient NPC identity token**.
- `FD0B` can alias `0x03003A32`; an actual Hawker-path overwrite was **not demonstrated**.
- A scratch-independent room/command guard was considered, but exclusive entry was not proved because `FD84` supports dynamically constructed script jumps.
- Conclusion: a global FE31 adapter or event-owner guard still lacked a bounded reachability/cross-context/overlap proof.

Reported artifacts: `reverse_engineering/hawker_stage1b.md`, reproducible analyzer and supporting evidence JSON.

### **Stage 1C — current architectural recommendation**

Codex's latest read-only investigation reports **`STAGE 1C — LOCALIZED IMPLEMENTATION FEASIBLE`**. The recommended design is:

**Two private Hawker interaction scripts generated from one parameterized schema**, rather than a global FE31 adapter.

Specific reported transformation **for each private copy**:

1. Relocate **77 internal pointers** so its internal control flow points to the corresponding private copy.
2. Replace the **ten `FE31` actor operands** with the new actor slot: **`7` for Namp** and **`8` for Mayonen**.
3. Preserve the original exchange's external/shared transaction state and native continuation semantics. Keep exchange rewards, cost, dialogue, eligibility, gauge handling, and tutorial behavior unchanged.
4. Generate both copies from **one common parameterized schema**, with explicit relocation/patch manifests; avoid unrelated manually edited script forks.

**Why this architecture:** It reportedly removes dependency on unproved scratch-binding lifetime and event-ownership guards, while isolating actor-specific changes. The **wrapper-only approach is insufficient** because it cannot safely fix `FE31` commands executed within the shared exchange. The **global guarded FE31 adapter remains unproved** and is not the recommended approach.

This is **reported architectural feasibility, not proof of complete deployment safety**. Inspect Stage 1C's evidence for the exact pointer ranges, command boundaries, external calls, dynamic-entry treatment, and continuation behavior before relying on the proposal.

Stage 1C artifacts reportedly created:

- `reverse_engineering/hawker_stage1c.md`
- `reverse_engineering/hawker_stage1c_evidence.json`
- `tools/analyze/hawker_stage1c.py`

Codex reported an independent analyzer replay match and **361 protected files unchanged**. No ROM, live RAM, save, or emulator state was modified.

## 5. Open gates before ROM construction

The architectural question improved substantially, but **the following must still be proved before insertion**:

1. **Script allocation and relocation safety:** Identify and independently validate sufficient non-overlapping space for both private copies and any wrappers/tables. Verify all **77 pointer relocations per copy**, instruction boundaries, embedded data, absolute/external pointers, `FD84` dynamic-entry interactions, and return/continuation behavior. Identify every map/script pointer that will be updated, and preserve source ROM size/translation resources as applicable.
2. **NPC registration and persistent identity:** Prove actor/table capacity and reserved slots (`7`/`8`), conflict-free IDs, event registration, sprite/collision linkage, indexing, progression/event-flag isolation, and room re-entry/save-reload semantics. The earlier check found candidate IDs absent from actor records, but full ownership/indexing was not demonstrated.
3. **Approach movement and collision safety:** Prove practical reachable interaction paths, dynamic actor collision handling, doors/transitions, player/NPC footprints and normal control recovery in each target map. Namp's neighboring blue NPC and Mayonen's doors must work independently. Do not equate a walkable cell with a valid entire path.
4. **Graphics and palette lifetime:** Confirm all 11 Hawker frames and assigned graphics/palette resources survive initial load, deferred/event resource writes, dialogue, exit, and re-entry; do not overwrite Mayonen door palette slot `5`.
5. **Functional equivalence and non-regression:** Ensure private script copies reproduce all relevant exchange branches and share authoritative state without inventing new transaction behavior. Verify original Oystown tutorial, original Hawkers, and unrelated NPCs are untouched. Static verification cannot replace runtime validation.

If any critical gate remains unresolved, **stop without constructing a speculative ROM**. Report exact evidence gaps and the smallest safe follow-up observation or static analysis. Do not call feasibility an implementation PASS.

## 6. Recommended next Codex task

**Task title:** *Hawker Stage 2 — Prove Private-Script Allocation, Registration, Movement and Graphics Safety*.

Suggested instruction:

> Read `AGENTS.md`, the modding plan, `reverse_engineering/hawker_stage1c.md`, Stage 1C evidence/analyzer, and earlier Hawker placement/final-gate reports. Accept the **two parameterized private scripts** as the current *candidate* architecture, not an approved patch. Avoid reopening rejected scratch/saved-return/global-adapter designs absent contradictory evidence. Perform bounded read-only proofs of (1) safe allocation and all 77 internal pointer relocations per copy; (2) actor ID/slot and event/table registration; (3) complete approach/collision/control-recovery paths for map `005F` cell `(25,5)` and map `004D` cell `(14,6)`; (4) graphics/palette lifetime, including protecting Mayonen palette slot 5; and (5) static branch/transaction equivalence. Produce reproducible evidence, a gate-by-gate PASS/BLOCKED table, and precise minimal user-operated debugger observations only if static evidence is insufficient. **Do not construct a ROM until all prerequisites pass.** Do not run mGBA, alter RAM or saves, or launch unrestricted analysis. Preserve protected artifacts.

Once all safety checks pass, a **separate explicitly authorized construction task** can generate a fresh cumulative experimental ROM and patcher, record all byte changes and output hashes, independently read back changes, audit protected artifacts and prepare a manual mGBA runtime checklist.

## 7. Future manual runtime acceptance (not yet performed)

**User operates mGBA; Codex does not.** Test only a newly built, statically gate-passing ROM from isolated, disposable saves/states.

- **Namp:** Hawker visible next to blue NPC; each separately interactive with correct facing/animation; no blocked paths; exchange and event exit recover; room re-entry safe.
- **Mayonen:** Hawker visible between door groups; both door groups remain usable; no palette/graphics corruption; correct approach/return; room re-entry safe.
- **Cross-Hawker:** Valid full-AWE exchange yields exactly two Binkies; selected gauge resets/consumes correctly; all applicable character/story branches, shared state, dialogue, cancellation/refusal, insufficient gauge, inventory capacity, and repeat protection behave as intended.
- **Oystown:** Existing Hawker and first-screen tutorial remain unchanged.
- **Regressions:** Kaizo's 24 thresholds/rewards, Detector 120/25, Rattlin' Dragon 262/54, translation, maps, doors, NPCs, inventory, battle, and save/reload remain correct within tested scope.

Never label static checks as runtime success, and do not infer untested negative-path coverage from successful transactions.

## 8. Preservation rules and session closeout

- Original Japanese/English ROMs, validated experimental ROMs, saves/savestates, research reports, patchers, manifests and hashes are protected.
- Prefer new isolated output paths and reproducible scripts over direct manual hex edits. Preserve separate original and translated/cumulative bus/file address distinctions.
- User alone operates mGBA and issues debugger commands, normally one bounded observation at a time; Codex conducts static investigation and constructs offline patches only on explicit authorization.
- No new Hawker ROM has been produced. No Hawker runtime validation has occurred.
- **Current checkpoint:** `STAGE 1C — LOCALIZED IMPLEMENTATION FEASIBLE`; **allocation, registration, movement, and graphics safety remain open**.
- **Next action:** Stage 2 targeted safety investigation, not yet implementation.
