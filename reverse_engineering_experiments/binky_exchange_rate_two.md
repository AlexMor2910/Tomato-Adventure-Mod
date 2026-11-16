# Constant two-Binky full-AWE exchange

> **Session 5 closeout supersedes historical test-status labels below:** all six Alessa/Sofoubi/Relleck character/stage reward tests are now user-confirmed passed. Offline checkpoints were independently inspected. See [current closeout](binky_exchange_session5_closeout.md) and [evidence](binky_exchange_session5_evidence.json). Cancellation, partial-gauge, capacity and multiple-full-gauge regressions remain pending. Older construction evidence/manifests are retained unchanged.

Date: 2026-10-13. **Implemented and verified offline; early Alessa runtime validated.**
Later Alessa tiers, Sofoubi and Relleck remain runtime untested. The original
construction findings below are preserved; subsequent runtime evidence and the
read-only remaining-test investigation are recorded at the end.
No mGBA/Ghidra operation, live RAM write, story edit, party edit or state rewrite.
The user authorized construction after critical static checks; those passed.

## Findings and evidence levels

The Hawker Kid exchange has **five transaction blocks**, selected by story flags,
full-charge checks and the existing character menu. Rewards are script immediates,
not a global Binky multiplier. Three blocks differ from the target rate; two
already award two. Changing all three differing blocks' display, grant and
capacity operands makes every successful path award two while preserving its
original selected-character reset, eligibility and return behavior.

- **User-confirmed runtime:** original early Alessa exchange accepted a full
  gauge, awarded one Binky and reset the gauge. Original Oystown introduction
  and normal shortcut travel worked. At construction time no patched exchange
  had been tested; the later early-Alessa result below supersedes that status.
- **User-reported hypotheses:** later character/story reward tiers in the request.
  They are not substituted for the actual branch conditions below.
- **Confirmed static:** exact script commands, dispatch pointers, native data flow,
  inventory records and patch comparisons described here.
- **Probable:** narrative meaning of the rate-selector flags. Their associations
  with What, joining characters or Letitbi are not proved by this investigation.
- **Untested at construction:** patched gameplay, later character selections,
  capacity rejection, advice rendering and checkpoint loading. The latest section
  confirms loading/early Alessa exchange for the reported case only.

Read-first sources: AGENTS.md, modding plan, all three handoffs in
`session_handoffs/`, readiness/progression/shortcut reports, AWE and exchange
reports, event/character/inventory mapping, checkpoint tools and existing patch
conventions. Historical findings were checked against actual ROM bytes. This
experiment does not continue missing-Gimmick or story reconstruction.

Reproducible bounded analysis:
[binky_exchange_rate.py](../../tools/analyze/binky_exchange_rate.py), command
`python -B tools/analyze/binky_exchange_rate.py`. It prints JSON only.
[Preflight evidence](binky_exchange_rate_two_evidence.json) retains the commands,
scoped native instructions, exact old/new bytes, original/replacement advice,
checkpoint reads and the 86-file protected inventory. No whole-ROM analysis or
arbitrary free-space search was used. Reviewing documented translation pointer
sites is a data-reference audit, not whole-ROM code analysis.

All bus-to-file conversions subtract `0x08000000`; RAM has no ROM file offset.
The event operands and native routines are existing original locations within
the English ROM. The advice is a translated asset; its address is specific to
the fingerprinted English baseline and validated recruitment derivative.

## Event entry, eligibility and character selection

Exchange event entry: **0x08107E81**, file **0x00107E81**. It prepares actor/event
state, then enters the exchange body at **0x08107E90**. Message 4AC's pointer
operand at0x08107E9A resolves the original “Whose AWE! points” dialogue; source
`ta_script_eng.txt` and `pointers1.dat` identify it as the Hawker's exchange.
The original Oystown intro is separate:0x081084CA and guard1F4. Neither is patched.
This is static script identification, not a newly captured live NPC dispatch.

| Check/site | Verified effect | Inputs/storage |
| --- | --- | --- |
|0x08107E90 FD35 01FC →081081CC|Exhaustion/retirement exit before normal selection|Main flag1FC:03003326 mask10 |
|0x08107E9E FD35 00BA →08107FC0|Selects the three-character charge/menu tree|FlagBA:030032FE mask04 |
|0x08107EA6 FD35 01C4 →08107ED7|Selects the two-character tree if BA path was not taken|Flag1C4:0300331F mask10 |
|Otherwise08107EAE|Checks character1 only|No party-record injection |
|FEC0 /08029BB8|Read character's persistent+58 into accumulator03003A24|Operand1/2/3; record03001EDC+index*60 |
|FD3B 0040 /0802A43C..2A4E6|Exact halfword equality branches to full-gauge choices|Charge must equal40hex; not a readiness-bit bypass |
|FEBC,FE7A,FEB5/B6/B7|Existing dialogue/response branches choose transaction/cancel/advice|Kept byte-for-byte; no selection remapping |

**Correction to a preliminary reading:** the selector is **1C4**, not C4; it is
encoded `C4 01`. The script checks flags, not a direct membership test or a named
boss ID. Character1/2/3 identities are independently documented by
`ta_menus_eng.txt`, RESTRUCT630BDC: Alesa/Sofubi/Rellek. The user spells them
Alessa/Sofoubi/Relleck. Do not infer the precise flag setters from those names.

The verified tree provides these original transaction blocks. Character column
is established from each block's final FEC1 operand; full menu behavior at later
stages remains untested. The data disagree with the reported “Relleck always one”
and “Sofoubi up to two” hypotheses in this ROM.

| Bus start /file offset | Reset character | Original displayed/granted quantity | Original rejection cutoff |
| --- | --- | --- | --- |
|08107F52 /00107F52|1, Alessa|1|99 |
|08107F89 /00107F89|2, Sofoubi|1|99 |
|081080F7 /001080F7|1, Alessa|3|97 |
|0810812E /0010812E|1, Alessa|2|98 |
|08108165 /00108165|3, Relleck|2|98 |

No additional FE55 grant occurs in the decoded exchange scope
`[0x08107E81,0x081081DA)`. All five blocks are55 bytes and match the same
transaction skeleton, differing only in the three quantity-related operands and
the selected character reset. Keeping all selection branches while equalizing
the five endpoints removes progression dependence of successful rewards.
The documented pointer map for offer message4B5 lists exactly those five block
sites. An additional use of thank-you message4B7 at0812DDD0 was inspected in its
bounded surrounding commands: it is in a FE46/FE97 event sequence, not another
full-AWE/item-grant transaction. Shared dialogue alone is not another exchange.

## Display, inventory update, capacity and reset

Each block performs the following normal sequence:

1. `FD00 quantity` (handler08028C7C) loads03003A24. Message4B5 uses `[NUMBER]`;
   `asm/dialog_center.asm:217–219` explicitly documents that accumulator.
   `FE31 03 01` is actor state, not a quantity setter. The offer and confirmation
   dialogue remain intact; only their supplied number changes.
2. FE7A handles the response; cancel exits through081081B4. No award on cancel.
3. `FE5C 37` queries itemID37. Source item-name row36 is Binky, one-basedID37.
   Handler080257C4→08028748 searches the ordinary inventory list at030019D5
   (count030019D4, two-byte entriesID/count), returning the count to03003A24.
4. `FD1F cutoff` at08029AAC computes comparison flags. `FD45` at0802984C
   rejects when count is **at least** cutoff, branching to081081C0. Original
   cutoffs are `100-quantity`, enforcing a successful final count≤99. For two,
   accept counts0–97; reject98/99 before consuming AWE. Existing refusal text4BA
   says the Hawker has no stock; this wording is preserved, not relabeled as a
   new capacity-specific message.
5. `FE55 37 quantity 081081D8` (08025634) stores item/quantity in03003A34/35,
   calls080291D4→08080424. The shared insertion routine finds/appends anID/count
   pair; **actual existing-stack addition/store is08080514–0808051E**. Its generic
   guards/failure paths08080534..80542 and event failure continuation are retained.
   Only these exchange operands change; the routine itself and other item awards
   are untouched. Any FE55 failure returns through the original failure target.
6. Original sound/thank-you dialogue executes; FEC1 invokes08029BEC and clears
   selected character+58 and+59. No artificial ready bits, partial-gauge exchange
   or manual reset is introduced. FEC1 is after the successful grant path.

New read-only corroboration: `before_oystown.ss0` has Binky entryID37/count2 at
030019D9/DA; `after_exchange_oystown.ss0` hasID37/count3 there, consistent with
the reported original one-Binky exchange. This is an endpoint observation, not
an instruction to use that slot address forever; inventory sorting can move it.
Verify ID before interpreting a count. This advances the earlier report's
unmapped-field status only for the inspected ordinary inventory representation.

## Exact patch

No assembly, branch, pointer, new allocation or event-length change is necessary.
The smallest supported rate edit is nine single-byte operand changes. Updating
only the grant would leave a wrong offer or inconsistent capacity cutoff.

| File offset (bus = offset+08000000) | Original → replacement | Role |
| --- | --- | --- |
|00107F54|01→02|Alessa one-tier offer |
|00107F6B|63→62|Alessa one-tier capacity cutoff99→98 |
|00107F76|01→02|Alessa one-tier actual grant |
|00107F8B|01→02|Sofoubi offer |
|00107FA2|63→62|Sofoubi capacity cutoff99→98 |
|00107FAD|01→02|Sofoubi actual grant |
|001080F9|03→02|Alessa three-tier offer |
|00108110|61→62|Alessa three-tier capacity cutoff97→98 |
|0010811B|03→02|Alessa three-tier actual grant |

All five patched blocks have `FD00 0200`, `FD1F 6200`, `FE55 37 02 ...`, with
their original FEC1 character preserved. Already-two blocks remain unchanged.
Eligibility, story tests, character selection, sounds, transaction failure paths,
AWE reset and original return instructions are preserved byte-for-byte.

### Correcting the obsolete progression advice

Message4B8 explicitly says the reward may change as friends join. Keeping that
claim would contradict the balance change. The offer message4B5 is already
dynamic, so needs no text rewrite beyond FD00.

4B8's only documented pointer, source`pointers1.dat` row4B8 atfile001081A2,
resolves **0865FC48**. Its original translated string is exactly205 bytes in
`[0065FC48,0065FD15)`. The next message begins0065FD15. The complete original
string round-trips from `ta_script_eng.txt` through `ta_table_eng.txt` and the
documented control codes to those exact bytes. `inserter/text.cpp` establishes
first matching character-table entry, space00 and control encoding. The documented
main-message pointer sites contain no other pointer into this allocation.

Only the false paragraph is rewritten, preserving the preceding full-gauge
requirement and ending “Nyo-ho-ho...”:

```text
Every full AWE! gauge[BREAK]
is worth two binkies,[CONTINUE]
from any character.[WAIT]
```

Complete replacement is175 bytes, endsFF40FF00, followed by30 FF bytes inside
the old string allocation. This is reuse of a verified owned string, not a claim
that arbitrary FF runs are free. No pointer, next string, translation source or
recruitment payload is modified. Lines fit the existing layout width; rendering
still requires a manual check. All other dialogue remains unchanged.

Both manifests and preflight JSON contain **complete old/new hexadecimal strings**
for every operation, including the205-byte text interval. Actual differing text
ranges (half-open) are:

- `[0065FCA4,0065FCB8)`
- `[0065FCB9,0065FD03)`
- `[0065FD04,0065FD11)`
- `[0065FD12,0065FD13)`
- `[0065FD14,0065FD15)`

These total109 changed text bytes. Plus nine script bytes = **118 actual changed
bytes per source**. No differences outside those14 ranges exist.

## Construction, artifacts and compatibility

Script: [binky_exchange_rate_two.py](../../tools/patch/binky_exchange_rate_two.py).
Default produces a standalone8MiB baseline patch; `--profile recruitment-test`
produces a separately verified16MiB test derivative. Both reject unexpected or
already patched inputs, validate every original operation, compare every output
byte, re-read the output/manifest, check protected hashes and reject existing
destinations. Optional `--output-name` accepts a simple new directory name only.
Failed writes can leave a fresh incomplete directory; never reuse it.

```powershell
python -B tools/patch/binky_exchange_rate_two.py
python -B tools/patch/binky_exchange_rate_two.py --profile recruitment-test
```

| Profile | Input SHA-256 | Output SHA-256 |
| --- | --- | --- |
|Standalone English,8MiB|8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde|b9967b15193b5aec701032742d322a1040373e76b176b1aeb1e65ce2c06078b6 |
|Recruitment test,16MiB|3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6|d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3 |

Standalone ROM:
`tools/patch/output/binky-rate-two-baseline-c4ec3611142c49cf93d891cbfc10f056/binky_exchange_rate_two.gba`
with [manifest](../../tools/patch/output/binky-rate-two-baseline-c4ec3611142c49cf93d891cbfc10f056/manifest.json).

**Use this ROM for the existing checkpoint test:**
`tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`
with [manifest](../../tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/manifest.json).

The test derivative preserves the recruitment redirect at0010D69F and every byte
from00800000 through01000000 (payload/reservation/padding). Only the new rate/text
patch differs from that exact validated source. Its existing wrapper will not
be replayed. No unspecified balance/music patch is stacked.

Existing checkpoints have recruitmentROM CRC E9ACB98F, matching title/game ID,
normal savedPCs08021EB0/080226E2 and no active interpreter slots. mGBA0.10.5
checks title/ID, CPU state and relevant PC/ROM-size bounds; a CRC mismatch by
itself is a version warning. Source:
[mGBA0.10.5 deserialization checks](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/serialize.c#L77).
The8MiB standalone is not rejected solely because the state originated under
16MiB, but shrinking changes mapping and could invalidate retained addresses.
**Do not assume cross-size gameplay compatibility.** The same-size test derivative
preserves the old layout and addresses; this supports a controlled load test,
not a claim it has already loaded successfully. No state/header/RAM is edited
to force compatibility. Stop on anything beyond an expected CRC-only warning.

## Verification and protected integrity

- Preflight passed: five complete transaction patterns, exact command boundaries,
  all FE55 exchange endpoints, nine operands, owned advice bytes/pointer, unchanged
  scoped handlers and identical sites in baseline/recruitment sources.
- Both constructions and readbacks passed complete comparisons,118 actual changed
  bytes, unchanged sizes/headers and exact operation/manifest matches.
- Independent verification reconstructed each expected output from the retained
  ledger and compared whole files/hashes. The test prefix differs from standalone
  at only the three original recruitment pointer bytes; extension remains exact.
- `python -B -m unittest discover -s tests -p test_binky_exchange_rate_two.py`:
  **five tests passed**. Tests check all five rates with counts0–99, correct
  rejection boundary98, already patched input/corrupt output rejection, next
  string preservation, wrapper preservation, existing-directory and unsafe-name
  rejection. No emulator or ROM output is produced by the tests.
- **All86 pre-existing protected ROM/save/checkpoint artifacts unchanged**, including
  Japanese/English baselines, validated recruitment ROM and user captures. Only
  two new experimental ROMs were added; current inventory88. Original JSONs,
  prior outputs, translation ASM/C++/text and saves/states remain unchanged.

New files: analysis tool, preflight JSON, patch script, five-test module and this
report. New local output artifacts: two ROMs and their manifests. No unrelated
research report or state-completion work was changed.

## Manual mGBA0.10.5 validation

The user performs every runtime action. Use the **16MiB test derivative** and a
disposable copy of root`after_exchange_oystown.ss0` (hash
`aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646`).
It is already in Oystown after the intro, with early Alessa, Binky count3 and
charge00. Preserve root`before_oystown.ss0` and all originals. Do not replay
recruitment or clear story/intro flags.

1. Configure a fresh isolated portable environment with independent saves/states,
   screenshots/logs and empty patches/cheats paths; loadStateExtdata=9,
   saveStateExtdata=9, rewindEnable=0, useBios=0, skipBios=1. Verify copied ROM and
   state hashes, open only those copies. Load paused. A CRC-only version warning
   is expected; stop on state rejection, title/ID/BIOS/size errors or other faults.
2. Confirm both characters, menus and movement, and record the Binky quantity in
   the inventory GUI before editing anything. Optional first debugger action only:
   `r/1 0x030019DA`, expected03 for this restored source. Its entryID at030019D9
   was statically verified37; if sorting/items changed, re-identify the entry
   instead of trusting the slot. Do not issue a command batch.
3. After reviewing that observation, separately confirm actual persistent charge
   at03001F94; expected00. Only after its current value is confirmed, use the
   previously validated user-operated full-charge mechanism to set40 in this
   disposable session, then verify with a separate read. No ready-bit, inventory,
   party or progression edits. This report does not request simultaneous writes.
4. Talk to the original Hawker and select Alessa. Offer must show **2**. Accept;
   dialogue must finish normally, GUI Binky count must increase exactly2 (3→5
   if unchanged), and gauge must reset. Verify counter/charge with separate
   individually reviewed reads if needed. Stop on wrong offer, wrong delta,
   partial award, no reset, corruption, freeze or abnormal return.
5. Check advice: full gauge required; every character yields two. Repeat a valid
   exchange only on a disposable branch after restoring a full gauge normally/
   through the authorized manual charge procedure. Confirm partial gauge and
   cancel do not grant Binkies or consume a valid gauge. Keep captures distinct.

**Pending later-state tests:** Alessa's former3-rate case, Sofoubi's selection,
Relleck's selection, all multi-full-gauge menus and naturally obtained near-cap
counts97/98/99. No valid later-party checkpoint was identified; do not manufacture
one by changing membership/story flags. Use a legitimate available state later
and check before/after inventory counts and selected-character reset. At count97,
a valid exchange should add2→99; at98/99 it should refuse without AWE consumption.
Near-cap test states are not fabricated in this work. Also verify an unrelated
Binky pickup remains at its original reward, and a disposable save/reload cycle.

Work stops after construction/documentation. Static uniformity is verified;
patched runtime success for any character/stage remains **untested** until the
user supplies observations.

## Subsequent early Alessa runtime validation (reported 2026-10-13)

The user explicitly confirmed testing the existing16MiB recruitment/exchange ROM:
SHA-256 `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3`.
They loaded a disposable copy of the pre-Oystown checkpoint, entered Oystown,
retained the functional DeMille–Alessa party, manually set persistent Alessa
charge03001F94 to40, and completed a normal exchange.

| Observation | Result | Evidence classification |
| --- | --- | --- |
|PatchedROM/checkpoint load and Oystown entry|Succeeded|User-confirmed runtime |
|Existing party functionality|DeMille–Alessa remained functional|User-confirmed runtime |
|Full Alessa gauge accepted|Yes|User-confirmed runtime |
|Binky award|Exactly2|User-confirmed runtime |
|AWE reset|Normal|User-confirmed runtime |
|Event completion|No errors reported|User-confirmed runtime |

Original early exchange previously accepted full AWE, awarded1 and reset normally;
patched exchange awarded2 under the reported early Alessa conditions. This is a
**successful user-confirmed runtime A/B comparison**. It used separate sessions
and disposable checkpoint copies, not a supplied frame-identical trace. No new
debugger transcript, inventory readback or screenshot is invented. Intermediate/
late Alessa, Sofoubi, Relleck, capacity refusal, cancellation, advice rendering
and physical save/reload remain **Untested** unless separately observed.

### Newly available user checkpoint and read-only verification

Root `after_exchange_oystown_alessa_test.ss0` actually exists, SHA-256
`85110875375c28ab412e4413e986d9cb65eb81353d1214f3b86e6d7b7a02f1cf`.
Format/PNG/state/extended-data checks pass; ROMCRC **AB34C118** matches the patched
testROM. Savedmap0104/node08, membership31/count02, three existing Gimmicks,
introflag1F4set, charge/ready00 and BinkyID37/count04 are **Codex-confirmed static**.
They corroborate the report but are not userconsole measurements or a complete
transaction audit. The old pre-entry state had02 Binkies and original post-exchange
state03; this new saved endpoint has04.

Both existing ROM outputs were re-read and verified against their full source
files, exact patch ledger, known hashes and manifests:118 changed bytes each,
five uniform two-Binky blocks, preserved native handlers/eligibility/selection/
reset and preserved16MiB recruitment payload. The patch script still matches its
construction hash. No builder/main was invoked, no ROM regenerated, and no
implementation concern requiring correction was found. Original manifests retain
their construction-time “runtime untested” metadata; this report carries newer
evidence without rewriting them.

Remaining-test report:
[binky_remaining_character_tests.md](binky_remaining_character_tests.md).
Read-only tool/evidence:
[binky_remaining_tests.py](../../tools/analyze/binky_remaining_tests.py) and
[binky_remaining_tests_evidence.json](binky_remaining_tests_evidence.json).

**Next recommended Candidate:** intermediate Alessa, using only flag1C4 at
0300331F mask10 on a disposable copy of the new post-test state; BA/1FC remain
clear, absent companion2 charge stays00 and only Alessa charge becomes40 through
the already validated manual procedure. Original and patched intermediate rates
are both2. A separate later Candidate usesBA at030032FE mask04, with both absent
companion charges00, selecting original3→patched2. Narrative milestone meanings
of these flags remain unresolved; they are conversation-only selector simulations,
not story reconstruction. Live values must be observed separately before writes.

FE49's full handler was now scoped: from31 it selectsindex2 and ORs40 (31→71),
then from valid71 selectsindex3 and ORs80 (71→F1), preserving activepartner1.
It invokes the original generic initializer, not a membership-only shortcut.
The last branch can reset an already present Relleck. Other companion branches
are Codex-confirmed static and runtime Untested; a safe one-shot carrier/default
inventory contract is not newly certified. FE4A/4B only alter membership bits and
are not initialization substitutes. No new character or patch was created.

All90 current protectedROM/save/checkpoint artifacts retain identical before/after
hashes. Both exchange outputs, validated recruitmentROM and all userstates are
preserved. Changed only this report; added the planning report, read-only tool
and evidenceJSON. No runtime experiment begins in this session. The exact first
future user observation is `r/1 0x0300331F` (expected00) after loading a disposable
copy of the new source while idle; no write or command batch is requested now.
