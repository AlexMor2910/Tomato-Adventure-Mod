# Enemy HP encoding: initializer versus scripted defeat thresholds

2026-10-20. Bounded read-only static investigation. No ROM changes, builds, patches, emulator/debugger/Ghidra launches, saves, savestates, or Git commits. Existing enemy CSVs and extractor remain unchanged.

## Result

**There is no subtraction of 3000 in the common enemy HP initializer.** It reads the unsigned 16-bit record field at `+0x0A`, masks off bit 15, and copies the result to both current and maximum HP. Thus Brikky `0C` really starts with **3030 in the battle HP variable**, not 30.

The smaller practical HP values come from **enemy control scripts that test current HP against 3000 and then trigger scripted removal/defeat behavior**, often by explicitly writing zero HP. Brikky `0C` tests `HP <= 3000` and takes a path writing its own HP to zero: its local damage budget to that threshold is **30**. This is a script threshold convention, not a universal numeric decoder. Normal damage subtraction does not preserve a 3000 floor.

The six supplied examples have supporting local paths: Brikky `0C` **30**, Grikky `0D` **25**, Brikky `1D` **130**, Grikky `1E` **110**, Oops `1A` **220**, Cap'n Garco `2A` **160**. These are local threshold damage budgets, conditional on the relevant script path and unchanged HP. They are not necessarily independently required damage for every actor in a paired encounter.

Values 3600–4500 are not one separate encoding class: some use the same threshold convention, some have multiple thresholds, some are controlled by another actor's script. The 20000-HP arms initialize to **20000**; **17000 effective HP is not established**. Exact-3000 records must not be decoded to zero by a blanket subtraction.

## Sources and bounded method

Read repository instructions and the modding plan; reused:

- [gimmick_palace_enemy_research.md](gimmick_palace_enemy_research.md) and its [evidence JSON](gimmick_palace_enemy_evidence.json): original enemy table, initializer seed, target layout and common HP relationship. Its old HP values describe the masked stored field, not a verified defeat budget for every boss.
- [battle_damage_candidates.md](battle_damage_candidates.md): the known HP subtraction path. No new runtime confirmation is claimed.
- `tools/extract/extract_enemies.py`, existing `enemies.csv` and `enemies_raw.csv`, `tomatotrans-1.1.1/ta_enemies_eng.txt` NAMES, `inserter/text.cpp`'s previously documented `EnemyInfoAddress`, and `asm/battle_enemies.asm` context.
- Existing `tools/analyze/thumb_inspect.py: decode` for bounded ARMv4T Thumb decoding. No new disassembler dependency or analysis program was launched. Its output was inspected with literal pools and switch tables excluded from the retained instruction evidence.

The enemy table begins at original Japanese file `0x00634F50`, bus `0x08634F50`, stride `0x4C`, count **182**, zero-based IDs `00..B5`. Its exclusive end is `0x00638558`. English names come from the existing CSV, checked against NAMES; they are not decoded from Japanese embedded name bytes. Only HP and directly required script pointers were interpreted.

Candidate searches were limited to native battle file range `[0x00040000,0x00053000)`: aligned constants and instruction candidates chose follow-up windows. This was not whole-ROM analysis, and a raw constant match was not accepted as control-flow evidence. Direct dependencies outside that range were only the known table fields and pointed enemy HP/action scripts. High-HP record `+0x14` prefixes were limited to 80 bytes, `+0x18` context to 64 bytes; selected branch/zero paths were read in explicitly bounded windows. Prefix inventory stops at return, an unexpanded opcode, an unconditional branch, or the bound. It does not drift into the next enemy's script after a return.

All addresses below are ROM bus addresses; subtract `0x08000000` for file offsets. RAM addresses have no ROM file offset. All functions lack recovered project-owned symbols; numeric entries/blocks and helper `decode` are the source references. Full instruction bytes, excluded data ranges, branch-target script bytes, source hashes, per-record values and confidence labels are in [enemy_hp_encoding_evidence.json](enemy_hp_encoding_evidence.json).

## INIT: HP initialization

The bounded initializer block establishes:

```text
08048272  ldr r0,[080482A8]   ; 03000A40
08048274  mov r8,r0
08048276  ldr r1,[080482BC]   ; 00007FFF
08048278  mov r10,r1
...
08048288  ldr r1,[080482B0]   ; 030008EC, enemy-record pointer array
0804828C  ldr r0,[r3]
0804828E  cmp r0,#0
08048290  bne 080482C4       ; non-null slot
...
080482C4..CA                 ; target = 03000A40 + slot*38h
080482CC  ldrh r2,[r0,#0A]
080482CE  mov r0,r10
080482D0  and r0,r2
080482D2  strh r0,[r1,#0E]   ; current HP
080482D4  ldr r0,[r3]
080482D6  ldrh r2,[r0,#0A]
080482D8  mov r0,r10
080482DA  and r0,r2
080482DC  strh r0,[r1,#10]   ; maximum/reset HP
```

For a non-null enemy record R:

```text
raw_hp = read_u16le(R + 0x0A)
initial_current_hp = initial_max_hp = raw_hp & 0x7FFF
```

**Confirmed static.** No `-3000`, division, phase decoder, or HP-dependent type branch occurs between these reads and stores. None of the 182 extracted HP fields sets bit 15; the mask is implemented, but that bit's separate meaning is not established here. It must not be named a boss flag from this evidence.

Opcode `27` handler `0x08041C9C..0x08041D02` is a separate reset path: `0x08041CEA` loads target max HP `+0x10`, and `0x08041CEC` restores current HP `+0x0E` from it. It does not subtract 3000 either. Full reset/phase behavior of every actor was not traced.

## DAMAGE and END: stored HP and battle completion

The documented damage application caller retains ordinary numeric HP:

```text
08046DFA  ldrh r1,[r4,#0E]   ; current HP
08046DFC  ldrh r0,[r7]       ; computed damage scratch
08046DFE  sub r1,r1,r0
08046E02  strh r1,[r4,#0E]
08046E04  lsl r1,r1,#16
08046E06  cmp r1,#0
08046E08  bge 08046E0C
08046E0A  strh r0,[r4,#0E]   ; r0 was set to zero at 08046E00
```

This stores the low 16 bits of the difference and clamps a negative signed-halfword result to zero. For the ordinary nonoverflowing domain it is `max(current_hp - damage, 0)`. It does not subtract an encoding offset or clamp to 3000. This is one verified HP application path, not an assertion about all damage sources.

At `0x0804CE8C..0x0804CEC6`, each eligible target slot loads record `+0x14` (`0x0804CEB0`) and invokes script interpreter `0x08040860` (`0x0804CEB4`). Target flags `0x300` gate eligibility. Script completion/continuation is handled before subsequent zero-HP processing; a yielding script may delay the later steps.

Removal routine `0x0804CFE8..0x0804D154` skips flagged slots, checks **current HP == 0** at `0x0804D034..38`, sets the removal flag at `0x0804D068..6A`, and decrements remaining-enemy byte `0x03000BAF` at `0x0804D082..88`. It does not universally remove `HP <= 3000` actors. Once count is zero, `0x0804D09C..0x0804D142` has formation-specific end handling; that branch selection is preserved in the evidence rather than expanded into encounter research. The caller also checks zero count at `0x0804CF0E..14`, writes result byte `0x03001973=1`, and selects state 6 via `0x08048584` at `0x0804CF24..28`. These establish the counted battle-end chain; a particular boss cutscene or scripted victory condition is not inferred just from HP.

## VM and SCRIPT: decoding the actual HP conditions

Interpreter dispatch at `0x08040932..4A` fetches a byte opcode and indexes the real 256-word dispatch table at `0x0804096C`. Selected table values and decoded call stubs establish these handlers:

| Opcode | Handler | Proven operation |
| --- | --- | --- |
| `20 selector` | `0x08041808` | Load signed current HP from `03000A40 + slot*38h + 0E` into 32-bit accumulator `0x03000758`. |
| `04 u16 target` | `0x08041214` | Branch if accumulator equals immediate. |
| `07 u16 target` | `0x0804131C` | Branch if accumulator <= immediate, using unsigned comparison. |
| `08 u16 target` | `0x08041374` | Branch if accumulator > immediate, using unsigned comparison. |
| `0A u16 target` | `0x08041424` | Branch if accumulator AND mask is nonzero; does not change accumulator. |
| `21 selector u16` | `0x0804184C` | Store immediate into current HP at `0x08041880`; a zero write also conditionally changes a target bookkeeping bit, with a formation exception. |
| `23 selector` | `0x08041910` | Load target flags `+0x0A` into accumulator. |
| `27 selector` | `0x08041C9C` | Reset current HP from max HP, alongside state reset. |

Helper `0x08041114` resolves selectors: 0,1,2 are literal slots; selector 3 means the current script's slot/context (`0x08041134`). Hence `20 03` followed by a comparison is a self-HP test, not enemy ID 3. Negative HP is sign-extended by opcode 20 and subsequently compared unsigned; the reviewed post-damage path normally prevents negative HP. No broader signed-domain simplification is assumed.

The comparison immediate `b8 0b` is **3000**. For example, Brikky `0C` record control pointer is `0x080D3C9C`:

```text
080D3C9C  20 03                      accumulator = own current HP
080D3C9E  04 00 00 BE 3C 0D 08       if HP == 0: return path
080D3CA5  07 B8 0B AD 3C 0D 08       if HP <= 3000: branch 080D3CAD
080D3CAC  FF                         return otherwise
080D3CAD  43 ...                     intervening message command
...       45 3C; 44                  wait/control commands
080D3CB5  21 03 00 00                own HP = 0
```

Command lengths across these intervening commands were checked through their dispatch/argument-cursor handlers; their rendering/audio callees were not followed. `+0x18` is separately dispatched as an action script by `0x0805040C..26`; it is not another HP field.

Cap'n Garco `2A` uses the equivalent inverse condition: at `0x080D10B0`, `20 03` reads own HP; `04 0000` skips an already-zero actor; `08 3000` returns while HP is **above** 3000. Otherwise the fallthrough contains `21 03 0000`. Thus `3160 - 3000 = 160` is supported for that local transition.

## Brikky and Grikky: every named variant

All ten variants have an actual 3000 comparison in their own `+0x14` prefix. Locations below are the **comparison opcode**, not just a raw occurrence of `B8 0B`.

| ID | Name | Raw/initialized HP | HP comparison | Effective HP exported | Qualification |
| --- | --- | ---: | --- | ---: | --- |
| `0C` | Brikky | 3030 | `0x080D3CA5` | 30 | Self threshold → self zero. |
| `0D` | Grikky | 3025 | `0x080D3CCD` | 25 | Self threshold → self zero. |
| `1D` | Brikky | 3130 | `0x080D228F` | 130 | Own slot 0 threshold → zero; partner checks can clear both. |
| `1E` | Grikky | 3110 | `0x080D232B` | 110 | Own slot 1 threshold → zero; paired handling. |
| `49` | Brikky | 3200 | `0x080D3148` | 200 | First also checks partner slot 1 at `0x080D313F`; can be cleared through pairing. |
| `4A` | Grikky | 3250 | `0x080D31C3` | 250 | Threshold handler clears both slots. |
| `73` | Brikky | 3400 | `0x080D334B` | 400 | Partner check and separate single/pair zero paths. |
| `74` | Grikky | 3250 | `0x080D33C3` | 250 | Partner check and separate single/pair zero paths. |
| `AE` | Brikky | 3700 | `0x080D39AB` | blank | Threshold margin 700; additional 3200 comparison and conditional handler. |
| `AF` | Grikky | 3650 | `0x080D3B3F` | blank | Threshold margin 650; additional 3200 comparison and conditional handler. |

For AE/AF, the common 3000 convention is **Confirmed static**, but a single independently depletable defeat HP is not established. Their handlers at `0x080D39BA`/`0x080D3B4E` branch on additional state and contain further operations before possible HP zero writes. The 3200 checks at `0x080D39B2`/`0x080D3B46` establish intermediate HP-dependent behavior; its complete phase/state meaning is unresolved. They must not silently inherit the simpler first-pair formula.

## Large values and exceptions

| Record(s) | Stored HP | Supported interpretation / remaining limit |
| --- | ---: | --- |
| Selemo `00/01`, Invisidude `54` | 3000 | Remains 3000 on initialization. Special script prefixes/return do not establish effective zero; exported effective HP blank. |
| Death Lilby `5F` | 3600 | Prefix compares <=3000, <=3200 and <=3450 at `0x080D294F/56/5D`. This proves multiple HP-dependent branches, not a separate 3600 encoding. Threshold margin 600 is retained separately; effective HP blank pending control-path/phase proof. |
| Left/Right Arm `76/77` | 20000 | Initialize to 20000. Own control prefixes at `0x080D2DBC`/`0x080D2E4C` enter conditional state logic, not a proven 3000 depletion rule. Core Coupling `75` tests slot 0 <=3000 at `0x080D2ACB`; target `0x080D2C8F` includes zero writes to slots 0,1,2. Arm removal can therefore be externally driven. No 17000 or invulnerability claim. |
| Chekkit `8C` | 3700 | Own-slot <=3000 at `0x080D3E5D`; branch target `0x080D3F54` has additional state-dependent control. Margin 700, effective blank. |
| Left/Right Arm `8D/8E` | 3600 | Actual <=3000 checks at `0x080D4038`/`0x080D434A`, targeting `0x080D4274`/`0x080D45AA`. Complex branch handlers; effective blank. They are distinct records from the 20000 arms. |
| Gimmick Robo `A9` | 3700 | <=3000 at `0x080D34E6` → `0x080D34FB` writes slot 0 HP zero. Local effective budget 700. |
| Gimmick Robo `AA` | 4500 | <=3000 at `0x080D3CEE` → `0x080D3CFA` clears both slots. Local budget 1500, with paired-clearing caveat. |
| Gimmick Robo `AB` | 4500 | Its own prefix at `0x080D3DE8` does not establish an independent HP threshold in this bound. A partner's script can clear slot 1. Do not assign 1500 merely from its name/value. |
| Gimmick Robo `AC` | 4500 | At `0x080D357E`/`0x080D3587`, either slot 0 or slot 1 <=3000 leads to `0x080D358F`, clearing both. Local budget 1500; damage needed for both is not necessarily 3000 total. |
| Gimmick Robo `AD` | 4000 | Prefix at `0x080D3624` begins state-dependent logic; complete HP termination link not established. Effective HP blank. |
| Brikky/Grikky `AE/AF` | 3700/3650 | Same 3000 comparisons, plus 3200 branches; see variant table. |
| Abira/arms `B0/B1/B2` | 3850/3700/3300 | State-dependent prefixes; B2 has a threshold branch but a complete independent defeat interpretation was not proven. Effective values blank. |
| Abiwrath/Binkies `B3/B4/B5` | 4000/3900/3900 | Prefixes test relevant slots <=3000 at `0x080D463E`/`0x080D5154`/`0x080D4E6D`. Branches feed complex control; no unproven 1000/900/900 effective values exported. |

“Externally driven” means another script can write that slot's HP; it does not prove the arm cannot be damaged. The known damage calculation has a target-flag gate that can suppress damage, but this investigation does not establish when these specific arms set it. No invulnerability, boss category, susceptibility, or ATK/DEF interpretation is inferred from large HP alone.

A secondary check independently corroborates the 3000 convention: `0x080489FC..0x08048A06` reads the original record's raw HP; if raw >3000 and current HP <=3000, it skips the subsequent effect branch. Similar checks exist at `0x08048A98..A2`, `0x08048B34..3E`, `0x08048BEC..F6`, and `0x08048CE0..EA`. Only their HP gates were relevant; effect probabilities and susceptibility values are outside scope. This is evidence of a reserved scripted threshold zone, not a global HP conversion or categorical boss flag.

## CSV and confidence contract

[enemy_hp_verified.csv](../tools/extract/extracted_data/enemy_hp_verified.csv) contains **all 182 records**, retaining original unsigned `raw_hp`, its hex representation, high bit, and separately `initialized_hp`. No existing CSV is replaced.

- `effective_hp` is populated for **119** records below 3000 with their confirmed common initialized HP/zero-threshold budget. It does not certify absence of later scripted HP changes.
- For **16** manually reviewed threshold-to-zero paths, `effective_hp = initialized_hp - 3000`, and `effective_hp_kind=local_script_threshold_damage_budget`. This is an actor-local nominal budget, not guaranteed total encounter damage, turns, maximum HP display, or a universal engine decoder.
- **47** effective HP cells remain blank. Their raw and initialized HP are still Confirmed static; row `confidence=Unresolved` refers to the effective defeat/phase interpretation.
- `observed_script_threshold` and `threshold_margin_candidate` retain a proven comparison and its arithmetic margin separately from effective HP. A nonempty candidate margin is explicitly **not** a verified defeat HP.
- Each row includes enemy ID/name, record/HP-field file and bus offsets, HP-control/action script pointers, classification, evidence IDs and limitations. `Ehh` resolves to JSON `records[*].claim_id`; the other IDs resolve to `claims`.

The JSON uses Confirmed static / Unresolved here, refining repository Confirmed / Unconfirmed labels. No new runtime claim is included. Raw HP, initial HP, threshold comparison, local zero path, and final encounter victory are separate facts.

## Validation and stopping boundary

Validated 182 unique ordered IDs, stride/address arithmetic, raw record lengths, redundant HP fields against raw bytes, old masked extraction against raw HP, and names against English NAMES. All HP fields and record +0x14/+0x18 pointers match **both** preserved baseline ROMs. Core HP native windows match between ROMs. Script windows often differ in translation message pointers; all **196 inventoried prefix commands** and the HP zero-store commands in all **16 reviewed paths** separately match both baselines. The message handler is translated, so whole-script/window equality is not claimed. Per-window hashes retain actual differences.

Protected input/source SHA-256 values were checked unchanged, along with baseline ROM sizes/modification timestamps. Outputs were created exclusively. Existing experimental ROMs and saves were neither used nor changed. No extracted sprites or unrelated game assets were created.

The global question is resolved: **masked stored HP plus explicit scripted thresholds**, rather than a universal `raw - 3000` decoder. The remaining bounded uncertainties are per-record effective defeat conditions: additional state at AE/AF, state/phase-controlled high-HP components, exact-3000 special scripts, and resets/externally forced zero writes. Resolving those requires tracing the specific branch conditions and phase writers at the recorded stop addresses; it does not justify an unrestricted ROM investigation. This audit stops at those limits.
