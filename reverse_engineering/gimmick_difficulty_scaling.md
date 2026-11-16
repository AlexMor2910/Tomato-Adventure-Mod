# Gimmick difficulty scaling: bounded static audit

Date: 2026-10-20. Phase 1 documentation only. No emulator, debugger, Ghidra launch, ROM construction, patch, save access, or gameplay change was performed. Existing disassembly was reused. New ROM reads were restricted to the listed routine windows and the 50-record table. The converter itself does not open ROMs.

## Findings and limits

All 50 records use **unsigned byte percentages**, not unsigned/signed 16-bit percentages, in the shared menu calculation. Each apparent little-endian word at `+0x28+2*j` contains a percentage byte followed by an independent auxiliary byte. The loader decodes the latter according to record `+0x27 & 15`. Thus the 14 large-word records are not anomalously huge Attack multipliers. Their auxiliary bytes have a proven decoder but unresolved gameplay meanings.

Ordinary menu adjustment supports **seven settings, 1–7**, assuming an initially valid setting. Calculation code supports nine slots. Battle code can add two to its zero-based selector. Consequently slots 8–9 are explicitly implemented calculation cases; **unreachability is not proven**. All 50 records repeat the entire seventh pair in slots eight and nine. Saturation of a two-step battle adjustment is a plausible reason for duplication, not a proven designer intent or a proven gameplay path.

The complete CSV contains verified percentages and conditional menu Attack calculations for all 50 records, including slots 8–9. Unknown auxiliary meanings and universal battle damage remain empty. “Verified” in the filename applies to populated static fields, not to complete gameplay semantics or runtime coverage.

## Inputs, provenance and address convention

Read `AGENTS.md` and `tomato_adventure_modding_plan.md`; reused these sources:

- [gimmicks.md](gimmicks.md), [ghidra_loader_trace.md](ghidra_loader_trace.md), [gimmick_calculations.md](gimmick_calculations.md), [battle_damage_candidates.md](battle_damage_candidates.md), and [gimmick_runtime_tests.md](gimmick_runtime_tests.md). Earlier candidate descriptions are superseded only where actual instruction evidence permits.
- Existing traces `ghidra/run-cffeb54fcbc540a78ce312e1604a9711/loader.txt` (loader), `ghidra/run-50ecc6655f7542ed8a8d9f69e3b2d68a/loader.txt` (menu), and `ghidra/run-3937c795ad674666ab7b2c4938e09b04/loader.txt` (battle); their source scripts are `tools/analyze/ghidra/TraceGimmickLoader.java`, `TraceGimmickCalculations.java`, and `TraceGimmickBattle.java`. No new run was made.
- `tools/extract/extract_game_data.py`, `make_gimmicks_csv.py`, `make_gimmicks_csv_v2.py`, `extract_gimmick_names.py`, and the existing raw/named CSVs in `tools/extract/extracted_data/`. The old numeric-pattern classifier is not reused as semantic evidence.
- `tomatotrans-1.1.1/asm/gimmick_text.asm`, and the English names under `RESTRUCT 62C250 08 58 7F001E 10 40 32` in `ta_menus_eng.txt`. Names are joined from the existing complete named CSV and independently checked against this source table.

ROM bus addresses below subtract `0x08000000` to obtain file offsets. RAM addresses have no ROM file offsets. Original records: file `[0x0062C250,0x0062D380)`, bus `[0x0862C250,0x0862D380)`, stride `0x58`, IDs 1–50. `R = 0x0862C250 + (ID-1)*0x58`. English names are separately relocated to `0x087F001E`, stride `0x40`; scaling data are not taken from that text table.

The JSON records bounded-range SHA-256 comparisons. Both ROMs match every record's `+0x22..+0x39` and all five checked unsigned-byte-load opcodes. Loader continuation, battle selector/calculation/application, difficulty writer, upgrade writer, and division windows match. The wider menu window `[0x08075970,0x08075B00)` has three differences at `0x08075AFC/FE/FF`, beyond the calculation and its final literal at `0x08075AF8`; do not claim that whole window is identical. The table's only three differing bytes are at `0x0862CC8C..8E`, the previously documented Choo-Choo graphics pointer, outside coefficient fields. These local comparisons do not authenticate full ROM hashes anew or certify the entire translation.

## Instruction evidence and formulas

Evidence IDs below resolve to structured claims in [gimmick_difficulty_scaling_evidence.json](gimmick_difficulty_scaling_evidence.json). All routines lack project-owned symbolic names; their entries and trace blocks serve as symbols. Confidence “Confirmed static” establishes instructions/data flow; it does not assert live execution for every ID.

### M1: menu calculation, all 50 IDs

`0x08075970..0x08075AEC`, file `0x00075970..0x00075AEC`, writes a result structure P. `0x0807565C..0x080756A8` finds a matching ID in three-byte party/storage entries S. `S[1]` is the one-based selector and `S[2]` the additive upgrade byte. At `0x08075990` it loads S[2]; `0x080759AE` loads S[1]; `0x080759B6..BA` loads R[0x22], adds S[2], and stores P+8. There is no record-type branch around this addition or percentage calculation.

`0x080759BE..CE` subtracts 1 from the selector, checks unsigned `<=8`, and dispatches nine cases. Entries `0x08075A04 + 0x14*j` select `R+0x28+2*j` for j=0..8. The shared instructions are:

```text
08075AB0  ldrb r5,[r0]       ; unsigned selected percentage, ONE byte
08075AB2  ldrh r0,[r7,#8]   ; base plus upgrade
08075AB4  mul r0,r5
08075AB6  mov r1,#100
08075AB8  bl 080F7B08       ; signed division, truncation toward zero
08075ABC  strh r0,[r7,#10]
```

For valid IDs, successful S lookup and d in 1..9:

```text
p = read8(R + 0x28 + 2*(d-1))
unscaled = read8(R+0x22) + read8(S+2)
menu_Attack = floor(unscaled * p / 100)
```

Operands are nonnegative bytes. Maximum possible numerator is `510*255=130050`; quotient <=1300, so the halfword stores cannot overflow for this formula. There is no explicit menu minimum of 1, maximum clamp, random draw, target mitigation, or type-specific arithmetic. Invalid selectors bypass the coefficient load into preserved r5; this is **not** a clamp/default. Missing ID lookup and invalid IDs are outside the formula's supported domain.

Callers reload P+8/P+10 and send them to decimal rendering. `0x08076E28` and `0x0807892C` render Attack rows; English label descriptors are mapped in `gimmick_calculations.md`. `0x08075ABC` stores a calculated menu value, not HP damage, and the routine does not return Attack in r0.

### L1: auxiliary-byte decoding

Loader entry `0x08065518`, retained continuation `0x0806556C..0x080656B6`; see the full instruction appendix in `ghidra_loader_trace.md`. With W=`0x03003F34`, a copied record:

```text
pair_offset = (2*(loader_selector-1)) & 255
080655A4  ldrb r1,[r3]      ; pair's first byte
080655AE  strb r1,[...+69]  ; percentage copy to W+0x69
080655B2/B6 cmp type,1/2
080655BA  ldrb r1,[r3,#1]   ; second byte, type 1/2 branch
080655BE  and r0,r1         ; low nibble -> W+0x72
080655C8..D0               ; (aux>>4 + aux<<4) & 15 -> high nibble
080655E4  ldrb r1,[r3,#1]   ; other types
080655E8  and r0,r1         ; aux & 127 -> W+0x72
080655F0  mov r1,#0         ; other types -> W+0x71=0
080655F8  strb r1,[...+71]
```

Precisely, if `type = R[0x27]&15` is 1 or 2, `W[0x72]=aux&15`, `W[0x71]=aux>>4`; otherwise `W[0x72]=aux&127`, `W[0x71]=0`. The high bit is discarded in the latter branch. This is byte packing, not a signed coefficient or one 16-bit percentage. No transformations of the percentage itself occur beyond unsigned byte loading and copying.

The English loader prefix uses an unaligned `ldr` of W+0x27 at `0x08065564`, versus Japanese `ldrb` at `0x0806556A`. Its retained continuation is identical. On the documented ARM7TDMI rotated-word-load interpretation, the accessed byte occupies r1's low byte, so the low-nibble/bit4–5 operations should agree; hardware behavior was not newly tested. Classifications here use the original ROM's proven type decoder. Menu/battle direct ROM byte calculations do not depend on this loader-prefix difference.

The separate display reader `0x0802BA2C..0x0802BA44`, documented in `battle_damage_candidates.md`, calculates `(W[0x22]+W[0x6A])*W[0x69]/100`. It supports the percentage role of the copied byte without establishing an HP consumer of that copy. Meanings and downstream consumers of W+0x71/+0x72 remain unresolved.

### D1: difficulty range and extra slots

Writer `0x08079AE4..0x08079B62` changes S[1]. At `0x08079B0C..14`, increment is permitted only when current byte <=6. At `0x08079B2A..32`, decrement is permitted only when >1. Starting in 1..7, ordinary L/R adjustment stays in 1..7; help text at descriptors `0x084904C0/C8` and the seven-marker renderer `0x08079B78..0x08079BFA` corroborate that UI range. This is conditional adjustment, not normalization of corrupt state: initial 0 or 8/9 is not forcibly clamped.

M1 accepts selectors 1..9; the loader has no 1..9 bound and truncates its offset to a byte. Battle helper `0x080484CC..0x080484F6` returns `k=(Q[0x21]+(2 if Q[0x23]!=0 else 0))&255`. Battle calculation accepts k=0..8, otherwise bypassing percentage multiplication. If Q[0x21] were d-1, setting 6 with the flag selects slot 8 and setting 7 selects slot 9. **That antecedent and the ordinary flag-setting path are not proven by the available trace.** Upgrades change an additive byte, not this selector in the known upgrade writer. No event-based selector path is established here.

All 50 full raw pairs satisfy slot7=slot8=slot9. Duplication could flatten the +2 battle adjustment above playable level 7 (**Probable rationale**); it is not evidence of unreachable padding. Precise missing evidence: bounded writers feeding Q+0x21/+0x23 and the gate `0x03000C65`, plus their connection to persistent S[1]. Existing traces stop at these inputs. This audit makes no exhaustive claim about indirect/event writers and stops here.

### U1: upgrades

Writer `0x08081188..0x080811C8` finds S, loads cap R[0x23] at `0x080811AA`, adds the unsigned increment to S[2], **stores a byte first** at `0x080811B0`, then compares its low byte to the cap at `0x080811B6..BA`:

```text
S[2] = min((S[2] + (increment & 255)) & 255, R[0x23])
```

The item call at `0x08080D8C` passes item-record byte +9 to this writer. Existing source manifests identify Cell/Volt/Star amounts 1/3/5 and Attack improvement. Menu upgrades enter **before** percentage scaling. There is no proven upgrade-dependent percentage/index adjustment in M1/U1. The formula permits byte wrap before capping; it must not be replaced by mathematical saturating addition. Ordinary cap meaning is supported by the Battery display, but battle Q+0x22 has not been proven copied from S[2].

### B1: conditional battle formula, not universal damage

Routine `0x080485B0..0x0804881C` recomputes from original ROM, rather than reading menu P. For actor a=`read8(0x03000BB6)` and slot s=`read8(0x03000C30+a)`, Q=`0x03000938+a*0x84+s*4`; R uses zero-based record index Q[0x20]. T=`0x03000A40+target*0x38`. Helper `0x080484CC` supplies k as above. Scratch H is halfword `0x03000BF8`.

```text
H = R[0x22] + Q[0x22]                          # 08048602..06
if read8(0x03000C65)==1 and k<=8:
    H = trunc(H * read8(R+0x28+2*k) / 100)     # 08048754 ldrb; 56 mul; 5A divide; 5E strh
V = clamp(signed16(T.u16[0x18]+T.u16[0x14]),1,999)
H = (H-V) & 65535                             # 08048794..96
if R[0x27]&128:
    if read8(0x03000BAF)==2: H = trunc(signed16(H)*80/100) & 65535
    if read8(0x03000BAF)==3: H = trunc(signed16(H)*70/100) & 65535
if signed16(H)<=0: H=1                        # 080487EC..F8
if T.u16[0x0A]&0x4000: H=0                    # 08048802..10
```

`signed16` first retains the low 16 bits; `trunc` is toward zero, including negative intermediate results. Initial B<=510 and scaled A<=1300. Post-subtraction scratch is stored as 16 bits and read as signed for percentage/minimum branches. This formula preserves that distinction. V is a **target subtraction quantity**, not a proven Defense stat. No random input is identified inside this routine; earlier generation is untraced.

At caller `0x08046D60`, call `0x08046DE6` computes H, `0x08046DEE` sends it to a display routine, and `0x08046DFA..0x08046E0A` reloads it, subtracts from target HP +0x0E, stores, and clamps negative signed HP to zero. GY1 is the previously user-observed Gear-Yo case: displayed/pre-subtraction Attack 26, target quantity 10, scratch 16, HP 24→8. It is the only runtime confirmation claimed here.

The routine's percentage path has no per-ID/type arithmetic exception; its presence does not prove all 50 Gimmicks execute this damage routine or use identical effective damage. Only the shared menu stat formula is assigned unconditionally across valid records. `+0x27` bit7 gates post-subtraction scaling for IDs 4,11,12,20,21,24,30,46,47,48,50; global/flag gameplay names remain unresolved. Auxiliary-byte special effects could affect other paths. No universal damage or performance/RNG formula is exported.

## Complete-set classification and CSV specification

The JSON `records` contains all IDs, names, raw values, decoded bytes and per-record table addresses; the CSV is [gimmicks_scaling_verified.csv](../tools/extract/extracted_data/gimmicks_scaling_verified.csv). Grouping follows actual decoder branches, not numeric magnitude:

| Original type nibble | IDs | Auxiliary decoder |
| --- | --- | --- |
| 0 | 1–8,11,13,14,16–18,21–27,29,30,34–41,46–50 | low7; all auxiliary bytes zero in these 36 records |
| 1 | 19 Fumigator,20 Bee Gatling,31 Puffer | low/high nibbles |
| 2 | 43 Pop Horn,44 Fart Horn | low/high nibbles |
| 3 | 9 Cupid Bow,10 Judgment | low7 |
| 4 | 12 SlotZooka,42 Lucky Cat | low7 |
| 5 | 15 Mag-Mitt,33 Spider Gun | low7 |
| 6 | 28 Pyramet,45 Love Song | low7 |
| 8 | 32 UFO-Cast | low7 |

These 14 nonzero-auxiliary records are exactly the previously large-word group. For example Cupid Bow's first word 17520=`0x4470` means 112% and auxiliary `0x44`→W+0x72=68, W+0x71=0. Fumigator's 30836=`0x7874` means 116%, W+0x72=8, W+0x71=7. The auxiliary quantity names are not inferred from these numbers.

CSV schema (UTF-8, decimal values except explicit address fields; blank means not established):

| Columns | Meaning / evidence |
| --- | --- |
| `gimmick_id`, `english_name`, `name_source` | Original runtime ID, existing English manifest name and provenance; T1/Rnn |
| `rom_file_offset`, `rom_bus_address`, `base_attack` | Original record location and byte +0x22; T1/Rnn |
| `upgrade_cap`, `record_type`, `post_subtraction_gate_bit7` | Raw byte +0x23, +0x27 low nibble and high bit; U1/L1/B1 |
| `difficulty_1` through `difficulty_7` fields | One-based menu selector slots; D1 |
| `slot_8`, `slot_9` fields | Implemented extra array slots, ordinary gameplay reachability unresolved |
| Each prefix's `_raw_u16`, `_percent`, `_aux_raw` | Little-endian raw pair, low byte, high byte; T1/M1/L1 |
| Each prefix's `_loader_work72`, `_loader_work71` | Original-loader byte transformations, with no asserted gameplay units; L1 |
| Each prefix's `_menu_attack_upgrade0` | Conditional M1 output for that slot at upgrade **zero**; 8/9 values are hypothetical menu inputs, not claimed accessible |
| `auxiliary_decode`, `auxiliary_gameplay_meaning` | Decoder class; meaning left empty |
| `slots_8_9_reachability` | Unresolved; repeated data does not prove padding |
| `formula_class` | M1 shared by all IDs; B1 only if that battle path is used |
| `upgrade_interaction` | Symbolic M1/U1 formula; battle additive source unresolved |
| `battle_damage` | Empty for all rows; no assumed universal damage |
| `confidence`, `runtime_confirmation`, `evidence_refs` | Populated facts Confirmed static; GY1 limited runtime observation separately labeled; claim IDs |

JSON claim confidence uses exactly `Confirmed static`, `Confirmed runtime`, `Probable`, `Candidate`, or `Unresolved`. These refine repository Confirmed/Probable/Candidate/Unconfirmed labels. Overall row confidence covers populated static values, not empty or explicitly unresolved interpretations.

## Reproduction and validation

From the workspace root, use a **fresh output path**:

```powershell
python tools/extract/convert_gimmick_scaling.py --self-test
python tools/extract/convert_gimmick_scaling.py --input tools/extract/extracted_data/gimmicks_raw.csv --names tools/extract/extracted_data/gimmicks_named_complete.csv --output <fresh-output.csv>
```

The standalone standard-library converter requires all three paths, enforces 50 ordered unique IDs, indexes, record lengths, file/bus offsets, every redundant raw byte/halfword, matching named/raw base and nine fields, and nonempty sourced names. Output uses exclusive creation, including when output aliases an input; no overwrite flag exists. It reuses existing extraction and name resources rather than rebuilding either. It exports raw facts separately from calculated menu predictions and unknown gameplay interpretations.

Three synthetic tests pass, covering nibble/low7 decoding with nonzero upper bytes and masked high bits, truncation, upgrade-before-scaling, maximum byte arithmetic, byte wrap before cap, invalid inputs/IDs/offsets/lengths/redundant bytes/words, 50-row conversion, and refused overwrite with unchanged bytes. The real conversion produced 50 rows. Independent checks matched the source English name table, raw input fields against both ROMs, and decoded unsigned byte opcodes; no emulator result was manufactured. Synthetic calculations do not create runtime evidence.

## Unresolved questions and stopping boundary

1. Which ordinary paths set battle Q+0x21/+0x23 and C65, and do they map S[1] to d-1? This is required to prove slots 8/9 are reachable through normal actions, rather than only present in dispatch. No exhaustive event/exception reachability proof exists.
2. What consume W+0x71/+0x72 and what units do their type-dependent quantities represent? The original-loader transforms are proven; their gameplay meanings are deliberately empty.
3. Which battle setup writes Q+0x22 from persistent upgrades, and which Gimmicks actually dispatch through B1? These missing links prevent universal effective-damage or upgrade-in-battle claims.
4. Why were complete pairs duplicated? They are compatible with saturating a +2 index adjustment; intent remains unconfirmed. The English loader's unaligned flag load also retains the historical hardware-verification caveat.

The bounded audit ends at those specific missing input/consumer links. No enemy-definition, map, Binky, Hawker, progression, graphics, or balance investigation was started.
