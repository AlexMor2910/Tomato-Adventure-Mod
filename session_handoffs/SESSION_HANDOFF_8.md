# SESSION_HANDOFF_7 — End-of-day project handoff

**Date:** 2026-10-15  
**Status:** Session paused. **The most recent Hawker implementation prompt has NOT been sent to Codex.** No Hawker-placement ROM has been created.  
**Priority for next session:** Complete the remaining Hawker safety checks, then implement the two placements *only if* they pass.

> **Document note:** This handoff is based on the Codex results reported in the conversation. It is a standalone updated Session 7 handoff for copying into the repository at `session_handoffs/SESSION_HANDOFF_7.md`; no repository files were directly inspected or modified in this chat.

## 1. Decisions and confirmed project state

- **Kaizo principal objective: COMPLETE.** Codex documented 24/24 rewards and user-confirmed runtime success of native 94-Binky acquisition; no final counter readback of 100 was supplied. Do not reopen Kaizo.
- **Gimmick Palace enemy research:** Detector (`A5`) and Rattlin’ Dragon (`9C`) were visually confirmed by the user after Codex reconstructed two transparent sprite frames for each.
- **Detector rebalance:** implemented in a separate cumulative experimental ROM and **statically verified**, **not runtime tested**. Detector HP changed **135 → 120**; base mitigation **38 → 25**. This shared-species modification affects Detector wherever encountered.
- **Rattlin’ Dragon:** deliberately **unchanged**, HP **262**, base mitigation **54**. It remains a powerful late-game challenge.
- **Hawker placement:** **FINAL MAJOR OBJECTIVE; NOT IMPLEMENTED**. User wants identical **two-Binky AWE exchange** at all Hawkers, including identical rewards, costs, dialogue, conditions and exchange state. The tutorial remains triggered on the **first screen of Oystown**, not by the added Hawkers.
- **Latest action:** The proposed “Final Hawker Objective — Complete Safety Checks and Implement” prompt was drafted in ChatGPT but **the user explicitly has not pasted it into Codex**. Start the next session from that point, not as though implementation was attempted.

## 2. Detector experimental ROM and evidence

**Output ROM:** `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`  
**Reproducible patcher:** `tools/patch/detector_rebalance.py`  
**Report:** `reverse_engineering/experiments/detector_hp120_mit25.md`

| Field | ROM bus address | File offset | Original bytes | New bytes |
|---|---|---|---|---|
| Detector A5 HP | `08638056` | `00638056` | `87 00` (135) | `78 00` (120) |
| Detector A5 mitigation | `0863805A` | `0063805A` | `26 00` (38) | `19 00` (25) |

Independent readback confirmed 120/25. Full-ROM comparison found exactly two changed bytes. All other enemy records, Detector AI/attacks/graphics/rewards/formations, and Rattlin’ Dragon stats remained unchanged. Header checksum passed. At the time of the patch, 42 protected artifacts retained their hashes. **Runtime Detector testing was deferred** because reaching the enemy is cumbersome; do not represent it as verified in-game.

Research and sprites:

- `reverse_engineering/gimmick_palace_enemy_research.md`
- `reverse_engineering/gimmick_palace_enemy_evidence.json`
- `reverse_engineering/palace_enemy_sprite_investigation.md`
- `tools/analyze/extract_palace_enemy_sprites.py`
- `reverse_engineering/exports/palace_enemy_sprites/` (Detector A5 40×40; Rattlin’ Dragon 9C 80×40; two transparent native and 4× enlarged frames each)

The sprite extractor is reproducible for the investigated enemies; universal enemy support was not established.

## 3. Hawker targets and requested positioning

User identified both rooms via screenshots and confirmed these placements:

| Location | Map ID | Hawker cell | Context | Reserved NPC slot | Graphics slot | Palette slot | Candidate approach target (pixels) |
|---|---|---|---|---|---|---|---|
| Namp Lagoon, third room | `005F` | `(25,5)` | Upper-left; directly left of blue NPC at `(26,5)` | 7 | 7 | 7 | `(407,111)` |
| Mayonen, room before caverns | `004D` | `(14,6)` | Upper side between both door groups | 8 | 5 | 6 | `(231,127)` |

Base-collision checks show the destination cells are in bounds and walkable. **Complete approach paths, full sprite/interaction footprints and dynamic collisions have not yet been certified.** Mayonen palette slot **5 must stay intact** because door actors reference it; proposed new Hawker palette slot is **6**.

## 4. Hawker dependency investigation — confirmed findings

Codex resolved several earlier blockers without producing a ROM:

- The shared two-Binky exchange contains **ten `FE31 03 01` occurrences**, distributed across **five offer branches and five advice/refusal/exit branches** (not ten writes per conversation).
- In `FE31`, `03` selects **actor slot 3** and `01` selects that actor's **normal directional animation controller**. Namp's slot 3 belongs to the **existing blue NPC**; naive script reuse would alter the wrong actor.
- The interaction dispatcher records the clicked NPC's actor slot at RAM **`0x03003A32`**. FE31's existing **`FD` operand** can read this binding. **Do not globally replace FE31 operands or change existing Hawkers:** any adaptation must be narrowly scoped to the two new instances.
- **`FD01` supplies pixel X**, **`FD02` supplies pixel Y**. **`FE01`** hands the approach continuation to **player actor 0**, correcting an earlier interpretation.
- The Hawker's **11 frames** and resource layout were traced, and graphics capacity was judged sufficient. Resource *lifetime* still needs validation.
- Proposed design: **room-specific movement wrappers + unchanged shared exchange + narrowly guarded FE31 actor-binding adapter for the two new Hawkers**. This is a recommendation pending the outstanding safety checks, not a completed implementation.

Evidence and analysis files:

- `reverse_engineering/hawker_placement_investigation.md`
- `reverse_engineering/hawker_placement_investigation.json`
- `reverse_engineering/hawker_placement_safety_followup.md`
- `reverse_engineering/hawker_placement_safety_evidence.json`
- `tools/analyze/hawker_placement_safety.py`
- `reverse_engineering/hawker_dependency_resolution.md`
- `reverse_engineering/hawker_dependency_resolution_evidence.json`
- `tools/analyze/hawker_dependency_resolution.py`

## 5. Explicit outstanding safety checks (before any Hawker patch)

1. **Scratch-binding lifetime:** verify how long `0x03003A32` remains valid, including interrupted dialogues, nested calls, continuation paths and any writes that could replace the clicked actor slot.
2. **Scoped FE31 adapter:** establish exact correctness for only the new Hawkers; prove existing Hawkers and other NPCs retain original semantics. Favor a fail-safe fallback to existing behavior outside the new context.
3. **Approach trajectories:** validate complete movement from all practical reachable directions at both maps, including dynamic actor collisions, doors/transitions and restoration of player control. Adjust coordinates only with documented evidence.
4. **Graphics/palette lifetime:** confirm that all 11 frames and palette/graphics bindings survive room entry, conversation and re-entry without disrupting current actors, especially Mayonen door palette slot 5.
5. **Persistent actor IDs:** verify conflict-free identifiers and actor limits, interaction registration, progression flags and behavior after map re-entry / save-state or reload as applicable.

If any critical dependency remains unproved, **stop without patching** and report precise evidence and a safe alternative. Do not relax safety criteria to finish faster.

## 6. Next Codex task — paste during the next session

**Task:** *Final Hawker Objective — Complete Safety Checks and Implement*.

Give Codex the paths in Sections 3–4 and the five checks in Section 5. Instruct it to:

- Avoid repeating already evidenced general research; resolve the concrete remaining checks.
- If and only if all checks pass, add one functional Hawker at **Namp `005F` `(25,5)`** and one at **Mayonen `004D` `(14,6)`**, using the reserved NPC/graphics/palette allocations unless evidence requires a documented change.
- Retain the **unchanged authoritative two-Binky AWE exchange**, with room-specific approach wrappers and narrowly scoped FE31 handling. Every Hawker must have identical transaction behavior; no new tutorial triggers.
- Build a **new cumulative experimental GBA ROM**, preserving Kaizo and Detector 120/25, with Rattlin’ Dragon 262/54 and all existing maps, NPCs, doors and exchanges unchanged except narrowly necessary additions.
- Supply a reproducible patcher, full changed-offset/byte ledger, independent readback and regression/integrity checks, plus a runtime test checklist.
- **Never call static verification runtime success.** If blocked, report findings and leave the cumulative ROM untouched.

The actual final prompt drafted in the conversation was **not submitted to Codex**. It can be reused next session or replaced with a more concise implementation instruction based on this handoff.

## 7. Verification baseline and future runtime checklist

Most recent Codex investigation reported **43 protected game artifacts unchanged**, cumulative experimental ROM hash preserved, Detector **120/25** and Rattlin’ Dragon **262/54**. **No Hawker-placement ROM was built and no Hawker runtime test occurred.**

When a new Hawker ROM is finally built, test in emulator:

- **Namp:** Hawker appears beside blue NPC; each can be talked to independently; exchange works; room exit and re-entry remain stable.
- **Mayonen:** Hawker appears between doors; doors, approach movement, graphics and exchange work; re-entry remains stable.
- **Cross-Hawker:** identical two-Binky costs/rewards/dialogue/conditions and shared state; no duplicate or unintended rewards.
- **Oystown:** first-screen tutorial still activates in its established location; existing Hawker exchange is unaffected.
- **Regression:** previous Kaizo gameplay and Detector balance remain represented in cumulative ROM; Rattlin’ Dragon remains unchanged.

## 8. Session closeout

**Kaizo: COMPLETE** · **Detector rebalance: STATICALLY VERIFIED, RUNTIME PENDING** · **Rattlin’ Dragon: UNCHANGED** · **Hawker analysis: ADVANCED, PLACEMENT PENDING** · **Last Codex implementation prompt: NOT SENT**.

**Next action:** Resume with the five Hawker safety checks. Authorize implementation only after they pass. Keep the original and current cumulative experimental ROMs intact.
