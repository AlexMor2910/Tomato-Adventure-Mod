# Enemy offense, Defense, and susceptibility: bounded static analysis

2026-10-20. **Partially verified database**, with complete record coverage. No ROM,
save, state, patch, emulator, debugger, Ghidra, build, or Git commit was used.
The extraction reads the two fingerprinted baseline ROMs and existing CSVs.
HP results are imported unchanged; no boss HP investigation was repeated.

## Findings

Enemy offense is **action-based on the traced ordinary path**: unsigned action
byte `+0x08`, doubled, is reduced by the party target's current mitigation.
There is no established species-wide ATK scalar. Enemy `+0x0C` feeds turn
selection, and must not be mistaken for ATK. Each species has three initial
action pointers; scripts can replace them. This does not prove that every
action uses the ordinary formula, nor that no other offensive field exists.

Enemy `u16(+0x0E)` is confirmed base Defense for the known Gimmick damage path.
It initializes target `+0x14`; the subtraction also includes mutable `+0x18`.
Scripts can replace `+0x14`, so base Defense alone is not live total Defense.

Enemy `u16(+0x10)` contains **six established two-bit application-susceptibility
codes**, at shifts 0, 2, 4, 6, 8, 10. Codes 0/1/2/3 select 100/60/20/0 percent
of an incoming effect application threshold. These are probability modifiers,
not effect-duration multipliers, elemental resistances, or damage multipliers.
Bits 12..15 and some effect names remain unresolved.

## Sources and address convention

Repository instructions and `tomato_adventure_modding_plan.md` were consulted.
Existing sources reused: `enemy_hp_encoding.md` and its evidence JSON,
`battle_damage_candidates.md`, `gimmick_palace_enemy_research.md` and its JSON,
`gimmick_calculations.md`, `tools/extract/extract_enemies.py`, the three existing
enemy CSVs, translation `ta_enemies_eng.txt`, `inserter/text.cpp:EnemyInfoAddress`,
and `asm/battle_sleep.asm`. The latter concerns **party** sleep state; its bit
labels are not transferred to enemy target flags without evidence.

All ROM bus addresses below equal file offset plus `0x08000000`. Thus
`0x08049722` is file `0x00049722`. RAM has no ROM file offset.
The [evidence JSON](enemy_attack_defense_susceptibility_evidence.json) explicitly
records file and bus addresses, raw instruction bytes, literal values, bounded
code intervals, table destinations, record values, input hashes, and Japanese /
English comparisons. Numeric routine labels are used because no source symbols
have been recovered. Inspector source symbol: `tools/analyze/thumb_inspect.py:inspect`.

| Input | SHA-256 |
| --- | --- |
| Japanese baseline | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |

The enemy table is original Japanese file `0x00634F50`, bus `0x08634F50`,
182 records of `0x4C` bytes, exclusive end `0x00638558`. Named action records
start there: bus `0x08638558`, 256 records of `0x10` bytes, exclusive end
file `0x00639558`. The translation replaces name storage `+0..+7` with pointers
and metadata. This run checks **every enemy's +8..+4B** and every referenced
action's **+8..+F** for equality across baselines. The numeric offsets below
therefore apply to both supplied baselines; relocated English name pointers do
not have the Japanese inline-name interpretation.

Bounded candidate searches stayed in native battle file `[0x40000,0x53000)`;
one focused action-buffer literal search used `[0x44000,0x4A000)`. Searches chose
leads, not proof. Retained instruction windows exclude identified pools and
switch data. Only pointed representative action-script prefixes were read;
they are raw context, not a complete VM disassembly. The existing PRNG entry
was inspected only because susceptibility handlers call it.

## Field layout and initialization

| Record field | Width | Battle destination | Evidence and interpretation |
| --- | --- | --- | --- |
| `+0x0A` | u16le, masked `&0x7FFF` | T+0x0E current / +0x10 max HP | Previously established; HP CSV remains authoritative |
| `+0x0C` | u16le | T+0x12 | `080482DE..E2`; base input used in turn selection, not established ATK |
| `+0x0E` | u16le | T+0x14 | `080482E4..E8`; base Defense for traced subtraction |
| `+0x10` | u16le packed | Read directly from ROM | Six susceptibility codes below |
| `+0x1C/+0x20/+0x24` | u32le ROM pointers | `030008F8 + slot*12 + action_slot*4` | `080482EA..08048304`; three initial actions |

T is enemy target `0x03000A40 + slot*0x38`. Initializer clears T+0x16 and
T+0x18 at `08048256/58`. All these copies are **Confirmed static**.
At `0804D27E..0804D2A4`, signed-low-halfword bounded `T+0x12 + T+0x16`
is compared across eligible enemy actors; the selected slot feeds active-enemy
byte `03000BB7` at `0804D32C..2E`. This establishes turn-selection consumption.
The familiar player-facing label “Speed” is **Probable**, not needed for extraction.

## Action power and damage

Action record `A = 0x08638558 + action_id*0x10`:

| Offset | Width | Proven use |
| --- | --- | --- |
| `+8` | u8 | Doubled offensive power on ordinary damage branch |
| `+9` | u8 | Low 7 bits dispatch type; bit 7 bypasses single-target filter |
| `+A` | u8 | Additional effect parameter, e.g. application threshold in a separate effect pass |
| `+B` | u8 | Extracted raw; meaning unresolved |
| `+C` | u32le | ROM script pointer or null; script semantics not reconstructed |

VM opcodes `40/41/42` select initial action slots 0/1/2: dispatch words at
bus `08040A6C/70/74` lead to stubs `08040F08/30/58`, calling
`08041FCC/0804215C/080422F0`. The handlers copy 16 bytes from the mutable action
pointer array to **`03000C40`** (`08041FDE..08041FF2`, analogous second/third
handlers). `08041E30..08041E82` is a script-stream writer of an action pointer
in that array: initial table slots are not an exhaustive inventory of actions
possible after script mutation.

`080477C0..EC` calls damage/action dispatcher `080495D4` and separate additional
effect pass `08049B58`. `080495D8..EE` indexes low-seven-bit type into the actual
23-word switch table at `080495F8`. Types **0..7 and 12..20** enter `08049654`.
Types 8/9/10/11/21/22 have different destinations; those formulas are not generalized.

On the ordinary branch, party P is `03000938 + party_slot*0x84`:

```text
V = clamp(s16((P.u16[0x18] + P.u16[0x1C]) & 65535), 1, 999)
D = max(s16(2*A.u8[8] - V), 1)
if P.u16[0x10] & 0x4000: D = 0
P.current_hp(+0x12) = max(s16(P.current_hp - D), 0)
```

For actual machine truncations, use `080496FE..08049760` in JSON. The formula
assumes ordinary nonoverflowing HP. `08049722` is the unsigned power read,
`08049724` doubles it, `0804972A` subtracts bounded mitigation, and
`08049746..50` subtracts damage from **party HP**. This party +0x12 must not be
confused with enemy T+0x12. The branch iterates up to party-count `03000BAD`;
action bit 7 or selected party byte `03000BB8` controls target eligibility.
Party byte +5==4 skips the target. An earlier flag-4 branch at `0804968A..FE`
has state-specific random handling and is not included in the compact formula.

No enemy level or party-stat scaling beyond the traced mitigation is read in
this arithmetic. That limited negative finding does not cover upstream scripts
or alternate types. No separate physical/special power pair or elemental
taxonomy is established. Bosses use the same action-table structure; special
boss script/type overrides remain possible.

### Representative static traces

| Enemy | Enemy record bus / file | Initial action slot 0 | Raw power / ordinary power | Base DEF | Susceptibility word |
| --- | --- | --- | --- | --- | --- |
| Watchman Kid 02 | `08634FE8 / 00634FE8` | action 00, `08638558` | 4 / 8 | 10 | 0 |
| Brikky 0C | `086352E0 / 006352E0` | action 0A, `086385F8` | 7 / 14 | 10 | 11263 (`2BFF`) |
| Detector A5 | `0863804C / 0063804C` | action D4, `08639298` | 62 / 124 | 38 | 14431 (`385F`) |
| B5 | `0863850C / 0063850C` | action F8, `086394D8` | 29 / 58 | 22 | 14463 (`387F`) |

For Watchman Kid, record+1C points to action 00 (type 6); for Brikky it points
to action 0A (type 6). Initializer -> mutable slot -> VM opcode 40 copy ->
type-6 ordinary destination -> `2*4` or `2*7` -> party mitigation subtraction
is the same established consumer chain. This demonstrates how their **initial
slot values** are consumed when selected; it is not proof every script selects
every slot. Brikky's verified HP budget 30 is preserved independently.

Detector has initial actions D4/93/C5: power bytes 62/2/51, types 2/10/6.
Its Annoying Siren action 93 (`08638E88`) is type 10 and therefore must not
be assigned ordinary final damage 4. That is only its doubled raw power,
retained in the explicitly conditional `ordinary_path_power` column.
The null script in Cupie 06 slot 2 is exported as missing, not bus zero.

## Defense and dynamic mitigation

Known Gimmick path `080485B0` uses:

```text
V = clamp(s16((T.u16[0x14] + T.u16[0x18]) & 65535), 1, 999)
scratch = attack_value - V
```

Reader/subtraction instructions `0804876C..96` are **Confirmed static**.
The known later clamp gives minimum 1; target flags `T+0x0A & 0x4000`
force scratch to zero (`08048802..10`). Existing record+27/global-count scaling
is documented in `battle_damage_candidates.md`; it was not re-investigated.
The prior user-reported Gear-Yo 26−10=16 and HP 24→8 remain **Confirmed runtime**
only for that reported replay. No new runtime observations are asserted.

Known writers:

- `080482E8`: base ROM +0E -> T+14 during initialization.
- `080418C0..08041902`: selector plus two stream bytes replace T+14 at
  `080418F4`; stream cursor advances. No universal ROM-specific final value
  can be inferred without tracing each control path.
- `08048258` and reset `08041CDE`: clear T+18. Reset also clears T+16.
- `080498BC`: conditionally clears T+18 under target flag 0x40.
- `080498F2..FA`: adds `2*u8(action_buffer+8)` to T+18; `0804991E..26`
  removes that amount under the local counter bound. This is the type-10
  destination in the dispatch table; its full encounter timing is not proven.
- `08048D4C..66`: successful susceptibility-gated effect adds
  `trunc(-50*s16(T+14)/100)` to T+18. Repeated applications are additive;
  counter +9 increases by 3, with local bound 6 and rollback at `08048D76..90`.
  It also clears an opposing flag-0x10 modifier and its counters first.

Thus a persistent `base_defense` column is justified, with dynamic fields
documented separately. A zero stored Defense still encounters clamp-to-1 on
this path. No universal Defense-ignoring category or separate enemy physical /
special Defense has been established. Alternate action calculations are an
explicit dependency, not evidence that all damage subtracts this field.

## Susceptibility decoding

Lookup: original and English file **`00631AD4..D7`**, bus **`08631AD4..D7`**,
four unsigned bytes `64 3C 14 00` = **100,60,20,0**.
For every category, `code=(enemy.u16[0x10]>>shift)&3` and
`application_multiplier_percent=lookup[code]`.

| Shift / bits | Exact field reader (bus; file=bus−08000000) | Handler | Proven effect, operational label |
| --- | --- | --- | --- |
| 0 / 1:0 | `08048A1C` (u8) | `080489D4` | OR target flag 0001; counter +3=max(old,4*high nibble) |
| 2 / 3:2 | `08048ABC` (u16) | `08048A70` | OR target flag 0004; clear counter +4, set state +5=high nibble |
| 4 / 5:4 | `08048B50` (u16) | `08048B10` | Set target event byte +0C=6 |
| 6 / 7:6 | `08048C0C` (u16) | `08048BC8` | Reduce turn-selection input via T+16 by half of signed T+12 |
| 8 / 9:8 | `08048D00` (u16) | `08048CBC` | Reduce Defense via T+18 by half of signed T+14 |
| 10 / 11:10 | `08048DC4` (u16) | `08048DB4` | Add fraction of scratch damage to active party actor recovery field +1E |

Effect dispatcher `08048820` selects an odd Gimmick coefficient byte at
`R+0x29+2*k`, takes its high and low nibbles, and dispatches using low nibble
of Gimmick R+27 (`0804892A..4C`). This was inspected solely to identify the
effect inputs; the completed Gimmick difficulty investigation was not reopened.
The six readers and shifts are instruction-established, not correlations.
Do not translate enemy flag 0004 as party “sleep” merely because party sleep
also uses flag 4: the structures and handlers differ.

### Application formula versus duration

Let `p` be the low nibble passed by the effect dispatcher and `d` its high nibble.
The first, second, fourth, fifth and sixth categories use incoming threshold
`b=8*p`; the third uses `b=4*p`.

```text
q = u8(trunc(b * lookup[code] / 100))
r = u8(PRNG() % 100)
apply only if r < q
```

The calls to division/remainder helpers are `080F7B08/080F7BA0` and PRNG
`0802F73C`; instruction evidence includes the PRNG's masked `0x7FFF` result.
This is a deterministic pseudorandom comparison; uniform independent rolls
are not assumed. A threshold above 100 passes every possible remainder on
this test. A zero lookup always fails this particular gate, but is **not**
proof of immunity to scripts that directly set flags.
For example, low nibble 10 gives threshold 80/48/16/0 for ordinary *8
categories, versus 40/24/8/0 for the third category.

The high nibble affects duration/state only in handlers that actually consume
it. First category multiplies it by 4 before updating a counter; second stores
it as state byte +5. The Defense/turn effects use fixed local +3 counter
increments and maximum 6. Do not interpret lookup 60 as “60% duration”.

The first five handlers reject current signed HP==0, and reject when
**raw u16 initial HP > 3000 AND current signed HP <= 3000**. That raw test
does not reapply the initializer mask. They also reject target flag `0x4000`.
Second category additionally rejects an existing flag 4. The sixth recovery
handler does not contain those HP/flag guards. These are state-dependent gates,
not a generic boss immunity flag or a story-progression dependency.

Watchman Kid codes are all 0 (100% incoming threshold). Brikky codes are
3/3/3/3/3/2 (0/0/0/0/0/20%). Detector codes are 3/3/1/1/0/2
(0/0/60/60/100/20%). B5 is 3/3/3/1/0/2. These are stored factors,
not unconditional observed success percentages. Record field addresses and
exact values for every enemy are in the long-format CSV and JSON.

No elemental field or Fire/Ice/Lightning labels are established. No separate
`enemy_resistances.csv` is emitted: it would duplicate the proven susceptibility
codes or imply unsupported attributes.

## Outputs, reproduction, validation

- `tools/extract/extracted_data/enemies_complete.csv`: 182 records. Every
  authoritative HP column retained verbatim, including evidence and limitations;
  explicit HP aliases added. No effective HP estimates are filled in.
- `enemy_attacks.csv`: 546 initial enemy/action-slot relationships. Duplicate
  action pointers in different slots are intentionally retained. This is
  complete initial-slot extraction, not complete script-reachable action coverage.
- `enemy_susceptibilities.csv`: 1,092 enemy/category pairs; stored multiplier,
  exact field address, code, reader, operational effect and confidence.
- `enemy_attack_defense_susceptibility_evidence.json`: reproducible static evidence.
- `tools/extract/extract_enemy_combat.py` and `tests/test_extract_enemy_combat.py`.

The user-supplied 20,000-HP `distraction_target` and qualifying high-HP
`possible_recurring_enemy` descriptions are hypotheses in distinct columns.
They do not replace verified HP classifications or values. Other proposed
boss practical-HP estimates remain blank because this task does not prove them.

From workspace root, use **new output destinations** (the extractor refuses
existing files, including its own earlier outputs):

```powershell
python tools/extract/extract_enemy_combat.py --japanese-rom "Tomato Adventure (Japan).gba" --english-rom "Tomato Adventure (Japan) (patched).gba" --names tomatotrans-1.1.1/ta_enemies_eng.txt --hp-csv tools/extract/extracted_data/enemy_hp_verified.csv --enemies-csv tools/extract/extracted_data/enemies.csv --raw-csv tools/extract/extracted_data/enemies_raw.csv --output-dir NEW_OUTPUT_DIR --evidence-output NEW_EVIDENCE.json
python -m unittest discover -s tests -p test_extract_enemy_combat.py
```

The standard-library extractor reuses the existing standard-library Thumb
decoder. It validates exact baseline hashes/sizes, table bounds, IDs, names,
existing raw records, HP/Defense agreement, action alignment/bounds, nullable
script bounds, cross-ROM numeric equality, CSV roundtrips and JSON agreement.
Inputs are hashed before and after. Tests include ordinary enemy 02, boss 0C,
Detector A5, 20,000-HP records, a null action script, malformed IDs/names,
truncated/modified ROMs, and intentionally inconsistent susceptibility data.
Validation completed: **8 tests passed**, including fresh CLI reproduction and
refusal to overwrite outputs. All retained native windows match between the
two baseline ROMs. The extraction's input before/after hashes match.

## Dependencies at the stopping boundary

**Confirmed static:** initial action relationships, ordinary action power and
damage consumer, base Defense, listed dynamic writers, six susceptibility
encodings, application comparisons and local state gates.

**Probable:** the player-facing “Speed” label for the turn-selection quantity.

**Unresolved:** complete action-script execution/reachability and replacement
closure; type-specific formulas outside the ordinary branch; all upstream
party mitigation writers; full effect-state random handling on the ordinary
damage branch; player-facing names of three operational categories;
susceptibility bits 12..15; any additional elemental/resistance systems.
The next bounded dependencies are the type destinations recorded in JSON,
action-script dispatch from copied record +C, and target status-message/flag
consumers for operational labels. No exhaustive boss overrides or absence of
other systems is claimed. This is the requested stopping point.
