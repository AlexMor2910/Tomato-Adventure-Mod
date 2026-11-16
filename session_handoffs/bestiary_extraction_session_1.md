# Tomato Adventure — Bestiary Extraction Session 1 Handoff

**Session date:** 2026-10-20  
**Status:** Session deliberately closed by the user. Data extraction has advanced through Gimmicks, enemies, Binky pickup census, and field-map rendering. **General graphics extraction has not begun.**  
**Authorization:** This document is a handoff, **not** authorization to run Codex, modify ROMs, launch emulators, perform new analysis, or start another extraction task.

## 1. Project direction and operating rules

The user decided to stop spending resources on the unresolved two-Hawker placement objective and pivot to read-only data extraction from *Tomato Adventure* (GBA), favoring reproducible **Python scripts** and bounded Codex static analysis rather than autonomous exploratory changes. Desired deliverables:

1. All Gimmick statistics in CSV.
2. All enemy data (ATK, DEF, HP, susceptibilities) in CSV.
3. Binky counts by room and overworld node.
4. Extracted field maps.
5. Extracted graphics (still pending).

Preserve Japanese and English source ROMs, cumulative experimental ROMs, patches, CSVs, reports, evidence, saves, savestates, and previous tool outputs. Favor **new versioned artifacts**, hashes, read-only operations, tests, and explicit confidence labels. Do not overwrite files; do not distribute copyrighted ROMs or extracted graphics. The **user operates mGBA**; Codex must not independently launch or control it. No gameplay modification is requested as part of extraction. Refer to `AGENTS.md` and `tomato_adventure_modding_plan.md`.

The previous modding objective is explicitly paused: Hawker placement has **not** been implemented or runtime-tested; Session 10 Gate A was reported PASS, Gates B/C/D and overall E blocked. Do not resume Hawker work automatically. The preceding cumulative experimental ROM was reported as `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`, SHA-256 `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0` (verify against active workspace before relying on it). Prior achievements remain distinct: Kaizo 24/24 rewards user-confirmed in tested gameplay, universal two-Binky exchanges successful in six tested scenarios, Detector 120 HP / 25 mitigation statically verified but not runtime-tested, Rattlin' Dragon unchanged at 262 HP / 54 mitigation.

## 2. Gimmick statistics extraction

### Results

- Original Gimmick table: file `0x0062C250`, bus `0x0862C250`; **50 records**, stride `0x58`, runtime IDs **1–50**.
- Verified original base Attack byte: record offset `+0x22`.
- English Gimmick names **50/50** recovered from the `RESTRUCT` / name mapping in translation toolkit `ta_menus_eng.txt`, with zero-based name indices mapped to runtime IDs +1.
- Candidate fields `+0x28..+0x38` were initially interpreted as nine 16-bit percentages; bounded Codex follow-up reported the correct interpretation as **nine pairs of unsigned bytes**, with the **low byte a percentage** and high byte a separate auxiliary value. This resolves previously anomalous high `u16` values.
- Codex-reported common **menu** formula for all 50: `floor((base + upgrade) * percentage / 100)`.
- Menu adjustment supports difficulties **1–7**. Slots **8–9 duplicate slot 7** but have implemented calculation paths; ordinary gameplay reachability of these slots remains unproved.
- Meanings of auxiliary bytes and universal battle-damage behavior remain unresolved; do not equate displayed Attack with damage for all Gimmicks.
- Earlier user-confirmed Gear-Yo example: base 21, first coefficient 124%, displayed Attack 26 at difficulty 1 / upgrade 0; separately observed battle damage 16 after a 10-point target subtraction quantity. Do not generalize the runtime observation across all Gimmicks.

### Artifacts

Initial Python files under `tools/extract/`: `extract_game_data.py`, `make_gimmicks_csv.py`, `make_gimmicks_csv_v2.py`, `extract_gimmick_names.py`, `merge_gimmick_names.py`. Initial CSVs included `gimmicks_raw.csv`, `gimmicks.csv`, `gimmicks_v2.csv`, `gimmicks_named_complete.csv`, `gimmick_names_to_fill.csv` (historical intermediate mapping).

**Later Codex-reported canonical scaling artifacts in the active workspace** (not all attached to this conversation):

- `reverse_engineering/gimmick_difficulty_scaling.md`
- `reverse_engineering/gimmick_difficulty_scaling_evidence.json`
- `tools/extract/extracted_data/gimmicks_scaling_verified.csv`
- `tools/extract/convert_gimmick_scaling.py`

Codex reported synthetic and CSV/JSON consistency tests passed; exact counts were not supplied for this task. Do not silently replace the canonical CSV with earlier, less accurately labeled coefficient CSVs.

## 3. Enemy database, action power, DEF, susceptibility

### Base table and naming

- Enemy table: file `0x00634F50`, bus `0x08634F50`, stride `0x4C`, **182 records**, IDs `0x00–0xB5`, exclusive end `0x00638558`.
- English names mapped from translation toolkit `ta_enemies_eng.txt` `NAMES:` section.
- Raw initial HP: `u16(+0x0A) & 0x7FFF`.
- Base Defense-equivalent / mitigation: `u16(+0x0E)`; copied into a runtime target field. Other dynamic target modifiers can affect final damage; this value alone is not a universal invariant Defense.
- `extract_enemies.py`, `enemies.csv`, `enemies_raw.csv` were generated in the early phase.

### Critical boss HP correction — established static findings

**There is no universal subtraction of 3,000 in the battle HP initializer.** It copies the masked record field to both current and maximum HP. Certain boss/actor control scripts compare current HP with **3,000** and explicitly set HP to zero when a condition is met. Consequently, `raw_hp - 3000` can represent a useful **local scripted-threshold damage budget** for supported paths, but cannot be applied to all high-HP records indiscriminately.

Codex-reported static examples:

| Enemy | ID | Initialized HP | Local threshold budget / note |
|---|---|---:|---|
| Brikky | `0C` | 3030 | 30, script-supported |
| Grikky | `0D` | 3025 | 25, script-supported |
| Brikky | `1D` | 3130 | 130, partner interactions possible |
| Grikky | `1E` | 3110 | 110, paired handling |
| Brikky | `49` | 3200 | 200, partner interactions possible |
| Grikky | `4A` | 3250 | 250, paired handling |
| Brikky | `73` | 3400 | 400, conditional pair paths |
| Grikky | `74` | 3250 | 250, conditional pair paths |
| Brikky / Grikky | `AE / AF` | 3700 / 3650 | Additional 3200/state conditions: not assigned simple verified effective HP |

Death Lilby `5F`: initialized HP **3600**; scripted checks at **3450, 3200, 3000**. User recalls a three-phase or three-target mechanic, consistent with a **proposed** 600 practical-HP budget and transitions after approximately 150 and 400 damage, but specific final defeat causality remains unproved.

Two `20000`-HP arm records (`76/77`) are described by the user as **distracting targets** during the fifth main boss; scripts can remove arms through other actor-controlled state. Do not infer 17,000 practical HP or invulnerability. Exact-3000 records may use special scripted win conditions, sometimes turn-based per user recollection, but must not be treated as zero effective HP. User suspects some other unresolved high-HP cases represent reappearing/reviving enemies: **hypothesis only**, not established for each record. The battle interpreter can restore current HP from maximum HP, but universal connection is unproved.

**Codex-reported HP CSV results:** 182 records; **119** ordinary effective-HP entries, **16** supported local threshold-budget entries, **47** effective-HP cells left unresolved. Keep `initialized_hp`, `effective_hp`, `threshold_margin_candidate`, and hypotheses separate. Local threshold budget is not necessarily independently required damage to end a multi-actor encounter.

HP files attached in this conversation: `enemy_hp_encoding.md`, `enemy_hp_verified.csv`, `battle_damage_candidates.md`. The separately reported `reverse_engineering/enemy_hp_encoding_evidence.json` should be read directly in the workspace if needed.

### Subsequent ATK / susceptibility findings (Codex-reported)

- **182** rows in master `enemies_complete.csv`, preserving authoritative HP columns.
- **546 initial action-slot relationships** in `enemy_attacks.csv`; these are relationships, **not 546 unique attacks**.
- Ordinary action power uses **`u8(action + 8) * 2`**, not necessarily a single enemy-wide ATK stat.
- Base Defense: enemy `u16(+0x0E)`.
- **1,092 susceptibility entries** across six codes per enemy. Codex reports application multipliers **100%, 60%, 20%, 0%**; these affect status/effect application, **not automatically elemental damage resistance**.
- Alternate action formulas, complete script-driven action coverage, some status labels, and susceptibility bits 12–15 remain unresolved. The bestiary is **partially verified**, not universally complete.
- Codex reported **8 tests passed** and previous artifacts unchanged.

Codex-reported workspace artifacts:

- `reverse_engineering/enemy_attack_defense_susceptibility.md`
- `reverse_engineering/enemy_attack_defense_susceptibility_evidence.json`
- `tools/extract/extracted_data/enemies_complete.csv`
- `tools/extract/extracted_data/enemy_attacks.csv`
- `tools/extract/extracted_data/enemy_susceptibilities.csv`
- `tools/extract/extract_enemy_combat.py`
- `tests/test_extract_enemy_combat.py`

## 4. Binky pickup census and node totals

The first bounded static census of the game's **registered pickup structure** found **74 distinct pickups awarding 74 Binkies**, with this specific registration structure's census reported complete. This is **not** a proven game-wide fixed-Binky total. **Seven scripted reward candidates** remain unresolved. Repeatable AWE/Hawker exchanges, shop purchases, enemy drops, and other nonfixed sources must not be counted as fixed room collectibles.

- **35** Binky pickups have **probable** node assignments.
- **39** remain without supported node assignments.
- Count quantities rather than number of objects when they can differ.
- Map ID and overworld node ID are different; reachability does not prove unique node ownership. Unknown totals must not silently be recorded as zero.
- Codex reported **10 tests passed**, protected files unchanged.

Codex-reported artifacts:

- `reverse_engineering/binky_location_extraction.md`
- `reverse_engineering/binky_location_extraction_evidence.json`
- `tools/extract/extracted_data/binky_locations.csv`
- `tools/extract/extracted_data/binkies_per_room.csv`
- `tools/extract/extracted_data/binkies_per_node.csv`
- `tools/extract/extracted_data/binky_map_nodes.csv`
- `tools/extract/extracted_data/binky_other_sources.csv`
- `tools/extract/extracted_data/binky_unresolved.csv`
- `tools/extract/extract_binky_locations.py`
- `tests/test_extract_binky_locations.py`

## 5. Field map PNG extraction and directed graph

The map renderer reused the known map-record structure (file table `0x0062D3E4`, stride `0x1C`; music selector lower six bits at record byte `+5`) and existing translation/map/tile knowledge.

**Codex-reported results:**

| Output | Result |
|---|---:|
| Map catalog entries | **494** |
| Successfully rendered maps | **471** (~95.3%) |
| Unsupported maps | **23**, unresolved tile sources |
| Supported directed map transitions | **864**, script-driven coverage partial |
| PNGs per supported map | 3 layers + combined initial-background image |
| Node assignment improvement for Binkies | **None**: 35 probable and 39 unassigned remain |
| Automated tests | **9 passed** |

Outputs:

- `reverse_engineering/map_extraction.md`
- `reverse_engineering/map_extraction_evidence.json`
- `tools/extract/extract_field_maps.py`
- `tools/extract/extracted_data/maps.csv`
- `tools/extract/extracted_data/map_transitions.csv`
- `tools/extract/extracted_data/map_node_assignments.csv`
- `tools/extract/extracted_data/binky_map_nodes_v2.csv`
- `tools/extract/extracted_data/binkies_per_node_v2.csv`
- `reverse_engineering/exports/field_maps_v1/` (local PNGs)

Do not claim 864 directed edges give a complete graph or that all background images were visually validated in-game. The 23 unsupported maps need source/tile resolution; do not fake imagery. The map graph did **not** resolve the 39 unassigned Binkies, and original pickup identities/quantities were preserved.

## 6. Exact stopping point and deferred work

The user requested to **stop here** after reviewing the map extraction results. The next **proposed** (not authorized or started) objective is **general graphics extraction** using Python and tightly scoped Codex static research, reusing:

- `tools/extract/extract_field_maps.py` for native GBA tile/palette/map decoding;
- `tools/analyze/extract_palace_enemy_sprites.py` for the previously investigated Detector/Rattlin' Dragon sprite frames (only those enemies' reproducibility is established; not a general sprite decoder);
- the translation toolkit's `inserter/`, image resources, and compression handling.

Potential future graphics: enemies, NPCs, player characters, Gimmick animations/effects, portraits, interface elements, tilesets/palettes. For any future task: record source offsets, palettes, dimensions, frames, encoding, confidence, and unresolved resources; export only reliably decoded assets; keep copyrighted exports local and outside public commits. **Do not launch graphics extraction automatically from this handoff.**

Other optional follow-ups are resolving 23 map sources, seven scripted Binky reward candidates, 39 missing Binky node associations, special boss HP behavior, alternate enemy attack formulas and susceptibility status labels, and Gimmick auxiliary-byte semantics. These are **documented open questions**, not reasons to restart broad investigations without explicit request.

## 7. Provenance and instructions for the next session

This handoff is based on uploaded older project handoffs, uploaded raw/intermediate CSVs and HP research, and **Codex completion summaries supplied by the user**. The newest Gimmick-scaling, comprehensive enemy-combat, Binky, and map source reports/JSON/CSVs/PNGs were **not attached here and have not been independently inspected in preparation of this handoff**. Paths and passing-test counts for them are reported by Codex, not freshly verified by this assistant. Consult the actual active repository files before changing confidence levels, using generated outputs, or modifying scripts. No ROMs, patches, saves, or emulator sessions were modified to create this handoff.

When separately asked to resume:

1. Read `AGENTS.md`, the modding plan, Session 10 closeout, and this handoff; respect the Hawker pause and other protected artifacts.
2. Inspect the current project's actual reports/scripts/CSVs and source ROM fingerprints; distinguish attached evidence from Codex-reported summaries.
3. Confirm the newly requested goal before initiating a bounded extraction; **do not interpret this handoff as permission to run anything**.
4. Prefer Python for deterministic extraction/CSV/PNG and Codex for narrow static dependencies; no unrestricted whole-ROM analysis, automatic mGBA operation, or speculative game patches.
5. Preserve confirmed facts, user gameplay hypotheses, and unresolved values in separate fields; never promote a numeric pattern to a proven game mechanic without supporting code or runtime evidence.

**Final status:** Gimmicks named and menu scaling mapped (some auxiliary/battle meanings unknown); 182-enemy partially verified bestiary produced; 74 registered Binkies counted with incomplete node ownership; 471 of 494 field maps rendered; general graphics extraction **not started**. **Session closed at the user's request.**
