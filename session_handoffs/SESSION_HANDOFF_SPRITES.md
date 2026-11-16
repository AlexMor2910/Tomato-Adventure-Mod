# Tomato Adventure — Session Handoff: Sprite Extraction Closeout and Cumulative ROM Hack

**Handoff date:** 2026-10-27  
**Current phase:** Close sprite extraction; next session is dedicated to preparing **one cumulative English-language Tomato Adventure ROM hack** incorporating the five user-requested feature groups.  
**Evidence basis:** Uploaded `AGENTS.md`, Session Handoffs 1–10, `bestiary_extraction_session_1.md`, and the user's later Codex completion summaries through field-sprite extraction v1. The active Windows repository, ROMs, v1–v6 evidence files, PNGs and scripts **were not inspected directly** while writing this handoff. Treat summarized Codex results as reported, and verify the actual workspace at the start of the next session.

## 1. User decisions and project scope

The user will **classify the extracted sprites manually**. Do **not** assign more sprite-classification or playable-character name-binding work to Codex now. End the extraction phase with its existing versioned artifacts; no more extraction runs are required for this handoff.

The next session must focus on **constructing and testing a cumulative ROM hack** with these five requested changes:

1. **Music replacements:** Dropper Village → Pokypine Forest; Mayonen Caverns → Mayonen; Captain Grocko Ship → Namp Lagoon; Oyster Sewers → Oystown; the Vault → Oops Mannor (retain user's destination names; verify exact in-game identifiers and spelling before mapping songs).
2. **Hanzo reward and Gimmick balance swap:** Hanzo Lab 1 grants **Dojo Pup instead of Erupter**; Hanzo Lab 2 grants **Erupter instead of Dojo Pup**. Swap **their Attack values at every difficulty/level**, i.e. for each relevant displayed attack level, Dojo Pup receives Erupter's former value and Erupter receives Dojo Pup's former value. “Eruptor” in the request appears in earlier research as **Erupter**; confirm the mapping from in-ROM names, not spelling alone.
3. **Kaizo:** Preserve the established proportional **180 → 100 cumulative Binky** threshold rebalance and all 24 existing rewards and prerequisites.
4. **Hawker exchanges:** Every **existing, available** Hawker must give exactly **two Binkies per qualifying full AWE gauge** for all supported characters/story branches, preserving costs, dialogue, gauge consumption, capacity and cancellation semantics. **This request does not reauthorize adding two new Hawker NPCs to Mayonen/Namp.** That earlier placement objective was explicitly paused and remains unimplemented.
5. **Detector:** HP **135 → 120** and base mitigation **38 → 25**; leave Rattlin' Dragon at HP **262** and mitigation **54**.

No further sprite work, map-renderer research, graphics publication, or Hawker placement should distract from this release-preparation objective.

## 2. Sprite-extraction closeout — preserve and stop

### Enemy sprites: latest Codex-reported v6

- 182 enemy records cataloged; **157** have scoped sprite output; **25** are context-dependent shared-renderer participants without proven standalone child silhouettes.
- **330** v5 native frames preserved; v6 adds **five labeled composite profiles**, with **18 composite frames reusing unchanged v5 PNGs** (not 18 new unique sprite extractions).
- Chekkit `0x8C`: four transparent 80×80 OBJ frames added in v5 via documented upload projection; BIOS overflow side effects **not runtime-verified**.
- All 25 remaining actors select tile data while one root descriptor submits the full OBJ list, including base blocks. Do not claim 182 standalone PNG sprite sets.
- v6 files: `reverse_engineering/multipart_enemy_ownership_v6.md`, `_evidence.json`, `reverse_engineering/exports/enemy_sprites_v6/final/`, `tools/analyze/multipart_ownership_v6.py`, corresponding tests.
- Codex reported **46 tests passed** and **9,070 protected files unchanged**. Optional future *user-operated* breakpoint at `0x08040424` during Big Donut transition was documented, **not performed**. Defer it.

### Field sprites: latest Codex-reported v1

- **371** discovered resources: **332** with scoped frames, **29** partially supported animation/frame resources, **10** unresolved palette bindings.
- **4,390** native transparent PNGs exported.
- Catalog crosses **494 maps**, **2,987 actor registrations** and **522 descriptor/palette bindings**.
- Default player resource has **14 frames/five sequences**, identity as DeMille only **Probable**. Alessa/Sofoubi/Relleck remain anonymously cataloged; cardinal facing names and complete animation transitions are unproved. **User will classify these manually**; do not silently assign identities.
- Files: `tools/extract/extract_field_sprites.py`, tests, `reverse_engineering/exports/field_sprites_v1/final_verified/`, previews, `reverse_engineering/field_sprite_extraction_v1.md`, evidence JSON, `unsupported.csv`, `playable_coverage.json`.
- Codex reported **17 tests passed** and **9,105 protected files unchanged**.

**Closeout policy:** Preserve all generated CSVs/JSONs/PNGs/reports/scripts and their confidence labels. Do not claim a whole-game complete sprite census or runtime-proven animations. Keep copyrighted extracted assets local, excluded from public releases/commits. The next task does **not** depend on further sprite classification.

## 3. Proven cumulative mod baseline and isolated historical experiments

### Authoritative cumulative *starting candidate* for next session (Codex-reported)

`tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`

SHA-256: `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`

The latest prior handoffs report that this ROM cumulatively retains the English translation, Alessa recruitment experiment, two-Binky exchange, Kaizo 100-Binky patch, and Detector balance changes. **Reverify the actual hash, source ancestry, and each cumulative byte ledger before extending it.** The Alessa recruitment wrapper is experimental and not a replacement for full natural recruitment/progression; consider whether it belongs in the intended release rather than blindly propagating every historical test-only modification. Prior handoffs describe this ROM as the cumulative experimental input, not a vetted public release.

Historical fingerprints:

| Artifact | SHA-256 | Evidence status |
|---|---|---|
| Japanese source ROM | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` | protected baseline |
| English-translated baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` | protected baseline |
| Kaizo cumulative experimental ROM before Detector | `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2` | Codex-reported, Kaizo 24/24 user-tested |
| Detector cumulative experimental ROM | `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0` | Codex-reported static verification, runtime not done |
| Hanzo 1 standalone Dojo Pup experiment | `749762aa8c3c0fae433d46c0ebbcbf4f54646790baf4b6129414e6e5832cdfea` | user-confirmed Hanzo 1 reward and battle usability on separate ROM |
| Mayonen Caverns standalone music experiment | `7fc50105e340510079158ca74e61f778b63b3276793ec9b6ffbe29c2af75c761` | user-confirmed map `0x001E` entry only on separate ROM |

**Important:** The Hanzo 1 reward change and Mayonen single-room BGM experiment were **not yet shown to be incorporated into the Detector cumulative ROM**. All five new song-area tasks and the Hanzo 2/Attack swap are separate integration work.

## 4. Feature-by-feature implementation specification and evidence gaps

### A. Music — five area families

Requested source area → target song/area:

| Affected area | Desired music | Current evidence | Required next step |
|---|---|---|---|
| Dropper Village | Pokypine Forest | No complete map-ID/song-ID list supplied | Identify all intended village rooms, map records and event overrides; verify original and target song selector |
| Mayonen Caverns | Mayonen | First confirmed Caverns map `0x001E` already patched/tested **separately**, selector byte `0x0D→0x07` at file `0x0062D731`; user heard Mayonen theme after fresh map entry | Enumerate and prove *all* Caverns rooms and override behavior; don't assume all adjacent maps are Caverns |
| Captain Grocko Ship | Namp Lagoon | No verified room list/song ID supplied | Map the full ship region, music selectors, transitions/overrides, and target song |
| Oyster Sewers | Oystown | No verified room list/song ID supplied | Map sewer rooms, current selector and target song, overrides |
| the Vault | Oops Mannor | No verified room list/song ID supplied | Verify exact area identity, spelling, room membership, desired music selector, and overrides |

Established generic mechanic: map record table **file `0x0062D3E4`**, stride **`0x1C`**; music selector occupies the **low six bits of byte `+5`**, upper bits must be preserved. An ordinary playback path uses **sound ID = selector + 200**; event commands **`FE A7`, `FE A8`, `FE A9`, `FE AB`** may override map music. In prior Mayonen experiment map `0x0048` selected Mayonen theme `0x07`, playback `0xCF`; Caverns `0x001E` originally selected `0x0D`, playback `0xD5`. Those facts do **not** prove selector values for the other requested areas.

**Acceptance:** For each area, produce a map-ID/room-name/current byte/new byte/target selector/source evidence/override status ledger; change only verified scoped records and necessary verified overrides; manually test first entry, movement through internal rooms, battle-return/transition and re-entry. Avoid unrequested adjacent maps. Unproven region boundaries are blockers, not permission for broad substitutions.

### B. Hanzo Lab 1 / Lab 2 rewards and per-level Attack inversion

**Already established:** First Hanzo reward script command at bus `0x0810D698`: `FD 0B 1C 1B 00`. The Erupter ID operand is at **file `0x0010D69B`**; standalone experimental replacement **`1B→29`** grants **Dojo Pup** (ID `0x29`, decimal 41) instead of **Erupter** (ID `0x1B`, decimal 27). User confirmed the text, menu and Dojo Pup battle use. The patch script `tools/patch/hanzo_dojo_pup.py` was created historically. Verify it against the latest cumulative ROM before integration.

**New/unproved:** Hanzo Lab 2's original Dojo Pup reward script, precise operand and progression path have **not** been mapped in the provided handoffs. Codex must locate and prove the actual Hanzo 2 reward command and change its selection to Erupter using the normal acquisition handler. Verify no duplicate/unobtainable Gimmick problems under normal story progression and preserve event flags, dialogue where relevant, and character ownership.

**Attack inversion is new and not equivalent to swapping base Attack bytes.** The Gimmick table is file `0x0062C250`, **50 records**, stride `0x58`, runtime IDs `1..50`. Original base Attack is record byte `+0x22`; difficulty/menu coefficients live around `+0x28..+0x38` as **nine pairs of bytes** (low byte percentage; high byte auxiliary with unresolved meaning). For ordinary menu computation Codex reported **`floor((base + upgrade) * percentage / 100)`**, difficulties **1–7**, with slots **8–9 duplicating slot 7** despite implemented calculation paths. User previously proved one Gear-Yo example; do **not** claim that the menu formula proves all battle damage formulas.

**Exact requested acceptance target:** for **each difficulty/level** and the agreed upgrade state(s), displayed Attack for Dojo Pup after patch equals Erupter's original displayed Attack and vice versa. Investigate whether swapping full attack-defining data (base and relevant coefficients, with care for high auxiliary bytes) achieves the result without unintended other-stat changes; alternatively apply the smallest validated field-level patch. The meaning of high auxiliary bytes and upgrade-dependent effects must be established or explicitly bounded. Provide baseline/after per-level comparison table, byte ledger, item owner and battle-use regression. Do not swap whole Gimmick records, ownership IDs, animations, names, or effects without proof and approval.

### C. Kaizo — cumulative donations 180 → 100

**Completed, user-confirmed principal objective:** all **24/24** Kaizo rewards acquired and functional during tested gameplay using the Kaizo experimental ROM. No final donation-counter readback of exactly `100` was separately supplied; negative-path, save/reload and capacity regressions remain outstanding. Preserve existing implementation.

Approved sequential thresholds (old → new):

`4→2, 7→4, 10→6, 13→7, 17→9, 21→12, 26→14, 31→17, 37→21, 43→24, 50→28, 57→32, 65→36, 73→41, 81→45, 90→50, 99→55, 109→61, 119→66, 130→72, 141→78, 153→85, 165→92, 180→100`.

The patch reportedly changes exactly **51 bytes**, including 48 reward display/comparison operand bytes, file `0x000FC7A9` cumulative-cap comparison, file `0x000FCCD8` clamp, and English dialogue byte `0x0064FE13` (`78→70`, 180→100). `tools/patch/kaizo_binky_100.py` and `reverse_engineering/kaizo_binky_100_proposal.{md,json}` have the exact approved ledger. Original flags, rewards, script branches and whole-stack donation behavior stay unchanged: at 99 donated, donating five removes all five but credits only up to 100, leaving four uncredited. The complete unlock remains subject to original Hanzo story prerequisites.

**Next step:** verify **already present and unchanged** in cumulative input; do not recompute proportional thresholds or reimplement another Kaizo patch.

### D. Hawker — two Binkies per full AWE gauge

**Completed, user-confirmed:** six applicable exchange scenarios passed: Alessa early/intermediate/late, Sofoubi early/late, Relleck applicable late. Successful exchange awards **exactly 2 Binkies**, consumes selected full AWE gauge and finishes normally. The previously validated two-Binky patch is part of the reported cumulative experimental ancestry. Preserve the rate-two code and original Oystown tutorial.

**Not yet proven:** cancellation/refusal, partial gauge, capacity near 97/98/99, other full-gauge preservation, dedicated save/reload, and all contexts the user calls “any point in the game.” Do not upgrade six tested scenarios to an exhaustive runtime guarantee. Test existing Hawkers when available through normal progression; avoid story-bypassing flags as general acceptance proof. If the user wants **new Hawkers in Mayonen/Namp**, that is a *separate paused feature* with unsolved actor-registration/movement/graphics lifetime gates and not part of this build request.

### E. Detector stats

Already statically patched in the cumulative input: enemy ID `0xA5`, original record table file `0x00634F50`, stride `0x4C`. Exact Detector offset changes:

| Field | File offset | Original | Patched |
|---|---|---|---|
| HP | `0x00638056` | `87 00` (135) | `78 00` (120) |
| Base mitigation | `0x0063805A` | `26 00` (38) | `19 00` (25) |

Codex reported independent static verification. **Runtime Detector battle testing was never reported.** Rattlin' Dragon `0x9C` remains HP `262`, mitigation `54`. Verify in the cumulative ROM; no new balance changes.

## 5. Recommended next-session workflow — one reproducible cumulative build

1. **Reconnaissance, preservation, and baseline audit:** read `AGENTS.md`, the modding plan, latest handoffs and active patch reports/scripts/JSON; verify hashes and parentage of the Japanese source, English baseline and Detector cumulative ROM. Audit current protected files. Decide explicitly whether the historical Alessa recruitment test wrapper belongs in the release candidate; do not silently propagate test-only progression shortcuts into a normal-play release.
2. **Produce a feature matrix:** identify already present changes (Kaizo, two-Binky, Detector) versus missing changes (five music areas, Hanzo 1, Hanzo 2, Attack inversion). Establish a precise evidence-backed address/operand map and byte-level proposal for each new change. Do not invent room IDs, music selectors, Hanzo 2 operand or attack coefficients.
3. **Investigate only missing dependencies, bounded:** enumerate music rooms and event overrides, locate Hanzo 2 reward, prove per-level Attack mapping; document remaining unknowns before patching. Reuse existing research, avoiding whole-ROM analysis.
4. **Construct reproducible patches:** build a **new isolated/versioned cumulative output**, never in place. Scripts must assert input SHA-256, expected original bytes, address interpretation, source ancestry, nonoverlap and output hashes; produce a changed-byte ledger for each feature and for the combined ROM. Preserve all source ROMs, previous experimental ROMs, saves, savestates and evidence. If essential mapping is unproved, leave that feature unpatched, report the exact blocker, and do not claim full completion.
5. **Independent offline verification:** replay manifest/ledger and read back all changed bytes; verify all 24 Kaizo thresholds and cap, six known Hawker branches and original tutorial, Detector/Rattlin' stats, Hanzo reward operand values, full per-level Attack table, all selected map music bytes and unchanged upper metadata bits, ROM header, and full-file unexpected-change scan. Run synthetic tests; provide changed-file list and protection audit.
6. **Manual gameplay acceptance, user-operated mGBA only:** prepare a concise ordered checklist and isolated save/test environments for the user to exercise each feature. Codex must **not** operate mGBA, issue debugger commands, change live RAM or load/save states on its own. Static PASS does not equal runtime success.
7. **Release package:** prepare patch/source/manifest/readme suitable for user-owned source-ROM application; **never distribute copyrighted ROMs or extracted sprites**. Label output **experimental** until manually validated.

## 6. Acceptance checklist for the cumulative ROM

- [ ] The five requested area music replacements are correctly scoped to all confirmed rooms, with overrides accounted for and no unrelated music changes.
- [ ] Hanzo 1 grants Dojo Pup and Hanzo 2 grants Erupter through normal story paths, with proper ownership and no progression regressions.
- [ ] Every relevant difficulty/level shows the pair's Attack values swapped; upgrade behavior and battle calculations are tested to the proven scope.
- [ ] Kaizo's 24 threshold progression ends at 100, original prerequisites/rewards/flags intact, 24/24 principal objective maintained.
- [ ] Every qualifying Hawker exchange gives 2 Binkies, gauge consumption/eligibility preserved; untested negative branches separately labeled until user tests.
- [ ] Detector = 120 HP / 25 base mitigation; Rattlin' Dragon unchanged 262 / 54; other enemies unchanged.
- [ ] English translation, ordinary maps/NPCs/doors, Oystown first-visit tutorial, existing events and save operations not regressed within tested scope.
- [ ] All original ROMs, historical experimental outputs, sprite exports, source scripts, evidence, saves and savestates untouched.
- [ ] New cumulative file and reproducible patch scripts, hashes, byte ledgers, independent tests and user-operated mGBA checklist delivered.

## 7. Opening instruction to Codex for next session

> **Tomato Adventure — Cumulative ROM Hack Assembly.** Sprite extraction is closed; I will classify sprite identities manually. Read `AGENTS.md`, `tomato_adventure_modding_plan.md`, the newest handoffs, and active ROM/patch/evidence files. Use the Detector cumulative experimental ROM (reported SHA-256 `124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`) as the *candidate* source only after verifying its identity, complete ancestry and whether test-only Alessa recruitment modifications should be retained. Prepare one reproducible, isolated cumulative English ROM hack implementing (1) Dropper Village→Pokypine Forest, Mayonen Caverns→Mayonen, Captain Grocko Ship→Namp Lagoon, Oyster Sewers→Oystown, Vault→Oops Mannor music; (2) Hanzo 1 Dojo Pup, Hanzo 2 Erupter, and swap both Gimmicks' displayed Attack values for every difficulty/level without swapping unrelated properties; (3) preserve Kaizo's validated 24 rewards and 180→100 thresholds; (4) preserve the established universal two-Binky Hawker exchange in existing locations, without adding new NPCs; and (5) preserve Detector HP 120/mitigation 25 and unchanged Rattlin' Dragon. First verify all missing map IDs, music IDs/overrides, Hanzo 2 reward operand and exact per-level Attack encodings. Do not guess. Produce feature-by-feature patch plan and exact ledger, then guarded isolated construction only for fully supported features. Independently verify complete output, run tests, audit protected artifacts, and provide a user-operated mGBA acceptance plan. Do not operate mGBA, modify live RAM or saves, touch protected originals, resume Hawker placement, or resume sprite extraction. Keep all results labeled static vs runtime.

## 8. Exact stopping state

- **Sprite extraction:** Closed by user decision, with manual visual classification to follow outside Codex.
- **Current playable sprite identities:** DeMille probable, others unnamed; not blockers to ROM build.
- **Most advanced cumulative ROM:** Detector experimental input above, pending fresh hash verification.
- **Kaizo:** principal 24/24 objective user-confirmed; preserve.
- **Two-Binky Hawker:** six successful character/story scenarios user-confirmed; preserve, regressions pending.
- **Detector:** 120/25 statically verified only.
- **Music:** Mayonen Caverns `0x001E` single-map proof exists separately; requested five-area music package not yet implemented.
- **Hanzo swap:** Hanzo 1→Dojo Pup tested separately; Hanzo 2→Erupter and per-level Attack inversion newly requested and not implemented.
- **Extra Hawker placements:** still paused, blocked, not included in current request.
- **Next objective:** independently verified and manually tested cumulative ROM release candidate, not new sprite extraction.
