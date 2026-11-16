# mGBA Runtime Debugging Setup

## Installation and status

Phase 1, 2026-10-10. The installed executables are `mGBA/mGBA.exe` (Qt frontend) and `mGBA/mgba-sdl.exe` (SDL frontend). Both `--version` outputs identify **0.10.5**, revision **`26b7884bc25a5933960f3cdcd98bac1ae14d42e2`**. Qt's Windows file version is `0.10.5.0`; bundled `CHANGES.txt` dates this release to 2025-03-08. No dependency was installed.

| Executable | SHA-256 |
| --- | --- |
| `mGBA.exe` | `feb3695aea18a57841a5058729fb1a679ad12a5a4e00f0de00ff1c0ba1a6798c` |
| `mgba-sdl.exe` | `7a98c18b830610fb3613ad67254a9984f0ce9017b03773c5453b78f55826f87c` |

**Configured:** isolated inputs, portable configuration, paths, launch scripts and ROM preservation checks. **Not verified:** a working live debugger connection or interactive GUI session in this host environment. Two hidden probes could not reach the GDB endpoint. Therefore the deliverable is a documented **manual debugging workflow**, not a claim of automated gameplay capture. No Gimmick calculation, menu screenshot or battle damage was observed at runtime.

Confidence labels: **Confirmed (local)** identifies measured executable/hash/help output or a completed setup check. **Confirmed (source)** identifies version-pinned debugger/API behavior; it is not an executed test. **Probable/Candidate** retain interpretations from prior disassembly. **Unconfirmed** marks runtime behavior not yet captured.

## Debug interfaces and automation limits

Both local help outputs advertise `-g/--gdb`, default port 2345, config overrides `-C key=value`, and state-loading flag `-t`. The installed SDL help does **not** advertise `-d`; do not assume a standalone terminal CLI debugger is available in that build. Neither GDB nor an ARM GDB executable was found on the checked PATH. This does not prevent use of the built-in Qt console.

The Qt binary contains debugger-console, GDB-controller, memory-view and scripting components. The [0.10.5 Qt implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/platform/qt/Window.cpp) exposes these tools. Their interactive availability still needs checking after the manual launch.

The [0.10.5 remote stub](https://github.com/mgba-emu/mgba/blob/0.10.5/src/debugger/gdb-stub.c) implements register/memory reads, stepping/continuation and execution/read/write/access watchpoints. The [ARM debugger implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/arm/debugger/debugger.c) supports hardware-style execution points without patching ROM instructions. A standard-library Python diagnostic client is included, but it did not complete a connection here; its operations are **unverified locally**. Do not treat an advertised interface as a successful round trip.

Lua is documented in the bundled README and [official scripting API](https://mgba.io/docs/scripting.html). That API documents memory/register reads, instruction stepping, frame callbacks, screenshots and state-file operations; its published reference is generated from 0.10.2. These are useful script primitives, not proof of instruction-level breakpoint callbacks. No documented `emu:addBreakpoint`/`emu:setBreakpoint` is assumed for this installation. Lua was not executed here. Frame polling alone cannot establish which instruction read a value.

## Protected inputs and isolated paths

| Source ROM | Bytes | SHA-256 |
| --- | --- | --- |
| `Tomato Adventure (Japan).gba` | 8,388,608 | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| `Tomato Adventure (Japan) (patched).gba` | 8,388,608 | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |

The preparation script gates both hashes, records size/mtime, copies **only the English ROM** to a new `rom/english.gba`, copies both existing executables, and creates `bin/portable.ini` with a fresh `config.ini`. It never imports project saves or states. Save/state filename discovery, including Git-ignored files outside Ghidra's artifact tree, found no existing candidates; no pre-existing save was loaded or altered.

Each session is under `reverse_engineering/mgba/run-<ID>/`:

```text
bin/          executable copies, portable.ini, config.ini
rom/          fingerprinted English ROM copy
saves/        newly generated test save only
states/       uniquely named test states
screenshots/  uniquely named captures
logs/         command manifests, diagnostics, copied console output
patches/      empty isolated automatic-patch lookup directory
cheats/       empty isolated automatic-cheat lookup directory
session.json  protected-file metadata and paths
```

The entire session tree is excluded by `reverse_engineering/mgba/.gitignore`; the installation is excluded by root `.gitignore`. No Git repository was initialized. Source ROMs and copies are fingerprinted again after probes and after the manual launcher exits. These safeguards do not rely on the emulator's working directory alone.

Configuration overrides are `savegamePath`, `savestatePath`, `screenshotPath`, `patchPath`, `cheatsPath`, `useBios=0`, `skipBios=1`, `frameskip=0`, `rewindEnable=0`, and a session-local log path. Portable config selection and directory mapping are supported by [0.10.5 config code](https://github.com/mgba-emu/mgba/blob/0.10.5/src/core/config.c) and [directory code](https://github.com/mgba-emu/mgba/blob/0.10.5/src/core/directories.c). No BIOS file, patch or cheat is supplied. The manual user should check the loaded paths in settings before progressing; do not select either source ROM through the GUI file picker.

Only newly generated analysis saves may evolve during gameplay. Preserve checkpoints using new state filenames; do not overwrite baseline states or bring in another existing save without explicit authorization. Future tests should use separately prepared sessions and explicitly authorized checkpoint copies.

## Reproduction and manual launch

From the repository root:

```powershell
python tools/analyze/mgba/prepare_session.py
python tools/analyze/mgba/start_session.py reverse_engineering/mgba/run-<printed-ID>
```

Fresh prepared session from this investigation:

```powershell
python tools/analyze/mgba/start_session.py reverse_engineering/mgba/run-6d783e19ca1b
```

That session has not been used for gameplay or probes. The launcher opens the Qt frontend for manual interaction and stays running until mGBA closes. It refuses to overwrite launch logs. It does not enable GDB or import a state automatically. All exact executable arguments are retained in the session logs. If launch fails, inspect the process log; do not install software automatically.

The bundled defaults map GBA A/B to X/Z, L/R to A/S, Start to Enter and Select to Backspace; directions use the emulator's configured controls. Confirm bindings in the GUI. Progress through the fresh game until an owned Gimmick, its adjustment/menu page and an ordinary battle are available. An appropriate Cell/Volt/Star is useful for the upgrade comparison but is not required for the first calculation capture.

Use the Qt debugger console from the tools menu. Start with `help` and `status`; retain the output to confirm the actual build's command set. Memory inspection is also available in the game-state views. The [version-pinned console implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/debugger/cli-debugger.c) defines:

| Task | Console command |
| --- | --- |
| Execution point | `break 0x08075970` |
| Current CPU state | `status`, `print/x r0`, `print/x r1`, `print/x lr` |
| Single instruction | `next` |
| Resume | `continue` |
| Byte / halfword / word read | `r/1 ADDRESS`, `r/2 ADDRESS`, `r/4 ADDRESS` |
| Byte dump | `x/1 ADDRESS COUNT` |
| Memory access points | `watch/r ADDRESS`, `watch/w ADDRESS`, `watch ADDRESS` |
| Inspect/remove points | `listb`, `listw`, `delete POINT_ID` |

Plain `break` uses hardware-style metadata. Mode-specific software breakpoint commands and memory/register editing are not part of this workflow. Verify PC and CPSR T bit at each stop; do not assume every instruction in the game is Thumb. The exact Gimmick capture sequence is in [gimmick_runtime_tests.md](gimmick_runtime_tests.md).

If the console is unavailable, retain a screenshot of its menu/help/error and stop instruction tracing. The memory viewer can still record data but cannot establish a producer/consumer PC. If a remote connection is later wanted, configure the GUI server explicitly for loopback `127.0.0.1`, port `2345`, then repeat the diagnostic. No installed GDB client is required for the included probe; it remains experimental until a successful round trip is logged.

## Failed automation probes: precise limitation

1. SDL probe: `run-24f08599ee6a`, using `-g`, dummy SDL video/audio and explicit isolated paths. The process stayed alive with CPU activity, but the diagnostic received no packet. A contemporaneous `netstat` sample showed a client `SYN_SENT` to `127.0.0.1:2345` and no listener on that port. The long-running attempt was stopped by terminating only its copied emulator process; Python then exited. Its initial result file contains only the scope label, so it is **not a successful or complete probe**.
2. Qt probe: `run-2000e25a7706`, using `-g`, Qt offscreen mode and isolated paths. The bounded diagnostic failed with `RuntimeError('mGBA debugger did not become available')`, stored in `logs/probe-results.json`. Cleanup stopped its own process and protected-file verification passed.

Commands and available diagnostics remain in each run's `logs/`. No register response, memory response, breakpoint hit, watchpoint hit or step result was captured. Root cause is unresolved: these observations do not distinguish renderer/startup limitations from host networking or debugger initialization issues. They do not prove mGBA generally lacks automation. The probe now has a wall-clock connection deadline and refuses to replace existing probe evidence. No emulator process from these probes is left running.

The next required input is manual gameplay/checkpoint preparation, followed by confirmation that the ordinary visible Qt console works. No gameplay facts were added to `gimmicks.md` or `symbols.md` because there is no new runtime evidence.
