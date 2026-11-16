# Hawker Stage 1C — localized script adaptation

2026-10-16. **GO for a parameterized private-script architecture; no authorization
to construct a ROM follows from this report.** Local literal actor selectors remove
the two Stage 1 ownership dependencies. Allocation, registration and the remaining
placement/resource safety checks are still prerequisites to implementation.

This follows [Stage 1](hawker_stage1.md), [Stage 1B](hawker_stage1b.md),
[dependency resolution](hawker_dependency_resolution.md) and the
[final gate](hawker_final_gate.md). Their scratch and dialogue-handler investigations
were reused, not repeated. No ROM, RAM, save or existing Hawker was changed.

## Input and reproducibility

Input: `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, 16 MiB,
SHA-256 `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
All bus addresses below refer to this **translated cumulative ROM**; subtract
`08000000` for file offsets. No new Japanese-ROM address equivalence is claimed.
Function names are descriptive analysis labels.

Run `python -B tools/analyze/hawker_stage1c.py`; stdout is the reproducible
[evidence JSON](hawker_stage1c_evidence.json). The analyzer reads the pinned ROM,
decodes only the established script extent and four existing wrappers, checks
selected native functions, and compares symbolic command graphs. It does not
generate relocated payload bytes or choose a destination. Source bytes and 361
protected existing research/script/game files match before and after, including
the previously protected game artifacts. This is static evidence, not runtime
verification or verification of an already constructed copy.

## 1. Wrapper-only approach: rejected

**Confirmed:** existing 16-byte wrappers at `08102D27`, `08102D37`, `08102D47`,
`08102D57` contain FD01 X, FD02 Y, FD2F `08107E81`, FD7D. They establish the
coordinates and call the common interaction using the existing return mechanism.
They do not parameterize FE31. The ten commands in the common block are literally
`FE 31 03 01`; the selector is read afresh for each executed command.

FE31 dispatch table entry `0862B978` points to Thumb handler `08028ED1`.
The existing selector resolver `08022798` accepts literal 7 and 8. The setter
`08065E4C` updates the selected actor's directional-controller bits at actor+3,
with actor base `03001BDC + 30*slot`. Therefore a wrapper's preliminary
`FE31 07 01` cannot redirect a later `FE31 03 01`. A postamble cannot undo the
wrong actor's animation and is not a reliable exit interceptor. **NO-GO for B.**

## 2. Private copies: bounded script and relocation proof

**Confirmed source inventory:** `[08107E81,081081DA)` is 857 bytes, 164 decoded
commands. Extent SHA-256:
`0c320e92fdcd968fe2d80c2b6005effd0060952cd6bb5623bbf79e50cb8fbd6d`.
161 commands are conservatively reachable from the entry. The three commands at
`081081A8`, `081081AC`, `081081B2` have no local inbound edge; retain them rather
than delete or reinterpret them. The entire extent's command graph is acyclic.

There are 77 typed internal script pointer fields, all targeting command
boundaries inside the extent, and 28 external dialogue-data fields referencing
15 existing messages. The JSON contains every field address and original target.
Pointer field offsets from command start are:

| Commands | Field offset | Treatment |
|---|---:|---|
| FE01 | +3 | Internal script |
| FD30, FD45, FE7A, FEB5, FEB6, FEB7 | +2 | Internal script |
| FD35, FD3B, FE55 | +4 | Internal script |
| FEC8, FEBC, FE66 | +2 | External dialogue data; unchanged |

**Proposed deterministic transformation:** for private base B, map each internal
pointer P to `B + (P - 08107E81)`. Preserve each external data pointer and every
other source byte except the ten FE31 actor bytes. Use selector 7 for map005F
and 8 for map004D. No concrete B is selected here. Apply this one schema twice,
not independently maintained script edits. This is a relocation specification,
not a patch or payload.

The ten FE31 command addresses are `08107F56`, `08107F8D`, `081080FB`,
`08108132`, `08108169`, `0810819C`, `081081A8`, `081081B4`, `081081C0`,
`081081CC`. Replace only their +2 selector; preserve mode01. All ten are followed
by FEC8, whose handler `08029E24` resets utility+1 to 140. No other command or
transaction parameter is adapted.

Native conditional evidence is recorded for FD35 `08029F90`, FD3B `0802A43C`,
FD45 `0802984C`, and choice core `08025F1C`: their typed destinations are script
PCs, not dialogue pointers. Pointer relocation preserves branch destinations and
fallthrough offsets. All local branches are classified, including retained blocks.
The symbolic views for actors3/7/8 agree after substituting the intended actor
parameter. This establishes **structural equivalence of the specified
transformation**, not equivalence of an unbuilt binary.

### Dynamic command, transfer and exit boundaries

The only FD84 is `08107E88: FD 84 00 36 06 08`. It dispatches fixed main command36
with coordinate scratch operands06/08. It does not dispatch FD30 or obtain a
script destination from scratch. Preserve it unchanged. There is no FD2F, FD31,
FD75 or FD7C inside this extent. No nested bytecode subroutine needs a separate
relocation closure.

Entry `08107E81: FE 01 00 90 7E 10 08` uses native FE01 `0802886C`:
the already advanced continuation `08107E88` is given to player actor0 while the
interaction executes explicit body `08107E90`. For a copy these become B+7 and
B+F. Native stores at `080288EC/EE` preserve this split. Main2F at B+D reaches
the existing continuation boundary. Completion logic `080226AC` / comparison
at `080226FC` compares pointed-to command words, rather than requiring the
original ROM pointer value. The pre-body FD84/main2F words differ from the body's
`FD 35 FC 01` prefix; relocation preserves that boundary. No new return token or
stack convention is introduced.

**Important inherited external exit:** all eleven FD7D sites preserve native
`0802A03C`. Contexts below16 use `08024290`. General contexts16..31 read global
`03003A20` at `0802A06C`: zero ends the event via `08022908`; nonzero is consumed,
cleared at `0802A076`, and installed as event PC at `0802A08C`. FD75
`08027E50` can write that global continuation at `08027EC0` before a scene
transition. Do not assume FD7D always terminates or that the global is zero.
The copy retains precisely this external engine contract; it does not duplicate,
capture or relocate an external caller's continuation. The local graph's exit
nodes explicitly mean native end **or external continuation**, not a proof of
whole-game reachability. There is no new return stack and no new global context.

## 3. Shared transaction state and behavioral preservation

**Confirmed:** five FE55 sites (`08107F73`, `08107FAA`, `08108118`, `0810814F`,
`08108186`) retain `FE55 37 02` and their common capacity/failure destination
`081081D8`. Native FE55 `08025634` stages item/quantity in `03003A34/35` and
uses the existing inventory path through `080291D4` / `08080424`. A nonzero status
takes the failure branch; success falls through FEB0, FE66, FEC1, FD7D. Character
reset operands remain `[1,2,1,1,3]`. No new inventory, AWE storage, reward counter,
claim flag or transaction routine is allocated. The unchanged engine accesses
the same game state regardless of which ROM script supplies its arguments.

Preserve all full-gauge comparisons, selection, flags, refusal branches, text,
item37 quantity02, and gauge reset commands byte-for-byte. The conservative
entry graph has 64 paths with no FE55 attempt and 34 with one; none has two.
This syntactic count overapproximates feasible states and is not a gameplay test.
The retained locally unreferenced block is also checked for cycles. Existing
Oystown tutorial entry `081084CA` is not copied or newly invoked.

Correct FE31 action is the intentional behavioral difference. Because selectors
7/8 are literal, its RAM-staging handler, register usage, flags, stack and cursor
advance remain native. No trampoline, hook, calling-convention adaptation, scratch
actor selector or saved-return identity check is needed. Scratch `03003A32` and
saved-return exclusivity remain **unproved as reported in Stage1B**, but neither
is a dependency of this actor-selection mechanism.

## 4. Architecture comparison

| Criterion | A: global guarded FE31 | B: wrapper + original shared body | C: private parameterized bodies |
|---|---|---|---|
| Correct actor identity | Unproved guard ownership | Literal3 still executes | Literal7/8 in each copy |
| Global interpreter edits | Required | None | None |
| Scratch / ownership dependence | Unresolved | Does not solve binding | None for actor selection |
| Dynamic entry proof | Global guard exclusivity required | Shared commands unaffected | Local outgoing graph classified; native exits preserved |
| Relocation | Hook and context machinery | Small wrapper only | 77 internal fields per body |
| Existing Hawkers | Misclassification risk | Original behavior, new binding wrong | Original bytes and engine untouched |
| Maintenance | Interpreter-sensitive | Insufficient | One hash-pinned parameterized schema |
| Decision | Reject current unproved design | Reject | Recommend, subject to construction gates |

Isolation comes from dedicated event registration and physical script placement,
not an inferred runtime identity. Original events retain original pointers and
FE31 semantics. No global command can accidentally rebind the Namp blue NPC
because no global command is changed. Conversely, private copies are not a
defense against corrupted PCs or arbitrary external jumps. Future registration
and allocation must prove legitimate entry pointers, ownership and disjointness;
this report does not certify those still-unbuilt tables.

## 5. Remaining technical dependencies and next stage

1. Reserve and validate disjoint ROM space before constructing anything. Two
   bodies plus two 16-byte wrappers require 1,746 raw bytes (1,752 with each
   instance padded to four bytes), excluding actor/resource tables. Existing
   Alessa reservation `[00800000,00800020)` file offsets is protected, including
   its unused tail. The current payload matches its manifest. No new free-space
   address has been approved; FF bytes alone are not ownership evidence.
2. Future generation must pin this source hash, decode and validate all typed
   fields, emit private pointers, independently read back and compare each copy
   against the schema, and verify unrelated ROM bytes. This is statically
   resolvable; today's symbolic equality cannot replace output validation.
3. Prove map005F slot7 and map004D slot8 event/actor registration, capacity,
   persistence and re-entry. Prove graphics/palette lifetime and physical movement
   safety separately. They were deliberately not investigated here.
4. Proposed wrappers retain FD01/FD02 then FD2F to their own private body and
   FD7D. Coordinates407/111 and231/127 are inputs to the next safety stage,
   **not validated trajectories**. Mayonen door palette5 remains reserved.

**Confidence:** source decoding, typed pointer inventory, literal binding and
symbolic graph preservation are Confirmed within the pinned extent. Actual
placement and resource safety are Unconfirmed here. Successful gameplay,
cancellation/control recovery, inventory refusal, progression and room re-entry
remain runtime-unverified. No manual debugger experiment is needed to choose
between these architectures: observing one original conversation cannot prove
universal ownership, allocation safety or correctness of a future copy. Manual
acceptance of an independently verified future build remains necessary.

This removes the original Stage1 actor-ownership blockers rather than moving
them into another RAM marker. It introduces ordinary, explicit relocation and
registration proof obligations. **Proceed with the remaining safety checks using
architecture C; do not construct a ROM until those gates and allocation pass.**

STAGE 1C — LOCALIZED IMPLEMENTATION FEASIBLE
