# Three-map music resolution and Cumulative v3 — 2026-10-28

**Tomato Adventure — Cumulative v3 Incomplete Experimental Build.** Map016D
is now confirmed as an active Oyster Sewers side channel and changes selector
0E→10. Maps012C and0158 remain unresolved and unchanged. No emulator, live RAM,
save, savestate or gameplay operation was performed.

## V2 revalidation and an explicit correction

The actual8,388,608-byte v2 matches SHA-256
`300e38f33881307682e1faf0bae4d4194306c2bfec9978f63d30b244719bd482`.
Its canonical English-baseline rebuild and v1 incremental output reproduce every
byte. The separate v2 verifier passes all281 differences,87 confirmed rooms,
the AWE restore,2,304 Attack comparisons, prior feature preservation, header and
both BPS decodes. Actual BPS and ZIP hashes match release_identity.json. All45
existing relevant tests were rerun unchanged and passed; seven new tests pass.

**V2's statement that016D had no ordinary incoming edge was incorrect.** The
original ROM and retained map_transitions.csv already contain both016C→016D and
016D→016C (rows594/595). This was a reporting/investigation oversight, not a missing
catalog edge or a game change. V3's independent ordinary-exit census exposed it.
The initial new-session unresolved draft is preserved as
`tools/patch/output/cumulative-v3-20261028/resolution_draft_before_016d.json`.
Historical v2 sources/reports remain unchanged; this report supersedes that one
reachability claim. No established destination-track identity was changed.

## Address convention and bounded scope

ROM bus address minus08000000 gives file offset; RAM addresses have no ROM
offset. Actual map table is file0062D3E4, stride1C. All three current music bytes
are0E; byte+5 low six bits are the selector. Record addresses/bytes and operation
decisions are in `cumulative_v3_music_resolution.json`.

The investigation follows registered roots for the three records,0124–012B,
0155–0157/015B,010B–010F and0169–016C. Existing conservative traversal is reused
only as an overapproximation: false paths are retained. No traversal budget was
exhausted. Ordinary incoming references were independently recounted from all494
actual map exit lists. Literal destination searches are bounded to the existing
field-script interval file0F9000..13D1EC. Native literal-load xrefs were limited
to the known native code interval0..0F9000 and the two saved-destination buffers.
No unrestricted Ghidra analysis, sprite work or new map extraction occurred.

## Destination storage, writers and consumers — Confirmed static

| Mechanism | Native address | Data flow |
|---|---|---|
| FD73 | 08027DB8 | Read an immediate LE16 map operand through080227F0; store at03001AC4+6=03001ACA; populate remaining arrival bytes |
| FD74 | 08027DFC | Read low/high bytes through08022534, combine low+(high<<8), store at03001ABC+6=03001AC2; populate remaining arrival bytes |
| FD75 | 08027E50 | Read saved03001AC2, copy to03001ACA and request03001936; copy arrival fields, merge command flags and call0802C1F0 |
| Normal exit | 08069AA6..08069AAC | Read LE16 exit-record+4, write03001ACA and request03001936 |
| Field loader | 08033D2A..08033D36 | Load request+6, multiply by28 and select original map record |

FD75's one-byte argument is flags, **not a map ID**. It does not add one or
construct a new ID from scratch variables. FD73's two-byte reader consumes staged
argument bytes; FD74's two byte reads likewise use the explicit arguments in
these scenes. The observed writers in the scoped Oystown paths select010B
(plus inherited/external paths selecting0008). No scoped writer selects012C,
0158 or016D. These facts narrow the earlier indirect-writer lead; they do not
prove absence of every aliased write in the entire game.

Other saved-buffer xrefs include new-game initialization to map1, save/restore
copies, existing request copies and the map-selection controller below. Arbitrary
old saves are not evidence of a normal incoming route, and were not inspected.

### Conditional arithmetic selector — Confirmed code, ordinary access unproved

Native08068418 has a path that reads the current saved map03001ACA, adds an
offset stored in utility030018BC+4 at080684C0..C6, and writes the resulting low
halfword to03001ACA and03001936 at080684E8/EC. Thus predecessor+1 can numerically
select012C from012B,0158 from0157 or016D from016C when this controller is active
and its input/range conditions permit. This is conditional selection, not proof
of story reachability or region membership.

The caller chain is08020ED2→08068090→080683A4→08068418. Dispatch table
0862B408 index3 points to Thumb wrapper08020ED1. Initialization08067FDC reads
the menu at0864A19C; decoding with ta_table_jpn.txt yields “Map,” “Battle,”
“Pattern,” “Partner,” “Difficulty,” “Kaizo,” “Return.” Input handlers use the
key-state halfwords030019C4/C8 and category03001AE5+4. This is **Probable** map/test
UI context. Normal-game activation of that category/state was not established.
Do not call it an ordinary doorway or treat possible map cycling as area proof.

## A. Map012C

- Record file0062F4B4; music file0062F4B9, actual0E (see machine ledger for exact
  independently computed addresses). No ordinary incoming exit was found.
- No literal FE7C/FE7D/FD73/FD74 destination012C appears in the bounded field
  scripts. This is a negative scoped finding, not exhaustive unreachability.
- Default0812472A initializes/returns (`FE89; FD7C`). Ordinary interaction
  pointers use the common FD7D termination block08124B2D.
- Rectangle0812D7B3 checks flag0155, stages a battle30 and later sets0155. Its
  local event behavior is real; it does not supply an incoming destination writer.
- Graphics resemble a village copy, but original0E differs from ordinary village04.
  Neither this resemblance, the flag nor conditional controller selection proves
  Dropper Village or Vault ownership. There is no normal incoming writer→consumer
  chain to establish an identity. No local A7/A8/A9/AB was found in the bounded
  registered-root closure; transitive/global coverage remains qualified.

**Decision:**leave unchanged; region identity and normal reachability Unresolved.
No proposed selector. Smallest useful follow-up is the activation/creation path
for rectangle0812D7B3's intended map context, or a user-observed natural transition
that actually enters012C. Do not manufacture such an entry through the map/test UI.

## B. Map0158

- Actual selector0E. Its outgoing ordinary exit at0813C4AC returns to0127.
  No ordinary incoming edge or bounded literal destination0158 was found.
- The alleged0127 indirect path was checked concretely. Registered rectangle
 0810054A tests flag010B (`FD36 0B01`):when clear it branches to return08100564;
  otherwise it executes `FE7D 5701...` at08100557, selecting **0157**, not0158.
- No FD73/FD74/FD75 in the scoped0127 closure constructs0158. The established
 0157 scene can proceed to015B or return0127, as retained in v2; those values are
  not silently reinterpreted as0158.
-0158's default is0812472A; its placeholder/common interactions terminate through
 08124B2D. No local music override was found. Its village-looking resource is
  not sufficient to identify a Vault illusion or a village room.

**Decision:**leave unchanged; normal incoming route and ownership Unresolved.
The proof stops before an incoming writer. Smallest useful next evidence is a
specific writer/dispatch context selecting0158, or a natural user-observed entry.
The outgoing edge alone does not justify Oops Mannor08.

## C. Map016D — Confirmed static Oyster Sewers

This proof does not rely on FD73/74 being incoming writers:

1. The retained normal Oystown010F event at08105ACC executes FE7C with destination
   016C; an alternate FE7D at08105B3C also selects016C. V2 already established
   016C as a sewer channel, with its ordinary Oystown entry/return contexts.
2. Map016C's actual exit list pointer selects file0013C610. Its second record at
   **0813C61A** is `00 03 00 04 6D 01 06 0D 84 08`:source x0,y3..4, destination
   **016D**, arrival x13,y4 after normal high-bit coordinate masking.
3. The native normal-exit consumer at08069AA6 reads record+4, writes016D to
   03001ACA and03001936, and the field loader selects record016D. This is an
   authored normal exit, not a hypothetical save value or map-test arithmetic.
4. Map016D's return record at **0813C628** is
   `0E 03 0E 04 6C 01 02 01 84 08`:source x14,y3..4, destination016C at x1,y4.
   Both edges already exist in retained map_transitions.csv.
5.016C and016D select the same original sewer tileset and base palette. Their
   retained backgrounds form compatible neighboring lower channels. Region proof
   combines the normal Oystown script path, confirmed sewer anchor, paired exits,
   native consumer and resource identity; it is not adjacency alone.
6.016D's default at **0810C600**, selected by event table0815B094, executes FD74
   and FD73 with **010B**. These set return information **after entry**, not the
   incoming016D ID. Subsequent flag00C3/01FE branches each initialize/return; they
   neither replace the map nor disable the ordinary exit. Actor interaction
   08106970 can set00C3 after its shared event; its narrative meaning is not
   invented. All flags and interactions are unchanged.
7. There is no A7/A8/A9/AB in the bounded local registered-root closure. Ordinary
   music is map byte+5 low6; the verified Oystown source remains selector10.

**Patch:**file **0062FBD5**, bus0862FBD5, byte **0E→10**. Upper metadata bits
remain zero and unchanged. No script, story flag, return destination, exit,
collision, actor or music interpreter is changed. Reachability is **Supported
static under existing normal area/story access**, not newly runtime-confirmed.

## Construction, verification and limits

V3 canonical build reuses the exact v2 pipeline from the English baseline, then
applies the approved016D byte. Incremental v2→v3 must match it. The independent
verifier imports neither analyzer nor v3 builder:it checks exact incoming/return
records, Oystown entry command, native writer bytes, resource identity, all three
decisions and the sole output difference. It reconstructs canonical output from
the previous full ledger and checks both BPS decodes. Reversing this one byte
reproduces exact v2 and passes its independent verifier, including all prior
features and2,304 Attack comparisons.

The initial assertion of no incoming edge for all three maps failed during
independent checking. It was investigated against the original ROM and retained
CSV, leading to the supported016D operation; it was not simply suppressed. A
separate hand-transcribed native literal-load byte witness was corrected after
readback (0C4C→0D4C); no native code was modified. Initial evidence/draft files
are retained locally. Final evidence is
`cumulative_v3_destination_evidence_final.json`; preliminary evidence is historical.

Only016D is resolved for patching.012C/0158 remain unassigned, and possible global
native/event continuation contexts are not exhaustively proved. Therefore v3
remains **Incomplete Experimental**, even though all88 confirmed music rooms and
the AWE lesson restore pass static checks. No gameplay success is asserted.
