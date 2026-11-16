# Hawker Stage 2 — construction readiness

2026-10-17. **Construction is blocked.** The private-script allocation and
relocation design passes. Persistent bit ownership, movement in active room
states, and resource-writer lifetime do not yet have complete proofs. These are
missing proofs, not observed failures. No ROM or private script was constructed;
no emulator, RAM, save, or savestate was operated or changed.

Reproduce: `python -B tools/analyze/hawker_stage2.py`. The analyzer prints JSON;
save a replay to a new temporary path, not over historical evidence. Companion:
`hawker_stage2_evidence.json`. The handoff's provenance warning was respected:
actual ROM, prior JSON, analyzers, allocation producer and manifests were read.

All ROM addresses below refer to the **English cumulative input**, not newly
verified Japanese locations. File offset = bus address minus `08000000`.
Ranges are half-open. Native function names are analyst labels, with exact
roots in the analyzer's `roots` dictionary; they are not recovered game symbols.

## A. Executive gate summary

| Gate | Result | Evidence | Remaining blocker |
|---|---|---|---|
| Script allocation/relocation | PASS | Pinned expansion producer/ancestor establishes ownership of the reserved area; exact ranges below. Independent length-table decode covers 164 commands/857 bytes, 77 internal pointers, 28 external pointers, ten FE31 operands. | None for the specified candidate architecture. Allocation does not certify table contents under B. |
| NPC registration/identity | BLOCKED | 15-record copy capacity; slots7/8 append without renumbering; exact map pointers/records captured. New trace proves the ID bit bank and its 384-byte save/load mapping. | Ownership and initial-state contract of bits0BFE/0BFF; complete initializer/registration lifetime. |
| Movement/collision | BLOCKED | Complete bounded direct CFG of scheduler080664A8 and rectangle routine0803DF48; exact active-controller roots and candidate neighborhoods captured. | Reachable interaction origins, dynamic controller trajectories/footprints, transition intersections and completion in those states have not been composed into a path proof. |
| Graphics/palette lifetime | BLOCKED | Existing resource format/11 frames reused; exact header edits, initial free slots and stable preceding tile allocations established. Deferred Mayonen actor controller found in current bytes. | Complete room/event resource-writer closure through deferred initialization, interaction and re-entry. |
| Exchange equivalence/regression | BLOCKED | **Static exchange transformation passes**; all source fields match Stage1C; cumulative baseline/51 Kaizo ledger bytes and enemy values checked. | Full gate includes original NPC/door preservation, which depends on B/C/D. No semantic failure found in the private exchange schema. |

## B. Exact construction specification

### Input, provenance and preservation

Required input: `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`,
16,777,216 bytes, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.

Independent comparison to pinned Kaizo parent
`7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`
again finds exactly file00638056 `87→78` and0063805A `26→19`.
All 51 Kaizo manifest ledger bytes match. Detector120/25 and Dragon262/54
read back correctly; header complement is valid. Thus the current translation,
original Hawkers/tutorial, Alessa wrapper and cumulative parent modifications
remain byte-identical outside those two accepted Detector changes. This verifies
the input; it does not verify behavior of an unbuilt integration.

The evidence records before/after fingerprints for protected ROMs, saves,
states, prior reports, manifests and source tools. Every recorded file matched.
No commit was made. `.editorconfig` was absent at workspace root; new Python
uses tabs, UTF-8 and final newline.

### Gate A: exact owned allocation

**Confirmed static ownership**, not an inference from FF bytes: inspect
`tools/patch/alessa_recruitment_wrapper.py` (`INPUT_SIZE`, `OUTPUT_SIZE`,
`RESERVATION_SIZE`, `build`, `verify_output`) and its pinned manifest in
`tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f/`.
The producer hash matches that manifest. Its pinned actual ancestor has an
8-MiB input and deliberately creates the 8-MiB expansion, reserves
file00800000..00800020 and verifies every remaining expansion byte as padding.
The current input's **entire suffix00800020..01000000 equals that ancestor**.
This is producer-owned expansion, outside the original translated 8-MiB image,
not a hole selected inside unknown game/translation data. The old Alessa
reservation, including its unused tail, remains excluded.

| Allocation | File start..end | Bus start..end | Bytes |
|---|---|---|---:|
| Namp private body | 00800020..00800379 | 08800020..08800379 | 857 |
| Alignment padding | 00800379..0080037C | 08800379..0880037C | 3 |
| Namp wrapper | 0080037C..0080038C | 0880037C..0880038C | 16 |
| Mayonen private body | 0080038C..008006E5 | 0880038C..088006E5 | 857 |
| Alignment padding | 008006E5..008006E8 | 088006E5..088006E8 | 3 |
| Mayonen wrapper | 008006E8..008006F8 | 088006E8..088006F8 | 16 |
| Namp relocated resource/actor block | 008006F8..008007E8 | 088006F8..088007E8 | 240 |
| Mayonen relocated resource/actor block | 008007E8..008008E8 | 088007E8..088008E8 | 256 |

Expected input bytes in each destination are FF repeated for its length; exact
per-range SHA-256 is in JSON `allocation.ranges`. Starts are four-byte aligned;
bytecode itself need not have aligned internal instructions/pointer fields
(the source entry is unaligned). All proposed starts/ends are disjoint, within
the existing16-MiB image and the GBA ROM address window; output size stays
01000000. No new native code, dialogue, graphics payload, scratch data, event
table, global hook or continuation stack is allocated by this design. Existing
graphics/palette/animation data remain shared read-only resources.

### Script boundaries and independent relocation inventory

Source file00107E81..001081DA / bus08107E81..081081DA, exactly857 bytes;
SHA-256 `0c320e92fdcd968fe2d80c2b6005effd0060952cd6bb5623bbf79e50cb8fbd6d`.
The next command at081081DA belongs outside the chosen source extent; the
extent is a bounded control-flow closure, not a claim that the following bytes
are padding. All164 commands consume the extent exactly. No unclassified opcode
or embedded-data gap occurs within it. All internal destinations are decoded
command starts, including the retained locally unreferenced block.

`hawker_stage2.py:commands` independently reads native operand lengths from
0062B6C4/0062B736/0062B815, rather than importing Stage1C's decoder or relocation
dictionary. The separately transcribed typed field inventory agrees with
**every** Stage1C field address and target:77 internal code pointers,28 external
dialogue pointers, and ten actor operands. The JSON has the complete manifests
for **each copy**, with source field address/bytes, destination field address,
old/new target, and exact little-endian replacement bytes. No raw four-byte
pattern search is used to infer pointer types.

For body bus base B: each typed local pointer P becomes
`B + (P - 08107E81)`; each external pointer stays byte-identical. Every other
source byte stays unchanged except the ten FE31 selector bytes `03→07` or
`03→08`. FE31 mode01 stays unchanged. One common parameterized schema must
implement this rule; independent manually maintained forks are prohibited.

The only FD84 is08107E88 `FD 84 00 36 06 08`: fixed command36 with scratch
coordinate operands, not a dynamic script destination. Reused Stage1C native
FE01/FD84/FD7D evidence remains tied to the same pinned whole-ROM input.
FE01 gives actor0 B+7 and the original interaction B+F:
Namp08800027/0880002F; Mayonen08800393/0880039B. Preserve main2F at B+D.
FD7D may end the event **or consume external continuation03003A20**. Its eleven
sites stay native; no assumption that this global is zero, and no relocation of
an external caller's continuation. No nested FD2F/FD31/FD75/FD7C exists in the
copied extent. These are static native-contract findings, not runtime evidence.

Wrappers, exact proposed bytes:

- Namp at0880037C: `FD 01 97 01 FD 02 6F 00 FD 2F 20 00 80 08 FD 7D`.
- Mayonen at088006E8: `FD 01 E7 00 FD 02 7F 00 FD 2F 8C 03 80 08 FD 7D`.

The wrappers preserve existing FD01/FD02/FD2F/FD7D form. Their player targets
(407,111)/(231,127) remain **Candidate trajectories under Gate C**.

### Gate B: exact table operations, pending record approval

| Operation | Namp | Mayonen |
|---|---|---|
| Map record bus | 0862DE48 | 0862DC50 |
| Existing block bus | 08145010 | 08144388 |
| Map +14 pointer field, file | 0062DE5C | 0062DC64 |
| Expected pointer bytes | `10 50 14 08` | `88 43 14 08` |
| Proposed pointer bytes | `F8 06 80 08` | `E8 07 80 08` |
| Existing actor count / new slot | 6 /7 | 7 /8 |
| Header bytes copied | 70 hex | 70 hex |
| New record offset in block | D0 | E0 |
| New record bus | 088007C8 | 088008C8 |
| Terminator record bus | 088007D8 | 088008D8 |

Copy all original16-byte actor records byte-identically, at the same indices.
Append one16-byte actor and a16-byte terminator whose first byte is FF. Do not
overwrite either original terminator/neighbouring block. JSON `maps` records
every original record and the entire expected header, so preservation is
reviewable byte-for-byte. Door/transition/event-table pointers are unchanged.

**Confirmed:** native08034ED4..08034F50 copies112 header bytes followed by up
to15 records, with FF termination. Slots7/8 fit. Native08034244 loader starts
slot1, strides16 source bytes and48 runtime actor bytes. Dispatcher0806974A
uses `(slot-1)*16`, reads interaction pointer at+A and registers it through
0806AAA0. This confirms the table/slot linkage, not persistent ownership.

Pending actor field specification: derive both records from existing Oystown
Hawker record0814D4C4 (`28 03 32 00 00 00 CF 1F 10 08 27 2D 10 08 C9 05`),
retain control/offset conventions, set graphics low-five-bit index7/5,
palette high nibble7/6, cells(25,5)/(14,6), initializer08101FCF and private
wrapper0880037C/088006E8. Direction nibble2 is inherited from that template.
**Do not emit a final actor record yet**: ID0BFE/0BFF and this initializer's
complete room lifetime are not certified. These are proposed values, not approved
replacement bytes. No new story flag is specified.

New confirmed ID trace:08034498..080344A8 fetches record+E/+F and invokes
0806AFB8. That wrapper reads the bit via08069F60 using base03003107.
ID0BFE addresses03003286 mask40;0BFF addresses the same byte mask80.
Save staging0802EF0E..0802EF36 copies384 bytes from03003107 to02001905;
load0802F48A..0802F4B4 restores384 bytes from decoded slot+105.
Consequently these IDs are **in range and serialized**, immediately before
variable bank03003287. This resolves range/save-extent uncertainty; it does
not show the bits are reserved or have a safe value in all existing saves.

Exact actor-bank command consumers are now identified: FD53 at080276E8
sets an immediate16-bit ID through0806B02C; FD54 at0802770C clears through
0806B0B8; FD5B/FD5C at08027778/080277AC read through0806AFB8. They are
distinct from main story-flag operations. Actor-record absence alone cannot
exclude these script consumers or bulk initialization/restoration effects.

### Gate C: bounded collision result

Cells/targets are unchanged. Their local base-collision neighborhoods are
captured from the actual input in JSON. Base00 is only a necessary condition.
Hawker anchors are(407,95)/(231,111), with proposed player positions16 pixels
south. Initial actor records have no occupant in either Hawker cell.

The new audit follows the **entire direct CFG** rooted at080664A8:565 native
instructions through080669C8, no unclassified direct edge within the helper's
bound. Its two direct callees are0802FEF0 (native `BX LR`) and animation
selection0803310C. Thus the former report's unspecified downstream scheduler
destinations are now inventoried. However, this routine stages movement using
arrays03002D14/34/54/74/84/94 and actor state; a closed direct CFG does not
prove the subsequent ticks or their starting states. The complete direct
rectangle-test CFG at0803DF48 is also captured. No full path simulation or
all-origin collision proof is claimed.

Concrete dynamic dependency: Namp blue NPC slot3 has controller081130AF..CE,
starting `50 44 01 54 00 91 01 74 00`, followed by51/52/53/54/55/56/5C.
Main50 handler08023DB8 stores those eight bytes into context+32..39 hex.
Their four raw halfwords are0144/0054/0191/0074. **Do not interpret these as a
certified movement rectangle yet**: controller consumers and56 behavior must
establish trajectories before comparing them with the Hawker footprint. This
is the exact reason initial blue-NPC cell(26,5) does not prove separation.

Mayonen default0812667C..9B conditionally transfers player/NPC events and
installs actor1 controller08128A95 via FE06 at08126690. That deferred controller
also uses50..56. Existing door actors remain slots4..7; their interactions
0812820A/08128217 retain their FE7C transition paths. Leaving these ROM bytes
unchanged alone does not prove access around an additional collision actor.

Namp's independent interaction dispatch and Mayonen door clearance therefore
remain unproved in active states. Conversation control-return semantics are
preserved structurally, but their scheduling alongside approach completion has
not been proved for the two new room contexts.

### Gate D: resource operations and lifetime boundary

| Binding in relocated header | Namp | Mayonen |
|---|---|---|
| Graphics slot / header offset | 7 /1C | 5 /14 |
| Expected descriptor pointer | `00 00 00 00` | `00 00 00 00` |
| Proposed descriptor pointer | `7C F7 13 08` | `7C F7 13 08` |
| Palette slot / header offset | 7 /5C | 6 /58 |
| Expected palette pointer | `EC B1 43 08` | `EC B1 43 08` |
| Proposed palette pointer | `CC C3 43 08` | `CC C3 43 08` |

Descriptor0813F77C references tiles0840C96C..0840CFCC (51 tiles), four
animation sequences at08451E78 and11 compositions at08444860; palette is
0843C3CC..0843C3EC. Established Stage1 dependency evidence covers their
formats, all11 frame bounds, and initial tile budgets. Namp adds after slots0..6;
Mayonen after0..4, so existing descriptor tile bases are not shifted by insertion.
No original actor uses the proposed palette bank. Existing resources need no
ROM copies or pointer relocation.

**Mayonen palette5 is protected:** header+54 remains `EC B1 43 08`; existing
door records keep high nibble5. The new record must use palette6, not5.
These facts prove initial assignments, not that a later palette/VRAM writer
cannot target6. The deferred FE06 controller and FE89 completion consumers
are captured as concrete lifetime roots. No complete transitive writer set
was established for the rooms' other event/actor callbacks, their native
callees, or reload. Lifetime PASS is therefore withheld for initial completion,
idle/directional/conversation animation and re-entry as a combined requirement.

### Gate E: static equivalence versus integration

**Confirmed static transformation:** every byte of the authoritative exchange
is accounted for. Only77 typed pointer fields and ten actor selector bytes
are parameterized per copy. External28 dialogue pointers stay identical. The
Stage1C conservative graph/path evidence is reused after exact field/source
revalidation: no path attempts FE55 twice, including retained blocks. Each of
five FE55 endpoints retains item37 quantity02, native capacity branch,
FEB0/FE66/FEC1/FD7D sequence and character reset operands[1,2,1,1,3].
Story/retirement/character selection, full-gauge tests, advice, refusal,
cancellation, capacity rejection, dialogue and shared state are byte-preserved.
No new inventory counter, claim bit, gauge storage or tutorial call is added.

Intentional differences are precisely: local pointer rebasing; FE31 actor7/8;
room-specific wrapper X/Y; registration/resource records placing each service
in its requested room. Original exchange08107E81 and Oystown introduction
081084CA are excluded from the write set. This establishes exchange-schema
equivalence after actor renaming, **not runtime verification** or universal
engine-state reachability. Registration, collision and resource interference
remain possible regression dependencies, so the complete E gate is BLOCKED.

### Generator and independent future verification requirements

Stage3, only after remaining proofs, needs a new parameterized patcher under
`tools/patch/` and a separate output directory/manifest. No such patcher or
output exists in this stage. It must:

1. Refuse any input size/hash or expected-byte mismatch. Pin source extent hash,
   all original map/block records and owned destination hashes from this JSON.
2. Use one common source-schema generator, parameterized by body base, actor slot,
   wrapper coordinates, block resources and **approved** actor identity/initializer.
3. Apply the complete77-field manifest and ten selector edits per body; preserve
   every external field. Copy original actor records unchanged; perform only the
   two map-pointer edits and approved new-block header/record operations above.
4. Independently read back emitted scripts with a separate decoder; reverse local
   pointers and actor renaming and compare every857 source byte. Check each
   instruction boundary, field and wrapper; verify native continuation offsets.
5. Compare the entire output to the pinned input. Allow changes only in the
   reserved allocation and two map pointer fields, unless new proof explicitly
   revises this specification. Preserve file size/header, all original Hawkers,
   tutorial, translation, Kaizo ledger, Detector and Dragon. Record actual byte
   ledger, output SHA-256 and protected before/after hashes. An output fingerprint
   cannot exist until construction and must not be invented now.

## C. Exact remaining blockers and next actions

| Unknown | Implementation impact | Smallest concrete next analysis | Who |
|---|---|---|---|
| Ownership/default state of actor bits0BFE/0BFF | A saved bit can hide/invert the new actor; record absence and in-range serialization are insufficient. | Close FD53/FD54 writers and FD5B/FD5C references for these IDs, including FD84-constructed operands and bank initialization/bulk operations; prove how existing-save tail bits are treated. Start at the four exact handlers above and bank03003286, not general progression research. | Codex offline |
| Active blue-NPC/Mayonen controller trajectories and interaction origins | Potential overlap, blocked approach/door access or stalled control recovery. | Decode controller56 consumers of context+32..39 and movement-tick consumers of03002D14..94; combine only the two recorded controller streams, local footprints, interaction-origin tests and room transition rectangles into a bounded reachable-state/path check. | Codex offline first |
| Resource writer closure for the two room contexts | A deferred write could replace Hawker tiles/palette or affect a door. | Enumerate room event/callback roots from the two existing event tables and original actor records; close only resource-mutating operations/native callees, retaining slot/VRAM-range annotations. Include FE06 actor1 controller08128A95, FE89 completion0802602C, new initializer08101FCF and shared exchange callees. | Codex offline |
| Complete existing-NPC/door noninterference | Prevents full E regression PASS. | Discharge the B/C/D obligations above; do not repeat reward/dialogue decoding. | Same offline pass |

The **single most effective next action** is the actor-bit ownership/default-state
proof rooted at FD53/54/5B/5C and03003286. It can invalidate the registration
design even if movement/resources fit, and now has exact handlers, bank extent
and serialized location. Another ordinary Hawker conversation cannot prove it.

No mGBA observation is requested now: these open dependencies still have
concrete offline evidence paths. If, after that path analysis, controller
scheduling leaves a genuinely dynamic question, design **one** read-only
observation of that specific origin/actor state, with stop conditions. Do not
ask the user to test an absent Hawker, edit RAM, manufacture progression, or
perform broad exploration. Runtime acceptance of a future built integration
remains separate and user-operated.

## D. Construction readiness decision

Neither placement is certified ready for safe construction. Gate A now has exact
allocation and relocation manifests; B/C/D remain narrow technical proof work,
and E's integration portion depends on them. The next authorized session needs
those proofs before construction; it cannot proceed directly to a ROM build.
Do not substitute successful static exchange equivalence for those missing
registration, path and lifetime guarantees.

**STAGE 2 BLOCKED — EXACT REMAINING GATES IDENTIFIED**
