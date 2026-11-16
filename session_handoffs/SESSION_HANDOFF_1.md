# Tomato Adventure Session Handoff

Session ended 2026-10-11. Stop here: no further development, ROM edits, experiments or commits are authorized by this handoff.

## Current status

Phase 1 mapping continues, with one explicitly authorized, controlled gameplay proof of concept completed. The independent CSV Gimmick patcher is implemented and verified. Gear-Yo 21→22 is the only included balance change; it is an experiment, not a finalized release decision. Translation ASM/C++ and protected source ROMs remain unchanged. Music, AWE, progression and other systems have not been modified.

Read `AGENTS.md` and `tomato_adventure_modding_plan.md` before resuming. Newer evidence sections supersede older historical “unconfirmed” statements in research documents; do not generalize tested Gear-Yo behavior to every record.

## Verified discoveries and experiments

- Original Gimmick table: file `0x0062C250`, bus `0x0862C250`, stride `0x58`, documented 50 records. Runtime IDs 1..50 correspond to zero-based indices 0..49. Gear-Yo is ID 1/index 0; base byte is +0x22, file `0x0062C272`.
- Menu routine `0x08075970` is Thumb and writes a caller-supplied structure, not a scalar return. Gear-Yo difficulty 1/upgrade 0: base 21 and coefficient 124 produce `floor(21*124/100)=26`. User confirmed r0=26 at `0x08075ABC` and stored output `0x02014D02=26`.
- Battle routine `0x080485B0` recomputes from original record/action inputs and writes scratch `0x03000BF8`. At `0x08048794`, user measured r1=26, r0=10; subtraction yields 16. At `0x08048796`, scratch store of 16 was confirmed.
- Caller `0x08046D60`, BL at `0x08046DE6`, applies scratch damage. User confirmed `0x08046E02` stores target HP at `0x03000A4E` (target `0x03000A40` +0x0E): HP 24→8, exactly 16 damage.
- Subtraction quantity comes statically from target +0x14/+0x18, bounded to 1..999. Do not label it Defense: individual live source values and gameplay meanings are unresolved. Static writers and optional 80%/70%, minimum and suppression branches are documented. No RNG source is established.
- Read watchpoint on `0x03003F9D` produced no hit in the reported replay. BIOS stop `0x00000188` was not a watchpoint hit. Battle reads the coefficient from ROM; the copied coefficient has a display reader.
- Controlled A/B, user-confirmed in mGBA: original Gear-Yo base/displayed Attack 21/26 and damage 16; experimental 22/27 and damage 17. Exactly one byte changed, `0x15→0x16`. No new experimental HP/register transcript was supplied with that final A/B report.

Sources: [runtime tests](reverse_engineering/gimmick_runtime_tests.md), [battle arithmetic](reverse_engineering/battle_damage_candidates.md), [Gear-Yo experiment](reverse_engineering/experiments/gearyo_attack_22.md), [ROM verification](reverse_engineering/rom_verification.md), [symbols](reverse_engineering/symbols.md).

## Protected fingerprints

| ROM | SHA-256 |
| --- | --- |
| Japanese | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` |
| English baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` |
| Gear-Yo experimental | `5cd1cc5c70dce892476d5162d49e0e1552600d37087181f79d0cc4e3d8120a8f` |

Original experiment: `reverse_engineering/experiments/testing/gearyo-281d1d7030904d5684c2ff29d3e90c1b/`, separate A/B directories. Generalized output: `tools/patch/output/gearyo-reference-validation/balanced.gba` and manifest. These are local ignored artifacts, not distributable repository content.

## CSV patcher commands and results

```powershell
python tools/patch/gimmick_balance.py --dry-run
python tools/patch/gimmick_balance.py --apply
python -m unittest discover -s tests -p test_gimmick_balance.py
```

Commands are for a future authorized session; none were rerun for this closeout. Prior results: **10 synthetic tests passed**. Applying `data/gimmick_balance.csv` reproduced the existing experimental ROM byte-for-byte and matched its SHA-256; exactly one offset differs. No inconsistency was found. See [usage](tools/patch/README.md) and [dry-run report](reverse_engineering/experiments/gimmick_balance_dry_run.md).

Default mode is dry run, creating no files. Apply requires the original English fingerprint and writes a fresh ignored directory. Optional `--output-name NAME` refuses an existing directory. The tool checks all expected bytes, ID/name pairs, field allowlist, ranges, duplicate/conflicting changes, full-file differences and output readback. Manifests record source/CSV/output hashes, exact entries and verification. Only one-byte `base_attack` +0x22 is supported. IDs 1..50 are supported structurally; only Gear-Yo's tested conditions are runtime-validated. Patched inputs are rejected, so experiments do not silently stack. Output safety checks are not proof of gameplay safety. No emulator session is launched by this patcher.

## Debugging workflow and checkpoint cautions

Ghidra 12.1.4/JDK 23 workflow: raw ROM at `0x08000000`, `ARM:LE:32:v4t`, bounded Thumb seeds, `-noanalysis -readOnly`. Scripts are under `tools/analyze/ghidra/`; project/log/cache files remain ignored. Do not run whole-ROM auto-analysis by default.

mGBA 0.10.5 debugging is manual; GDB connectivity was not established. Original checkpoints are in `reverse_engineering/mgba/run-6d783e19ca1b/`; protected branch is `run-8583a5fb3db2/`. Source menu state SHA-256: `570e17c82b6d3592a0b003d991a33b6bf320c04ff7322a339e735f6c65280230`; battle: `cd21cb39ce11ac7ab032982576e1bed13ab2864fa431e855a6bb209c125667c7`. Preserve them and existing saves.

Experimental ROM CRC differs. State loading restores old RAM caches; refresh menus and verify actual calculation stops. Use isolated save/state directories and disable embedded savedata writeback as documented. Never edit RAM/state headers to force expected results. The manual launcher now uses unique filenames and can safely relaunch a session without replacing logs.

## Git status, exclusions and suggested commits

`git status --short` and `git rev-parse --show-toplevel` both returned “not a git repository.” No root `.git` exists in this workspace. Therefore there is no index/history against which to identify uncommitted changes, and no claim that files were checked out, staged or already tracked. No repository was initialized and no commits were made.

Ignore-policy audit: root `.gitignore` excludes `/Ghidra/`, `/mGBA/`, `*.gba`, `*.sav`, all numbered `*.ss[0-9]*` states and Python caches. Whole Ghidra and mGBA session directories are excluded by their nested ignore files, retaining only `.gitignore`; experiment `/testing/` and patcher `/output/` are excluded. Closeout broadened the former slot-0/1-only state rule and added cache exclusions. Existing generated state/ROM/executable paths are covered by these rules. An indexed-file audit cannot be performed until a Git repository exists; ignore rules do not untrack already indexed files in a future repository. Review extracted copyrighted assets before publishing any translation-toolkit baseline; do not blindly add the entire workspace.

After Git initialization/restoration is separately authorized, organize candidate source/documentation changes as follows (review exact file lists; no commits now):

1. **Repository setup and mapping:** `AGENTS.md`, plan, root/nested ignore policies and translation/memory/ROM verification documentation. Establish provenance for existing translation sources separately; do not treat them as newly authored work.
2. **Bounded Ghidra analysis:** `tools/analyze/ghidra/`, read-only verification helpers, symbols/Gimmick calculation and battle reports. Exclude generated project trees.
3. **Manual runtime workflow:** `tools/analyze/mgba/`, setup/runtime reports, capture template and unique-log launcher fix. Exclude all sessions, saves and states.
4. **Gear-Yo proof of concept:** `tools/experiments/gearyo_attack_22.py` and experiment report. Exclude experimental ROMs and session outputs.
5. **CSV balancing infrastructure:** `data/gimmick_balance.csv`, `tools/patch/gimmick_balance.py`, README/ignore file, `tests/test_gimmick_balance.py`, test ignore file and dry-run report.
6. **Session handoff:** this file, reflecting final reviewed state.

Use concise imperative commit subjects and record validation/evidence scope. Stage explicit paths, then inspect `git status`, `git diff --cached --stat`, `git ls-files` and `git check-ignore` for artifact paths before any approved commit.

## Recommended next objective and milestones

Continue **plan §7, Gimmick Balance Changes**, beginning with a broader baseline characterization rather than another speculative stat edit. This best uses the validated patching infrastructure. Pick one documented candidate Gimmick and record menu/damage at multiple difficulties and minimum/average/perfect performance, then justify one proposed change. No candidate or value has been selected yet.

Milestones for the next authorized session:

1. Expand Gear-Yo regression coverage across difficulty, upgrade and fresh battle entry, retaining separate captures and checking conditional modifiers.
2. Resolve the target subtraction fields and battle action-selector/additive writers where needed to interpret results; investigate RNG only when an actual source enters the path.
3. Characterize one additional Gimmick and propose an evidence-backed CSV row for review; test it individually before combining balance changes.
4. Add another patchable field only after verifying its encoding/consumers and adding field-specific tests. Keep music/AWE/progression work separate. Hanzo reward mapping is a later complementary objective once candidate Gimmick behavior is understood.

No additional development began during closeout. Remaining objectives are recommendations, not work already authorized or completed.
