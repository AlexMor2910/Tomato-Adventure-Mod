# Hawker Stage 2B — completed registration proof

2026-10-17. **Gate B passes for the registration records specified below.**
IDs `0BFE` and `0BFF` can be retained. One concrete correction is required:
the new records must start with `29`, not the Oystown template's `28`, so the
new actors initialize visible. This is static construction readiness for
registration, not runtime acceptance or permission to construct a ROM.

The requested `hawker_stage2b.md`, `hawker_stage2b_evidence.json` and analyzer
already existed from another session. They are preserved. This separate follow-up
supersedes their technical BLOCKED decision with additional evidence; it does
not rewrite historical findings. Reproduce with:

```text
python -B tools/analyze/hawker_stage2b_registration_followup.py
```

Output: `hawker_stage2b_registration_followup_evidence.json`. Save a replay to a
new temporary file. Gate A, private-script relocation and exchange equivalence
were not rerun. The Stage1C parameterized two-script architecture remains intact.

Input is the actual 16-MiB cumulative English ROM
`tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
All ROM addresses below are **English cumulative bus addresses**; subtract
`08000000` for file offsets. RAM addresses have no ROM file offsets. Function
names are analyst labels; the analyzer's `roots` and `native_windows` identify
their source locations, exact instructions/bytes and evidence hashes.

## A. Actor ID verdict

| Proposed NPC | Candidate ID | Result | Evidence | Required change |
|---|---|---|---|---|
| Namp Hawker | `0BFE` | SAFE | Unsigned bit decoder; global byte03003286 mask40; reset, writer census and serialization proof below | Retain ID. Use corrected control byte29 in its ordinary NPC record. |
| Mayonen Hawker | `0BFF` | SAFE | Same byte, independent mask80; same reset/writer/serialization proof | Retain ID. Use control byte29; palette6, preserving door palette5. |

SAFE applies to normal game-produced state and the exact registration schema
below. It does not cover edited/corrupt saves, arbitrary RAM/PC corruption or
future patches that allocate these bits. Reserve both IDs globally in future
mod manifests. No alternative-ID search is needed.

### Encoded semantics and global ownership

**Confirmed static:** FD53/54 at080276E8/0802770C assemble two bytes into a
halfword and invoke0806B02C/0806B0B8. FD5B/5C at08027778/080277AC invoke
0806AFB8 and conditionally consume/take their branch pointer. The three wrappers
select bank03003107. Generic08069F60/08069F8C/08069FBC perform AND/OR/BIC using:

```text
ID = unsigned16(argument)
byte address = bank base + (ID >> 3)
mask = ROM[0863A01C + (ID & 7)]
mask table = 01 02 04 08 10 20 40 80
```

All high ID bits contribute to the byte index; they do not encode an actor
class, polarity, map or special sentinel. Neither candidate is passed to the
runtime actor-slot resolver. Both use byte index017F, with masks40 and80.
Masked updates preserve the other candidate's bit. The serialized bank is384
bytes, supporting IDs0000..0BFF; the decoder itself has no range check.

The same ID in two maps aliases the same global persistent bit. It is safe only
when shared state is intended; the engine does not enforce uniqueness. For
example ID062B occurs in maps0112/01EC through their shared record0814E13C.
The proposed two Hawkers use distinct bits for independent identity.

Ownership is established by a bounded mutator proof, not just a search for the
two ID values:

1. All494 map descriptors and2,987 actor records are inventoried through their
   actual actor-block pointers and FF terminators. Maximum ID is0B9B; neither
   candidate occurs. The nonzero actor-initializer roots and map-default roots
   lie inside the event/registration domain below.
2. A conservative **all-byte** census of file000F9000..0015BA3C covers event
   scripts, actor records and event tables, ending at the known tileset-pointer
   table. There are5 FD53 candidates,425 FD54,80 FD5B and0 FD5C. Every operand
   is below0B9C. Including noninstruction bytes overapproximates potential uses;
   absence of a candidate operand does not depend on guessing command boundaries.
   Exact sites/bytes are in JSON `flag_sites`. The five setters are0812FC54,
   0812FC67,081302B7,081302CC,0813031A, using IDs0ADD/0AEB/0B23/0B2A/0B31.
3. Dynamic arguments were checked separately. All25 FD84 occurrences in that
   same domain have fixed family00: they dispatch main commands, not FD53/54/
   5B/5C. Thus the ordinary immediate-operand census is not invalidated by an
   unexamined scratch-derived actor-bank call at an existing FD84 site. The
   retained Alessa expansion script is independently matched and contains no
   actor-bank operation; its scratch writes remain in the separate scratch bank.
4. Targeted native direct-call and literal censuses cover file00000000..000F9000
   and the translated pool007F0000..00800000. They find eight calls to the three
   actor-bank wrappers:080276FC,08027720,0802778C,080277C0,080344A8,
   08069C22,08069CAA,08069D42. The first four are the decoded commands;
   080344A8 reads the loaded record's ID. The additional setters obtain IDs from
   pickup/battle records, rather than allocating another numerical ID domain.
5. The generic bit helpers were also audited, closing the possibility of another
   ordinary wrapper selecting this bank. Their12 direct callers select
   03003107,030032E7,03003A0D,03003E71 or0200EF6C. For the full unsigned16-bit
   ID range, all bases except03003107 address ranges disjoint from03003286.
   JSON `generic_bit_core_calls` records every caller, base and conservative
   8192-byte range. No Thumb function-pointer literal for these private helpers
   appears in the scoped native/event/VM-dispatch regions; the census is not
   limited to FD handlers.
6. All eight native03003107 literal pools are accounted for: three wrappers,
   save stage/load, reset, temporary backup and temporary restore. The latter
   two copy384 bytes without inventing new flag values. Their precise windows
   are08075D92..08075DBE and0807612E..08076158.

For the proposed records, byte0 bit7 is clear (ordinary NPC, not contact battle),
and byte1 bit7 is clear (ordinary event, not pickup). The branches at08069860..68
and08069780..8A exclude those automatic claim routes. The private exchange and
the complete initializer do not introduce a pickup/battle claim operation.
Existing pickup/battle records retain their original IDs below0B9C. This accounts
for08069CAA and08069D42; they are not silently omitted from ownership analysis.

These facts establish the normal-state invariant: no existing actor-bank mutator
changes either reserved bit, and other masked writes preserve them. This proof
does not assert immunity to arbitrary native pointer corruption or treat raw
pattern candidates as demonstrated executed commands.

### Default state, save and reload

**Confirmed static call/data flow:**08032984 constructs zero in r8 at08032990..
94. At08032A12..1C it requests a fixed-source BIOS fill of96 words beginning
at nominal03003107, followed by the neighboring flag/variable clears. The
trampoline080942E0 is `0C DF 70 47` (SWI0C, return).

Alignment matters: the actor fill's word-aligned physical range is
03003104..03003284. It alone is insufficient to prove byte03003286 zero.
The subsequent variable fill at08032A30..3A uses nominal destination03003287,
zero source and control01000018. Its aligned range03003284..030032E4 **does
clear03003286**. The two fills together establish the default of both bits as0.
The fill/count and alignment semantics are corroborated by the pinned upstream
[mGBA0.10.5 BIOS implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/hle-bios.s#L243-L270)
and [multiple-store implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/memory.c#L1500-L1530).
This is source inspection, not execution of mGBA.

0802EF0E..0802EF36 copies384 actor-bank bytes to staging02001905;
0802F48A..0802F4B4 restores384 bytes from decoded save-slot+105. The candidate
byte is slot+284 / staging02001A84. Save/load and temporary backup/restore
preserve it byte-for-byte. Zero default plus the closed normal mutator set gives
zero in ordinary game-produced premod saves; no save migration or save-file
write is required. Existing `before_oystown.ss0` and `after_kaizo_100_complete.ss0`
also have both bits zero in their serialized IWRAM; these two read-only samples
corroborate the invariant and are not its universal proof.

## B. Gate B decision and lifecycle proof

**Confirmed:** local actor slots7/8 are valid independently of persistent IDs.
The runtime reset at08035192..080351B6 clears16 records of48 bytes, including
player0. Source table copy08034ED4..08034F50 supports15 NPC records plus its
terminator. The resource/actor loader starts slot1 and advances once per16-byte
record. Six/seven existing records therefore append as slots7/8 without
renumbering any original actor or door.

The normal room-entry path at08031A88 calls runtime reset08035148 at08031B54,
then room loader08033C88 at08031B80. Loader0803411C obtains the new map's
actor/resource block and builds the same runtime structures for both slots.
The special entry dispatcher08037054 branches only for maps001E..002A; neither
005F nor004D can take its indirect scene handler.

The record+E persistent flag is checked at08034498..080344A8. With byte1 bit7
clear, a set persistent bit hides the actor; a zero bit preserves the initial
visible state. **The new record must start29:** first-byte bit0=1 bypasses the
initial hide at0803428A..080342B8. The inherited28 would call08065DC0 with zero,
set runtime actor+2 bit0, set activation-array bit0 and remove occupancy. An ID
change cannot fix that template error. No old Oystown record is modified.

The selected schema therefore produces active, visible actors with persistent
bit0 and ordinary event dispatch. Native0803F8CE..0803F8D6 binds
`03001948 = map.actorBlock + 70`. Interaction0806974A..7E uses
`(clickedSlot-1)*10` and the record+A pointer;080697C8..D4 registers the private
wrapper via0806AAA0. No persistent ID is used as an actor-array index.

Actor initializer registration0803F990 iterates slots1..15, skips hidden actors,
reads record+6 and supplies the **local slot** to0806AAA0. That constructor
clears the selected28-byte event record through08071C58 at0806AB2A, then
installs its script pointer at0806AB56. Old slot7/8 script cursors and linkage
cannot be inherited through this constructor.

The full shared initializer is08101FCF..08102004,53 bytes. It begins `2B01;5C`,
then executes the gesture loop at08101FD2; final FD30 returns to08101FD2.
**5C is not termination:**08024290 saves the advanced cursor into context+14.
The full bounded command list and backedge are in JSON `initializer`. The loop
does not fall through to the unrelated resource command following08102004.
Main2B at08023C74 uses the event's local actor slot (limited to0..15), so both
initializers affect their own actors. It changes animation mode, not visibility;
this is why control byte29 is required before initializer scheduling.

Normal transition0802C1F0 calls08071C04, which calls080694D4. That reset clears
the event table and all32 event records through08071C58. Room exit cannot leave
the Hawker initializer running in a reused slot after that transition. Normal
entry clears actor/auxiliary state and rebuilds registration; unpopulated slots
after the terminator are hidden by080346B2..0803472E. These operations do not
clear/reassign the global actor-bit bank. Re-entry and ordinary save/reload use
the same persistent interpretation and reconstruct the same local identity.

## C. Patch-ready registration manifest

These are specifications only. They reuse Stage2's destinations; allocation and
script relocation are unchanged and are not re-investigated here.

| Field | Namp | Mayonen |
|---|---|---|
| Map/cell/local actor slot | 005F /25,5 /7 | 004D /14,6 /8 |
| Persistent ID / encoded bytes | 0BFE /`FE 0B` | 0BFF /`FF 0B` |
| Source block / destination block | 08145010 /088006F8 | 08144388 /088007E8 |
| New record bus / file | 088007C8 /008007C8 | 088008C8 /008008C8 |
| Following terminator bus / file | 088007D8 /008007D8 | 088008D8 /008008D8 |
| Initializer record+6 | 08101FCF | 08101FCF |
| Interaction record+A | 0880037C | 088006E8 |
| Runtime actor record | 03001D2C | 03001D5C |
| Event record | 03003B98 | 03003BB4 |
| Activation byte | 030028E8 | 030028E9 |
| Occupancy halfword | 03002768 | 0300276C |
| Interaction-offset pair | 0300283C | 03002840 |
| Persistent byte/mask/default | 03003286 /40 /0 | 03003286 /80 /0 |
| Existing event table, unchanged | 0815A1BC | 0815A124 |

Exact16-byte new records, each replacing sixteenFF destination bytes:

```text
Namp:    29 07 72 19 05 00 CF 1F 10 08 7C 03 80 08 FE 0B
Mayonen: 29 05 62 0E 06 00 CF 1F 10 08 E8 06 80 08 FF 0B
```

Retain direction nibble2 and zero signed offset from the original template.
Copy the70-byte resource header and six/seven original16-byte actor records
unchanged at their original indices, then append the new record and a16-byte
terminator `FF` followed by fifteen zero bytes. Terminator destination also
expects sixteenFF bytes. No new event/door table or story flag is allocated.

| Operation | Expected bytes | Proposed bytes |
|---|---|---|
| Map005F actor-block pointer, file0062DE5C | `10 50 14 08` | `F8 06 80 08` |
| Map004D actor-block pointer, file0062DC64 | `88 43 14 08` | `E8 07 80 08` |
| Relocated Namp header+1C, graphics7 | `00 00 00 00` | `7C F7 13 08` |
| Relocated Namp header+5C, palette7 | `EC B1 43 08` | `CC C3 43 08` |
| Relocated Mayonen header+14, graphics5 | `00 00 00 00` | `7C F7 13 08` |
| Relocated Mayonen header+58, palette6 | `EC B1 43 08` | `CC C3 43 08` |

Mayonen header+54 remains `EC B1 43 08`, and door records keep palette5.
The companion JSON records all original header/actor bytes and operations.
Construction must refuse a source hash, expected-record or destination-byte
mismatch and independently verify the emitted records and original actor indices.
There is no output ROM/hash in this investigation.

## D. Impact on remaining gates

- **C:** slot capacity, activation/hide polarity, occupancy-removal linkage,
  own-slot initializer scheduling, normal transition cleanup and entry reset are
  resolved. The loader obtains collision dimensions and sprite pointers from the
  selected descriptor for that same runtime actor; identity is not a separate
  collision index. This does not establish approach geometry, dynamic occupancy,
  blue-NPC trajectory separation or Mayonen door clearance. Gate C remains open.
- **D:** initial graphics/palette binding and normal room-entry header reload are
  resolved; all prior resource assignments stand. The full initializer loop is
  now bounded and does not fall through into the following resource command.
  Re-entry reconstructs the bindings. Deferred room resource writers and survival
  of all11 frames across active room events still require Gate D proof.
- **E:** the registration-identity dependency is discharged for these corrected
  records. Existing actors, IDs, door records, tutorial and original exchange
  bytes stay outside the proposed registration write set. Full regression still
  depends on C/D. Stage2's exchange-schema equivalence remains unchanged.

## E. Exact next action

Proceed with one bounded C/D investigation rooted in the already identified
controller scripts: Namp blue NPC081130AF..081130CE and Mayonen deferred
actor1 controller08128A95..08128AB4. Resolve command56's consumption of the
command50 parameters, then compose those trajectories with the two fixed Hawker
footprints, interaction origins and door/transition rectangles. Use the same
entry/callback graph to close graphics/palette writers. Do not repeat actor-ID
ownership, script relocation or exchange decoding.

No debugger observation is requested: those remaining questions still have
specific static paths. Gate B PASS does not permit direct ROM construction
while C/D are open. Runtime acceptance stays a separate user-operated phase.

## Preservation and scope

There were zero ROM/save/state writes and no emulator or Ghidra execution.
The analyzer verifies the prior Stage2 fingerprints and all1,141 fingerprints
from the earlier Stage2B evidence, including its original analyzer/report hashes.
Its combined before/after ledger contains1,146 protected files; all match.

An analyzer-name collision temporarily replaced the earlier Stage2B analyzer.
It was recovered from its recorded creation/edits and restored **byte-for-byte**
to SHA-256 `c1020353cf3ecb6c9286a73573d38ee3633e4c8e07c9d35e9944d118edde789e`.
The earlier report/evidence were not overwritten. This incident is recorded in
the new evidence; the final preservation claim is fingerprint equality, not a
claim that no protected source file was ever touched during the session.

New artifacts are this follow-up report, its evidence JSON, and
`tools/analyze/hawker_stage2b_registration_followup.py`. No commit was made.

**GATE B PASS — ACTOR REGISTRATION SAFE**
