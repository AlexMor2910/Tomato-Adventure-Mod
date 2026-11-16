# Pre-Oystown experimental state construction

**Latest status:** a valid post-recruitment capture and user-created pre-entry/
post-exchange checkpoints now exist. The source-absence blocker below is
historical. Oystown access/introduction and one exchange are user-confirmed;
completion requirements and artifact details are appended below.

Date: 2026-10-13. Authorized controlled construction; no emulator operation.
**Result: reproducible capture package prepared; no post-recruitment source state
exists in the inspected workspace. No state transformation or ROM patch applied.**
The package is not a completed pre-Oystown checkpoint.

## Current authorization and evidence

The current user instruction supersedes the earlier progression report's
recommendation to replay natural progression. We will reuse the validated Hanzo
party and construct experimental progression incrementally. Natural Mayonen
recruitment, complete story playthrough and exhaustive cinematic reconstruction
are not prerequisites. Unknown effects remain documented risks.

Read-first sources: AGENTS.md, modding plan, all three session handoffs in
`session_handoffs/`, progression report/evidence, Oystown readiness, AWE report,
recruitment report/preflight/allocation, checkpoint inspector and preparation
documentation. Older statements that recruitment/AWE remain untested are
historical: latest user-confirmed runtime observations supersede them for the
tested scenario. Prior reports and evidence files remain unchanged.

**User-confirmed runtime:** membership31, Pop Horn count01/entry2B0100,
Erupter acquired, normal menus/movement/battle/Gimmicks/event return. Charge-only
40 at03001F94 enabled ordinary-battle AWE; post-battle05 included later charge
gain and does not measure an exact cost. Save/reload, tutorial completion and
full progression consistency remain **untested**.

## Source audit and concrete preparation

Tool: [pre_oystown_foundation.py](../../tools/analyze/pre_oystown_foundation.py).
Default prints a read-only audit; `--prepare` creates fresh unchanged input copies,
a capture guide and manifest. Reproduce from workspace root:

```powershell
python -B tools/analyze/pre_oystown_foundation.py --prepare
```

Each preparation uses a UUID output directory; `--output-name NAME` accepts only
a simple name and rejects an existing destination. The tool never invokes an
emulator, writes live memory, patches ROMs, rewrites PNG chunks or edits saves.
It checks all retained progression-evidence protected hashes, not just baselines.
If a membership31 candidate exists, preparation stops for context review instead
of automatically selecting it. Failed verification can leave a fresh incomplete
directory; never reuse it.

Output:
`reverse_engineering/experiments/testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/`

- `rom/alessa_recruitment_wrapper.gba`: byte-identical copy of validated ROM.
- `inputs/entry-stop.ss0`: byte-identical pre-recruitment checkpoint copy.
- `captures/`: empty destination for a new user-created post-recruitment state.
- [manifest.json](testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/manifest.json): complete source audit, both character-record snapshots for every unique checkpoint, before/after hashes, zero-byte changes, protected inventories.
- [CAPTURE.md](testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/CAPTURE.md): manual capture/isolation instructions.
- Empty saves/patches/cheats/screenshots/logs directories. No launcher or emulator
  executable was executed; these paths do not configure an existing emulator.

**Confirmed static:** 81 pre-existing protected ROM/save/checkpoint artifacts,
36 numbered state files containing nine unique PNG states. All nine successfully
passed PNG CRC/bounds,240x160 dimensions, single gbAs decompression to0x61000,
state magic01000007 and known ROM CRC/title/ID checks. All contain membership10,
Alessa inventory count0 and DeMille inventory count1. No membership31 source was
found. Duplicate paths are retained in the manifest. These checks identify saved
bytes; they do not certify a stable gameplay context or emulator load.

The `.sav` beside the validated recruitment ROM is8192 erased FF bytes, hash
`7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f`.
Other battery saves are classified only erased/non-erased; existing early-save
findings remain documented in Oystown readiness. Physical EEPROM record selection,
checksum and encoding are not sufficiently mapped for direct save transformation.
No battery save is promoted as a post-recruitment foundation.

| Copied input | Source and copy SHA-256 | Verification |
| --- | --- | --- |
| Validated recruitment ROM,16MiB | `3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6` | Full-file equality; modified bytes0 |
| Root entry-stop.ss0 | `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29` | Full-file equality; modified bytes0 |

No RAM fields changed. Manifest `state_changes` is empty. Input and output
checkpoint membership remain10; this is intentional preservation of the
pre-recruitment input, not implementation of StageA.

## Stages and next verified mechanisms

| Stage | Verified evidence / proposed mechanism | Applied result and remaining condition |
| --- | --- | --- |
| A: preserve party | Validated Hanzo wrapper on the fingerprinted ROM. Inspect membership03001AB4=31 and both records03001EDC/03001F3C, stride60; inventories count+7, entries+8 stride3. | Blocked: available snapshots predate recruitment. Export the already validated party; never inject31 into an uninitialized record or replayFE49 on a recruited party. Stats/HP/levels/equipment will be measured from that source, not invented. |
| B: four remaining core Gimmicks | Confirmed static IDs/owners below; normalFE53 acquisition08025624→0802927C→0806ADA0 includes usage0200EF08+2*(ID-1) and empty equipment-slot initialization. | Not applied. A separately reviewable atomic event carrier must use the new source's actual interpreter context, preserve return and avoid duplicate grants. No direct native calls or inventory-entry guessing. |
| C: full AWE | User-confirmed charge-only03001F94=40. Existing persistent ready03001F95 must be coherent00–03; ordinary battle derives lowbits03 at threshold40hex. | Not applied without valid source. After source review, narrow persistent-charge transformation is supported in principle; no battle-local/ready edit. Tutorial171 remains untouched. |
| D: progression throughLab3 | Confirmed static main bank030032E7+ID//8. Route23–27:030032EB masks08,10,20,40,80. Claimed229:0300332C mask02;22A:same byte mask04. Original setters08111E7C/E80,08112213/217; Ouch route2608116590. | Not applied. These are suitable individual experimental route/reward markers after acquisition validation, not proof of every original scene effect. Preserve adjacent bits; no bulk lower-numbered flags. ToyParts03001AB6 lowbits01/02 and Ouch257/byte3C need separate state review; do not silently synthesize unknown key-item/actor effects. |
| E: Namp placement | Node06 arrival08130E34:FE7C map0060,070880, callback081148EB; normal loader0802C1F0. | Not applied. MapID-only transformation would omit camera/actors/loader/context. Prefer a verified interpreter-driven original arrival in a separate atomic experiment, then capture after normal field control returns. Existing return005F afterOuch is not0060. |
| F: first Oystown pending | Intro guard1F4:03003325 mask10; script081084CA tests and sets at081086F0. Arrival08130E4E/setup08102491 also consult1C0. | Existing audited states have1F4 clear. Preserve it in new source; do not reset it after visiting. Other first-entry conditions remain unresolved. Original Binky scripts/commands/ROM bytes unchanged. |

### Verified seven-core inventory

| Gimmick | ID | Owner | Event evidence / normal direct grant encoding |
| --- | --- | --- | --- |
| Gear-Yo |01|DeMille|Present in early snapshots/user tests; preserve existing entry |
| Erupter |1B|DeMille|HanzoLab1 operand0810D698; preserve validated grant |
| Pop Horn |2B|Alessa|0812732C/validated wrapper; preserve validated grantFE536B |
| Dojo Pup |29|DeMille|Lab2 operand08111E45 packed29;FE5329 |
| Puffer |1F|Alessa|Lab2 operand08111E59 packed5F;FE535F |
| SneaKar |1D|DeMille|Lab3 operand081121DD packed1D;FE531D |
| RabiShoes |07|Alessa|Lab3 operand081121F1 packed47;FE5347 |

IDs/ownership/packed encoding are **confirmed static** in progression evidence.
The last four direct grants outside their original scene are **candidate**, not
runtime-validated. Difficulty is supplied by0300196E, not assumed01; expected
counts4/3 only if these are the only acquisitions and no duplicates exist.
Optional availability/equipment at the target is unresolved; no extra grants.

## Serialization limits and controlled continuation

Known read-only mGBA0.10.5 PNG layout: gbAs compressed serialized GBA state,
IWRAM `[0x19000,0x21000)`, EWRAM `[0x21000,0x61000)`, checked by existing
`tools/analyze/mgba/inspect_checkpoint.py`. This is sufficient for byte inspection,
not a tested state writer. No new serializer is implemented while the necessary
party source is absent. A later charge/flag writer must preserve every other
chunk/byte, correctly recompress and regenerate PNG CRC, independently reparse,
and compare complete decompressed state and all metadata. Save/reload is still a
manual validation milestone. Never change ROM identity fields to force loading.

Recommended construction remains an **experimental hybrid**, **candidate** overall:
use already validated recruitment; original atomic acquisition and normal arrival
logic for complex state; narrowly verified charge/route/claimed-marker changes
for simple persistent fields. This replaces the prior natural-playthrough
recommendation for this authorized branch. Story unknowns do not prohibit an
incremental usable experiment, but missing initialized source and unverified
transient placement do prohibit guessing their representations.

The recruitment ROM's16MiB expansion and redirect remain unchanged. No additional
payload or stacking was done. A future carrier must hash-gate that source, account
for the existing payload/reservation at08800000, and must not invokeFE49 again.

## Exact next user action and manual validation

**If the tested party is still available:** while idle in the field after the
reward/battle (outside dialogue and battle), use mGBA's save-state-to-file facility
to export one new state to:

`reverse_engineering/experiments/testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/captures/post-recruitment.ss0`

Do not overwrite an existing slot/file. This is the single requested emulator
action; no debugger command or RAM edit is requested. It captures existing
runtime evidence without revisiting Mayonen or progressing further.

If that party is no longer available, configure a fresh isolated portable
mGBA0.10.5 environment according to CAPTURE.md, open the package's ROM copy and
disposable entry-stop copy, finish only the already validated Hanzo reward, then
export the idle post-event field state. Copy/load only into the new environment;
keep the previous test environment unchanged. A CRC-only ROM-version warning is
expected for the pre-patch checkpoint; stop on actual load/title/ID/BIOS errors,
freeze, abnormal return, inventory/equipment or membership behavior. This fallback
is a short reproduction of the validated experiment, not a complete playthrough.

After capture: rerun the read-only audit; independently check party/record/inventory
and1F4 before choosing any writer/carrier. Validate each new milestone separately:
menus and correct grant ownership; next ordinary battle/AWE; route access;
normal Namp movement/exit; save/reload on disposable files. Only after each outcome
passes combine stages. Do not enter Oystown during preparation. Future debugger
observations will be requested individually, not as a batch.

## Integrity and closeout

All81 pre-existing protected files matched the retained progression evidence and
their new before/after hashes. Japanese baseline SHA-256
`0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12`;
English baseline
`8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`;
validated recruitment ROM/root checkpoint hashes above remain unchanged.
Only two new protected-format artifacts were added: unchanged ROM and checkpoint
copies. Manifest readback/full-file copy comparisons passed. No original file,
existing test environment, prior report, save or state was overwritten.
An independent verifier checked all81 old hashes, the exact83-path after-inventory,
both full-file copies and manifest, nine unique/36 total states, empty captures
and zero changes. Existing-destination refusal and three unsafe-name refusals
passed; every existing package file retained its hash after those rejection checks.

Changed source/documentation: new `tools/analyze/pre_oystown_foundation.py` and
this report. Generated package: manifest,CAPTURE.md, two unchanged input copies.
**Completed:** source search, exact-source protection, capture preparation,
verified-ID preparation plan. **Not completed:** post-recruitment foundation,
four grants, charge transformation, synthetic progression, Namp placement,
tutorial completion and first-entry end-to-end validation. Stop here: source
checkpoint absent; smallest next dependency is exporting the validated party.

## Foundation now available — validation and completion update

The user supplied the protectedpost-recruitmentcapture, then manuallyvalidated
route0B→CB→FB, normaloverworldtravel, Oystownintro andonefullAWE-for-oneBinky
transaction. **User-confirmed runtime**, noassistantemulatoroperation. The
fullstory-equivalence andoptionalinventoryrequirements remainunresolved.

Root `before_oystown.ss0` nowexists: SHA-256
`d20fc78972641d76e1b56f23daa80c9fedd4c07fa22edb63e69d37371db21c53`.
MatchingROMCRC E9ACB98F, map00DF/Lab3exterior, cachednode07, party31/count02,
routeFB,1F4clear, charge05, ready00, Gear-Yo/Erupter/PopHorn. It is thepreferred
completionfoundation, with no need torepeatrecruitment/unlockroutes. It is not
Namp0060 or a fullycompleteinventory. Use the normalexterior exit tonode7,
then left tonode8 fornormalentry; do notentertheLab3scene automatically.

Root `after_exchange_oystown.ss0` alsoexists: SHA-256
`aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646`.
MatchingROMCRC, map0104/node08, party31, unchangedthreeGimmicks, routeFB,
introflagset andsavedcharge00. Preserveit as thesuccessful-exchangecontrol,
neverresetintroflag to manufacturepreentry. Bothfilespassedread-onlyPNG/state/
ROMidentitychecks;newstaticreads aredistinctfromreportedconsoleobservations.

StageA: initializedpartyfoundation nowpresent. StageD: routeaccessshortcut now
runtimevalidated, nothistoricalstorycompletion. StageF: preentryguardclear in
source andoriginalintro successfullyobserved inbranch. StageB: missingDojoPup
(29,DeMille),Puffer(1F,Alessa),SneaKar(1D,DeMille),RabiShoes(07,Alessa).
StageC: userfullcharge/exchangeworks, butpreentrycapturecharge05stillneeds a
separatefuturecharge40step. StageE: finalNamp0060placementnotconstructed.
Tutorial/optionalcontent/stageequipment/save-reload remainunresolved.

Recommendednextminimalexperiment: unchangeddisposablepreentryreload andnormal
introreproduction; thenpreflightoneshotoriginalFE5329 grant forDojoPup before
testingothergrants. FulloriginalLab2/3scenes are notcertifiedfromthisshortcut
(ToyParts/rewardmarkersabsent). Noarbitraryinventoryinjection orreplayFE49.
See [exchange/completion report](oystown_binky_exchange.md) forrequirements,
originalacquisitionaddresses, optionalKaizogaps andincrementalstrategy.

Documentation/read-onlytooling only. All86 currentprotectedfiles unchanged,
includingthevalidatedROM andallnewuserstates. No newROM/checkpointconstructed,
noRAMwrite, nocopy/rename/relocation ofuserstates andnoemulatoroperation.
