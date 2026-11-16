# Hawker Stage 1B — ownership-token decision

Follow-up to [Stage 1](hawker_stage1.md), 2026-10-16.

**Result: BLOCKED. Reject the saved-return word as a sufficient NPC-ownership
token. Do not implement the proposed marker-dependent FE31 adapter.** The word
has verified call/return semantics, but an exclusive actor-ownership invariant
has not been proved. This is not a finding that a normal Hawker conversation
actually overwrites it. Scratch14 likewise cannot yet be trusted for the complete
interaction. The narrow remaining dependency is **reachable event-entry and
cross-context writer ownership**, rather than another inventory of text handlers.

## Input, scope and evidence

Input: `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
All ROM bus addresses in this report are **English cumulative ROM** addresses;
subtract `08000000` for file offsets. RAM addresses have no ROM offset. No new
Japanese-ROM equivalence is claimed. Descriptive function names below correspond
to analysis-helper labels, not recovered game symbols.

Reproduce with `python -B tools/analyze/hawker_stage1b.py`. Evidence is
`hawker_stage1b_evidence.json`: 29 additional explicit native roots, checked prior
instruction bytes, command-dispatch identities, and a bounded pointer inventory.
Previous Stage 1 JSON datasets were read and reused, not regenerated or changed.
No movement, graphics-allocation or persistent-ID checks were attempted.

358 scoped existing research/script/game files retained their before/after hashes,
including all 115 previously protected game artifacts. Independent replay matched
the saved Stage 1B output. No ROM construction, patch buffer, emulator operation,
RAM write or checkpoint/save modification occurred.

## 1. Saved-return lifecycle: what is established

For current context `c = u8(030039C0)`, define:

```
E(c) = 03003AD4 + 1C*c, c in 0..31
script PC = u32(E(c)+4)
saved return = u32(E(c)+8) = u32(03003ADC + 1C*c)
```

The saved-return words occupy addresses `03003ADC` through `03003E40`, stride1C.
They are a field of a 28-byte event record, not a dedicated actor ID and not a
stack of script returns.
The operations below are confirmed accesses, not an exhaustive proof against all
computed writes to this RAM range.

| English ROM bus / analysis symbol | Relevant evidence | Confirmed ownership/lifetime fact |
|---|---|---|
| `0802896C` / FD2F | `0802898C: 00 68` loads event+4; `0802898E: 08 60` stores it to event+8. Later installs callee at +4 and sets flag40. | The **currently executing event** owns this call's return word. A second call in the same event replaces it. |
| `0802A3B4` / FD31 | `0802A3C2..0802A3CE` computes event+8 and stores the current PC (`08 60` at `0802A3CE`); sets flag40 at `0802A3F6`. | A second native call-form opcode also writes the field. It is not exclusive to FD2F or Hawkers. Dispatch identity FD31 was independently read from the FD table. |
| `08028A98` / FD7C | Flag40 branch at `08028AAC..08028AB0`; `08028AC4` clears flag40; `08028AD6` reads event+8; `08028AE6` restores event+4. | Reads the single saved return. It **does not clear the saved word**. After returning, the word can be stale while the event remains allocated; flag40 matters. |
| `08071C58` / event-record clear | Computes `E(selected_context)`; `08071CA0: 1C 20` selects length28; calls `0802F950`. | Clears the whole record, including +8. This is initialization/destruction of event storage, not a nested-return pop. |
| `0806AAA0` / event constructor | `0806AAC6: FF 28`, `0806AAC8: 22 D1`: non-FF context selection branches directly to setup. `0806AB2A: 07 F0 95 F8` calls the record clear; `0806AB56: 08 60` installs the new script PC. | FF selects a free general event; an **explicit selected context** reaches reset/setup without that free-context search. The field is not protected against explicit event replacement. |
| `080226AC` / linked-context completion | Compares the selected event PC with its +14 continuation pointer, changes scheduling bits and context links. | Completion/link handling has its own fields. This routine does not provide an extra saved-return stack. |

**Confirmed scoped behavior:** separate contexts' FD2F/FD31 operations compute
different addresses, so ordinary calls in another context do not overwrite this
word. General allocation under FF checks scheduling bitsets while choosing a free
context. That protects against ordinary allocation reusing a busy context; it is
not equivalent to excluding explicit replacement of a selected context.

The shared exchange has no FD2F or FD31 command in its already decoded extent
`08107E81..081081DA`. Its FE01 operation keeps the body in the original event and
links the player continuation through other fields. The traced choice/refusal
paths change the script PC and dialogue scheduling/result fields, not +8.
Thus **normal one-level wrapper preservation is Probable**, with strong local
support; no actual nested overwrite on a Hawker path was demonstrated.

For general contexts, shared FD7D ends the event through the native termination
path and record clear. Normal destruction does not merely leave the shared script
running with an empty marker. For actor contexts, FD7D takes the distinct native
continuation path at `08024290`; do not move interactions into actor contexts and
assume termination/locking will be identical.

### Collision and reuse conclusions

- Existing wrapper continuations are `08102D35`, `08102D45`, `08102D55`,
  `08102D65`. They are distinct. Proposed W_N+0E/W_M+0E must be distinct from
  each other and existing continuations if later allocated; no addresses were
  assigned or allocation checked here.
- The word records a **calling bytecode location**, not which NPC was clicked.
  An unrelated event that enters the same wrapper can produce the same word.
  The current evidence has not excluded every dynamic entry into a wrapper.
- A nested FD2F/FD31 changes the word rather than preserving an outer marker.
  FD7C clears flag40 while leaving the old word; record reset removes both.
- To use the marker safely, the proof must exclude relevant nested calls,
  alias stores and replacement/restart paths for the whole live interaction,
  and establish exclusive wrapper entry. Per-event storage alone proves none
  of those exclusions.

**Decision:** reject a saved-return comparison as the sufficient identity test.
It may be a corroborating guard after a separate ownership proof. This rejects
the implementation proposal, not the verified native call mechanism.

## 2. Scratch-binding status and overlapping writes

RAM `03003A32` remains global scratch+0E. Stage 1's 15 message strings / 16
control handlers were reused. This follow-up traced the outstanding menu variants,
line-buffer helpers, numeric/name helpers and FE55 capacity continuation rather
than repeating their entry-handler inventory. The new JSON records exact code
and computed stores, including buffer bases `030041DC`, `030046DC`, `03004E0C`
and character data at `03001EDC`. These observations narrow possible destinations;
they do not certify every transitive alias or concurrent script.

A concrete **Confirmed static writable alias** now exists:

```
FD0B handler 0802A2F4:
  0802A2F6 -> 08022534     fetch offset byte
  0802A2FA -> 08022A84     form scratch + (offset & 7F)
  0802A302                save destination pointer in utility+8
  0802A304 -> 080227F0     fetch halfword
  0802A308                recover destination
  0802A30A: 08 80         strh r0,[r1,#0]
```

For example, bytes `FD 0B 0E 00 00` would store a halfword zero at `03003A32`.
**This is an unexecuted opcode counterexample, not a discovered live Hawker
script or a patch.** It refutes an engine-wide guarantee that the binding can
only be written by NPC interaction dispatch. It does not establish an actual
overwrite during ordinary gameplay.

Store width matters: a store starting before the binding can overlap it. Merely
searching for the literal address or a `strh ...,#14` instruction is insufficient.
FD0B supports a direct binding write through an alias. Its scalar scratch-offset
mechanism cannot reach the event table: scratch+7F is `03003AA3`; even a four-byte
access there ends before `03003AD4`. This rules out **that bounded-width alias
family** as a saved-return writer, not arbitrary longer copies or other pointers.

**Final scratch status: BLOCKED / not trusted as the actor identity.** The exact
unresolved question is whether any relevant live concurrent/continuation path
can execute a binding-overlapping write. No such path has been proved reachable,
and none has been proved absent. Refusal/cancellation result stores established
in Stage 1 remain separate from this binding. No new RAM was assumed available.

## 3. Why the literal-caller inventory is not an ownership proof

An unaligned literal-pointer search, limited to file `000FC000..00159C00`, found:

| Pointer value | Occurrences, English bus addresses |
|---|---|
| `08107E81` shared entry | `08102D31`, `08102D41`, `08102D51`, `08102D61` |
| `08107E90` body | `08107E84` |
| `08102D27` wrapper | `0814D4CE` |
| `08102D37` wrapper | `0814B39A` |
| `08102D47` wrapper | `081511A2` |
| `08102D57` wrapper | `081521D2` |

Those wrapper references agree with the previously identified original NPC
interaction pointers. **Confirmed bytes, bounded search**; not a whole-ROM or
complete dynamic call-graph claim.

There is a specific native reason not to promote this to complete ownership:

- FD84 at `08028490` fetches a command family/opcode and supplies arguments
  through scratch-offset pointers (`08022A84`). Its non-two-byte route copies
  the bytes at `080284CE..080284E2` into argument staging.
- `080299D0` selects FD/FE/main dispatch for that staged command. At
  `080299F2` it can call FD dispatch `080247B4`.
- With staged FD30, `08029F2C` installs the constructed target at the current
  event's script-PC field without an FD2F saved return.

For example, FD84 familyFD/opcode30 can obtain a four-byte target from the two
scratch halfwords at offsets06/08. The target need not appear as one contiguous
literal in the calling script. This native capability is **Confirmed**; an
actual unrelated dynamic call into the Hawker exchange is **Unconfirmed**.

This is the specific remaining static dependency: **close reachable entry and
replacement/writer paths for live interactions**, including relevant FD84-fed
transfers. Do not count raw pointer occurrences as that proof.

## 4. FE31 guard decision and narrow alternative

### Rejected marker guard

The previously proposed predicate combines map, ten command sites, literal03/01,
flag40 and a W_N+0E/W_M+0E saved return. Its local comparisons are implementable,
but exclusivity and lifetime have not been established. Worse, if a new
interaction loses its marker while a shared FE31 is still reached, delegating
to native literal3 would animate Namp's blue NPC. Calling that fallback safe
outside the new context does not prove it safe after loss of context evidence.
**No complete safe marker-dependent guard is approved.**

### Narrowest viable alternative to investigate

Use the **current executing command and unique service room**, not a long-lived
scratch or return marker. It needs no new RAM and no copied reward implementation.
The exact proposed predicate is:

1. At handler entry `u32(030039EC) == 030039D9`, staged opcode at `030039D8`
   is31, and staged operands at `030039D9..030039DA` are03/01.
2. `c = u8(030039C0)` is0..31 and the active event's next ROM PC
   `u32(03003AD8 + 1C*c)` is in:
   `08107F5A, 08107F91, 081080FF, 08108136, 0810816D,
    081081A0, 081081AC, 081081B8, 081081C4, 081081D0`.
3. Current map is005F with the verified new service registration in slot7,
   or004D with that registration in slot8. Current-map RAM halfword `03001936`
   is an existing documented field (see `hanzo_lab1_progression.md`, map-descriptor
   evidence); no new map-state variable is proposed.
4. The actor's interaction registration must identify its unique wrapper W_N/W_M;
   construction must establish that the service in each room has exactly that
   owner and cannot be entered by an unrelated event. This last condition is
   **not established by the pointer inventory above**.

Within a proved service scope, the actor is the immutable instance constant7 or8.
It never comes from scratch14, current event ID, or saved return. Outside that
scope, original FE31 must remain unchanged.

**Feasibility only:** because scope condition4 is not closed, this alternative
also does not receive PASS. Adding more comparisons to mutable fields would not
repair that missing proof. Nor may failed ownership validation in a suspected
new-Hawker context silently fall back to actor3. A fail-closed no-animation path
would require its own interpreter side-effect contract; it is not supplied here
as a purportedly complete solution.

### Argument staging and execution contract for a future verified scope

The corrected Stage 1 staging trace stands. The event PC above is the advanced
ROM PC, while FE31's arguments are fetched from RAM. A small **design-only**
adapter could substitute the one staged selector byte with literal7/8 immediately
before delegating to the unchanged native handler. Native FE31 then consumes both
arguments once, resolves the literal, and performs all original setter/utility
side effects. No new transaction branch or transaction state is introduced.

Important additional constraint: FE dispatch `0802479E` writes the selected
handler pointer into utility+12. Replacing its table pointer would initially put
the adapter pointer there. Before delegation, normalize utility+12 to the original
Thumb pointer `08028ED1`; otherwise claiming exact original fallback state is
unjustified. Native byte fetch saves/restores utility+12.

The narrow design can use only volatile r0..r3, with no calls or additional stack
frame. At the first native byte fetch, r2 is replaced at `0802253A`, r0 at
`0802253C`, r3 at `08022540`, and r1 at `08022542`, before their incoming values
are used. Thus these entry-register values are not inputs to FE31. Keep r4..r11,
LR and SP untouched; supply r0=`08028ED1` for the final Thumb BX. This preserves
stack alignment without borrowing persistent RAM or retaining any CPU frame
across dialogue. A registration-pointer guard must assemble the actor record's
unaligned +0A pointer from bytes or aligned halfwords, as native dispatch does;
an ordinary unaligned ARM7 word load is not a valid substitute. No actual adapter
instructions were assembled.

Native fetch `08022534` and literal resolution `08022798` do not consume incoming
condition flags before setting their own; native FE31's last mode setter supplies
the final flags and utility+1/+5 side effects. Consequently the guard must tail-
delegate without appending flag-changing work after the setter. This preserves
the native flag contract; it does not require a CPSR write. VM scheduling does
not occur inside the traced byte-fetch/resolver/setter path. This describes the
calling contract, not runtime success or proof of an unassembled adapter.

## 5. One bounded manual observation, if needed

A sample cannot close all static entry paths, so a matching result does not
upgrade this report to PASS. If concrete evidence of an unexpected return-word
writer is needed, use **one interaction**, on the unchanged cumulative ROM:

1. Immediately before manually talking to the existing Oystown Hawker, set an
   execution breakpoint at `08028990` (after FD2F stores its return word).
2. At that stop, read `c=u8(030039C0)` and `u32(03003ADC+1C*c)`.
   Require c in16..31 and the word `08102D35`; otherwise stop the observation.
3. Remove the execution breakpoint. Set one **write watchpoint covering four
   bytes** at `03003ADC+1C*c`. Resume normal dialogue and choose cancellation.
4. Expected first write is the record-destruction byte-fill instruction
   `0802F960`, beginning to zero that word as the interaction ends. Record the
   writer PC, context ID and word; stop on the first write. If an earlier/different
   writer appears, record it and stop immediately. If the game stalls, stop.
5. Remove the watchpoint before continuing. Do not change RAM, save/load a state,
   save the game, or inject input.

The expected clear is ordinary lifecycle behavior, not marker corruption. A
different writer would identify a concrete path to audit. No observation was
performed by Codex, and this experiment does not prove scratch preservation,
all exchange branches or exclusivity of the two future wrappers.

## 6. Final recommendation

Do not keep extending the saved-return marker into a more elaborate identity
scheme. It is not approved as an ownership mechanism. Prefer the staged-selector
adapter with immutable per-room actor selection **only after** the bounded
service-entry ownership graph closes, including relevant dynamic FD84 transfers
and explicit event-replacement/overlapping-writer reachability during dialogue.
That proof is the next concrete dependency; if it cannot be closed, reject that
adapter too. Do not relax original-NPC fallback requirements, allocate speculative
RAM, duplicate exchange logic, or proceed to the other three safety checks.

**STAGE 1B BLOCKED — SPECIFIC STATIC DEPENDENCY REMAINS**
