# Hawker Stage 2B — actor identity and registration

2026-10-17. **Gate B remains BLOCKED.** Neither candidate is proved unsafe;
neither has the complete persistent-state ownership and callback-lifecycle proof
required for approval. This investigation establishes the decoder, local
activation behavior, additional record-based writers, and initializer semantics.
It does **not** establish an exhaustive event-operand/write closure. No ROM was
constructed or modified. No emulator, live RAM, save or savestate was operated.

Reproduce: `python -B tools/analyze/hawker_stage2b.py`. The analyzer prints JSON;
the recorded output is `hawker_stage2b_evidence.json`. Save replays to a new path.
Native names below are analyst labels, with roots in that analyzer's `roots`.
All ROM addresses refer exclusively to the cumulative **English** input; file
offset = bus address minus `0x08000000`. No Japanese-address equivalence is asserted.
Ranges are half-open. Confidence applies to static instructions/data unless stated.

The actual 16-MiB input hashes to
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`:
`tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`.
Stage 2's Gate A and exchange transformation findings stand; they were not rerun.
The Stage 1C design remains two private scripts from one parameterized schema.

## A. Actor ID verdict

| Proposed NPC | Candidate ID | Result | Evidence | Required change |
|---|---|---|---|---|
| Namp Hawker | `0x0BFE` | UNPROVED | Decoder `08069F60`, bank wrapper `0806AFB8`; byte `03003286`, mask `40`; loader `08034498..08034574`; JSON `native`, `conditional_manifest` | No numerical replacement justified. Close state ownership and callback lifecycle before approving this record. |
| Mayonen Hawker | `0x0BFF` | UNPROVED | Same decoder/wrapper; byte `03003286`, mask `80`; same loader; JSON `native`, `conditional_manifest` | Same unresolved proof. |

**Confirmed:** these values are valid indices into the serialized actor-bit bank.
They are not special sentinels, actor slots, graphics indices or decoded classes
in the traced handlers. The bound comes from the save extent, not a runtime
range check: the generic decoder itself does not reject out-of-range values.

**Unconfirmed:** exclusive ownership of those bits and their values in every
supported existing save. Absence in actor records is insufficient. No candidate
was shown unsuitable, so an alternative-ID search is not justified. Selecting
another absent number would reproduce the same unresolved ownership question.

## B. Decoder, state and writer proof

| Structure/function | ROM bus / file offset | Evidence and purpose | Confidence |
|---|---|---|---|
| FD53 | `080276E8` / `000276E8` | Fetches two operand bytes into `030018BC+4/+5`; calls `0806B02C` | Confirmed |
| FD54 | `0802770C` / `0002770C` | Same operand assembly; calls `0806B0B8` | Confirmed |
| FD5B | `08027778` / `00027778` | Reads bit; nonzero invokes branch reader `08029F2C`, zero consumes pointer through `08022874` | Confirmed |
| FD5C | `080277AC` / `000277AC` | Reads bit; zero invokes branch reader, nonzero consumes pointer | Confirmed |
| Actor bank wrappers | `0806AFB8`, `0806B02C`, `0806B0B8` / `0006AFB8`, `0006B02C`, `0006B0B8` | Install `03003107` as bank base; read/set/clear; restore scratch context | Confirmed |
| Generic bit helpers | `08069F60`, `08069F8C`, `08069FBC` / corresponding file offsets | `ldrh` ID, byte offset `ID >> 3`, mask-table index `ID & 7`; AND / OR / BIC | Confirmed |
| Mask table | `0863A01C..0863A024` / `0063A01C..0063A024` | `01 02 04 08 10 20 40 80` | Confirmed |
| Argument byte fetch | `08022534` / `00022534` | Reads from staged cursor `030039C0+2C`, advances it, returns byte in scratch+1 | Confirmed |
| FD84 and dispatch | `08028490`, `080299D0`, `08029A20` / corresponding file offsets | Builds argument bytes at `030039C0+19` onward using scratch-resolved sources, then dispatches staged opcode | Confirmed |

Thus `address = 03003107 + (ID >> 3)`. Both candidates have byte index `017F`;
their respective bit indices are 6 and 7. High bits contribute to the byte index;
none is stripped as a class/polarity field. Set preserves the other seven bits;
clear preserves the other seven bits. The two candidates do not alias each other.
An ID used by multiple maps **does** share persistent state: no map number enters
the address formula. Map-local actor slots and globally indexed persistent bits
are separate identities. Unique IDs are needed for independent persistent state,
although the decoder does not enforce uniqueness.

FD53/54 operands must not be described as universally ROM-immediate constants.
Ordinary predecode stages script arguments; FD84 can supply scratch-derived
bytes through the same cursor. A search for literal `FE 0B` / `FF 0B` cannot
close the state-ownership proof. This audit records the dynamic construction
mechanism but does not enumerate and prove every script path reaching it.

Additional **Confirmed** actor-record consumers, beyond the four commands:

- `08069C0C`: special pickup interaction reads current record `+E/+F` through
  `03001AD8`; `08069CAA` sets that bit on its success path.
- `08069D14`: when `03001974 != FF` and `03001973 == 1`, computes
  `03001948 + (selectedSlot-1)*10`, loads record `+E/+F`, and sets the bit at
  `08069D42`. This writer needs its caller/state contract accounted for in a
  complete lifecycle proof; it is not excluded merely by inspecting FD53.
- Actor loader `08034498..080344A8` reads each record's ID and bank bit.

The analyzer inventories only the established 494 map descriptors and their
2,987 actor records. Neither candidate occurs there. This limits record-sourced
writers in the **existing** tables, but does not prove absence of script-sourced
or native/bulk state use. Native BL/literal candidate xrefs are bounded to file
`00021000..00072000`; they are explicitly not a reachability or whole-engine
writer closure. Generic helper calls using other bank bases do not automatically
write the actor bank. No conclusion rests on absence from this candidate search.

### Default, save and reload

**Confirmed:** `0802EF0E..0802EF36` stages 384 actor-bank bytes into `02001905`;
`0802F490..0802F4B4` restores them from decoded save-slot `+105`. Both candidate
bits occupy decoded slot byte `+284`, staging byte `02001A84`. Reload restores
their saved values; the loader does not select a fresh map-specific flag bank.

Reset routine `08032984` sets r8=0 at `08032990..94`. At `08032A12..1C` it
passes a zero source, destination `03003107`, control `01000060` to wrapper
`080942E0` (`0C DF 70 47`, BIOS SWI 0C then return). Adjacent reset requests
target `030032E7` and `03003287` with control `01000018` at `08032A20..3A`.
**Confirmed:** call arguments and zero-source construction. **Probable:** this is
the normal new-game bank clear. The invocation contract, BIOS alignment handling
for these unaligned destinations and subsequent initialization are not fully
proved here. The raw call alone is not claimed as proof that the two bits remain
zero at first room entry. An existing save can restore nonzero values regardless
of this reset request. No saves were loaded to infer a universal default.

## C. Registration specification and conditional manifest

The following bytes are an exact **conditional specification**, not approved
patch bytes. Registration safety remains unproved. JSON `conditional_manifest`
contains original header/actor bytes, expected map pointers and proposed edits.
There is no complete patch-ready *approved* manifest while Gate B is blocked.

| Field | Namp | Mayonen |
|---|---|---|
| Map / cell / local slot | `005F` / `(25,5)` / `7` | `004D` / `(14,6)` / `8` |
| Candidate persistent ID | `0BFE` | `0BFF` |
| Original map record | `0862DE48` | `0862DC50` |
| Map actor pointer field / expected → proposed | file `0062DE5C`: `10 50 14 08` → `F8 06 80 08` | file `0062DC64`: `88 43 14 08` → `E8 07 80 08` |
| Source / proposed block | `08145010` / `088006F8` | `08144388` / `088007E8` |
| New record / following terminator | `088007C8` / `088007D8` | `088008C8` / `088008D8` |
| Record index relative to actor list | `(7-1)*10 = 60` | `(8-1)*10 = 70` |
| Init/controller pointer at record+6 | `08101FCF` | `08101FCF` |
| Interaction pointer at record+A | `0880037C` | `088006E8` |
| Runtime actor base `03001BDC+30*slot` | `03001D2C` | `03001D5C` |
| Activation byte `030028E1+slot` | `030028E8` | `030028E9` |
| Occupancy halfword `0300274C+4*slot` | `03002768` | `0300276C` |
| Interaction offset pair `03002820+4*slot` | `0300283C` | `03002840` |
| Persistent byte / mask | `03003286` / `40` | `03003286` / `80` |
| Existing event table, unchanged | `0815A1BC` | `0815A124` |

Candidate record contents derived from template `0814D4C4`:

```text
Namp:    28 07 72 19 05 00 CF 1F 10 08 7C 03 80 08 FE 0B
Mayonen: 28 05 62 0E 06 00 CF 1F 10 08 E8 06 80 08 FF 0B
```

Both new record destinations currently expect sixteen FF bytes. Specify a new
16-byte terminator `FF` followed by fifteen zero bytes, also over sixteen FF
destination bytes. Copy the original `70`-byte header and all six/seven original
records byte-identically at the same indices, then perform only these header edits:

| Relative block offset | Expected | Proposed | Binding |
|---|---|---|---|
| Namp `+1C` | `00 00 00 00` | `7C F7 13 08` | graphics slot7 |
| Namp `+5C` | `EC B1 43 08` | `CC C3 43 08` | palette7 |
| Mayonen `+14` | `00 00 00 00` | `7C F7 13 08` | graphics slot5 |
| Mayonen `+58` | `EC B1 43 08` | `CC C3 43 08` | palette6 |

Mayonen palette5 at `+54` remains unchanged. Existing allocation/wrapper targets
come from Stage 2; this report does not reopen their allocation or relocation.

### Visibility, activation and interaction

**Confirmed local behavior:** control byte `28` has bit0 clear. The loader at
`0803428A..080342B8` calls `08065DC0` with activation argument zero. That helper
sets runtime actor+2 bit0 and `030028E1+slot` bit0; it writes `FFFF` to the
occupancy halfword. This establishes linkage/initialization, not collision-free
movement or the ultimate occupancy updater.

Record byte1 `07`/`05` has bit7 clear. Loader `080343F0..FA` puts this zero in
`03001B6C`. At `080344AC..08034574`, a zero persistent bit skips the additional
activation call; a set bit calls `08065DC0` again with argument zero. Both paths
therefore end with the same relevant activation bits and occupancy halfword.
The candidate IDs' *saved bit values alone* do not invert these specific records'
initial activation. This narrows Stage 2's general warning about visibility;
it does not certify arbitrary record control bits or all subsequent consumers.

Interaction dispatcher `0806974A..7E` uses `(slot-1)*10`, masks record control
with `82`, and reads nonzero pointer at `+A`. `28 & 82 == 0`. Byte1 bit7 is
clear, so `08069784..8A` bypasses pickup handler `08069C0C`; the ordinary event
path at `080697C8..D4` stores clicked slot at `03003A32` and calls `0806AAA0`.
This proves the registration dispatch selection after the engine selects this
slot; interaction-origin and actor-selection geometry remain Gate C work.

### Initializer and lifecycle boundaries

**Confirmed:** `08101FCF..08101FD2` decodes as `2B 01; 5C`. Main dispatch table
entry `0862B5A8` is `75 3C 02 08`, selecting `08023C74`. For context IDs at most
15, this handler uses the context as local actor slot, consumes literal mode1,
and calls `08065E4C`. That helper updates runtime actor+3 as
`(old & F8) | mode`; it does not load graphics or palettes and does not write
persistent flags. Main5C table entry `0862B66C` selects `08024290`, which writes
the context's saved script pointer at context record+14 from context record+4
(`03003AD4 + 1C*context`). Calling it ordinary permanent actor deletion would
be unsupported. Slots7/8 satisfy main2B's context limit independently of ID.

**Unconfirmed lifecycle obligations:** complete scheduling of record+6 on entry,
all callback roots reached by either room's events, pending selected-slot state
around exit, and teardown/reinitialization ordering on re-entry. The loader's
unused-slot tail applies `08065DC0` with argument zero to slots through15; the proposed populated
slots precede that tail. That is not a room-exit cleanup proof. Record+6 is stored
in actor state by the loader; this audit does not certify every later scheduler
consumer. No dedicated new persistent write or exit callback is proposed.

Re-entry repeats registration **if the normal loader path is invoked**. Save/load
preserves IDs' bit values and does not namespace them by room. Bit-value-independent
initial activation is established; universal re-entry, interaction and deferred
writer noninterference are not. The exact initial/default and cleanup contracts
therefore remain partially specified, which precludes PASS under the requested
definition.

## D. Remaining gate impact

- **C, movement/collision:** resolved local slot-to-activation and occupancy-reset
  linkage, interaction offset-pair locations, standard-event dispatch and mode1
  initializer. Unresolved: occupancy update/removal over time, movement ownership,
  interaction origins, neighboring Namp controller trajectories and Mayonen door
  access. No path or movement PASS follows from registration instructions alone.
- **D, graphics/palette:** the proposed initializer's direct instructions only
  change actor mode/context state; it is not itself a resource-copy command.
  Existing slot/palette bindings stand. Scheduling, animation consumers, deferred
  room writers and resource teardown/re-entry closure remain unresolved. No new
  lifetime PASS is claimed.
- **E, regression:** Stage 2's static exchange equivalence remains PASS within
  its stated scope. Complete regression remains dependent on B/C/D. No contradictory
  exchange or relocation evidence was found.

## E. Smallest next proof task

Complete an **actor-bank operand provenance closure**, rooted specifically at
`080276E8/0802770C/08027778/080277AC` and FD84 staging `08028490`, using typed
event command boundaries and reachable script sources. For every reachable
actor-bank read/write, prove whether the operand can equal `0BFE`/`0BFF`; include
record-based setters `08069CAA/08069D42` and reset/load callers. Deliver a closed
list of writers/readers or a concrete conflicting use, rather than another
raw-ID absence search. No alternative ID is justified before this result.

This proof is still a static-analysis task; a single debugger observation cannot
prove global flag ownership. No user-operated debugger request is warranted.
If ownership closes, finish only the two rooms' entry/exit actor callback closure
to approve the conditional records, then use those same callbacks to finish the
remaining C/D dependencies. Construction remains withheld until those gates pass.

## Preservation

Only three new files are introduced: this report, its evidence JSON, and
`tools/analyze/hawker_stage2b.py`. The analyzer verifies every one of Stage 2's
671 protected fingerprints against actual files, then compares before/after
fingerprints for workspace ROM/save/state, report/source/manifest and common
asset formats outside installed Ghidra/mGBA directories and Git/cache directories,
plus every historically protected file inside those tool installations. Exact
suffix selection is in `snapshot()`; compiled Ghidra API classes are excluded.
This includes original/translated/cumulative ROMs, saves,
states, assets, manifests and previous analysis artifacts. The evidence records
1,141 before/after fingerprints, including all 671 historical fingerprints, plus
the new analyzer/report hashes. Zero ROM writes; no prior artifacts edited.

**GATE B BLOCKED — SPECIFIC ACTOR DEPENDENCIES UNRESOLVED**
