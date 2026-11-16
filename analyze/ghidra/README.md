# Bounded Ghidra loader analysis

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1
```

Requires the existing Ghidra 12.1.4 installation and a compatible JDK; defaults to `C:\Program Files\Java\jdk-23`. Optional parameters: `-Jdk`, `-GhidraRoot`, `-Rom`. The Japanese ROM is SHA-256 gated. No dependency installation, translation build, ROM export or patch occurs.

The first stage uses the standard Java compiler API through `CompileScript.java` to read bundled dependency classes with `JarFile`, avoiding the observed Windows/JDK ZipFS and directory case-check failures. It compiles the Ghidra script without changing or copying dependencies. The supported precompiled script is then executed by Ghidra headless with `-noanalysis -readOnly`. A new unique run directory prevents collisions or overwrite. Original input files are read directly; all database, cache, settings and compiler data live under `reverse_engineering/ghidra/` and are excluded from Git.

`loader.txt` contains the bounded Thumb loader, references, literal/BL candidates, selected caller/consumer contexts and original-record pointer-slot values. `arguments.json` captures exact Java arguments; headless/script logs retain failures. A completion marker and error-log checks detect script failures despite a successful import exit. Both ROMs are fingerprinted and checked after analysis.

Limits: raw word/BL scans return candidates, not an exhaustive caller graph. Indirect calls, ARM code, aliases and pointer-target semantics require further investigation. TMode is set only for evidenced Thumb windows; whole-ROM analysis is disabled. No speculative bytes or instructions are changed.

To refresh only the instruction appendix of the authored report from a successful run (requires existing Python 3):

```powershell
python tools/analyze/ghidra/export_trace.py reverse_engineering/ghidra/run-<GUID>/loader.txt
```

The exporter validates mapping, completion and loader instruction count before updating the generated appendix. It preserves the report's authored interpretation sections. Python is optional for headless analysis itself.

Details: [workflow](../../../reverse_engineering/ghidra_analysis.md), [loader evidence](../../../reverse_engineering/ghidra_loader_trace.md).

For the complete calculation at `0x08075970`, all seven direct Thumb callers,
selected renderers, and difficulty/upgrade writers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1 -Script TraceGimmickCalculations
python tools/analyze/ghidra/export_calculations.py reverse_engineering/ghidra/run-<GUID>/loader.txt
```

This reuses the same hash-gated raw import, compiler adapter, `-noanalysis`,
`-readOnly`, isolation and protected-ROM checks. The calculation script also
reads the preserved English ROM for narrowly scoped byte comparisons. It
reports direct BL candidates, all-alignment constant-pointer candidates, and
aligned cache-offset matches, then validates callers in explicit Thumb windows.
Switch cases are seeded only from evidenced address tables. Its output retains
the filename `loader.txt` for compatibility with the runner; use the calculation
exporter, which validates the 136-instruction function before updating the new
report's generated appendix. See [calculation findings](../../../reverse_engineering/gimmick_calculations.md).

For the battle candidate recomputation and target halfword update:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1 -Script TraceGimmickBattle
```

This follows the same isolated read-only workflow, decoding only the scoped
candidate functions and actual switch-table destinations. The ignored
`loader.txt` retains their instruction evidence and narrowly scoped English
comparisons. See [battle candidates](../../../reverse_engineering/battle_damage_candidates.md).
