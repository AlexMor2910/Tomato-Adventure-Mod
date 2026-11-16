# Hawker placement investigation - screenshot-defined targets

2026-10-15. **Investigation only; no placement ROM built.** This supersedes earlier
target-room assumptions, not the accepted gameplay changes. Existing cumulative
input is `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
Detector remains 120 HP / 25 mitigation; Rattlin' Dragon remains 262/54. Kaizo's
completed implementation is unchanged. All 42 artifacts in the Detector build's
protection inventory were rehashed successfully. No emulator/Ghidra operation.

## Screenshot identification

Both screenshots were found in the workspace and visually inspected:

- `screenshots/Captura de pantalla 2026-10-15 185215.png`: Namp shoreline, Alcatraz
  facade and eastern boat landing. Matches reconstructed background of **map 005F**.
- `screenshots/Captura de pantalla 2026-10-15 185326.png`: Mayonen beige walls,
  pink frog, purple paving, central gray door and eastern covered doorway.
  Matches reconstructed background of **map 004D**. This is not map 0048, nor
  the previously considered outdoor maps 0049/004A/004B.

Confidence: **Confirmed static visual match**, not a runtime current-map readback.
Do not infer Namp map 0062 merely because the user called the room the third room.

| Target | Record bus / file | Actor block bus | Existing actors | Candidate new cell |
|---|---|---|---:|---|
| Namp 005F | `0862DE48` / `0062DE48` | `08145010` | 6 | `(25,5)` |
| Mayonen 004D | `0862DC50` / `0062DC50` | `08144388` | 7 | `(14,6)` |

Coordinates are zero-based 16-pixel map cells. Namp's relevant existing NPC is
actor 3 at `(26,5)`, record `081450A0`, interaction `081130ED`; proposed `(25,5)`
is directly left. Mayonen actor 1 starts `(10,6)`, while door actors 4/5 are at
`(10,4)`/`(11,4)` and actors 6/7 at `(18,5)`/`(18,6)`. Proposed `(14,6)` is in
the upper walkable area between those door groups. Neither candidate overwrites
an existing actor record or shares its initial cell with an existing occupant.

Both candidate cells read **00 in original base collision data**, addressed via
file `00303950 + 4*mapID`. Exact collision addresses and neighboring actor data
are in the adjacent JSON. This is necessary but insufficient to certify complete
runtime accessibility: active actor positions, script overlays, sprite footprint
and layer priority still need resolution. Coordinates remain **Candidate** until
those checks are complete; no pixel-perfect runtime placement is claimed.

## Background reconstruction

`tools/analyze/hawker_room_preview.py` reads the existing map tables and writes
new local PNGs only. The translation toolkit's `inserter/tiles.cpp` establishes
16x16 chips composed of four 8x8 tile references. Palette table file 00255F00,
compressed tileset pointers 0015BA3C, layer chipmaps 0026E358, chipsets 0031E7B4.
RLE/LZ77 graphics are decoded without emulator execution; 4bpp tile palettes and
H/V flips are applied. Background images omit actors and unloaded reserved/
animation tiles, so they are identification previews rather than exact runtime
screenshots or collision simulations. Map005F preview omits indices 768..771
and 1023; map004D omits 1023. The architectural matches remain clear.

Matched previews:
`exports/hawker_room_recon/map_005F_background.png` and
`exports/hawker_room_recon/map_004D_background.png`.

Other explicitly bounded candidate previews were generated to rule out incorrect
rooms. These are local ignored PNGs, not modifications to game graphics.

## Existing two-Binky Hawker

The established AWE exchange is **not an ordinary item-stock table**. Shared entry
`08107E81` leads to body `08107E90`; existing source-specific wrappers are:

| Existing map / actor | Actor record | Interaction wrapper |
|---|---|---|
| 00D7 / 4 | `0814B390` | `08102D37` |
| 0104 / 3 | `0814D4C4` | `08102D27` |
| 0149 / 3 | `08151198` | `08102D47` |
| 015D / 5 | `081521C8` | `08102D57` |

Each wrapper supplies two FD01/FD02 halfwords and calls `08107E81` through FD2F.
For example Oystown uses `FD01 8600`, `FD02 8700`; the wrapper at `08102D37`
uses `FD01 3600`, `FD02 7100`. These are observed transient operands, not
new progression requirements; their complete consumers must be traced before
selecting a relocated wrapper. Existing actors differ in graphics binding and
control bytes, so copying a record without its resources is insufficient.

The shared script has actor/event commands including FE01, FD84 and FE31;
transaction/end paths repeatedly contain `FE31 03 01`. The operand semantics
and actor-context behavior must be established before deciding whether reuse
needs a minimal binding wrapper. Do not assume literal 03 identifies a local
actor slot merely from its value.

Existing behavior to preserve: retirement/exhaustion flag 1FC; BA/1C4 selection
branches; eligible companion/full AWE 40; item37 acquisition and existing capacity
cutoffs; successful two-Binky award and selected-gauge reset; all original
dialogue, cancel/refusal/return paths. Oystown introduction `081084CA` and guard
1F4 are separate and must not be triggered in the new rooms. Earlier reports
document six user-confirmed exchange-rate scenarios; relocation is untested.

## Open service-scope question

The earlier final objective specified the **two-Binky AWE exchange**. The new
request also mentions a shop inventory. No new inventory is to be invented.
A clarification was requested: exchange, existing item shop, or both. This affects
which original actor/scripts/resources must be reused. Until answered, neither a
shop nor a combined service is inferred from the word Hawker.

## Remaining implementation prerequisites

- Resolve the requested service and trace its complete actor/palette/graphics
  configuration, including availability and any shop stock if applicable.
- Verify transient wrapper operands and context-sensitive script commands;
  avoid manipulating original NPCs or the player through an incorrect binding.
- Existing actor tables have room under the 15-record loader limit, but their
  terminators do not establish writable padding. Safest candidate architecture
  is a separately allocated copy of each actor block with the existing records
  byte-identical and one appended actor, then relocate only the map +14 pointer.
  Free/reserved ROM space, resource-slot capacity and persistence IDs have not
  been approved by evidence yet; do not overwrite neighboring map records.
- Preserve existing graphics/palette references, initializers, actor identities,
  door triggers, NPC interactions, encounters and map appearance. Determine
  visibility/collision flags rather than guessing them.
- Recheck the candidate coordinates against complete active-state behavior;
  runtime navigation and interaction will remain user-operated validation.

No ROM patch was made while these details remain unresolved. Machine-readable
evidence is `hawker_placement_investigation.json`. This report and preview helper
are new artifacts; existing enemy and Kaizo reports were not rewritten.

### Subsequent scope confirmation and safety audit

The user subsequently confirmed the existing two-Binky AWE exchange only, both
map IDs/candidate cells above, and preservation of the Oystown tutorial. The
service-scope question is closed. See
[hawker_placement_safety_followup.md](hawker_placement_safety_followup.md) and
`hawker_placement_safety_evidence.json` for new bounded native traces, including
the literal actor3 state dependency and wrapper argument indirection. Placement
remains unimplemented under the user's critical-dependency stop condition.
