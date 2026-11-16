# Hawker Stage 1 — scratch lifetime and scoped FE31 binding

2026-10-16. **Scratch lifetime: BLOCKED. Scoped adapter safety: BLOCKED.**
This investigation establishes additional interpreter/context semantics and a
scratch-independent candidate design. It does **not** establish complete write
closure for either binding. No ROM, RAM, save, checkpoint, existing script,
historical evidence or experimental output was modified. The other three Hawker
safety checks were not investigated.

## Scope, input and reproducibility

The input is the English cumulative Detector ROM,
`tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
All ROM bus addresses below refer to that input, **not verified Japanese-ROM
equivalents**; subtract `08000000` for file offsets. RAM addresses have no ROM
offset. Helper labels are descriptive analysis symbols, not recovered source names.

New evidence:

- `tools/analyze/hawker_stage1.py` -> `hawker_stage1_evidence.json`.
- `tools/analyze/hawker_stage1_dialogue.py` -> `hawker_stage1_dialogue_evidence.json`.

Both print JSON only when run with `python -B`. The first inventories 51 explicit
native roots / 2,050 instruction entries (overlapping routines can repeat entries).
It follows direct branches inside a 4-KiB per-root bound, excludes unreachable
literal pools, records direct calls without automatically certifying them, and
stops explicitly at indirect PC writes. It is not a whole-ROM disassembler or
alias-analysis proof. The second inventories 15 bounded messages by hash and
control sequence, 16 control-table records, and selected menu/wait helpers; it
does not export dialogue text or graphics.

The first audit fingerprinted 353 existing scoped research/script/game files
before and after. It also checked all 115 prior protected game-artifact hashes.
The second rechecked those 115 game artifacts. All matched; ROM writes = 0.
Independent reruns reproduced both analysis datasets and every initially protected
fingerprint. The first rerun's expanded file inventory also includes newly created
Stage 1 helper/evidence files; comparison retained the original 353-file scope.

## A. Scratch-binding lifetime

### Ownership and direct accesses

**Confirmed static:** the binding is a halfword at RAM `03003A24 + 0E =
03003A32`, in a global scratch block. It is not stored inside each event record.

| English ROM bus / helper symbol | Exact evidence | Meaning and limitation |
|---|---|---|
| `080697C8..080697CC` / clicked-slot store | `0D 48 C6 81`: load `03003A24`; `strh r6,[r0,#14]` | Native interaction initialization writes the clicked actor slot. |
| `080227D4..080227D8` / actor resolver FD | load `03003A24`; `ldrh r0,[r0,#14]` | FD actor operand reads the halfword; resolver subsequently stores the low byte to utility+1. |
| `08022A84..08022AD4` / scratch pointer resolver | `08022AB2`: load scratch base; `08022AB6`: `add r0,r0,r1`; `08022AB8`: `str r0,[r4,#12]` | A script-controlled scratch offset becomes a pointer in utility+12. This is an alias source, not itself a write to the binding. |

The entry gates previously identified at `08069728..08069748` and interaction
locking exclude a second ordinary clicked-NPC interaction while locked. They do
not turn the scratch block into per-event storage and do not exclude scripts,
callbacks or initialization routines from writing it. No preservation guarantee
has been inferred merely from those gates.

### Rooted dialogue path

**Confirmed static call/data flow**, with full instruction bytes in the JSON:

```
FE C8: 08029E20 -> 08029DAC -> 08028C48
FE66:  08029D98 -> 08029DAC -> 08028C48
08028C48 -> 0806A5A0, 0806A540, 08029DC8
08029DC8 -> 08022534 (four byte fetches), 08029E04
08029E04 -> 0806A804 -> 08071B0C
08071B0C -> 0806ECC8, 0806BD94
0806BD94 -> 0806C904
```

At `08029DAE..08029DB4`, the bridge writes dialogue configuration to `03003E8B`.
At `08028C66` (`E8 73`), it writes current context ID to `030039CF`, for later
dialogue completion. These are distinct from `03003A32`.

At `0806A906` the message pointer is stored at `03003EE8+20 = 03003F08`.
At `0806BDB2` it is installed at `03004188`, the dialogue text cursor.
Those pointers identify message/text ownership, not the clicked NPC.

The context-bit helpers manipulate bitsets rooted at `030039C1` and `030039C5`.
Their core routines `08069EF0` / `08069F28` use `context>>3` as the byte offset
and `context&7` as the bit. Under the engine's context IDs0..31 these accesses
remain inside their four-byte bitsets. **Confirmed conditional bounds:** these
specific accesses cannot alias `03003A32`; this does not certify all callees.

The utility save stack at `03000608` with depth at `03000604` saves/restores
utility words during these nested native calls. The traced wrappers save
`030018BC` fields and the utility result at `03000600`; they do **not** save and
restore the entire `03003A24` scratch block. Treating native nesting as automatic
scratch preservation would be incorrect.

### Deferred dialogue, choices, cancellation and end

**Confirmed static:** initialization is not the entire dialogue lifetime.
`0806BC98` is a deferred update path. Its active-text route reaches `0806CB10`;
at `0806CB84..0806CB8A`:

```
ldr r1, =030018BC
ldr r0, [r4,#4]       ; r4 = 03004188
str r0, [r1,#12]
bl 080F7ACC           ; trampoline is BX r0
```

The callback pointer comes from the 12-byte control records at `08649F70`.
`0806DE40..0806DE96` scans for the control code, reads record+4, and stores it at
dialogue+4. All 15 messages directly referenced by FEBC/FEC8/FE66 in the shared
exchange were inventoried. Their entire observed control set is:

`00 01 02 05 12 26 30 32 40 41 42 43 80 82 83 84` (each prefixed FF).
These controls are parameterless in these strings; no arbitrary embedded event
pointer was inferred. The JSON preserves hashes, control order and callback bytes.

| Control | Callback Thumb pointer | Purpose established from code/source |
|---|---|---|
| FF00 | `0806CEB1` | End: calls `0806CD44`, sets dialogue+10 to4. |
| FF01 / FF02 | `0806CEC5` / `0806CF35` | Wait/continue paths. |
| FF05 / FF12 | `0806CFC1` / `0806D891` | Break / default pause. |
| FF26 | `0806DD61` | Centering; reaches translated `0806E80C`. |
| FF30 / FF32 | `0806D905` / `0806D919` | Color controls. |
| FF40 | `0806D091` | Simple wait. |
| FF41 / FF42 / FF43 | `0806D18D` / `0806D1F5` / `0806D279` | Menu choices and menu execution. |
| FF80 | `0806DAA5` | Reads numeric scratch value at `03003A24`; no binding write in the handler itself. |
| FF82 / FF83 / FF84 | `0806DB5D` / `0806DB61` / `0806DB65` | Character-name formatting. |

**Confirmed specific writes, not complete transitive preservation:** the ordinary
menu route `0806D278 -> 0806D2BC` updates selected option at dialogue+32,
RAM `030041A8`. Confirmation at `0806D2F6` sets its high bit. Refusal is a menu
choice that later drives the shared branch, not an independent scratch-binding
assignment. `08071E06..08071E24` reads this byte, tests high bit80, masks7, and
writes the selection to `030039C0+13 = 030039D3`. Selection branches at
`08025F1C` read that context-global choice and write event+4, the script PC.
These identified stores do not target `03003A32` or event+8.

The full exact menu and wait handlers are in the dialogue evidence. Some contain
computed output stores, e.g. `0806D472` / `0806D4A0` write through utility+4.
Helper `0806D388` derives that destination from a buffer rooted at `030046DC`.
The existence of a separate buffer base is established; complete bounds and all
transitive copies have **not** been certified. A constant-reference search alone
would miss such aliases.

Dialogue completion `08071D84` uses the saved context ID at `030039CF` to restore
that event's activity bits. It does not preserve scratch by copying it. Event
termination follows FD7D `0802A03C`; `08022908` clears context links and reaches
`08071C58`, which clears the selected event's 28-byte record through `0802F950`.
The cleared event table is rooted at `03003AD4`, beyond the scratch binding.
This proves the destination of that particular clear, not every interrupt path.

### Proven versus unresolved

**Confirmed:** one binding initializer, the FD read, scratch-offset pointer
construction, rooted dialogue submission, deferred callback-table ownership,
choice-result writes, event-record clearing, and disjoint destinations for the
specific stores above. No additional concrete overwrite of `03003A32` was found
in these traced stores. That is not evidence that no overwrite exists.

**Probable:** normal native Hawker dialogue preserves the clicked slot; the
observed menu/result destinations support this. **Unconfirmed:** preservation
across every asynchronous update, transitive formatter/copy/sound helper,
concurrent event and interruption path. No complete path-sensitive store/alias
closure was performed. The global event scheduler (`08021EBA..08021F14`) iterates
contexts0..31; a conversation lock is not proof that every other event is stopped.

The shared script's own bounded command inventory contains no FD2F nested call.
It uses scratch0 for transaction values, FD01/FD02 wrapper coordinates, and
existing native helpers. This is **Confirmed script inventory**, not a proof that
every native callee or concurrent context is unable to target scratch+0E.

**Task A: BLOCKED.** FE31 FD01 substitution remains unjustified. No safely unused
RAM allocation was identified or proposed.

## B. Exact FE31 contract and a better candidate discriminator

### Important cursor correction

**Confirmed static; supersedes the old proposed ROM-argument-cursor guard.**
VM predecode `08022388` copies the command into staging at `030039C0+19`, then
copies arguments over that staging and sets its argument cursor at context+2C.
For `FE31 03 01` at ROM command address C:

| Moment | Staged argument cursor `u32(030039EC)` | Active event PC |
|---|---|---|
| FE31 handler entry | `030039D9` | C+4 |
| After first `08022534` | `030039DA` | C+4 |
| After second `08022534` | `030039DB` | C+4 |

The active event PC is `u32(03003AD8 + 1C*context)`, where current context is
`u8(030039C0)`. At `080224D2` predecode stores the advanced original-ROM PC there.
At `0802248E` (`CC 62`) it sets the separate staged-argument cursor.
Byte fetch `0802254C..08022558`, bytes
`C8 6A D8 60 05 78 0D 76 01 30 D8 60 C8 62`, reads/increments **RAM staging**.
Therefore testing that argument cursor against C+3 will not identify these sites.
The ten correct original-PC guard values are C+4, listed in the evidence JSON.

### Native calling convention

**Confirmed static:** FE dispatch at `0802478C` loads a Thumb pointer from
`0862B8B4 + 4*opcode` into utility+12 and invokes `080F7ACC` (`BX r0`).
FE31's dispatch pointer at `0862B978` remains `08028ED1`.

Handler `08028ED0..08028EF4`, exact sequence:

```
30 B5             push {r4,r5,lr}
F9 F7 2F FB       bl 08022534          ; selector byte -> utility+1
F9 F7 5F FC       bl 08022798          ; resolve selector
06 4D 06 4C       ldr r5,=030018F0 / ldr r4,=030018BC
60 78 28 70       ldrb r0,[r4,#1] / strb r0,[r5,#0]
F9 F7 27 FB       bl 08022534          ; mode byte -> utility+1
60 78 68 70       ldrb r0,[r4,#1] / strb r0,[r5,#1]
3C F0 AF FF       bl 08065E4C
30 BC 01 BC 00 47 pop {r4,r5} / pop {r0} / bx r0
```

`08065E4C` computes actor base `03001BDC + 30*selector` and writes
`actor[3] = (actor[3]&F8)|mode`. It also writes utility+1 and utility+5. Preserve
both side effects as well as the actor write. The current selector and mode are
in `030018F0` bytes0/1, not ABI parameters assumed in r0/r1.

A future adapter must fetch both arguments exactly once, retain resolver behavior
outside its scope, preserve r4..r11 and SP, preserve its return linkage, and avoid
changing utility/global memory during guards. Restore any guard registers before
tail-delegating to the original handler. The native handler uses a 12-byte save
frame; its helpers use additional balanced frames and the utility save stack.
Do not silently add an assumed ABI stack-alignment requirement or borrow the
utility stack for persistent binding.

Incoming condition flags are not an input contract: native fetch/resolve/update
code sets them internally. The inspected FE dispatch return sequence is POP/BX,
with no flag-dependent branch. For the adapted path, make the unchanged native
mode-update call the last flag-affecting operation, followed by ordinary register
restoration/return. For fallback, tail-delegate to the original handler. No need
to modify CPSR or change ARM/Thumb state is established. This is a source-level
contract, **not verification of assembled adapter machine code**.

### Candidate: use the existing event return slot, not clicked scratch

**Confirmed static structure:** event records start at `03003AD4`, stride1C.
FD2F at `0802896C` saves the current event's already-advanced script PC into
its **+8 saved-return word**, installs the callee at +4, and sets flag40 at +0.
At `0802898C..08028990`, bytes `00 68 08 60` perform the saved-PC load/store.
The existing Oystown wrapper at `08102D27` calls the shared script at wrapper+8;
its saved return is `08102D35` (wrapper+0E).

This is **one saved return word**, not an event call stack. A later FD2F in the
same event replaces it. The existing shared exchange inventory has no FD2F.
FE01 `0802886C` leaves the original event executing the exchange body and moves
the player approach continuation into actor0. Its traced writes alter +4 and
the player linkage fields, not the original event's +8 word.

Initialization/termination `08071C58..08071CA8` computes the chosen event record,
sets length1C at `08071CA0`, and calls byte-fill `0802F950`. Clearing +8 prevents
a terminated interaction from retaining the marker in a normally reused record.
The bit40 flag alone is insufficient, and a saved return alone is insufficient
without its ownership/lifetime proof.

**Candidate design, not approved patch:** assign unique wrapper symbols W_N and
W_M only when a later stage validates allocations. No numeric addresses are
invented here. Both wrappers retain the existing 16-byte wrapper shape. A future
adapter can evaluate all of:

1. Current context is in0..31 and its event record is active for execution.
2. Event flag40 is set and saved-return word equals exactly W_N+0E or W_M+0E.
3. Event +4 equals one of the ten shared FE31 sites plus4.
4. Staged selector/mode bytes are exactly03/01 and staged-argument cursor has the
   expected FE31 phase; reject indirect invocation masquerading as these sites.
5. Marker W_N is permitted only on map005F with appended slot7; W_M only on
   map004D with appended slot8. The room-map getter must be independently checked
   when implementing; this report does not assign a new RAM address to it.
6. The corresponding registered actor interaction pointer equals its unique
   wrapper. Validate those pointer identities as build guards and runtime guards
   where justified. Slot values come from immutable per-instance constants7/8,
   never from scratch14, FF (current event), or an unallocated RAM variable.

Only a matching instance changes the actor argument passed to the original
mode setter. Every nonmatching invocation delegates to original FE31 semantics.
All reward, gauge, capacity, progression, character-selection and dialogue script
bytes remain unchanged. This introduces no separate exchange economy.

The same marker would cover every offer/advice/refusal/cancellation/capacity/
retirement site, without ten global operand changes. Dialogue termination clears
the event rather than requiring an added persistent cleanup flag.

**Remaining safety issue:** complete transitive write closure for event+8 and
event/context identity has not been established either. Loss of a marker while
the shared exchange continues could cause fallback to literal actor3, including
Namp's blue NPC. Fallback outside a new interaction is safe; fallback after
unexpected context damage inside one is not proof of safety. This is why the
return-word design is **Candidate/Probable feasibility**, not a PASS.

**Task B: BLOCKED.** The ROM-cursor assumption is disproven and corrected; a
scratch-independent discriminator with real engine storage exists, but a fully
safe adapter has not yet been proved or assembled. Do not implement the older
map/site/scratch-equality proposal or this candidate prematurely.

## Smallest useful manual observation

Static work can still resolve concrete outstanding paths, so manual observation
is useful supporting evidence, not presently a substitute for that work.
One bounded experiment on the unchanged cumulative ROM can test both new cursor
and return-word predictions:

- User manually sets **one execution breakpoint at `08028ED0`**, then normally
  interacts with the existing Oystown Hawker with an eligible full gauge.
- At the offer hit, read `u16(03003A32)`, `u8(030039C0)`,
  `u32(030039EC)`, and event words+4/+8 at
  `03003AD4 + 1C*u8(030039C0)`. Do not change any values.
- Expected: binding3; staged cursor `030039D9`; saved return `08102D35`;
  event+4 one of offer sites+4 (`08107F5A`, `08107F91`, `081080FF`, `08108136`,
  `0810816D`). Record the actual context ID rather than guessing it.
- Resume manually and select the refusal option. At the cancellation FE31 hit,
  expect binding3, cursor `030039D9`, the same saved-return marker, and event+4
  `081081B8`. Record any differing values and stop the observation immediately.
- Otherwise stop collecting after that second hit, remove the breakpoint, and
  resume to player control. Do not save, load/modify a savestate, edit RAM, or
  inject input. If the expected offer never appears or a stall occurs, stop.

Matching observations corroborate staging and marker survival across that menu
path only. They cannot prove absence of transient scratch writes, every success
branch, capacity/retirement branches, interruptions or the proposed new rooms.
No debugger experiment was executed by Codex.

## Concrete next Stage 1 work before the other three checks

Finish a path-sensitive destination/alias audit, using the now-resolved finite
text callback set. The dialogue evidence lists remaining direct callees explicitly
in `direct_callee_frontier_not_certified`; some are already traced in the first
dataset, so combine those results rather than redoing them. In particular close
the ordinary menu/wait formatting/copy paths (`0806D030`, `0806D124`,
`0806E68C`, `0806E700`, `0806E744`, numeric/name expansion), and establish which
alternate UI-kind paths `0806D51C`/`0806D718` can actually run for Hawker dialogue.
Track computed stores, bulk-copy lengths and utility-pointer restoration.

Separately close relevant active-event writes during the exchange, including
the FE55 item-acquisition continuation and any concurrent-context scratch-pointer
stores that can reach scratch+0E. Track both `03003A32` and the active event+8
marker. A global literal scan or a successful sampled conversation is inadequate.
This is targeted interpreter/dialogue work, not a request to reanalyze maps,
graphics, persistence allocation, enemy systems or the whole ROM.

Prefer the return-marker discriminator if its lifecycle closes: it removes the
need for scratch14 to be the authoritative actor identity and allocates no RAM.
Only after that static proof should Stage 1 pass and remaining Hawker safety
checks resume. No experimental ROM should be constructed now.

**STAGE 1 BLOCKED — FURTHER TARGETED STATIC ANALYSIS REQUIRED**
