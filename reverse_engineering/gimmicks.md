# Gimmick Record and Consumer Investigation

## Runtime-confirmed subtraction GY-SUB-16 (2026-10-11)

Evidence: user's manual mGBA report, interpreted against the bounded Thumb disassembly. At `0x08048794`, `sub r1,r1,r0`, r1 was `0x1A` (26), r0 was `0x0A` (10); stepping produced r1=`0x10` (16). At `0x08048796`, `strh r1,[r2,#0]`, r2 was `0x03000BF8`; stepping stored `0x0010`. Subtraction, intermediate result and scratch write are **Confirmed (runtime)** for this Gear-Yo replay. The previously confirmed HP write at `0x08046E02` changed target HP `0x03000A4E` from 24 to 8, a reduction of 16. These are successive user-reported experiments, not a newly supplied continuous console transcript.

The captured battle pre-subtraction value equals the independently confirmed displayed Attack 26. The measured arithmetic is `26 - 10 = 16`; call the 10-point operand **target subtraction quantity**, not Defense. Individual source-field values were not reported. No minigame or RNG modifier is confirmed by this equality. Source tracing and the remaining conditional modifiers are documented in [battle_damage_candidates.md](battle_damage_candidates.md).

## Runtime-confirmed battle damage (2026-10-11)

User-reported manual mGBA evidence confirms `0x080485B0` output `0x03000BF8=16` is applied by `0x08046E02` to target HP `0x03000A4E`: r1=8, one `strh` changes HP 24?8. This confirms the tested Gear-Yo damage path, separately from menu Attack 26. It does not confirm why the intermediate arithmetic yields 16.

Static direct record dependencies are +0x22, the selected even coefficient among +0x28..+0x38, and +0x27 bit 7. Battle action selector/additive/auxiliary bytes are separate inputs with unresolved writers and gameplay meanings. Target +0x14/+0x18 subtraction, optional 80/70% scaling and clamps are decoded; defence/performance meanings remain Candidate. No identified random-number source supports an RNG claim. See [battle_damage_candidates.md](battle_damage_candidates.md) and [gimmick_runtime_tests.md](gimmick_runtime_tests.md).

## Battle-side recomputation candidate (2026-10-11)

The user's confirmed baseline values at copied base `0x03003F56`, coefficient `0x03003F9D` and Gear-Yo state triple did not produce a read-watchpoint hit at `0x03003F9D` during the reported replay. BIOS stop `0x00000188` was not a hit. This negative observation is recorded in [gimmick_runtime_tests.md](gimmick_runtime_tests.md).

Bounded Ghidra disassembly now establishes a **static** path from original record +0x22 and selected even coefficients into scratch `0x03000BF8` in routine `0x080485B0`, then through caller `0x08046D60` to subtraction/store of a target halfword at `0x08046E02`. The action-record selector can receive a +2 adjustment, and target quantities/flags influence the result. This differs from simply transferring the menu Attack output. For the tested Gear-Yo action, damage output and target +0x0E current HP are now **Confirmed (runtime)**: scratch 16 was subtracted from HP 24, producing 8 at `0x08046E02`. Subtraction 26 minus 10 and scratch store 16 are now runtime-confirmed; branch conditions remain unmeasured. Work +0x69 has a confirmed display-oriented reader at `0x0802BA3A`; its timing and any additional aliases/copies remain unresolved. See [battle_damage_candidates.md](battle_damage_candidates.md) for exact instructions and formulas.

The next manual targets are `0x080485B0`, `0x08046DEA`, and `0x08046E02`, activated sequentially. No game instructions, ROMs or checkpoints were changed, and the successful Gear-Yo menu result is not generalized into a universal battle formula.

## Gear-Yo live confirmation (2026-10-11)

**Confirmed (runtime), tested case only:** the user reports a successful manual mGBA 0.10.5 experiment for Gear-Yo at difficulty 1 and upgrade 0. In Thumb routine `0x08075970`, r0 was `0x1A` (26) at `0x08075ABC` immediately before `strh r0,[r7,#10]`. At `0x08075AE8`, output `P=0x02014CF8`, halfword `P+0x0A=0x02014D02` was `0x001A`. Base 21 and selected coefficient 124 give `floor((21+0)*124/100)=26`, matching displayed Attack. The reported read `0x000A` at P+0 is a separate field, not Attack.

This confirms this Gear-Yo calculation and stored/displayed result. It does not promote every original +0x22 byte, every even coefficient, nonzero upgrade behavior or other Gimmicks to runtime-confirmed gameplay meanings. Battle damage, HP updates, RNG, AWE and Kaizo remain Unconfirmed. The evidence is the user's explicit live report, not direct agent/emulator control; full entry registers/caller and a new transcript were not supplied. Details are in [gimmick_runtime_tests.md](gimmick_runtime_tests.md#completed-live-test-gy-d1-u0-2026-10-11).

Battle-checkpoint reinspection shows matching Gear-Yo non-text bytes in work record `0x03003F34`, copied base 21 at `0x03003F56`, and selected coefficient 124 at derived work +0x69 (`0x03003F9D`). These are Confirmed checkpoint contents, not an established battle consumer. The read watchpoint subsequently returned a negative result; the new instruction targets above replace that primary strategy. No ROM, checkpoint or gameplay code was changed.

## Calculation and consumer follow-up (2026-10-10)

[gimmick_calculations.md](gimmick_calculations.md) adds a complete 136-instruction Thumb trace of `0x08075970`, seven verified direct callers, output-buffer consumers, and mutable-state writers. The useful result is a 17-byte caller-supplied structure, typically at `read32(0x03004FF8+8)+0x5AE8`; r0 contains the popped return address on exit, not an attack result.

- **Confirmed static:** `+0x22 + S[2]` forms output halfword `+8`, and `floor((+0x22 + S[2]) * R[0x28+2*(S[1]-1)] / 100)` forms `+0x0A` for selector 1..9. The decoded callers render these values in the Attack section. Base Attack and difficulty-adjusted Attack are now **Probable** interpretations; battle damage remains **Unconfirmed**.
- **Confirmed static:** routine `0x08079AE4` adjusts the selected party Gimmick entry's S[1] with input masks `0x100/0x200`, ordinarily within 1..7, and redraws it. Help descriptors explicitly instruct L/R difficulty adjustment. S[1] as difficulty and the even pair bytes as difficulty-specific Attack percentages are **Probable**. Arithmetic cases 8/9 do not establish nine user-selectable settings.
- **Confirmed static:** routine `0x08081188` increases S[2] and caps the truncated byte at original record `+0x23`; item dispatcher `0x08080C84` passes item byte `+9`, then can recompute the menu result. Output S[2]/`+0x23` supplies Battery numbers and a ratio gauge. Battery/upgrade current value and capacity are **Probable**, strengthening the legacy `maxBattery` guess without claiming a damage maximum or AWE relation.
- **Confirmed static:** result values reach decimal sprite/OAM output and ratio/meter tile DMA paths. No traced path reaches a battle HP write, defence formula, random multiplier, AWE change, or Kaizo threshold. Odd pair bytes retain their prior loader-only interpretation.
- **Confirmed binary:** the calculation envelope, lookup, selector writer and additive-state writer match the supplied English ROM in the explicitly compared ranges. The earlier loader `+0x27` load difference remains separate.

Next: mGBA should correlate the recovered output fields with the displayed values during difficulty adjustment and one powerup, then capture battle-time readers of the same original/state fields. The linked report records exact trace stops and addresses; no runtime experiment or gameplay modification has been performed.

## Ghidra static follow-up (2026-10-10)

See [ghidra_analysis.md](ghidra_analysis.md) for the isolated read-only workflow and [ghidra_loader_trace.md](ghidra_loader_trace.md) for complete instruction evidence, caller context and limitations. Older source-only statements below are historical; this follow-up adds Japanese-ROM static evidence, with no emulator/gameplay confirmation.

- **Confirmed static:** complete Thumb loader at `0x08065518` returns at `0x080656C0`; embedded literals at `0x080655D4..E3` are data. The original byte load at `0x0806556A`, copied work base `0x03003F34`, biased table base `0x0862C1F8`, stride `0x58`, and retained continuation operations are independently decoded by Ghidra.
- **Confirmed static:** routine `0x0806ACA0` calls the loader at `0x0806ACFE`, supplying bytes from utility `+1/+5/+4` into `0x03001AD2/+1/+2`. Raw BL scanning found this one direct Thumb encoding; indirect/ARM callers remain unmapped.
- **Confirmed static:** `+0x25` is masked/shifted as previously observed. Selector-derived offset passes through a byte store, so pair lookup uses `((selector-1)*2)&0xFF`. The second pair byte is decoded as two nibbles for low-nibble group 1/2 of `+0x27`, otherwise low seven bits and zero. Gameplay meanings remain Unconfirmed.
- **Confirmed static:** `+0x3C` is a byte-stream pointer: its leading byte goes to work `+0x6B`, subsequent nonzero bytes are copied at work `+0x73`, and later selection uses nine-byte stepping. A grouped-data interpretation is Candidate; no text/effect/minigame-script identity is confirmed. Other pointer-tail consumers remain unidentified in the scoped functions.
- **Confirmed static:** separate routine `0x08075970` reads `+0x23` into output halfword `+6`, adds `+0x22` to a state-record byte into output halfword `+8`, and multiplies that intermediate by one of nine even bytes `+0x28/+0x2A/.../+0x38`, divides by 100, then stores output halfword `+0x0A`. The nine-case selector originates in the state record returned by `0x0807565C`. These establish an additive operand and percent-style coefficients; base power, battle damage, difficulty and Kaizo semantics remain Candidate/Unconfirmed.
- **Confirmed static:** accessor `0x080754B0` reads low nibble of original `+0x27`; the arithmetic routine separately reads bit 7 into output byte `+0x0F`. No flag meaning is assigned.

Most useful next step: trace `0x08075970`'s output into its callers and correlate it in mGBA with visible values. Compare original and English `+0x27` loads at runtime; the translation's word-load difference is source-consistent but its hardware effect remains unverified. Both ROMs and translation source are preserved.

## Scope and confidence

Phase 1, 2026-10-09. The initial source investigation below read the translation repository. The subsequent binary verification section records read-only inspection of both supplied ROMs. No build, dumper, assembler, emulator, or gameplay patch was run. Source paths below are relative to `tomatotrans-1.1.1/`.

**Confirmed** means an explicit source operation or manifest layout; it does not confirm the running game's behavior. **Probable** indicates an interpretation supported by operations and comments. **Candidate** preserves an upstream hypothesis. **Unconfirmed** indicates unidentified data or missing evidence. Every gameplay interpretation still needs binary analysis and runtime verification.

The repository provides a partial replacement of one loader and several text consumers. It does **not** provide the loader's entire original body, damage calculation, difficulty selection, RNG, or a complete Gimmick implementation. Unnamed routines below remain identified by their existing addresses; no new function symbols are assigned.

## Binary verification follow-up

See [rom_verification.md](rom_verification.md) for input paths, full SHA-256 hashes, exact byte dumps, ASM comparisons and limited Thumb instruction listings; [data/gimmick_raw_fields.csv](data/gimmick_raw_fields.csv) contains 50 records per ROM with all 54 non-text bytes. Both files were found in the workspace root by recursive discovery, and each is 8,388,608 bytes. Binary facts apply to those fingerprinted inputs, not an arbitrary ROM revision.

- All 50 supported records are present at the expected offsets. Their text bytes `+0x00`–`+0x21` are identical between inputs. Forty-nine complete records match; the remaining record differs at only three bytes.
- Choo-Choo index `0x1D`, field `+0x44`, has Japanese bytes `1C 7A 57 08` and English bytes `B0 AF 68 08` at file `0x0062CC8C` / bus `0x0862CC8C`: pointer `0x08577A1C` becomes `0x0868AFB0`. All other original-record bytes are unchanged. This is Confirmed binary evidence of graphics relocation, not a power/difficulty edit.
- Both pointed-to streams begin `30 00 30 00`, an RLE header declaring `0x3000` decoded bytes. The Japanese stream consumes 5,049 encoded bytes; the English stream consumes 6,955 through its final packet, exceeding the source's original budget. Its final run nominally extends 69 bytes beyond the declared decoded size. This is a Confirmed packet-length observation consistent with the upstream encoder defect; runtime decompressor behavior remains unverified.
- Literal slots at file `0x000655D4`, `0x000655D8`, `0x000655DC`, `0x000655E0` contain `0x030018BC`, `0x03001AD2`, `0x0862C1F8`, `0x03003F34` in **both** inputs. Their values, previously comment-described, are now Confirmed binary reads. RAM-derived addresses below therefore have verified bases for these ROMs.
- The retained region file `[0x0006556C,0x000656B8)` is byte-identical, including its four literal words. The patched prefix and epilogue differ as expected. Seventy-seven bounded checks derived from `asm/gimmick_text.asm` match; no checked mismatch was found. One symbolic helper call's placement remains unverified. This is local agreement, not proof of full build provenance.
- Japanese file `0x0006556A` contains `01 78`, a byte load at copied-record `+0x27`; English file `0x00065564` contains `01 68`, a word load at the same unaligned address, matching ASM line 132. Hardware/runtime handling still needs independent verification.
- Limited instruction inspection of the shared continuation shows low-bit group extraction, an indexed two-byte lookup starting at copied-record `+0x28`, and a word dereference from `+0x3C`. Exact instruction evidence is in the report. This strengthens access/type evidence, but does not identify difficulty, power, character restrictions or Kaizo meanings.

No ARM-capable installed disassembler was found on the checked PATH/workspace/import paths. Available GNU objdump 2.43.1 advertises x86/iamcu, not ARM. The local Python Thumb inspector is a bounded analysis helper and has not replaced the need for an independent ARMv4T/Thumb disassembler and GBA debugger. No tooling was installed.

## Table references, count and index conventions

| Source | Evidence | Conclusion / confidence |
| --- | --- | --- |
| `asm/gimmick_text.asm:1-23` | Original base `0x0862C250`, stride `0x58`, and a commented “Original struct guesses” declaration. | Confirmed stated layout; non-text field meanings are Candidate. |
| `asm/gimmick_text.asm:83-96` | Reads an ID byte, multiplies by `0x58`, loads a biased base from a literal, calls `0x080F954C` with copy size `0x58`. | Confirmed patched instructions; Probable original-table loader, subject to checking literal contents. |
| `ta_menus_eng.txt:1303,1355` | `RESTRUCT 62C250 08 58 7F001E 10 40 32` and `RESTRUCT 62C258 1A 58 7F002E 30 40 32`. | Confirmed: 50 name/description entries, because count `32` is hexadecimal. |
| `ta_menus_jpn.txt:1279,1331` | Same record bases/counts/strides in the Japanese reference manifest. | Corroborating reference layout; it is not an inserter input. |
| `dumper2.c:229-235` | Legacy extraction loop `i < 0x32`; name length 8, description length 26, stride 88. | Corroborates 50 supported records; legacy code was not executed. |
| `inserter/text.cpp:1221-1256` | Parses hexadecimal RESTRUCT operands and writes each text field at the specified translated destination/stride. | Confirmed inserter behavior; no gameplay-field decoding. |
| `inserter/images.cpp:754-786` | `InsertChooChooAnimationTiles` supplies relocation pointer slot file `0x0062CC8C`, inside record index `0x1D` at offset `+0x44`. | Confirmed source pointer-write site; supports Choo-Choo graphics-pointer role. |
| `ta_menus_eng.txt:206-256` | Separate menu name block has the same 50 names in identical order. | Confirmed translation ordering; descriptor at bus `0x08490420`, file `0x00490420`. |

The supported table covers **50 records**, indices `0x00`–`0x31`. The computed span is bus `[0x0862C250, 0x0862D380)`, file `[0x0062C250, 0x0062D380)`, length `0x1130`. Last record starts at bus `0x0862D328` / file `0x0062D328`. These are derived source extents, not a verified physical table boundary; the repository alone cannot exclude additional unused records.

For zero-based record index `i`, the original location is `0x0862C250 + i*0x58`. In the loader and obtained-item formatter, the expected ID is `g = i+1`, yielding IDs `0x01`–`0x32`. The loader uses the comment-described biased literal `0x0862C250-0x58` and the formatter subtracts one translated stride. There is no visible loader range check establishing validity for ID 0 or IDs beyond 50. Other event/inventory conventions require separate verification.

The full 50-name mapping and derived record addresses are in [symbols.md](symbols.md#gimmick-nameindex-catalogue). Examples: index `00` / loader ID `01` is Gear-Yo; `0B` / `0C` is SlotZooka; `29` / `2A` is Lucky Cat; `31` / `32` is Shadowreel. These are Confirmed English-manifest names with Probable runtime associations. No Kaizo/Hanzo ownership or character restriction is derived from this ordering.

## Original `0x58`-byte field map

Offsets below refer to an **original ROM record**, not translated text slots or the extended RAM work structure. Intervals are inclusive here. Candidate subdivisions follow the upstream guessed struct; they are not recovered binary types. Together the rows cover all 88 bytes with no gaps.

| Record offset | Bytes | Suspected type | Interpretation | Supporting source evidence | Confidence | Runtime verification needed? |
| --- | --- | --- | --- | --- | --- | --- |
| `0x00`–`0x07` | 8 | Encoded text array | Original embedded name. Copied to a separate 16-byte translated name slot. | `asm/gimmick_text.asm:2,6`; English RESTRUCT line 1303; `dumper2.c:232-233`. | Confirmed source layout | Yes: ROM bytes, encoding and runtime ID association. |
| `0x08`–`0x21` | 26 | Encoded text array | Original description/instructions. Separate translated slot is 48 bytes. | `asm/gimmick_text.asm:2,7`; English RESTRUCT line 1355; `dumper2.c:234`. | Confirmed source layout | Yes: ROM bytes and all consumer paths. |
| `0x22` | 1 | Candidate `uint8_t` | Upstream calls it `atk`. Possible power-related byte; base-power versus maximum-power meaning is unknown. No visible read ties it to damage. | `asm/gimmick_text.asm:8`; included only in whole-record copy at lines 89-96. | Candidate | Yes: find consumers and damage data flow. |
| `0x23` | 1 | Candidate `uint8_t` | Upstream `maxBattery`. Battery meaning and relation to uses, power or AWE are unestablished. | `asm/gimmick_text.asm:9`; bulk copy only. | Candidate | Yes: trace consumers; do not equate this with AWE. |
| `0x24` | 1 | Unknown byte | Upstream `unk24`; no individual field consumer visible. | `asm/gimmick_text.asm:10`; bulk copy only. | Unconfirmed | Yes. |
| `0x25` | 1 | Unsigned byte, possible packed bits | Explicit byte read; low seven bits stored in extended work byte `+0x70`; shifted value stored at `+0x6F`. Upstream calls it `uses`; its high bit and gameplay meaning are unresolved. | `asm/gimmick_text.asm:11,117-128`. | Confirmed byte/mask operations; Probable uses interpretation | Yes: trace downstream reads and usage depletion. |
| `0x26` | 1 | Unknown byte | Upstream `unk26`; no separate byte access visible. | `asm/gimmick_text.asm:12`; bulk copy only. | Unconfirmed | Yes. |
| `0x27` | 1 | Byte with bit-group consumers; meanings unknown | Upstream `flags`. Japanese loader byte-loads it; English word-loads at the unaligned address. Shared continuation masks low four incoming bits and extracts low-byte bits 4–5; neither group is assigned a gameplay meaning. No four-byte field is established here. | `asm/gimmick_text.asm:13,130-133`; binary file `0x0006556A` / `0x00065564`; `rom_verification.md` continuation listing. | Confirmed byte/load encodings; Probable bit-field access; meanings Candidate | Yes: independent disassembly and alignment/runtime behavior. |
| `0x28`–`0x29` | 2 | Indexed byte pair | Guessed `levels[0].d0/d1`; binary continuation reads from copied base +0x28 with a two-byte selector stride. Nine entries/difficulty interpretation still unconfirmed. | `asm/gimmick_text.asm:14`; binary file `0x0006558C`–`0x000655B0`, instruction listing in report. | Confirmed bytes; Probable indexed-pair access; gameplay meaning Unconfirmed | Yes: identify selector callers and valid range. |
| `0x2A`–`0x2B` | 2 | Candidate pair of bytes | Guessed `levels[1]`; no level-selection consumer visible. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x2C`–`0x2D` | 2 | Candidate pair of bytes | Guessed `levels[2]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x2E`–`0x2F` | 2 | Candidate pair of bytes | Guessed `levels[3]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x30`–`0x31` | 2 | Candidate pair of bytes | Guessed `levels[4]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x32`–`0x33` | 2 | Candidate pair of bytes | Guessed `levels[5]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x34`–`0x35` | 2 | Candidate pair of bytes | Guessed `levels[6]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x36`–`0x37` | 2 | Candidate pair of bytes | Guessed `levels[7]`; no identified formula. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x38`–`0x39` | 2 | Candidate pair of bytes | Guessed `levels[8]`; nine guessed entries do not establish nine difficulty settings. | `asm/gimmick_text.asm:14`. | Candidate | Yes. |
| `0x3A` | 1 | Unknown byte | Upstream `unk3a`. | `asm/gimmick_text.asm:15`; bulk copy only. | Unconfirmed | Yes. |
| `0x3B` | 1 | Unknown byte | Upstream `unk3b`. | `asm/gimmick_text.asm:16`; bulk copy only. | Unconfirmed | Yes. |
| `0x3C`–`0x3F` | 4 | 32-bit address used for a byte read | Upstream `void *unk3c`; binary continuation loads this word from the copied work record and dereferences it. CSV records exact values; target data meaning is unidentified. | `asm/gimmick_text.asm:17`; ROM bytes `D0 6B` at file `0x000655FE`, `03 78` at `0x00065602`; report confirms literal work base. | Confirmed word/dereference instruction bytes; Probable pointer role; meaning Unconfirmed | Yes: inspect referenced structures and downstream copies. |
| `0x40`–`0x43` | 4 | Candidate graphics pointer | Upstream `somePalette`; not verified by image insertion code. | `asm/gimmick_text.asm:18`. | Candidate | Yes. |
| `0x44`–`0x47` | 4 | ROM bus pointer for Choo-Choo; candidate same type elsewhere | Upstream `someImage`; Choo-Choo image inserter may write a relocated 16-color compressed tileset bus pointer here. Establishes an intended graphics reference for index `0x1D`, not every entry's target/type. | `asm/gimmick_text.asm:19`; `inserter/images.cpp:754-786,167-180,92-96`; `ta_menus_eng.txt:1333`. | Confirmed Choo-Choo pointer-write site; Probable graphics role/general field | Yes: original pointer, decoder, other entries and live consumer. |
| `0x48`–`0x4B` | 4 | Candidate pointer to pointer data | Upstream `void **unk48`; not established as code, script, effect or RNG data. | `asm/gimmick_text.asm:20`. | Candidate type; meaning Unconfirmed | Yes. |
| `0x4C`–`0x4F` | 4 | Candidate pointer to pointer data | Upstream `void **unk4c`; target unknown. | `asm/gimmick_text.asm:21`. | Candidate type; meaning Unconfirmed | Yes. |
| `0x50`–`0x53` | 4 | Candidate pointer | Upstream `void *unk50`; target unknown. | `asm/gimmick_text.asm:22`. | Candidate type; meaning Unconfirmed | Yes. |
| `0x54`–`0x57` | 4 | Candidate pointer | Upstream `void *unk54`; target unknown. | `asm/gimmick_text.asm:23`. | Candidate type; meaning Unconfirmed | Yes. |

There is **no confirmed numerical gameplay interpretation** for any byte in `0x22`–`0x57`. Binary evidence strengthens pointer/lookup access descriptions; confirming a mask, address or copy operation is narrower than confirming what it means in battle.

## Loader trace: routine at `0x08065518`

ROM bus entry `0x08065518` corresponds to file offset `0x00065518`. It has no `.func` name in this repository. Only its prefix `[0x08065518,0x0806556C)` and epilogue `[0x080656B8,0x080656C2)` are replaced. The prefix branches into retained original instructions at `0x0806556C`; neither that continuation nor callers are supplied as source.

The prefix's static data flow (`asm/gimmick_text.asm:73-133`) is:

1. Preserve r8 through r3 and save registers. Load literal slots at bus `0x080655D4`, `0x080655D8`, `0x080655DC`, `0x080655E0` (file offsets `0x000655D4`, `0x000655D8`, `0x000655DC`, `0x000655E0`). Comments describe values as utility RAM `0x030018BC`, ID RAM `0x03001AD2`, biased ROM base `0x0862C1F8`, and work RAM `0x03003F34`, respectively. Slot addresses are Confirmed operands; actual literal contents remain unverified.
2. Read ID `g` with `ldrb`, preserve `g*0x40` in r5, compute record source as biased base plus `g*0x58`, and call `0x080F954C` with r0=destination, r1=source, r2=`0x58`. Its memcpy role is Probable from call setup/comments; implementation is absent.
3. Set r8 to zero. Calculate translated name pointer `GimmickText + (g-1)*0x40`, store it as a word at work-record `+0`. This changes a **RAM copy**, not the original ROM name bytes.
4. Put the name pointer and limit 16 in utility parameters, call `0x0806A0D8`, and store its returned length byte at work-record `+0x68`. The helper's exact trimming semantics need verification; other comments describe trailing NULs, while this comment says spaces.
5. Read original-copied byte `b` at `+0x25`. Write `b & 0x7F` to extended byte `+0x70` and `(b << 1) & 0xFF` to `+0x6F` (the byte store truncates). Load mask `0x7F` into r12 for retained code. The shifted byte loses bit 7, so it does not preserve a separate high-bit flag.
6. Set r0 to work-record `+0x27`, issue `ldr r1,[r0]`, and branch to `0x0806556C`. Because this address is not word-aligned, instruction encoding and hardware load behavior must be checked before interpreting r1 as four consecutive record bytes. The source does not expose its subsequent use.

The initial source-only trace ended at step 6. The subsequent binary listing now exposes the retained continuation, but its numerical gameplay meanings and caller context remain unverified. Register values described here are local data flow, not a recovered public function ABI.

## RAM work structure versus original ROM record

These are IWRAM bus addresses and have **no ROM file offsets**. Absolute addresses are derived from base `0x03003F34`, now verified in both ROMs at literal slot bus `0x080655E0` / file `0x000655E0`. The following table describes the source-visible prefix; the retained continuation accesses additional work offsets, so this is not a full RAM allocation map.

| Work offset / absolute bus | Size | Source-visible use | Evidence / confidence |
| --- | --- | --- | --- |
| `+0x00` / `0x03003F34` | 4 | Replaces first four copied name bytes with translated ROM text pointer; dereferenced by patched name renderer. | `asm/gimmick_text.asm:103-105,55-57`; Confirmed operations, Probable absolute base. |
| `+0x04`–`+0x57` | 84 | Initially retains copied original record bytes, including Japanese name tail/description and non-text data. Later writes by original continuation are unknown. | `asm/gimmick_text.asm:89-105`; Confirmed prefix behavior. |
| `+0x25` / `0x03003F59` | 1 | Source of both uses-related transformed bytes. | `asm/gimmick_text.asm:117-128`; Confirmed read, Probable uses role. |
| `+0x27` / `0x03003F5B` | Word instruction | Unaligned load passed to retained code; no schema inferred from its width. | `asm/gimmick_text.asm:130-133`; Confirmed address, meaning Unconfirmed. |
| `+0x58`–`+0x67`, `+0x69`–`+0x6E` | 16, 6 | Outside original copy; initialization and meanings absent from shown prefix. | No visible assignments; Unconfirmed. |
| `+0x68` / `0x03003F9C` | 1 | Translated name length, consumed by renderer. | `asm/gimmick_text.asm:114-115,59-61`; Confirmed operations. |
| `+0x6F` / `0x03003FA3` | 1 | Shifted/truncated source byte `+0x25`. | `asm/gimmick_text.asm:126-128`; Confirmed transformation; downstream purpose Unconfirmed. |
| `+0x70` / `0x03003FA4` | 1 | Low seven bits of source byte `+0x25`. | `asm/gimmick_text.asm:121-125`; Confirmed transformation; downstream purpose Unconfirmed. |

The source touches at least `0x71` bytes of work-structure span; this is not proof of its total allocation size. Do not put `+0x68/+0x6F/+0x70` into the original `0x58`-byte field map.

## Choo-Choo graphics pointer cross-reference

`InsertChooChooAnimationTiles` is an existing C++ function (`inserter/images.cpp:754`), not a ROM routine. It loads palette file `0x005ED7EC` (bus `0x085ED7EC`) and a tileset at file `0x00577A1C` (bus `0x08577A1C`), with a supplied original compressed-size budget of 5,049 bytes and 384 16-color tiles. It replaces the sign graphic, then selects run-length compression through `SaveTilesetParams.useRLE = 1` (`inserter/images.cpp:756-781`). These are Confirmed source operands; binary contents and runtime use remain untested.

The relocation slot is file `0x0062CC8C` / bus `0x0862CC8C`. Arithmetic ties it to the same record table:

```text
0x0062CC8C - 0x0062C250 = 0x0A3C = 0x1D * 0x58 + 0x44
record 0x1D: file 0x0062CC48 / bus 0x0862CC48
English name: Choo-Choo; expected loader ID: 0x1E
```

If recompressed data exceeds 5,049 bytes, `SaveCompressedTileset` aligns the shared pool cursor, calls `WriteRelocs` to store `newOffset | 0x08000000` at that slot, and writes the compressed data to the pool (`inserter/images.cpp:167-180,92-96`). Otherwise it overwrites the original tileset in place and leaves the record pointer slot unchanged. No build was run; binary verification nevertheless establishes that the supplied English ROM has pointer `0x0868AFB0` here, targeting a relocated stream that consumes 6,955 encoded bytes.

This is independent executable-source evidence supporting `+0x44` as a graphics-pointer field for Choo-Choo. It does not identify an effect script, RNG modifier or power field. The palette is loaded separately, so it does not confirm record `+0x40` as the palette pointer. Generalization to all 50 entries is Probable, not Confirmed.

## Text consumers and translation boundary

| Consumer / patch site, ROM bus (file offset) | Visible access / cross-reference | Evidence / confidence |
| --- | --- | --- |
| Comment-described routine `0x0802B7F0` (`0x0002B7F0`), patch at `0x0802B868` (`0x0002B868`) | Reads work-record pointer `+0` and length `+0x68`; calls renderer `0x0802BEF0` (`0x0002BEF0`), resumes at `0x0802B882` (`0x0002B882`). Caller-to-loader connection is described by comment, not a visible call instruction. | `asm/gimmick_text.asm:48-66`; Confirmed patch accesses, Probable containing routine role. |
| Comment-described routine `0x0804AA5C` (`0x0004AA5C`) | Name lookup is redirected through literal patch `0x0804AB7C`; stride byte `0x0804AAC4` becomes 64, length byte `0x0804AAD0` becomes 16; clear-width helper called at `0x0804AADC`. These bus sites map to file offsets `0x0004AB7C`, `0x0004AAC4`, `0x0004AAD0`, `0x0004AADC`. | `asm/gimmick_text.asm:34-43`; Confirmed patches; surrounding routine is absent. |
| Description patch sites `0x0804DE32`, `0x0804DF46`, `0x0804DFCA`, `0x0804E7D0` (file `0x0004DE32`, `0x0004DF46`, `0x0004DFCA`, `0x0004E7D0`) | Store translated description pointer at battle message buffer `+4` instead of copying text. Related literals at bus `0x0804DE4C`, `0x0804DF80`, `0x0804E04C`, `0x0804E7F8` (file `0x0004DE4C`, `0x0004DF80`, `0x0004E04C`, `0x0004E7F8`) point to `GimmickText+0x10`; stride/length become 64/48. | `asm/gimmick_text.asm:146-210`; Confirmed patch sites. Repeated upstream function comment does not identify every containing entry. |
| Battle message drawing patches at `0x0804A4E0`, `0x0804A510` (file `0x0004A4E0`, `0x0004A510`) | If buffer length exceeds `0x1A`, read pointer at `+4`; measure and draw with VWF. Gimmick descriptions have max length `0x30`, selecting this pointer path. | `asm/battle_message.asm:14-86`; Confirmed source path, runtime untested. |
| `FormatObtainedItem`, `0x0806B27C` (`0x0006B27C`) | Decodes tagged ID from `0x03003A34`; Gimmick path clears bits 7/6 and indexes translated text with `(ID-1)*0x40`. It does not load gameplay fields. | `asm/dialog_item.asm:17-26,64-106`; Confirmed source decoding. |
| Comment-described routine `0x0806AD60` (`0x0006AD60`) | Prior Gimmick-name path; patched formatter explicitly bypasses it. No body or confirmed current call path available. | `asm/gimmick_text.asm:45-46`; `asm/dialog_item.asm:91-96`; Candidate original role. |
| `MenuStatusGimmickPickWho`, `0x08078C18` (`0x00078C18`) | Draws status text from descriptor `0x084904B8` (`0x004904B8`) and selected character's name. Reads menu state, not a Gimmick record restriction field. | `asm/menu_gimmicks.asm:5-10,33-83`; Confirmed source behavior. |

Translated text at bus `0x087F001E` / file `0x007F001E` uses 50 `0x40`-byte records: name at `+0`, length 16; instructions at `+0x10`, length 48; allocation `0xC80`. `asm/addresses.inc:3` and the RESTRUCT directives establish this. Only text is inserted there. No power, difficulty or flags are copied into this translated table.

The text relocation path leaves original record bytes in place, and the loader initially copies their non-text region `+0x22`–`+0x57` into RAM. **The image path has an exception:** Choo-Choo's original-record pointer at `+0x44` can be repointed when its translated tileset grows. Thus the earlier overview's statement that original gameplay data is retained must not be interpreted as byte-for-byte preservation of every non-text field. No power/difficulty/RNG field edit is established. This does not certify unrelated patches' gameplay behavior or that the existing English ROM matches the sources.

## Gameplay objectives: evidence limits

| Objective | Repository evidence | Supported conclusion |
| --- | --- | --- |
| Base power | Comment `atk` at `+0x22`. | Candidate only; no damage consumer or formula. |
| Maximum power | No explicitly identified max-power field or consumer. | Unconfirmed; do not reinterpret `maxBattery` as maximum power. |
| Difficulty | Guessed nine byte pairs at `+0x28`–`+0x39`; difficulty instructions are separate text. | Candidate array subdivision only; no selector, numeric range or scaling curve established. |
| RNG/random modifiers | No PRNG call, distribution, random multiplier or verified table-field consumer found in project-owned Gimmick patch sources. | Unconfirmed; random-seeming instructions/names are not field evidence. |
| Character restrictions | No Gimmick eligibility decoder found. The selected-character menu merely draws text/names; clothing eligibility code concerns a different table. | Unconfirmed; do not transfer clothing flag meanings to Gimmicks. |
| Special effects | Candidate `flags` byte and guessed pointer tail, without downstream consumers. | Unconfirmed; no specific bit/effect assignment. |
| Kaizo parameters | No Kaizo-specific record field, reward table or progression consumer. Prior dialogue pointers identify reward-related text. | Unconfirmed; neither dialogue mentioning 180 nor “levels” establishes a 180 cap/threshold here. |

## Next investigation and required tools

Static analysis of this translation repository is sufficient to establish text layouts, count/order, replacement operations and concrete binary investigation entry points. It is **insufficient to identify gameplay fields** or finish the loader/consumer graph.

The next focused task needs a read-only ROM inspector and GBA-capable disassembler, followed by a GBA debugger for runtime verification:

1. Fingerprint both provided ROMs without overwriting them. Validate table bytes, literal contents and instructions at the documented offsets independently in Japanese and translated ROMs.
2. Disassemble the complete routine beginning at `0x08065518`, including retained continuation at `0x0806556C`, and locate actual callers. Inspect the `+0x27` load before assigning a field width or value.
3. Identify all references to the original table, biased/interior table pointers and RAM work structure. Search for computed accesses as well as literal base references; the patch sources are not a complete call graph.
4. In a debugger, record ID and copied data for named Gimmicks. Watch reads of non-text bytes and derived work bytes during selection, difficulty changes, minigame execution and damage resolution. Record the PC/caller and subsequent calculation for each access.
5. Trace `+0x22`, `+0x23`, `+0x25`, proposed byte pairs and pointer targets into concrete outputs. Keep unknowns unknown if an access only supplies UI text. Handle Kaizo reward/progression through its event pointers separately unless a real link to record fields is found.

The binary follow-up supplies exact table values, literal values, pointer-target headers and bounded instruction observations in the linked report/CSV. It supplies no runtime effect tests or invented gameplay symbols. Independently validate the Thumb interpretation and trace live consumers before changing gameplay.

## Balance investigation readiness

The tested battle arithmetic now confirms pre-subtraction 26 minus target quantity 10, scratch 16, and HP reduction 16. Static tracing separates target +0x14 and mutable +0x18 and identifies conditional percentage/minimum/suppression branches; their gameplay names remain unresolved. A constrained future Gear-Yo +0x22 base-byte prototype is supportable for testing, with original ROM preservation and byte/hash assertions, but broad balance safety is not established. No prototype was implemented. Exact source writers, predictions and next capture are in [battle_damage_candidates.md](battle_damage_candidates.md).
