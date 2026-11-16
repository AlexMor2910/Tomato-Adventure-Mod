# Tomato Adventure — Session Handoff 2

**Session date:** 2026-10-11  
**Focus:** Hanzo Lab 1 progression, isolated overworld/lab experiments, and a transition to **user-operated mGBA console debugging**.  
**Status at handoff:** The last user-reported mGBA session was paused at the Hanzo event decoder's cursor-read instruction, before executing it. No further emulator stepping or gameplay is authorized by this document. This handoff records evidence; it does not authorize new experiments.

> **Evidence/provenance warning:** The attached `hanzo_lab1_progression.md` snapshot contains historical sections that predate later Codex results relayed in this conversation. Where dates/status conflict, treat the chronological results in this handoff as newer *reported* evidence, and confirm against the live workspace report and retained artifacts before changing confidence labels. The two most recent debugger traces below were supplied directly by the user. Reports of other later A/B and door experiments were conveyed as Codex summaries; their underlying captures were not independently inspected in this handoff.

## 1. Project constraints and sources

Read before further work:

- `AGENTS.md`
- `SESSION_HANDOFF.md`
- `reverse_engineering/hanzo_lab1_progression.md` (latest workspace copy, including any newer Codex additions)
- `tomato_adventure_modding_plan.md` and applicable mGBA/checkpoint documentation

Keep original Japanese and English ROMs, saves, and existing checkpoints unchanged. No direct ROM patch, invented progression value, inventory injection, teleport, or speculative story-flag edit is authorized. Use fresh isolated experiment copies; `loadStateExtdata=9` excludes embedded savedata restoration. Do not treat a source `.ss0` or ROM as disposable. Preserve screenshots, console transcripts and hashes. Keep confidence classifications separated: **Confirmed (runtime)**, **Confirmed (static)**, **Probable**, **Candidate**, and **Unconfirmed**.

The preexisting `SESSION_HANDOFF.md` records the separate Gear-Yo balance experiment (base 21→22), CSV patcher and Phase 1 mapping status. Nothing in this session authorizes further balance edits or promotion of the experimental ROM to a release.

### Protected baseline fingerprints (from original handoff)

| Artifact | SHA-256 |
| --- | --- |
| Japanese original ROM | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English-translated baseline ROM | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Gear-Yo experimental ROM (not for Hanzo tests) | `5cd1cc5c70dce892476d5162d49e0e1552600d37087181f79d0cc4e3d8120a8f` |

## 2. Chronological progression findings

### 2.1 Early isolated flag A/B stopped at village departure

The first controlled experiment used separate A/B copies of the early Gear-Yo menu state. B changed only the route flag `0x21` via `0x030032EB: 0x01 → 0x03` (`old | 0x02`). The full 96-byte flag bank differed only by that bit; `0x23` and `0x20A` stayed clear. Both sessions nevertheless fought Watchman Kid at the village gate, then the game naturally set `0x20C` (reward byte `0x48 → 0x58`) and transferred both to map `0x005C`. The run correctly stopped as unexpected relative to the planned overworld comparison. No overworld/lab proof was obtained from that first experiment.

- `0x20C`: probable completed first-departure/guard-event marker; do **not** synthesize it via RAM edits.
- Previous experiment stop states: A/B in `reverse_engineering/mgba/run-3160380dd05b/` and `reverse_engineering/mgba/run-45d355b68953/`, respectively; consult report for exact artifacts.
- The first experiment's stopped-state hashes and full evidence remain in the investigation report.

### 2.2 User played normally to Pokypine Wood; two natural checkpoints

The user played the English baseline normally and created two project-root mGBA states. Their analysis was reported by Codex, without running a new emulator session:

| Root state | Interpretation | Size | SHA-256 |
| --- | --- | ---: | --- |
| `pokypine_forest.ss0` | Forest image/checkpoint | 39,424 bytes | `2a2603842095aa3c4fe0f8a09381f897128afafdf36db7daa89e59da3250c886` |
| `map_pokypine.ss0` | Overworld, labeled “Pokypine Wood” | 51,501 bytes | `1079f53c58187342856f405d9c18bc7d96cfc9ea7ba9c224569d7914d9841eb2` |

Both reportedly passed `inspect_checkpoint.py` format/PNG CRC/state-version/ROM-identity checks (mGBA 0.10.5; English ROM CRC32 `A9BB7CD7`). `map_pokypine.ss0` retained field map `0x0008` but **overworld node `0x01`** in `0x030035F4`; these are different concepts. Its state had route byte `0x030032EB=0x01`, reward byte `0x03003328=0x58`, persistent byte `0x030032C4=0x00`. Thus flags `0x20` and `0x20C` were set naturally, while `0x21`, `0x22`, `0x23`, and `0x20A` remained clear. Hanzo-local selectors `0x8D` and `0x96` were clear; DeMille had only Gear-Yo `[01,01,00]`, not Erupter. Flag `0x110` was additionally set (meaning unresolved); kidnapping/briefing candidates `0x16E`, `0x112`, `0x209`, `0x21E` were clear. The state embedded 8,192 bytes of `FF` savedata: load with writeback exclusion as above.

### 2.3 Later isolated overworld A/B — route unlock verified

Codex reported a new isolated experiment using `map_pokypine.ss0`:

- **A** (flag `0x21` clear) stayed at overworld node 1 on left input.
- **B** (only `0x21` set by `0x030032EB: 0x01→0x03`) selected node 3 and displayed **“Hanzo Lab 1.”**
- Runtime tracing reportedly confirmed the flag check and node-3 branch.
- `0x20A` and `0x23` stayed clear; no lab entry or confirmation input was made.
- Both emulators were closed, with **45 protected-file checks passed**.

**Result:** flag `0x21` as the node-1→node-3 overworld unlock is **Confirmed (runtime, per Codex experiment report)**, but this is *not* proof of a safe story skip.

### 2.4 Later isolated lab-entry experiment — arrival, door, pointer fetch

A subsequent Codex report stated:

- Normal node-3 arrival reached lab exterior map `0x002F`.
- Normal movement worked; the laboratory door selected interior map `0x0030`.
- During interior loading, the engine fetched Hanzo's event pointer `0x0810D4C0`.
- Experiment stopped before script dispatch. No Hanzo dialogue or Erupter reward; `0x20A` and `0x23` still clear.
- Emulator closed; **367 protected-file checks passed**.
- Captures and disposable state are under `reverse_engineering/mgba/run-7f871ba72efc/`; referenced stopping checkpoint: `states/entry-stop.ss0`.

**Result:** ordinary exterior arrival and doorway selection were **Confirmed (runtime, per Codex report)**; full interior initialization, script activation, and first reward remain separate questions.

## 3. New preferred workflow: user operates debugger; Codex performs static analysis

The user asked to reduce Codex tool/credit usage. The adopted division of work is:

1. **User:** opens isolated mGBA, pauses/unpauses GUI when appropriate, loads working checkpoint copies, enters one debugger command at a time, captures exact console output and visual state.
2. **Codex:** reads source/ROM statically, identifies *minimal* targeted debugger commands and expected observations, reviews supplied outputs, and updates the report when authorized.
3. **Do not** let Codex autonomously launch mGBA, inject buttons, inspect live memory, change RAM or perform gameplay experiments unless this policy is explicitly changed by the user.

**GUI pause distinction:** In the observed mGBA setup, `continue` did not advance execution while the GUI's **Emulation → Pause** was still enabled. The user had to turn off GUI Pause; the installed breakpoint then stopped the CPU. In one earlier trial two hits appeared after one `continue` (registration and later a cursor update). Do not assume a single textual `continue` guarantees only one hit or that the debugger cannot resume through frontend state interactions. Capture and check the actual CPU state after each hit.

## 4. Manually verified experiment A — registration store

### Setup

- Isolated English ROM, mGBA 0.10.5, working copy of `reverse_engineering/mgba/run-7f871ba72efc/states/entry-stop.ss0`, `loadStateExtdata=9`.
- Initial `status`: `r0=0810D4C0`, `r15=0803F948`, cycle `13838173312`, map `0x0030`; source pointer at `[0x030018C8]=0x0810D4C0`.
- Initial route byte `[0x030032EB]=0x03`; reward bank `[0x03003328]=0x58`; persistent byte `[0x030032C4]=0x00`.
- First paused breakpoint: `0x0806AB56`, Thumb instruction `6008  str r0, [r1,#0]`, `r0=0x0810D4C0`, `r1=0x03003C98`.
- Read destination **before** the store: `[0x03003C98]=0x00000000`.
- `next` executed one instruction: PC advanced to instruction `0x0806AB58` (`7D70  ldrb r0,[r6,#21]`), cycle count `13838175666→13838175671`.
- Read destination **after** the store: `[0x03003C98]=0x0810D4C0`.
- Reward bank remained `0x58`, so flag `0x20A` remained clear. No dialogue/reward was observed during the single-step test.

**Conclusion:** the engine's store registers Hanzo's event pointer in slot 16's cursor — **Confirmed (runtime from user's manual transcript)**. This isolated store does not demonstrate command fetch/dispatch/reward acquisition or full interior initialization.

### Exact saved user transcript (`Investigation Hanzo.txt`)

```text
> status
 r0: 0810D4C0   r1: 030018BC   r2: 03001908   r3: 030039C0
 r4: 03000604   r5: 030018BC   r6: 00000000   r7: 03001900
 r8: 03001974   r9: 00000000  r10: 00000000  r11: 00000000
r12: 00000000  r13: 03007B84  r14: 0803F9DF  r15: 0803F948
cpsr: 6000003F [-ZC---T]
Cycle: 13838173312
0803F946:  1C0D      mov r5, r1
> break 0x0806AB56
 r0: 0810D4C0   r1: 030018BC   r2: 03001908   r3: 030039C0
 r4: 03000604   r5: 030018BC   r6: 00000000   r7: 03001900
 r8: 03001974   r9: 00000000  r10: 00000000  r11: 00000000
r12: 00000000  r13: 03007B84  r14: 0803F9DF  r15: 0803F948
cpsr: 6000003F [-ZC---T]
Cycle: 13838173312
0803F946:  1C0D      mov r5, r1
Added breakpoint #1
> continue
Hit breakpoint 1 at 0x0806AB56
 r0: 0810D4C0   r1: 03003C98   r2: 030018BC   r3: 03003AD4
 r4: 03000604   r5: 03000608   r6: 030039C0   r7: 030018BC
 r8: 03001974   r9: 00000000  r10: 00000000  r11: 00000000
r12: 00000000  r13: 03007B70  r14: 08071CA9  r15: 0806AB58
cpsr: 0000003F [------T]
Cycle: 13838175666
0806AB56:  6008      str r0, [r1, #0]
> r/4 0x03003C98
 0x00000000
> next
 r0: 0810D4C0   r1: 03003C98   r2: 030018BC   r3: 03003AD4
 r4: 03000604   r5: 03000608   r6: 030039C0   r7: 030018BC
 r8: 03001974   r9: 00000000  r10: 00000000  r11: 00000000
r12: 00000000  r13: 03007B70  r14: 08071CA9  r15: 0806AB5A
cpsr: 0000003F [------T]
Cycle: 13838175671
0806AB58:  7D70      ldrb r0, [r6, #21]
> r/4 0x03003C98
 0x0810D4C0
> r/1 0x03003328
 0x58
```

An earlier, *less controlled* attempt stopped first at the same registration store, then at the same native store with `r0=0x0810D4F2`, `r1=0x03003AD8` ~7 million cycles later. At that later stop, `[0x03003C98]=0x0810D4F2`, `[0x03003AD8]=0`, and interior graphics were visible without dialogue; flags/byte values were `0x030032EB=03`, `0x03003328=58`, `0x030032C4=00`. The relation between those two context destinations was **not** resolved by that trace. Do not conflate that second hit with the isolated registration result.

## 5. Static event interpreter trace supplied by Codex

The following is **Codex-reported static analysis**, not independently decoded during handoff preparation:

| Role | Address / value | Evidence level |
| --- | --- | --- |
| Script context base | `0x03003AD4` | Confirmed (static, per Codex) |
| Context stride | `0x1C` | Confirmed (static, per Codex) |
| Slot 16 cursor | `0x03003C98` | Confirmed (static) and registration confirmed (runtime) |
| Registration store | `0x0806AB56`: `str r0,[r1,#0]` | Confirmed (runtime) |
| Decoder | `0x08022388` | Confirmed (static, per Codex) |
| Decoder cursor read | `0x080223CA`: `ldr r2,[r0,#0]` | Confirmed (runtime in next experiment) |
| Command header fetch | `0x080223E6` | Confirmed (static, per Codex); **not yet runtime-observed** |
| First event bytes | `FD 0D 3D` at `0x0810D4C0` | Confirmed (static, per Codex/report) |
| FD dispatcher | `0x080247B4` | Confirmed (static, per Codex); **not yet runtime-observed** |
| Native FD0D handler | `0x0802693C`, via trampoline `0x080F7ACC` | Confirmed (static, per Codex); **not yet runtime-observed** |

`FD 0D 3D` refers to an **interpreted event command**, not a Thumb program at `0x0810D4C0`; do not treat that data address as an ordinary CPU-execution breakpoint. The earlier report decodes `FD0D` as a read of persistent variable-bank selector `0x3D` (RAM byte `0x030032C4`). The original Hanzo selector subsequently checks a threshold `<0x12` and flags `0x96`, `0x8D`, `0x20A`.

## 6. Manually verified experiment B — decoder about to read Hanzo cursor

The user reopened an isolated ROM/session, kept the GUI paused while loading `entry-stop.ss0`, and verified the **exact original initial CPU state** (`r0=0810D4C0`, `r15=0803F948`, cycle `13838173312`). A breakpoint was added at `0x080223CA` **before resuming**, with response `Added breakpoint #1`. `continue` then reached the decoder breakpoint.

### Exact latest user-supplied console evidence

```text
> status
 r0: 0810D4C0   r1: 030018BC   r2: 03001908   r3: 030039C0
 r4: 03000604   r5: 030018BC   r6: 00000000   r7: 03001900
 r8: 03001974   r9: 00000000  r10: 00000000  r11: 00000000
r12: 00000000  r13: 03007B84  r14: 0803F9DF  r15: 0803F948
cpsr: 6000003F [-ZC---T]
Cycle: 13838173312
0803F946:  1C0D      mov r5, r1
> break 0x080223CA
Added breakpoint #1
> continue
Hit breakpoint 1 at 0x080223CA
 r0: 03003C98   r1: 00000003   r2: 00000010   r3: 03003AD8
 r4: 03000604   r5: 03000608   r6: 030018BC   r7: 030039C0
 r8: 00000000   r9: 00000000  r10: 00000000  r11: 00000000
r12: 030019CA  r13: 03007BC8  r14: 08021F37  r15: 080223CC
cpsr: 0000003F [------T]
Cycle: 13838779087
080223CA:  6802      ldr r2, [r0, #0]
> r/4 0x03003C98
 0x0810D4C0
> r/4 0x03003C98
 0x0810D4C0
```

**Interpretation (Confirmed runtime, narrow):** The CPU stopped just before executing `ldr r2,[r0,#0]` at `0x080223CA`, with `r0=0x03003C98` (slot-16 cursor address). Two paused memory reads showed that the cursor contained `0x0810D4C0`. The machine therefore reached the precise point **about to read** the Hanzo script cursor. `r2=0x10` is the *pre-instruction register value*, consistent with slot index 16, **not** the cursor contents yet; the load has not executed. Do not claim the command header was fetched, FD dispatched, or FD0D handler executed in this test.

**Last known user-reported live state:** mGBA is paused at `0x080223CA`, before that load, with breakpoint #1 installed. The user has not reported stepping or resuming past this point, nor closing the emulator. If the emulator has since been closed, reload a *working copy* of the original `entry-stop.ss0` and reestablish a breakpoint before running. Never assume RAM/PC is preserved across separate process launches.

## 7. Relevant RAM, route and Hanzo control summary

| Field | Address / mask | Meaning and status |
| --- | --- | --- |
| Current field map | `0x03001936` (16-bit) | Lab interior `0x0030` in entry-stop; retained map `0x0008` in overworld checkpoint |
| Current overworld node | `0x030035F4` | Node `0x01` at Pokypine checkpoint; node 3 Hanzo Lab 1 in controlled route B |
| Route flags `0x20..0x23` | `0x030032EB`, masks `01/02/04/08` | `0x21` enables node 1→3; `0x23` onward unlock, not set by shortcut |
| First departure flag `0x20C` | `0x03003328`, mask `0x10` | Naturally set by guard sequence; `0x58` byte includes this bit |
| Hanzo first reward `0x20A` | `0x03003328`, mask `0x04` | Clear when byte `0x58`; probable first-reward claimed flag |
| Persistent byte selector `0x3D` | `0x030032C4` | `0x00` in inspected states; precise global meaning unresolved; first Hanzo path checks `<0x12` |
| Hanzo later selectors | flags `0x8D`, `0x96` | Clear in natural Pokypine state; broader meanings must not be assumed |
| First reward | probable Gimmick ID `0x1B` / Erupter | No live grant or menu/equipment/persistence validation yet |

The lab door's static ordinary path uses exterior `0x002F` → interior `0x0030`. The script entry is `0x0810D4C0`. A static route unlock and even successful room entry do **not** establish a coherent skip of preceding kidnapping/briefing effects or later Mayonen/Toy Part events.

## 8. What is proven, and what is not

**Confirmed by later Codex-reported runtime experiments** (underlying captures in workspace):

- `0x21` alone enables the node-1→node-3 overworld route; A remains at node 1.
- Node 3 is labeled Hanzo Lab 1.
- Natural arrival reaches exterior `0x002F`; normal doorway path selects interior `0x0030`.
- Relevant reward/onward flags were still clear at those experiments' stop points; protected files passed the reported checks.

**Confirmed directly by user-supplied console transcripts:**

- `0x0806AB56` writes `0x0810D4C0` to slot-16 cursor `0x03003C98` when single-stepped.
- The shared decoder reached `0x080223CA` with `r0=0x03003C98`; the cursor readback was `0x0810D4C0` twice immediately before the `ldr`.

**Not yet proven:**

- Whether `0x080223E6` fetches `FD 0D 3D` in a manually observed trace.
- Whether the FD dispatcher/trampoline/native handler executes, and which script side effects occur.
- Full interior initialization, NPC/Hanzo behavior, Erupter grant and uniqueness, equipment/usage initialization.
- Later story coherence (kidnapping, briefing, Mayonen, Toy Parts, saving/reloading from a disposable in-game save).
- The intended meaning of `0x030032C4` and the unknown flag `0x110`.

## 9. Safe handoff / next milestone

**Do not immediately `next` or `continue` at the current stop.** First give Codex the latest manual decoder transcript and ask for **bounded read-only static analysis** of `0x080223CA→0x080223E6`, with one guarded debugger observation that captures the first command header *before its handler runs*. The user must personally perform any runtime command, one step at a time. Limit the next experiment to **command fetch**, not event completion or reward acquisition. If the decoder unexpectedly references another slot or a different script pointer, stop and record registers without speculative edits.

Suggested brief for Codex:

> Read `AGENTS.md`, both session handoffs, and the latest `reverse_engineering/hanzo_lab1_progression.md`. The user has manually confirmed the slot-16 registration store and the decoder breakpoint at `0x080223CA`, with `[0x03003C98]=0x0810D4C0`. Perform static analysis only; do not run mGBA. Explain the smallest safe way for the user to observe the first `FD 0D 3D` header fetch around `0x080223E6`, stopping before any native handler executes. Provide one exact next console instruction, expected registers, failure stop condition, and confidence limits. Update the report only when specifically authorized.

### Closeout and safety

- This handoff file is a new documentation artifact only; no ROM, save, state, script, or experiment file was modified in its creation.
- Earlier Codex experiments reportedly closed emulators and passed **45** and **367** protected-file checks respectively; **no new protection audit was performed** during this handoff creation.
- The user has not yet reported a final emulator close or post-session hash verification for the current manual decoder session. Do not claim that either occurred.
- No changes to the protected baseline have been authorized by this handoff.
