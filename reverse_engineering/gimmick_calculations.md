# Gimmick Calculations and Their Consumers

## Scope, reproduction and confidence

Phase 1, 2026-10-10. Ghidra **12.1.4**, existing JDK **23.0.1**, language **ARM:LE:32:v4t**, compiler `default`. Japanese ROM file offset zero maps to bus `0x08000000`. Whole-ROM auto-analysis is disabled; disassembly follows only bounded seeds and explicit switch-table destinations. All routines below have coherent **Thumb** code. No invented gameplay function names are assigned.

Inputs are the preserved workspace-root ROMs:

| Input | SHA-256 |
| --- | --- |
| `Tomato Adventure (Japan).gba` | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| `Tomato Adventure (Japan) (patched).gba` | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |

Re-run from the repository root using the existing isolated headless runner/compiler adapter:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1 -Script TraceGimmickCalculations
```

The original loader script remains the default. The new script is `tools/analyze/ghidra/TraceGimmickCalculations.java`. It produces `loader.txt`, expanded `arguments.json`, input metadata and logs under an ignored, unique `reverse_engineering/ghidra/run-<GUID>/` directory. `-readOnly` discards the temporary import/database. No ROM, translation source, gameplay code or Ghidra installation is written; no build, installation or emulator was run. Both ROM hashes/sizes/timestamps pass the runner's post-analysis checks.

Successful final calculation run: `reverse_engineering/ghidra/run-50ecc6655f7542ed8a8d9f69e3b2d68a/`. It completes with `TRACE_COMPLETE`, **136 calculation-function instructions**, and no script error. All discovered direct calls below are independently decoded in Ghidra caller contexts. The first attempt stopped at an overly narrow validation bound for the item dispatch table; the evidenced destination `0x08080F0C` was then admitted within the already scoped routine. No speculative repair or ROM edit was involved.

Refresh the instruction appendix from this successful trace:

```powershell
python tools/analyze/ghidra/export_calculations.py reverse_engineering/ghidra/run-50ecc6655f7542ed8a8d9f69e3b2d68a/loader.txt
```

**Confirmed (static)** establishes bytes, instructions, addresses, arithmetic or a traced display write. **Probable** assigns a gameplay interpretation supported by those operations and the translation's label/description manifests. **Candidate** is a lead requiring additional evidence. **Unconfirmed** means no established connection. None of these observations is runtime-confirmed gameplay behavior. All instruction addresses are bus addresses; subtract `0x08000000` for ROM file offsets. RAM and MMIO addresses have no ROM offsets.

## Function boundary, interface and return

Entry is **`0x08075970`** / file **`0x00075970`**. The last executable instruction is **`0x08075AEC`**, `bx r0`; the executable envelope ends at **`0x08075AEE`**. The following alignment/pool data is not code. The surrounding extent through `0x08075AFC` contains final literal words, not a longer executable tail.

The complete control-flow body consists of:

- `[0x08075970,0x080759D0)`: setup and computed dispatch.
- Nine case entries `0x08075A04 + n*0x14`, n=0..8: each has 14 executable bytes. Eight cases branch to `0x08075AB0`; the ninth falls through to it. Intervening alignment and literal words are excluded.
- `[0x08075AB0,0x08075AEE)`: common arithmetic, flags and epilogue.

The switch address table is `[0x080759E0,0x08075A04)`. The actual table values justify the nine explicit Thumb seeds; Ghidra's automatic switch recovery is not assumed. The prologue saves r4-r7/LR; r7 preserves input r1, r6 preserves the low eight bits of input r0. Ordinary Thumb BL calls and the matching epilogue support the instruction mode. `mov pc,r0` case transfers remain in Thumb mode; even case-address words are not ARM-entry evidence.

| Register at entry | Observed role | Confidence |
| --- | --- | --- |
| r0 | Low eight bits are a one-based original-record ID, `g`. | Confirmed static indexing; valid supported IDs 1..50 from prior manifests |
| r1 | Caller-provided writable result pointer, `P`; 17 bytes are written. | Confirmed static output interface |
| r2/r3 | No entry value contributes to the recovered calculation; overwritten before relevant use. | Confirmed static local data flow |
| r4-r7 | Saved/restored; not recovered public argument registers. | Confirmed static |

**This function does not return the calculated attack value in r0.** At `0x08075AE8` it restores r4-r7, at `0x08075AEA` it pops the saved return address into r0, and at `0x08075AEC` it branches through r0. Its useful results are memory writes to P, giving a void-like interface. A caller that needs a scalar reloads it from P. The register return therefore must not be followed as though it were damage or strength.

## Memory sources and output schema

Let `R = 0x0862C250 + (g-1)*0x58`. Routine `0x0807565C` searches the party/storage area and returns the first matching three-byte entry `S`; separate calls obtain S for `S[2]` and `S[1]`. For ordinary stable state, they identify the same entry. Search storage starts at IWRAM `0x03001EDC`, group stride `0x60`, with up to 20 triples beginning at group `+8`; group count is byte `0x030035F0`. Existing `asm/menu.asm` and `asm/menu_gimmicks.asm` identify the same stride/base as character data, corroborating a party Gimmick-state interpretation. The complete search routine is `[0x0807565C,0x080756A8)`.

Every verified caller supplies:

```text
M = 0x03004FF8
B = read32(M + 8)
P = B + 0x5AE8
```

B is a live pointer; its exact runtime value is not recovered from static ROM bytes. These offsets describe a menu cache, not the original 0x58-byte record or loader work structure at `0x03003F34`.

| Result offset | Width | Exact source / calculation | Observed consumer / interpretation |
| --- | --- | --- | --- |
| `P+0x00` / `B+0x5AE8` | u16 | Zero-extended byte `read8(0x0200EF06 + 2*g)` | Numeric display at y=16; one per-ID usage value. Used/remaining/total convention still unresolved. |
| `P+0x02` / `B+0x5AEA` | u16 | Zero-extended byte `read8(0x0200EF07 + 2*g)` | Paired numeric display at y=16; second per-ID usage value. |
| `P+0x04` / `B+0x5AEC` | u16 | `S[2]` | Current value in the Battery display; also gauge numerator. Battery/upgrade count Probable. |
| `P+0x06` / `B+0x5AEE` | u16 | `R[0x23]` | Battery capacity display and gauge denominator; independently caps increases to S[2]. Cap operation Confirmed, battery-capacity meaning Probable. |
| `P+0x08` / `B+0x5AF0` | u16 | `R[0x22] + S[2]` | Numeric Attack-section value at y=32. Unscaled attack/strength interpretation Probable. |
| `P+0x0A` / `B+0x5AF2` | u16 | Difficulty-selected percentage scaling of `P+8`, detailed below. | Numeric Attack-section value at y=40. Difficulty-adjusted attack/strength interpretation Probable; actual damage Unconfirmed. |
| `P+0x0C` / `B+0x5AF4` | u16 | `S[1]` | Difficulty number and meter; S[1] is adjusted by the input routine below. Difficulty setting Probable. |
| `P+0x0E` / `B+0x5AF6` | u8 | Masked bit from EWRAM bitmap `0x0200EF6C`, indexed by g | Conditional symbol display; meaning Unconfirmed. It is a raw masked bit, not necessarily normalized 0/1. |
| `P+0x0F` / `B+0x5AF7` | u8 | `R[0x27] >> 7` | Conditional symbol display; flag meaning Unconfirmed. |
| `P+0x10` / `B+0x5AF8` | u8 | `R[0x27] & 0x0F`, via `0x080754B0` | Nonzero value indexes symbols at `0x0845700C + 4*(value-1)`; gameplay category/effect meaning unresolved. |

`0x08069F60` implements the bitmap read through utility block `0x030018BC`: it reads bit index g from utility halfword `+4`, uses byte offset `g>>3`, selects mask byte from `0x0863A01C + (g&7)`, ANDs that with the bitmap byte, and writes the result to utility `+1`. The calculation then copies it into `P+0x0E`. No AWE meaning is derived from this bit access.

The calculation does not explicitly validate zero ID, record range, successful S lookup, or a caller-supplied buffer size. State assumptions and valid callers need runtime checking; static disassembly does not assert an observed failure.

## Reconstructed arithmetic

For valid selector `d = S[1]` in 1..9:

```text
b = S[2]                          # zero-extended state byte
a = R[0x22]                       # zero-extended original byte
c = R[0x28 + 2*(d-1)]             # even member of selected pair
P.u16[+8] = a + b
P.u16[+A] = trunc_toward_zero((a + b) * c / 100)
```

The three operands are unsigned bytes, so the ordinary product is nonnegative and fits signed 32-bit; the quotient is integer floor in this domain. Ghidra confirms call `0x08075AB8 -> 0x080F7B08`, whose signed quotient implementation was decoded previously and in this run. The result is stored with `strh`, not rounded. No random draw or HP write is present; no defence or AWE input is identified among the recovered sources.

If d is outside 1..9, the function skips loading c and reaches multiplication with the incoming preserved r5 value. No valid multiplier is established on that path; the formula above deliberately excludes it. Do not infer a clamp, default coefficient or tenth difficulty.

The odd pair bytes `+0x29/+0x2B/.../+0x39` are **not read by this function**. They remain connected to the loader's separate packed decoding. Difficulty selector 1..7 is evidenced in the UI controller below; the arithmetic has nine cases, which does not prove nine player-selectable difficulties.

## Verified callers and result destinations

Seven even-offset Thumb BL encodings target `0x08075970`, and all seven decode as calls within the scoped caller code. A scan for raw little-endian words `0x08075970` and Thumb pointer `0x08075971` at **all byte alignments** finds zero matches. This supplies no identifiable constant indirect reference; computed/encoded references, ARM veneers and indirect dispatch remain outside an exhaustive caller proof.

| Caller entry | Call instruction | ID source | Subsequent consumption |
| --- | --- | --- | --- |
| `0x08076E28` | `0x08076E46` | Byte in B's two-byte list at `B+0x2E00 + 2*M[0x17]` | Reads cached fields; `P+8/+A` feed decimal sprites, `P+4/+6` feed Battery numbers, `P+C` feeds Difficulty number. |
| `0x080770A8` | `0x0807715E` | Same menu list formula | `0x0807716A` loads `P+C` for `0x08079B78`; caller later invokes `0x08076E28` and `0x08078CAC`. Label setup uses Uses/Attack/Battery/Difficulty descriptors. |
| `0x08078550` | `0x08078604` | Selected party triple `read8(0x03001EDC+8+0x60*M[0x14]+3*M[0x17])` | `P+4/+6` go to ratio-gauge renderer `0x08081340` at `0x0807862A`, destination `B+0x3498`, descriptor `0x084906B8`. |
| `0x0807892C` | `0x08078ABE` | Same selected party triple, saved in r9 | Draws cached numeric values and flags; Attack `P+8/+A` at `0x08078B04/0x08078B16`; Battery values at `0x08078B28/0x08078B3A`; Difficulty at `0x08078B4C`. |
| `0x08078CAC` | `0x08078D76` | Low byte of entry r2, saved as r7 | Reads `P+4/+6`, sends to `0x08081340` at `0x08078D96`; rendering destination derives from entry r1. |
| `0x0807995C` | `0x0807997E` | Selected party triple | Attack values feed `0x080742B8` at `0x080799C0/0x080799D2`; Difficulty at `0x080799E4`; usage values and conditional symbols are also rendered. No Battery-number read was identified in this caller. |
| `0x08080C84` | `0x08080EB4` | Selected party triple, or menu list when byte `0x03001970` equals 2 | After item action, refreshes P; reads `P+4/+6` for `0x08081340` at `0x08080ED4`, destination VRAM `0x06007800`. |

All call sites and entries are ROM bus addresses, with file offsets obtained by subtracting `0x08000000`; e.g. `0x0807997E` corresponds to `0x0007997E`. r0 is overwritten after the calculation or another helper is called; none forwards a calculated scalar from r0. The post-call halfword reads are the real result flow.

## UI evidence and downstream arithmetic

`0x080770A8` loads descriptors `0x08490498`, `0x084904A0`, `0x084904A8`, `0x084904B0` and calls the existing text-drawing target `0x080748BC`. `ta_menus_eng.txt:663-672` maps these to **Uses, Attack, Battery, Difficulty**. This is direct source label evidence combined with decoded caller layout, not an arbitrary name inferred from byte values.

`0x08076E28` and `0x0807892C` place `P+8` at `(224,32)` and `P+A` at `(224,40)` using `0x080742B8`; `0x0807995C` places them at `(112,56)` and `(112,64)`. These rows are consistent with the Attack section. The exact visible layout/meaning of the two Attack numbers should still be photographed in mGBA. Battery `P+4/+6` appears as paired numbers with a separating symbol and as a ratio gauge; the current/cap interpretation is additionally supported by the cap writer below.

The downstream arithmetic identified here is rendering arithmetic:

- **`0x080742B8..0x08074308`**: r0/r1 carry coordinates, r2 the displayed integer, r3 a display attribute. It obtains a decimal remainder using `0x080F7CE8` with divisor 10, indexes a digit sprite-pointer table at `0x08456C70`, calls `0x080744FC`, moves x left by 8, obtains a quotient using `0x080F7C70`, and repeats while nonzero. Modulo/division semantics of those library helpers are Probable from this digit loop; their full implementations were not newly analyzed.
- **`0x080744FC..0x080745B8`**: copies sprite records, adjusts 8-bit y and 9-bit x attributes, applies a palette/display nibble, and writes records into IWRAM OAM staging `0x030014B8` using target `0x080942E4`. Caller `0x080770A8` then sets up DMA3 from `0x030014B8` to `0x07000000` at `0x08077230..40`. This is a concrete display sink, not an HP write.
- **`0x08081340..0x08081400`**: r0 is destination base, r1/r2 numerator/denominator, r3 and stack metadata describe the gauge. It computes a fixed-point width from `(width<<16)/denominator`, multiplies by numerator, shifts by 16, divides the pixel span into groups of 8 and a remainder, selects ROM halfword patterns, and sets up DMA3 (`0x040000D4`) into a destination derived from r0. Callers use `P+4/+6`, not `P+A`. The equality case adds one pixel. These operations establish ratio-gauge rendering; zero-denominator behavior and live display geometry require verification.
- **`0x08079B78..0x08079BFA`**: takes the low byte of `P+C`, builds a small meter from halfwords at `0x084907E4..EA`, and DMA-copies seven halfwords into the screen/VRAM destination. Comparisons against 7 affect the final marker. This is display consumption of the selector, not a power calculation.

## Difficulty selection and battery/upgrade progression

**Selector writer `0x08079AE4..0x08079B62` (Confirmed static):** computes selected entry byte address `0x03001EDC + 8 + 0x60*M[0x14] + 3*M[0x17] + 1`. It tests masks `0x100` and `0x200` in halfword `0x030019C6`. The first increments the byte only when it is at most 6; the second decrements only when above 1. For ordinary initial state this constrains adjustment to **1..7**. It redraws the same byte through `0x08079B78`.

The caller `0x080791E8` invokes this writer at `0x0807929C`. The help-text renderer `0x08079C14` uses descriptors `0x084904C0/0x084904C8`, whose English manifests explicitly instruct L/R difficulty adjustment (`ta_menus_eng.txt:675-685`). Together this strongly supports S[1] as the difficulty setting and the even record bytes as difficulty-dependent Attack multipliers (**Probable gameplay interpretation**). The initial state and special settings 8/9 remain unknown. The separate loader uses the same selector convention, but this report does not trace a complete minigame execution path from these UI handlers.

**Additive-state writer `0x08081188..0x080811CA` (Confirmed static):** r0 is low-byte Gimmick ID, r1 is low-byte increment. It calls `0x0807565C`, reads `R[0x23]`, updates S[2], compares the truncated byte to the cap, and stores the cap if exceeded:

```text
t = (S[2] + (r1 & 0xFF)) & 0xFF
S[2] = min(t, R[0x23])
```

The byte truncation occurs **before** the comparison; this formula must not be silently replaced by an unbounded saturating addition. Normal item increments observed below are 1/3/5, and the cap/check structure is separate from any proposed mod limit.

Caller **`0x08080D8C -> 0x08081188`**, within `0x08080C84`, passes the selected Gimmick ID and byte `+9` of an item record. Item record base is `0x08630E5C`, stride `0x10`, with one-based input ID. Low-five-bit action types 26..29 in item byte `+8` select the table case at `0x08080D88`; the item amount is forwarded in r1. The subsequent item-action dispatch can reach `0x08080EB4`, recomputing P and redrawing its Battery gauge. The source item-name and description manifests associate this family with Cells/Volts/Stars and Attack up 1/3/5 (`ta_menus_eng.txt:414-437`, `RESTRUCT` at line 1413). The menu tutorial at descriptor `0x084907BC` also says Cell use increases attack power (`ta_menus_eng.txt:1134-1157`). This supports S[2] as a battery/upgrade quantity which contributes additively to displayed Attack; it is not an AWE segment value or a demonstrated Kaizo progression counter.

## Stronger field interpretations and where the trace stops

| Original field | Strongest interpretation now supported | Confidence and limit |
| --- | --- | --- |
| `+0x22` | Base component of an Attack-section value, with the mutable battery/upgrade byte added. | Addition and UI consumption Confirmed static; base attack/strength Probable. Exact battle-damage role Unconfirmed. |
| `+0x23` | Cap on the mutable additive byte; displayed Battery maximum and gauge denominator. | Cap, display and ratio roles Confirmed static; battery/upgrade capacity Probable. It is not demonstrated maximum damage. |
| Even `+0x28..+0x38` | Percentage coefficients selected by the mutable difficulty byte; applied to base plus upgrade. | Arithmetic and selection Confirmed static; difficulty-adjusted Attack scaling Probable. Reachability/meaning of settings 8/9 Unconfirmed. |
| Odd `+0x29..+0x39` | Still handled separately by the earlier loader. | No new interpretation from this function. |

The trace reaches **UI numbers, OAM staging, tile/gauge data and DMA display writes**, plus difficulty and upgrade-state writers. It does **not** reach an enemy/character HP subtraction, defence interaction, Gimmick performance outcome, random multiplier, or AWE gain/spend routine. No known caller directly computes battle damage from P+A. Aligned raw word matches for cache offsets `0x5AF0/0x5AF2` are confined to literal slots in the three decoded numeric-display contexts; this is a search result, not proof no alias-based consumer exists.

The precise unresolved link is between the **displayed adjusted Attack** at `P+0x0A` and the **battle-time calculation**. The cache's dynamic B value, additional global readers, callback dispatch and battle record aliases were not exhaustively traced. Actual battle damage may independently recompute related fields instead of reading this menu cache. Static absence here cannot establish that displayed Attack is unrelated to damage. No specific Kaizo threshold or cap is identified.

## Translation compatibility

Read-only byte comparison finds zero differing bytes in these half-open bus ranges (file range = bus minus `0x08000000`):

| Range | Comparison purpose |
| --- | --- |
| `[0x08075970,0x08075AFC)` | Entire calculation envelope, case/pool data, flags and epilogue |
| `[0x0807565C,0x080756A8)` | State lookup and its in-body literals |
| `[0x08079AE4,0x08079B78)` | Selector writer and following literal pool |
| `[0x08081188,0x080811D0)` | Additive-state increment/cap writer and literal |

This confirms local numeric-code compatibility of these supplied ROMs. It does not certify all UI code or the translation globally. The earlier loader's original byte-load versus translated unaligned word-load at `+0x27` remains a separate runtime issue; it is not an instruction difference in this calculation.

## Required runtime verification and next step

The best next step is **mGBA runtime debugging** focused on this now-recovered interface. Use an owned, named Gimmick and record emulator version, save/location, entry r0/r1 and LR at `0x08075970`, live B, matched S and all 17 output bytes. Break at `0x08075ABC` to observe the quotient write; compare unscaled/adjusted Attack values with the visible menu. Test difficulty 1 and 7, then one Cell/Volt/Star increase while watching S[1]/S[2] at writers `0x08079B14`, `0x08079B32`, `0x080811B0`, `0x080811BA`.

Next, use the same Gimmick in battle. Capture reads of its ROM `+0x22`, its state S[2], and its selected even coefficient, then follow those actual PCs to performance scaling and the eventual HP write. Watch P+0x0A as well, but do not rely only on that watchpoint: battle code may recompute from original/state records. This will identify the next bounded static target and resolve whether the displayed value participates in damage. AWE/Kaizo investigations remain separate until an actual data-flow link appears.

## Instruction evidence

The appendix below is extracted from the successful Ghidra run. It contains the complete calculation and selected supporting contexts; the ignored full trace retains all seven callers and rendering/helper windows. Numeric routine identifiers are addresses, not newly assigned gameplay symbols.

<!-- generated-ghidra-calculation-evidence -->

Trace SHA-256: `d9f58b6d76c1f36d0948479f34b41b563dc6723081eafe02a7b5aa0afb5456cc`.

### Complete calculation function

```text
BLOCK 08075970..08075aed (inclusive window, data gaps omitted)
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
08075a04  ldr r2,[0x08075a14]
  REF READ 08075a14 literal=0862c250
08075a06  sub r1,r6,#0x1
08075a08  mov r0,#0x58
08075a0a  mul r0,r1
08075a0c  add r0,r0,r2
08075a0e  add r0,#0x28
08075a10  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a18  ldr r2,[0x08075a28]
  REF READ 08075a28 literal=0862c250
08075a1a  sub r1,r6,#0x1
08075a1c  mov r0,#0x58
08075a1e  mul r0,r1
08075a20  add r0,r0,r2
08075a22  add r0,#0x2a
08075a24  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a2c  ldr r2,[0x08075a3c]
  REF READ 08075a3c literal=0862c250
08075a2e  sub r1,r6,#0x1
08075a30  mov r0,#0x58
08075a32  mul r0,r1
08075a34  add r0,r0,r2
08075a36  add r0,#0x2c
08075a38  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a40  ldr r2,[0x08075a50]
  REF READ 08075a50 literal=0862c250
08075a42  sub r1,r6,#0x1
08075a44  mov r0,#0x58
08075a46  mul r0,r1
08075a48  add r0,r0,r2
08075a4a  add r0,#0x2e
08075a4c  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a54  ldr r2,[0x08075a64]
  REF READ 08075a64 literal=0862c250
08075a56  sub r1,r6,#0x1
08075a58  mov r0,#0x58
08075a5a  mul r0,r1
08075a5c  add r0,r0,r2
08075a5e  add r0,#0x30
08075a60  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a68  ldr r2,[0x08075a78]
  REF READ 08075a78 literal=0862c250
08075a6a  sub r1,r6,#0x1
08075a6c  mov r0,#0x58
08075a6e  mul r0,r1
08075a70  add r0,r0,r2
08075a72  add r0,#0x32
08075a74  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a7c  ldr r2,[0x08075a8c]
  REF READ 08075a8c literal=0862c250
08075a7e  sub r1,r6,#0x1
08075a80  mov r0,#0x58
08075a82  mul r0,r1
08075a84  add r0,r0,r2
08075a86  add r0,#0x34
08075a88  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075a90  ldr r2,[0x08075aa0]
  REF READ 08075aa0 literal=0862c250
08075a92  sub r1,r6,#0x1
08075a94  mov r0,#0x58
08075a96  mul r0,r1
08075a98  add r0,r0,r2
08075a9a  add r0,#0x36
08075a9c  b 0x08075ab0
  REF UNCONDITIONAL_JUMP 08075ab0
08075aa4  ldr r2,[0x08075af0]
  REF READ 08075af0 literal=0862c250
08075aa6  sub r1,r6,#0x1
08075aa8  mov r0,#0x58
08075aaa  mul r0,r1
08075aac  add r0,r0,r2
08075aae  add r0,#0x38
08075ab0  ldrb r5,[r0,#0x0]
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
```

### Selected writer and renderer contexts

```text
BLOCK 080742b8..08074307 (inclusive window, data gaps omitted)
080742b8  push {r4,r5,r6,r7,lr}
080742ba  mov r7,r8
080742bc  push {r7}
080742be  add r4,r2,#0x0
080742c0  lsl r0,r0,#0x10
080742c2  lsr r5,r0,#0x10
080742c4  lsl r3,r3,#0x18
080742c6  lsr r7,r3,#0x18
080742c8  ldr r0,[0x08074308]
  REF READ 08074308 literal=08456c70
080742ca  mov r8,r0
080742cc  lsl r6,r1,#0x10
080742ce  add r0,r4,#0x0
080742d0  mov r1,#0xa
080742d2  bl 0x080f7ce8
  REF UNCONDITIONAL_CALL 080f7ce8
080742d6  lsl r0,r0,#0x2
080742d8  add r0,r8
080742da  ldr r0,[r0,#0x0]
080742dc  lsl r1,r5,#0x10
080742de  asr r1,r1,#0x10
080742e0  asr r2,r6,#0x10
080742e2  add r3,r7,#0x0
080742e4  bl 0x080744fc
  REF UNCONDITIONAL_CALL 080744fc
080742e8  add r0,r5,#0x0
080742ea  sub r0,#0x8
080742ec  lsl r0,r0,#0x10
080742ee  lsr r5,r0,#0x10
080742f0  add r0,r4,#0x0
080742f2  mov r1,#0xa
080742f4  bl 0x080f7c70
  REF UNCONDITIONAL_CALL 080f7c70
080742f8  add r4,r0,#0x0
080742fa  cmp r4,#0x0
080742fc  bne 0x080742ce
  REF CONDITIONAL_JUMP 080742ce
080742fe  pop {r3}
08074300  mov r8,r3
08074302  pop {r4,r5,r6,r7}
08074304  pop {r0}
08074306  bx r0

BLOCK 08079b78..08079bf9 (inclusive window, data gaps omitted)
08079b78  push {r4,r5,r6,r7,lr}
08079b7a  sub sp,#0x10
08079b7c  add r6,r0,#0x0
08079b7e  lsl r1,r1,#0x18
08079b80  lsr r3,r1,#0x18
08079b82  ldr r0,[0x08079b90]
  REF READ 08079b90 literal=03004ff5
08079b84  ldrb r0,[r0,#0x0]
08079b86  cmp r0,#0x5
08079b88  bne 0x08079b94
  REF CONDITIONAL_JUMP 08079b94
08079b8a  mov r7,#0x15
08079b8c  mov r0,#0x4
08079b8e  b 0x08079b98
  REF UNCONDITIONAL_JUMP 08079b98
08079b94  mov r7,#0x14
08079b96  mov r0,#0xb
08079b98  mov r1,#0x0
08079b9a  ldr r4,[0x08079bfc]
  REF READ 08079bfc literal=084907e6
08079b9c  lsl r5,r0,#0x5
08079b9e  ldr r0,[0x08079c00]
  REF READ 08079c00 literal=084907e4
08079ba0  ldrh r2,[r0,#0x0]
08079ba2  lsl r0,r1,#0x1
08079ba4  add r0,sp
08079ba6  strh r2,[r0,#0x0]
08079ba8  add r0,r1,#0x1
08079baa  lsl r0,r0,#0x18
08079bac  lsr r1,r0,#0x18
08079bae  cmp r1,#0x5
08079bb0  bls 0x08079ba2
  REF CONDITIONAL_JUMP 08079ba2
08079bb2  mov r1,sp
08079bb4  ldrh r0,[r4,#0x0]
08079bb6  strh r0,[r1,#0xc]
08079bb8  mov r1,#0x0
08079bba  cmp r1,r3
08079bbc  bcs 0x08079bd2
  REF CONDITIONAL_JUMP 08079bd2
08079bbe  ldr r0,[0x08079c04]
  REF READ 08079c04 literal=084907e8
08079bc0  ldrh r2,[r0,#0x0]
08079bc2  lsl r0,r1,#0x1
08079bc4  add r0,sp
08079bc6  strh r2,[r0,#0x0]
08079bc8  add r0,r1,#0x1
08079bca  lsl r0,r0,#0x18
08079bcc  lsr r1,r0,#0x18
08079bce  cmp r1,r3
08079bd0  bcc 0x08079bc2
  REF CONDITIONAL_JUMP 08079bc2
08079bd2  cmp r3,#0x7
08079bd4  bne 0x08079bde
  REF CONDITIONAL_JUMP 08079bde
08079bd6  mov r0,sp
08079bd8  ldr r1,[0x08079c08]
  REF READ 08079c08 literal=084907ea
08079bda  ldrh r1,[r1,#0x0]
08079bdc  strh r1,[r0,#0xc]
08079bde  add r0,r5,r7
08079be0  lsl r0,r0,#0x1
08079be2  add r0,r6,r0
08079be4  ldr r1,[0x08079c0c]
  REF READ 08079c0c literal=040000d4
08079be6  mov r2,sp
08079be8  str r2,[r1,#0x0]
08079bea  str r0,[r1,#0x4]
08079bec  ldr r0,[0x08079c10]
  REF READ 08079c10 literal=80000007
08079bee  str r0,[r1,#0x8]
08079bf0  ldr r0,[r1,#0x8]
08079bf2  add sp,#0x10
08079bf4  pop {r4,r5,r6,r7}
08079bf6  pop {r0}
08079bf8  bx r0

BLOCK 08079ae4..08079b61 (inclusive window, data gaps omitted)
08079ae4  push {r4,lr}
08079ae6  ldr r2,[0x08079b64]
  REF READ 08079b64 literal=03004ff8
08079ae8  ldrb r0,[r2,#0x14]
08079aea  lsl r1,r0,#0x1
08079aec  add r1,r1,r0
08079aee  lsl r1,r1,#0x5
08079af0  ldr r0,[0x08079b68]
  REF READ 08079b68 literal=03001ee4
08079af2  add r1,r1,r0
08079af4  ldrb r2,[r2,#0x17]
08079af6  lsl r0,r2,#0x1
08079af8  add r0,r0,r2
08079afa  add r0,#0x1
08079afc  add r4,r1,r0
08079afe  ldr r0,[0x08079b6c]
  REF READ 08079b6c literal=030019c6
08079b00  ldrh r1,[r0,#0x0]
08079b02  mov r0,#0x80
08079b04  lsl r0,r0,#0x1
08079b06  and r0,r1
08079b08  cmp r0,#0x0
08079b0a  beq 0x08079b1c
  REF CONDITIONAL_JUMP 08079b1c
08079b0c  ldrb r0,[r4,#0x0]
08079b0e  cmp r0,#0x6
08079b10  bhi 0x08079b1c
  REF CONDITIONAL_JUMP 08079b1c
08079b12  add r0,#0x1
08079b14  strb r0,[r4,#0x0]
08079b16  mov r0,#0x19
08079b18  bl 0x08092e70
  REF UNCONDITIONAL_CALL 08092e70
08079b1c  ldr r0,[0x08079b6c]
  REF READ 08079b6c literal=030019c6
08079b1e  ldrh r1,[r0,#0x0]
08079b20  mov r0,#0x80
08079b22  lsl r0,r0,#0x2
08079b24  and r0,r1
08079b26  cmp r0,#0x0
08079b28  beq 0x08079b3a
  REF CONDITIONAL_JUMP 08079b3a
08079b2a  ldrb r0,[r4,#0x0]
08079b2c  cmp r0,#0x1
08079b2e  bls 0x08079b3a
  REF CONDITIONAL_JUMP 08079b3a
08079b30  sub r0,#0x1
08079b32  strb r0,[r4,#0x0]
08079b34  mov r0,#0x19
08079b36  bl 0x08092e70
  REF UNCONDITIONAL_CALL 08092e70
08079b3a  ldr r0,[0x08079b70]
  REF READ 08079b70 literal=06007800
08079b3c  ldr r4,[0x08079b74]
  REF READ 08079b74 literal=03001edc
08079b3e  ldr r3,[0x08079b64]
  REF READ 08079b64 literal=03004ff8
08079b40  ldrb r1,[r3,#0x17]
08079b42  lsl r2,r1,#0x1
08079b44  add r2,r2,r1
08079b46  ldrb r3,[r3,#0x14]
08079b48  lsl r1,r3,#0x1
08079b4a  add r1,r1,r3
08079b4c  lsl r1,r1,#0x5
08079b4e  add r1,#0x1
08079b50  add r2,r2,r1
08079b52  add r4,#0x8
08079b54  add r2,r2,r4
08079b56  ldrb r1,[r2,#0x0]
08079b58  bl 0x08079b78
  REF UNCONDITIONAL_CALL 08079b78
08079b5c  pop {r4}
08079b5e  pop {r0}
08079b60  bx r0

BLOCK 08081188..080811c9 (inclusive window, data gaps omitted)
08081188  push {r4,r5,lr}
0808118a  add r4,r0,#0x0
0808118c  add r5,r1,#0x0
0808118e  lsl r4,r4,#0x18
08081190  lsr r4,r4,#0x18
08081192  lsl r5,r5,#0x18
08081194  lsr r5,r5,#0x18
08081196  add r0,r4,#0x0
08081198  bl 0x0807565c
  REF UNCONDITIONAL_CALL 0807565c
0808119c  add r2,r0,#0x0
0808119e  ldr r1,[0x080811cc]
  REF READ 080811cc literal=0862c250
080811a0  sub r4,#0x1
080811a2  mov r0,#0x58
080811a4  mul r0,r4
080811a6  add r0,r0,r1
080811a8  add r0,#0x23
080811aa  ldrb r1,[r0,#0x0]
080811ac  ldrb r0,[r2,#0x2]
080811ae  add r5,r5,r0
080811b0  strb r5,[r2,#0x2]
080811b2  lsl r5,r5,#0x18
080811b4  lsr r5,r5,#0x18
080811b6  cmp r5,r1
080811b8  bls 0x080811bc
  REF CONDITIONAL_JUMP 080811bc
080811ba  strb r1,[r2,#0x2]
080811bc  mov r0,#0x2a
080811be  bl 0x08092e70
  REF UNCONDITIONAL_CALL 08092e70
080811c2  mov r0,#0x1
080811c4  pop {r4,r5}
080811c6  pop {r1}
080811c8  bx r1
```
