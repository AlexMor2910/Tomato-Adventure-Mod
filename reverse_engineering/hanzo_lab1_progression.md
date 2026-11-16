# Hanzo Lab 1 progression investigation

Date: 2026-10-11. Scope: source/ROM investigation and an authorized isolated RAM-only A/B experiment. Protected ROMs, saves and original checkpoints remain unchanged.

## Finding

The isolated overworld A/B test **confirms that setting only flag `0x21` unlocks leftward route selection from node 1 to node 3 (Hanzo Lab 1)**. The subsequent entry-only experiment confirms normal arrival on exterior map `0x002F`, exterior movement and the door transition selecting interior map `0x0030`. It stopped during interior initialization, immediately after the loader fetched Hanzo's default event pointer `0x0810D4C0` and before dispatching that script. **A fully initialized, controllable interior, the handoff and safe subsequent story progression remain unverified.** No reward/onward flag was manually set; the entry test needed no new RAM edits.

The first reward is **Erupter**, probable runtime Gimmick ID `0x1B`. Flag `0x20A` is a **Probable first-reward completion marker**: it redirects the Hanzo interaction to the post-reward message and is set at the end of the first-reward sequence. The decoded local selectors require `read8(0x030032C4) < 0x12` and flags `0x96`, `0x8D`, and `0x20A` all clear. These are conditions at the located selector, not a complete list of interaction prerequisites. Flag `0x23` is a separate onward-route unlock set by the reward sequence.

The latest route-only test used the naturally obtained root `map_pokypine.ss0`, avoiding the first-departure sequence that interrupted the earlier experiment. Both the earlier interruption and the new positive route evidence are retained below. No reward/onward flags were manually set.

## Manual registration confirmation and static interpreter trace

Evidence supplied by the user from **their manual mGBA 0.10.5 debugger session**. The assistant did not launch/control an emulator, inspect live RAM or execute this test. The user explicitly authorized this documentation update. Static follow-up used bounded read-only ROM inspection and the existing `tools/analyze/thumb_inspect.py`; only this report was edited.

### Confirmed manual runtime result

The user's initial stop was at displayed Thumb instruction `0x0803F946`, raw r15=`0x0803F948`, with r0=`0x0810D4C0`. They installed execution breakpoint #1 at `0x0806AB56` and continued. It hit before `str r0,[r1,#0]`, with:

| Observation | User measurement | Level |
| --- | --- | --- |
| Instruction at breakpoint | `0x0806AB56`, opcode `6008`, `str r0,[r1,#0]` | Confirmed (runtime), user transcript |
| r0 / r1 | `0x0810D4C0` / `0x03003C98` | Confirmed (runtime), user transcript |
| Destination before store | `r/4 0x03003C98` → `0x00000000` | Confirmed (runtime), user transcript |
| CPU before store | raw r15=`0x0806AB58`, CPSR=`0x0000003F`, cycle `13838175666` | Confirmed (runtime), user transcript |
| After one `next` | Displayed next instruction `0x0806AB58`; raw r15=`0x0806AB5A`, cycle `13838175671` | Confirmed (runtime), user transcript |
| Destination after store | `r/4 0x03003C98` → `0x0810D4C0` | Confirmed (runtime), user transcript |
| Reward-bank byte afterward | `r/1 0x03003328` → `0x58`; mask `0x04` for `0x20A` clear | Confirmed (runtime), user transcript |

This confirms **registration of Hanzo's event pointer**. The tested instruction only stores the pointer; it does not fetch or execute the event's command bytes. The transcript does not establish scheduling activation, event dispatch, full interior initialization, Erupter acquisition or subsequent story safety. No post-test measurement of `0x030032EB` was supplied, so its current runtime value is not newly confirmed here.

The console's displayed instruction and breakpoint address identify the execution location; raw r15 is +2 in these Thumb stops. Preserve that distinction when reading later debugger output.

### Registration records and scheduling, Confirmed (static)

All ROM addresses below are bus addresses; corresponding file offsets are `bus - 0x08000000`. The scoped registration, decoder, dispatch and first-handler windows were byte-compared between the protected Japanese and English ROMs and are identical. Input ROM SHA-256 values match the handoff. Routine names here are research descriptions, not recovered developer symbols.

| Structure / routine | Exact evidence and purpose |
| --- | --- |
| Context bank `0x03003AD4`, stride `0x1C` | Registration at `0x0806AB30..0x0806AB56` computes `(slot*8-slot)*4 = slot*28`, then adds the cursor offset +4. Scheduler loops over indices 0..31 (`0x08021F08..14`). Thus the indexed bank covers 32 records, derived extent `[0x03003AD4,0x03003E54)`. |
| Slot 16 | Record base `0x03003C94`; cursor +4 is `0x03003C98`, exactly the user-measured destination. Earlier probes restricted to task IDs `<16` omit this valid default-script slot and cannot prove absence of an active default event. |
| `0x08071C58` | Registration calls this at `0x0806AB2A`. At `0x08071C92..0x08071CA4` it derives the same record and zeroes exactly 28 bytes via `0x0802F950`. It also clears indexed scheduling bits. |
| Context +2 | `0x0806AB3A..3C` stores `0xFF` here before the cursor registration. Its full semantic label is Unconfirmed. |
| Context +4 | Persistent command cursor. Registration writes it at `0x0806AB56`; decoder reads it at `0x080223CA` and advances it at `0x080224D2`. |
| Context +0x14 / +0x18 | Conditional zero at `0x0806AB78` affects +0x14; countdown logic at `0x08022274..0x080222A2` uses +0x18. Do not infer the remaining record fields from the stride alone. |
| Registration routine `0x0806AAA0` | Saves requested slot from utility +1 into `0x030039D7` (+0x17) and `0x030039D5` (+0x15); preserves source `0x030018C8` on the shared scratch stack, resets the record, writes the cursor, then sets a scheduling bit. The observed request is slot `0x10`; the slot-`FF` alternative searches slots `0x10..0x1F`, not used in the supplied test. |
| Scheduling bitmap `0x030039C1..0x030039C4` | `0x0806AB7A..7E` passes base `0x030039C1` and slot index to bit-set helper `0x0806A540`, which calls `0x08069EF0`; byte OR/store is at `0x08069F14..1A`. For slot 16 this is byte `0x030039C3`, mask `0x01`. This later call had not been reached in the user's single-store test. |
| Scheduler loop `0x08021EBA..0x08021F14` | Stores selected slot index in `0x030039C0`; calls gating helper `0x08022680`, tests that slot's bit via `0x0806A4F8`, and calls the command interpreter at `0x08021EDE` → `0x08021F30`. Exact gating-helper semantics and runtime eligibility remain Unconfirmed. |

Scheduling bits are **not the persistent story bank** at `0x030032E7`. Pointer registration, enabling a scheduler slot and actually executing an opcode are separate steps.

### First-command fetch, decode and dispatch, Confirmed (static)

The Hanzo stream begins at ROM `0x0810D4C0` (file `0x0010D4C0`) with **`FD 0D 3D`**: FD-family opcode `0x0D`, argument `0x3D`.

| Native address / source | Operation |
| --- | --- |
| Interpreter `0x08021F30`; call `0x08021F32` | Calls decoder `0x08022388`, then chooses command family from decoded prefix at utility byte `0x030018BD`. |
| Decoder `0x08022388`; `0x080223BA..CA` | Reads current task byte `0x030039C0`, computes `0x03003AD4 + task*0x1C + 4`. At **`0x080223CA`**, `ldr r2,[r0,#0]` is about to read that cursor. For Hanzo slot 16, r0 should be `0x03003C98`. This is the earliest proposed observation boundary before fetching the first command's bytes. |
| `0x080223D8..0x080223E6` | Supplies the cursor as utility source, header destination `0x030039D9`, count 2; calls copy helper `0x0806A00C` to fetch the two header bytes. For an untouched Hanzo cursor those bytes are `FD 0D`. |
| `0x08022424..26`; `0x030039D8` | FD/FE path saves the second header byte as opcode `0x0D`; selects the family-specific argument-count table. FD table is `0x0862B815`; entry `+0x0D = 0x0862B822` contains **1**. |
| `0x0802247A..0x0802248E` | Copies argument bytes into shared parameter buffer beginning `0x030039D9` and sets parameter cursor `0x030039EC` (+0x2C of the control structure). For this command the copied byte is `0x3D`. Header and argument buffers reuse storage; they are not persistent script data. |
| `0x080224AA..0x080224D2` | Advances the context cursor past header and arguments. For the first FD0D command, the derived next cursor is `0x0810D4C3`, before native handler execution. This expected advancement is not yet measured by the user. |
| `0x08021F38..0x08021F52` | Decoded prefix `FD` selects FD dispatch routine `0x080247B4`. |
| FD dispatcher `0x080247B4`, table `0x0862BC30` | Opcode indexes a 32-bit native function pointer. Entry `0x0862BC64` (`base+4*0x0D`) contains `0x0802693D`, a Thumb-tagged pointer. |
| `0x080247C8` → trampoline `0x080F7ACC` | Calls the trampoline; its `bx r0` transfers to the selected handler. This is native command dispatch, distinct from registration. |
| First handler `0x0802693C` | FD0D implementation. Calls byte-argument reader `0x08022534`, which reads `0x030039EC`; then indexes persistent variable bank `0x03003287 + argument`. With argument `0x3D`, byte load at `0x08026958` reads `0x030032C4`; `0x08026960` writes the returned value to transient accumulator `0x03003A24`. None of this execution is newly confirmed by the registration transcript. |

An execution breakpoint at the script-data address `0x0810D4C0` is not the proposed mechanism. The CPU executes the native decoder/handlers, which read that address as data.

### Single next manual observation

From the current user stop at displayed instruction `0x0806AB58`, the safest next breakpoint is **`0x080223CA`**, before the native decoder reads the registered command cursor. It is a shared decoder boundary: its first hit might belong to another script slot. That possibility is intentional; stop and report it instead of continuing blindly toward Hanzo.

First command:

```text
break 0x080223CA
```

The supplied transcript still has old breakpoint #1 at `0x0806AB56`. After installing the new breakpoint, remove only that old point, then resume to the new point:

```text
delete 1
continue
```

At the hit, collect the displayed instruction/register status (normally printed automatically). Expected for Hanzo: instruction `ldr r2,[r0,#0]` at `0x080223CA`, r0=`0x03003C98`, r2=`0x10` (slot index still present before the load). If r0 matches, make just this memory read:

```text
r/4 0x03003C98
```

Expected: `0x0810D4C0`. **Do not execute `next` or another `continue` at this stop.** Send the breakpoint/status output and that word read. If the stop is at another slot, another breakpoint, an unexpected instruction, or dialogue appears, remain paused and send that observation instead. No gameplay input, flag manipulation or additional runtime operation is requested.

This next observation would establish that the scheduled decoder is about to consume Hanzo's registered cursor; it still would not establish command dispatch, full interior initialization or reward correctness. Those require separately staged observations after the user returns evidence. The assistant will not run mGBA or propose further execution before receiving that output.

## Entry-only experiment: normal exterior and door, stopped before default-script dispatch

Executed 2026-10-11 under separate authorization for normal arrival and the laboratory door, with an explicit stop before Hanzo's reward sequence. Newest evidence takes precedence over the older unverified-entry statements below. The experiment inherited the already validated `0x21` bit from a copy of the prior B stop state; **zero direct gameplay RAM writes occurred in this experiment**.

### Isolation and source

| Item | Location / fingerprint |
| --- | --- |
| Experiment directory | `reverse_engineering/experiments/testing/hanzo-entry-f87e9d336845426e985b93bdeb48fd00/` |
| Fresh emulator session | `reverse_engineering/mgba/run-7f871ba72efc/` |
| Protected source state | `reverse_engineering/mgba/run-376aeda5b619/states/route-selection-stop.ss0` |
| Source SHA-256 | `d1e79a2f9cc39c33e2fea2f5256d14e98987158d763a58067f34a9ebadb798e9` |
| Loaded working copy | New session `states/source-node3.ss0`, byte-identical to that protected source |
| ROM | Separate baseline English `rom/english.gba`, SHA-256 `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Backing save | Separate copy of prior B `saves/english.sav`, SHA-256 `7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f` |

Recorded hash/size/mtime fingerprints for **367 protected existing files**: ROM/save/checkpoint inputs plus prior experiment screenshots, logs, manifests and harness artifacts. Created new archival copies of the critical ROMs/root checkpoints/source state. Copied mGBA Qt 0.10.5 into a fresh portable session with independent ROM, save, state, screenshot, log, patch, cheat and configuration paths. Configuration `loadStateExtdata=9` and explicit `emu:loadStateFile(workingCopy,9)` excluded embedded savedata. No original or prior experimental file was used as an output target.

After pausing and reloading the working copy, confirmed the live selected-node stack cell `0x03007BB4=3`, screen title “Hanzo Lab 1,” frame 49081, inherited route byte `0x030032EB=0x03`, reward-bank byte `0x03003328=0x58`, and persistent byte `0x030032C4=0`. Cached entry node `0x030035F4=1` and retained field map `0x03001936=0x0008` were the expected unchanged pre-confirmation context, not contradictory destination values.

### Arrival on exterior map `0x002F`

Sent one normal A-button confirmation on node 3. Used instruction stepping to observe arrival, releasing the key during the normal overworld exit. No script cursor, coordinate, party, inventory, register or additional flag was edited.

| Address / observation | Evidence | Level |
| --- | --- | --- |
| `0x08088B78` / file `0x00088B78` | Raw scripting PC `0x08088B7A` reached node-3 arrival case. | Confirmed runtime |
| `0x08088C3C` / file `0x00088C3C` | Raw PC `0x08088C3E`, r0=`0x08130E09`, r1=`0x030018BC`, before the arrival script pointer store. | Confirmed runtime arrival source |
| `0x08130E09` / file `0x00130E09` | Previously decoded FE7D arrival script encodes map `0x002F`; resulting live map changed to `0x002F` at raw PC `0x0802A140`, after native map store `0x0802A13C`. | Confirmed static bytes plus runtime destination |
| `0x03001938` | After loading: descriptor `0x0862D908`. | Confirmed runtime |
| `0x0300193C` | Exit table `0x0813AFE8`. | Confirmed runtime |
| `0x03001944` | Event table `0x08159D14`; its first word is default source `0x08111CB2`. | Confirmed runtime table pointer; source pointer Confirmed ROM bytes |

The first map-ID observation occurred before the descriptor/graphics switched, so its old descriptor values were not mistaken for completed loading. Waited through the normal fade with neutral input and conservative script/flag guards. Screenshot `exterior-fade-complete.png` shows the translated **“Hanzo Lab 1”** title, sign-bearing laboratory building, surrounding terrain, exterior actors and DeMille. No Hanzo speech or other automatic dialogue was observed. The title plaque and fade are normal arrival presentation, not the reward sequence.

Normal movement was confirmed: right input changed DeMille's actor X from 79 to 99 at unchanged Y=143. Then continued right and up through ordinary controls to pixel `(151,119)`, directly below the documented door rectangle `(9,6)`. Exterior flag-bank bytes stayed unchanged. The game's exterior initialization naturally changed persistent label byte `0x03003287` from `0x01` to `0x0A`, matching `FD4D 00 0A` in `0x08111CB2`; persistent byte `0x030032C4` stayed zero. This was an original script write, not an experiment edit.

The early exterior wait harness looked for mode byte `0x03001902=2` before declaring readiness. That assumption did not hold: the field exterior was visibly rendered and movable while the byte remained 1. Its bounded instruction budget ended with no error/stop, after which neutral observation and the actual movement test established readiness. The generic controller mode byte must not be used alone to classify field versus overworld or infer a softlock. No temporary gates were cleared to compensate.

### Normal laboratory door transition

Continued up using ordinary input, then released it as soon as the destination map halfword changed. The documented exit record was selected automatically:

| Address / observation | Evidence | Level |
| --- | --- | --- |
| `0x03001AD8` | Selected exit-record pointer `0x0813AFE8`, the exterior door record with destination `0x0030`. | Confirmed runtime |
| `0x08069AAC` / file `0x00069AAC` | Raw PC `0x08069AAE`, r0=`0x00000030`, before the normal transition's map halfword store. | Confirmed runtime destination store input |
| `0x03001936` | Became `0x0030` at raw PC `0x08069AB0`, frame 49236. | Confirmed runtime door transition |
| `0x03001938`, after further loading | Interior descriptor `0x0862D924`. | Confirmed runtime |
| `0x0300193C`, after further loading | Interior exit table `0x0813B000`. | Confirmed runtime |
| `0x03001944`, after further loading | Interior event table `0x08159D1C`. | Confirmed runtime |

The doorway triggered when the actor fields read Y=112, X=151; these pixel fields are not a direct substitute for the transition detector's grid-coordinate convention. The exact record pointer, destination register and stored map ID establish which doorway was used without inventing a coordinate formula.

### Conservative stop before Hanzo script execution

While allowing only interior loading to continue, a read-only guard detected source `0x0810D4C0` in utility word **`0x030018C8`** and halted **before the next CPU instruction**. This occurred at frame **49265**, raw PC **`0x0803F948`**, corresponding to next Thumb instruction **`0x0803F946`**. r0 was `0x0810D4C0`, r1 was `0x030018BC`. No more emulation instructions, frames or gameplay inputs ran after this detection; only read-only capture and serialization to a new disposable stop state followed.

Read-only disassembly after stopping explains that boundary:

```text
0803F93E  load address 0x03001944
0803F940  load event-table pointer
0803F942  load first word of event table
0803F944  store that word to utility source +0x0C (0x030018C8)
0803F946  add r5,r1,0              ; next instruction at the stop
0803F948  mov r0,0x10
0803F94A  strb r0,[r5,1]
0803F94C  bl 0x0806AAA0           ; subsequent script-start/registration helper, not executed
```

Thus the loader **automatically fetched Hanzo's default source**, but this test did **not** observe the initial reward path executing or speech opening. Active event cursor from the previously used context probe was still zero. Whether the default script merely initializes actors/waits for interaction or proceeds automatically into the first handoff remains **Unconfirmed**. Stopping at source preparation was deliberately more conservative than waiting for dialogue or acquisition.

At the stop the screen was black during the normal fade, and player actor fields were zero during initialization. **Fully rendered interior graphics and free interior movement were not observed.** This is a paused loading boundary, not evidence of a softlock or missing actor bug. No neutral frames were run to finish the fade because that would advance toward the untested default script.

**Event-table layout correction:** the default source is the **first word at the table base**, not base+4. Exterior base `0x08159D14` contains `0x08111CB2`; interior base `0x08159D1C` contains `0x0810D4C0`. A diagnostic read at `0x08159D20` returned `0x000000FF`, because that is subsequent trigger/terminator data, not the default pointer. The corrected read and native first-word load above are retained in the logs. Earlier references to adjacent `FF` bytes must not be interpreted as a four-byte prefix to the default source.

### Final state, artifacts and preservation

| Field | Start | Stop |
| --- | --- | --- |
| Map ID | Retained `0x0008`, selected overworld node 3 | `0x0030`, interior descriptor installed |
| Route byte `0x030032EB` | `0x03` | `0x03` |
| Flag `0x21` | Set | Set |
| Flag `0x23` | Clear | Clear |
| Reward-bank byte `0x03003328` | `0x58` | `0x58` |
| Flag `0x20A` | Clear | Clear |
| Persistent byte `0x030032C4` | `0x00` | `0x00` |
| Owned Gimmicks | One `[01,01,00]` Gear-Yo entry | Same; no Erupter |

All **96 flag-bank bytes** match the source checkpoint exactly. The only persistent variable-bank difference is the original exterior label write `0x03003287: 01→0A`. No first-reward opcode was intentionally advanced, no interaction input was sent in either field map, and no in-game saving or subsequent progression occurred.

Artifacts are in the new session's `logs/` and `screenshots/`, including `node3-before-confirm.png`, `exterior-fade-complete.png`, `exterior-movement.png`, `door-approach.png`, `door-map-transition.png`, `interior-load-watch.png` and `entry-stop.png`. Logs `02-arrival-console.txt`, `07-door-console.txt`, `09-interior-console.txt` and `10-stop-console.txt` contain the execution/map/source observations and complete command history. The experiment manifest, runtime results and preservation verification are separate from previous runs.

Disposable stop state: `states/entry-stop.ss0`, SHA-256 **`d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29`**. It is stopped during interior loading, before default-script dispatch; do not describe it as an idle laboratory checkpoint or resume it casually for a reward test.

Closed the sole experiment emulator. All **367 protected-file hash/size/mtime checks passed**, including prior captures, root states, protected ROMs, original saves and previous experimental states. The working English ROM, imported B state, copied backing save and emulator binaries also retained their starting hashes. No ROM patch, save editor, extra RAM edit or gameplay-code change was introduced.

**Conclusion:** normal node-3 arrival on `0x002F`, normal exterior movement and the door transition installing map `0x0030` are **Confirmed (runtime)** for the inherited one-bit route unlock. Finishing interior initialization without an automatic handoff remains **Unconfirmed**, because the loader prepares the Hanzo default script and execution was stopped before dispatch. Reward acquisition and story-safety experiments require separate authorization; no such experiment was performed.

## Route-only A/B result from the natural overworld checkpoint

Executed 2026-10-11 under explicit authorization to test one left input in each isolated session and edit only flag `0x21` in B. The scope ended at overworld route selection: **no confirmation/A-button input, lab entry, Hanzo interaction, reward acquisition, in-game save or later-story test occurred**.

### Inputs, isolation and evidence artifacts

| Item | Location / fingerprint |
| --- | --- |
| Experiment directory | `reverse_engineering/experiments/testing/hanzo-route21-e403d5880f814caea273f8288f30a649/` |
| Control A | `reverse_engineering/mgba/run-3da22fc56cdb/` |
| Experimental B | `reverse_engineering/mgba/run-376aeda5b619/` |
| Source checkpoint | Root `map_pokypine.ss0`, **51,501 bytes**, SHA-256 `1079f53c58187342856f405d9c18bc7d96cfc9ea7ba9c224569d7914d9841eb2` |
| Other protected root checkpoint | `pokypine_forest.ss0`, **39,424 bytes**, SHA-256 `2a2603842095aa3c4fe0f8a09381f897128afafdf36db7daa89e59da3250c886` |
| ROM in both sessions | Independent `rom/english.gba` copies; baseline English SHA-256 `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Backing savedata | Independent `saves/english.sav` copies of root `Tomato Adventure (Japan) (patched).sav`, 8,192 bytes, SHA-256 `7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f` |

Before preparation, recorded hashes, sizes and modification timestamps for **45 existing ROM/save/checkpoint files**, including earlier experiments and both root states. Created new archival copies of both protected ROMs, both root checkpoints and the backing save. Each A/B directory has its own copied mGBA Qt 0.10.5 executable, portable config, ROM, checkpoint, savedata, logs, screenshots, states, and empty patch/cheat lookup directories. All experiment assets remain local and ignored.

State-loading configuration was `loadStateExtdata=9`. After pausing each GUI, the scripting console explicitly loaded its own checkpoint copy with `emu:loadStateFile(path,9)`, excluding embedded savedata. Ran 60 neutral-input frames in each session and verified identical flag banks, retained field map and overworld mode. Both were at **frame 49030**, displaying “Pokypine Wood,” with cursor position `(162,147)` and node-entry byte 1. No source asset was opened for writes or used as emulator output.

Exact Lua commands and full console histories are retained in session `logs/`; screenshots are in `screenshots/`. The experiment directory contains `manifest.json`, `runtime-results.json`, `post-experiment-verification.json`, archival copies and a copied UI console runner. This test used the working Qt scripting interface; no GDB connection, software breakpoint, ROM patch or register edit was used.

### Runtime initial state and one-bit verification

The following values are **Confirmed (runtime)** in both sessions before directional input:

| Field | Initial A/B | Final A | Final B |
| --- | --- | --- | --- |
| Route byte `0x030032EB` | `0x01` | `0x01` | **`0x03`** |
| Flag `0x20`, mask `0x01` | Set | Set | Set |
| Flag `0x21`, mask `0x02` | Clear | Clear | **Set** |
| Flag `0x22`, mask `0x04` | Clear | Clear | Clear |
| Flag `0x23`, mask `0x08` | Clear | Clear | Clear |
| Flag-bank byte `0x03003328` | `0x58` | `0x58` | `0x58` |
| Flag `0x20C`, mask `0x10` there | Set | Set | Set |
| Flag `0x20A`, mask `0x04` there | Clear | Clear | Clear |
| Persistent byte `0x030032C4` | `0x00` | `0x00` | `0x00` |
| Retained field map `0x03001936` | `0x0008` | `0x0008` | `0x0008` |
| Mode byte `0x03001902` | `0x01` | `0x01` | `0x01` |
| Character-0 owned Gimmicks | One entry `[01,01,00]` (Gear-Yo) | Same | Same |

B's `logs/02-bit.lua` asserted route byte `0x01`, flag-bank byte `0x58`, and persistent byte zero while paused at frame 49030. Its **sole direct gameplay RAM write** was `emu:write8(0x030032EB, old+0x02)`. Given the asserted old value, this is exactly `old | 0x02`. It read all 32 KiB of IWRAM immediately before/after, without advancing a frame: only byte `0x030032EB` changed. The other **32,767 IWRAM bytes**, including the other **95 flag-bank bytes**, were identical. The changed byte's XOR was exactly `0x02`, preserving all seven neighboring bits.

Final A/B snapshots likewise differ in the flag bank only at `0x030032EB`, XOR `0x02`. Their full 96-byte persistent variable banks are identical. Neither the reward-claimed flag nor the onward-route flag changed naturally or manually during this limited test.

### Route decision and execution evidence

Each session received one left-key press/release episode through normal GBA input mask `0x20`, with no other directional or confirmation input. Instruction stepping was used solely to observe execution. In these Thumb traces, the scripting API's raw PC register was **two bytes ahead of the instruction about to execute**. Raw PC values are retained alongside the corresponding instruction addresses; they must not be reported as debugger execution-breakpoint PCs without accounting for this offset.

| Instruction address (ROM file offset) | Observation | Level |
| --- | --- | --- |
| `0x08088DDE` (`0x00088DDE`) | Left-input dispatch leads to `0x08089088`; traces in both sessions pass this path. | Confirmed runtime dispatch path |
| `0x08089100` (`0x00089100`) | B raw PC `0x08089102` observes node-1 case before `mov r0,#0x21`; by raw PC `0x08089120`, r0 is `0x21`. | Confirmed runtime flag selector |
| `0x080889F0` (`0x000889F0`) | B raw PC `0x080889F2`: r0=`0x21`, utility word `0x030018C0=0x21`, immediately before call to main flag reader. | Confirmed runtime flag ID |
| `0x0806AE2C` (`0x0006AE2C`) | B raw PC `0x0806AE2E`: main reader invoked with ID `0x21`. | Confirmed runtime call |
| `0x08069F7A` (`0x00069F7A`) | B raw PC `0x08069F7C`: selected mask/result r4=`0x02`, source byte in r0=`0x03`, before storing the result into utility byte +1. | Confirmed runtime packed-bit result |
| `0x08089128` (`0x00089128`) | A raw PC `0x0808912A`: r0=0, utility result=0, CPSR=`0x6000003F` (Z set); clear-flag branch is taken. B at the same raw PC: r0=2, utility result=2, CPSR=`0x2000003F` (Z clear); branch is not taken. | Confirmed runtime A/B branch distinction |
| `0x08089194` (`0x00089194`) | A next raw PC `0x08089196` follows the unchanged-node path. | Confirmed runtime denied-route path |
| `0x0808912A` (`0x0008912A`) | B raw PC `0x0808912C` reaches `mov r0,#3`; at raw PC `0x08089198`, r0 is 3. | Confirmed runtime destination result |
| `0x08088DEC` (`0x00088DEC`) | A raw PC `0x08088DEE` returns r0=1; B returns r0=3. | Confirmed runtime caller handoff |

Utility word +4 is restored by the flag wrapper after the read; later trace lines show `0x268` there. That restored value is not the flag ID used by the completed query. The B trace above captures ID `0x21` before the call and the result afterward.

**Control A:** the zero flag result returned node 1. Final live selected node was 1 and screenshot title remained “Pokypine Wood.” No dialogue, cutscene, field-map transition or actor anomaly was observed.

**Experimental B:** the flag result was `0x02`, and the route routine returned 3. With keys released, allowed the normal overworld movement animation to finish. After 45 neutral frames the selected-node cell became 3; observed another six neutral frames with guards on map/mode, node and flags. Final screenshot title was **“Hanzo Lab 1”**, cursor `(120,135)`, selected node 3. No destination confirmation was sent, so the game stayed on the overworld. Maps `0x002F` and `0x0030` were not loaded.

### Important node-storage correction

The **live selected overworld node** in these two invocation frames was a 32-bit stack cell at **`0x03007BB4`**, observed through the route routine's r4 pointer and its caller. This is a session-specific stack address, not a new universal persistent field. It was 1 initially, remained 1 in A, and became 3 in B after animation.

Byte **`0x030035F4` remained 1 in both sessions**, including B's node-3 screenshot. Prior code analysis shows it seeds the selection on entering the overworld and receives the committed selection when that screen exits; it is not continuously synchronized with cursor selection. Thus the earlier root-state inspection correctly identified initial node 1, but reading this byte alone cannot establish the current cursor node after movement. Retained field map `0x0008` also stayed unchanged during overworld selection and must not be labeled a lab map visit.

### Diagnostic limitation and stop discipline

A's first observer compared raw PC directly against instruction addresses, so its stop predicate missed the node-1 entry due to the Thumb +2 PC offset. It reached its bounded 350,000-step limit and printed **“Route decision not observed within step budget; stop”**, despite having captured the zero-result branch and return to node 1. This was an observation-harness error, **not an emulation softlock or unexpected game event**. Its left input was released before that assertion, after approximately five frames. No second directional input was sent to A. A read-only capture then confirmed node 1 and the unchanged screen/flags. The original diagnostic transcript is retained.

B's observer used the corrected raw-PC offset and stopped at the first captured return to the route caller (step 57,717), then released left before advancing the neutral animation frames. Both therefore used one press/release episode; the press durations were not frame-identical. The decisive branch/result was observed directly, and initialization was matched at frame 49030. No additional RAM edits were used to compensate for the A observer error.

No unexpected gameplay state occurred. Both sessions were stopped at the route-selection scope, captured into **new disposable** `states/route-selection-stop.ss0` files, and closed. There was no in-game saving, Hanzo event, Erupter acquisition or story-continuity test.

### Artifacts, verification and conclusion

Useful captures: A `screenshots/control-after-left.png` and `screenshots/final-route-stop.png`; B `screenshots/after-one-bit.png`, `screenshots/left-decision.png`, `screenshots/selected-node3-stop.png`, and `screenshots/final-route-stop.png`. Live flags and instruction traces are in A `logs/02-left-console.txt`/`05-final-console.txt` and B `logs/02-bit-console.txt`/`03-left-console.txt`/`04-selection-console.txt`/`05-final-console.txt`. Launch arguments and process logs are separate per session.

| New stop artifact | SHA-256 |
| --- | --- |
| A `states/route-selection-stop.ss0` | `4cd1b66dab75cb8d6bfa84c867427def623749d2b3683d8d142af804b1535bd3` |
| B `states/route-selection-stop.ss0` | `d1e79a2f9cc39c33e2fea2f5256d14e98987158d763a58067f34a9ebadb798e9` |

After closing both emulators, all **45 protected-file hash/size/mtime checks passed**. Both root checkpoints, protected Japanese/English ROMs and all enumerated existing saves/checkpoints remain unchanged. Each isolated English ROM, imported checkpoint and backing save also retains its starting hash. The session's copied emulator binaries passed the existing verifier. No persistent patch or patcher was created; only isolated experiment artifacts and this report were added/updated.

**Confirmed (runtime): flag `0x21` alone enables node 1 → node 3 route selection in the tested baseline English ROM and natural overworld checkpoint.** Entry into Hanzo's maps, reward grant correctness, omitted kidnapping/briefing dependencies and later story safety remain **Unconfirmed**. The successful route test must not be generalized into a validated story skip.

## Authorized A/B runtime experiment: stopped before overworld comparison

Executed 2026-10-11 under the user's explicit authorization to prepare isolated sessions and change only bit `0x02` of `0x030032EB` in B. This section supersedes the earlier “no experiment executed” status. The user's instruction to stop on unexpected event state took precedence over completing the route/Hanzo stages.

### Preparation and controls

| Artifact | Location / validation |
| --- | --- |
| Experiment manifest and protected backups | `reverse_engineering/experiments/testing/hanzo-flag21-a0ba005c0e5840eaa7c975120a5ef444/` |
| Control A | `reverse_engineering/mgba/run-3160380dd05b/` |
| Experimental B | `reverse_engineering/mgba/run-45d355b68953/` |
| ROM in each session | `rom/english.gba`; unchanged English SHA-256 `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Source checkpoint actually loaded | Separate byte-identical copies of `gimmick_menu.ss0`, SHA-256 `570e17c82b6d3592a0b003d991a33b6bf320c04ff7322a339e735f6c65280230` |
| Other checkpoint copied, not loaded | `gimmick_battle.ss0`, SHA-256 `cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7` |
| Backing savedata | Separate copies of original `saves/english.sav`, SHA-256 `37f0efba33abc9f4b622166b3f2b124ef2144e99e510bfd39e346050982a6874` |
| Emulator | Copied mGBA Qt 0.10.5 executables, portable configuration, separate save/state/screenshot/patch/cheat directories; `loadStateExtdata=9` excludes embedded savedata. |

Each session loaded only its own ROM/checkpoint/save copies. Archival copies of both protected ROMs, both source checkpoints and the source backing save were created under the experiment's `protected_backups/`. No original was selected in the emulator. All artifacts containing ROMs, saves, screenshots and states remain in ignored local directories.

GDB launch in A briefly accepted a TCP connection, but subsequent interrupt/status requests did not produce a usable response; the reconnect was refused. No memory-write packet was sent. Instead, the working Qt **Scripting** console was accessed through Windows UI Automation. Live observations and button input used documented `emu:read8/read16/readRange`, `setKeys`, `runFrame` and `screenshot` methods; see the [official mGBA scripting reference](https://mgba.io/docs/scripting.html). Its published reference describes 0.10.2, so successful execution in the installed 0.10.5—not API availability alone—is the runtime evidence here.

Both emulators were paused before controlled scripted input. Lua input helpers pressed ordinary GBA buttons for bounded frame counts and released them between presses. They did not write coordinates, script cursors, registers, inventory or story variables. A and B started from identical checkpoint bytes but had different accumulated menu frame counts before pausing; NPC timing required a small additional normal movement correction in B. This was not a frame-identical whole-RAM comparison. The one-bit write comparison itself advanced **zero frames**.

### Verified bit change and relevant flags

**Confirmed (runtime):** both initial live sessions matched the checkpoint's route/reward prerequisites:

| Field | Initial live A | Initial live B | B immediately after the write | At final stop: A / B |
| --- | --- | --- | --- | --- |
| `0x030032EB` | `0x01` | `0x01` | `0x03` | `0x01` / `0x03` |
| Flag `0x20`, mask `0x01` | Set | Set | Set | Set / set |
| Flag `0x21`, mask `0x02` | Clear | Clear | **Set** | Clear / set |
| Flag `0x22`, mask `0x04` | Clear | Clear | Clear | Clear / clear |
| Flag `0x23`, mask `0x08` | Clear | Clear | **Clear** | Clear / clear |
| `0x03003328` | `0x48` | `0x48` | `0x48` | `0x58` / `0x58` |
| Flag `0x209`, mask `0x02` there | Clear | Clear | Clear | Clear / clear |
| Flag `0x20A`, mask `0x04` there | Clear | Clear | **Clear** | Clear / clear |
| `0x030032C4` | `0x00` | `0x00` | `0x00` | `0x00` / `0x00` |

B's only direct gameplay RAM write occurred in `logs/02-field-and-bit.lua` at emulator frame **33458**. The script asserted old byte `0x01`, reward byte `0x48` and persistent variable `0x00`, then called `emu:write8(0x030032EB, old + 0x02)`. With the asserted old value this is exactly `old | 0x02`. Immediate readback was `0x03`. It compared all 96 flag-bank bytes before/after: byte index 4 changed by exactly `0x02`, and the other 95 bytes were identical. No frames ran between those reads and the write. The transcript explicitly records `flag21=1 flag23=0 flag20A=0`.

At the final stopped state, A and B's **entire 96-byte flag banks still differ only by flag `0x21`**. The shared `0x48→0x58` change is the game's own setting of flag `0x20C` during the guard/departure script, not an edit by the experiment. Neither `0x23` nor `0x20A` was ever manually set.

### Gameplay observations and stop condition

1. Exited the Gear-Yo menu normally. Captured live menu and field screenshots; both retained only Gear-Yo. Walked through maps `0x0001 → 0x0002 → 0x0003` using ordinary movement and transitions. These map IDs are now **Confirmed (runtime)** for this path. Some capture filenames contain an intended destination (such as `map3-idle` or `overworld-arrival`); actual logged map IDs and screenshots determine the observation, not the filename.
2. Approaching the north village gate triggered the same scene in both sessions. Captured Pasaran's “The gate's still closed,” DeMille's “Well, looks like we're not going anywhere,” and the guard refusing departure. Source messages `564..56E` identify the scene. The guard demands a fight. **Setting `0x21` does not bypass this earlier gate event.**
3. Fought Watchman Kid normally in both isolated sessions. Two successful Gear-Yo actions defeated him; the first action changed the established target HP halfword `0x03000A4E` from 24 to 8 in both sessions. Victory screen showed 1 XP, 12 Pacifiers and 5 Binkies. There were no battle-stat edits. A diagnostic line labeled a read at `0x03000946` “demilleHP=0”; that address/label was not validated and must not be treated as DeMille HP evidence. The visible UI showed DeMille alive, and the experiment continued normally.
4. Advanced the ordinary victory/guard dialogue (`56F..571`). The post-battle input batch captured each dialogue step. At step 9, both sessions automatically changed current map from `0x0003` to **`0x005C`** and flag byte `0x03003328` from `0x48` to `0x58`. Step 10 had already been included in that bounded batch when the new map was inspected; there were no further button inputs afterward. Screenshots show a grassy field with DeMille, Pasaran and another actor, rather than the planned overworld selector. This was an **unexpected state relative to the experiment protocol**, shared by A and B, not evidence that B was corrupted.
5. Stopped both sessions, performed read-only final captures, and wrote **new** disposable `states/experiment-stop.ss0` files. Then closed both experiment emulators. No teleport, extra flag, persistent variable change or inventory injection was attempted. No in-game save was made.

**Not observed:** overworld node 1's denied/allowed route comparison, maps `0x002F/0x0030`, Hanzo dialogue, Erupter acquisition, handoff completion flags, repeat-interaction behavior, Mayonen access or later-story consistency. These remain Unconfirmed (runtime), despite the prior static route mapping.

At the stop, both character-0 records have Gimmick count 1 and entry `[01,01,00]` (Gear-Yo ID 1, selector 1, additive byte 0); there is no owned ID `0x1B` entry. Final `0x8D`, `0x96`, `0x209`, `0x20A` and `0x23` are clear; `0x030032C4` remains zero. All observed changes to experience, HP/level, rewards or item counts resulted from the same normal guard battle and script in A/B.

### Newly exposed first-departure dependency

After stopping emulator execution, read-only ROM inspection explains the shared transfer:

| Location (bus / file offset) | Evidence | Level |
| --- | --- | --- |
| `0x0810CFA9` / `0x0010CFA9` | `FD 35 0C 02 C7 D1 10 08`: tests flag **`0x20C`**, branches to `0x0810D1C7` when set. | Confirmed static check |
| `0x0810D1B6` / `0x0010D1B6` | `FD 49 0C 02`: sets `0x20C`. Its RAM byte is `0x03003328`, mask **`0x10`**, decoded save offset `+0x326`. | Confirmed static writer; flag change Confirmed runtime |
| `0x0810D1BC` / `0x0010D1BC` | `FE 7C 5C 00 00 07 12 6B EE 10 08`: map-transfer command encodes map `0x005C` and pointer `0x0810EE6B`; followed by `FD 7D`. | Confirmed bytes; destination Confirmed runtime; continuation-pointer role Probable |
| Dialogue pointer operands `0x0810CFD8`, `0x0810CFF6`, `0x0810D02E`, `0x0810D123`, `0x0810D153`, `0x0810D165`, `0x0810D181` | `pointers1.dat` associates messages `564`, `565`, `566`, `56E`, `56F`, `570`, `571`. | Confirmed source/script association |

Flag `0x20C` is therefore **Probable first village-departure/guard-event completion**, separate from both the Lab route flag and Hanzo's claimed flag. The first-departure script has its own transfer and intervening state; clearing the Lab reward selectors or setting `0x21` cannot bypass that script's `0x20C` branch. Do not manually set `0x20C`: its producer includes the guard fight, rewards, actor movements and a destination/continuation context.

Next research should trace `0x0810EE6B`, the completed-departure branch `0x0810D1C7`, and normal exits from map `0x005C` before proposing how to reach a stable overworld control point. A future continuation could use the preserved disposable stop states, retaining A's clear/B's set `0x21`; it must honor the stop condition and should not add speculative flags. Whether ordinary return travel after the naturally set `0x20C` permits the intended comparison is unresolved. No further experiment was performed.

### Evidence artifacts and preservation verification

The experiment directory contains `manifest.json`, `runtime-results.json`, `post-experiment-verification.json`, archival copies, and the UI console runner. Session `logs/` contain exact Lua commands, console transcripts, launch commands and debugger diagnostics; `screenshots/` retain the corresponding captures. Complete scripting history is retained in each `logs/28-stop-console.txt`. The final source ROM readback and all protected hash/size/mtime checks passed after both emulators closed.

| Preserved stop-state artifact | SHA-256 |
| --- | --- |
| A `states/experiment-stop.ss0` | `5d9258dc36758d6599fa72548c65a90e7336855a513d2c6c1893e7ec8e8609cc` |
| B `states/experiment-stop.ss0` | `079055064db34325edff27576977dbeca6fb6e93eebea6d5659d002da69058f3` |

Eight protected source inputs were fingerprinted in the manifest: both root ROMs and all existing `.sav`/`.ss*` files under `reverse_engineering/mgba/` before creating these sessions. Their hashes, sizes and modification timestamps are unchanged. Both copied English ROMs, both copied source checkpoints in each session, and both copied backing saves also retain their original hashes after shutdown. New stop states and captures were created under fresh filenames only. No persistent ROM patch or patcher was created; the Lua harness is an isolated runtime experiment, not gameplay code.

**Conclusion:** the one-bit write and its narrow flag effect are **Confirmed (runtime)**. It is **not yet established as sufficient for safe progression to Hanzo's first event**. Both sessions followed the same required guard/departure sequence and reached an intervening scripted map before the planned route comparison. The experiment was stopped without extending its edit scope; route/Hanzo behavior and subsequent-story side effects remain unresolved.

## Entrance follow-up: route flag, door, and current checkpoint

Continuation on 2026-10-11. This section supersedes the initial investigation's unmapped-entrance statements and the old conditional experiment below. Read the required repository instructions, handoff and this report again. All analysis remained read-only; no emulator was launched. The only edited file is this report.

### Result and scope

The physical lab door has no story-bit, inventory or party test in the decoded ordinary transition path. Access is instead gated upstream by **overworld route flags**. Internal map `0x002F` is the sign-bearing exterior; internal map `0x0030` is the room whose default event pointer is Hanzo's reward script. Both are **Probable gameplay identifications**, backed by confirmed table links, graphics association and the reward dialogue. They have not been visited in a new live trace.

From the protected early snapshots, flag `0x20` already permits the first overworld connection; `0x21` is clear and blocks the next connection to the Hanzo node. The smallest plausible manipulation is **one byte write preserving all other bits**, `B := B | 0x02` at `0x030032EB`. In the inspected snapshots B is `0x01`, so the proposed new byte is `0x03`. Re-read the live byte after returning to a stable field/overworld state; do not assume a menu-state value remains current.

This is a **Candidate safe skip / Confirmed static route unlock**, not a validated replacement for the kidnapping and palace-briefing events. Later story coherence remains a required experiment outcome.

### Map records, entrance and dispatcher

All bus addresses below have ROM file offset `bus - 0x08000000`; no table in this section was relocated by the English translation. The following were compared directly and are byte-identical between the fingerprinted Japanese and English ROMs: lab map records `[0x0062D908,0x0062D940)`, exits `[0x0013AFE8,0x0013B00C)`, overworld arrival script `[0x00130E09,0x00130E18)`, and the cited generic transition/flag-wrapper instruction windows.

| Address / source symbol | Evidence and purpose | Level |
| --- | --- | --- |
| `0x0862D3E4`, stride `0x1C` | Map descriptor base. `0x08033CB8..0x08033CC2` computes `(ID*8-ID)*4` and stores descriptor pointer at `0x03001938`. Current map ID is read from halfword `0x03001936`. | Confirmed static |
| `0x0862D908`, descriptor ID `0x2F` | +0x0C pointer `0x0813AFE8` (exits); +0x10 pointer `0x08159D14` (event triggers). First header halfword is `0x002F`, matching the translation's sign graphics map. | Confirmed bytes; exterior Probable |
| `0x0862D924`, descriptor ID `0x30` | +0x0C `0x0813B000`; +0x10 `0x08159D1C`. At that trigger record, bytes `FF 00 00 00` precede pointer `0x0810D4C0`, Hanzo script. | Confirmed bytes; interior Probable |
| `0x0813AFE8` | Ten-byte door record `09 06 09 06 30 00 00 03 07 80`: rectangle x=9, y=6; destination map `0x0030`; destination entry bytes `00 03 07 80`. | Confirmed parsed geometry/destination; exact fractional positioning semantics incomplete |
| `0x0813AFF2` | Ten-byte exterior exit `04 09 05 09 04 80 00 01 01 00`: rectangle x=4..5, y=9; special destination `0x8004`, corresponding to overworld node 3. | Confirmed bytes and special-destination arithmetic; node association Probable |
| `0x0813B000` | Interior exit `03 08 04 08 2F 00 04 09 07 00`, followed by `FF` terminator at `0x0813B00A`: returns to exterior `0x002F`. | Confirmed parsed destination |
| `0x08159D14` → `0x08111CB2` | Exterior default event is `FD 4D 00 0A FE 89 FD 7D`: writes persistent byte `0x03003287 = 0x0A`, then event control. No flag test in this short root. | Confirmed bytes/write; FE scheduling unresolved |
| `0x080349C4..0x08034A92` | Iterates exit rectangles from pointer at `0x0300193C`, stride 10, terminates on first byte `FF`. Marks cells in `0x02001E08` and exit indexes in `0x02002588`. No story-bit or inventory lookup in this body. | Confirmed static |
| `0x08069994..0x08069BF4` | Ordinary exit dispatcher, indexes those records using `0x02002588`. Destination at +4/+5; high bit selects overworld path. Normal path copies map ID and entry coordinates into `0x03001AC4` and `0x03001930`, then calls map-transition machinery. | Confirmed static |
| `0x08069A2A..0x08069A54` | Reads destination bytes; for high-bit destination clears an animation parameter, reads low destination byte, subtracts 1 at `0x08069A4A`, writes `0x030035F4` at `0x08069A50`, calls `0x0802C1A8` with r0=1. Thus `0x8004` selects node 3. | Confirmed static |
| `0x08069AA6..0x08069B18` | Normal path stores destination map at `0x03001936` (`strh` at `0x08069AAC`) and destination entry fields. At `0x08069B40`, calls `0x0802C1F0` to initiate field transition. | Confirmed static |
| `0x08033C88` and `0x0803F8A4` | Loader/accessor derive the descriptor from current map ID and establish exit, event and graphic pointers. In the ordinary loader, `0x08033E24` loads descriptor +0x10 into `0x03001944` and `0x08033E26` calls `0x08034890`. | Confirmed static dispatcher link; event trigger scheduling Probable |

The generic exit routine also checks temporary state: `0x0300190C` bit 0, `0x03001904`, `0x03001909` and `0x03001908` must not block processing (`0x080699A4..0x080699CC`); the normal exit branch additionally rejects `0x0300190C` bit 1 (`0x080699FE..0x08069A0A`). These appear to gate movement/transition activity, **not story unlocks**. Their complete lifecycle is unresolved. Do not clear them manually: wait for stable gameplay and use normal controls. Collision and actor obstruction can still prevent reaching an exit rectangle; absence of a flag test in this routine does not prove every field path is traversable in every story state.

### Overworld route checks: entry versus onward progression

The four input routines are dispatched by `0x08088D78`: key masks `0x40`, `0x80`, `0x20`, `0x10` select targets `0x08088E20`, `0x08088F48`, `0x08089088`, `0x0808919C`. These are the GBA up/down/left/right masks. Each routine uses the current overworld node as a switch index, reads a flag through `0x080889BC`, and returns either the next node or the unchanged node when the flag is clear. `0x080889EA..0x080889F0` passes the ID to the established main flag reader. This is executable movement gating, not merely an arrow graphic.

| Route / relevant instruction | Actual test and result | Level |
| --- | --- | --- |
| Node 0 → node 1, left | Switch `0x080890A4`, node 0 target `0x080890E8`: `mov r0,#0x20` at E8, call wrapper at EA, zero result branches unchanged at F4; otherwise `mov r0,#1` at F6. | Confirmed static |
| Node 1 → node 3, left | Same table, node 1 target `0x08089100`: `mov r0,#0x21`, branch to `0x0808911E`, flag read; zero stays unchanged, otherwise `mov r0,#3` at `0x0808912A`. | Confirmed static **Lab route unlock** |
| Node 2 → node 3, down | Switch `0x08088F64`, node 2 target `0x08088FC0`: tests flag `0x22`; if set returns 3 at `0x08088FCE`. | Confirmed static alternate Lab connection |
| Node 3 → node 1, down | Same table, node 3 target `0x08088FA8`: tests `0x21`, returns 1 at `0x08088FB6`. | Confirmed static return route |
| Node 3 → node 2, up | Switch `0x08088E3C`, node 3 target `0x08088E80`: tests `0x21`, returns 2 at `0x08088E8E`. | Confirmed static; route asymmetry with node 2's `0x22` is real in inspected code |
| Node 3 → node 4, right | Switch `0x080891B4`, node 3 target `0x08089210`: tests `0x23` via `0x08089216`, zero stays unchanged, set returns 4 at `0x08089222`. | Confirmed static **onward unlock** |
| Arrival at node 3 | `0x08088AF0` selects per-node script; index 3 target `0x08088B78` loads `0x08130E09`. Script is `FE 7D 2F 00 04 08 08 00 80 01 00 00 00 FD 7D`. It encodes entry to exterior `0x002F`. | Confirmed table/script bytes; FE7D full handler not traced, arrival semantics Probable |
| Arrival at node 0 / node 1 / node 2 / node 4 | Corresponding scripts `0x08130DE2`, `0x08130DEF`, `0x08130DFC`, `0x08130E18` encode maps `0x0003`, `0x0008`, `0x001A`, `0x0048` respectively. | Confirmed bytes; place-name mapping Probable |

This identifies node 0 as the village-side entry, node 1 as the wood-side entry, node 2 as palace-side entry, node 3 as Lab 1, and node 4 as Mayonen-side entry (**Probable**, supported by map/name/event associations). At node 3 the input-selection path contains no first-reward flag `0x20A` test. Likewise the physical door uses no `0x20A` test. A claimed reward and an unlocked lab route are separate state.

Overworld arrow renderer `0x0808825C` separately reads `0x20..0x23` in these cases; it is corroborating display evidence, not the basis for the movement conclusion. Inspect the node switch arrays as 32-bit data, not Thumb instructions.

### Initialization and backward writer trace

| State | RAM / mask / decoded save offset | Initialization and modification evidence | Meaning / level |
| --- | --- | --- | --- |
| `0x20` | `0x030032EB`, `0x01`, slot `+0x2E9` | Zero-filled with main bank; `FD49 2000` at `0x0810F03A`, `0x0812470B`, `0x08124A39`. First two are separate event paths; last is bulk unlock. | Confirmed route 0↔1; natural event meaning partly unresolved |
| `0x21` | same byte, `0x02`, same slot offset | Zero-filled; `FD49 2100` at `0x08125867`, `0x0810D49E`, `0x08124A3D`. | Confirmed route 1→3 and Lab return; first natural writer Probable kidnapping-stage unlock |
| `0x22` | same byte, `0x04`, same slot offset | Zero-filled; `FD49 2200` at `0x0810D4A2`, `0x08124A41`. | Confirmed route 2→3; Probable palace briefing completion route |
| `0x23` | same byte, `0x08`, same slot offset | Zero-filled; `FD49 2300` at `0x0810D6C8`, `0x08124A45`. | Confirmed route 3→4; Probable first Hanzo handoff onward unlock |
| `0x209` | `0x03003328`, `0x02`, slot `+0x326` | Zero-filled; test `FD35 0902` at `0x0810D204`; set at `0x0810D4A6`. | Probable palace briefing completed; **not** reward-claimed `0x20A` |
| `0x20A` | same byte, `0x04`, same slot offset | Zero-filled; original Hanzo test/set documented above. | Probable first reward claimed; not entrance unlock |
| `0x16E` | `0x03003314`, `0x40`, slot `+0x312` | Zero-filled; tested at `0x081251C6`, set at `0x08125863`, four bytes before `0x21` is set. | Probable kidnapping scene completion; flag is **0x16E, not 0x6E** |
| `0x8D` | `0x030032F8`, `0x20`, slot `+0x2F6` | Zero-filled; set at `0x0811CE34`, after dialogue `919` about obtaining all six Toy Parts. | Probable final Toy Part progression; selects later Hanzo event, not Lab access |
| `0x96` | `0x030032F9`, `0x40`, slot `+0x2F7` | Zero-filled; set at `0x0810D8E0`, after Hanzo phone-call/all-brothers reward sequence `590..59B`. | Probable late Hanzo completion; not first entrance unlock |
| Byte `0x3D` in persistent variable bank | `0x030032C4`, whole byte, slot `+0x2C2` | Variable bank `0x03003287..0x030032E6` initialized to zero; many `FD4D 3D value` writes, listed below. | Confirmed persistent byte; Probable broader Gimmick/event stage, exact semantics Unconfirmed |

Initialization: routine starting `0x08032984` sets r8=0 at `0x08032990..94`; `0x08032A20..2C` fills `0x030032E7` with 24 words (96 bytes), BIOS transfer control `0x01000018`; `0x08032A30..3A` similarly clears the 96-byte variable bank `0x03003287`. Both banks also load from decoded saves: flag bank slot +0x2E5, byte bank slot +0x285 (`0x0802F4B4..0x0802F4DA`). This is **Confirmed static initialization**, with new-game role **Probable**; invocation timing was not observed. Savedata loads, wholesale initialization and generic flag writers are additional modification mechanisms beyond literal event commands.

The listed FD49 writers come from full-ROM raw-pattern searches, with surrounding event bytes inspected. No literal `FD4A` clear commands for `0x20..0x23`, `0x16E`, `0x209`, `0x20A`, `0x8D`, or `0x96` were found. This is not an exhaustive semantic write graph: indirect IDs, alternative opcodes, loads and arbitrary native stores may modify them.

Natural `0x21` writer: `0x08125863` sets `0x16E`, then `0x08125867` sets `0x21`. Surrounding dialogue `A65..A75` describes Brikky/Grikky capturing Pasaran and receiving orders from Abira. Earlier test at `0x081251C6` branches to `0x081254CB` when `0x16E` is already set; test/set `0x112` at `0x081251CE`/`0x081251D6` introduces another scene-state dependency. Flag `0x112` is RAM `0x03003309`, mask `0x04`, decoded slot +0x307. Its complete semantic writer/read graph was not traced. The `0x21` write is therefore not an isolated natural story update.

Natural second route writer: map `0x001B` descriptor `0x0862D6D8` points to trigger list `0x08159BC4`; its default trigger at `0x08159BD0` points to `0x0810D1F0`. That event tests `0x8F`, `0x8D`, `0x209`, and `0x20F`, and its first-briefing branch has messages `574..583` about the palace wall, six Toy Parts and the first Super Kid in Mayonen. At `0x0810D49E..0x0810D4AE` it sets `0x21`, `0x22`, `0x209`, and `0x21E`. Thus briefing completion also refreshes the wood-to-lab route. **Confirmed bytes and table links; Probable quest-briefing semantics.** The other guards `0x8F/0x20F` select alternate briefings rather than appearing in the lab door dispatcher; full late-event effects remain unresolved. `0x21E` is RAM `0x0300332A`, mask `0x40`; its purpose is Unconfirmed.

Bulk writer: block at `0x08124A39` sets **all flags `0x20..0x2E`**, followed by further commands. A pointer to it occurs at `0x0812F433`. It is a Candidate debug/shortcut lead, not an approved safe skip. Do not invoke it or emulate its flag list; it opens later routes and bypasses the original handoff's onward gate.

### Additional Hanzo prerequisite: persistent variable byte

This corrects the initial report's incomplete statement that the three local flag checks alone select the initial event:

```text
0810D4C0  FD 0D 3D                ; load persistent byte 0x030032C4
0810D4C3  FD 1F 12 00             ; compare accumulator to 0x0012
0810D4C7  FD 45 D9 D6 10 08       ; branch when accumulator >= 0x12
0810D4CD  FD 4D 00 0A             ; otherwise write variable-bank byte 0 = 0x0A
0810D4D1  FD 35 96 00 ...         ; subsequent flag selectors
```

`FD0D` handler `0x0802693C` indexes `0x03003287 + parameter`; byte read at `0x08026958`, accumulator `0x03003A24` written at `0x08026960`. `FD1F` handler `0x08029AAC` subtracts the immediate from the unsigned accumulator; negative result sets comparison bit `0x10`, equality sets `0x80` in context byte `0x030039D4`. `FD45` handler `0x0802984C` takes the pointer branch when bit `0x10` is **clear** (`0x08029862..66`). These instructions are byte-identical in the two ROMs. The guard is **Confirmed static**, independent of inventory/party semantics.

Full-ROM raw FD4D-pattern matches for byte selector `0x3D`, shown as `ROM bus: value`, were:

```text
080FCF51:08  081089B0:0B  0810B0F3:0A  0810BB82:01  0810D9FB:13
0811203A:0E  0811236D:0F  081127A5:10  08112B2D:11  08112EC9:12
0811415A:06  0811417C:07  0811B473:09  081224AD:0D
08125FC3:03  08125FE5:04  081263EC:05  0812986E:0C  0812F8D1:02
```

Each match identifies exact bytes and a potential writer; no comprehensive event-stage meaning is assigned. Many corresponding reads compare adjacent thresholds in Gimmick-related event regions. The lab's later event at `0x0810D9FB` writes `0x13`. This byte must not be set to `0x12` to “advance story”: that would instead bypass the initial Hanzo branch. Its initialization/load and FD4D generic writer are confirmed, but other write mechanisms remain possible.

The previously unresolved reward temporary selectors `1A`/`1C` also have a concrete resolution now: `0x08022A84` masks the selector to seven bits and adds it to `0x03003A24`; therefore the preceding FD0B stores target halfwords `0x03003A3E = 0x0083` and `0x03003A40 = 0x001B`. They are script temporaries, not the owned-Gimmick inventory. The downstream FE grant handler remains to be traced.

### Protected checkpoint findings and limitations

The existing PNG states were decompressed **in memory only**, using the established mGBA serialized layout from `tools/analyze/mgba/inspect_checkpoint.py` (IWRAM slice `0x19000..0x21000`). No state was loaded into an emulator, rewritten or reserialized. Hashes matched the handoff. The complete set of set bits in the 96-byte main bank is identical in both:

```text
20 122 201 202 203 205 206 207 20B 20E 222
```

| Snapshot | Current map halfword `0x03001936` | Flag byte `0x030032EB` | `0x030032C4` | `0x030035F0` |
| --- | --- | --- | --- | --- |
| `run-6d783e19ca1b/gimmick_menu.ss0` | `0x0001` | `0x01` (`0x20` only) | `0x00` | `0x01` |
| `run-6d783e19ca1b/gimmick_battle.ss0` | `0x0003` | `0x01` | `0x00` | `0x01` |

Current-map interpretation is **Confirmed static field plus checkpoint bytes**, not a new live location observation. `0x030035F0` is the character-group count used by Gimmick lookup; one group is present, consistent with early DeMille-only gameplay (**Probable party interpretation**). Gear-Yo ownership was already established in prior research. No additional friend, item or inventory prerequisite appears in the decoded route/door decisions. Full FE arrival, actor interaction and grant routines could still depend on other state.

Map `0x0001` exits toward `0x0002`; map `0x0003` has exit rectangle x=6..8,y=6 at `0x0813AC8E` encoding special destination `0x8001` (overworld node 0). Both use ordinary transition records. Reaching that exit physically and avoiding automatic village scenes must be validated in A. The battle snapshot should finish the battle normally; editing battle or menu RAM to force field travel would add unrelated risk.

### Smallest plausible manipulation and revised isolated experiment

**Proposed change only:** set `0x21`, byte `0x030032EB`, mask `0x02`, via `old | 0x02`. **Leave `0x22`, `0x23`, `0x209`, `0x20A`, `0x16E`, byte `0x030032C4`, inventory, party, map coordinates, map ID and script cursors unchanged.** The copied snapshots need no clearing of the three reward selectors. One bit is enough for the decoded node-1-to-lab connection. If normal field exit or event behavior requires another change, stop and trace the missing dependency; do not expand this into a bulk story update.

Use the preservation procedure from the initial experiment below: closed source sessions; hashes and protected archival copies; fresh, independent A/B sessions with baseline English ROM; explicit isolated save/state/patch/cheat paths; embedded savedata excluded (`loadStateExtdata=9`); no saves or checkpoints overwritten. No such preparation or manipulation has happened in this continuation.

1. **A, zero-write control.** Copy `gimmick_menu.ss0` into A, load only that working copy, exit menus normally. Reach village map `0x0003` and its normal overworld exit. If field scripts block the exit, record the exact scene/actor and stop before B. Record map, all 96 flag bytes, variable byte `0x030032C4`, owned Gimmicks and character-group count. At overworld node 0, use left to reach node 1 (flag `0x20` already set); try left again. Break at `0x08089100`/`0x0808911E`, then `0x08089124`/`0x08089128`: expect flag `0x21` mask result zero and unchanged node 1. Confirm node initialization at `0x08088A90..98` and retain actual input/PC transcript. Do not rely on arrow appearance alone.
2. **B, one-bit trial.** Independently copy the same source checkpoint into B. Follow the same path and pause in idle overworld node 1 before selecting left. Read `0x030032EB` and the reward/variable prerequisites. If they match A, record the byte and edit only `old | 0x02` using the built-in memory editor after separate experiment authorization. Resume left selection; at `0x08089124` expect utility result `0x02`, and at `0x0808912A` expect next node 3. This avoids guessing a teleport or editing a suspended interpreter context.
3. **Normal lab entry.** Select node 3 normally. Break at `0x08088B78` to confirm arrival script pointer `0x08130E09`; watch the normal map loader reach exterior `0x002F`. Walk to the door rectangle at (9,6); break at `0x08069AA6` and `0x08069AAC` to capture destination halfword `0x0030`, then inspect `0x03001936/38/44` after loading. Verify the default event pointer resolves to `0x0810D4C0`. If the door/arrival stalls, capture temporary gates and actor/collision state; do not clear them blindly.
4. **Original handoff.** Trace byte `0x030032C4`, then `0x96/0x8D/0x20A` reads and grant temporaries `0x03003A3E/40`. Watch writes to `0x030032EB` and `0x03003328`; record masks and writer PC because `0x209/0x20A` share a byte. Confirm Erupter is granted once to DeMille, menu/usage/equipment behave coherently, `0x23` becomes set by the script, and `0x20A` becomes set. Re-enter/interact again and confirm no duplicate reward.
5. **Subsequent-story check, still disposable.** Test node 3→4 through the original `0x23` check, Mayonen arrival/dialogue, leaving/re-entering the lab, saving to a new B-only save, restarting from that save without a state, and an ordinary battle. Also return toward the wood/palace and check whether the skipped kidnapping scene replays because `0x16E/0x112` remain unset; visit the palace wall briefing normally and observe whether it sets `0x209/0x21E/0x22` coherently. Compare against a naturally progressed pre-Hanzo control when available. Explicitly inspect quest state, Pasaran's story status, actors and subsequent Super Kid/Toy Part events. Passing access/reward checks alone is insufficient to claim preserved progression.
6. **Rollback and decision.** Close B; keep logs and fresh experiment artifacts separate. Resume normal play only from a fresh copy of the protected source checkpoint. Verify source ROM/save/state hashes and timestamps. If omitted story effects cause replay, softlock, contradictory NPC state or broken quests, classify `0x21` as an access-only shortcut and report the missing producers. Do not add `0x16E`, `0x112`, or `0x209` speculatively; their surrounding events may perform additional writes. The safe-skip objective remains unresolved until these checks succeed.

### Remaining dependencies

- Full FE7D arrival handler and default-event/actor scheduler are not decoded end-to-end; current evidence links the relevant records but is not runtime proof.
- Normal village exit availability from each copied checkpoint needs live verification. Temporary movement gates and collision/actor scripts can still block travel.
- The kidnapping producer sets `0x16E` and depends on `0x112`; the briefing sets `0x209/0x21E`. Their complete side-effect sets and later readers must be traced before claiming that a one-bit route skip preserves the story.
- Persistent byte `0x030032C4` is an additional reward-event selector with multiple writers. Its exact meaning, inventory relationships and indirect writers are unresolved; changing it is not recommended.
- First-reward acquisition still needs the FE grant call chain and runtime observation. No requirement for extra party members or items was found in the route/door path; that does not prove no dependency elsewhere.

Verification: cited native route, byte-variable, map-descriptor and generic transition windows are identical in both protected ROMs. Checkpoints were read without emulator execution. No new gameplay behavior is labeled Confirmed (runtime).

## Initial investigation retained for provenance

The remaining sections record the initial investigation. Where they say the entrance is unmapped, no minimal edit is available, selectors `1A/1C` are unresolved, or `0x23` has no interpretation, the entrance follow-up above supersedes those statements. Its revised A/B experiment replaces the older conditional experiment. Confidence labels and protected-input fingerprints remain applicable.

## Scope, inputs, and evidence levels

Read `AGENTS.md`, `SESSION_HANDOFF.md`, the modding plan (especially §§6 and progression research), `translation_project_overview.md`, relevant `symbols.md` and `memory_map.md` entries, `gimmicks.md`, and the mGBA/checkpoint documentation. Inspected translation ASM, inserter main-message handling, `notes/SCRIPT.md`, legacy `hacking notes.txt`, dialogue and pointer manifests. The current user instruction authorizes this investigation despite the handoff's historical stop instruction.

Read both ROMs with Python `Path.read_bytes()` and decoded bounded Thumb windows with the existing `tools/analyze/thumb_inspect.py`; no build, dumper, patcher, Ghidra analysis, emulator, RAM write, or save/state operation was run. Python bytecode writing was disabled. Only this report was created.

| Input | SHA-256 observed in this investigation |
| --- | --- |
| `Tomato Adventure (Japan).gba` | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| `Tomato Adventure (Japan) (patched).gba` | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |

**Confirmed (static)** means directly decoded bytes or source behavior, not an observed live event. **Probable** indicates a supported gameplay interpretation. **Candidate** identifies a lead. **Unconfirmed** means no sufficient evidence. There is no new runtime confirmation in this report. Original routines have no recovered developer names; names below describe research roles.

ROM bus addresses are file offsets plus `0x08000000`. RAM addresses have no ROM file offset. Save-relative offsets are offsets in the game's decoded slot record, **not demonstrated offsets in an mGBA `.sav` file**.

## Translation source and event locations

`notes/SCRIPT.md` documents dialogue formatting (`FF` codes), not the FD/FE event language. Its sound/display flags must not be treated as story flags. `inserter/text.cpp:InsertMainScript` translates text and updates pointer locations listed in `pointers1.dat`; message IDs do not identify executable scripts. `MainScriptHandle2C` in `asm/name_long.asm` bounds a map actor index and updates actor byte +5. It is not a global story-stage setter. `asm/bug_nocash.asm` repairs store widths related to saving, not progression semantics.

| Location / source | Purpose and evidence | Status |
| --- | --- | --- |
| `ta_script_eng.txt:5980–6037`, messages `584`–`58F` | Hanzo introduction, examination of Gear-Yo, invention, Erupter reward, and subsequent greeting. `58B` explicitly names Erupter. | Confirmed text; Probable first-reward association |
| `pointers1.dat`, physical rows `0x584+1` through `0x58F+1` | Message pointer operands lead into the event region below. `58B` has only `FFFFFFFF`, so there is no direct pointer slot for that literal reward message in this manifest. | Confirmed manifest |
| `0x0810D4C0` / file `0x0010D4C0` onward | Candidate interaction entry; starts `FD 0D 3D`, `FD 1F 12 00`, `FD 45 ...`, `FD 4D 00 0A`, followed by flag selectors. Meaning of preceding setup/selection commands remains unresolved. | Confirmed bytes; Candidate entry |
| `0x0810D517` / file `0x0010D517` | `FE C8` with message `584` pointer operand at `0x0810D519`; English target `0x086630DC`, Japanese target `0x0800F2D1`. | Confirmed pointer/bytes |
| `0x0810D68D` / file `0x0010D68D` | `FE C8`, message `58A`; English pointer operand at `0x0810D68F` targets `0x08663297`. | Confirmed pointer/bytes |
| `0x0810D69C` / file `0x0010D69C` | `FD 2F 33 4B 12 08`: transfers script execution to shared block `0x08124B33`. | Confirmed static script-transfer mechanism |
| `0x0810D6A3`, `0x0810D6B0`, `0x0810D6B9` | `FE C8` operands at +2 correspond to messages `58C`, `58D`, `58E`. | Confirmed pointer associations |
| `0x0810DA42` / file `0x0010DA42` | `FE C8`; operand at `0x0810DA44` targets English `0x08663468`, message `58F` (“How's the new Gimmick treating you?”). | Confirmed bytes/text; Probable post-reward branch |
| `inserter/images.cpp:905`, map `0x002F` | First Hanzo sign asset record. Other sign maps are `00DE`, `00DF`, `00E0`, `00E1`, `0168`. | Confirmed graphics association; Candidate Lab 1 internal map ID |
| `ta_menus_eng.txt:1697`, `POINTERLIST 649A08` row `09` | Display name “Hanzo Lab 1.” Overworld list row `03` also names Lab 1. | Confirmed text indices; neither proves internal map ID |

The bounded event region file `[0x0010D4C0,0x0010DA60)` differs between ROMs in text pointer operands. The exact flag-selector commands, completion writes, and shared-call bytes cited here were checked directly. Shared block file `[0x00124B33,0x00124B65)` is byte-identical. Do not equate original message addresses with relocated English addresses.

## Local selection and claimed state

The dispatch table at `0x0862BC30` (file `0x0062BC30`) supplies FD handler pointers. Legacy notes identify the table; the inspected pointers and handler bodies support these specific commands:

| Command / original handler bus (file offset) | Evidence | Status |
| --- | --- | --- |
| `FD 35`, `0x08029F58` (`0x00029F58`) | Calls `0x08029F90` with mode 1. That reads a little-endian 16-bit flag ID through `0x080227F0`, invokes `0x0806AE2C`, and transfers to the supplied target if the returned mask is nonzero. | Confirmed static set-bit conditional branch |
| `FD 36`, `0x08029F6C` (`0x00029F6C`) | Same shared handler with mode 0; takes target when flag result is zero. | Confirmed static clear-bit conditional branch |
| `FD 49`, `0x08029FF0` (`0x00029FF0`) | Mode 1 to `0x080274A4`, reads two flag-ID bytes, then calls `0x0806AEA0` to set the bit. | Confirmed static set-flag command |
| `FD 2F`, `0x0802896C` (`0x0002896C`) | Reads pointer and preserves/replaces script cursor in a stride-28 script-context record rooted at `0x03003AD4`. | Confirmed static transfer; full call/return lifecycle unresolved |

Hanzo's selector executes in this order:

| Command address (bus / file) | Condition and target | Interpretation |
| --- | --- | --- |
| `0x0810D4D1` / `0x0010D4D1` | `FD 35 96 00 E9 D6 10 08`: if `0x96` set, branch `0x0810D6E9`. | Confirmed static condition; Probable alternate later Hanzo event |
| `0x0810D4D9` / `0x0010D4D9` | `FD 35 8D 00 F4 D6 10 08`: if `0x8D` set, branch `0x0810D6F4`. | Confirmed static condition; broader story meaning Unconfirmed |
| `0x0810D4E1` / `0x0010D4E1` | `FD 35 0A 02 D9 D6 10 08`: if `0x20A` set, branch `0x0810D6D9`. | Confirmed static condition; Probable first-reward completion gate |
| Fall-through `0x0810D4E9` onward | Initial encounter, messages `584` onward. | Probable initial-reward path, provided earlier setup selects this interaction |
| `0x0810D6C8` / `0x0010D6C8` | `FD 49 23 00`: set `0x23`. | Confirmed static write; exact gameplay meaning Unconfirmed |
| `0x0810D6CC` / `0x0010D6CC` | `FD 49 0A 02`: set `0x20A`. | Confirmed static write; Probable reward-claimed marker |

At `0x0810D6D9`, a nested FE block eventually reaches `FD 7D`; the containing script subsequently reaches the `58F` greeting. FE block scheduling and the earlier FD45/FD4D selectors were not fully decoded. Consequently, claim prevention is Probable as gameplay behavior, despite confirmed conditional-bit mechanics. Inventory ownership may impose an additional check in the acquisition path; no uniqueness guarantee has been proved.

A bounded raw-pattern scan of file `[0,0x00140000)` found only this `FD35 0A02` test and this `FD49 0A02` set, strengthening the localized interpretation. The same scan found many `FD35 8D00` occurrences, including earlier event regions and `0x0011CA59`, and `FD49 8D00` at `0x0011CE34`. Flag `0x8D` is not safe to label “Hanzo unlock.” `FD49 9600` occurs at `0x0010D8E0` in the alternate Hanzo region. `FD49 2300` also occurs at `0x00124A45`. These are raw byte matches, not exhaustive parsed cross-references; absence of a pattern does not prove absence of other readers/writers.

## Reward ID and acquisition side effects

Before calling the shared block, bytes at `0x0810D693` are:

```text
FD 0B 1A 83 00
FD 0B 1C 1B 00
FD 2F 33 4B 12 08
```

`FD0B` handler `0x0802A2F4` reads an address selector and stores a decoded halfword. Selectors `1A` and `1C` are not yet traced through address resolver `0x08022A84`; they must not be described as confirmed inventory addresses. The shared block includes `FD15 1A00`, masking/testing, nested FE commands, and `FE16` at `0x08124B50`. Their full acquisition/notification semantics remain unresolved.

The `1B00` argument agrees with Erupter's table index `0x1A` / runtime ID `0x1B` in `symbols.md:337` and the dialogue. Thus the **reward ID is Probable**, rather than confirmed by a traced grant instruction. Original Erupter record: bus `0x0862CB40`, file `0x0062CB40`; name/index association is supported by `ta_menus_eng.txt:1330` and the loader's one-based indexing.

Routine `0x0806ADA0` (file `0x0006ADA0`) is a Probable Gimmick insertion helper: it uses character index from utility byte +5, ID from +1, character records `0x03001EDC + index*0x60`, count at +7, and appends a three-byte entry at +8. It initializes entry +1 from `0x0300196E`, entry +2 to zero, writes two bytes at `0x0200EF08 + 2*(ID-1)` from original record +0x25 masked by `0x1F`, and attempts to fill an empty equipped slot at character +0x5A..+0x5D. Its body is identical in both ROMs. This is not yet a verified call chain from Hanzo. It shows why writing an owned-ID byte or completion flag alone is inadequate: acquisition can touch count, difficulty, usage state and equipment.

## RAM and persistent representation

| Address / source window | Evidence and meaning | Status |
| --- | --- | --- |
| `0x030018BC` | Shared utility parameters: flag ID at +4; flag reader result byte at +1. `saving_screen.asm:98–119` supplies IDs `0x28` and `0x2D0`. | Confirmed source/static interface; unrelated flag meanings Unconfirmed |
| `0x0806AE2C` / `0x0006AE2C` | Supplies base `0x030032E7` to bit reader `0x08069F60`, preserving utility words through scratch stack `0x03000604/608`. | Confirmed static main flag wrapper |
| `0x08069F60` / `0x00069F60` | Reads 16-bit ID, indexes `base + (ID >> 3)`, returns byte AND mask from table `0x0863A01C`. Result is zero or the actual mask, not normalized to 1. | Confirmed static representation |
| `0x0863A01C` / `0x0063A01C` | Eight mask bytes `01 02 04 08 10 20 40 80`. | Confirmed ROM bytes |
| `0x0806AEA0` / `0x0006AEA0`; `0x08069F8C` / `0x00069F8C` | Wrapper selects main flag base; helper ORs selected mask into existing byte. | Confirmed static set behavior |
| `0x08069FBC` / `0x00069FBC` | Generic bit clear via BIC. Main clear wrapper is called at `0x080274F0`, target `0x0806AF2C`; that wrapper was not fully traced. | Confirmed generic clear; Probable main clear wrapper |
| `0x030032E7..0x03003346` | 96-byte region loaded from decoded slot +0x2E5; room for 768 bits, IDs `0..0x2FF`. Accessor has no observed range check. | Confirmed copied extent; not proof all bits are story flags or valid IDs |
| `0x0802F4DC..0x0802F502` / file `0x0002F4DC..0x0002F502` | In `LoadSaveSlot`, copies exactly 96 bytes from slot pointer +0x2E5 to the RAM flag base. | Confirmed static load mapping |
| `0x0862D394` / `0x0062D394` | Four slot pointers `02000000`, `02000600`, `02000C00`, `02001200`. Slot role/count beyond this table not established. | Confirmed bytes |
| `0x0802EF5C..0x0802EF80` / file `0x0002EF5C..0x0002EF80` | Copies 96 flag bytes to `0x02001AE5`, consistent with staging-record base `0x02001800 + 0x2E5`. | Confirmed static serialization into staging; staging-record interpretation Probable |

These inspected flag helper and slot-load windows are byte-identical in Japanese and English ROMs. Literal pools were treated as data, not instructions. Translation replacements inside `SavingLoadSaveInfo` do not relocate the underlying main flag array.

| Flag | RAM byte | Mask | Decoded slot byte | Meaning status |
| --- | --- | --- | --- | --- |
| `0x96` | `0x030032F9` | `0x40` | `+0x2F7` | Confirmed selector; later-event interpretation Probable |
| `0x8D` | `0x030032F8` | `0x20` | `+0x2F6` | Confirmed selector; global story meaning Unconfirmed |
| `0x20A` | `0x03003328` | `0x04` | `+0x326` | Confirmed test/set; first reward claimed Probable |
| `0x23` | `0x030032EB` | `0x08` | `+0x2E9` | Confirmed post-event set; meaning Unconfirmed |

Physical EEPROM/save-file encoding, checksum algorithm, redundancy, record selection and final persistent write transaction were not traced. The 0x600 slot spacing is a RAM buffer layout, not a license to edit `.sav` bytes at matching offsets. A RAM edit could persist if the game saves; only a separate disposable session provides reliable rollback.

## Minimal changes: what can and cannot be recommended

**For the local initial dialogue selector:** the minimum is zero writes if those three bits are already clear. If the lab can be entered in a coherent early state, leave them clear and let the original event grant Erupter and set its completion state. Do not pre-set `0x23` or `0x20A`; do not inject inventory.

**For an already-claimed coherent lab checkpoint:** clearing only `0x20A` is a candidate event-replay experiment, conditional on `0x96/0x8D` being clear. It is not a proposed story skip or safe reward duplication: the owned Erupter entry and acquisition side effects could already exist.

**For reaching the lab from the available early Gear-Yo checkpoint:** no proven minimal edit set is available. The local flags above appear to select dialogue variants, not open the route. Do not clear `0x8D/0x96` wholesale in a later save, set every earlier flag, change map coordinates by guessing, force a script cursor, or assume menu-name indices are map IDs. Those operations can bypass required party, transport, key-item, actor, position, and event-context initialization.

The preferred conditional skip would be a verified entrance-gate bit change while preserving the unclaimed Hanzo state, using the game's normal map-transition/event machinery. If travel instead depends on multiple event side effects, a naturally obtained pre-Hanzo checkpoint is safer and faster than manufacturing global progression. Mapping may show that story-flag manipulation is unsuitable; this remains a valid outcome.

## Recommended reversible experiment — future authorization only

1. **Protect and isolate.** Close all mGBA windows. Record paths, SHA-256, sizes and timestamps of the two source ROMs and every chosen source save/state. Make protected archival copies, then independent working copies in a fresh ignored session with unique filenames. Use the baseline English ROM hash above, not the Gear-Yo experiment. Keep original `run-6d783e19ca1b` and `run-8583a5fb3db2` untouched. Record mGBA 0.10.5 revision and checkpoint provenance.
2. **Control savedata.** Follow `mgba_setup.md` and `gimmick_runtime_tests.md` isolation settings: separate savegame/state/patch/cheat paths, portable config, no automatic patches/cheats, rewind off, and `loadStateExtdata=9` excluding savedata mask `0x2`. Existing checkpoints embed all-FF savedata; do not restore that into a populated backing save. Verify the actual paths and state-load options in the GUI. The source state hashes in the handoff are menu `570e17c82b6d3592a0b003d991a33b6bf320c04ff7322a339e735f6c65280230` and battle `cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7`.
3. **Read-only access trial (A).** Load only a working checkpoint copy. Exit menus/battles normally into a stable field state. Record party, inventory/count/equipment, current area, and all 96 flag bytes. Try normal travel toward the lab; retain exact blocked entrance/NPC text. Set execution breakpoints at `0x0806AE2C`, `0x08029F90`, and `0x080274A4`. At each relevant stop, record PC, caller/LR, utility +4 ID, script cursor and returned mask. Use `watch/w 0x03003328` and `watch/w 0x030032EB` when tracing the reward; shared bytes can be changed for unrelated bits, so interpret the mask and writer PC. Trace map transition/readers before interpreting any access flag.
4. **Validate the event baseline.** Obtain a coherent just-before-Hanzo control checkpoint if A cannot reach the lab; a user-supplied existing checkpoint or a separate naturally progressed control is acceptable. It may require some baseline play once; the current evidence does not yet support avoiding that entirely. Confirm internal map ID and NPC interaction. Record the `0x96/0x8D/0x20A` checks, utility `1B` acquisition argument, actual call to the grant helper, owned-entry/count changes, usage/equipment initialization, and the final bit writes. This promotes the claimed-state and reward-ID hypotheses to runtime evidence.
5. **Single-change trial (B), conditional.** Start a second independent working copy of the same pre-event checkpoint. Only if A has demonstrated an entrance gate that requires no other missing state, pause in stable field state and change that one verified RAM bit with the debugger memory editor, preserving the seven neighboring bits. Record old byte, mask and new byte; no guessed address/value is specified here. Use normal entrance transition and talk to Hanzo. If already clear, make no edit. Keep `0x20A` unclaimed and do not modify inventory or script context. If another prerequisite is missing, stop and trace it before expanding the trial.
6. **Acceptance and persistence.** Check correct lab/party, one Erupter granted to DeMille, count/difficulty/usage/equipment consistency, `0x23/0x20A` writes, second interaction with no duplicate grant, leaving/re-entering, menu operation and an ordinary battle. Save to a newly named disposable backing save only; restart from that save without a state and verify the behavior and flags. Compare with A and inspect every changed flag, rather than expecting an identical whole-RAM image. Animation, counters and transient RAM naturally differ. Stop on missing actors, frozen scenes, duplicate rewards, unexpected routing or save validation failure.
7. **Rollback.** Close B and retain its logs for analysis. Restore by starting a fresh working copy from the protected pre-edit checkpoint; reversing one byte after an event has run does not undo inventory or other side effects. Verify all protected ROM/save/state fingerprints after closing the emulators. Do not promote B's saves into normal play until wider progression regression is separately justified.

No memory editing, session preparation, emulator launch or experiment was performed during this investigation.

## Unresolved questions and next bounded research

- What are FD45/FD4D and preceding setup doing at `0x0810D4C0`? Which map actor invokes this script, and is it definitely internal map `0x002F`?
- Which entrance, transport, area or NPC condition blocks the current early checkpoint? No access gate was identified by the translation sources alone.
- What exact global state does `0x8D` represent? Its many references argue against treating it as a disposable local switch. What is the later Hanzo state represented by `0x96`?
- Does `0x20A` alone prevent duplication, or does the acquisition helper also test inventory? What broader system uses `0x23`?
- Resolve selectors `1A/1C` through `0x08022A84`, FE16 dispatch and the complete shared reward block; trace the actual grant to DeMille instead of inferring from message text.
- Trace decoded staging data to EEPROM, including checksums/redundancy, before any proposal involving persistent-file edits. For the recommended RAM trial, let the game serialize normally into a disposable save.

The evidence supports targeted RAM experiments after access mapping. It does not yet support a safe, unconditional early-game story-flag recipe or a patcher.
