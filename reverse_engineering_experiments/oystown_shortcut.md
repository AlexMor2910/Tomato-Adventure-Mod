# Controlled Oystown shortcut preparation

**Latest status (2026-10-13): user-confirmed runtime success.** The party reached
Oystown normally, its original introduction played, and one full-AWE Binky
exchange succeeded. The preparation blockers below are historical. See the
appended validation section and [completion report](oystown_binky_exchange.md).

2026-10-13. Read-only static inspection and documentation; no emulator operation,
RAM write, ROM generation or checkpoint modification.

**Result:** the captured DeMille–Alessa party is valid. Overworld route edits are
substantiated, but a safe route from this particular cave checkpoint to the
overworld remains unresolved. **No write is instructed at the current stop.**
This is an experimental shortcut, not a canonical story-state reconstruction.
Natural recruitment or complete story playthrough is not required.

## Sources and reproducibility

Reviewed AGENTS.md, all three handoffs in `session_handoffs/`, modding plan,
progression report/evidence, Oystown readiness, state-construction report,
recruitment report, Hanzo overworld/exit/interpreter mapping, checkpoint tooling.
Latest user-confirmed recruitment/AWE results supersede historical untested
claims for those tested scenarios. Previous artifacts/reports remain unchanged.

New bounded tool: [oystown_shortcut.py](../../tools/analyze/oystown_shortcut.py).
Run `python -B tools/analyze/oystown_shortcut.py`; it prints JSON only.
[Evidence](oystown_shortcut_evidence.json) records the exact capture, CPU/field
bytes, route instructions, eight selected map exit tables, Oystown commands and
84 protected-file hashes before/after. No broad script/code analysis was done.
Native/script addresses are unchanged original-ROM locations within the English
recruitment derivative; file offsets = bus minus08000000.

Evidence labels: **Confirmed static** means verified saved bytes/ROM operations;
**user-confirmed runtime** means prior supplied observations; **probable** denotes
supported interpretation; **candidate** denotes untested experimental procedure;
**unresolved/untested** denotes missing context/runtime evidence.

## Captured state

Source:
`testing/pre-oystown-foundation-47e2ab0d9c1b4772b524a4c482e99775/captures/post-recruitment.ss0`

SHA-256: `4eb81a006e852955556664f8c76c4526458048dab644dfa6f36a4b20d352946f`;
size50433 bytes. **Confirmed static:** PNG240x160, all chunk CRC/bounds and
gbAs decompression checks pass; serialized length61000, version01000007.
Extended metadata streams also pass bounded decompression/size checks; an8192-byte
embedded savedata block exists. Use `loadStateExtdata=9` to avoid importing it.

ROM CRC32 **E9ACB98F** and title/game code match the validated16MiB recruitment
ROM exactly, SHA-256
`3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6`.
This capture no longer has the pre-patch CRC mismatch. BIOS checksum59FE2303.
No state identity header was altered. Actual emulator load remains untested here.

| Field | Actual saved value | Classification / implication |
| --- | --- | --- |
| Current map03001936 |001F|Confirmed static; screenshot shows a rendered cave, not HanzoLab1/Namp/overworld |
| Descriptor03001938 |0862D748|Confirmed static; matches001F descriptor |
| Exit pointer0300193C |0813AE9C|Confirmed static; matches001F exits |
| Event table03001944 |08159C04|Confirmed static saved pointer |
| Arrival callback0300194C |08128AC5|Confirmed static retained pointer; not proof of active event |
| Cached overworld node030035F4 |04|Confirmed static; Mayonen node association confirmed source. This is not a live overworld selection while the party is in the cave. |
| Membership03001AB4 / derived count030035F0 |31 /02|Confirmed static; prior party/menu/battle functionality user-confirmed runtime |
| DeMille count03001EE3 |02|Entries03001EE4..E9:01 01 00 /1B 01 00; Gear-Yo/Erupter |
| Alessa count03001F43 |01|Entry03001F44..46:2B 01 00; PopHorn |
| Equipped slots03001F36..39 /03001F96..99 |01 1B 00 00 /2B 00 00 00|Confirmed static; consistent with owned core Gimmicks |
| Alessa charge03001F94 /ready03001F95 |05 /00|Confirmed static. Full charge is absent; this experiment preserves both bytes. |
| Tutorial171 |clear|Confirmed static; neither completion nor full charge will be synthesized |

Both full60-byte character records are retained in evidence. Inventory counts are
within20-slot bounds and records contain initialized names/stats/equipment rather
than empty data. This supports preserving the validated party; it does not newly
certify every stat, current HP, save/reload or target-stage balance.

### CPU and interpreter context

Saved rawr15=03005DB8, CPSR20000092, LR08092185. CPSR low mode12 is IRQ and
Thumb bit20 is clear: the snapshot is in an ARM interrupt context in IWRAM,
**not stopped at a native event-handler boundary**. Do not interpret this PC as
the main field-loop PC or inject a handler call/register/cursor change.
CPU register layout is verified against the pinned
[mGBA0.10.5 serialized-state definition](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h)
and [serialization implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/serialize.c).

Scheduling bitmap030039C1..C4 is00000000: none of the32 mapped interpreter
slots is enabled. Two inactive records retain old cursors0812D878/08100746;
nonzero stale pointers alone do not indicate an active event. The bitmap/record
interpretation is backed by registration0806AAA0 and scheduler08021EBA..21F14
in the Hanzo report. Transition gates03001904,03001908,03001909,0300190C and
camera-busy03001B4A are allzero. Screenshot contains no dialogue/menu overlay.

**Probable idle field scene**, supported by these independent bytes; stable input
control and CPU return to ordinary gameplay still require a user observation.
An IRQ snapshot is not itself corrupt or an active story event. No flag write is
proposed until a safe overworld control point is reached and observed. A single
snapshot cannot prove successful movement or future event scheduling.

## Necessary flags and exact conditional arithmetic

Main flag bank030032E7; byte = base+(flag>>3), mask=1<<(flag&7).
Accessor/storage mapping is established in Hanzo/progression evidence.

| Flag | Address /mask | Saved state | Route or preservation evidence |
| --- | --- | --- | --- |
|23|030032EB /08|set, byte0B|Lab1node3→Mayonennode4; already earned in Hanzo reward |
|24|030032EB /10|clear|Node4→5 up:08088E98 loads24, calls080889BC, returns5 only ifnonzero |
|25|030032EB /20|clear|Node5→6 up:08088EB0 loads25, same reader, returns6 only ifnonzero |
|26|030032EB /40|clear|Node6→7 left:08089134 loads26, returns7 at08089142 |
|27|030032EB /80|clear|Node7→8 left:0808914C loads27, returns8 at0808915A |
|28|030032EC /01|clear, byte00|LaterLab4 link; unnecessary for incoming node7→8, leaveunchanged |
|1F4|03003325 /10|clear, byte00|081084CA testsintroguard;081086F0 setsit. Preserveclear untilnormalintro executes. |
|1C0|0300331F /01|clear, byte00|Additional Oystown setup/default branch input; preserveexistingclear value, semantic meaning unresolved |

All four reviewed route bodies are byte-identical between the English baseline
and recruitment ROM. They read a single indicated flag, not party/inventory/
tutorial fields. **Confirmed static** edge checks do not guarantee camera,
selector graphics or arrival scripts are safe in an artificially advanced story.
For node6→7→8 alone maskC0 suffices. Starting from the captured node4 area,
the minimum known path also requires24 and25: **maskF0**, notC0.

**Conditional edit record, not a command to execute now:**

- Address030032EB; captured original0B; proposed0B OR F0 = **FB**.
- Exact changed bitsF0 correspond solely to24,25,26,27. Low nibble0B unchanged;
  unrelated flags20–23 preserved. Do not assignFB if a fresh live read differs.
- Purpose: unlocknode4→5→6→7→8 as an artificial route shortcut, without claiming
  original bosses/ToyParts/rewards occurred.
- Future action after safe overworld access and review of a fresh0B read:
  `w/1 0x030032EB 0xFB`.
- Subsequent verification action, requested separately: `r/1 0x030032EB`, expectFB.
- Stop if location/control is wrong, the live original differs, verification
  differs, introflag is alreadyset, a scene unexpectedly starts, or party/inventory
  changes. Never issue this write as a batch with reads or movement.

If any route bits are already naturally set by then, recompute `B | F0` from
the reported liveB and edit only missing bits; no write if already enabled.
No write to03003325,0300331F, inventories, AWE, actors, camera or node/map fields.

## Current-room exit and route strategy

The snapshot is already inside Mayonen Caverns. This is not a request to revisit
Mayonen or replay Alessa recruitment. **We cannot describe it as a Hanzo source
or teleport it by changing a cached node.**

001F's two ordinary exits, confirmed from descriptor0862D748+0C:

| Record | Rectangle x/y | Destination |
| --- | --- | --- |
|0813AE9C,04 09 05 09 1E 00 04 07 04 00|x4..5,y9|001E, original recruitment map |
|0813AEA6,13 05 13 08 20 00 02 01 06 80|x19,y5..8|0020, deeper cave |

The generic normal exit machinery08069994..69BF4 preserves full destination/
arrival context; high-bit special exit handling08069A2A..69A54 writes node then
calls0802C1A8. **No direct overworld exit is present in001F's table.**
The bounded adjacent exit graph is001F↔0020↔0021;0021 connects0022 and002A;
002A↔002B↔002E, with002E reaching0024 (tutorial map). None of those selected
tables supplies an overworld exit. This is not an exhaustive map/script graph:
actor interactions and scripted transitions can add paths.

001E has an empty ordinary exit table at0813AC28. Its script-based return and
scene guards are not equivalent to a simple normal doorway. Captureflags114set,
105/108/1FE/117clear. Original001E script081271E9 uses these guards; flag117
remainsclear despite successful wrapper recruitment. FE49 is not idempotent and
can initialize another companion if reached with Alessa present. Do not enter001E
or0024 blindly, set117 to bypass research, or follow deeper scenes as a shortcut.

**Narrow blocker:** a verified, non-recruiting exit from the current001F field
to idle overworldnode4. The user may already know a normal safe exit from their
tested session; if so, its observed map/event outcome is the needed evidence.
No direct handler invocation, scene replay, mapID-only/node-only edit or speculative
transition is proposed. A separate controlled original-transition experiment
would require its actual interpreter/exit context and further authorization if
normal exit cannot be established.

Once node4 overworld access is verified, the intended normal selection sequence is
**Up:4→5;Up:5→6;Left:6→7;Left:7→8**. Merely selectnodes5/6/7; do not press the
enter/confirm button at those nodes or visit their labs/Namp story scenes. At8,
confirm only after the route/read/guard checks have been reviewed. This uses the
normal selector and Oystown arrival; it does not enter Namp's internalmap0060.
The present goal is Oystown access, not the final Namp checkpoint.

## Oystown arrival and introduction preservation

Normal node8 selector case08088BC8 chooses arrival08130E4E:
FE7D map0104, arrival0107000182, setup08102491. NormalFE7D handler0802A134
uses loader0802C1F0; do not recreate its transient request by hand.
Setup/default also branch on1C0 and1F4; setupcalls081084CA at0810257F.
That intro skips when1F4 is set and writes1F4 at081086F0 after its body.
**Confirmed static:** clear1F4 preserves eligibility for that introductory block;
**unresolved:** complete first-entry/actor/quest compatibility in this shortcut,
and whether other guards cause an alternative setup path. Preserve both actual
clear guard inputs, no synthetic tutorial/claimed/boss flags.

Original Binky exchange scripts and NPC commands are unchanged. This test does
not certify exchange eligibility or availability. The capture's charge05 is not
full; exchange activation is deferred. Arrival's original introduction may mention
AWE/Binkies naturally; observing it is distinct from manually initiating exchange.

## User-operated staging — one debugger action at a time

1. Preserve the original capture and validated ROM/environment. Make a fresh
   disposable copy of the capture and a verified unchanged recruitmentROM copy
   in a new isolated mGBA0.10.5 environment. Set separate save/state/patch/cheat/
   screenshot paths, `loadStateExtdata=9`, `saveStateExtdata=9`, `rewindEnable=0`,
   `useBios=0`, `skipBios=1`. Confirm GUI paths before loading. Do not use baseline,
   music or balance ROMs. Expected ROM/capture hashes are above; stop on load,
   title/ID, CRC or BIOS discrepancy for this matching capture/ROM pair.
2. Load only the working copy and pause. **Only debugger action requested now:**
   `r/1 0x030032EB`. Expect0B. Report the exact result and whether the visible
   scene is the captured cave. This confirms the live starting byte; it does not
   authorize the conditional write yet. Stop on a different result.
3. After that observation is reviewed, validate one ordinary movement within the
   current room, without crossing exits/talking to actors. Stop on locked control
   or automatic scene. The next investigation will establish the safe exit;
   no speculative flag write resolves this field-context blocker.
4. At a verified idle node4 overworld control point, request a new route-byte read
   separately, then review it. Intro guard03003325 and secondaryguard0300331F
   are separate subsequent reads, each requested individually. Stop if1F4set;
   never clear a consumedintro to manufacture a first visit.
5. Only then issue a justified one-byte OR-preserving route edit from the actual
   live value, followed by a separately requested verification read. Route plan
   above is conditional preparation, not a ready batch of debugger commands.
6. Traverse the four selector edges, recording each node/title. Stop on blocked
   movement, unexpected entry/dialogue or abnormal selector. EnterOystown normally
   only after those prerequisites pass. Observe original intro completion, normal
   movement/menus and bothparty members with unchangedGimmicks. Do not activate
   Binky exchange. Save evidence under new names only.

Rollback by discarding the disposable branch; never reverse arbitrary flags
after scenes have run. A later first-entry test consumes1F4 on that branch, so keep
the source and pre-entry branch intact. No fullstory, optionalinventory, equipment,
charge or tutorial changes belong to this experiment.

## Integrity and closeout

**84 current protected ROM/save/checkpoint files** have identical before/after
SHA-256 inventories in new evidence; includes the new user capture and previous
unchanged preparation copies. Baselines and recruitmentROM match expected hashes.
Independent verification repeated the analysis and produced identical JSON,
checked all84 current hashes and prior protected hashes, confirmed the single
membership31 candidate and matching ROMCRC, and checked that0B→FB changes no
bits outsideF0. All passed; runtime writes0.
No runtime artifact was created or modified. New files only:
`tools/analyze/oystown_shortcut.py`, this report and `oystown_shortcut_evidence.json`.

Preparation stops before writes: minimum overworld bits are verified, but current
room→overworld context and stable input are not yet runtime-established. The
smallest immediate observation is the single read above; the narrow subsequent
dependency is a verified safe escape from001F that avoids original recruitment.
No claim is made that Oystown or its exchange has been reached or validated.

## Subsequent user-confirmed validation and preserved checkpoints

The user reported membership 31, Mayonen outdoor map 0048 and cached node 04.
They first added flags 26/27, changing the route byte 0B→CB, then flags 24/25,
CB→FB. Combined mask F0 preserved the lower nibble 0B. Normal Mayonen exit and
overworld travel through Hanzo Lab 3 to Oystown succeeded without reported errors.
This is **user-confirmed runtime route accessibility**, not completion of all
skipped story events. No original recruitment replay is required or proposed.

The user entered Oystown normally: its original introduction and Binky exchange
introduction played without visible errors/freezes. They filled persistent AWE
at 03001F94 to 40 and completed one exchange: one Binky added and gauge reset,
with no apparent errors. These are **user-confirmed runtime** observations;
the transcript did not measure a Binky counter, immediate final charge or flag writes.

Two newly inspected rootfiles now exist and match the recruitmentROM:

- `before_oystown.ss0`: SHA-256 `d20fc78972641d76e1b56f23daa80c9fedd4c07fa22edb63e69d37371db21c53`;
  map00DF (Lab3exterior), cachednode07, membership31, routeFB,1F4clear,charge05.
- `after_exchange_oystown.ss0`: SHA-256 `aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646`;
  map0104, cachednode08, membership31, routeFB,1F4set,charge00.

These are **confirmed static saved values**, distinct from user console reads.
Inventories retain Gear-Yo, Erupter and Pop Horn; four later core rewards are absent.
The only differing byte in the 96-byte main flag bank between these endpoints is
03003325: 00→10. This spans introduction, manual charge editing and exchange,
so do not attribute it solely to the transaction or call it a full state audit.

Prefer the protected pre-entry file as the completion foundation; no repeat Hanzo
wrapper or route unlock is needed. It is at Lab 3 exterior, not Namp 0060 or
overworld node 8. Keep the post-exchange file as a separate control; never clear
its intro flag to reconstruct pre-entry. Save/reload, repeat exchanges, optional
inventory, tutorial completion and later story compatibility remain untested.
See the linked completion report/evidence for missing rewards and the plan.

All 86 current protected artifacts remain unchanged, including all 84 previously
recorded paths. No ROM/RAM/state edit or emulator operation occurred. No further
debugger action is requested now.
