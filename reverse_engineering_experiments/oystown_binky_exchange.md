# Oystown exchange validation and checkpoint completion

2026-10-13. Documentation, bounded static inspection and read-only artifact
verification. No emulator operation, live write, ROM construction or state edit.

## Runtime results and their limits

**User-confirmed runtime:** the initialized DeMille–Alessa party left Mayonen
normally, used the overworld route to HanzoLab3/Oystown, entered Oystown normally,
played the original introductory sequence including the Binky exchange
introduction, and showed no apparent errors/freezes. The user then filled Alessa's
persistent AWE charge at03001F94 to40hex; the exchange accepted it, awarded one
Binky and reset the gauge without apparent errors.

Reported progression edit sequence: original030032EB=0B; flags26/27 first added
withmaskC0→CB; flags24/25 then added withmask30→FB. Combined addedmaskF0, lower
nibble0B preserved. Initial user reads: membership03001AB4=31, cachednode
030035F4=04, Mayonen outdoor map03001936=0048. These observations supersede the
earlier cave-exit preparation blocker for the **tested** route, not proof of
every preceding story outcome or a universal cave-exit recipe.

The supplied transcript does not independently measure the Binky storage field,
an immediate post-transaction charge byte or exchange-specific flag writes.
Those remain separate from the new saved-state observations below. A successful
transaction is established by the user's observation; repeat transactions,
exhaustion, battery save/reload and later story compatibility remain untested.

## Artifact inventory

Read-only tool: [oystown_completion.py](../../tools/analyze/oystown_completion.py).
Reproduce: `python -B tools/analyze/oystown_completion.py` (JSON to stdout only).
[Evidence JSON](oystown_completion_evidence.json) includes all checkpoint groups,
full relevant character records, flags, scoped grant/exchange handlers and86
protected hashes. Required documentation and historical handoffs were reviewed;
latest runtime evidence supersedes older untested findings without erasing them.

| Exact workspace-relative path | SHA-256 | Saved classification |
| --- | --- | --- |
| `before_oystown.ss0` | `d20fc78972641d76e1b56f23daa80c9fedd4c07fa22edb63e69d37371db21c53` | Pre-entry foundation; map00DF, cachednode07, intro1F4clear |
| `after_exchange_oystown.ss0` | `aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646` | User-named/reported post-exchange; map0104, cachednode08, intro1F4set |
| `reverse_engineering/experiments/testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/captures/post-recruitment.ss0` | `4eb81a006e852955556664f8c76c4526458048dab644dfa6f36a4b20d352946f` | Earlier cave foundation; map001F, cachednode04, route0B, introclear |

All three are **confirmed static** PNG240x160 checkpoints: chunk CRC/bounds,
single state decompression to61000, version01000007, matching recruitmentROM
CRC32E9ACB98F/title/game code pass. Size:29297/35239/50433 bytes respectively.
No emulator load was performed. Other early checkpoints are retained in the
machine-readable inventory; none substitutes for these later party sources.
No separate post-introduction/pre-exchange checkpoint was found. The post-exchange
file actually exists; it is not inferred from the previous recommendation.

All three contain membership31, derivedcount02, DeMille entries01 01 00 and
1B 01 00, Alessa entry2B 01 00, and acquisitiondifficulty0300196E=01.
Both character records and equipped slots remain coherent with these entries.
Pre-entry/post-exchange character records differ only at Alessa charge+58:
05→00. This is an endpoint comparison spanning travel/introduction/manual charge/
exchange; it is **not** a complete transaction-level audit.

| Field | Pre-entry | Post-exchange | Evidence/limit |
| --- | --- | --- | --- |
|030032EB routebyte|FB|FB|Confirmed static; all24–27set |
|03001F94 charge|05|00|Confirmed static saved values; manual intermediate40 is user-confirmed, absent from these endpoints |
|03001F95 ready|00|00|Confirmed static |
|1F4 at03003325 mask10|clear(byte00)|set(byte10)|Confirmed static; consistent with original intro setter081086F0 |
|1C0 at0300331F mask01|clear|clear|Confirmed static, no edit needed for tested outcomes |
|171 tutorial at03003315 mask02|clear|clear|Confirmed static; lesson completion unresolved; tested entry/exchange did not require setting this flag |
|117 recruitment-scene marker|clear|clear|Confirmed static; do not replay original scene |
|227/228,229/22A,257,271/272|allclear|allclear|Confirmed static absent boss/reward/record markers; necessity for untested later gameplay unresolved |
|ToyParts03001AB6 /bytevariable3C030032C3|00 /00|00 /00|Confirmed static; not obstacles to the observed entry/exchange, not equivalent to completing their source scenes |

Across the96-byte main bank030032E7..3346, only03003325 changes00→10 between
these endpoints. Other persistent banks/items/actor state are not exhaustively
audited. Do not attribute every endpoint difference to the exchange alone.

The **pre-entry capture is outside HanzoLab3 on map00DF**, not an overworld
selection already atnode8 and not Namp map0060. Its screenshot shows HanzoLab3's
exterior. Descriptor0862EC48+0C points to exits0813BD08: firstrecord
`00 05 00 06 08 80 04 01 01 00` exits x0,y5..6 tospecialdestination8008,
whose normal dispatcher subtracts1→node7; secondrecord0813BD12 enters0032.
Use the normal exterior exit, then left7→8 and normal confirmation, as the
tested approach. Do not enter the lab/recruitment scene as a preparation shortcut.
Both new captures have schedulingbitmap030039C1..C4 zero; this supports idle
interpreter state, not independent proof of movement/control or reload success.

## Exchange code corroboration

Confirmed static, original locations unchanged in English/recruitmentROM:

- FEdispatchtable0862B8B4: C0→08029BB9 (Thumb), C1→08029BED.
- FEC0 handler08029BB8..29BDC reads selected character+58 and writes the
  transient accumulator03003A24. FEC1 handler08029BEC..29C18 clears **both**
  selected character+58/+59. Neither requires an invented battle-local edit.
- At08107FC0..0810801F, decoded FEC0 checks for companions1/2/3 precede
  `FD3B 4000 ...` branches. This corroborates the full-charge threshold40hex.
  Complete FD3B menu branch, stock/quantity and all external calls are not
  exhaustively audited here.
- Transaction-path endings in this bounded span contain FEC1 with selected
  companion operands (e.g.08108160 `FE C1 01`). This is consistent with reset,
  not proof that this particular branch executed in the user's transaction.

One Binky added is **user-confirmed runtime**, not a newly decoded inventory
counter. No address/quantity/stock field is invented from message numbering,
item operands or raw memory differences. Subsequent stock/exhaustion behavior
remains unresolved despite the successful first exchange.

## Missing core inventory and initialization

Names/IDs: source`ta_menus_eng.txt`,BLOCKFIXED490420 andRESTRUCT62C250;
runtimeID=row+1. Original Lab2script08111CE6 (map0031), Lab3script08112090
(map0032); shared reward08124B33. **Confirmed static**:

| Missing Gimmick | RuntimeID /owner | Original reward operand/shared call | Candidate atomic grant |
| --- | --- | --- | --- |
|Dojo Pup|29 /DeMille(index0)|08111E45 `FD0B 1C 2900`; call08111E4A|FE53 29 |
|Puffer|1F /Alessa(index1)|08111E59 packed5F; call08111E5E|FE53 5F |
|SneaKar|1D /DeMille(index0)|081121DD packed1D; call081121E2|FE53 1D |
|RabiShoes|07 /Alessa(index1)|081121F1 packed47; call081121F6|FE53 47 |

All four are absent in **both** inspected new checkpoints. Existing three
Gimmicks need preservation, not duplicate acquisition. Expected seven-core-only
counts after eventual grants:DeMille4/Alessa3; this is not optional completeness.

FE53 handler08025624→0802927C extractsowner high2bits/ID low6bits and calls
0806ADA0. The helper appends`ID,difficulty,upgrade0`, incrementscharacter+7,
sets two usagebytes0200EF08+2*(ID-1) fromoriginalrecord+25&1F and fills an
empty equippedslot+5A..5D. Capacityguard0806ADB4 accepts priorcount≤19; it
does not establish safe duplicate suppression. Current counts2/1 leave capacity.
Currentdifficulty01 is saved evidence; later acquisition must recheck the actual
event-time value rather than hardcoding inventoryentries. Correct preparation
must use the game's normal grant machinery through a valid interpreter, not
direct native calls or inventory-only injection.

Original Lab2event guardsclaimed229 and later setsroute25 at08111E7C, claimed229
at08111E80. Lab3guards22A and setsroute27 at08112213, claimed22A at08112217.
These original scenes also call actor/animation/common routines and can handle
ToyParts. A grant alone does not reproduce those effects. The shortcut lacks
ToyParts and both claimedmarkers; do not assume replaying an entire scene here
is safe just because its reward ID is known. AtomicFE53 grants are a **candidate**
way to reproduce complex inventory initialization; a stable, one-shot carrier
for this advanced source still needs preflight. The early Hanzo wrapper proves
one carrier only and must not be replayed on this recruited party.

### Optional content: explicit unresolved list

**No additional named optional Gimmick is confirmed pre-Oystown by the present
bounded evidence. This is an incomplete availability list, not proof there are
none.** The50-name ROM catalogue cannot be treated as early inventory.

Identified optional acquisition system: **Kaizo's Binky-funded Gimmick rewards**.
Translationmessages0E6,0ED–0F5,0F8 (`ta_script_eng.txt:1001–1097`) explicitly
describe Binky totals/thresholds and dependence on Hanzo-made Gimmicks. Pointer
slots080FC681,080FC78F,080FCD02/03B,080FCDC5 in`symbols.md` anchor this system.
This is **confirmed text**, with **candidate** relevance to pre-entry optional
availability. RewardIDs/owners, exact thresholds, mapaccess and per-stage gates
are unresolved. Do not assert Kendama/Chomper/etc. availability from their names
or adjacent catalogue rows. Early shop/NPC/treasure reward availability is likewise
unresolved; neither amounts nor IDs are approved for granting. Narrow next static
research: map Kaizo's reward table and its Hanzo/inventory gates at these known
sites, rather than scan/grant the wholeROM. The user only requires a verified
list, so uncertainty is preserved instead of filling it with guessed items.

## Remaining dependencies by category

| Category | Evidence and implication |
| --- | --- |
|A: sufficient for tested function|Initialized31 party plus existing3Gimmicks, routeFB, normal map/overworld navigation, unconsumedintro and user-filledcharge40 produced successful arrival/introduction/oneexchange. No conclusion that every one of these is individually necessary. |
|B: supported future requirements|Original claimed229/22A gates repeatLab2/3reward paths; if atomicgrants are used, leaving these clear permits later duplicate scene rewards. Decide/test narrowly scoped claimed bookkeeping after grants, not before. Return/Namp edges use25/26; laterLab4routes use28, currentlyclear. Do not enable later routes prematurely. |
|C: possible historical bookkeeping|227/228,257,271/272,ToyParts andvariable3C are absent yet did not prevent tested function. 271/272 are set before video-choice completion and cannot be called “video watched.” Their later readers can make them functional, so “optional bookkeeping” is provisional, not permission to discard/set them. |
|D: unresolved|Tutorialcompleted equivalence; stock/exhaustion/repeat exchange; Binky counter/save representation; optionalKaizo progression; laterquest dependencies; levels/equipment adequacy; physicalsave/reload; normalNamparrival and control. |

No newly identified absent flag is proved mandatory for the **already successful**
exchange. Preserve the successful branch as a control. Setting117/171/all earlier
bits would add untested changes, not repair demonstrated failure.

## Reproduction and checkpoint-completion plan

**Preferred foundation:** protected`before_oystown.ss0`, copied into a fresh
isolated mGBA0.10.5 branch with matching validatedROM, separatesave/state/cheat/
patch paths and`loadStateExtdata=9`. It already contains party31, three initialized
Gimmicks, routeFB and clear1F4. No repeat recruitment or route writes are needed.
Keep`after_exchange_oystown.ss0` as a separate successful-exchange control; never
clear its introflag to manufacture a pre-entry state.

Reproducing from the earlier cavecapture, if required, means reaching the
user-observed outdoorMayonen0048 normally, confirming liveB, ORing missingF0bits
in disposableRAM, normal overworld4→5→6→7 and capturing a newidlepre-entryfile.
The exact cave-to-outdoor traversal was not captured by Codex; use the later
foundation rather than pretend that segment is fully scripted. Do not replay001E.
Full persistentcharge40 is a separate finalpreparation step after source review;
existingpre-entrycharge05 is not full. No readybyte or tutorialflag edit is needed
for the already tested AWE/exchange behavior. This report performs no such write.

Incremental completion, each a fresh independently validated branch:

1. Validate that an unchanged disposablecopy of`before_oystown.ss0` reloads,
   exitsLab3exterior normally and again yieldsoriginalOystownintro. Preserve
   source; stop on mismatch/loaderror/missingparty/unexpectedintroconsumption.
   This validates the preservedartifact, not just an earlier live session.
2. Preflight a one-shot atomicgrant carrier for **Dojo Pup only** (`FE53 29`),
   using a validoriginal interpreter context and preservingreturn. Do not call
   FE49 or entireLab2/3scenes. No carrier is newly certified here, so construction
   must wait for its scopedpreflight and separateauthorization. Future validation:
   DeMillecount2→3, entryID29 withactualdifficulty/upgrade0, usage/equipment,
   menus/movement/battle, existinginventories unchanged. Stop on duplication,
   abnormalreturn, wrongowner orcorruption. Then test remaininggrants individually.
3. Only after grants pass, assess whether claimed229/22A should reflect delivered
   rewards to preventregrant. Keep routeFB; do not add boss/ToyPart/historyvalues
   without specificreader evidence. Test relevantreturn interactions separately.
4. Set onlycharge40 in a disposablefuturebranch, capture anewpre-entry artifact,
   and validate save/reload andordinarybattle/exchange on separatecopies. Capture
   immediately before/afterexchange for futuretransaction-level audit, not just
   endpoints across travel. A laternormal ingamesave/reload test must use fresh
   batterysavepaths; offlineEEPROM editing is not supported.
5. Investigate optionalKaizogates and stageequipment separately. If the broader
   target still demandsNamp0060, use normalarrival08130E34/callback081148EB in a
   separatevalidatedtransition experiment. Currentpreferredartifact is near
   Oystown atLab3exterior, not the finalNampcheckpoint.

**Recommended next minimal runtime experiment:** reload an unchanged disposable
pre-entrycopy and reproduce normalintro, with no edits. No runtime action is
requested in this read-only session. If a later debugging observation is needed,
start with one read only: `r/1 0x030032EB`, expectedFB, and review before further
actions. The next **construction** milestone is a separately preflighted single
DojoPup grant, not simultaneousfourgrants/history reconstruction.

## Integrity and files

86 current protectedROM/save/checkpoint hashes are identical before/after analysis;
all84 priorshortcut protectedhashes stillmatch. Japanese/English baselines and
validatedrecruitmentROM match establishedfingerprints. Userstates were never
rewritten, renamed, moved orloaded. The new savedcharge00 is a **read-only static
observation**, not an assistant RAMedit or userconsole measurement.

Independent verification repeated the tool and obtained identical JSON. Extended
metadata decompression checks passed. It checked all 86 current protected hashes,
all retained earlier hashes, both matching checkpoint identities, unchanged
DeMille records, Alessa's sole record difference at +58 (05→00), and the sole
96-byte main-bank difference at 03003325 (00→10). All passed. These comparisons
are endpoint evidence, not attribution of a complete exchange transaction.

Changed: appendedlatestfindings to`oystown_shortcut.md`,
`../oystown_binky_readiness.md`, `pre_oystown_state_construction.md`; createdthis
report, `oystown_completion_evidence.json` and`tools/analyze/oystown_completion.py`.
Priorfindings/evidence/manifests preserved. No acquisitionpatch or finalstate
constructed. Runtime success is established for the reportedshortcut/introduction/
oneexchange; completeness and long-termcompatibility remainunresolved.
