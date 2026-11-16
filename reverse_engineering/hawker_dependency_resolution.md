# Hawker actor and movement dependency resolution

2026-10-15. **Static research; no placement ROM built.** This resolves the
animation-mode and movement-encoding questions from the safety follow-up.
It corrects that report's FE01 ownership interpretation. The remaining
implementation checks are listed explicitly below; no gameplay was modified.

Evidence: `hawker_dependency_resolution_evidence.json`, reproducible with
`python -B tools/analyze/hawker_dependency_resolution.py`. Input is the same
16-MiB Detector cumulative ROM, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
ROM bus addresses below are English cumulative addresses; subtract `08000000`
for file offsets. RAM addresses have no ROM file offset.

## FE31: resolved semantics

**Confirmed static:** FE31 takes an actor selector followed by an animation
controller mode. Literal03 is actor slot3. Handler `08028ED0` resolves its first
operand through `08022798`, then calls `08065E4C`, which writes
`actor[3] = (actor[3] & F8) | mode` at actor base `03001BDC + 30*slot`.

The consumer at `08035D98..08035DBC` extracts those three bits and dispatches
through the eight-entry table at `08035DC8`:

| Mode | Dispatch address | Established behavior |
|---:|---|---|
| 0 | 08035F2E | Return without this animation-controller update |
| 1 | 08035DE8 | Normal directional animation controller |
| 2 | 08035EB0 | Separate controller; complete meaning not needed/claimed here |
| 3 | 08035E66 | Separate animation sequence controller with completion handling |
| 4,5 | 08035EF8 | Separate controller; not renamed here |
| 6 | 08035E14 | Calls 08035F38; separate controller |
| 7 | 08035E1A | Related directional animation controller |

For **mode1**, `08035DE8..08035E0A` reads and clears the actor's movement/change
flag in `03001B27[slot]`. If set, `08035E3C..08035E4C` maps actor field+4 through
`0813A3F8` and selects an animation using `0803310C`. Otherwise
`08035E5C..08035E64` calls `08033218`, which advances the animation timer, frame
pointer and composition pointer. That routine's frame-duration comparison and
FFFF loop marker handling are visible at `08033218..080332D0`.

Thus `FE31 03 01` **sets actor3 to its normal directional animation controller**.
It does not directly set a direction, teleport, or toggle visibility. Direction
is actor field+4, position is +28/+30; the separate enable/hide helper `08065DC0`
alters field+2 bit0. FE31 itself does not immediately replace the current frame;
the controller acts during subsequent actor updates.

### All ten uses

| FE31 command bus | Role in the exchange control flow |
|---|---|
| 08107F56 | Offer in first character1 transaction block |
| 08107F8D | Offer in character2 transaction block |
| 081080FB | Offer in alternate character1 transaction block |
| 08108132 | Offer in another character1 transaction block |
| 08108169 | Offer in character3 transaction block |
| 0810819C | Advice dialogue path, message4B8 |
| 081081A8 | No-full-gauge dialogue path, message4B9 |
| 081081B4 | Refusal/cancel dialogue path, message4B6 |
| 081081C0 | Capacity-rejection continuation, message4BA |
| 081081CC | Retirement-flag continuation, message4BB |

These are **ten branch sites**, not ten writes executed for every conversation.
A chosen offer can execute its write and later a refusal/capacity-path write.
Every site chooses the same controller before the following dialogue.
The branching structure explains the repetition. Restoring ordinary Hawker
animation is a **Probable intent**, not proof of the original author's reason.

The opcode does not require its target to be a Hawker. Original maps00D7 and015D
put their exchange NPCs in slots4 and5 while this script still addresses3.
Therefore globally replacing3 with a different selector would change existing
behavior. The fact that an original NPC can tolerate that write is not evidence
that Namp's blue NPC should receive it.

### Verified engine binding for a new Hawker

**Confirmed static:** native NPC interaction dispatch at `0806974A..0806977E`
selects record `(clicked_slot - 1)*10` from `03001948` and reads its +A interaction
pointer. At `080697C8..080697D4` it writes the clicked slot to scratch halfword
`03003A24+14` = **03003A32**, then starts the event. The resolver's existing
operand **FD** reads that exact halfword (`080227D4..080227D8`).

Consequently `FE31 FD 01` can address the clicked NPC without hard-coding7/8,
provided that scratch14 still belongs to this interaction. Entry gates at
`08069728..08069748` and interaction locking at `08069D60..08069D6E` prevent
another ordinary NPC interaction while one is active. This establishes the
ordinary ownership route; transitive callees still require a write audit before
treating scratch14 as immutable across the entire exchange.

Other explicit actor-sensitive operations in the bounded exchange entry are
`FE01 00`, indirect main command36, and main command `2F 00`. Main2F handler
`08023D80` uses the current context, lookup `0863A024`, and `0803E4A8`; it updates
direction field+4 and selects an animation. It must be preserved with the
movement continuation, not mistaken for transaction logic.

## Movement encoding and ownership: resolved

### Correction to the previous FE01 interpretation

The previous report said FE01 installed the **body** on actor0. The complete
trace shows the reverse transfer for this entry. That earlier conclusion is
superseded here.

The VM predecodes and advances the current event's cursor before dispatching its
handler (`08022388..0802250C`, then `08021F30`). At `FE01 00 90 7E 10 08`:

1. `08028880..0802889C` reads explicit destination **08107E90** and saves the
   current event's already-advanced continuation **08107E88**.
2. `080288AE..080288B6` passes that saved continuation to `0806AAA0` for explicit
   actor/event0. This is the player continuation.
3. `080288BA..080288EE` installs the explicit destination08107E90 into the
   original event context and saves linkage/return information for actor0.

Therefore actor0 executes **FD84 movement at08107E88 and facing at08107E8E**;
the original interaction event executes the transaction body08107E90. The
movement target is the **player**, not the new Hawker or Namp's blue NPC.
FF means current event context and is not a safe replacement for the Hawker's
literal3; the body context can be a general event rather than a map actor.

### Coordinates and byte order

**Confirmed static:** FD01 stores a little-endian halfword at scratch+6; FD02
stores one at scratch+8. `FD84 00 36 06 08` supplies these four scratch bytes to
main command36. Handler `08023CA4..08023CFE` reverses their argument staging;
`080663C0..08066494` reconstructs the halfwords and compares them with the
current actor's pixel coordinates. The resulting assignments are:

| Wrapper command | Target | Actor field |
|---|---|---|
| FD01 | X pixel coordinate | +30 |
| FD02 | Y pixel coordinate | +28 |

Map initialization proves the origin and units: actor Y tile coordinate at+34
becomes `16*y + 15` at field+28 (`08033820..08033856`); actor X tile coordinate
at+35 becomes `16*x + 7` at field+30 (`08033858..0803388A`). Signed actor offsets
from byte5 are subsequently added (`0803388C..08033906`). Neither target is a
path index or actor ID. Command36 requests movement by the target deltas; it is
not an unconditional position write. Large deltas encounter rejection branches,
so target encoding alone does not prove a traversable approach.

For the proposed zero-offset Hawkers:

| Room/cell | Hawker anchor X,Y | Candidate player approach cell | Player target X,Y | FD01 / FD02 halfword bytes |
|---|---|---|---|---|
| Namp005F (25,5) | 407,95 | (25,6) | 407,111 | `97 01` / `6F 00` |
| Mayonen004D (14,6) | 231,111 | (14,7) | 231,127 | `E7 00` / `7F 00` |

**Confirmed:** these target cells are in bounds and their original base collision
bytes are00. **Candidate:** these are appropriate full approach destinations.
They are not approved patch bytes yet. Collision traversal from every available
interaction side, pixel offsets, dynamic actor occupancy and movement completion
still need independent verification. In Namp row4 at x24..26 is18; in Mayonen
(14,8) is18. Those nearby boundaries must be included in the approach check.

## Graphics, palettes, footprints and slots

**Confirmed static:** loader `0803411C..08034240` iterates **16 graphics
descriptors** followed by **12 palettes**. `080340C0..08034100` copies descriptor
byte3 times32 bytes directly from descriptor+4 into sequential OBJ VRAM starting
06010000; it does not decompress these tiles. Palette copies are32 bytes each.
Actor initialization reads dimensions from descriptor bytes0/1 into fields7/8,
and animation/composition tables from descriptor+8/+12. Collision rectangle
tests consume fields7/8 at `0803DF48..0803E02C`. Renderer `080332DC..08033396`
consumes a u16 part count followed by six-byte GBA OAM parts and supplies the
actor's tile base and palette bank. These are verified formats, not guessed
dimensions from the descriptor's first two bytes.

Hawker resource descriptor **0813F77C**, file0013F77C:

| Resource | Bus / file | Meaning |
|---|---|---|
| Descriptor bytes0/1 | 08 / 08 | Collision dimension parameters |
| Descriptor byte3 | 33 | 51 4bpp tiles, 1632 bytes |
| Tile data | 0840C96C / 0040C96C | Direct copy, through file0040CFCC exclusive |
| Palette | 0843C3CC / 0043C3CC | Original32-byte Hawker palette |
| Animation table | 08451E78 / 00451E78 | Four animation-sequence pointers |
| Composition table | 08444860 / 00444860 | Eleven frame pointers |

The four animation sequences contain frame/duration pairs:
0: `3/12,4/12,3/12,5/12`; 1: `0/12,1/12,0/12,2/12`;
2: `0/4,6/6,7/6,10/4,9/4,10/4,8/4`; 3: `8/6,9/6`.
Each ends at FFFF. Durations are encoded animation units; no measured FPS claim.

| Frames | OAM rectangle bounds relative to anchor, right/bottom exclusive |
|---|---|
| 0..6 | (-8,-24) to (8,0), 16x24 |
| 7 | (-16,-24) to (8,0), 24x24; six parts |
| 8,9 | (-8,-20) to (8,4), 16x24 |
| 10 | (-7,-20) to (9,4), 16x24 |

These are composition rectangles, not opaque-pixel or collision rectangles.
Namp's immediately adjacent blue NPC makes frame10's one-pixel extension beyond
the normal right edge relevant to the visual check; it is not proof of opaque
overlap or collision. Preserve the agreed cells pending that check.

| Map | Append actor slot | Free graphics slot | Free palette slot | OBJ tiles before -> after |
|---|---:|---:|---:|---:|
| 005F | 7 | 7 | 7 | 308 -> 359 |
| 004D | 8 | 5 | 6 | 136 -> 187 |

The actor loader limit is15 NPC records plus player0. Existing slots remain
unchanged if a complete relocated actor block appends the new record. Both
graphics totals are well below the1024-tile OBJ space. **Mayonen palette5 is
already referenced by door actors**, despite initially holding the default
palette; it cannot be repurposed. Palette6 is unreferenced by its existing actors.

A bounded inventory of494 map records found2987 actor records, maximum persistent
ID0B9B. IDs0BFE/0BFF are absent from those actor records, but are **Candidate IDs**,
not yet certified free of script references or saved-flag use. Original actor
records, transitions, base collisions and room default scripts remain untouched.

## Architecture decision

| Strategy | Assessment |
|---|---|
| A: transaction separated from actor sequence | Clean conceptual separation, but removing movement/facing or controller writes changes interaction choreography. More behavioral scope than necessary. |
| B: room wrappers plus shared reward body | **Recommended.** Keep08107E81/08107E90 and every reward/progression branch authoritative; new wrappers provide only the verified room-specific player approach targets. Add a narrowly scoped actor-binding adapter. |
| C: relocated/duplicated exchange | Feasible fallback if B cannot be safely bound. Relocation must fix all internal branches and return/linkage entries. Duplicated rewards are avoidable and could diverge. |

For B, do not globally replace all ten operand03 bytes with FD. Preserve existing
rooms' exact behavior. A **Candidate native adapter** can delegate the original
FE31 handler except when all these guards match: map005F/004D, one of the ten
exchange command sites, literal actor03, and clicked-NPC scratch14 equal to the
new room's appended slot7/8. Only that case substitutes the clicked slot; mode1
and all other command behavior remain unchanged. This preserves a single
authoritative exchange script and all original tutorial/reward logic.

The FE31 dispatch pointer is at **0862B978 / file0062B978** (table0862B8B4,
entry31), currently Thumb pointer08028ED1. A replacement handler and wrappers
would be newly allocated data/code; no change has been made to that pointer.
An adapter must reproduce the native argument-fetch ordering and caller register
contract. Its command-site guard must use the actual argument cursor after the
first fetch (expected site+3), rather than assume a PC value from opcode names.
This design is **Candidate**, not a verified executable patch.

## Remaining precise implementation gate

The opcode semantics, clicked-NPC binding, FE01 player ownership, target encoding,
slot capacity and resource formats are now established. Both rooms have room for
one additional Hawker. They are **not yet certified as a safe complete build**:

1. Audit transitive exchange callees for scratch14 writes and independently verify
   a concrete adapter's command-cursor guard, fallthrough behavior and register
   preservation. No adapter machine code has been assembled/verified in this task.
2. Verify command36 completion/collision behavior for approaches from every
   accessible side, including Mayonen's nearby row8 obstacle and Namp's blue NPC.
   The current evidence proves destination encoding and base walkability, not the
   complete movement trajectory or interaction reach rectangle.
3. Finish palette/VRAM lifetime checks through room events, the Namp gesture's
   opaque footprint check, and persistent actor-ID/script ownership validation.
   Resource initialization capacity alone does not certify every later event.

Under the user's implementation boundary, no speculative ROM was built. This is
not a request to alter accepted coordinates or gameplay. The Oystown tutorial
remains separate and unchanged; Kaizo, Detector and Rattlin' Dragon are untouched.
The previous report's runtime checklist still applies after a verified build.

## Artifacts and validation

Added this report, `hawker_dependency_resolution_evidence.json`, and
`tools/analyze/hawker_dependency_resolution.py`; older reports receive correction
links only. The helper reads29 explicit native windows, the bounded exchange,
11 compositions, four animation sequences, the two resource headers, and the
494-record map table for persistent-ID inventory. No emulator or Ghidra execution.
Its output was reproduced and compared with the saved evidence. Protected game
artifact hashes were compared with the prior43-artifact ledger; all unchanged.
No new ROM, patcher, RAM write, gameplay change, or runtime success is claimed.
