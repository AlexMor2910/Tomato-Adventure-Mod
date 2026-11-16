# Tomato Adventure — Session Handoff 6

**Session date:** 2026-10-14  
**Status:** End-of-day handoff. Kaizo 100-Binky patch built and partly runtime validated; experimental direct-RAM Hanzo Gimmick fixture **failed and must be discarded**.  
**Authorization:** Documentation only. This handoff authorizes no ROM edits, emulator operation, RAM writes, savestate modifications, or commits.

## 1. Read first, preserve evidence, and keep responsibilities separate

Read `AGENTS.md`, Session Handoffs 1–5 (especially `session_handoffs/SESSION_HANDOFF_5.md` in the active workspace), the latest Kaizo proposal and experiment reports, and `tomato_adventure_modding_plan.md`. This file is the continuation of Session 5, not a replacement for prior technical documentation.

**The user alone operates mGBA and executes debugger commands.** Codex may do bounded, read-only static analysis and, only with explicit permission, isolated reproducible offline patch construction. Never autonomously operate mGBA, launch Ghidra, alter live RAM, overwrite source ROMs or checkpoints, or treat static tests as runtime validation. For interactive debugger guidance default to **one action and its expected observation per turn**. If the user requests batching, first verify that the exact baseline and all prerequisites hold; avoid blind multi-byte inventory editing after the failure in §7.

The original Japanese and English ROMs, earlier experiment ROMs, savestates, manifests, and scripts are protected. Use disposable branches and fresh filenames. Distinguish observed results from inferred causes. No ROMs or saves are attached to this handoff.

## 2. ROM identities and current outputs

| Artifact | SHA-256 | Notes |
|---|---|---|
| Japanese original | `0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12` | Protected |
| English translation baseline | `8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde` | Protected |
| Validated two-Binky + Alessa recruitment ROM | `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3` | 16 MiB; 118 changes relative to its recruitment source |
| **Kaizo 100-Binky experimental ROM** | **`7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`** | Built from the preceding ROM, 16 MiB, **exactly 51 changed bytes** |

Relevant workspace-relative paths:

- Validated predecessor: `tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`
- **Current experimental ROM:** `tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba`
- Kaizo patch script: `tools/patch/kaizo_binky_100.py`
- Synthetic tests: `tests/test_kaizo_binky_100.py`
- Proposal/ledger: `reverse_engineering/kaizo_binky_100_proposal.md`, `reverse_engineering/kaizo_binky_100_proposal.json`
- Output validation documents in the Kaizo output folder: `manifest.json`, `byte_differences.tsv`, `independent_verification.json`, `README.md`.

Codex reported 11 tests passing, including 18,100 donation arithmetic cases; full-file comparison of 16,777,216 bytes identified precisely the approved 51 differences; ROM header/checksum unchanged and 388 prior protected artifacts plus a separate 867-file documentation/data audit unchanged. **These are Codex-reported offline results, not independently reproduced here.**

### 2.1 Exact Kaizo change specification

The 24 original → new cumulative thresholds, in progression order:

`4→2, 7→4, 10→6, 13→7, 17→9, 21→12, 26→14, 31→17, 37→21, 43→24, 50→28, 57→32, 65→36, 73→41, 81→45, 90→50, 99→55, 109→61, 119→66, 130→72, 141→78, 153→85, 165→92, 180→100`.

These correspond respectively to UFO-Cast, Lucky Cat, Cyclooka, Rocket Pak, Kendama, Bouncer, Bee Gatling, Pyramet, Fart Horn, Origami, Popocon, BowlingRice, Bunny Hop, Shadowreel, SlotZooka, Flame Doll, TwinDragon, SesameTop, Judgment, Mansnow, Dragonfire, Momotaro, StarScope, and Choo-Choo.

Each reward has a displayed and a comparator 16-bit little-endian threshold; one changed low byte each = 48 changed bytes. Extra changes:

- File `0x000FC7A9` / bus `0x080FC7A9`: cap comparator `B4 00 → 64 00` (one byte actually changes).
- File `0x000FCCD8` / bus `0x080FCCD8`: cumulative clamp `B4 → 64`.
- File `0x0064FE13` / bus `0x0864FE13`: English dialogue `78 → 70`, “make 180 friends...” → “make 100 friends...”.

Kaizo's cumulative donated count is persistent variable `0x30` at RAM `0x030032B7`. The original whole-stack donation removal behavior was explicitly approved to remain: donating five when prior cumulative total is 99 reaches 100 but removes all five, leaving four surplus uncredited. **This is not an inventory-capacity change.** Claimed-gift flags `0x195–0x1AC`, prerequisites `0x22B`, `0x22C`, `0x22D`, `0x096`, reward IDs, recruitment wrapper, and two-Binky exchange implementation must remain unchanged. Legacy complete saves are not automatically migrated.

## 3. Universal two-Binky exchange milestone: completed but bounded

User-confirmed live successful exchange for **all six applicable character/story selections**: Alessa early/intermediate/late; Sofoubi early/late; Relleck applicable late. Each full AWE gauge awarded exactly two Binkies, consumed that gauge, and ended normally. This is not proof of arbitrary unsupported story stages. Remaining regressions include cancellation, insufficient charge, capacity refusal, multiple full gauges, and dedicated save/reload.

Relleck's independently inspected successful state `relleck_initialized_guarded_successful.ss0`: 26,683 bytes, SHA-256 `9de814b789f88989c1a4f0330ff024d4b0d81a7031e15d4c3c2c2bf55ec5ec9c`; state showed membership `F1`, `0xBA` set, `0x1C4` clear, Binkies 6, zero AWE charge/readiness, idle event interpreter, and matching character records. The exchange **delta** remains user-confirmed runtime evidence, not reconstructed solely from the saved snapshot.

Session 5 documents reportedly created: `reverse_engineering/experiments/binky_exchange_session5_closeout.md`, `reverse_engineering/experiments/binky_exchange_session5_evidence.json`, `session_handoffs/SESSION_HANDOFF_5.md`; consult active workspace copies.

## 4. Kaizo introduction: live success

Original checkpoint `before_kaizo_100_test.ss0` (workspace root), 42,200 bytes, SHA-256 `b1a3980b2802a10d63798209237072074edf67998450ad1a8c30ffaa9153b9bd`; embedded original two-Binky ROM CRC32 `AB34C118` (mGBA 0.10.5). Saved on map `0x0173`, membership `F1`, six carried Binkies, no cumulative donations or claims, introduction flag `0x1AD` clear. It was successfully trial-loaded into the new Kaizo ROM without reported warning.

Codex discovered Kaizo's introduction is a **floor trigger**, not Kaizo's speech script: map `0x0173` event table `0x0815B0C4`, trigger grid x=4–5/y=7 at `0x0815B0C8`, event `0x080FC0A4`, conditional on flag `0x1AD`. Kaizo conversation separately registers `0x080FC742` and can reach donations without setting introduction flag; therefore donations before introduction completion are unsafe for progression testing. Introduction script awards DeMille **A-B Glove** (item ID `0x10`), resets donation variable `0x30` to zero at `0x080FC6D1`, initializes threshold cache variable `0x31` at `0x030032B8` to original `4` at `0x080FC6D5`, and sets `0x1AD` at `0x080FC6D9`. The cache initializer remains 4 in the patch; subsequent donation processing computes current normalized thresholds, so **do not manually alter the cache**.

The user activated the floor trigger, observed mGBA breakpoint `0x0806AB56` registering `r0=0x080FC0A4` (and then continuation registrations), removed two breakpoints, let the cutscene finish, received A-B Glove without errors. Live checks then confirmed:

- `r/1 0x0300331C` = `0x20` — introduction flag `0x1AD` set.
- `r/1 0x030032B7` = `0x00` — cumulative donations zero.
- `r/1 0x030019DA` = `0x06` — six carried Binkies.

**Clean post-introduction, pre-donation state (PREFERRED FUTURE BASELINE):** `before_kaizo_first_donation.ss1`, 27,918 bytes, SHA-256 `67a177a6c8f8a37f424183a2d2777ec59b296381d27e8790e411a7dde40f73d6`, embedded Kaizo ROM CRC32 `0E525B4A`; map `0x0173`; membership `F1`; intro `0x1AD` set; donations 0; six Binkies; all Kaizo claim flags and all four Hanzo completion flags clear; no active interpreter. **The savestate opens with the Gimmick menu displayed on A-B Glove; close it normally before taking memory observations or making any proposed test modifications.** The savestate includes erased embedded 8 KiB savedata; Codex recommended loading disposable copies with `loadStateExtdata=9` to exclude embedded savedata restoration.

## 5. First donation — user-confirmed partial Kaizo runtime success

After the introduction, the user donated the six carried Binkies to Kaizo. **UFO-Cast (new threshold 2) and Lucky Cat (new threshold 4) were both awarded**; Cyclooka (threshold 6) was not awarded, consistent with Hanzo Lab 4 completion flag `0x22B` being clear. No post-donation checkpoint of this successful live test was found by Codex at that time. Do **not** claim all 24 rewards or final Choo-Choo/retirement have passed runtime testing. Actual new cumulative count and each claim flag after donation were not separately provided as debugger readbacks.

## 6. Hanzo prerequisites: four encounter completions, fourteen Gimmicks

The four Kaizo gates are **Hanzo encounter-group completion flags**, not simple item-ownership flags. A character owning Gimmicks does not itself set the associated completion flag.

| Flag | Encounter | Required normal reward Gimmicks |
|---|---|---|
| `0x22B` | Lab 4 | DeMille Chomper `03`; Alessa Spider Gun `21`; Sofoubi Sun Beam `23` |
| `0x22C` | Lab 5 | DeMille Tail Wag `11`; Alessa Fumigator `13`; Sofoubi Electric Eel `0B` |
| `0x22D` | Lab 6 | DeMille NanaBoard `27`; Alessa Cupid Bow `09`; Sofoubi Zap Drum `17`; Relleck Seed Bomb `0D` |
| `0x096` | Later Lab 1 | DeMille Shell Fist `05`; Alessa Love Song `2D`; Sofoubi Hotafant `2F`; Relleck Yokozuna `19` |

Original acquisition helper is `0x0806ADA0–0x0806AE28`: append three-byte entry (ID, difficulty, upgrade); increment recipient count; set two usage bytes; equip in first available slot. It does **not** set completion flags and has no duplicate protection. No replay-safe native acquisition carrier was established for the Kaizo setup. Codex modeled a *direct memory substitute* with 97 individual byte writes on the post-introduction checkpoint, but this has **not been validated at runtime** and the attempted manual implementation crashed (§7).

Codex's intended post-introduction inventory baseline was:

| Character | Count location | Original count | Expected theoretical count after all 14 |
|---|---|---:|---:|
| DeMille | `0x03001EE3` | `03` (IDs `01 1B 10`) | `07` |
| Alessa | `0x03001F43` | `01` (`2B`) | `05` |
| Sofoubi | `0x03001FA3` | `01` (`15`) | `05` |
| Relleck | `0x03002003` | `02` (`31 25`) | `04` |

Acquisition difficulty `0x0300196E=01`; flags at `0x0300332C` initially `00` (masks `08`, `10`, `20` for `22B`,`22C`,`22D`), and `0x030032F9` initially `00` (mask `40` for `096`). All these live baseline reads matched before writes.

**Critical A-B Glove change:** DeMille's third item is at `0x03001EEA–0x03001EEC = 10 01 00`, equipped at `0x03001F38=10`. Never use the earlier pre-introduction DeMille append addresses or overwrite this item. The post-introduction Chomper target is `0x03001EED`.

## 7. Failed direct-RAM inventory insertion — do not reuse branch

The user approved a test fixture; we began manually editing a disposable mGBA session derived from `before_kaizo_first_donation.ss1`. The following were user-reported executed or checked:

1. Original inventory counts `03 / 01 / 01 / 02`, acquisition difficulty `01`, Hanzo flag bytes `00/00` confirmed by live debugger.
2. Chomper DeMille: entry `0x03001EED–EF = 03 01 00`; usage `0x0200EF0C–0D = 07 07`; equip `0x03001F39=03`; count `0x03001EE3=04`. The item-ID `03` was specifically read back.
3. Spider Gun Alessa: entry `0x03001F47–49 = 21 01 00`; usage `0x0200EF48–49 = 07 07`; equip `0x03001F97=21`; count `0x03001F43=02`. User reported writes done.
4. Sun Beam Sofoubi: entry `0x03001FA7–A9 = 23 01 00`; usage `0x0200EF4C–4D = 07 07`; equip `0x03001FF7=23`; count `0x03001FA3=02`. User reported success.
5. Hanzo Lab 4 flag `0x0300332C` originally still `00` when initially checked, then explicitly written `08`; readback **confirmed `08`**.
6. At user request, an **unverified multi-group batch** of commands was supplied for Lab 5 (Tail Wag, Fumigator, Electric Eel), Lab 6 (NanaBoard, Cupid Bow, Zap Drum, Seed Bomb), and later Lab 1 (Shell Fist, Love Song, Hotafant, Yokozuna). **Do not assume all commands executed, or that the intended final flags and counts were achieved.** There were no individual readback results supplied for these later groups.
7. Upon returning to gameplay and opening **Sofoubi's Gimmick menu**, the game **crashed**. User observed that DeMille and Alessa's Gimmicks appeared fine, but Sofoubi had a missing entry after his initial Gimmick; user suspects **Electric Eel** was absent. This is an observation/suspicion, **not** a proven missing byte or root cause. The emulator was closed; no crashed-state RAM dump or diagnostic checkpoint exists.

Potential causes include skipped debugger commands, incomplete Sofoubi `0B 01 00` entry at `0x03001FAA–AC`, count/entry inconsistency, equipment/usage state, or the multi-command paste procedure. The precise cause is **unknown**. Do not assert inventory-count mismatch or missing Electric Eel as established. The user's later `r/4 0x03001FA7` inspection was suggested but **not executed** because the emulator was already closed.

**Critical operational lesson:** Do not trust pasted multi-line mGBA console commands without readbacks. Do not mass-edit 97 bytes again. Never resume with an incomplete Gimmick inventory. Discard any partially modified fixture; preserve original `before_kaizo_first_donation.ss1` and the successful Kaizo donation evidence. Do not reconstruct a damaged state by guessing fixes.

## 8. Exact safe next-session priorities

**Priority 1: Recover cleanly.** Launch the unchanged **Kaizo 100-Binky experimental ROM** and load a *disposable copy* of `before_kaizo_first_donation.ss1` with the recommended savedata-exclusion setting. Close the Gimmick menu normally. Confirm interpreter idle, preserved intro flag `0x1AD`, Binkies 6, donations 0, and baseline inventory counts before any edits. No new writes are authorized by this handoff.

**Priority 2: Investigate the crash read-only.** Ask Codex to audit the actual post-introduction Sofoubi memory layout, contiguous entries, usage/equipment addresses, index/count semantics, and the exact mGBA debugger's multi-command execution behavior. The intended Sofoubi entries were: `0x03001FA4=15 01 00` (Super Fan), `0x03001FA7=23 01 00` (Sun Beam), `0x03001FAA=0B 01 00` (Electric Eel), `0x03001FAD=17 01 00` (Zap Drum), `0x03001FB0=2F 01 00` (Hotafant). No proof the last three were successfully written. Prefer a reproducible, guarded, native-acquisition fixture if it can be separately proved safe; do not build a new ROM without authorization.

**Priority 3: Test Lab 4 / Cyclooka in isolation.** The quickest controlled follow-up is a fresh disposable copy of the preserved post-introduction checkpoint with **only three Hanzo Lab 4 Gimmicks** (Chomper, Spider Gun, Sun Beam), strict incremental readback, normal menu validation *before* enabling `0x22B`, completion flag readback, then a separate checkpoint prior to the six-Binky donation. This limits the exposed surface; do not proceed to Labs 5/6/1 in a single session until an earlier phase passes. The exact sequence should be reviewed again by Codex after the failure.

**Priority 4: Broader Kaizo runtime validation.** Eventually test newly normalized reward boundaries, story-gated gifts, claimed-flag replay protection, multiple rewards per donation, `99 + 5` full-stack removal/cap behavior, Choo-Choo at 100, retirement, capacity, and save/reload. The two-Binky exchange's pending negative-path regressions and early-area Hawker/NPC placement (Mayonen first screen map `0x0048`; Namp Lagoon likely second screen `0x0061`, to verify visually) remain separate objectives.

## 9. Safeguards, omissions, and important files

- Last reported Codex audit after post-introduction Hanzo fixture analysis: **401 protected artifacts unchanged**. No audit of the user's crashed live RAM is possible; that state was closed without preserved diagnostics.
- Session 6 did **not** request or approve any further patch construction, alteration of original ROMs, or placement of NPCs.
- **Avoid overwriting** `before_kaizo_100_test.ss0`, `before_kaizo_first_donation.ss1`, the successful Relleck checkpoint, or any previous rate-two or Kaizo ROM.
- The two Codex reports underlying §6–7 were pasted into this conversation and are available as the conversation's `Pasted text.txt` attachments; the verified per-entry table must be reconsulted rather than guessed if this experiment is later reauthorized.
- The separately created Session 5 file was not available among the local files used to compile this handoff. Session 5 details in this document come from the user-supplied Codex report and conversation history; inspect its actual active-workspace version next session.

**Stop point:** The game crashed while opening Sofoubi's Gimmick menu after a multi-group Hanzo fixture write attempt, and the user closed the emulator. **No current live test session should be treated as valid.** Restart next time from the protected post-introduction `.ss1` checkpoint, and prefer a minimal Lab 4-only test with guarded verification.
