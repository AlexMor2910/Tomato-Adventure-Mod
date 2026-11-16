# Gimmick Battle Arithmetic and Target-Value Candidates

## Target quantity source and post-subtraction audit

Bounded Ghidra rerun: `reverse_engineering/ghidra/run-77915b5e283f445b852f06c5942e10dd/loader.txt`, `TRACE_COMPLETE`. The existing script now also decodes `0x080418C0..0x08041904`, `0x08041C9C..0x08041D02`, and the basic-block region `0x08049890..0x08049938`. The last is a scoped block, not a newly established function boundary. All seven compared Japanese/English spans are byte-identical. No whole-ROM auto-analysis was performed.

### Proven source of the operand, unresolved meaning

`0x0804876C` loads T+0x18; `0x0804876E` loads T+0x14; `0x08048770` sums them. The low halfword is interpreted as signed for the bounds: nonpositive becomes 1, values above 999 become 999. That bounded sum is the runtime-observed r0=10 at `0x08048794`. Neither individual halfword was captured live, so their split must not be inferred from the total.

At Thumb function `0x080418C0`, entry r0 supplies an input pointer and low-byte r1 a context index. It reads a selector byte, calls `0x08041114` for a target index, then copies two following bytes through `0x080F954C` into a stack temporary. The following verified instructions store that halfword into target +0x14:

```text
080418da  mov r0,sp
080418dc  add r1,r6,#0       ; source cursor after selector byte
080418de  mov r2,#2
080418e0  bl 080f954c       ; two-byte copy call; helper body not expanded here
080418e4  add r6,#2
080418e6  ldr r1,[08041908] ; 03000A40
080418e8..ee               ; target pointer = base + r4*0x38
080418f0  mov r1,sp
080418f2  ldrh r1,[r1,#0]
080418f4  strh r1,[r0,#0x14]
```

The advanced cursor is stored in `0x0300074C + context*4` at `0x080418FC`, supporting a **Candidate script/input-stream setter** interpretation. This is a real writer, but it is not proven to initialize this particular enemy's 10-point operand. Trace stops at the incoming cursor and target-selection helper; stream origin/opcode, enemy-definition initializer, and last writer for this replay remain unresolved. No Defense label is assigned.

For +0x18, `0x08041CDE` clears it during a target reset that also clears flags and copies +0x10 to current HP. In the scoped `0x08049890` block, target is selected by byte `0x03000BB9`; `0x080498BC` conditionally clears +0x18 under target flag 0x40. `0x080498FA` adds `2*read8(r7+8)` to +0x18; `0x08049926` subtracts the same amount when target byte +9 exceeds 6. Source r7 and block dispatch remain untraced. Thus +0x18 is mutable, with an additive/removal path; naming it a particular status or defence bonus would be premature.

### Remaining modifiers between scratch store and HP write

| Instructions | Static effect | Tested Gear-Yo evidence |
| --- | --- | --- |
| `0x08048798..EA` | Record +0x27 bit 7 gates BAF=2 → 80%, BAF=3 → 70%; otherwise bypass | Branch inputs not captured; positive 16 would become 12 or 11 if applied |
| `0x080487EC..F8` | Signed result <=0 becomes 1 | Positive 16 does not meet condition |
| `0x08048802..10` | Target +0x0A bit 0x4000 makes scratch zero | Final measured damage 16 excludes suppression for tested action |
| `0x08046DEA..DF0` | Pass scratch to probable numeric display `0x0804B2F0` | This callee's further callees were not exhaustively audited for aliases |
| `0x08046DFA..E02` | Reload scratch; subtract it from target HP and store | Confirmed runtime HP 24 minus 16 becomes 8 |
| `0x08046E04..0A` | Clamp negative signed HP to zero after store | Not triggered by measured HP 8; knockout behavior untested |

The caller contains no extra damage multiply/divide between display return and HP subtraction. The net result remains 16 in the reported tests, but a continuous branch/alias trace has not been supplied. No RNG source is identified.

### Next verification and balance-prototype readiness

The smallest useful next replay stops at `0x0804876C`, before loading the two source fields. For the known target 0, record `status`, `print/x r0` (must be `0x03000A40`), `r/2 0x03000A54`, `r/2 0x03000A58`, `r/2 0x03000A4A`, `r/1 0x03000BAF`, and `r/1 0x0862C277` (Gear-Yo +0x27). This separates the 10-point quantity and identifies the known post-subtraction gates without changing memory. If the pointer differs, calculate addresses from that live target pointer. To trace initialization later, arm one write watchpoint on the measured nonzero source field from a **new earlier battle-entry checkpoint**; the present minigame checkpoint may be too late. Capture the actual writer PC and registers rather than assuming the setter above ran.

**Enough evidence for a narrowly scoped experimental prototype design: yes.** Gear-Yo original base byte `0x0862C272` (file `0x0062C272`, record +0x22) feeds both menu and this confirmed battle path; a future +1 base-byte experiment is more isolated than changing shared arithmetic or target fields. With unchanged upgrade/coefficient/path, 21→22 and coefficient 124 predict menu/pre-subtraction 27 and damage 17 against the same measured subtraction quantity 10. Those are predictions, not modified-ROM results. Preserve originals, assert the expected original byte and ROM fingerprint, produce a separate derived ROM through a reproducible patch, and test the same menu/battle plus another outcome and difficulty before accepting balance. Broad release safety, other Gimmicks, upgrades, status branches and knockout behavior are not established. No patch was implemented or ROM modified; Phase 1 remains active.

## Runtime-confirmed subtraction GY-SUB-16 (2026-10-11)

Evidence: user's manual mGBA report, interpreted against the bounded Thumb disassembly. At `0x08048794`, `sub r1,r1,r0`, r1 was `0x1A` (26), r0 was `0x0A` (10); stepping produced r1=`0x10` (16). At `0x08048796`, `strh r1,[r2,#0]`, r2 was `0x03000BF8`; stepping stored `0x0010`. Subtraction, intermediate result and scratch write are **Confirmed (runtime)** for this Gear-Yo replay. The previously confirmed HP write at `0x08046E02` changed target HP `0x03000A4E` from 24 to 8, a reduction of 16. These are successive user-reported experiments, not a newly supplied continuous console transcript.

The captured battle pre-subtraction value equals the independently confirmed displayed Attack 26. The measured arithmetic is `26 - 10 = 16`; call the 10-point operand **target subtraction quantity**, not Defense. Individual source-field values were not reported. No minigame or RNG modifier is confirmed by this equality. Source tracing and the remaining conditional modifiers are documented in [battle_damage_candidates.md](battle_damage_candidates.md).

## Runtime-confirmed Gear-Yo damage and modifier trace

**Confirmed (runtime), user-reported manual mGBA experiment, 2026-10-11:** routine `0x080485B0` produced scratch `0x03000BF8 = 0x0010` (16). At `0x08046E02`, `strh r1,[r4,#14]`, target pointer r4 was `0x03000A40`, HP at `0x03000A4E` was `0x0018` (24), and r1 was `0x00000008`. Executing one instruction changed HP to `0x0008`. Thus the calculated result was the actual HP reduction: `24 - 16 = 8`. This confirms the damage output and target +0x0E HP write for this action; other targets, Gimmicks and zero-clamp/knockout behavior remain untested. Evidence is the user's report, not an agent-generated transcript.

The independently measured menu Attack is 26 at difficulty 1, upgrade 0. The subsequent subtraction capture confirms pre-subtraction 26, target quantity 10 and scratch 16. Battle coefficient/action bytes and the individual target source fields were not supplied.

### Reconstructed arithmetic and direct record dependencies

For ordinary positive, nonoverflowing inputs, the bounded Thumb disassembly yields:

```text
B = R[0x22] + Q[0x22]
k = (Q[0x21] + (2 if Q[0x23] != 0 else 0)) & 255
A = floor(B * R[0x28 + 2*k] / 100) if C65 == 1 and k <= 8 else B
V = clamp(signed16((T.u16[0x18] + T.u16[0x14]) & 65535), 1, 999)
X = A - V
if R[0x27] & 0x80:
    X = trunc_toward_zero(X * 80 / 100) if BAF == 2 else
        trunc_toward_zero(X * 70 / 100) if BAF == 3 else X
D = max(X, 1)
if T.u16[0x0A] & 0x4000: D = 0
```

`C65` and `BAF` mean bytes at `0x03000C65` and `0x03000BAF`. Intermediate scratch stores truncate to 16 bits; later signed loads matter outside the ordinary domain. Exact instructions below remain authoritative.

Direct damage dependencies **Confirmed (static)**: original record +0x22 (base), even +0x28/+0x2A/.../+0x38 (conditional percentages), and +0x27 bit 7 (conditional scaling gate). Record +0x23, +0x25, odd coefficient-pair bytes and +0x3C..+0x57 are not read directly by this function. Their indirect influence through earlier action setup is unresolved; do not call them irrelevant. Q+0x22 is a battle additive byte, not yet proven to be the persistent upgrade byte. Q+0x23 is an action flag, distinct from original record +0x23.

Target +0x14/+0x18 are confirmed subtraction inputs; a defence interpretation remains **Candidate**. Q's selector/flag could encode a performance-related adjustment, but neither their writers nor a causal minigame-result link has been identified. This trace stops at those input bytes. No PRNG call, seed update or random-number input is identified in `0x080485B0`; its calls are the selector helper and integer division. Earlier input generation remains untraced. Neither RNG nor a critical-hit/performance name is justified.

### Subtraction procedure (completed; historical)

Replay the preserved battle checkpoint with one breakpoint at **`0x08048794`**, immediately before `sub r1,r1,r0`. Remove earlier investigation points using their actual IDs. At the hit, capture `status`, `print/x r1` (pre-subtraction A), `print/x r0` (bounded target quantity V), `print/x r7` (record index), `r/2 0x03000BF8`, `r/2 0x03000A54` and `r/2 0x03000A58` (the known target's +0x14/+0x18), plus `r/1 0x03000BAF` and the actual record's +0x27 byte. Step `next` twice to execute subtraction and its scratch store, then read `r/2 0x03000BF8` again. Use target-specific addresses only if this replay is still target 0.

If A=26 and V=10, the subtraction produces 16; compare the subsequent final scratch at `0x08046DEA` to confirm later branches preserve it. If A differs from 26, the next focused capture is `0x08048754` before coefficient load: record r0 (coefficient address), r2 (B), r6 (k), and read the addressed coefficient byte. That stop is conditional; use an entry/input capture if the percentage path is bypassed. No broad RNG probe or minigame manipulation is needed for the first experiment.

The earlier sections below preserve the static discovery history. Their former Probable HP/damage status is superseded by the runtime result above, not by a universal formula validation.

## Scope and reproducibility

Phase 1, 2026-10-11. New evidence is bounded **static Ghidra disassembly** and read-only inspection of the previously fingerprinted Gear-Yo battle checkpoint. No emulator interaction, ROM/state write, gameplay patch, build or dependency installation was performed. The successful menu test remains separate from battle damage.

Ghidra 12.1.4, JDK 23.0.1, `ARM:LE:32:v4t:default`, raw Japanese ROM at bus `0x08000000`, `-noanalysis -readOnly`. Source: `tools/analyze/ghidra/TraceGimmickBattle.java`, compiled through the existing adapter. Reproduce:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/analyze/ghidra/run-loader.ps1 -Script TraceGimmickBattle
```

Successful run: `reverse_engineering/ghidra/run-3937c795ad674666ab7b2c4938e09b04/`; ignored `loader.txt` contains all scoped instructions, literal references, switch destinations, direct-call candidates and English comparisons. It ends in `TRACE_COMPLETE`. The nine switch cases were seeded from actual address words, not speculative whole-ROM analysis. Only the functions/basic blocks listed below were decoded. No gameplay function names are assigned.

| Input | SHA-256 |
| --- | --- |
| Japanese ROM | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English ROM | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Source battle checkpoint | `cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7` |

**Confirmed (static)** means an observed instruction/data-flow operation; **Confirmed (checkpoint)** means saved bytes. **Probable** describes the damage/HP interpretation supported by arithmetic and context. **Candidate** identifies an untested connection. The Gear-Yo result-to-HP path is now **Confirmed (runtime)** by the report above; other behaviors remain untested. ROM file offsets are bus minus `0x08000000`; RAM has no ROM file offset.

## Negative watchpoint result and coefficient use

The user confirmed live `0x03003F56=0x15`, `0x03003F9D=0x7C`, and state bytes at `0x03001EE4` of `01 01 00`, then armed read watchpoint #1 at `0x03003F9D`. No hit message appeared during the reported replay. The debugger's stop at BIOS `0x00000188` was explicitly **not** a watchpoint hit; continuing resumed gameplay normally. This is a negative observation for that replay, not proof the byte is never read, that watchpoints are broken, or that the UI result is battle damage.

A concrete reader exists at **`0x0802BA3A`**, in the source-known name/status display routine beginning `0x0802B7F0`. It computes from copied work-record +0x22 and derived work +0x6A, then reads work +0x69, multiplies and divides by 100. It stores the result in utility halfword `0x030018BC+0x0C`, selects VRAM destination `0x0600BAE0`, and calls `0x0802C044`. This is display-oriented data flow. Its actual timing relative to the battle checkpoint has not been measured, although the checkpoint already has the minigame running.

```text
0802ba2c  mov r3,r9               ; r9 = work+0x22
0802ba2e  ldrb r1,[r3,#0x0]
0802ba30  mov r2,r8               ; r8 = work+0x6A
0802ba32  ldrb r0,[r2,#0x0]
0802ba34  add r1,r1,r0
0802ba36  add r0,r6,#0x0          ; r6 = 03003F34
0802ba38  add r0,#0x69
0802ba3a  ldrb r0,[r0,#0x0]       ; reads 03003F9D
0802ba3c  mul r0,r1
0802ba3e  mov r1,#0x64
0802ba40  bl 0x080f7b08
0802ba44  strh r0,[r4,#0xc]       ; r4 = 030018BC
0802ba46  ldr r0,[0x0802ba90]     ; literal 0600BAE0
0802ba48  str r0,[r4,#0x8]
0802ba4c  bl 0x0802c044
```

No transfer of that coefficient byte to an HP calculation was confirmed. A preliminary raw-literal/local-register scan was used only to choose seeds; it is not an exhaustive alias, ARM, DMA or indirect-reference analysis. Ghidra independently validates this particular reader. An earlier action-selection checkpoint would be necessary to establish whether it executes before the supplied minigame checkpoint.

## Separate battle-side recomputation at 0x080485B0

Entry **`0x080485B0`**, return `0x0804881C`, Thumb. Static prologue saves r4-r7, r8/r9 and LR. Input low byte r0 selects target index t, preserved in r9. The routine writes a halfword scratch result at **`0x03000BF8`**; r0 at return is the saved return address, not the arithmetic result.

Inputs are fetched from battle-side records, not the menu output P:

```text
a = read8(03000BB6)
s = read8(03000C30 + a)
Q = 03000938 + a*0x84 + s*4
i = read8(Q+0x20)                # zero-based original Gimmick record index
u = read8(Q+0x22)                # additive battle-side byte; source writer unresolved
R = 0862C250 + i*0x58
T = 03000A40 + t*0x38            # target-record candidate
```

Helper **`0x080484CC..0x080484F8`** returns `read8(Q+0x21)`, adding 2 (with byte truncation) when `read8(Q+0x23)` is nonzero. Call at `0x080485DA` supplies actor/slot indices already used to select Q. This yields an effective zero-based coefficient index k; it must not be equated blindly with the menu's one-based selector d. Meaning of the auxiliary Q+0x23 flag and the source writes into these action fields are unresolved.

At **`0x08048602..06`**, original record +0x22 plus u is stored in the scratch halfword. If byte `0x03000C65` is 1 and k is 0..8, actual switch table `[0x08048640,0x08048664)` selects original even bytes `R+0x28+2*k`. The common block scales the scratch:

```text
08048600  add r0,#0x22
08048602  ldrb r0,[r0,#0x0]       ; original record base byte
08048604  add r0,r0,r2            ; r2 = Q[+0x22]
08048606  strh r0,[r3,#0x0]       ; r3 = 03000BF8
...
08048754  ldrb r0,[r0,#0x0]       ; selected coefficient directly from ROM
08048756  mul r0,r2              ; r2 = signed scratch halfword
08048758  mov r1,#0x64
0804875a  bl 0x080f7b08
0804875e  strh r0,[r4,#0x0]       ; r4 = 03000BF8
```

This is **Confirmed static recomputation** from original record/battle inputs. There is no read of `0x03003F9D` or the menu's `0x02014D02` in this scoped function. Therefore a read watchpoint on work +0x69 need not detect this arithmetic. The menu Attack 26 is not demonstrably copied into this scratch; the source of u and coefficient-index adjustments still needs tracing.

The remaining operations strengthen a **Probable offensive damage** interpretation:

- `0x0804876C..96`: sum target halfwords +0x18 and +0x14, apply 1/999 bounds under signed-halfword handling, subtract the bounded value from scratch. Defence meaning is Candidate; subtraction and scratch write are Confirmed runtime for the Gear-Yo replay.
- `0x08048798..EA`: if original record +0x27 bit 7 is set, global byte `0x03000BAF` value 2 selects 80% scaling, value 3 selects 70%; other values bypass it. Flag/global meanings are Unconfirmed.
- `0x080487EC..F8`: nonpositive signed scratch becomes 1.
- `0x08048802..10`: target halfword +0x0A bit `0x4000` makes scratch zero. Its gameplay meaning is Unconfirmed.

For ordinary nonoverflowing values, the core is original base plus battle additive byte, optional selected percentage, subtraction of a bounded target quantity, optional 80/70% branch, lower bound 1, and conditional suppression to zero. Actual signed casts/16-bit stores matter; this is not a complete universal damage formula. There is no identified PRNG call in this routine. Randomness in earlier inputs or untraced paths is neither established nor excluded.

## Caller, display transfer and probable HP subtraction

A raw Thumb BL scan finds one direct call to `0x080485B0`: **`0x08046DE6`**, independently decoded in Thumb routine **`0x08046D60`**. That caller iterates target indices 0..2 with selection/flag checks. Its r7 holds `0x03000BF8`, r8 holds target base `0x03000A40`.

Immediately after return it loads scratch and passes target index/result to `0x0804B2F0`. Bounded disassembly of that callee shows decimal division, digit graphics and display/sound setup, supporting a **Probable damage-number display** role. Caller then reloads scratch and applies it to target halfword +0x0E:

```text
08046de4  add r0,r5,#0x0
08046de6  bl 0x080485b0
08046dea  ldrh r1,[r7,#0x0]       ; calculated scratch, before display
08046dec  add r0,r5,#0x0          ; target index
08046dee  bl 0x0804b2f0
08046df2  sub r0,r6,r5           ; r6 = 8*target index
08046df4  lsl r0,r0,#0x3         ; 56*target index
08046df6  mov r1,r8
08046df8  add r4,r0,r1           ; target pointer
08046dfa  ldrh r1,[r4,#0xe]      ; old target quantity
08046dfc  ldrh r0,[r7,#0x0]      ; scratch reloaded after display
08046dfe  sub r1,r1,r0
08046e00  mov r0,#0x0
08046e02  strh r1,[r4,#0xe]      ; concrete candidate HP-modification instruction
08046e04  lsl r1,r1,#0x10
08046e06  cmp r1,#0x0
08046e08  bge 0x08046e0c
08046e0a  strh r0,[r4,#0xe]      ; conditional zero clamp
08046e0c  add r0,r5,#0x0
```

Subsequent code reads this field as signed, branches on zero and conditionally calls `0x08048E40`. That callee was not analyzed here. The target quantity's **current HP** interpretation is now Confirmed (runtime) for target `0x03000A40`, by the captured 24?8 store above. For target 0 the candidate address is `0x03000A4E`; target 1/2 addresses differ by 0x38. The checkpoint contains 24 at target-0 +0x0E and another 24 at +0x10, but equality alone does not prove current/max HP semantics.

Three concrete prioritized stops:

| Stop | Purpose / confidence |
| --- | --- |
| `break 0x080485B0` | Enter recomputation, capture target index and battle inputs; confirmed static entry |
| `break 0x08046DEA` | Read completed scratch at `0x03000BF8` before it is passed to display; confirmed static handoff |
| `break 0x08046E02` | Inspect pending target halfword write, r4 pointer and r1 proposed value; confirmed static subtraction/store; Gear-Yo HP write Confirmed runtime |

Use these sequentially, not a global divide breakpoint or a large set of overlapping watchpoints. Optional `watch/w 0x03000BF8` is supported by concrete stores above but can be noisy; optional target write-watch should be armed only after the live r4 identifies the actual target. `0x0804875E` is a focused intermediate coefficient-scaled-store stop if input arithmetic later needs resolution; it is conditional on the scaling path.

## Translation checks and unresolved work

Zero differing bytes between supplied ROMs in `[0x080485B0,0x08048820)`, `[0x08046D60,0x08046E5C)`, `[0x080484CC,0x080484FC)`, and `[0x0802BA08,0x0802BA50)`. Ranges include relevant code/pool bytes. This is local compatibility evidence, not full translation certification. Protected ROM hash/size/mtime checks passed; no checkpoint was changed.

Unknowns: target enemy identity; meaning/source of battle Q fields and selector adjustment; flags at C65/BAF/target +0x0A; how performance results enter these fields; and any earlier copying or alias-based coefficient consumption. No confirmed transfer of the UI Attack output to battle damage, no intermediate battle arithmetic capture exists yet; final damage and HP delta are now runtime-confirmed. The new breakpoints target these concrete gaps; the intermediate subtraction operands remain the next measurement.

## Revalidation after live damage report

The established bounded workflow completed again in `reverse_engineering/ghidra/run-3857293b23c243d08c26cc8e0feca509/loader.txt` (`TRACE_COMPLETE`). Original/English comparisons still report zero differing bytes in the four scoped ranges; protected ROM checks passed. No unrestricted analysis was enabled.
