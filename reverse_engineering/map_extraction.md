# Field background extraction and directed room graph

2026-10-20. Read-only static extraction from the fingerprinted original Japanese
ROM. No emulator, debugger, Ghidra, ROM/save/RAM change, patch, or Git commit.

## Delivered scope

**471 of 494 maps have complete registered-background exports:** three separate
RGBA layers and one combined PNG each, **1,884 PNGs**. These reconstruct the
full field layout with the base palette and first uploaded graphics frames.
They omit actors, event-driven changes, animation playback, palette animation,
scrolling/effects and UI. They are **not runtime screenshots or a simulation of
every map state**. Static decoding and local PNG inspection do not establish
runtime validation.

**23 maps are unsupported**, because their referenced tiles are not supplied
by the decoded base tileset and first supplemental uploads. No partial or
guessed PNG was emitted for them. Exact first failing tile/layer appears in
`maps.csv` and the evidence JSON.

The graph contains **864 directed edges**: 830 ordinary exit rectangles,
17 overworld returns, 16 overworld arrivals, and one registered-prefix scripted
transfer. Script coverage is deliberately partial; 1,799 unsupported prefix
stops are documented. No reverse edge is invented.

All **74 original Binky identities and quantities** remain intact in v2.
The graph supplies new reachability evidence, but no stronger exclusive node
ownership proof. Existing statuses remain unchanged: **35 probable node
associations and 39 unassigned pickups**. No scripted reward candidate is promoted.

## Sources and reproducibility

Read `AGENTS.md`, the modding plan, existing map/overworld documentation,
`binky_location_extraction.md` and its JSON/CSV data. Reused known map/exit/
arrival findings and the existing Thumb inspector. The prior room-preview
decoder was consulted only for the map format; no placement research resumed.

Toolkit evidence:

- `inserter/images.cpp:LoadCompressedTileset`, `SaveTilemapAsChips`,
  `InsertIntroMaps`, and the existing Namp map edits establish resource pointer
  tables, the 15-bank palette convention, chips, and compressed graphics.
- `inserter/tiles.cpp:Tile::Load16`, `Chip::FromTilemap`, `Chipmap::EncodeMap`
  establish 4bpp nibble order, tile entries, TL/TR/BL/BR chips and row-major layouts.
- `inserter/lz77.cpp` and `rle.cpp` establish GBA compression families. This
  implementation uses strict bounds and the correct 24-bit header size; it does
  not copy the existing RL decoder's `input[3] < 16` size-expression typo.

Published source: `Tomato Adventure (Japan).gba`, 8 MiB, SHA-256
`0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12`.
The CLI also accepts the untouched English baseline SHA-256
`8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`.
English resource-pointer relocations are followed from the actual source;
translated images must not be assumed byte-identical to Japanese resources.
The published images use Japanese source graphics, including embedded signage.

All addresses below are ROM bus addresses unless called file offsets;
**file offset = bus − 08000000**. RAM/VRAM/register addresses have no ROM offset.
The JSON records native instruction addresses, file offsets, bytes, literal
values, input hashes, format fields, initial uploads and PNG hashes.

## Map record and resource selection

Map table bus `0862D3E4`, file `0062D3E4`, stride `1C`, count 494,
table indices `0000..01ED`. The field-map index identifies the room record;
the first halfword separately selects shared graphics resources.

| Offset | Width/encoding | Proven purpose and reader |
| --- | --- | --- |
| +00 | u16le | Resource-table index, `08033D3E`, `08034D4E` |
| +02 | u8 flags | Specific loader shifts observed; complete meaning unresolved |
| +03 | u8 | Width in 16-pixel cells, `08033D5A..62` |
| +04 | u8 | Height in 16-pixel cells, `08033D4E..56` |
| +05 | packed u8 | Low six music-selector bits, prior established knowledge; high two copied separately |
| +06 | u8 | Unresolved here; no invented rendering role |
| +07 | one-based u8, 0=none | Supplemental initial graphics/animation definition, `08034DA0` |
| +08 | u8 | Additional runtime definition at `083DDD44`, `08033E6A..78`; effects unexpanded |
| +09..0B | bytes | Unresolved |
| +0C | u32le bus pointer | This room's exit list, `08033CC6` |
| +10 | u32le bus pointer | Default/rectangle event table, `08033E22` |
| +14 | u32le bus pointer | Actor block, `08033E30`; registrations start +70 |
| +18 | u32le | Copied at `08033E66` to `03001B5C`; meaning unresolved |

The catalog's `width_tiles` and `height_tiles` use **8-pixel native tile units**,
twice the record's cell dimensions. It also retains cell dimensions explicitly.
`tileset_id` and `palette_id` are resource-table indices; there is no separately
proved independent palette-selector field.

**Correction to earlier documentation:** bytes after file `006309EC` are not
merely padding. They form a per-field-map priority table. The earlier Binky
extractor's observed initial `39` bytes were real values in this table. Its
494-map census remains valid; existing evidence was preserved unchanged.

## Layout, graphics and palette formats

Let `g=u16(record+00)`, and layer `k=0,1,2` correspond to BG1/BG2/BG3:

| Table bus | Indexing | Data format / evidence |
| --- | --- | --- |
| `0815BA3C` | +4*g | Tileset bus pointer, native `08034D52..58` |
| `0815B84C` | +g | Raw-copy block count, byte*512, `08034D90..98` |
| `08255F00` | +4*g | Base palette bus pointer, `08033D42..4A`; 240 RGB555 entries from toolkit convention |
| `0826E358` | +12*g+4*k | Layout pointer, `08033DAA..CA` |
| `0831E7B4` | +12*g+4*k | Chipset pointer, `08033DCC..E4` |
| `08303950` | +4*g | Collision byte-array pointer, `08033DEC..F4` |
| `086309EC` | +field_map_id | Three two-bit BG priorities, `08033C98..B4` |

The graphics, palette, layout and collision tables are selected by **g**, not
blindly by field-map ID. Exit/event/actor pointers remain room-record fields.
Adjacent room IDs imply neither resource sharing nor shared node ownership.

Each layout is an uncompressed row-major `width_cells*height_cells` array of
u16 chip indices. Each chipset entry is 8 bytes: four native tile halfwords in
**top-left, top-right, bottom-left, bottom-right** order. Native chip expansion
`08034C88..D6` reads each index, multiplies by 8 and copies those halfwords.
Null layout pointers represent absent layers, consistent with `08034AEC`.

Native tile entry:

```text
bits 0..9  = 8x8 tile number
bit 10     = horizontal flip
bit 11     = vertical flip
bits 12..15 = palette bank
```

Tiles contain 32 bytes, row-major 4bpp, low nibble first. Pixel color index zero
is transparent in each layer. Other pixels select `bank*16+index` in the RGB555
palette; 5-bit channels expand by `(v<<3)|(v>>2)`. An opaque reference outside
the loaded 15-bank base palette is rejected rather than guessed.

Native `08034D48..9A` loads the base tileset at **VRAM 06008000**. Header 10
uses GBA LZ77, header 30 uses GBA RL. Both carry a 24-bit little-endian output
size. Header 00 copies raw bytes after its four-byte header using the native
512-byte block-count table. Other header values remain unsupported.

The new decoder rejects truncated input, invalid backward distances, output
overrun tokens, non-whole tiles, oversized advertised output and bad pointers.
Tileset output is capped at 32 KiB; image allocation at 4,194,304 pixels.
It never allocates directly from an unchecked compression size.

### Reserved tile and initial supplemental graphics

Full field setup requires zero at `030030E6` on its initialization path
(`08031AAA..B0`). It passes that zero to a BIOS fixed fill of eight words at
`0600FFE0` (`08031AFC..08031B04`). Thus tile 1023 relative to char base
`06008000` begins transparent. A base or supplemental upload that actually
writes that tile overrides it. No other out-of-range tile is assumed blank.

For nonzero record+07, table `0813D1EC + 4*(selector-1)` selects a definition.
Native `08034DF0..08034E8E` establishes variable-size records:

```text
+0   control byte; FF terminates the list
+1   0 selects BG VRAM 06000000; nonzero selects OBJ VRAM 06010000
+2   u16 destination tile offset relative to that VRAM base
+4   u8 count of additional frame pointers
+5   u8 tile count minus 1
+6   u32 first raw graphics-frame pointer
+10  additional frame pointers (4 bytes each)
```

Each initial upload copies `(byte5+1)*32` bytes. For BG uploads, renderer byte
offset relative to its char block is `u16(+2)*32-8000h`. The extractor copies
the first raw frame, checks all bounds, skips later frame pointers, and does not
export OBJ resources. Native CPUFastSet control is a word count of eight per
tile. Definition traversal is capped at 128 records.

This supplies tiles 768 onward used by the representative maps. The former
preview's silent omissions are not repeated. Later frames and event-selected
graphics remain outside this static background profile.

### Composition and collision limits

Priority comes from field-map table byte `086309EC+map_id`: bits 1:0 for BG1,
3:2 for BG2, 5:4 for BG3. Native `08034F58..94` puts these into BG control
registers. Lower priority values draw in front; BG1 wins a tie with BG2/BG3.
The combined PNG draws back to front over palette color zero. Individual PNGs
retain transparent pixels. BG0 UI, actors, blending, scrolling, palette animation
and event overrides are excluded. Additional record+08 runtime definitions are
documented without pretending to simulate their effects.

Collision is one unsigned byte per 16-pixel cell: `08034AB0..DA` copies exactly
width*height bytes into `02001E08`. Exits and events subsequently overlay their
own metadata. The bit meanings and full movement/collision rules are unresolved;
the tool exports its pointer, not a guessed walkability visualization.

## Representative preflight and catalog extension

Before the all-map pass, the same decoder strictly rendered:

| Field map | Cells | PNG dimensions | Initial BG supplemental uploads |
| --- | --- | --- | --- |
| 004D, Mayonen | 20×10 | 320×160 | 4 |
| 005F, Namp Lagoon | 33×10 | 528×160 | 1 |
| 0104, Oystown | 22×10 | 352×160 | 0 |
| 0173, laboratory example | 15×10 | 240×160 | 2 |

All use the common format. Local Mayonen/Namp combined PNGs were inspected
for coherence; this was not a game execution or new runtime comparison.
The all-map pass then accepted 471 and rejected 23. Native field-reader
evidence, toolkit encoding and automated pixel examples are the basis for
format confidence, rather than appearance alone.

Unsupported IDs: 001F, 0020, 0021, 0022, 0023, 0024, 0025, 0027, 0028,
002A, 002B, 0043, 0044, 0045, 006B, 006C, 00DE, 0171, 0175, 0176, 0178,
017C, 019B. The smallest next dependency is the additional writer/load source
for each recorded missing tile; they may require event/animation/context
initialization. No wider search or guessed zero filling was undertaken.

## Directed transition extraction

The prior Binky JSON's 847 registered exit records are checked byte-for-byte
against this ROM. Every record produces exactly one directed edge. Source
coordinates are inclusive rectangles `[byte0..byte2] × [byte1..byte3]`.
Destination `u16(+4)` is a field-map ID unless bit 15 selects overworld.

Native `08069AA6..08069B18` establishes normal destination X=`byte7&7F`,
Y=`byte8&7F`; byte6 is a separate entry parameter, and byte9 supplies subcell
nibbles. The CSV intentionally does not label those omitted values as integer
coordinates. Door versus edge-of-map appearance remains unresolved, so the
supported type is `ordinary_exit_rectangle`, not an invented door classification.
Blank `required_flag` means no flag established here, not proof of unrestricted
playability. Ordinary transition engine activity gates still exist.

For overworld returns, native `08069A2A..54` computes
`node=(destination&FF)-1`. Each of 16 real arrival scripts begins FE7C/FE7D
with a u16 map destination and X/Y bytes; native `0802A0A0` / `0802A134`
consume them. Node 0F selects an immediate return and has no arrival edge.

Script transfers are discovered only from actual map defaults, 8-byte rectangle
events, and ordinary actor interaction pointers. A narrow interpreter follows
FD30 jumps, FD35/FD3B flag branches and returns, and accepts FE7C/FE7D transfers.
It stops at every other operation, dynamic construction, or a 128-command root
budget. It does not scan every ROM byte for transfer-looking patterns.
The retained additional edge is **005E → 005D**, command bus **081166D6**,
destination `(1,1)`, directly at its registered script root. Its existence is
Confirmed static; actual event availability still depends on game state.

All 1,799 stopping records are in JSON `script_prefix_stops`, with source room,
root, stop address/opcode or budget reason. These are unresolved dependencies,
not extra traversable edges. Full conditional transfers, calls, teleports and
story-dependent area connections remain incomplete.

## Node associations and Binky v2

The graph preserves direction. Breadth-first traversal starts separately from
each known overworld arrival and records minimum distance and all observed
node reachability. Conditional paths, if decoded, would be potential paths,
not a proof of simultaneous reachability.

`map_node_assignments.csv` gives a node only for an observed direct arrival or
return association with no observed competing node. Other maps retain candidates
and distances but no inferred owner. Even a direct relationship does not prove
exclusive ownership. Current classifications: 16 direct associations,
55 reachability-only Candidate rows, 423 Unresolved rows. No observed multi-node
reachability was found in this **partial graph**; missing script edges can still
conceal shared rooms. Numerical map adjacency is never used.

For Binkies, prior probable assignments are preserved when no stronger evidence
exists. Mere new reachability never promotes an unassigned pickup. The v2 rows
add graph candidates/distances, change status and evidence references; no node
assignment changed in this bounded pass. Both prior IDs and quantities match
exactly, collection flags are not counted twice, and all subtotals sum to 74.
Complete node quantities remain blank. The seven earlier reward candidates
remain unresolved and excluded. No earlier Binky file or evidence was edited.

## Outputs, safety and tests

- `tools/extract/extracted_data/maps.csv`: 494 map records and render status.
- `map_transitions.csv`: 864 supported directed edges.
- `map_node_assignments.csv`: direct associations, candidates and distances.
- `binky_map_nodes_v2.csv`: 74 preserved pickups with graph evidence.
- `binkies_per_node_v2.csv`: partial subtotals plus explicit unassigned pool.
- `reverse_engineering/map_extraction_evidence.json`: format and static evidence.
- `tools/extract/extract_field_maps.py`, `tests/test_extract_field_maps.py`.
- Local PNG directory: `reverse_engineering/exports/field_maps_v1/`, containing
  `map_004D.png`, `map_004D_layer1.png` through layer3, and stable equivalents
  for each supported map. Its `.gitignore` excludes all generated graphics.
  These are personal-analysis artifacts, not distributable repository assets.

Run from workspace root with **new destinations**:

```powershell
python -B tools/extract/extract_field_maps.py --rom "Tomato Adventure (Japan).gba" --menus tomatotrans-1.1.1/ta_menus_eng.txt --binky-evidence reverse_engineering/binky_location_extraction_evidence.json --binky-locations tools/extract/extracted_data/binky_locations.csv --output-dir NEW_CSV_DIR --image-dir NEW_PNG_DIR --evidence-output NEW_EVIDENCE.json --all
python -B -m unittest discover -s tests -p test_extract_field_maps.py
```

Without `--all`, only the four preflight maps are rendered while the full catalog
and bounded graph are still written. With `--all`, the four-map preflight must
pass before extending to the rest. New files are opened exclusively and all
destinations are checked before rendering. Inputs are hashed before and after.
The tool is standard-library Python plus reused local extraction/Thumb helpers.

PNG uses RGBA8, filter zero, fixed zlib level 9, no timestamps. Evidence includes
the zlib version and output hashes. Tests cover known RGB555 and nibble examples,
H/V flips, transparency, palette banking, synthetic four-tile layouts, priority
and tie composition, valid/malformed compressed streams, directed/shared-map
reachability, no reachability-only ownership promotion, Binky aggregation,
representative PNG reproduction, every emitted PNG hash, catalog consistency,
baseline identity, fresh CLI reproduction and overwrite refusal. **All 9 tests
passed.** Input hashes remained unchanged.

No runtime verification is claimed. This task ends with the static renderer,
catalog, graph, v2 subtotals and documented blockers.
