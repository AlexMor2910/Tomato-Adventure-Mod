# Gimmick Loader: Static Ghidra Trace

## Evidence and execution mode

Phase 1, 2026-10-10. Input and reproduction: [ghidra_analysis.md](ghidra_analysis.md). Evidence comes from the fingerprinted **Japanese** ROM, Ghidra 12.1.4 `ARM:LE:32:v4t`, and `tools/analyze/ghidra/TraceGimmickLoader.java`. **Confirmed (static)** means decoded instructions/local data flow. Gameplay names remain Candidate; no mGBA run was performed. Addresses in instruction listings are ROM bus addresses; subtract `0x08000000` for file offsets. RAM addresses have no ROM offsets.

The complete loader occupies executable ranges `[0x08065518,0x080655D4)` and `[0x080655E4,0x080656C2)`. Entry has coherent Thumb pushes saving r4-r7/LR and r8, ordinary Thumb BL calls and matching restores ending in `bx r0` at `0x080656C0`. Branches skip `[0x080655D4,0x080655E4)`, an embedded literal pool. This confirms a Thumb body; the script does not use ARM decoding for this routine. BX returns in the caller's saved mode. The following literal words are data, not additional function instructions.

| Slot | Value | Purpose from observed use | Status |
| --- | --- | --- | --- |
| `0x080655D4`, `0x080656C4` | `0x030018BC` | Shared parameter/work block | Confirmed static |
| `0x080655D8`, `0x080656CC` | `0x03001AD2` | Three byte-sized loader parameters | Confirmed static |
| `0x080655DC` | `0x0862C1F8` | Original table minus stride `0x58` | Confirmed static |
| `0x080655E0`, `0x080656C8` | `0x03003F34` | Copied record / extended work structure | Confirmed static |
| `0x080656D0` | `0x03001ADC` | Stores end of variable byte copy | Confirmed static; overall purpose unknown |
| `0x080656D4` | `0x03000608` | Indexed word stack storage | Confirmed static; call-stack-like purpose Probable |
| `0x080656D8` | `0x03000604` | Stack index word | Confirmed static; overall lifetime unknown |

## Complete loader data flow

1. `0x08065522..0x08065534`: load unsigned ID from `0x03001AD2`, multiply by `0x58`, add biased table base, populate utility source `+0x0C`, destination `+0x08`, length word `+0x04`, call `0x0806A00C`. Copy intent is Probable; the helper implementation was not fully traced. No ID bounds check is present. Supported IDs 1..50 come from prior table/manifests, not a range check here.
2. `0x08065538..0x0806554C`: pass copied-name address and limit 8 to `0x0806A0D8`, store returned parameter byte at work `+0x68`. Exact text-trimming behavior remains unverified.
3. `0x0806554E..0x08065566`: byte `+0x25` produces work `+0x70 = b & 0x7F` and `+0x6F = (b << 1) & 0xFF`. These operations do not establish a uses counter or an AWE field.
4. `0x08065568..0x0806558A`: byte-load `+0x27`; low nibble goes to work `+0x6C`, `+0x6D` is zeroed, bits 4-5 go to `+0x6E`.
5. `0x0806558C..0x080655AE`: parameter byte at `0x03001AD3` supplies selector `s`. The effective pair offset is `((s-1)*2) & 0xFF`, because the result passes through byte stores before the halfword lookup. Read `work + 0x28 + offset`; first byte goes to `+0x69`. The loader has no range check proving s=1..9.
6. `0x080655B2..0x080655F8`: if low nibble of `+0x27` is 1 or 2, second pair byte's low nibble goes to `+0x72`, high nibble to `+0x71`. Otherwise low seven bits go to `+0x72` and `+0x71=0`. This is confirmed packed-value decoding, with numerical/gameplay meanings unknown.
7. `0x080655FE..0x0806564C`: load pointer from `+0x3C`; leading byte goes to `+0x6B`. Copy subsequent nonzero bytes into work `+0x73` onwards, stopping at NUL or eight copied bytes, and store destination cursor at `0x03001ADC`. This supports a header/byte-stream role for `+0x3C`; neither text nor minigame script semantics are established.
8. `0x0806564E..0x080656B6`: use parameter `0x03001AD3-1` (truncated to byte) to offset the `+0x3C` stream; advance by 9 per iteration, copy a byte into the extended buffer, and use third parameter `0x03001AD4` to write `+0x6A` and drive further iterations. Utility base/index operations at `0x03000608` / `0x03000604` save and restore a word. The eight-byte first phase and nine-byte stepping suggest grouped data (Candidate); record boundaries and high-level purpose remain unknown. Initial loop count 8 is distinct from the selector and is not proof of nine gameplay difficulties.
9. `0x080656B8..0x080656C0`: restore saved registers and return. Work span reaches at least `+0x73` with up to eight first-phase bytes; this is not a complete allocation/lifetime model.

## Caller and cross-reference evidence

The raw even-offset Thumb BL scan across the ROM finds one encoding targeting `0x08065518`: **`0x0806ACFE`**. Ghidra then decodes it in coherent Thumb routine `[0x0806ACA0,0x0806AD4C)` (literal pool follows), confirming the direct call. This scan does not enumerate ARM calls, indirect calls, veneers, or all computed dispatch paths.

At `0x0806ACF0..0x0806ACFC`, the caller copies utility bytes `+1`, `+5`, `+4` respectively into `0x03001AD2`, `0x03001AD3`, `0x03001AD4`. Its prologue and return validate Thumb mode. It saves/restores utility fields via the same indexed word stack as the loader. No source-defined name is assigned. These upstream arguments do not yet identify a difficulty setting or playable-character index.

The source-known name consumer `0x0802B7F0` calls this wrapper at **`0x0802B80E`**, establishing the static chain `0x0802B7F0 -> 0x0806ACA0 -> 0x08065518`. In the original Japanese code, `0x0802B866` loads work base `0x03003F34`, the following instructions use its embedded name and `+0x68` length, and `0x0802B87E` calls `0x0802BEF0`. This strengthens the earlier comment-only connection. Only the requested bounded prefix of the name consumer was decoded, not its entire body.

Ghidra confirms direct loader calls at `0x08065534 -> 0x0806A00C` and `0x08065542 -> 0x0806A0D8`, conditional/loop branches, and PC-relative literal reads listed above. Computed record accesses are explained by data flow; the literal reference to `0x080655DC` is not a direct cross-reference to every table row.

## Additional record-field consumers

| Consumer / instruction | Original field | Additional static evidence | Interpretation / confidence |
| --- | --- | --- | --- |
| `0x08075970` routine; `0x080759B2..B8` | `+0x22` | Add this unsigned byte to a state-record byte returned by `0x0807565C`, store halfword at output `+8`. | Confirmed additive operand; Candidate base component of a derived value. Actual power/damage role unknown. |
| `0x080759A0..A6`, local blocks `0x0807530E..10`, `0x080755D0..D2` | `+0x23` | Byte read from original computed record; `0x08075970` stores it as output halfword `+6`. | Confirmed byte consumption; battery/capacity role remains Candidate. |
| `0x08075A04..0x08075AAE`; common `0x08075AB0..BC` | Even bytes `+0x28,+0x2A,...,+0x38` | Nine switch cases select offsets; multiply output halfword `+8` by chosen unsigned byte, divide by 100 via `0x080F7B08`, store low halfword at output `+0x0A`. | Confirmed percent-style scaling operation; Candidate level-dependent scaling. Not confirmed battle damage. |
| `0x080759AE..C0` | Selector source | State-record byte `+1` is stored to output `+0x0C`, subtract 1, permit 0..8, use an explicit nine-entry address table at `0x080759E0..0x08075A04`. | Confirmed 1..9 switch in this consumer; gameplay identity of selector unknown. Out-of-range selectors bypass the table cases; multiplier provenance on that path is unresolved. |
| `0x080754B0`; `0x080754C2..C8` | `+0x27` | For nonzero ID, read low nibble of original record; zero ID returns `0xFF`. | Confirmed independent low-nibble accessor; purpose unknown. |
| `0x08075AD8..DE` | `+0x27` | Extract bit 7 into output byte `+0x0F`. | Confirmed bit access; semantics unknown. |
| Loader `0x080655FE`, `0x0806564E` | `+0x3C` | Load and consume stream pointer twice. | Confirmed pointer use; header/grouped-stream interpretation Candidate. |

The instruction table at `0x080759E0` is treated as data and each target basic block is seeded separately. This avoids pretending Ghidra automatically recovered the computed `mov pc,r0` switch. `0x080F7B08` is a Thumb signed integer division implementation (sign normalization, shift/subtract quotient, restore sign); only positive small operands are relevant to the observed multiply-by-byte/divide-by-100 operation. Other call semantics and consumers still need tracing.

The selected windows do not identify additional consumers of the odd pair bytes outside the loader. `+0x25` has only the documented loader transformation in this bounded analysis.

Ghidra also decodes routine `[0x0807565C,0x080756A8)`: it reads group count at IWRAM `0x030035F0`, searches storage rooted at `0x03001EDC`, advances groups by `0x60`, and compares ID bytes in up to 20 three-byte entries starting at each group's `+8`. A match returns the entry address; no match returns zero. These are Confirmed static operations from the script's helper window. For `0x08075970`, returned entry `+1` supplies the nine-case selector and `+2` supplies the additive state byte. Inventory/owned-Gimmick state is a Candidate interpretation; no difficulty, upgrade, character ownership or battery semantics are assigned. The calling routine's assumptions about successful lookup need runtime checking.

## Pointer fields and limits

The script records the seven word slots `+0x3C,+0x40,+0x44,+0x48,+0x4C,+0x50,+0x54` for all 50 original records in ignored `loader.txt`. This reproduces numeric target evidence without extracting images or treating addresses as functions. Previous Choo-Choo `+0x44` graphics relocation remains valid; no additional live code consumer of `+0x40..+0x57` was confirmed in the scoped functions. Palette, graphics, pointer-list and other guessed field types remain Candidate, except the already documented Choo-Choo target evidence.

Aligned raw base matches reveal many work-buffer references, plus table references near battle code and inventory/menu code. A matching raw word is a search lead, not a confirmed instruction reference. The default trace retains their addresses locally. Alias propagation, interior/biased addresses, ARM callers and indirect dispatch remain incompletely mapped; absence of a scoped consumer is not proof a field is unused.

## Comparison with translation ASM

`asm/gimmick_text.asm:69..144` intentionally replaces the prefix and epilogue. The Japanese loader calls game utility `0x0806A00C`; the translation uses `0x080F954C` and replaces embedded name data in the work copy with a translated pointer. Their copy/name setup should not be conflated.

The original continuation begins at `0x0806556C`. Prior binary verification establishes `[0x0806556C,0x080656B8)` is identical between ROMs, including the literal pool. The new Ghidra decoding independently corroborates its Thumb operations. The Japanese epilogue returns at `0x080656C0`; the shortened translation returns at `0x080656BE`.

The key behavioral difference is real and source-consistent: Japanese `0x0806556A` is **`ldrb r1,[r0]`** at work `+0x27`, whereas English `0x08065564` is **`ldr r1,[r0]`** at that unaligned address. No four-byte field is inferred. Translation source matches the previously checked English bytes; this is a difference from original code, not a newly established source/binary mismatch. Register value and low-bit decoding on actual ARM7TDMI hardware/emulation need runtime comparison.

## Runtime verification and next investigation

In mGBA, break at `0x0806ACFE`, `0x08065518`, `0x08075970`, and `0x08075AB8`. Record actual caller, parameters at `0x03001AD2..D4`, selected record ID/name, selector, r0/r1 and output pointer on entry to `0x08075970`. Compare output `+8/+0x0A` against visible UI and battle results while changing difficulty and performing the minigame. Watch record-copy `+0x22/+0x23/+0x25`, derived `+0x69..+0x72`, and stream writes from `+0x73`; capture read/write PCs. Compare Japanese and English `+0x27` loads with matching input data and follow the decoded low nibble/bits 4-5. Use the emulator version and a reproducible save/location/action sequence in the eventual runtime report.

**Single most useful next investigation:** trace the output of `0x08075970` into its callers and validate it live. It offers the clearest new link from original `+0x22` and the nine even-byte coefficients to a concrete calculated value. Until that output is tied to an observed gameplay quantity, do not label it damage, power, difficulty progression, AWE, RNG, or Kaizo.

## Instruction evidence

The complete loader and targeted context listings below are generated from the successful Ghidra trace. Basic-block listings are not claims that all containing functions have been recovered.

<!-- generated-ghidra-instruction-evidence -->

Trace: `reverse_engineering/ghidra/run-cffeb54fcbc540a78ce312e1604a9711/loader.txt`; SHA-256 `5edfb8543f7e60b6116c91114e36a9ab576b11298f22a27858a84673dcc69b5c`.

### Complete loader and literals

```text
LOADER (literal pool 080655d4..080655e3 excluded)
08065518  push {r4,r5,r6,r7,lr}
0806551a  mov r7,r8
0806551c  push {r7}
0806551e  ldr r7,[0x080655d4]
  REF READ 080655d4
08065520  ldr r4,[0x080655d8]
  REF READ 080655d8
08065522  ldrb r0,[r4,#0x0]
08065524  mov r2,#0x58
08065526  mul r0,r2
08065528  ldr r1,[0x080655dc]
  REF READ 080655dc
0806552a  add r0,r0,r1
0806552c  str r0,[r7,#0xc]
0806552e  ldr r6,[0x080655e0]
  REF READ 080655e0
08065530  str r6,[r7,#0x8]
08065532  str r2,[r7,#0x4]
08065534  bl 0x0806a00c
  REF UNCONDITIONAL_CALL 0806a00c
08065538  str r6,[r7,#0xc]
0806553a  mov r0,#0x0
0806553c  mov r8,r0
0806553e  mov r0,#0x8
08065540  strb r0,[r7,#0x1]
08065542  bl 0x0806a0d8
  REF UNCONDITIONAL_CALL 0806a0d8
08065546  ldrb r1,[r7,#0x1]
08065548  add r0,r6,#0x0
0806554a  add r0,#0x68
0806554c  strb r1,[r0,#0x0]
0806554e  sub r0,#0x43
08065550  ldrb r2,[r0,#0x0]
08065552  mov r1,#0x7f
08065554  mov r12,r1
08065556  mov r0,r12
08065558  and r0,r2
0806555a  add r1,r6,#0x0
0806555c  add r1,#0x70
0806555e  strb r0,[r1,#0x0]
08065560  lsl r2,r2,#0x1
08065562  add r0,r6,#0x0
08065564  add r0,#0x6f
08065566  strb r2,[r0,#0x0]
08065568  sub r0,#0x48
0806556a  ldrb r1,[r0,#0x0]
0806556c  mov r5,#0xf
0806556e  add r2,r5,#0x0
08065570  and r2,r1
08065572  add r0,#0x45
08065574  strb r2,[r0,#0x0]
08065576  mov r0,#0x0
08065578  add r3,r6,#0x0
0806557a  add r3,#0x6d
0806557c  strb r0,[r3,#0x0]
0806557e  lsl r1,r1,#0x18
08065580  lsr r1,r1,#0x1c
08065582  mov r0,#0x3
08065584  and r1,r0
08065586  add r0,r6,#0x0
08065588  add r0,#0x6e
0806558a  strb r1,[r0,#0x0]
0806558c  ldrb r0,[r4,#0x1]
0806558e  sub r0,#0x1
08065590  lsl r0,r0,#0x1
08065592  strb r0,[r7,#0x1]
08065594  strb r0,[r7,#0x4]
08065596  mov r0,r8
08065598  strb r0,[r7,#0x5]
0806559a  add r0,r6,#0x0
0806559c  add r0,#0x28
0806559e  ldrh r1,[r7,#0x4]
080655a0  add r3,r0,r1
080655a2  str r3,[r7,#0xc]
080655a4  ldrb r1,[r3,#0x0]
080655a6  add r0,r3,#0x1
080655a8  str r0,[r7,#0xc]
080655aa  add r0,r6,#0x0
080655ac  add r0,#0x69
080655ae  strb r1,[r0,#0x0]
080655b0  strb r2,[r7,#0x1]
080655b2  cmp r2,#0x1
080655b4  beq 0x080655ba
  REF CONDITIONAL_JUMP 080655ba
080655b6  cmp r2,#0x2
080655b8  bne 0x080655e4
  REF CONDITIONAL_JUMP 080655e4
080655ba  ldrb r1,[r3,#0x1]
080655bc  add r0,r5,#0x0
080655be  and r0,r1
080655c0  strb r0,[r7,#0x1]
080655c2  add r1,r6,#0x0
080655c4  add r1,#0x72
080655c6  strb r0,[r1,#0x0]
080655c8  ldrb r0,[r3,#0x1]
080655ca  lsr r1,r0,#0x4
080655cc  lsl r0,r0,#0x4
080655ce  add r1,r1,r0
080655d0  and r1,r5
080655d2  b 0x080655f2
  REF UNCONDITIONAL_JUMP 080655f2
080655e4  ldrb r1,[r3,#0x1]
080655e6  mov r0,r12
080655e8  and r0,r1
080655ea  add r1,r6,#0x0
080655ec  add r1,#0x72
080655ee  strb r0,[r1,#0x0]
080655f0  mov r1,#0x0
080655f2  strb r1,[r7,#0x1]
080655f4  add r0,r6,#0x0
080655f6  add r0,#0x71
080655f8  strb r1,[r0,#0x0]
080655fa  ldr r1,[0x080656c4]
  REF READ 080656c4
080655fc  ldr r2,[0x080656c8]
  REF READ 080656c8
080655fe  ldr r0,[r2,#0x3c]
08065600  str r0,[r1,#0xc]
08065602  ldrb r3,[r0,#0x0]
08065604  strb r3,[r1,#0x1]
08065606  add r0,#0x1
08065608  str r0,[r1,#0xc]
0806560a  add r0,r2,#0x0
0806560c  add r0,#0x6b
0806560e  strb r3,[r0,#0x0]
08065610  add r0,#0x8
08065612  str r0,[r1,#0x8]
08065614  mov r0,#0x8
08065616  strb r0,[r1,#0x4]
08065618  add r3,r1,#0x0
0806561a  ldr r5,[0x080656cc]
  REF READ 080656cc
0806561c  mov r8,r5
0806561e  add r7,r2,#0x0
08065620  ldr r5,[0x080656d0]
  REF READ 080656d0
08065622  ldr r6,[0x080656d4]
  REF READ 080656d4
08065624  ldr r4,[0x080656d8]
  REF READ 080656d8
08065626  ldr r0,[r3,#0xc]
08065628  ldrb r1,[r0,#0x0]
0806562a  strb r1,[r3,#0x1]
0806562c  add r0,#0x1
0806562e  str r0,[r3,#0xc]
08065630  lsl r0,r1,#0x18
08065632  cmp r0,#0x0
08065634  beq 0x0806564a
  REF CONDITIONAL_JUMP 0806564a
08065636  ldr r0,[r3,#0x8]
08065638  strb r1,[r0,#0x0]
0806563a  add r0,#0x1
0806563c  str r0,[r3,#0x8]
0806563e  ldrb r0,[r3,#0x4]
08065640  sub r0,#0x1
08065642  strb r0,[r3,#0x4]
08065644  lsl r0,r0,#0x18
08065646  cmp r0,#0x0
08065648  bne 0x08065626
  REF CONDITIONAL_JUMP 08065626
0806564a  ldr r2,[r3,#0x8]
0806564c  str r2,[r5,#0x0]
0806564e  ldr r1,[r7,#0x3c]
08065650  mov r5,r8
08065652  ldrb r0,[r5,#0x1]
08065654  sub r0,#0x1
08065656  strb r0,[r3,#0x1]
08065658  ldrb r0,[r3,#0x1]
0806565a  strh r0,[r3,#0x4]
0806565c  ldrh r0,[r3,#0x4]
0806565e  add r1,r1,r0
08065660  str r1,[r3,#0xc]
08065662  mov r0,#0x9
08065664  str r0,[r3,#0x4]
08065666  str r2,[r3,#0x8]
08065668  mov r0,#0x8
0806566a  strb r0,[r3,#0x1]
0806566c  mov r0,#0x9
0806566e  str r0,[r3,#0x4]
08065670  ldr r0,[r3,#0xc]
08065672  add r0,#0x9
08065674  str r0,[r3,#0xc]
08065676  ldr r2,[r4,#0x0]
08065678  lsl r0,r2,#0x2
0806567a  add r0,r0,r6
0806567c  ldr r1,[r3,#0x0]
0806567e  str r1,[r0,#0x0]
08065680  add r2,#0x1
08065682  str r2,[r4,#0x0]
08065684  ldr r0,[r3,#0xc]
08065686  ldrb r1,[r0,#0x0]
08065688  strb r1,[r3,#0x1]
0806568a  ldr r0,[r3,#0x8]
0806568c  strb r1,[r0,#0x0]
0806568e  add r0,#0x1
08065690  str r0,[r3,#0x8]
08065692  mov r1,r8
08065694  ldrb r0,[r1,#0x2]
08065696  strb r0,[r3,#0x1]
08065698  add r1,r7,#0x0
0806569a  add r1,#0x6a
0806569c  strb r0,[r1,#0x0]
0806569e  ldr r0,[r4,#0x0]
080656a0  sub r0,#0x1
080656a2  str r0,[r4,#0x0]
080656a4  lsl r0,r0,#0x2
080656a6  add r0,r0,r6
080656a8  ldr r0,[r0,#0x0]
080656aa  str r0,[r3,#0x0]
080656ac  ldrb r0,[r3,#0x1]
080656ae  sub r0,#0x1
080656b0  strb r0,[r3,#0x1]
080656b2  lsl r0,r0,#0x18
080656b4  cmp r0,#0x0
080656b6  bne 0x0806566c
  REF CONDITIONAL_JUMP 0806566c
080656b8  pop {r3}
080656ba  mov r8,r3
080656bc  pop {r4,r5,r6,r7}
080656be  pop {r0}
080656c0  bx r0

LITERAL WORDS
080655d4 = 030018bc
080655d8 = 03001ad2
080655dc = 0862c1f8
080655e0 = 03003f34
080656c4 = 030018bc
080656c8 = 03003f34
080656cc = 03001ad2
080656d0 = 03001adc
080656d4 = 03000608
080656d8 = 03000604
```

### Caller and consumer contexts

```text
TARGETED CONTEXTS (some are basic blocks, not complete functions)
BLOCK 0806aca0..0806ad4b
0806aca0  push {r4,r5,r6,lr}
0806aca2  mov r6,r8
0806aca4  push {r6}
0806aca6  ldr r6,[0x0806ad4c]
  REF READ 0806ad4c literal=03000608
0806aca8  ldr r5,[0x0806ad50]
  REF READ 0806ad50 literal=03000604
0806acaa  ldr r1,[r5,#0x0]
0806acac  lsl r0,r1,#0x2
0806acae  add r0,r0,r6
0806acb0  ldr r2,[0x0806ad54]
  REF READ 0806ad54 literal=03000600
0806acb2  mov r8,r2
0806acb4  mov r3,#0x0
0806acb6  ldrsh r2,[r2,r3]
0806acb8  str r2,[r0,#0x0]
0806acba  add r1,#0x1
0806acbc  str r1,[r5,#0x0]
0806acbe  lsl r0,r1,#0x2
0806acc0  add r0,r0,r6
0806acc2  ldr r4,[0x0806ad58]
  REF READ 0806ad58 literal=030018bc
0806acc4  ldr r2,[r4,#0x0]
0806acc6  str r2,[r0,#0x0]
0806acc8  add r1,#0x1
0806acca  str r1,[r5,#0x0]
0806accc  lsl r0,r1,#0x2
0806acce  add r0,r0,r6
0806acd0  ldr r2,[r4,#0x4]
0806acd2  str r2,[r0,#0x0]
0806acd4  add r1,#0x1
0806acd6  str r1,[r5,#0x0]
0806acd8  lsl r0,r1,#0x2
0806acda  add r0,r0,r6
0806acdc  ldr r2,[r4,#0x8]
0806acde  str r2,[r0,#0x0]
0806ace0  add r1,#0x1
0806ace2  str r1,[r5,#0x0]
0806ace4  lsl r0,r1,#0x2
0806ace6  add r0,r0,r6
0806ace8  ldr r2,[r4,#0xc]
0806acea  str r2,[r0,#0x0]
0806acec  add r1,#0x1
0806acee  str r1,[r5,#0x0]
0806acf0  ldr r1,[0x0806ad5c]
  REF READ 0806ad5c literal=03001ad2
0806acf2  ldrb r0,[r4,#0x1]
0806acf4  strb r0,[r1,#0x0]
0806acf6  ldrb r0,[r4,#0x5]
0806acf8  strb r0,[r1,#0x1]
0806acfa  ldrb r0,[r4,#0x4]
0806acfc  strb r0,[r1,#0x2]
0806acfe  bl 0x08065518
  REF UNCONDITIONAL_CALL 08065518
0806ad02  ldr r1,[r5,#0x0]
0806ad04  sub r0,r1,#0x1
0806ad06  str r0,[r5,#0x0]
0806ad08  lsl r0,r0,#0x2
0806ad0a  add r0,r0,r6
0806ad0c  ldr r0,[r0,#0x0]
0806ad0e  str r0,[r4,#0xc]
0806ad10  sub r0,r1,#0x2
0806ad12  str r0,[r5,#0x0]
0806ad14  lsl r0,r0,#0x2
0806ad16  add r0,r0,r6
0806ad18  ldr r0,[r0,#0x0]
0806ad1a  str r0,[r4,#0x8]
0806ad1c  sub r0,r1,#0x3
0806ad1e  str r0,[r5,#0x0]
0806ad20  lsl r0,r0,#0x2
0806ad22  add r0,r0,r6
0806ad24  ldr r0,[r0,#0x0]
0806ad26  str r0,[r4,#0x4]
0806ad28  sub r0,r1,#0x4
0806ad2a  str r0,[r5,#0x0]
0806ad2c  lsl r0,r0,#0x2
0806ad2e  add r0,r0,r6
0806ad30  ldr r0,[r0,#0x0]
0806ad32  str r0,[r4,#0x0]
0806ad34  sub r1,#0x5
0806ad36  str r1,[r5,#0x0]
0806ad38  lsl r1,r1,#0x2
0806ad3a  add r1,r1,r6
0806ad3c  ldr r0,[r1,#0x0]
0806ad3e  mov r4,r8
0806ad40  strh r0,[r4,#0x0]
0806ad42  pop {r3}
0806ad44  mov r8,r3
0806ad46  pop {r4,r5,r6}
0806ad48  pop {r0}
0806ad4a  bx r0
BLOCK 0802b7f0..0802b8bf
0802b7f0  push {r4,r5,r6,lr}
0802b7f2  mov r6,r10
0802b7f4  mov r5,r9
0802b7f6  mov r4,r8
0802b7f8  push {r4,r5,r6}
0802b7fa  sub sp,#0x8
0802b7fc  bl 0x0802be10
  REF UNCONDITIONAL_CALL 0802be10
0802b800  ldr r1,[0x0802b834]
  REF READ 0802b834 literal=03004eea
0802b802  ldr r5,[0x0802b838]
  REF READ 0802b838 literal=030018bc
0802b804  ldrb r0,[r5,#0x5]
0802b806  strb r0,[r1,#0x0]
0802b808  ldr r1,[0x0802b83c]
  REF READ 0802b83c literal=03004eeb
0802b80a  ldrb r0,[r5,#0x4]
0802b80c  strb r0,[r1,#0x0]
0802b80e  bl 0x0806aca0
  REF UNCONDITIONAL_CALL 0806aca0
0802b812  ldr r0,[0x0802b840]
  REF READ 0802b840 literal=03004ee0
0802b814  ldrb r0,[r0,#0x0]
0802b816  bl 0x0802af0c
  REF UNCONDITIONAL_CALL 0802af0c
0802b81a  ldr r0,[0x0802b844]
  REF READ 0802b844 literal=03004eec
0802b81c  ldrb r0,[r0,#0x0]
0802b81e  cmp r0,#0x0
0802b820  beq 0x0802b850
  REF CONDITIONAL_JUMP 0802b850
0802b822  ldr r0,[0x0802b848]
  REF READ 0802b848 literal=0862bf6b
0802b824  str r0,[r5,#0xc]
0802b826  mov r0,#0x8
0802b828  strb r0,[r5,#0x5]
0802b82a  ldr r0,[0x0802b84c]
  REF READ 0802b84c literal=06009a60
0802b82c  str r0,[r5,#0x8]
0802b82e  bl 0x0802bef0
  REF UNCONDITIONAL_CALL 0802bef0
0802b832  b 0x0802b882
  REF UNCONDITIONAL_JUMP 0802b882
0802b850  ldr r2,[0x0802b8b4]
  REF READ 0802b8b4 literal=06009a60
0802b852  mov r4,#0x1
0802b854  rsb r4,r4
0802b856  str r4,[sp,#0x0]
0802b858  ldr r1,[0x0802b8b8]
  REF READ 0802b8b8 literal=040000d4
0802b85a  mov r0,sp
0802b85c  str r0,[r1,#0x0]
0802b85e  str r2,[r1,#0x4]
0802b860  ldr r3,[0x0802b8bc]
  REF READ 0802b8bc literal=85000040
0802b862  str r3,[r1,#0x8]
0802b864  ldr r0,[r1,#0x8]
0802b866  ldr r0,[0x0802b8c0]
  REF READ 0802b8c0 literal=03003f34
0802b868  str r0,[r5,#0xc]
0802b86a  add r0,#0x68
0802b86c  ldrb r0,[r0,#0x0]
0802b86e  strb r0,[r5,#0x5]
0802b870  str r2,[r5,#0x8]
0802b872  str r4,[sp,#0x0]
0802b874  mov r0,sp
0802b876  str r0,[r1,#0x0]
0802b878  str r2,[r1,#0x4]
0802b87a  str r3,[r1,#0x8]
0802b87c  ldr r0,[r1,#0x8]
0802b87e  bl 0x0802bef0
  REF UNCONDITIONAL_CALL 0802bef0
0802b882  ldr r0,[0x0802b8c4]
  REF READ 0802b8c4 literal=03004eec
0802b884  ldrb r0,[r0,#0x0]
0802b886  cmp r0,#0x0
0802b888  beq 0x0802b8d8
  REF CONDITIONAL_JUMP 0802b8d8
0802b88a  ldr r2,[0x0802b8c8]
  REF READ 0802b8c8 literal=030018bc
0802b88c  ldr r1,[0x0802b8cc]
  REF READ 0802b8cc literal=0600a680
0802b88e  mov r0,#0x1
0802b890  rsb r0,r0
0802b892  str r0,[sp,#0x0]
0802b894  ldr r0,[0x0802b8b8]
  REF READ 0802b8b8 literal=040000d4
0802b896  mov r3,sp
0802b898  str r3,[r0,#0x0]
0802b89a  str r1,[r0,#0x4]
0802b89c  ldr r1,[0x0802b8d0]
  REF READ 0802b8d0 literal=85000030
0802b89e  str r1,[r0,#0x8]
0802b8a0  ldr r0,[r0,#0x8]
0802b8a2  mov r0,#0x0
0802b8a4  strh r0,[r2,#0xc]
0802b8a6  ldr r0,[0x0802b8d4]
  REF READ 0802b8d4 literal=0600a720
0802b8a8  str r0,[r2,#0x8]
0802b8aa  mov r0,#0x1
0802b8ac  strb r0,[r2,#0x5]
0802b8ae  bl 0x0802c044
  REF UNCONDITIONAL_CALL 0802c044
0802b8b2  b 0x0802b902
  REF UNCONDITIONAL_JUMP 0802b902
BLOCK 080754b0..080754d3
080754b0  lsl r0,r0,#0x18
080754b2  lsr r0,r0,#0x18
080754b4  cmp r0,#0x0
080754b6  beq 0x080754d0
  REF CONDITIONAL_JUMP 080754d0
080754b8  ldr r2,[0x080754cc]
  REF READ 080754cc literal=0862c250
080754ba  sub r1,r0,#0x1
080754bc  mov r0,#0x58
080754be  mul r0,r1
080754c0  add r0,r0,r2
080754c2  add r0,#0x27
080754c4  ldrb r1,[r0,#0x0]
080754c6  mov r0,#0xf
080754c8  and r0,r1
080754ca  b 0x080754d2
  REF UNCONDITIONAL_JUMP 080754d2
080754d0  mov r0,#0xff
080754d2  bx lr
BLOCK 08075970..080759cf
08075970  push {r4,r5,r6,r7,lr}
08075972  add r7,r1,#0x0
08075974  lsl r0,r0,#0x18
08075976  lsr r6,r0,#0x18
08075978  lsl r0,r6,#0x1
0807597a  ldr r2,[0x080759d0]
  REF READ 080759d0 literal=0200ef06
0807597c  add r1,r0,r2
0807597e  ldrb r1,[r1,#0x0]
08075980  strh r1,[r7,#0x0]
08075982  ldr r1,[0x080759d4]
  REF READ 080759d4 literal=0200ef07
08075984  add r0,r0,r1
08075986  ldrb r0,[r0,#0x0]
08075988  strh r0,[r7,#0x2]
0807598a  add r0,r6,#0x0
0807598c  bl 0x0807565c
  REF UNCONDITIONAL_CALL 0807565c
08075990  ldrb r0,[r0,#0x2]
08075992  strh r0,[r7,#0x4]
08075994  ldr r2,[0x080759d8]
  REF READ 080759d8 literal=0862c250
08075996  sub r1,r6,#0x1
08075998  mov r0,#0x58
0807599a  add r4,r1,#0x0
0807599c  mul r4,r0
0807599e  add r4,r4,r2
080759a0  add r0,r4,#0x0
080759a2  add r0,#0x23
080759a4  ldrb r0,[r0,#0x0]
080759a6  strh r0,[r7,#0x6]
080759a8  add r0,r6,#0x0
080759aa  bl 0x0807565c
  REF UNCONDITIONAL_CALL 0807565c
080759ae  ldrb r0,[r0,#0x1]
080759b0  strh r0,[r7,#0xc]
080759b2  add r4,#0x22
080759b4  ldrh r0,[r7,#0x4]
080759b6  ldrb r4,[r4,#0x0]
080759b8  add r0,r0,r4
080759ba  strh r0,[r7,#0x8]
080759bc  ldrh r0,[r7,#0xc]
080759be  sub r0,#0x1
080759c0  cmp r0,#0x8
080759c2  bls 0x080759c6
  REF CONDITIONAL_JUMP 080759c6
080759c4  b 0x08075ab2
  REF UNCONDITIONAL_JUMP 08075ab2
080759c6  lsl r0,r0,#0x2
080759c8  ldr r1,[0x080759dc]
  REF READ 080759dc literal=080759e0
080759ca  add r0,r0,r1
080759cc  ldr r0,[r0,#0x0]
080759ce  mov pc,r0
BLOCK 08075aa4..08075ab1
08075aa4  ldr r2,[0x08075af0]
  REF READ 08075af0 literal=0862c250
08075aa6  sub r1,r6,#0x1
08075aa8  mov r0,#0x58
08075aaa  mul r0,r1
08075aac  add r0,r0,r2
08075aae  add r0,#0x38
08075ab0  ldrb r5,[r0,#0x0]
BLOCK 08075ab2..08075aed
08075ab2  ldrh r0,[r7,#0x8]
08075ab4  mul r0,r5
08075ab6  mov r1,#0x64
08075ab8  bl 0x080f7b08
  REF UNCONDITIONAL_CALL 080f7b08
08075abc  strh r0,[r7,#0xa]
08075abe  ldr r4,[0x08075af4]
  REF READ 08075af4 literal=030018bc
08075ac0  ldr r0,[0x08075af8]
  REF READ 08075af8 literal=0200ef6c
08075ac2  str r0,[r4,#0xc]
08075ac4  str r6,[r4,#0x4]
08075ac6  bl 0x08069f60
  REF UNCONDITIONAL_CALL 08069f60
08075aca  ldrb r0,[r4,#0x1]
08075acc  strb r0,[r7,#0xe]
08075ace  ldr r2,[0x08075af0]
  REF READ 08075af0 literal=0862c250
08075ad0  sub r1,r6,#0x1
08075ad2  mov r0,#0x58
08075ad4  mul r0,r1
08075ad6  add r0,r0,r2
08075ad8  add r0,#0x27
08075ada  ldrb r0,[r0,#0x0]
08075adc  lsr r0,r0,#0x7
08075ade  strb r0,[r7,#0xf]
08075ae0  add r0,r6,#0x0
08075ae2  bl 0x080754b0
  REF UNCONDITIONAL_CALL 080754b0
08075ae6  strb r0,[r7,#0x10]
08075ae8  pop {r4,r5,r6,r7}
08075aea  pop {r0}
08075aec  bx r0
BLOCK 08075304..08075311
08075304  ldr r2,[0x0807533c]
  REF READ 0807533c literal=0862c250
08075306  sub r1,r6,#0x1
08075308  mov r0,#0x58
0807530a  mul r0,r1
0807530c  add r0,r0,r2
0807530e  add r0,#0x23
08075310  ldrb r5,[r0,#0x0]
BLOCK 080755c6..080755d3
080755c6  ldr r2,[0x080755fc]
  REF READ 080755fc literal=0862c250
080755c8  sub r1,r4,#0x1
080755ca  mov r0,#0x58
080755cc  mul r0,r1
080755ce  add r0,r0,r2
080755d0  add r0,#0x23
080755d2  ldrb r7,[r0,#0x0]
BLOCK 080f7b08..080f7b9d
080f7b08  cmp r1,#0x0
080f7b0a  beq 0x080f7b90
  REF CONDITIONAL_JUMP 080f7b90
080f7b0c  push {r4}
080f7b0e  add r4,r0,#0x0
080f7b10  eor r4,r1
080f7b12  mov r12,r4
080f7b14  mov r3,#0x1
080f7b16  mov r2,#0x0
080f7b18  cmp r1,#0x0
080f7b1a  bpl 0x080f7b1e
  REF CONDITIONAL_JUMP 080f7b1e
080f7b1c  rsb r1,r1
080f7b1e  cmp r0,#0x0
080f7b20  bpl 0x080f7b24
  REF CONDITIONAL_JUMP 080f7b24
080f7b22  rsb r0,r0
080f7b24  cmp r0,r1
080f7b26  bcc 0x080f7b82
  REF CONDITIONAL_JUMP 080f7b82
080f7b28  mov r4,#0x1
080f7b2a  lsl r4,r4,#0x1c
080f7b2c  cmp r1,r4
080f7b2e  bcs 0x080f7b3a
  REF CONDITIONAL_JUMP 080f7b3a
080f7b30  cmp r1,r0
080f7b32  bcs 0x080f7b3a
  REF CONDITIONAL_JUMP 080f7b3a
080f7b34  lsl r1,r1,#0x4
080f7b36  lsl r3,r3,#0x4
080f7b38  b 0x080f7b2c
  REF UNCONDITIONAL_JUMP 080f7b2c
080f7b3a  lsl r4,r4,#0x3
080f7b3c  cmp r1,r4
080f7b3e  bcs 0x080f7b4a
  REF CONDITIONAL_JUMP 080f7b4a
080f7b40  cmp r1,r0
080f7b42  bcs 0x080f7b4a
  REF CONDITIONAL_JUMP 080f7b4a
080f7b44  lsl r1,r1,#0x1
080f7b46  lsl r3,r3,#0x1
080f7b48  b 0x080f7b3c
  REF UNCONDITIONAL_JUMP 080f7b3c
080f7b4a  cmp r0,r1
080f7b4c  bcc 0x080f7b52
  REF CONDITIONAL_JUMP 080f7b52
080f7b4e  sub r0,r0,r1
080f7b50  orr r2,r3
080f7b52  lsr r4,r1,#0x1
080f7b54  cmp r0,r4
080f7b56  bcc 0x080f7b5e
  REF CONDITIONAL_JUMP 080f7b5e
080f7b58  sub r0,r0,r4
080f7b5a  lsr r4,r3,#0x1
080f7b5c  orr r2,r4
080f7b5e  lsr r4,r1,#0x2
080f7b60  cmp r0,r4
080f7b62  bcc 0x080f7b6a
  REF CONDITIONAL_JUMP 080f7b6a
080f7b64  sub r0,r0,r4
080f7b66  lsr r4,r3,#0x2
080f7b68  orr r2,r4
080f7b6a  lsr r4,r1,#0x3
080f7b6c  cmp r0,r4
080f7b6e  bcc 0x080f7b76
  REF CONDITIONAL_JUMP 080f7b76
080f7b70  sub r0,r0,r4
080f7b72  lsr r4,r3,#0x3
080f7b74  orr r2,r4
080f7b76  cmp r0,#0x0
080f7b78  beq 0x080f7b82
  REF CONDITIONAL_JUMP 080f7b82
080f7b7a  lsr r3,r3,#0x4
080f7b7c  beq 0x080f7b82
  REF CONDITIONAL_JUMP 080f7b82
080f7b7e  lsr r1,r1,#0x4
080f7b80  b 0x080f7b4a
  REF UNCONDITIONAL_JUMP 080f7b4a
080f7b82  add r0,r2,#0x0
080f7b84  mov r4,r12
080f7b86  cmp r4,#0x0
080f7b88  bpl 0x080f7b8c
  REF CONDITIONAL_JUMP 080f7b8c
080f7b8a  rsb r0,r0
080f7b8c  pop {r4}
080f7b8e  mov pc,lr
080f7b90  push {lr}
080f7b92  bl 0x080f7b9c
  REF UNCONDITIONAL_CALL 080f7b9c
080f7b96  mov r0,#0x0
080f7b98  pop {pc}
080f7b9c  mov pc,lr
BLOCK 0807565c..080756bf
0807565c  push {r4,r5,r6,lr}
0807565e  lsl r0,r0,#0x18
08075660  lsr r5,r0,#0x18
08075662  mov r3,#0x0
08075664  ldr r0,[0x08075688]
  REF READ 08075688 literal=030035f0
08075666  ldrb r0,[r0,#0x0]
08075668  cmp r3,r0
0807566a  bge 0x080756a0
  REF CONDITIONAL_JUMP 080756a0
0807566c  ldr r1,[0x0807568c]
  REF READ 0807568c literal=03001edc
0807566e  mov r12,r1
08075670  add r6,r0,#0x0
08075672  mov r4,#0x0
08075674  mov r2,#0x0
08075676  mov r0,r12
08075678  add r0,#0x8
0807567a  add r1,r4,r0
0807567c  ldrb r0,[r1,#0x0]
0807567e  cmp r0,r5
08075680  bne 0x08075690
  REF CONDITIONAL_JUMP 08075690
08075682  add r0,r1,#0x0
08075684  b 0x080756a2
  REF UNCONDITIONAL_JUMP 080756a2
08075690  add r1,#0x3
08075692  add r2,#0x1
08075694  cmp r2,#0x13
08075696  ble 0x0807567c
  REF CONDITIONAL_JUMP 0807567c
08075698  add r4,#0x60
0807569a  add r3,#0x1
0807569c  cmp r3,r6
0807569e  blt 0x08075674
  REF CONDITIONAL_JUMP 08075674
080756a0  mov r0,#0x0
080756a2  pop {r4,r5,r6}
080756a4  pop {r1}
080756a6  bx r1
BLOCK 08075a04..08075a11
08075a04  ldr r2,[0x08075a14]
  REF READ 08075a14 literal=0862c250
08075a06  sub r1,r6,#0x1
08075a08  mov r0,#0x58
08075a0a  mul r0,r1
08075a0c  add r0,r0,r2
08075a0e  add r0,#0x28
08075a10  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a18..08075a25
08075a18  ldr r2,[0x08075a28]
  REF READ 08075a28 literal=0862c250
08075a1a  sub r1,r6,#0x1
08075a1c  mov r0,#0x58
08075a1e  mul r0,r1
08075a20  add r0,r0,r2
08075a22  add r0,#0x2a
08075a24  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a2c..08075a39
08075a2c  ldr r2,[0x08075a3c]
  REF READ 08075a3c literal=0862c250
08075a2e  sub r1,r6,#0x1
08075a30  mov r0,#0x58
08075a32  mul r0,r1
08075a34  add r0,r0,r2
08075a36  add r0,#0x2c
08075a38  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a40..08075a4d
08075a40  ldr r2,[0x08075a50]
  REF READ 08075a50 literal=0862c250
08075a42  sub r1,r6,#0x1
08075a44  mov r0,#0x58
08075a46  mul r0,r1
08075a48  add r0,r0,r2
08075a4a  add r0,#0x2e
08075a4c  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a54..08075a61
08075a54  ldr r2,[0x08075a64]
  REF READ 08075a64 literal=0862c250
08075a56  sub r1,r6,#0x1
08075a58  mov r0,#0x58
08075a5a  mul r0,r1
08075a5c  add r0,r0,r2
08075a5e  add r0,#0x30
08075a60  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a68..08075a75
08075a68  ldr r2,[0x08075a78]
  REF READ 08075a78 literal=0862c250
08075a6a  sub r1,r6,#0x1
08075a6c  mov r0,#0x58
08075a6e  mul r0,r1
08075a70  add r0,r0,r2
08075a72  add r0,#0x32
08075a74  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a7c..08075a89
08075a7c  ldr r2,[0x08075a8c]
  REF READ 08075a8c literal=0862c250
08075a7e  sub r1,r6,#0x1
08075a80  mov r0,#0x58
08075a82  mul r0,r1
08075a84  add r0,r0,r2
08075a86  add r0,#0x34
08075a88  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075a90..08075a9d
08075a90  ldr r2,[0x08075aa0]
  REF READ 08075aa0 literal=0862c250
08075a92  sub r1,r6,#0x1
08075a94  mov r0,#0x58
08075a96  mul r0,r1
08075a98  add r0,r0,r2
08075a9a  add r0,#0x36
08075a9c  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
BLOCK 08075aa4..08075ab1
08075aa4  ldr r2,[0x08075af0]
  REF READ 08075af0 literal=0862c250
08075aa6  sub r1,r6,#0x1
08075aa8  mov r0,#0x58
08075aaa  mul r0,r1
08075aac  add r0,r0,r2
08075aae  add r0,#0x38
08075ab0  ldrb r5,[r0,#0x0]

SCALER SWITCH TARGET WORDS (data, not instructions)
080759e0 = 08075a04
080759e4 = 08075a18
080759e8 = 08075a2c
080759ec = 08075a40
080759f0 = 08075a54
080759f4 = 08075a68
080759f8 = 08075a7c
080759fc = 08075a90
08075a00 = 08075aa4
```
