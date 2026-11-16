# Alessa recruitment wrapper experiment

**Latest status:** the separately authorized 16 MiB experimental ROM has been
constructed and verified offline, and the user has now confirmed recruitment,
inventory, event completion and ordinary-battle operation in the tested scenario.
The runtime observations are recorded in the final section. The earlier
preflight and allocation sections are retained as historical evidence.

## Original preflight (historical)

Date: 2026-10-13. Targeted static analysis only. No emulator or Ghidra was
launched; no ROM, save or checkpoint was written. This is an incomplete
preflight, not a successful experimental patch. The user's mandatory safe-space
gate remains unresolved, so no speculative patch script or output ROM was created.

Read-first documentation: root AGENTS.md and modding plan; the three handoffs
under `session_handoffs/` (handoff 3 is latest); Hanzo progression, Oystown
readiness, ROM verification, translation overview, memory-map allocation tables,
patch README/current Hanzo patcher, script notes and checkpoint/isolation helpers.
Historical research is not treated as runtime proof.

## Reproducible evidence and integrity

Run `python -B tools/analyze/alessa_wrapper_preflight.py` from the workspace root.
It reads protected artifacts, validates fingerprints and command bytes, scans
pointer-shaped values, and prints JSON. It never patches or allocates ROM space.
The retained output is [alessa_wrapper_preflight.json](alessa_wrapper_preflight.json).
It includes all 79 protected ROM/save/checkpoint paths and hashes. Before/after
inventories and SHA-256 hashes matched for all 79 files.

| Input | Verified SHA-256 |
| --- | --- |
| Japanese original | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Root entry-stop.ss0 | `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29` |

Both ROMs are 0x00800000 bytes. The checkpoint is 20,490 bytes. Its decompressed
saved IWRAM again contains membership 0x10, party count 1, Alessa inventory count
0, and acquisition difficulty 1. Alessa record prefix is `01 8C 85 93 05 81 00`.
These are **confirmed static** saved bytes; only membership 0x10 has the separate
**user-confirmed runtime** observation in handoff 3. The preflight's small PNG
reader does not independently repeat every format/identity check in the existing
checkpoint inspector.

## Reverified command and handler facts

Bus addresses below map to file offsets by subtracting 0x08000000. Handler names
are research descriptions; their source is the English ROM dispatch table and
bounded decoding with `tools/analyze/thumb_inspect.py`, not recovered symbols.
Literal pools are data, even when a linear decoder renders instruction text.

| Address / relevant symbol | Evidence and purpose | Status |
| --- | --- | --- |
| 0x0810D693–0x0810D6A3 (exclusive), Hanzo parameters/call | `FD 0B 1A 83 00 FD 0B 1C 1B 00 FD 2F 33 4B 12 08`. Actual call starts 0x0810D69D, correcting historical report's 0x0810D69C. Continuation starts 0x0810D6A3 with `FE C8 6A 33 66 08`. | Confirmed static bytes |
| File 0x0010D69F–0x0010D6A3, pointer operand | Original `33 4B 12 08` encodes 0x08124B33 little endian. | Confirmed static |
| FD table 0x0862BC30, entries 2F/30/7C | Thumb pointers 0x0802896D / 0x08029F2D / 0x08028A99. | Confirmed static |
| 0x0802896C–0x080289B6, FD2F | Reads pointer via 0x08022874; computes context stride 28, copies cursor +4 to saved cursor +8 (store 0x0802898E), replaces +4, ORs context byte with 0x40. | Confirmed static direct handler semantics |
| 0x08029F2C–0x08029F4C, FD30 | Same pointer reader, writes context +4 at 0x08029F46; no write to +8 or context return bit in this body. | Confirmed static direct handler semantics |
| 0x08028A98–0x08028B0C, FD7C | If context bit 0x40 is set, clears it, loads +8 and restores +4 at 0x08028AE6. Also updates scheduling-related fields. Without the bit it takes a different termination path. | Confirmed static direct handler semantics |
| 0x08022874–0x080228F0, pointer reader prefix | Reads four operand bytes separately, stores them into utility +8..+11 and loads resulting word. No aligned script address requirement in these operand reads. Original shared target is itself unaligned. | Confirmed static prefix; complete decoder lifecycle not re-audited |
| FE table 0x0862B8B4, entries 49/53 | Thumb pointers 0x080252F5 and 0x08025625. FE dispatcher 0x0802478C calls trampoline 0x080F7ACC using this table. | Confirmed static |
| 0x080252F4–0x0802536C, FE49 | Absent-Alessa branch masks old membership with F0 and ORs 21, selects character 1 and calls 0x08032BF0. | Confirmed static; 10→31 runtime untested |
| 0x08032BF0–0x08032C08 | Passes character selector to 0x08032CB8. The wider nearby window includes translated name code and differs from Japanese; do not treat the entire window as unchanged original code. | Confirmed static call |
| 0x08025624–0x08025632, FE53 | Reads byte via 0x08022534 and calls 0x0802927C. | Confirmed static |
| 0x0802927C–0x080292AC | Extracts recipient bits 6..7, ID bits 0..5 and calls 0x0806ADA0. Operand 6B means character 1 / ID 2B. | Confirmed static |
| 0x08127326–0x0812732F | Original sequence `FD 49 17 01 FE 49 FE 53 6B`. | Confirmed static bytes; surrounding recruitment scene interpretation remains historical static evidence |
| 0x08124BF0 | `FD 7C` present in original shared block. | Confirmed static bytes |

The direct call/transfer/return mechanism supports the proposal. Preservation of
return context through **all** wrapper callees, decoder and shared-block branches
has not been exhaustively established here; end-to-end behavior remains
**probable/untested**, not confirmed. No direct native handler invocation occurred.

## Safe-space gate: unresolved

Candidate tail: file `[0x007F1BE0,0x00800000)`, bus
`[0x087F1BE0,0x08800000)`. Both Japanese and English bytes in this range are FF.
English's last non-FF byte is at 0x007F1BDF. `asm/addresses.inc` reserves MechaText
at 0x087F19A0 for 0x240 bytes and comments “Next at 0x087F1BE0.” The inserter's
reported pool ceiling is 0x007F0000; its writes do not have a fully enforced ceiling.
These facts support a **candidate** tail, not independently proven unused space.
`memory_map.md` explicitly warns against allocating at that endpoint before
ownership/build-output verification.

A byte-alignment-independent scan found **68 pointer-shaped values** into this
tail through 08/0A/0C cartridge windows. All candidates are retained in JSON.
Examples: file 0x00193B78 contains word 0x087F1F9E; file 0x0007A431 contains
0x087F60DA. These are **candidate numeric coincidences**, not confirmed code/data
references. Compressed data and overlapping bytes can produce such values.
No conclusion that the tail is actually referenced or unsafe follows from this
scan. Conversely, absence of a literal pointer to a particular 21-byte slot would
not rule out calculated pointers or range reads. No allocation was selected.

Resolving this gate requires bounded classification of relevant candidates and
allocation/build provenance sufficient to establish a reserved unused interval,
including possible computed accesses. A reproducible reserved extension could
be considered separately, but ROM expansion/mirroring behavior and the requested
same-size comparison would need an explicit technical design; it was not silently
substituted for verified in-ROM space.

## Deliverable status

- Patch script and experimental ROM: **not created**; mandatory preflight failed
  to establish allocation safety. The linked preflight is an analysis tool only.
- Payload location/replacement pointer: **unassigned**. Original pointer bytes
  are `33 4B 12 08` at file 0x0010D69F–0x0010D6A2 inclusive.
- Exact proposed 21-byte payload (not inserted):
  `FE 49 FE 53 6B FD 0B 1A 83 00 FD 0B 1C 1B 00 FD 30 33 4B 12 08`.
- Output hash and input/output full comparison: **not applicable**, no output.
- Modified ROM offsets/ranges: **none**. All 79 existing protected files retained
  identical hashes during the preflight audit.
- Runtime: **untested**. No experiment-specific savestate or emulator session was
  created. No progression, AWE, inventory, music or existing experiment was edited.

## Deferred manual test sequence

Do not test a wrapper now: there is no verified patched ROM. Once allocation and
remaining context checks pass and a separate verified output exists:

1. Use a fresh portable mGBA 0.10.5 environment with separate empty saves, states,
   patch and cheat directories, rewind disabled and `loadStateExtdata=9`.
   Record version/output hash. Use a disposable copy of the protected entry-stop
   checkpoint; do not edit its ROM identity/header or force RAM values. Stop if
   mGBA rejects the state or reports an unexpected ROM/state mismatch.
2. Let the first Hanzo reward run normally. Stop on freeze, corrupted dialogue or
   abnormal return. Confirm DeMille receives Erupter and Alessa appears.
3. Pause and perform only the first debugger action:
   `r/1 0x03001AB4`. Expected 0x31. Report that result before requesting another
   precise read. Later reads should separately check count 0x030035F0 = 2,
   inventory count 0x03001F43 = 1, and first entry 0x03001F44 = `2B 01 00`.
4. Check Alessa's stats/equipment and both inventories in menus; normal movement
   and an ordinary battle must recognize both members. Try Pop Horn where usable.
   Stop on unexpected membership, inventory/equipment corruption or abnormal event
   behavior. Do not replay Alessa's original recruitment scene or use this as a
   coherent story checkpoint. No runtime success claim precedes user observations.

The original recruitment flag 0x117 is deliberately absent from the proposal;
this experiment does not complete the robot encounter or broader progression.
DeMille-only membership and acquisition difficulty are established checkpoint
inputs; post-event initialization, inventory/equipment validity and battles are
predictions requiring manual evidence. Work stopped at the unresolved static gate.

## Safe-space and execution-context follow-up (2026-10-13)

Scope: read-only source review and bounded instruction/data inspection. The
retained preflight was used without repeating its whole-file pointer scan.
Reproduction: `python -B tools/analyze/alessa_wrapper_allocation.py` prints the
new [allocation/context evidence](alessa_wrapper_allocation.json). The helper
creates no patched buffers or ROMs and does not execute game instructions. Its
linear Thumb decoder is an observation aid; literal pools are explicitly excluded.

### Allocation mechanisms and candidate comparison

The cartridge image is a flat binary, not an ELF with recoverable section ownership.
The available source allocation ledger, insertion rules and verified baseline
size are therefore the relevant boundaries; an FF run is insufficient.

| Candidate / source | Ownership evidence | Decision / confidence |
| --- | --- | --- |
| Existing text/image pool, file `[0x0064B4EC,0x007F0000)` | `inserter/ta_insert.cpp:8–9,24–33` starts the shared cursor; `text.cpp:35–68` writes/deduplicates strings; `images.cpp:117–126` aligns and advances image allocations. TOMATO_SIZE is a reporting bound, not enforcement. Translation destinations depend on compression and deduplication. | **Confirmed static** translation ownership. Do not use as mod space without a baseline-specific allocation ledger. |
| Fixed text tables, `[0x007F0000,0x007F1BE0)` | `asm/addresses.inc:2–11` reserves tables through MechaText. Existing translated data occupies these slots. | **Confirmed static** reserved translation region; reject. |
| Replacement routine slack in `.region` / `.autoregion` | Included assembly modules reuse replaced code intervals; examples `credits.asm` and `dialog_item.asm`. `.area` bounds a replacement; `.region` can also host later `.autoregion` code/data. | **Confirmed static** allocation mechanism, unknown residual slack. No unused interval can be selected from a region directive alone. Reject without baseline-matching assembler placement evidence. |
| In-ROM tail starting file `0x007F1BE0`, bus `0x087F1BE0` | End of last named table; source comment “Next at” plus previously measured FF tail. A 21-byte candidate would end at `0x007F1BF5` exclusive. | **Probable** unused allocation tail, still **candidate** safe payload location. No computed-access/ownership proof; not recommended for implementation. |
| New extension starting file `0x00800000`, bus `0x08800000` | Exactly the verified baseline EOF; bytes at/above this offset do not exist in either protected 8 MiB input. No existing source/file interval can be overwritten there. | **Confirmed static** non-overlap by construction; **Probable** overall compatibility for the restricted experiment. Recommended design below. |

`tomatoadv.asm:2` opens a Japanese input at bus base 0x08000000 and includes all
translation modules. It contains no explicit expansion command, dedicated script
reserve or expansion compatibility test. Existing `rb+`/seek/write inserter logic
and 32-bit pointer encoding can represent an extended file, but that is not a
validated translation expansion workflow. Do not rebuild the translation over the
English baseline. Existing patchers enforce an 8 MiB size and equal-length
comparison; a future expansion patcher needs separate, explicit validation rules.

The existing scripts/shared reward lie near file 0x00100000–0x00130000. Their
absolute pointers are evidence of addressing, not ownership of gaps between
scripts. No repository documentation reviewed here reserves event free space.

Two of the old scan's 68 values were further classified: file 0x0007A431 overlaps
`bge` at 0x0807A430 and `ldrb` at 0x0807A432; file 0x00093ACF overlaps `lsl` at
0x08093ACE and `ldrb` at 0x08093AD0. These are instruction-byte coincidences,
**confirmed static within those windows**, not pointer literals. The remaining
66 values have not all been classified. None of the retained 68 points into the
21-byte candidate at 0x007F1BE0, but that does not eliminate computed accesses.
The old scan is not a free-space certificate.

### Recommended controlled expansion design

Propose a **16 MiB (`0x01000000` byte)** output, with an explicitly owned wrapper
reservation of 0x20 bytes beginning at file `0x00800000` / bus `0x08800000`.
The 21-byte payload occupies `[0x00800000,0x00800015)`; the remainder of the
reservation and extension would be explicitly filled with FF. The pointer to the
payload encodes as `00 00 80 08`. This is an arithmetic allocation proposal at
the input EOF, **not a discovered original-game address or an inserted artifact**.

A 21-byte append would be smaller but produce a non-power-of-two cartridge image.
mGBA 0.10.5's `GBALoadROM` maps a normal 16 MiB file directly; for non-power-of-two
files it switches to a 32 MiB buffer and size, with different handling of the
unprovided tail. Its patch path also accepts changed output sizes up to cartridge
capacity. Choosing 16 MiB avoids the non-power-of-two loading branch. This is
source support, not an emulator test. [mGBA 0.10.5 ROM loader and patch code](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/gba.c#L371).

GBA's wait-state-0 ROM window spans 0x08000000–0x09FFFFFF, so 0x08800000 is
reachable without a bank switch. The GBA header has no ROM-size field, and its
complement checksum covers only bytes 0xA0–0xBC. Preserving the existing header
requires no checksum rewrite for an append or this script-pointer edit. The
baseline's stored/calculated complement both equal 0xC4 (196), as recorded in
the new audit. [GBATEK memory map and cartridge header](https://www.akkit.org/info/gbatek.htm#gbacartridgeheader).

For the wrapper's byte data reads, mGBA 0.10.5 indexes by cartridge offset and
checks it against loaded ROM size; expanded offset 0x00800000 is valid in the
proposed image. Appending nevertheless changes previously out-of-range reads to
defined data, and CPU fetch mapping uses a size-dependent mask. Thus expansion
must not be claimed globally behavior-neutral. This investigation does not prove
the entire game never computes such addresses. Use wait-state-0 addressing and
keep EEPROM accesses separate; no save-driver modification is part of the design.
[mGBA 0.10.5 memory implementation](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/memory.c#L602).

Pure expansion can preserve the complete baseline as an unchanged prefix. The
**functional Hanzo wrapper cannot**: it necessarily redirects the pointer at
file `[0x0010D69F,0x0010D6A3)`. A future verifier must compare the full 8 MiB
prefix with exactly that four-byte operation allowlisted (three bytes actually
change for this address), then separately verify the extension's payload and FF
fill. No other prefix byte, including the header, should differ. Retain source
hash, prefix hashes/comparison, appended range checks and final readback hash.

Actual flashcart/hardware compatibility, other emulator behavior and global
out-of-range accesses remain **untested/unconfirmed**. The design targets the
isolated mGBA experiment, not release or hardware certification. No existing
ROM/save/checkpoint is to be resized or rewritten.

### Scoped execution-context validation

New instruction observations substantiate the additional wrapper path, rather
than extrapolating from isolated handler signatures. Bus ranges are half-open;
file offsets subtract 0x08000000. Research function names identify roles, not
original symbols. Operand tables are FD at 0x0862B815, FE at 0x0862B736.

| Address / symbol | Supporting evidence and consequence | Status |
| --- | --- | --- |
| 0x08021F30–0x08021F70, interpreter | Calls decoder before dispatching FD or FE through their original tables. | **Confirmed static** |
| 0x08022388–0x08022510, decoder | Loads context cursor +4, reads header/arguments, writes argument cursor at 0x030039EC for argument-bearing commands, and stores post-command cursor at 0x080224D2. Does not write saved context +8. FD2F has four operands, so the original saved continuation is 0x0810D6A3. | **Confirmed static** data flow |
| 0x0806A00C–0x0806A01E → 0x0802F97C–0x0802F9A0 | Header/argument copying uses successive `ldrb`/`strb`, no 8 MiB masking or truncation of source pointer. | **Confirmed static** expanded script reachability |
| 0x08022874–0x080228F8, pointer reader | Reads four bytes from the decoded argument cursor; constructs full little-endian word and advances argument cursor. Native pointers' Thumb-bit convention does not apply to event data. | **Confirmed static**; no event-data alignment requirement in this path; proposed reservation is four-byte aligned for clarity |
| 0x08022534–0x0802256E, byte operand reader | FE53's 6B comes from 0x030039EC, established anew by decoder for its one argument. FE49's zero-argument decoder path does not need to prepare an operand cursor. | **Confirmed static** |
| 0x080252F4 → 0x08032BF0 → 0x08032CB8 | FE49 selects character 1 when membership bit 20 is absent. Full initializer through 0x08032E44 clears count and initial inventory bytes, loads default HP/level/clothing/other character fields, zeroes charge/ready, returns normally. It preserves the name. | **Confirmed static** initialization path; resulting live record **untested** |
| 0x08032D3A–0x08032DA4 → 0x08080424 | Selector 1 has zero upper nibble, so initialization also grants the default ordinary item from character-template byte +23. Alessa template is file 0x00630BF8 (bus 0x08630BF8), stride 0x1C; default item is 0A and count 1. It selects the ordinary inventory at 0x03001A70. | **Confirmed static** side effect; item name not established here |
| 0x08080424–0x0808054E → 0x0808064C–0x08080800 → 0x08080800–0x08080874 | Item insertion/ordering path uses ordinary inventory and utility/scratch fields. Mode 1 follows 0x080807A2, bypassing the mode-0 item-effect dispatch path. The scoped called helper 0x0802FEF0 is `bx lr`. No event context or task-selection store occurs in this mode-1 path. | **Confirmed static** added call chain; inventory's live capacity/ordering still **untested** |
| 0x08025624 → 0x0802927C → 0x0806ADA0–0x0806AE2A | Grants recipient 1 / ID 2B, appends three-byte entry, writes difficulty and zero upgrade, updates Gimmick usage bytes, fills an empty equipped slot. No call/return-context write. | **Confirmed static**; acquisition outcome **untested** |
| 0x0802A2F4 → 0x08022A84 and 0x080227F0 | FD0B masks selector with 7F and resolves it relative to 0x03003A24; it stores a decoded halfword. Thus 1A→0x03003A3E, 1C→0x03003A40; restoring 0083 and 001B restores shared-reward inputs without touching task context. | **Confirmed static** |
| 0x08124B33–0x08124BF2, original shared block | Command boundaries parsed using actual argument counts. No FD2F occurs in the bounded block; its FD30 transfers preserve the saved return slot. Final FD7C remains at 0x08124BF0. | **Confirmed static** script structure; notification/worker behavior is inherited, **untested** here |
| 0x0802900C–0x080290CA and 0x080290E4–0x08029122 | Shared FE00 registers a child through 0x0806AAA0 and links cursors/worker fields; FE16 waits by rewinding +4 when work remains. Their direct bodies do not overwrite caller +8. | **Confirmed static** direct bodies; complete registration/worker lifecycle not newly certified |

The added FE49/FE53/FD0B path uses normal interpreter dispatch and returns
synchronously. Its scoped stores target character/general inventory, Gimmick usage,
utility arguments and scratch stack; they do not replace Hanzo's saved return
cursor, return bit or active task selection. The original shared reward receives
its original parameters after these handlers. Accordingly, **preservation of the
original call/return design is supported statically**, while scheduler interleaving,
notification animation, derived party refresh and gameplay remain **untested**.
No native handler was called directly or game instruction executed in this work.

State limits: the protected checkpoint gives membership 10, Alessa's initialized
name, empty inventory/equipment slots and difficulty 1. Its ordinary inventory
prefix is `01 01 01 00 ...` (one entry), consistent with space for the default
item; this is a saved snapshot, not proof of the state at wrapper dispatch. Earlier
Hanzo commands still execute before the wrapper. FE49 is not an idempotent
"ensure Alessa" operation: if Alessa is already present, it can initialize another
companion. Testing must start from the specified fresh checkpoint and stop on any
unexpected membership. Alessa equipment slots are already zero in that snapshot;
the initializer does not indiscriminately clear every byte of the 0x60-byte record.
Pop Horn acquisition will use the game's empty-slot logic. No robot flag or AWE
tutorial state is synthesized.

### Recommendation and authorization boundary

**Recommend the explicitly reserved 16 MiB expansion at file 0x00800000 rather
than reclaiming the in-ROM tail.** Allocation non-overlap and interpreter addressing
are **confirmed static**. Whole-experiment correctness is **probable**, and runtime
success is **untested**. This is sufficient static evidence to separately authorize
construction of this isolated experimental design, with the prefix-edit exception
and expansion verification rules above. It is not evidence for a normal-play ROM,
coherent pre-Oystown state or hardware release.

If an absolutely unchanged baseline prefix is required in the final runnable ROM,
construction is **not** possible with the proposed Hanzo pointer-redirection method;
that requirement must allow the documented pointer operation. If a same-size ROM
is required instead, construction remains **not ready**: residual translation
allocation ownership/computed references in the in-ROM tail are still unresolved.

No patch construction is authorized by this investigation. Work ends here; a
separate user instruction is required before implementation. Pending runtime
questions must remain recorded as such, not silently converted to confirmation.

Checkpoint compatibility detail: in mGBA 0.10.5, a CRC mismatch logs a different-
version warning rather than by itself making state loading fail; game-title/ID
mismatch and other invalid state checks are fatal. Expansion and the pointer edit
change CRC. Never edit the checkpoint header or treat a genuine title/ID mismatch
as expected. A CRC-only warning would need to be distinguished from other errors
in the later manual test instructions. Actual loading is **untested**.
[mGBA 0.10.5 deserialization checks](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/serialize.c#L77).

Verification: all **79** protected files in the retained preflight manifest matched
their recorded hashes before and after the new analysis. New JSON records scoped
window hashes/disassembly, command boundaries/argument sizes, header complement
and expansion arithmetic. No ROM, save, state or prior JSON was modified. Changed
files: this report; new `tools/analyze/alessa_wrapper_allocation.py`; new
`reverse_engineering/experiments/alessa_wrapper_allocation.json`.

## Authorized construction results (2026-10-13)

**Confirmed offline:** the exact authorized wrapper was inserted into a new 16 MiB
ROM, and only the Hanzo pointer operation affects the existing 8 MiB prefix.
**Runtime: untested.** No mGBA process was launched or controlled; no save/state
was created, loaded, copied or modified by this construction. The user separately
authorized this implementation after reviewing the allocation investigation.

### Artifacts and reproduction

- Script: [tools/patch/alessa_recruitment_wrapper.py](../../tools/patch/alessa_recruitment_wrapper.py).
- Regression checks: [tests/test_alessa_recruitment_wrapper.py](../../tests/test_alessa_recruitment_wrapper.py).
- ROM: `tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f/alessa_recruitment_wrapper.gba`.
- Manifest: [manifest.json](../../tools/patch/output/alessa-recruitment-wrapper-38386dab64e249cb9dfb4b205620053f/manifest.json).

Reproduce from the root: `python -B tools/patch/alessa_recruitment_wrapper.py`.
Each run uses a fresh UUID directory. Optional `--output-name NAME` accepts only
a simple directory name and refuses an existing directory, including this one.
The ROM bytes are deterministic; directory paths affect manifest metadata only.
Failed construction/readback can leave an unverified fresh directory; it is never
reused or silently overwritten. Do not rerun translation assembly/insertion.

| Artifact | SHA-256 |
| --- | --- |
| English input (8,388,608 bytes) | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Experimental output (16,777,216 bytes) | `3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6` |
| Output's first 8 MiB, with allowed pointer edit | `e9d9e90e008e2c9981986515682f5ff92297e3bbd5b09d9db19f201e1ce34eeb` |
| Appended 8 MiB | `4c17dc160931c2d5edbf952fe2a108b0112f9d04c49548ef2c798a6893b6cd90` |

### Exact operations and complete comparison

All ranges are file offsets, half-open unless explicitly noted.

| Range / address | Original / replacement | Verified result |
| --- | --- | --- |
| Call at file 0x0010D69D / bus 0x0810D69D | `FD 2F 33 4B 12 08` → `FD 2F 00 00 80 08` | Original FD2F remains intact. |
| Pointer operation `[0x0010D69F,0x0010D6A3)` | `33 4B 12 08` → `00 00 80 08` | Full 32-bit little-endian pointer to 0x08800000. |
| Payload `[0x00800000,0x00800015)` / bus 0x08800000 | Newly appended 21 bytes | Exact payload below. |
| Padding `[0x00800015,0x01000000)` | Newly appended 8,388,587 bytes | Every byte equals FF, including remaining 11 bytes of the 0x20-byte reservation. |

Exact inserted payload:

```text
FE 49 FE 53 6B FD 0B 1A 83 00 FD 0B 1C 1B 00 FD 30 33 4B 12 08
```

Actual existing-prefix differences are **three bytes**, separately from the
**8,388,608 newly appended bytes**:

| File offset | Before | After |
| --- | --- | --- |
| 0x0010D69F | 33 | 00 |
| 0x0010D6A0 | 4B | 00 |
| 0x0010D6A1 | 12 | 80 |

File 0x0010D6A2 remains 08. The entire prefix was compared, not only patch sites.
The original header and shared reward block `[0x00124B33,0x00124BF2)` remain
unchanged. Every appended byte was checked against either the approved payload or
FF padding. The script verifies its in-memory construction, re-reads the written
ROM, repeats the full comparison, records prefix/extension hashes, and re-reads
the manifest. A separate inline verifier independently repeated the full prefix
comparison, payload/padding validation, output/hash/manifest checks and evidence
fingerprints. **All passed; no unintended differences.**

All 27 recorded allocation instruction-window hashes matched the baseline before
construction. The allocation's size, EOF reservation, bus address and encoded
pointer matched the approved design. The manifest records both existing evidence
JSON hashes and the patch script hash. No changes to those evidence artifacts or
translation ASM/C++ sources were needed.

### Integrity and rejection validation

All **79 pre-existing protected ROM/save/checkpoint files** matched retained
preflight hashes and retained identical before/after hashes. The manifest includes
the full path/hash inventories. A final independent check also passed for all 79.
The new ROM is the only additional runtime artifact and is separate from the
Gear-Yo, Dojo Pup and Mayonen music experiments. Original Japanese, English and
root checkpoint hashes remain those listed above in the original preflight.

Command: `python -B -m unittest discover -s tests -p test_alessa_recruitment_wrapper.py`.
**Four tests passed**, covering approved layout/counts, changed-baseline rejection,
corruption of prefix/call/pointer/payload/first and last padding bytes, truncated
output rejection, existing-destination rejection with a preserved sentinel, and
path traversal/absolute-path rejection. These checks build buffers only; collision
checks use temporary text files, never ROM or state writes. Runtime correctness
is outside their scope.

### Manual mGBA 0.10.5 procedure

The user performs every step. These instructions supersede the earlier deferred
plan's broad mismatch stop rule: a CRC-only version warning is expected for this
patched/expanded ROM; an actual game-title/ID mismatch is not expected.

1. Create a fresh portable mGBA 0.10.5 folder with independent empty `saves`,
   `states`, `patches`, `cheats`, `screenshots` and `logs` directories. Use a copied
   executable/support files and a new `portable.ini`; do not use the old Oystown
   launcher, which opens the baseline. Configure `[mgba]` in its local `config.ini`
   with `loadStateExtdata=9`, `saveStateExtdata=9`, `rewindEnable=0` and explicit
   `savegamePath`, `savestatePath`, `patchPath`, `cheatsPath`, `screenshotPath`
   directed into this fresh environment. Match the checkpoint's existing HLE BIOS
   settings (`useBios=0`, `skipBios=1`). Verify the paths before testing.
2. Copy the new experimental ROM and **a disposable copy** of root `entry-stop.ss0`
   into the fresh environment. Verify the copied ROM's SHA-256 against the output
   above and the copied checkpoint against
   `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29`.
   Open only these copies, pause before loading the state, and load the working
   checkpoint. Record any warning. A CRC-only different-version warning is
   expected; stop on state rejection, title/ID mismatch, BIOS mismatch or other
   unexpected errors. Never alter the checkpoint's identity fields.
3. Resume normal gameplay and complete Hanzo's first reward interaction. Confirm
   normal dialogue/event completion, Alessa joining and DeMille receiving Erupter.
   Stop immediately on freeze, dialogue corruption, abnormal return or unexpected
   party/equipment behavior. Pause after event completion.
4. Perform **only this first debugger action**, then report the exact result and
   visible party/event outcome: `r/1 0x03001AB4`. Prediction: **0x31**, compared
   with the protected checkpoint's/user-confirmed initial 0x10. Do not edit RAM.
   If unexpected, stop before further gameplay or reads. Subsequent precise reads
   will be requested one at a time after this observation is reviewed.
5. After the membership observation is reviewed, validate both characters and
   their inventories/equipment in menus. Check Pop Horn for Alessa and Gear-Yo/
   Erupter for DeMille, ordinary movement, and a normal battle recognizing both
   characters. Test Pop Horn when usable. Stop on any inconsistent count, entry,
   equipment, menu or battle state; preserve observations in new files only.

Expected later read locations (static predictions; **not extra debugger actions
to execute now**):

| RAM address | Prediction / purpose |
| --- | --- |
| 0x030035F0 | Derived party count 2 after normal refresh. |
| 0x03001F3C | Alessa's 0x60-byte persistent record; name/stats/equipment require coherent inspection. |
| 0x03001F43 | Alessa Gimmick count 1. |
| 0x03001F44–0x03001F46 | Pop Horn entry `2B 01 00`. |
| 0x03001EE3 | DeMille Gimmick count 2 for the specified starting state. |
| 0x03001EE4–0x03001EE9 | Expected Gear-Yo `01 01 00`, then Erupter `1B 01 00`. |
| 0x03001F96–0x03001F99 | Alessa equipment slots; normal grant should fill an empty slot with 2B. |

### Remaining risks and stop boundary

Handler/context support remains **confirmed static**, overall gameplay behavior
**probable**, and recruitment, inventory, equipment, event return, movement and
battle results **untested**. Expansion changes previously out-of-range accesses;
global game/hardware compatibility has not been certified. Recruitment also grants
the default ordinary item 0A through the normal initializer. FE49 is not idempotent:
use the specified DeMille-only fresh checkpoint, do not replay the wrapper or
Alessa's original recruitment scene, and do not promote this as a story-consistent
save or normal-play ROM. AWE/progression/Binky work is excluded.

Construction and offline verification are complete. Work stops here pending the
user's manual observations; no further experiment or emulator operation follows.

## User-confirmed runtime validation (reported 2026-10-13)

The user explicitly supplied these observations in the AWE-investigation request.
They supersede the earlier runtime-untested status **for this tested scenario**.
Codex did not operate the emulator. No new screenshots, console transcript files,
post-battle state or battery-save round-trip were independently inspected here.

Test ROM SHA-256:
`3bba82ba6c581ca598aea1e21ecd654b41418f946e88ea6c5021d89b0357d7c6`.
The ROM and its existing isolated testing environment are protected and unchanged.

| Observation | User result | Confidence |
| --- | --- | --- |
| Alessa appears in party | Confirmed by user | User-confirmed runtime |
| Membership 0x03001AB4 | 31 | User-confirmed runtime |
| Alessa inventory count 0x03001F43 | 01 | User-confirmed runtime |
| Entry ID at 0x03001F44 | 2B | User-confirmed runtime |
| Entry difficulty at 0x03001F45 | 01 | User-confirmed runtime |
| Entry upgrade at 0x03001F46 | 00 | User-confirmed runtime |
| DeMille reward | Erupter received | User-confirmed runtime |
| Hanzo event return | Finished without apparent problems | User-confirmed runtime |
| Party menus | Both characters appeared | User-confirmed runtime |
| Movement | Normal movement worked | User-confirmed runtime |
| Ordinary battle | Both characters appeared; Gimmicks worked correctly; battle ended normally | User-confirmed runtime |
| Subsequent story | Progression continued | User-confirmed runtime, scope limited to reported continuation |

Complete Pop Horn entry `2B 01 00` matches the predicted acquisition structure.
The recruitment mechanism, return behavior and ordinary battle initialization are
validated for the tested scenario. This does **not** establish long-term saving/
reloading, every recruitment state, complete pre-Oystown prerequisites, or AWE
charge/eligibility/use. No AWE measurements were supplied with these results.
Future AWE research is separate: [awe_initialization.md](../awe_initialization.md).
