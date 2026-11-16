# Gimmick Palace ordinary-enemy HP and mitigation investigation

Initial Session 7 research, 2026-10-15, was documentation and bounded static inspection only. The separately approved Detector experiment is recorded below; original research values are retained.

**Status:** Kaizo 100-Binky rewards COMPLETE (user-confirmed 24/24); palace enemy research CURRENT; Mayonen/Namp Hawker placement DEFERRED - FINAL MAJOR OBJECTIVE. Existing Kaizo distribution is retained.

This is a partial bestiary. Exact names, values and map actor links below are Confirmed static. Exact floor names, traversal availability and full dungeon boundaries are not certified. Machine-readable sources, all actor addresses, map records, formation variants and bounded instruction evidence are in `gimmick_palace_enemy_evidence.json`.

## Approved Detector experiment

Detector A5 now has a separately built experimental profile: **HP 120, base mitigation 25**, replacing original retail/source values **135/38**. Rattlin' Dragon 9C is intentionally retained at **262/54**, with its entire record unchanged. All other enemy bytes and existing gameplay changes are preserved. The table below remains the **original-value bestiary**, not a readback from the derived ROM. See [experiment and verification](experiments/detector_hp120_mit25.md). The new ROM is `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256 `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`. Static verification passed; runtime is **UNTESTED**. The shared A5 record change applies wherever Detector is instantiated.

## Provenance and map identification

Original research/input ROM: `tools\patch\output\kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde\kaizo_binky_100.gba`, SHA-256 `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`. Japanese and English baseline numeric fields +08..+13 match all listed original entries; translation name storage differs as expected. Every displayed enemy name was also decoded from its actual translated ROM pointer and checked against `ta_enemies_eng.txt` NAMES rows.

The English source explicitly calls the dungeon **Gimmick Palace** (`ta_menus_eng.txt` overworld node 02, and script messages 891/892). No inspected source calls it Tomato Palace; that alternate-name equivalence remains unestablished. Do not silently relabel other maps Tomato Palace.

Strong named anchors: actor `08156AD4` in map **01B4** references `0812427A`, which displays message 892 (pointer slot `0812427C`) asking to jump to the top floor of Gimmick Palace. Its transition at `081242FA` selects **01E3**. Actor `08159530` in map **01E3** references `0812418A`, displaying message 891 (pointer slot `0812418C`) asking to return to the palace entrance; transition `08124218` selects **01B4**. Thus these are explicit palace entrance/top-floor anchors, rather than a guess from map numbering.

Ordinary door records link 01B4 - 01B2 - 01B5. An undirected connectivity inventory within the scoped map set links 01E3 through 01D1 to 01B7-01BA, 01BC-01CA and other rooms (full edges in JSON). Undirected connectivity establishes association, not guaranteed bidirectional traversability or progression order. The separate late-room component 01CD-01D0/01D6-01D9/01DE-01E2 has exact encounter links but its full connection to the named anchors remains **Probable**: 01E2 event-table `0815B7D4` references `0812EBDA`, which transitions to 01B3 at `0812EBDF`; 01B3 default is `0812EB0F`. Complete bridging/room labels need further tracing. No claim that every map in 01B2..01E6 is a palace ordinary-battle room is made.

## Data structures and evidence

- Map record: `0862D3E4 + mapID*1C`. +0C points to 10-byte door/exit records (FF first-byte terminator); +10 points to event table; +14 points to actor/graphics block. Actor records start at that block +70 and have stride 10 hex, terminated by first byte FF (at most 15 copied by the inspected initializer). `0803F8CE-0803F8D6` establishes +70; `08034ED4-08034F4E` copies the header and actor records.
- Enemy actor control bit 80 makes the unaligned word at actor +0A a battle descriptor: `0806984A-0806989C` reads four bytes, writes `03001978`, and starts the battle. This is an actual ordinary actor collision/interaction path, separate from scripted FE43 boss/event requests.
- Descriptor table is `084559B4`, stride 28 hex. FE43 IDs are one-based; the actors store direct descriptor pointers. `08047C7C-08047CEA` counts non-FF header bytes, selects a variant using RNG/remainder, then copies three enemy pointers into `030008EC`. Four header bytes select layout variants, not four simultaneous enemies. Slot 0 pointer is +04; slots 1/2 for variant k are +08+8*k and +0C+8*k. Null pointers are empty slots. Exact equal probabilities are not certified.
- Enemy records: `08634F50 + enemyID*4C`; IDs are zero-based NAMES row indices, as established by `EnemyInfoAddress` in `inserter/text.cpp:676-681`. Translation replaces +00..+07 with name pointer/length; +0A is uint16 HP masked with 7FFF, +0C is a separate field whose offensive role was not traced here, +0E is the base damage-subtraction halfword.
- Loader `080482CC-080482DC` copies record +0A into target current HP +0E and maximum HP +10. `080482E4-080482E8` copies record +0E into target +14. Targets are `03000A40 + slot*38`. `08048256-08048258` clears +16/+18 during initialization.
- The earlier Gear-Yo subtraction fields now have an established ROM relationship: `0804876C-08048794` subtracts clamp(signed16(T+14 + T+18),1,999). Record +0E therefore is a **base mitigation / Defense-equivalent** for this path. T+18 is mutable; event setters may also change T+14. This is not proof of one immutable universal Defense or of every Gimmick using this calculation. Earlier report deliberately left those fields unnamed; this new initializer trace supplies the missing static link.

Exit destination interpretation is additionally confirmed by `08069A0C-08069A30`: multiply selected exit index by 10, read +04/+05; `08069AA6-08069AAC` stores that halfword as current map ID at `03001936`. High bit 8000 takes the overworld branch rather than a room transition. These scoped instructions are retained in the evidence JSON.

## Partial bestiary, descending HP

All numbers are decimal. Bus/file columns are record starts; HP field = record+0A, base mitigation field = record+0E. Locations are exact map IDs, not invented floors. Confidence S = Confirmed static stats/name/actor formation link. P = complete dungeon/floor association remains probable in the late component described above. Great Boronga entries here are specifically the repeated ordinary-actor formation variants A6/A7/A8; no broader claim about other encounters with that name is made.

| Enemy | ID | Original HP | Original base mitigation | ROM bus / file | Maps | Formation buses | Confidence |
|---|---|---:|---:|---|---|---|---|
| Rattlin' Dragon | `9C` | 262 | 54 | `0x08637DA0` / `0x00637DA0` | 01B7, 01B8, 01B9, 01BC, 01BD, 01BE, 01BF, 01C1, 01C2, 01D7, 01D8, 01D9 | 0x0845642C, 0x084569A4, 0x08456A44, 0x08456ABC | S; P late-area labels |
| Great Boronga | `A7` | 180 | 50 | `0x086380E4` / `0x006380E4` | 01B7, 01B8, 01B9 | 0x08456ABC | S; floor unresolved |
| Great Boronga | `A6` | 150 | 40 | `0x08638098` / `0x00638098` | 01BC, 01BD, 01BE, 01BF, 01C1, 01C2, 01CD, 01CE, 01CF, 01D0, 01D7, 01D8, 01D9 | 0x0845642C, 0x084569A4, 0x08456A44, 0x08456AE4 | S; P late-area labels |
| Mystery Bolt | `99` | 140 | 68 | `0x08637CBC` / `0x00637CBC` | 01B7, 01B8, 01B9 | 0x08456ABC | S; floor unresolved |
| Great Boronga | `A8` | 140 | 50 | `0x08638130` / `0x00638130` | 01B7, 01B8, 01B9 | 0x08456ABC | S; floor unresolved |
| Detector | `A5` | 135 | 38 | `0x0863804C` / `0x0063804C` | 01B7, 01B8, 01B9, 01BE, 01BF, 01C1, 01C2, 01CD, 01CE, 01CF, 01D0 | 0x0845642C, 0x08456ABC, 0x08456AE4 | S; P late-area labels |
| Tomato Box | `98` | 121 | 24 | `0x08637C70` / `0x00637C70` | 01D7, 01D8, 01D9, 01DE, 01DF, 01E0, 01E1 | 0x084569A4, 0x08456A1C | S; P late-area labels |
| Debugger | `97` | 112 | 30 | `0x08637C24` / `0x00637C24` | 01CD, 01CE, 01CF, 01D0 | 0x08456AE4 | S; P late-area labels |
| S.C.Arecrow | `91` | 106 | 42 | `0x08637A5C` / `0x00637A5C` | 01B2, 01B5 | 0x0845697C | S; floor unresolved |
| Megamato | `93` | 102 | 26 | `0x08637AF4` / `0x00637AF4` | 01CD, 01CE, 01CF, 01D0, 01D6, 01D7, 01D8, 01DE, 01DF, 01E0, 01E1 | 0x084569CC, 0x08456A1C | S; P late-area labels |
| Tinimato | `92` | 92 | 20 | `0x08637AA8` / `0x00637AA8` | 01CD, 01CE, 01CF, 01D0, 01D6, 01D7, 01D8, 01DE, 01DF, 01E0, 01E1 | 0x084569CC, 0x08456A1C | S; P late-area labels |
| Papa Genome | `9B` | 83 | 20 | `0x08637D54` / `0x00637D54` | 01BE, 01BF, 01C1, 01C2, 01C9, 01CA | 0x08456404, 0x0845642C | S; floor unresolved |
| StarMato | `A2` | 80 | 12 | `0x08637F68` / `0x00637F68` | 01C9, 01CA | 0x08456404 | S; floor unresolved |
| Mogeha | `90` | 76 | 16 | `0x08637A10` / `0x00637A10` | 01BE, 01C1, 01CD, 01CE, 01CF, 01D0, 01D6, 01D7, 01D8 | 0x084569CC, 0x084569F4 | S; P late-area labels |
| Potty Rider | `94` | 68 | 14 | `0x08637B40` / `0x00637B40` | 01BC, 01BD | 0x08456A44 | S; floor unresolved |
| Potty Rider | `95` | 68 | 14 | `0x08637B8C` / `0x00637B8C` | 01BC, 01BD | 0x08456A44 | S; floor unresolved |
| Potty Rider | `96` | 68 | 14 | `0x08637BD8` / `0x00637BD8` | 01BC, 01BD | 0x08456A44 | S; floor unresolved |
| Fauxmato | `8F` | 64 | 22 | `0x086379C4` / `0x006379C4` | 01B2, 01B5 | 0x08456954, 0x0845697C | S; floor unresolved |

## Formation inventory

Counts below are authored actor references in the scoped tables. They are not encounter rates, mandatory fights or spawn probabilities; scripts, flags and movement can affect availability.

| Descriptor bus / one-based ID | Map IDs | Actor references | Possible formations |
|---|---|---:|---|
| `0x08456404` / `43` | 01C9, 01CA | 18 | 0: StarMato + Papa Genome; 1: StarMato + StarMato; 2: StarMato + StarMato |
| `0x0845642C` / `44` | 01BE, 01BF, 01C1, 01C2 | 15 | 0: Papa Genome + Papa Genome; 1: Papa Genome + Rattlin' Dragon; 2: Papa Genome + Great Boronga; 3: Papa Genome + Detector |
| `0x08456954` / `65` | 01B2, 01B5 | 7 | 0: Fauxmato + Fauxmato; 1: Fauxmato + Fauxmato; 2: Fauxmato + Fauxmato; 3: Fauxmato |
| `0x0845697C` / `66` | 01B2, 01B5 | 4 | 0: S.C.Arecrow + S.C.Arecrow; 1: S.C.Arecrow + Fauxmato; 2: S.C.Arecrow + Fauxmato |
| `0x084569A4` / `67` | 01D7, 01D8, 01D9 | 6 | 0: Tomato Box + Tomato Box; 1: Tomato Box + Rattlin' Dragon; 2: Tomato Box + Great Boronga; 3: Tomato Box + Great Boronga |
| `0x084569CC` / `68` | 01CD, 01CE, 01CF, 01D0, 01D6, 01D7, 01D8 | 16 | 0: Tinimato + Mogeha + Megamato; 1: Tinimato + Megamato + Tinimato; 2: Tinimato + Megamato + Tinimato; 3: Tinimato + Tinimato |
| `0x084569F4` / `69` | 01BE, 01C1 | 4 | 0: Mogeha + Mogeha + Mogeha; 1: Mogeha + Mogeha; 2: Mogeha + Mogeha; 3: Mogeha + Mogeha |
| `0x08456A1C` / `6A` | 01DE, 01DF, 01E0, 01E1 | 18 | 0: Tomato Box + Tomato Box; 1: Tomato Box + Tinimato + Megamato; 2: Tomato Box + Tinimato; 3: Tomato Box + Megamato |
| `0x08456A44` / `6B` | 01BC, 01BD | 14 | 0: Potty Rider + Great Boronga + Potty Rider; 1: Potty Rider + Potty Rider + Potty Rider; 2: Potty Rider + Great Boronga; 3: Potty Rider + Rattlin' Dragon |
| `0x08456ABC` / `6E` | 01B7, 01B8, 01B9 | 3 | 0: Mystery Bolt + Detector + Great Boronga; 1: Mystery Bolt + Great Boronga; 2: Mystery Bolt + Rattlin' Dragon; 3: Mystery Bolt + Great Boronga + Great Boronga |
| `0x08456AE4` / `6F` | 01CD, 01CE, 01CF, 01D0 | 9 | 0: Debugger + Debugger; 1: Debugger + Detector; 2: Debugger + Great Boronga; 3: Debugger + Detector + Debugger |

## Annoying Siren

**Confirmed static:** this exact English string is ATTACKS row 93, not NAMES row 93. Enemy 93 is Megamato. The attack record is `08638E88` / file `00638E88`; its script pointer is `080CFAB4`. Direct attack-slot pointers in the 182 enemy records identify Cybercop (62, HP 220/base mitigation 41, pointer field 08636C84) and Detector (A5, HP 135/base mitigation 38, pointer field 0863806C). Cybercop uses record+1C; Detector uses record+20.

Detector is explicitly present in ordinary palace-associated descriptors `08456ABC`, `0845642C` and `08456AE4` (variants and map links above). Thus Detector is the **Probable** species behind the user's palace recollection. Cybercop is not in the scoped palace ordinary actor formations and must not be added to this dungeon bestiary on the attack name alone. User experience that Choo-Choo is not an easy solution is preserved as a runtime report, not evidence of elemental resistance, immunity, armor penetration or a Siren-specific mechanic. Those mechanics remain unresolved.

## Initial pacing analysis (historical)

1. **Rattlin' Dragon (262 HP, mitigation 54):** highest HP in the inspected ordinary actor formations. Appears as a partner in several group types, so inspect both its damage taken and the aggregate formation cost. It is a plausible unidentified troublesome enemy, not an identification of the user's memory.
2. **Mystery Bolt (140/68):** highest base mitigation in this partial ordinary bestiary. Its formations can pair it with Detector and Great Boronga variants. Reducing HP alone might leave low-damage turns; measure actual attacks first.
3. **Detector (135/38):** Annoying Siren user; occurs with Papa Genome, Mystery Bolt and Debugger, including three-enemy formations. Particularly relevant to the reported Choo-Choo experience, whose cause is unresolved.
4. **Great Boronga A7/A6/A8 (180/50, 150/40, 140/50):** distinguish these three records rather than collapsing their shared name. Consider their role as partners in repeated ordinary formations; do not alter boss/event encounters just because the displayed name matches.
5. **Tomato Box (121/24), Debugger (112/30), S.C.Arecrow (106/42):** moderate HP can still cost extra actions in pairs/triples; Scarecrow has relatively high mitigation. Tinimato/Megamato/Mogeha multi-enemy groups may matter through combined HP rather than a single large enemy.

The initial analysis selected no replacement values. Subsequently, the user approved only Detector 120/25 and explicitly retained Rattlin' Dragon 262/54; the experiment above implements that decision. For a measured damage D, a simple identical-hit estimate is ceil(HP/D), with breakpoints at multiples of D; changing base HP would save one action only when crossing a measured breakpoint. Actual damage variability, targeting, minigame performance, overkill, status effects, AWE, and multiple enemy actions can invalidate that estimate. No attack/turn estimates are supplied without measurements.

## Exclusions and unresolved questions

- Brikkypress (9A) has HP 110/base mitigation 90 at `08637D08`, but no repeated ordinary actor formation link was established in this scope. It is excluded from balance candidates pending ordinary/boss/hazard classification. High Defense alone is not enough to include it.
- Nabira 9D (3480 HP) and Tomato Mecha A1 (3430 HP) are not among these ordinary actor formations. They are excluded; no bosses/minibosses are proposed for balancing. Scripted boss requests were not added to the candidate table.
- Complete palace boundary, exact floor/section names, script activation conditions, enemy respawning and real encounter rates remain unresolved. Nearby maps 0174..01A4 have different enemy families and were not silently merged into the palace.
- Siren action effects, Choo-Choo-specific interactions, and actual damage against each candidate need separately authorized investigation. No emulator commands or changes are executed or requested here.

## Files inspected and reproduction scope

Read project constraints and context: `AGENTS.md`, `tomato_adventure_modding_plan.md`, `session_handoffs/SESSION_HANDOFF_1.md` through `_6.md`, `reverse_engineering/kaizo_binky_100_proposal.md` and `.json`, `experiments/binky_exchange_rate_two.md`, `experiments/binky_exchange_session5_closeout.md`, `battle_damage_candidates.md`, `symbols.md`, `memory_map.md`, `pre_oystown_progression.md`, `gimmick_calculations.md`/runtime context from the preceding investigation, and debugger/checkpoint reports. Earlier runtime claims remain attributed, not independently reproduced.

Technical sources actually read for this extraction: `tomatotrans-1.1.1/inserter/text.cpp` (EnemyInfoAddress/InsertEnemies), `asm/battle_enemies.asm`, `asm/battle_message.asm` search references, `ta_enemies_eng.txt`, `ta_menus_eng.txt`, `ta_script_eng.txt`, `ta_table_eng.txt`, `pointers1.dat`, `hacking notes.txt`; `tools/analyze/thumb_inspect.py`, `pre_oystown_progression.py`; active ROM, Japanese original and English baseline. No external source, Ghidra or emulator was used.

Bounded binary work: selected native windows recorded in JSON; 182 known enemy records for Siren pointer lookup; 53 candidate map records 01B2..01E6, max 16 actors and 48 exits each; explicit palace title/teleporter scripts and arrival leads; small preliminary metadata samples 0174..01ED; targeted literal/transition searches in known native/script regions. Raw searches choose leads and are not by themselves control-flow proof.

No analysis script was added. JSON retains exact extracted stat addresses, actor-to-descriptor references, variants, map exit edges, names and disassembled evidence so the findings can be independently checked. Gameplay/ROM/save/checkpoint artifacts were fingerprinted before and after documentation generation.

Validation: 18 stat rows and 114 actor pointers were rechecked against the active ROM; every listed numeric field matches both baselines. The Kaizo closeout contains 24 unique rewards and explicitly records absence of a final counter readback. The selected 42-artifact before/after protection audit passed.
