# AWE initialization and tutorial investigation

Date: 2026-10-13. Bounded, read-only static analysis and user-authorized
documentation. No emulator/Ghidra execution, RAM edit, ROM construction, save/state
load or modification. Earlier AWE claims in `session_handoffs/SESSION_HANDOFF_3.md`
were checked against current ROM bytes; conclusions below distinguish literal
operations from gameplay predictions.

**Finding:** a narrowly controlled **Alessa persistent charge = 0x40** experiment
is supported for the already initialized DeMille–Alessa party. From valid readiness
00–03, normal battle initialization sets both ready bits and copies charge/ready
into the partner battle record. No separate DeMille-charge or tutorial-flag change
is justified for this first functionality experiment. Full tutorial completion and
a fully coherent pre-Oystown state remain **unconfirmed**.

**Latest evidence:** the charge-only experiment was subsequently performed by the
user and succeeded in an ordinary battle. See the final runtime section; static
predictions and remaining tutorial/save/progression limits below are preserved.

## Evidence, confidence and reproducibility

Read-first sources: AGENTS.md, modding plan, all three handoffs (latest 3),
[recruitment experiment](experiments/alessa_recruitment_wrapper.md), both retained
preflight/allocation JSONs and analysis tools, battle-menu/status assembly,
translation overview, symbols, character/event and ROM mapping reports.

New tool: [tools/analyze/awe_initialization.py](../tools/analyze/awe_initialization.py).
Run `python -B tools/analyze/awe_initialization.py` from the workspace root; it
prints JSON only. Retained output: [awe_initialization_evidence.json](awe_initialization_evidence.json).
It records 17 bounded instruction windows, parsed tutorial commands, threshold
bytes, scope hashes and current protected-file inventories. No whole-ROM pointer
scan, disassembly or automatic analysis is performed. Hashing complete files is
an integrity check, not game-code analysis. The local Thumb inspector is not an
emulator; known literal pools are excluded from instruction observations.

All 17 scoped instruction windows are byte-identical between Japanese baseline,
English baseline and the validated recruitment derivative. The scoped tutorial
commands likewise match in all three ROMs. Their addresses are **original-ROM
locations**, unchanged by translation/recruitment; the recruitment's separate
payload at 0x08800000 is newly allocated. Bus-to-file conversion subtracts
0x08000000. RAM addresses have no ROM file offsets. Function names below are
research descriptions, not recovered developer symbols.

Confidence vocabulary:

- **User-confirmed runtime:** explicit observations supplied in the current user
  request. Both characters, normal battle, Gimmicks, movement, event return and
  Pop Horn entry `2B 01 00` were observed. No AWE observation was supplied.
- **Confirmed static:** exact ROM bytes, addressed loads/stores or supported
  data flow within the stated scope.
- **Probable:** intended gameplay meaning supported by the code and existing
  terminology; not newly tested.
- **Candidate:** proposed edit or mechanism requiring a controlled test.
- **Unconfirmed/untested:** unavailable evidence or no runtime result.

## Persistent and battle fields

| Address / field | Meaning, source and evidence | Confidence |
| --- | --- | --- |
| 0x03001EDC + character*0x60 | Persistent character record base/stride. Used by initializer 0x08032CB8 and battle constructor 0x08047CFC. Alessa character index 1 → base 0x03001F3C. | Confirmed static; Alessa membership/inventory additionally user-confirmed runtime |
| Alessa +0x58 = 0x03001F94, unsigned byte | Charge. Initializer store 0x08032E28 clears it; battle constructor reads at 0x08048072; battle exit writes at 0x0803FE80. | Confirmed static data flow; AWE-charge interpretation Probable pending direct AWE runtime observation |
| Alessa +0x59 = 0x03001F95, unsigned byte | Ready state. Initializer store 0x08032E36 clears it; threshold comparisons OR bits 01/02; copied into battle and back. | Confirmed static operations; exact UI/action behavior untested |
| Battle record base 0x03000938, stride 0x84 | Participant record; character ID at +0, status halfword at +0x10. Normal constructor increments participant count at 0x0804808C. | Confirmed static |
| Partner slot 1 +6 = 0x030009C2 | Battle charge copied from Alessa when character 1 occupies slot 1; constructor store 0x08048074. | Confirmed static conditional mapping; slot identity must be checked if party arrangement differs |
| Partner slot 1 +7 = 0x030009C3 | Battle ready byte copied at 0x08048086 and checked by menu gate 0x0804DD4A. | Confirmed static |
| 0x03000BAD | Actual battle participant count read by menu gate. Distinct from persistent membership 0x03001AB4 and derived field-party count 0x030035F0. | Confirmed static |
| 0x08639784 + (companionID-1)*0x58 | Two AWE definitions per companion, each stride 0x2C; threshold byte at each definition +0x22. Alessa: 0x086397A6 = 28 hex / 40 decimal, 0x086397D2 = 40 hex / 64 decimal. | Confirmed static bytes/indexing |
| 0x03001F34 / 0x03001F35 | DeMille record +58/+59 exist and are copied by generic paths, but threshold evaluation skips companion ID zero and gate uses partner slot. | Confirmed static layout; no independent DeMille full-charge edit justified |

This is the game's partner AWE state for the DeMille–Alessa pairing. Do not invent
two independent gauges or fill DeMille's analogous fields merely because they
exist. Availability of the command at each participant's particular turn and the
precise player-facing AWE action selection still require manual observation.

### Initializer and recruitment dependency

FE49 selects Alessa when her membership bit is absent, calls 0x08032BF0 →
0x08032CB8, and clears charge/ready as described above. The validated wrapper's
FE53 then gives Pop Horn. The user-confirmed party/battle results substantiate
normal recruitment for that scenario; they do not measure AWE state specifically.

Full charge must be initialized **after recruitment**, not before FE49, which
would erase it. Replaying FE49 is not an idempotent way to repair AWE: with Alessa
present, it can initialize another companion. No membership, inventory, equipment,
ready-mask or battle-participant injection is proposed.

## Charge and readiness behavior

Battle constructor 0x08047CFC–0x080480BC derives both participants from membership
and initializes their battle records. At 0x08048006 it skips companion-threshold
processing for character ID zero. For a companion, 0x0804802E compares unsigned
charge with threshold 40 and 0x08048046 compares with threshold 64. Passing a
threshold **ORs** its bit into the persistent ready byte. The constructor then
copies charge/ready to the battle record.

**Correction to the earlier handoff's shorthand:** this is not a full recalculation
that clears obsolete bits. A below-threshold charge does not clear a stale ready
bit in this path. With fresh recruitment's ready=00, or a valid ready value in
00–03 and charge=40 hex, both low bits become 03. Unknown upper bits must not be
silently accepted or overwritten. The menu gate accepts any nonzero ready byte;
invented bit values can misleadingly make that gate pass.

Predictions from ready=00, all **confirmed static arithmetic / runtime untested**:

| Charge decimal (hex) | Ready low bits after normal battle initialization |
| --- | --- |
| 0 (00) | 00 |
| 39 (27) | 00 |
| 40 (28) | 01 |
| 63 (3F) | 01 |
| 64 (40) | 03 |

At 0x08042AC0–0x08042AD0 the normal gain path adds a table-supplied gain, stores
the resulting byte, and clamps a resulting byte above 64 to 64. Readiness is
subsequently ORed through the gain state machine at 0x08042B7E–0x08042BAC. This
supports 64 as the intended full charge. The arithmetic stores/truncates before
clamping; it is not an input validator for arbitrary out-of-range injected bytes.
Future initialization must use exactly 40 hex, not 64 hex or a larger value.

## Ordinary-battle eligibility

Source: `asm/battle_menu.asm` replaces AWE label drawing near 0x0804DCC6 and
0x0804DD08. Retained caller at 0x0804DCB0 invokes 0x0804DD10 before considering
the translated label. The gate's complete bounded body 0x0804DD10–0x0804DD64:

1. Read 0x03000BAD; if it equals 1, return false. The body does not robustly
   validate all malformed counts; normal battle construction supplies valid count 2.
2. For each participant, load status halfword +0x10 and reject if any bit in
   **0x0104** is set. For slots 0/1 these halfwords start at 0x03000948 and
   0x030009CC. Either participant can block the command.
3. Read partner slot's ready byte 0x030009C3; reject zero, accept nonzero.

These operations are **confirmed static**. No tutorial flag, field map, persistent
charge or event-completion flag is consulted directly in this body. Precise
gameplay names of status bits 0004 and 0100 are **unconfirmed** in this bounded
investigation; they must not be described as a particular ailment without further
writer/consumer evidence. The consequence is definite: either masked status
disables AWE regardless of charge.

The normal constructor clears participant status at 0x08047ECA. Subsequent battle
effects can set statuses. A successful gate is not proof that every action-state,
input, target and animation path will complete; the command's full menu/action
state machine was not exhaustively audited. No gate bypass is proposed.

## Consumption and persistence

| Native address / research role | Evidence / consequence | Confidence |
| --- | --- | --- |
| 0x080501D4–0x0805027C, AWE action state | Uses partner character ID minus one and selected definition byte at 0x03000C3C to select a 0x2C definition. After action completion check 0x0805023C, subtracts its threshold at 0x08050262, stores charge at 0x08050266, clears the entire battle-ready byte at 0x0805026C. | Confirmed static; successful execution untested |
| Lower/higher definition from initial charge 64 | Costs 40 or 64: immediate post-use charge prediction 24 (18 hex) or 0 respectively, ready 00. Both readiness bits are cleared even after the lower-cost use. | Confirmed static arithmetic; exact option labels and manual observation pending |
| 0x0803FE42–0x0803FE9C, battle exit | Copies battle HP/charge/ready to corresponding persistent character IDs for two slots, skipping FF IDs. A nonzero byte at **0x03000748** bypasses this copyback block. | Confirmed static; semantic name/all writers of this special-mode guard unconfirmed |
| 0x0803FE7C–0x0803FE90 | Copies each battle +6/+7 to persistent +58/+59. For Alessa slot 1 these map to 0x03001F94/95. | Confirmed static normal branch |

Further turns can add charge after AWE consumption, so do not insist the battle-end
charge still equals the immediate post-use subtraction. Compare the measured last
battle charge/ready with the resulting persistent fields when testing copyback.
Battery save/reload retention and every victory/escape/defeat/special-battle path
remain **untested**. “Persistent” here is the between-battle character record;
this report does not independently certify physical save serialization.

## Tutorial entry, exit and completion limits

The bounded stream is original bus `[0x08128D5A,0x08128F48)`. Command lengths are
read from the actual FD/FE/plain tables; arbitrary byte matches are not called
commands. It is unchanged in the recruitment ROM.

| Site | Verified operation / implication | Confidence |
| --- | --- | --- |
| 0x08128D5A | `FD 35 71 01 34 8F 12 08`: tests flag 0171 and transfers to 0x08128F34 when set. Handler 0x08029F58 → 0x08029F90 → flag reader 0x0806AE2C; transfer 0x08029F2C. | Confirmed static entry guard |
| 0x08128D62 | `FD 49 71 01`: sets flag 0171 before dialogue, battle, cleanup and return. Handler 0x08029FF0 → 0x080274A4 → 0x0806AEA0. Storage 0x030032E7+(171 hex >>3) = 0x03003315, mask 02. | Confirmed static; “completed tutorial” interpretation only Probable and insufficient by itself |
| 0x08128D9A / 0x08128E40 | FD0B selector 24 writes 0028 / 0060 to scratch halfword 0x03003A48; selector 12 at 0x08128D9F writes 0000 to 0x03003A36. These are not Alessa charge fields. | Confirmed static selector arithmetic |
| 0x08128E64 and 0x08128F1C | FE7A provides alternate script path/response handling around the lesson; alternate path 0x08128F22 transfers back to 0x08128E6A, later path 0x08128F2E to 0x08128E8E. | Confirmed static bytes/targets; exact response semantics unconfirmed |
| **0x08128E77** | `FE 41 59` selects battle descriptor 0x084559B4+(59 hex−1)*0x28 = **0x08456774**. Native handler 0x08024FC8 sets battle descriptor/mode parameters and calls 0x0802C2B4. | Confirmed static; corrects handoff's one-byte-early 0x08128E76 |
| 0x08128EEB / 0x08128EFB | `FE 75 01 01` then `FE 75 00 00`. Handler 0x08025D94 sets event control bytes 0x03003A09–0x03003A0C and mode-related 0x03004E06 handling. | Confirmed static writes; transient-control interpretation Probable |
| 0x08128EEF | `FE 83 02 01 01 02` feeds camera parameters through 0x08029698 → 0x08066168, including 0x03002790–0x03002794 and busy byte 0x03001B4A. FE86 at 0x08128EF5 waits on that byte via 0x08025FC0. | Confirmed static; not an AWE-ready setter |
| 0x08128F08–0x08128F14 | Audio command sequence FEAB / FEA9 0D, script callback FE07, final **FD7C** return. | Confirmed static main-path end; complete cleanup semantics not proven |
| 0x08128F34 | `FD 36 FE 01 44 8F 12 08`: tests flag **01FE** with false-condition branch to 0x08128F44. FD36 has six operands, not an empty terminator. | Confirmed static secondary branch |
| 0x08128F3C | `FD 35 B7 00 44 8F 12 08`: true-condition branch using flag **00B7**. 0x08128F44 has FE89 and 0x08128F46 FD7C. | Confirmed static checks; these flags' story meanings/relationship to lesson completion Unconfirmed |

Flag 171 being set **does skip the main lesson body at this entry**, but routes
through the additional guard/exit path. Thus it is sufficient to suppress this
body, not proof that all natural lesson effects occurred or that every possible
tutorial invocation is disabled. The flag is an entry marker, set before success.
The secondary checks 1FE/B7 are not established completion markers and must not
be set or cleared speculatively.

Within the decoded main stream, 171 is the only direct FD49 flag set. That is a
bounded observation, **not** proof that called scripts/battle code set no other
persistent marker. Actor callback scripts supplied through FE07, child events,
the special battle and full exit modes have not been transitively audited.
FE89 also adjusts scheduler/control state; FE83/86 clearly concern camera state.
No direct main-stream command was established as filling Alessa's AWE. Ordinary
battle initialization/gain/use may change it during the lesson; dedicated tutorial
battle effects remain unresolved. No replay of this whole scene at Hanzo is safe
to recommend: it assumes location, actors, scenario and event context.

Missing evidence for **completed tutorial equivalence**: natural entry/exit state
comparison; all relevant callback/special-battle persistent side effects; complete
meaning of 1FE/B7 and 0x03000748; and a demonstrated ordinary-battle AWE result
after the natural lesson. Until these are established, do not simulate completion
with flag 171 or arbitrary low-numbered story flags.

## Compare future initialization approaches

| Approach | Correctness, reproducibility and impact | Decision |
| --- | --- | --- |
| A: replay original lesson/event | Uses original mechanics, but lesson has actors, branching, scripted battle, scheduler/audio/camera controls. Hanzo context is not the original scene. No verified standalone persistent charge setter was identified in this scope. | Do not replay the tutorial in an unrelated carrier. Original scene is appropriate only at its normal entry with verified prerequisites. |
| B: guarded persistent charge initialization | One known byte after valid recruitment, followed by normal battle construction, gate, consumption and copyback. Keep ready bits and tutorial flags untouched; check existing state before applying. A future user-operated disposable RAM-only A/B test can log/reproduce the exact one-byte operation without changing any ROM. | **Recommended first controlled functionality experiment**, Candidate supported by confirmed static data flow. Requires separate authorization for the write and manual runtime work. |
| C: hybrid event-based charge initialization after recruitment | Correct ordering could preserve original recruitment and normal battle machinery. A derivative ROM needs a verified interpreter/native interface for the single charge store; one has not been established here. Tutorial suppression would be a separate change. | Candidate future production mechanism, not ready to implement from this investigation alone. |

### Minimal proposed change set (future authorization only)

Preconditions: disposable copy of a user-created **post-recruitment, outside-battle**
checkpoint on the validated recruitment ROM; membership 31; normal initialized
Alessa/inventory/equipment; valid readiness byte 00–03, no unexplained upper bits.
Charge must be in normal range 00–40. None of these post-recruitment AWE byte
values has yet been provided by the user. Do not substitute root entry-stop as
an already-recruited state.

Proposed data change: **only 0x03001F94 → 40 hex**. If already 40, no edit is
needed. Leave 0x03001F95 alone and let ordinary battle initialization OR low bits
to 03. Leave DeMille's fields, live battle fields, party count, statuses, tutorial
flag 171, 1FE/B7, AWE thresholds/gain/consumption, HP and inventories untouched.
If readiness/state preconditions are violated, stop and explain the discrepancy;
do not broaden the operation to “repair” fields automatically.

This one-byte plan is enough to **test full-charge functionality**. It is not a
method for manufacturing a completed tutorial, save serialization or coherent
pre-Oystown progression. No state editor, checksum fixer, RAM-writing script or
ROM patch was constructed in this session.

### Recruitment derivative and expansion implications

The verified SHA-256 recruitment ROM is the source of the valid party experiment,
not a normal English baseline: it contains Hanzo's permanent pointer redirect and
an appended 16 MiB image with its 21-byte script at 0x08800000. Its original
prefix differs at exactly three previously documented bytes. This investigation
confirmed all relevant AWE/tutorial instruction/data windows remain unchanged.

A future RAM-only A/B test should keep that ROM unchanged and start after its
one-time recruitment event. Do not replay Hanzo or original recruitment. A future
ROM derivative, if justified, must use this exact hash, a new output, verified
interpreter-level store/context and explicit payload allocation. Appending more
data or placing a setter before FE49 is not automatically safe. No current need
to change the Hanzo redirect, expand again or alter its reserved payload follows
from the charge-field evidence. Existing experiment ROM/environment remain intact.

## Manual observation and future validation sequence

No emulator action is requested for this static-only session. For a **future
authorized manual session**, the first precise action is:

```text
r/1 0x03001F94
```

Perform it only while paused outside battle after successful recruitment on the
verified ROM, then report the result and visible party/location. This is a read,
not a proposed write command. Subsequent debugger actions are requested **one at
a time after review**, rather than pasted as a bulk sequence.

Planned sequence, requiring separate authorization before any state change:

1. Preserve the existing ROM/test environment; use fresh isolated copies of the
   same known post-recruitment checkpoint for control A and charge trial B.
   Record hashes/version, disable rewind/patches/cheats, isolate saves/states and
   use `loadStateExtdata=9`. No protected source state is disposable.
2. Review the initial charge read; next independently inspect readiness and party
   identity. Verify prerequisites before proposing the one-byte controlled edit.
3. Enter the same ordinary battle naturally in A/B. Sequential reads should check
   slot-1 character ID 0x030009BC = 01, participant count 0x03000BAD = 02,
   charge 0x030009C2 = 40 and ready 0x030009C3 = 03 in B; inspect status halfwords
   0x03000948 / 0x030009CC only if the command is blocked. Do not modify them.
4. Observe the AWE command and usable options/animations with both characters
   recognized. If it remains blocked despite measured prerequisites, stop and
   obtain one next gate/action observation, not an eligibility bypass.
5. Use a normal AWE option. Pause at an appropriate manual observation boundary
   to record charge/ready after use; predicted charge is 18 or 00 hex depending
   on selected cost, ready 00. Additional turns may subsequently add charge.
6. End the battle normally; compare persistent 0x03001F94/95 with the last observed
   battle fields. If copyback differs, investigate mode guard 0x03000748 and actual
   exit path. Enter another battle normally and verify no forced refill. Saving/
   restarting from a new disposable battery save is a distinct persistence check.
7. Tutorial completion testing remains separate: at its natural entry, record
   pre/post state and flags in a separate authorized session. Do not combine the
   first charge trial with tutorial-flag edits.

Stop on unexpected membership/slot identity, invalid charge/ready values, altered
inventory/equipment, freeze, abnormal menu/action/return or unexplained persistence.
Never patch RAM to force the expected observation.

## Deliverable status and integrity

Updated recruitment report records all supplied runtime observations and limits.
New files: this report; `tools/analyze/awe_initialization.py`;
`reverse_engineering/awe_initialization_evidence.json`.

The new analysis verifies the expected Japanese, English, recruitment ROM and
root checkpoint hashes. **81 current protected ROM/save/checkpoint files** retain
identical before/after path/hash inventories. This inventory is the current
workspace snapshot, including existing user test artifacts; it is not a claim that
the workspace must still contain only the earlier 79 files. No prior evidence JSON,
manifest, experimental environment or translation source was edited.

Decision: a guarded one-byte **persistent-charge experiment can be proposed for
separate authorization**. Its results still need manual confirmation. An integrated
event-based ROM implementation and synthetic completed-tutorial state are **not
ready**: setter/context and tutorial completion effects remain unresolved. Work
stops here, with no construction, RAM edit or further progression work.

## User-confirmed charge-only experiment (reported 2026-10-13)

The user supplied these observations in the subsequent pre-Oystown progression
investigation request. Codex did not operate mGBA or perform the write. The user
reported a screenshot showing the battle interface/AWE command; no screenshot
file or additional live-memory capture was independently inspected in this session.

| Observation | Reported result | Confidence |
| --- | --- | --- |
| After recruitment and an ordinary battle, persistent charge 0x03001F94 | 01; user attributed this accumulated charge to the preceding battle | User-confirmed runtime read; origin attribution reported by user |
| Initial persistent readiness 0x03001F95 | 00 | User-confirmed runtime |
| Manual disposable-session operation | `w/1 0x03001F94 0x40` | User-confirmed runtime action, not a Codex action or instruction to repeat now |
| Subsequent charge read | 40 | User-confirmed runtime |
| Intentional other changes | No readiness byte, tutorial flag or other AWE address intentionally modified | User-confirmed procedure |
| New ordinary battle | DeMille and Alessa both appeared; AWE command visible; gauge appeared full; AWE worked | User-confirmed runtime availability/operation |
| After AWE use and battle completion, persistent charge 0x03001F94 | 05; user reported additional charge gained during the battle | User-confirmed runtime final read |

The tested DeMille–Alessa party supports **charge-only initialization at
0x03001F94 = 40 hex**. A manual readiness edit was unnecessary. This is consistent
with the traced normal threshold and copyback mechanisms. Battle-local ready bits
03 were not separately measured in the supplied observations, so retain that
value as a static prediction, not a new runtime read.

The transition from initial full charge to final 05 is consistent with consumption
plus post-use gain and post-battle persistence, but it does not independently
measure the quantity consumed. Do not derive an exact AWE cost from these endpoint
reads. Tutorial completion, battery save/reload, long-term progression and a
coherent full pre-Oystown state remain unresolved. Existing ROM/test artifacts
were preserved during this documentation update. No new AWE patch or state was
created. Further work: [pre_oystown_progression.md](pre_oystown_progression.md).
