# Translation Project Overview

## Scope and evidence

Phase 1 reconnaissance, 2026-10-09. Read `AGENTS.md`, `tomato_adventure_modding_plan.md`, the toolkit entry point, every included assembly file, project-owned inserter sources, build recipes, `notes/`, legacy hacking notes, and address-bearing text/pointer manifests. No build, assembler, inserter, dumper, or emulator was executed; no ROM was inspected or modified. This is a source map, not a verified disassembly of either existing ROM binary. Paths below are relative to `tomatotrans-1.1.1/`.

Confidence labels used throughout these documents:

- **Confirmed**: directly established source fact (a declaration, write destination, or implemented format). This does not confirm runtime correctness or the contents of a supplied ROM.
- **Probable**: purpose supported by executable source and comments, but not independently traced in-game.
- **Candidate**: plausible research lead or legacy interpretation requiring verification.
- **Unconfirmed**: unavailable address, unknown field, or unresolved placement.

See [memory_map.md](memory_map.md) for allocations and an exhaustive source address ledger; [symbols.md](symbols.md) for functions, structures, and research leads.

## Build pipeline (read only)

`i.bat:2` contains `armips tomatoadv.asm && a %1`. It assembles first and invokes the inserter only if assembly succeeds; it forwards one argument, commonly `--force`. It does **not** compile the C++ sources, create a BPS patch, or run validation. Commands resolve through the current directory/PATH, so the identity of `a.exe` and `armips.exe` needs recording before a future build.

`tomatoadv.asm:1-2` selects GBA mode and opens `ta.gba` as input and `test.gba` as output with bus base `0x08000000`. It includes `asm/addresses.inc`, then 30 `.asm` modules in source order, and closes the output. The input must be a compatible Japanese ROM; this pipeline is not intended to patch an already translated ROM. Re-running would recreate/modify `test.gba`; preserve all existing ROMs when designing a later build wrapper.

`inserter/Makefile` compiles six `.cpp` files into `../a` with `-O2 -std=c++11`; `Nmakefile` compiles the same files with MSVC into `..\a.exe`. However, `images.cpp` uses `std::size`, a C++17 library facility, while the GNU recipe requests C++11. Build compatibility and whether bundled executables match these sources remain untested. `dumper2.c` is legacy extraction tooling, uses C++ constructs despite its extension, and is absent from both build recipes.

## Assembly module responsibilities

| Included modules | What the translation changes |
| --- | --- |
| `addresses.inc` | Fixed ROM text allocations and scratch EWRAM aliases. |
| `bug_nocash.asm` | Two halfword/word store fixes intended to prevent a no$gba saving failure. |
| `fontmap.asm`, `vwf_8x8.asm` | Replace font data, repair variable-width drawing, width calculation, menu block rendering, and embedded name codes. |
| `battle_message.asm`, `battle_enemies.asm`, `battle_sleep.asm` | Extend battle messages; replace embedded enemy/attack names with pointer-plus-length records; rewrite status message routines that also update sleep/paralysis state. |
| `gimmick_text.asm`, `item_text.asm`, `mecha_text.asm` | Redirect names/descriptions to longer translated tables while retaining original non-text records. |
| `battle_menu.asm`, `battle_levelup.asm`, `battle_spoils.asm` | Battle labels, name rendering, reward/level-up text positioning. The internally named “Cool” label is translated as “AWE!”; this is not an AWE gain calculation. |
| `menu.asm`, `menu_gimmicks.asm`, `menu_friends.asm`, `shop_messages.asm`, `menu_items.asm`, `menu_equipment.asm` | Menu buffers, longer names, equipment descriptions, scroll rendering, and removal of a duplicate sprite load. |
| `dialog_item.asm`, `dialog_center.asm` | Format obtained item/Gimmick/clothing names and quantities; measure dialogue width. |
| `gimica_text.asm`, `gimica_tutorial.asm` | Card-game labels, descriptions, tutorial widths and timing. Gimica and Gimmicks are distinct systems. |
| `naming_screen.asm`, `name_long.asm`, `dialog_name.asm`, `saving_screen.asm` | English keyboards; seven-byte/five-tile names; character record name storage; dialogue/save-screen rendering. `name_long.asm` also bounds a main-script command index on Cream Mountain. |
| `title_screen.asm`, `map_text.asm`, `credits.asm`, `dialog_speed.asm` | Sprite/tile layouts, overworld labels, credits bytecode rendering, faster dialogue and beep timing. |

Several helpers and sprite records use `.autoregion`; reclaimed `.region` space is shared with later helpers. Their exact placement cannot be inferred from a containing region's start alone. An assembler listing/symbol export will be needed later. No `.asm` files outside the include chain were found, and no assembly module includes another assembly source; `fontmap.asm` embeds `fontdata.bin`.

## Inserter modification logic

`ta_insert.cpp:19-44` opens assembled `test.gba` in `rb+`, then runs main dialogue, menu directives, enemies, battle dialogue, Gimica tutorial, credits, and images in that order. The shared allocation cursor starts at file offset `0x0064B4EC`; its reporting boundary is `0x007F0000`. There is no enforced allocation ceiling in `InsertString` or the image allocator. Exact relocated destinations depend on string lengths, deduplication, image compression and alignment.

- `text.cpp:35-68`: zero-pad strings; deduplicate identical byte vectors, including in-place insertions. `--force` disables allocation deduplication and substitutes identifiers for untranslated text. It is a stress/debug mode, not a release workflow.
- `InsertMainScript`: message order indexes `pointers1.dat`; each row lists all pointer **locations** for one message. It encodes through `ta_table_eng.txt`, appends `FF 00`, and writes little-endian bus pointers. Message IDs identify dialogue, not executable event scripts or ROM addresses. `pointers2.dat` and `ta_misc_*` are not used by this inserter entry point.
- `InsertMenuStuff2`: implements all seven formats in `notes/MENUS.md`. Fixed blocks can move to the growing pool; dynamic pointers can overwrite text in place if it fits; `RESTRUCT` copies only text fields into predetermined translated layouts. Numeric directive parameters are hexadecimal, including counts and strides.
- `InsertEnemies`: original eight-byte names become `{ptr32, len8, 0, 0, 0}` inside otherwise retained enemy/attack records; names are capped at 24 bytes.
- `InsertBattleText`: retains suitable 16-byte original text or creates extended inline/pointer packets consumed by patched battle command `0x43`. Longer messages use a ten-byte packet with a text pointer; see `symbols.md`.
- Tutorial: 21 groups; 49-byte translated lines, with `0x1C` continuation/`0x7E` end markers. Relocates the pointer table only when it exceeds 56 entries.
- Credits: emits length-prefixed game-encoded text and control bytes; overwrites the original 2,216-byte allocation if it fits, otherwise relocates and updates its pointer.
- `images.cpp`: reads PNGs through bundled `stb_image.h`; constructs palettes, 8x8 tiles, tilemaps and 2x2 tile chips. Uses GBA LZ77 (`0x10`) or run-length (`0x30`) compression. Larger tilesets/chipsets move to four-byte-aligned pool space and known references are repointed. Chipmaps and ordinary tilemaps have separate in-place constraints. Palette edits are supported in some routines despite the README's broader warning about reusing palettes.

Source inventory checks found 3,031 English main-message IDs in contiguous order, matching the 3,031 physical rows of `pointers1.dat`. All 31 assembly includes resolve locally; the 30 assembly modules contain 72 named function declarations. Documentation references were checked against source file line counts. These checks establish source consistency, not binary or gameplay correctness.

## Source-level limitations for a future reproducible build

No ROM revision/hash gate, automatic BPS generation, comprehensive bounds check, or regression suite is present. Missing input assets and image failures can be reported without `main` returning failure; successful process exit is insufficient validation. Sources and executable versions must be checked before trusting reproduction.

Unmodified source anomalies to investigate separately: `rle.cpp` reconstructs the size with `(input[3] < 16)` rather than a left shift; its run encoder starts with a 130-byte run even when fewer matching bytes remain. `InsertIntroMaps` passes map ID `0x0070` for the `map01CC` chipset relocation. These are source observations, not demonstrated failures of the existing English ROM. No fixes were made.

## Modding leads and gaps

**Gimmicks:** original records at `0x0862C250`, stride `0x58`, with 50 translated entries. A real loader at `0x08065518` still copies original gameplay data to `0x03003F34`. Commented attack/battery/level fields are hypotheses; names and record indexing are stronger evidence. This is the clearest balance research entry point.

**AWE/Binkies/Kaizo:** AWE labels and relevant dialogue exist; exchange IDs `4A9`–`4BB` describe a full-gauge requirement and offers varying with friends. Kaizo IDs `0E6`, `0ED`–`0FA` describe Binky totals, next rewards and Hanzo prerequisites. Dialogue mentioning “180 friends” is not evidence of a threshold table or a Kaizo power maximum. Collection flags, gauge arithmetic and unlock conditions remain unmapped.

**Events/progression:** `MainScriptHandle2C`, legacy FD/FE script notes, script-flag reader `0x0806AE2C`, character records and save-loading code provide entry points. Hanzo sign maps are graphics evidence, not reward-event addresses. Dialogue and overworld names identify Mayonen text but do not establish a map group or unlock flag.

**Music:** dialogue beep caller `0x08065FC0` and RAM sound type `0x03003E8B` are leads. No song table, music assignment field, sound engine identity or instrument bank is established by this toolkit.

## Recommended next focused investigation

Perform a read-only Gimmick table/loader audit first: fingerprint the Japanese and existing translated ROMs, inspect the 50 original `0x58`-byte records, correlate the name indices in `symbols.md`, and disassemble the loader and its callers. Trace reads of candidate fields `+0x22`–`+0x39` before identifying power, difficulty, or Kaizo thresholds. Produce a record schema with observed values and cross-references; make no gameplay edits. This yields a bounded, evidence-backed model quickly. Follow with event cross-references from exchange/Kaizo dialogue pointer locations and a separate sound-dispatch investigation for map music.

## Source snapshot fingerprints

SHA-256 of selected source inputs read during this reconnaissance. These identify the inspected pipeline, not either ROM or bundled executable.

| Source | SHA-256 |
| --- | --- |
| `tomatoadv.asm` | `f395e291b0b5f7aceb160e6ba13eefc5b837bfa9151021f54c486d3a6066c129` |
| `i.bat` | `5869ebded2eec2886d40d49bae76aaf37d6b4b5dc07703f24ac4e19ed720c88e` |
| `asm/addresses.inc` | `91f0cc6a3f7aeaa4c3eccaea26185d12c040a2cc936c546915835226c426a0f6` |
| `inserter/ta_insert.cpp` | `b42d844bd877dea5fe5d570cf0bc9ef53730da8aedaa181b68d4e6c53ac5f563` |
| `inserter/text.cpp` | `33a161db52f0a55a9678fe220177bd75ad0214a5b92a399c660eec989b2b6772` |
| `inserter/images.cpp` | `e2c41ae0c6e6d6df66a48ca96c805e8aae4a7c02d8fed39344ae29d9966fbb65` |
| `pointers1.dat` | `4bd4fa8918c4d32aab8d427feeecd9febefccbdcc95f2c11cf84507ebc480d5e` |
