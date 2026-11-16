# Tomato Adventure — Session Handoff 3

**Session date:** 2026-10-12  
**Status:** Session closeout / documentation only. This handoff authorizes no further emulator execution, ROM modifications, experiments, or commits.  
**Scope:** Hanzo Gimmick reward, Mayonen Caverns BGM, isolated mGBA environments, and investigation toward a pre-Oystown Binky-exchange test state.

## 1. Read-first sources and operating rules

Before resuming, consult:

- `AGENTS.md`
- `SESSION_HANDOFF.md`
- `SESSION_HANDOFF_2.md`
- `SESSION_HANDOFF_3.md` (this file)
- `tomato_adventure_modding_plan.md`
- `reverse_engineering/hanzo_lab1_progression.md`
- `reverse_engineering/oystown_binky_readiness.md`
- `reverse_engineering/experiments/mayonen_caverns_music.md`
- Relevant mapping, checkpoint, battle, script, and patching documentation.

The project remains fundamentally in **Phase 1 ROM mapping**, with separately authorized controlled proof-of-concept experiments. Never overwrite protected Japanese or English baseline ROMs, existing experimental ROMs, original saves or checkpoints. Use isolated copies and record checksums. Do not distribute copyrighted ROM images.

**User-operated debugging rule:** The user operates mGBA and supplies observations. Codex is to conduct bounded, targeted **static analysis** and prepare artifacts only when explicitly authorized. It must not independently launch/control mGBA, load states, inject inputs, perform live RAM experiments, or launch Ghidra/whole-ROM analysis. Request only one precise debugger action at a time when dynamic evidence is necessary. Do not extrapolate static analysis into runtime confirmation.

**Evidence labels:** Distinguish *user-confirmed runtime*, *Codex-reported static*, *candidate/probable*, and *untested*. Earlier session handoffs and research may contain historical findings superseded by newer evidence; verify source artifacts before increasing confidence.

## 2. Protected baseline hashes and existing historical balance work

| Artifact | SHA-256 |
|---|---|
| Original Japanese ROM | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English baseline ROM | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Gear-Yo 21→22 balance experiment | `5cd1cc5c70dce892476d5162d49e0e1552600d37087181f79d0cc4e3d8120a8f` |

The earlier Gear-Yo one-byte balance experiment and CSV patcher remain separate; Gear-Yo 21→22 is **not** a release decision. The handoff-2 Hanzo event decoder trace reached `0x080223CA` with a cursor pointing to `0x0810D4C0`; that generic interpreter investigation was deliberately deprioritized in favor of identifying reward arguments directly.

## 3. Completed experiment: Hanzo awards Dojo Pup instead of Erupter

### 3.1 Static identification (Codex reported)

- Hanzo's first reward uses a **direct Gimmick ID** operand at bus address `0x0810D69B`, file offset `0x0010D69B`.
- Original command at `0x0810D698`: `FD 0B 1C 1B 00` (Erupter ID `0x1B` = 27).
- Codex mapped the original acquisition call to the shared block: call at `0x0810D69D` (`FD 2F 33 4B 12 08`, **corrected call start**; the old `0x0810D69C` statement was an off-by-one error), target `0x08124B33`; command `FD 15 1C 00` at `0x08124B9F`; `FE 54` at `0x08124BA3`; shared grant/inventory routine and initialization through `0x0806ADA0`.
- Character index is encoded in bits 6–7 and Gimmick ID in bits 0–5; Erupter is character 0 (DeMille), ID 27.
- Dojo Pup's confirmed static one-based ID is `0x29` = 41, derived from translation-table index `0x28` and the one-based loader.
- Replacing `1B 00` with `29 00` changes just the reward selection without changing the shared acquisition routine.

### 3.2 Patch (Codex reported verified)

- Script: `tools/patch/hanzo_dojo_pup.py`
- Output: `tools/patch/output/hanzo-dojo-pup-96034ad7bdfa4bd0b3e9313e3b617daf/hanzo_dojo_pup.gba`
- Only changed byte: file `0x0010D69B`, `1B → 29`.
- New command: `FD 0B 1C 29 00`.
- Experimental ROM SHA-256: `749762aa8c3c0fae433d46c0ebbcbf4f54646790baf4b6129414e6e5832cdfea`.
- Reproduction (for a *future authorized* session): `python -B tools/patch/hanzo_dojo_pup.py`. The script validates baseline and command, writes to a fresh directory and records a manifest.

### 3.3 Manual runtime evidence (user-confirmed)

- Hanzo event displayed **“Got Gimmick: Dojo Pup!”**.
- DeMille's Gimmick menu showed Gear-Yo and Dojo Pup; the user also confirmed **Dojo Pup works in battle**.
- This verifies the principal reward replacement and combat usability. Longer-term save/reload, uniqueness, or broader story progression were **not** conclusively tested.
- Do not modify the verified Dojo Pup experimental ROM while working on other experiments.

## 4. Completed one-map experiment: Mayonen Caverns BGM

### 4.1 Music-selection mechanism (Codex static + user runtime)

- Sound playback entry: `0x08092E70`; observed user breakpoint during Mayonen entry with `r0=0xCF`, LR `0x08065FE1`.
- Caller at `0x08065FD4` reads `0x03001972`, adds **decimal 200**, and calls `0x08092E70`: `sound ID = selector + 200`.
- Map-record base `0x0862D3E4`, stride `0x1C`; current map record pointer in `0x03001938`. Music selector is the lower six bits of map record byte `+5`; preserve upper bits. Event commands `FE A7`, `FE A8`, `FE A9`, `FE AB` can override normal map music.
- Mayonen overworld/first-screen arrival map `0x0048`: record `0x0862DBC4`, music byte bus `0x0862DBC9`, file `0x0062DBC9` = `0x07`. User confirmed selector `0x07` in RAM `0x03001972` while hearing the desired Mayonen theme; playback ID `0xCF`.
- User entered Mayonen Caverns and observed selector `0x0D` in RAM and map-record pointer `0x0862D72C` => map ID `0x001E`. Read of bus address `0x0862D731` returned `0x0D` (file offset `0x0062D731`); user identified audible music as Pokypine Forest, playback ID `0xD5`.

### 4.2 Patch (Codex reported verified)

- Script: `tools/patch/mayonen_caverns_music.py`.
- Output: `tools/patch/output/mayonen-caverns-map001e-86d6efb0c6824c9c851fb5602c4e4746/mayonen_caverns_map001e.gba`.
- Manifest alongside output: `manifest.json`.
- One-byte change **only** at file `0x0062D731`: `0D → 07`, on the **unmodified English baseline**.
- Experimental ROM SHA-256: `7fc50105e340510079158ca74e61f778b63b3276793ec9b6ffbe29c2af75c761`.
- Reproduction for a future authorized session: `python -B tools/patch/mayonen_caverns_music.py`.
- Codex reported the baseline and other protected files retained hashes; no autonomous emulator test was run.

### 4.3 Manual runtime evidence and limits

- First attempt after loading a previous save state and re-entering the Caverns still played Pokypine Forest. **Cause unresolved**; do not claim it was definitely save-state audio caching.
- A subsequent **fresh isolated launch** was successful: Mayonen's first screen played the desired theme; after entering Caverns map `0x001E` normally, the user reported **A: the Mayonen theme continued playing**.
- User was underleveled and elected not to travel deeper to test other rooms.
- Thus **runtime-confirmed for entry to map `0x001E` only**, not the entire Caverns. Codex recorded this in `reverse_engineering/experiments/mayonen_caverns_music.md`.
- Connected maps with `0x0D` music field, **not confirmed as Caverns locations**:

| Map | Music-field file offset | Original byte | Status |
|---|---|---|---|
| `0x001E` | `0x0062D731` | `0D` | User-confirmed Caverns room; patched and runtime-validated |
| `0x001F` | `0x0062D74D` | `0D` | Candidate; directly connected |
| `0x0020` | `0x0062D769` | `0D` | Candidate |
| `0x0021` | `0x0062D785` | `0D` | Candidate |
| `0x0022` | `0x0062D7A1` | `0D` | Candidate |
| `0x002A` | `0x0062D881` | `0D` | Candidate |
| `0x002B` | `0x0062D89D` | `0D` | Candidate |
| `0x002E` | `0x0062D8F1` | `0D` | Candidate |

Leave the candidates unchanged until map membership is proven and any event overrides assessed.

## 5. Isolated mGBA environments and checkpoint status

### 5.1 Music test environment

- Directory: `reverse_engineering/mgba/isolated_mayonen_music/`.
- Launcher: `launch.bat` (requires Python on PATH).
- Copied mGBA version **0.10.5.0**, experimental Mayonen ROM, isolated saves/states/screenshots/logs/configuration; each run uses fresh session directories. `loadStateExtdata=9` excludes embedded savedata restoration. Codex reported offline artifact/hash verification and did not launch emulator.
- Copied checkpoint `entry-stop.ss0` SHA-256: `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29`. It is a **Hanzo Lab 1 map `0x0030` checkpoint, NOT a Mayonen checkpoint**; Codex reported it contains no embedded savedata.
- User confirmed isolated emulator launch without warnings and Mayonen music success; no full audit of all runtime isolation aspects was reported.

### 5.2 Binky/Oystown test environment

- Directory: `reverse_engineering/mgba/isolated_oystown_binky/`.
- Launcher: `launch.bat`; copied mGBA 0.10.5.0; **unmodified English baseline ROM** (SHA-256 above).
- Fresh portable configs/saves/states/screenshots/logs each launch; `loadStateExtdata=9`. No checkpoint preselected. Codex reported 76 existing protected ROM/save/checkpoint files unchanged when creating it.
- User launched successfully without warnings; only New Game appeared because the isolated environment had no usable battery save. This is expected, not a malfunction.
- Existing `.sav` files: Codex found 16, with 12 erased (8192 bytes `FF`; SHA-256 `7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f`) and 4 identical early saves (SHA-256 `37f0efba33abc9f4b622166b3f2b124ef2144e99e510bfd39e346050982a6874`, map `0x0003`, route flags `0x27` and `0x28` clear). None provides a naturally progressed Alessa/full-AWE/Oystown state.
- Existing checkpoint content samples were also early-game; none is a verified ready-made pre-Oystown checkpoint.

## 6. New target: controlled pre-Oystown Binky-exchange state

The user **explicitly requested manual story/state changes**, rather than playing the entire game normally, provided they are reproducible, constrained to disposable copies and evidence-backed. Desired state:

1. **First screen of Namp Lagoon**, with normal movement and map access toward Oystown.
2. All **required** story conditions completed up to **before the first Oystown arrival** (not indiscriminately setting every lower-numbered flag).
3. **DeMille and Alessa** in the party with correctly initialized data.
4. All **normally obtainable Gimmicks up to that point**, with appropriate ownership and valid initialization.
5. AWE tutorial logically already shown, **AWE active and usable in ordinary battles**, preferably at full charge.
6. Oystown first-entry event and Binky-exchange functionality unmodified; later experimentation will focus on Binky exchange.

### 6.1 Route, arrival, and map facts (Codex static)

- Namp Lagoon overworld node `6`; node-6 arrival script `0x08130E34` selects map `0x0060` and arrival bytes `07 08 80`, setup script `0x081148EB`. Arrival movement/coordinate interpretation not runtime-validated.
- Route 6→7 checks flag `0x26` at `0x08089134`; route 7→8 checks `0x27` at `0x0808914C`. Node 9→8 checks flag `0x28`.
- Oystown overworld node `8` (`0x08`), arrival script `0x08130E4E`, destination map `0x0104`, setup script `0x08102491`.
- Complete required pre-Oystown flags, first-visit gating, stock/exhaustion prerequisites, and coherent progression are **not yet established**.
- Dialogue confirms a Binky exchange requiring full AWE and providing character choices; executable prerequisites and NPC location remain unresolved.

### 6.2 Party and recruitment facts

- DeMille character index 0; Alessa/Alesa character index 1.
- Character record base `0x03001EDC`, stride `0x60`; Alessa record `0x03001F3C`.
- Persistent membership/partner byte `0x03001AB4`. DeMille-only state has `0x10`; Alessa membership bit is `0x20` (upper nibble). Party count at `0x030035F0` is **derived** from membership, not a standalone authoritative flag (`0x08074F2C`/`0x08072970`).
- **User manually read `0x03001AB4 = 0x10`** in a paused early/Hanzo-entry checkpoint, satisfying the DeMille-only prerequisite. A debugger read initially displayed an interrupt/register dump before the repeated command successfully returned the byte; no edits were made.
- Normal recruit command `FE 49`, native handler `0x080252F4`. With Alessa absent it writes `(old_value & 0xF0) | 0x21`, i.e. expected `0x10 → 0x31`, via store `0x08025360`, and initializes character 1 through `0x08032BF0 → 0x08032CB8`, including inventory reset, default stats/equipment, charge/ready reset; preserves her initialized name.
- **Actual Alessa recruitment sequence** identified in Mayonen Caverns map `0x001E`, event-table entry `0x08159BEC` → script `0x081271E9`:
  - At `0x081272D1` tests flag `0x117`, branches to `0x081275B6` when set.
  - At `0x08127326`: `FD 49 17 01` sets flag `0x117`, stored at `0x03003309` mask `0x80`. Probable robot-encounter completion interpretation.
  - At `0x0812732A`: `FE 49` performs normal companion initialization.
  - At `0x0812732C`: `FE 53 6B` grants **Pop Horn**, recipient 1, Gimmick ID `0x2B`, through normal acquisition.
  - At `0x0812759F`: dialogue “[NAME2] becomes a friend” (message AB1).
  - At `0x081275AC`: `FE 1C` actor processing through `0x0803F38C`.
- Historical `FE 49` candidate `0x081166B8` is **not** Alessa's actual recruitment scene.
- Direct native handler invocation is unsafe: `FE 49` requires event/stack context; `FE 53` fetches operand from interpreter cursor `0x030039EC`; normal dispatch via `0x0802478C → 0x080F7ACC` supplies correct call context.
- Recruitment and Pop Horn inventory expectations in a fresh isolated wrapper experiment: Alessa inventory count at `0x03001F43` becomes 1; first entry at `0x03001F44` becomes `2B 01 00`, with normal equipment setup. Do not assume these are runtime-confirmed.

### 6.3 AWE research (Codex static)

| Property | Address/value | Evidence/status |
|---|---|---|
| Tutorial gate | Script `0x08128D5A`, tests flag `0x171`; `0x08128D62` sets it | Confirmed static; written **before** lesson, so “completed” is only probable |
| Tutorial flag storage | `0x03003315`, mask `0x02` | Confirmed static; **not** battle-menu unlock |
| Tutorial battle entry | `0x08128E76` `FE 41 59`, descriptor `0x08456774` | Confirmed static; tutorial also has other battle-context commands |
| Ordinary-battle AWE menu gate | `0x0804DD10` | Rejects one-character battles, participant status bits `0x0104`, and non-ready partner at `0x030009C3` |
| Alessa persistent charge | Character +`0x58` = `0x03001F94`, unsigned byte | Confirmed static; initializer clears it |
| Alessa persistent ready bits | Character +`0x59` = `0x03001F95` | Computed/initialized from charge thresholds |
| Battle partner charge | `0x030009C2` | Battle copy from persistent state (`0x08048072`/`0x08048074`) |
| Battle partner ready bits | `0x030009C3` | Battle copy, checked by menu |
| Maximum charge | `64` decimal = `0x40` | Gain path `0x08042AC0–0x08042AD0` clamps |
| Alessa thresholds | `40` and `64` decimal | Table `0x086397A6`, `0x086397D2`; check at `0x0804802E`/`0x08048046` |
| Consumption | `0x08050246–0x0805026C` | Subtracts selected threshold and clears ready bits |
| Persistence | `0x0803FE7C–0x0803FE90` | Writes battle state back to character; end-to-end runtime untested |

For a **coherent, already initialized DeMille–Alessa party**, a full Alessa persistent charge byte `0x03001F94 = 0x40` is a supported **candidate controlled edit**. The normal battle initializer should derive ready bits `0x03`; do **not** manually invent battle-local bits or HUD state. Flag `0x171` alone is **not** enough to enable AWE. Other possible eligibility side effects and actual runtime operation still require user verification.

An earlier Codex next-observation suggestion was breakpoint `break 0x08048072` (read of persistent charge before battle copy), but it was **not** performed. Recruitment was prioritized instead.

### 6.4 Inventory and state limitations

- The full list of mandatory/optional pre-Oystown Gimmicks, their ownership, and progression-linked acquisition flags is **unresolved**. Do not grant every Gimmick in the ROM.
- Generic character startup initializer is not a safe substitute for the recruitment event. The original event contains robot battle, dialogue, actor updates and additional progression conditions; cannot replay arbitrary script from an unrelated checkpoint.
- Oystown-ready checkpoint has **not** been created. No claim should be made that Alessa, full AWE, correct inventory, or coherent Oystown progression has already been achieved.

## 7. Most recent proposal: controlled Alessa recruitment wrapper — NOT YET IMPLEMENTED

Codex proposed using the **first Hanzo reward call as a temporary carrier** on a new experimental ROM, using the interpreter rather than direct native-handler calls. The protected root `entry-stop.ss0` (SHA-256 above) was inspected offline: membership `0x10`, party count 1, Alessa name already initialized, inventory count 0, acquisition difficulty parameter `0x0300196E=1`. The user independently confirmed membership `0x10`.

**Corrected original call:** begins at bus `0x0810D69D`, command `FD 2F 33 4B 12 08`. Pointer operand at file offset `0x0010D69F`. Proposed replacement points to verified free ROM space containing:

```text
FE 49                  ; original companion initialization
FE 53 6B               ; original Pop Horn acquisition (recipient 1, ID 0x2B)
FD 0B 1A 83 00         ; restore original Hanzo reward parameter
FD 0B 1C 1B 00         ; restore original Erupter reward operand
FD 30 33 4B 12 08      ; transfer to original shared reward block
```

- `FD 2F` saves caller cursor and sets return context; `FD 30` replaces the active cursor without a second nested return slot; the shared block's `FD 7C` at `0x08124BF0` returns to original Hanzo continuation (Codex static claim; runtime untested).
- Payload placement/free-space safety must be verified **before** patching. Do not assume any ROM address is free.
- Expected membership `0x10 → 0x31`, Alessa initialized, Pop Horn inventory, DeMille still gets Erupter, derived party count and battle records refreshed by normal game machinery. **All runtime outcomes remain untested.**
- The carrier also completes normal Hanzo reward and its progression effects; it does **not** complete Alessa's original robot encounter, set its flag coherently, or create a fully progressed pre-Oystown state. Do not replay the actual recruitment event after using this standalone test and do not promote the output as a normal-play ROM.
- No wrapper patch has been created, no new state constructed, no emulator run for wrapper testing, and no permission to proceed beyond this session's closeout.

## 8. Immediate next-session action

The latest assistant-produced **Codex implementation prompt is reproduced in full in §9**. At the next authorized session, user may submit it to Codex to implement a **separate** Alessa initialization experimental ROM using the English baseline, subject to free-space checks and strict original-file safety. Codex must **not** operate mGBA. The user would then validate the event, inventory, movement and battles manually in an isolated environment. Do not merge this experiment with Dojo Pup or Mayonen music.

Once isolated recruitment is runtime-validated, later work remains: (1) full AWE state from the real persistent byte and tutorial context; (2) consistent Namp Lagoon first-screen arrival; (3) complete pre-Oystown flags and normal first-entry gate; (4) accurate stage-appropriate Gimmick inventory; (5) eventual Binky-exchange mechanic study. All are separate milestones requiring evidence and explicit authorization.

## 9. Exact last prompt generated for Codex

> # Tomato Adventure — Experimental Alessa Recruitment Wrapper
>
> ## Objective
>
> Implement a controlled, reproducible experimental ROM patch that invokes the game's original Alessa recruitment and Pop Horn acquisition handlers through the normal event interpreter.
>
> Use the first Hanzo reward event as a temporary carrier.
>
> This experiment is strictly for validating party initialization. It is not a finalized pre-Oystown progression patch.
>
> ## Established evidence
>
> The protected `entry-stop.ss0` checkpoint has been inspected offline:
>
> - SHA-256: `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29`
> - Party membership: `0x10`.
> - Party count: 1.
> - Alessa's name is initialized.
> - Alessa inventory count: 0.
> - Acquisition difficulty at `0x0300196E`: 1.
>
> The user also manually confirmed membership `0x10` in mGBA.
>
> The game's normal recruitment handler is `FE 49`.
>
> The game's normal Gimmick acquisition command is `FE 53 6B`, granting Pop Horn to character 1.
>
> ## Proposed wrapper
>
> The original Hanzo call begins at `0x0810D69D`:
>
> `FD 2F 33 4B 12 08`
>
> Its pointer operand is at file offset `0x0010D69F`.
>
> Redirect the pointer to a new, verified free-space payload:
>
> ```text
> FE 49
> FE 53 6B
> FD 0B 1A 83 00
> FD 0B 1C 1B 00
> FD 30 33 4B 12 08
> ```
>
> The wrapper must:
>
> 1. Execute the native companion initialization through the event interpreter.
> 2. Grant Pop Horn through the normal acquisition helper.
> 3. Restore the original Hanzo reward parameters.
> 4. Transfer execution to the original shared reward block.
> 5. Return normally to Hanzo's event continuation.
>
> Do not jump directly into native handlers.
>
> ## Implementation requirements
>
> Before modifying anything:
>
> - Verify the English baseline SHA-256.
> - Verify the exact original Hanzo command bytes.
> - Verify the selected ROM space is unused and safe for the payload.
> - Verify the interpreter's call/return behavior and pointer encoding.
> - Confirm the wrapper doesn't overlap translated code, data, or referenced space.
>
> If any prerequisite cannot be established, stop without creating a ROM.
>
> Use the unmodified English baseline, not the Dojo Pup or Mayonen experimental ROMs.
>
> Create a fresh output directory and a reproducible patch script.
>
> Verify every modified byte and perform full-file comparison.
>
> Preserve the Japanese and English baseline ROMs, saves, checkpoints, and all previous experimental outputs.
>
> ## Strict runtime restrictions
>
> Do not launch or operate mGBA.
>
> Do not:
>
> - Run gameplay automatically.
> - Load or alter emulator checkpoints.
> - Inject controller input.
> - Execute live debugger commands.
> - Modify live RAM.
> - Launch Ghidra.
>
> Only static preparation, patch construction, verification, and documentation are authorized.
>
> ## Manual runtime validation
>
> Provide a concise test plan for the user.
>
> Expected observations after completing the first Hanzo reward interaction:
>
> - Membership byte `0x03001AB4` becomes `0x31`.
> - Alessa appears in the party.
> - Alessa's character record is initialized.
> - Alessa receives Pop Horn.
> - DeMille still receives Erupter.
> - Normal menu operation and movement remain functional.
> - Ordinary battle startup recognizes both characters.
>
> Do not assume these outcomes are confirmed until the user tests them.
>
> Stop if unexpected party membership, inventory contents, equipment, event-return behavior, or game freezes are observed.
>
> ## Deliverables
>
> Report:
>
> 1. Patch script and output ROM paths.
> 2. Verified payload location and justification.
> 3. Original and replacement pointer bytes.
> 4. Input and output SHA-256 hashes.
> 5. Exact modified byte ranges.
> 6. Protected-file verification results.
> 7. Manual test instructions.
>
> Do not modify Oystown progression flags, AWE charge, the starting map, or Binky exchange mechanics in this experiment.
>
> ## Success criterion
>
> Demonstrate that the original recruitment and acquisition handlers can initialize Alessa and grant Pop Horn correctly through a controlled Hanzo event wrapper, without corrupting normal event execution.

## 10. Closeout integrity and caveats

- **This handoff document is the only artifact created by the assistant in this closeout.** It was prepared from the user-provided Codex reports and manual observations in this conversation; it does **not** independently re-run Codex tools, verify local Windows files, or inspect the live workspace.
- No ROM, mGBA save/checkpoint, script, experimental output, or Git repository was changed during this closeout.
- Earlier protected-file audit counts (71, 72, 76) refer to **separate Codex reports at different times**, not a new unified audit. Do not infer a fresh audit from this document.
- The current emulator running/paused/closed state at the end of this session was **not established**; the last known user manual observation was the membership byte `0x10`. On a new session, verify live state rather than assuming it persists.
- Remaining investigation and implementation require fresh, explicit user authorization. No further experimentation is authorized by this handoff alone.
