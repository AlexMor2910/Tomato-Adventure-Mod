# Ghidra Headless Analysis Workflow

## Scope and installation

Phase 1, 2026-10-10. Read-only Japanese ROM analysis; no translation build, ROM write, gameplay patch, software installation, or translation source change. Static disassembly confirms instructions and local data flow, not in-game behavior.

The installation root is `Ghidra/` itself, not an additional nested distribution directory. Launcher: `Ghidra/support/analyzeHeadless.bat`. `Ghidra/Ghidra/application.properties` declares **12.1.4 PUBLIC**, build `20260921`, revision `8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc`, Java minimum 21, no declared maximum. Installed `C:\Program Files\Java\jdk-23` supplies 64-bit Java and javac **23.0.1**. LaunchSupport's `-jdk_home` validation selects this JDK. Headless startup and raw import succeed; no missing dependency was found.

`Ghidra/Ghidra/Processors/ARM/data/languages/ARM.ldefs` includes **ARM:LE:32:v4t**, `ARM4t_le.sla`, `ARMt_v45.pspec`, compiler `default` / `ARM_v45.cspec`. This is the appropriate little-endian ARMv4T/Thumb language for ARM7TDMI. Its default `TMode=0` is ARM: the script explicitly sets `TMode=1` only in evidenced Thumb code windows. It does not treat the entire ROM as Thumb or decode pointer targets as code.

## Inputs and mapping

| Input | Size | SHA-256 |
| --- | --- | --- |
| `Tomato Adventure (Japan).gba` | `0x800000` | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| `Tomato Adventure (Japan) (patched).gba` (preserved reference) | `0x800000` | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |

These match [rom_verification.md](rom_verification.md); this does not authenticate the Japanese dump against an external catalogue. The Japanese input is hash-gated. Raw `BinaryLoader` maps file offset zero to `0x08000000`, ROM span `[0x08000000,0x08800000)`. Raw-loader program image-base metadata remains zero; the actual block start determines the correct bus mapping, and the script logs both. It does not call `setImageBase`, which would relocate the already mapped block. An uninitialized IWRAM block `[0x03000000,0x03008000)` permits RAM address references; it contains no captured runtime state. No EWRAM, BIOS, MMIO, or cartridge mirror state is modeled.

## Reproduction

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1
```

The execution-policy option applies only to the child process; it does not change machine/user policy. Optional `-Jdk`, `-GhidraRoot`, and `-Rom` parameters accept explicit paths. ROM input must retain the documented Japanese hash.

The runner uses the same Java entry point as the installed batch launcher (`ghidra.Ghidra ghidra.app.util.headless.AnalyzeHeadless`). It bypasses `launch.bat`'s `LaunchSupport -save` to avoid writing a per-user JDK choice. All settings, cache, temporary files, compiler outputs and logs use a unique `reverse_engineering/ghidra/run-<GUID>/` directory. No imported ROM copy is needed. `.gitignore` there excludes every generated file; the root ignore file also excludes local Ghidra and ROM/save inputs.

Essential headless arguments (the runner stores exact expanded Java arguments in `arguments.json`):

```text
<run>/projects loader
-import "Tomato Adventure (Japan).gba"
-loader BinaryLoader -loader-baseAddr 0x08000000 -loader-fileOffset 0
-processor ARM:LE:32:v4t -cspec default -noanalysis -readOnly
-scriptPath <run>/classes
-postScript TraceGimmickLoader.class <run>/loader.txt
-log <run>/headless.log -scriptlog <run>/script.log
```

`-noanalysis` disables whole-ROM auto-analysis. `DisassembleCommand` follows flow only within explicit address restrictions. Full-ROM reads scan BL encodings and aligned literal values to generate candidates; this is not whole-ROM disassembly. `-readOnly` discards the import/database changes; Ghidra automatically disposes of the newly created temporary project. This workflow intentionally does not retain a browsable project database. Compiler classes, logs and text evidence persist locally. The runner checks completion markers/logs because headless import can report success even after a script error, and verifies both supplied ROM hashes/sizes/timestamps after analysis.

There is currently no Git repository metadata in this workspace or its parents. Ignore rules are prepared for future Git use; no main-workspace repository was initialized. Generated artifacts are entirely beneath the ignored directory.

## Technical issues and resolution

The first Java source-script run imported successfully but failed during OSGi bundle compilation with `java.nio.file.AccessDeniedException` in JDK ZipFS `removeFileSystem` / Windows `toRealPath`, initially for `Framework/Help/lib/timingframework-1.0.jar` (also `Debugger.jar`). Standalone javac against copied JARs reproduced it for `FileSystem.jar`; copying alone did not resolve the problem. The exact underlying JDK/Windows access cause is unresolved; this is not evidence of an incompatible language or damaged ROM.

Supported precompiled `.class` script loading is implemented in the bundled `Features/Base/lib/Base-src.zip`, `ghidra/app/util/headless/HeadlessAnalyzer.java`, `checkScript`. A directory-classpath attempt also failed: javac reported missing packages despite javap reading the same class files. JDK source inspection identifies an additional `toRealPath(NOFOLLOW_LINKS)` case-mapping check in `JavacFileManager`. Long nested class paths complicated extraction as well. Failed-attempt artifacts remain ignored; extraction is not part of the final workflow.

The final runner uses `tools/analyze/ghidra/CompileScript.java`, a standard `javax.tools.JavaFileManager` adapter that indexes classes in the installed JARs and reads them with `java.util.jar.JarFile`. It delegates platform/JDK classes and output writing to the standard compiler, avoiding dependency ZipFS and directory case-mapping checks. The installed Java launches this small adapter in source-file mode; it compiles `TraceGimmickLoader.java` into the isolated run's `classes/`. No dependency copies, extracted API classes, installed JAR changes, or additional software are needed. The final expanded trace uses this adapter and Ghidra's supported `.class` scripting path.

Successful final run: `reverse_engineering/ghidra/run-cffeb54fcbc540a78ce312e1604a9711/`. It ends with `TRACE_COMPLETE`, no reported script error, correct ROM block mapping and **203 loader instructions**. The runner's protected-file checks pass for both ROMs. The instruction appendix is exported with:

```powershell
python tools/analyze/ghidra/export_trace.py reverse_engineering/ghidra/run-cffeb54fcbc540a78ce312e1604a9711/loader.txt
```

The existing Python interpreter is used only for this optional documentation export. The exporter preserves authored prose and replaces only its marked instruction appendix, refusing incomplete or incorrectly mapped traces.

If reproduction fails, retain the unique run directory and inspect `headless.log`, `script.log`, and compiler output. Do not install a different JDK automatically. No runtime verification or blanket architecture assignment follows from a successful import.

Overlapping bounded disassembly required an additional adjustment: writing TMode over already decoded instructions raises `ContextChangeException`. The script now sets TMode only on undecoded seed addresses, verifies existing seed mode, and permits normal Thumb flow propagation. Previously decoded case blocks do not automatically extend their fallthrough when a larger window is later submitted, so common continuation `0x08075AB2` is an explicit, evidenced seed. Neither correction changes ROM bytes or clears speculative code. A coverage check requires all 203 loader instructions through the original return, excluding the literal pool.

## Analysis boundary

See [ghidra_loader_trace.md](ghidra_loader_trace.md) for addresses, instructions, field evidence and unknowns. No speculative disassembly repair, instruction replacement, or byte patching is performed. The script changes only temporary analysis metadata. Both original ROMs retain their documented SHA-256 values. The toolkit aggregate fingerprint remains `86b596dd580c0cc86b41392d45ac622bb2a256aa6bfca51cbb93618ce2529787`, matching the prior report.
