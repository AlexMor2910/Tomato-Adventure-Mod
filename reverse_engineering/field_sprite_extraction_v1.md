# Field NPC and playable-character sprite extraction v1

2026-10-27. Read-only static extraction from fingerprinted original Japanese and English baseline ROMs. Enemy v6 is preserved as a closed baseline; no multipart-enemy, Hawker, gameplay, Gimmick, portrait or interface investigation was performed. No emulator, ROM writer or Ghidra was used.

## Outcome and honest scope

**4,390 native transparent PNGs** from **522 observed descriptor/palette bindings**, plus 22 zero/disabled-object metadata rows with no invented canvas/PNG. Census: **494 map records, 2,987 registered actor records, 371 distinct loaded field graphics descriptors**. Of these descriptors, **332 support scoped referenced frames, 29 retain partial sequence/frame limitations, and 10 have no proven initial actor palette binding**. The registered non-player actor subset references **359 resources and 518 palette bindings**. These include field props, doors and pickups as well as people; all are cataloged as field actor resources, not all asserted to be named NPCs.

Canonical exports are `exports/field_sprites_v1/final_verified/`. The earlier `final/` discovery run is retained unchanged; its PNGs match the verified run, but its player-role name grouping is superseded by the narrower verified coverage. `resources.csv/json` catalogs all 371 resources; `frames.csv/json` supplies all 4,412 frame/palette rows and map/actor references; `animations.json` retains sequence order and raw thresholds; `actors.json` covers every registration; `unsupported.csv` covers all 39 partial or palette-unbound resources. Native frames are authoritative. Twelve 3x resource-role contact sheets are secondary previews in `previews/`, with exact cell/frame correspondence in sheets.json.

**Named playable-character work remains incomplete.** The default fallback player resource is exported; DeMille association is Probable rather than a newly proven name-to-graphics ID chain. Alessa, Sofoubi and Relleck are not assigned guessed resources. Anonymous field resources likely include story/cast variants, but that is not counted as named-character coverage. No complete animation or four-character extraction claim is made.

## Field graphics architecture

All addresses in the following explanation are original-ROM file offsets unless prefixed as bus/RAM. Bus = file + 08000000. Used field tile, palette, descriptor, animation and map/actor spans are byte-identical at the same offsets in the supplied Japanese and English baselines; these assets were not relocated by the translation. Per-resource exact ranges and SHA-256 values are in final_verified/evidence.json; discovery_evidence.json records map headers/actors. Native instruction windows are retained in field_sprite_extraction_v1_evidence.json.

Map table file 0062D3E4 has 494 records, stride 1C. Record +14 points at an actor/graphics block. Its first 70 bytes contain 16 u32 graphics-resource pointers at +00..3F and 12 palette pointers at +40..6F. Registered actor records start at +70, stride 10; first-byte FF terminates, at most 15 records. The loader copies this header and actors into RAM. If the first graphics pointer is zero, it selects fallback header file 00140180 for graphics/palette tables; the original actor-registration census is retained and effective-header provenance is explicit.

An actor selects graphics slot `(record[1]&1F)` (all observed values 0..15) and palette slot `record[2]>>4` (supported range 0..11). The low nibble of record[2] is a facing/sequence selector; it is passed through the lookup at file 00631920. The header-selected descriptor pointer binds actor state at RAM 03001BDC + slot*30. The descriptor is 10 bytes hex:

| Descriptor offset | Interpretation | Evidence / confidence |
|---|---|---|
| +00/+01 | Copied to actor geometry bytes +07/+08; not used as sprite image width/height | 080345E2..080345F8; Confirmed copy, precise geometry semantics unconfirmed |
| +02 | Retained raw, not assigned a meaning | No necessary consumer proved; Unconfirmed |
| +03 | Raw upload length in 32-byte tiles | 080340E2..080340F8; Confirmed |
| +04 u32 | Raw tile-data pointer | 080340F0..080340F8; Confirmed |
| +08 u32 | Animation sequence-pointer table | 08034608..0803460C and sequence setter; Confirmed |
| +0C u32 | OBJ frame-descriptor pointer table | 08034616..0803461C and sequence setter; Confirmed |

Tile upload uses CpuFastSet with exactly descriptor[3]*32 source bytes into sequential OBJ VRAM allocation beginning 06010000. No compression header is consumed on this traced field path. It is deliberately not fed into the enemy LZ77/RLE decoder. The established strict field-map decompressor remains available unchanged for genuinely compressed formats, but no speculative decompression fallback is used.

Field DISPCNT is set to **1E40** at bus 08034F96..08034FA0; bit 6 enables **1D OBJ mapping**. For each OBJ rectangle, tile rows advance by that rectangle's width in tiles, not enemy-style 32-tile VRAM pitch. Tiles are standard 8x8, 32-byte 4bpp; low nibble first. The exporter reuses extract_field_maps.tile_pixels, rgba555, take and png. Raw palette entries are 16 BGR555 halfwords, alpha zero for palette index zero.

An OBJ frame is u16 count followed by count six-byte attr0/attr1/attr2 entries. Shape/size fields determine rectangle dimensions, signed coordinates determine placement, and H/V flip bits apply to the entire rectangle. Sprite canvas is the explicit union of active rectangle bounds, not a nontransparent-pixel trim. Disabled non-affine objects contribute no visible rectangle; zero/disabled-only frames retain null dimensions and no PNG. Affine, alternate OBJ mode, mosaic, 8bpp and reserved shape are rejected. Runtime affine effects are present in the native draw helper but are outside this base-profile decoder.

Unlike the enemy palette-bank selection path, the field draw helper at bus 08033484..080334A8 adds a per-resource tile base and **replaces the OBJ palette bank with the actor-selected bank**. The raw bank bits in the descriptor do not prove a different per-part palette. The exporter normalizes the tile base and renders with that actor palette. Native priorities and descriptor order govern overlapping parts; lower numeric priority wins, then earlier OAM index. Screen translation, camera scrolling, battle effects, temporary recoloring, external occlusion and affine runtime state are excluded.

## Animations, facing and playable coverage

Each sequence-table entry is a pointer to ordered four-byte steps `(u16 frame_index, u16 threshold)` with FFFF as a two-byte terminator. Frame index selects `descriptor.+0C[frame_index]`. The initializer selects the first frame; the generic updater compares an actor counter against the current threshold, advances by four and wraps the sequence after FFFF. Raw zero thresholds are retained; their complete transition behavior is not invented.

No explicit sequence-count field was proven. The implemented bounded structural convention uses the packed pointer prefix ending at the first script pointer: `(first_script - table)/4`, integral in 1..64. Every selected pointer/step/OBJ/tile span is checked. This extent is **Probable**, not a promise of universal/full enumeration. Invalid frame pointers, tile overreach, excessive counts and empty sequences are retained as partial/unsupported conditions. Valid referenced frames remain exportable independently; a partial sequence is not silently promoted to a verified complete animation.

The facing lookup is confirmed numerically: selectors 1,2,4,8 choose sequence indices 1,3,0,2. These mappings are preserved in animations.json, with actor references carrying their initial selector and step associations. Cardinal direction names and which complete runtime states mean idle/walking have not been proven here. No animation timing in seconds or guessed pose names is emitted. The default resource's first sequence is exactly (0,10),(1,8),(0,10),(2,8), not a guessed frame order.

| Character | Field coverage | Remaining dependency |
|---|---|---|
| DeMille | Default fallback resource R_0013E58C: 14 referenced base frames, five sequences; 16x24 standard frames | Slot-0/default-header binding Confirmed; named identity Probable. Full idle/walk transitions and cardinal labels unresolved |
| Alessa | No named resource assignment claimed | Need an independent name/character-ID -> field actor/descriptor chain; not inferred from descriptor order or recruitment-room presence |
| Sofoubi | No named resource assignment claimed | Same exact identity-binding dependency |
| Relleck | No named resource assignment claimed | Same exact identity-binding dependency |

Seven distinct resources occupy the field-player slot across maps, listed in player_slot_resources.json. Slot 0 is a role, not evidence all variants depict DeMille or any other specific character. Each role/resource palette variant is exported anonymously. The map 001E recruitment context alone is insufficient to label an arbitrary descriptor Alessa, and no such assignment was made.

Field graphics are distinct from battle character graphics. This pipeline derives resources from map-header actor bindings and the field renderer, not battle participant records or enemy tables. Existing battle documentation establishes a separate participant structure; its graphics pointer chains and format were not imported or generalized. Battle character extraction is not included.

## Shared resources and unsupported cases

Sharing is recorded by raw tile source and palette pointer identities. shared_graphics.json groups tile-source pointers; descriptors with the same source can have different upload lengths/animations, so source sharing is not a whole-sprite or NPC-name alias. All observed descriptor/palette combinations are exported separately. Resource/variant IDs encode their actual file addresses, making filenames deterministic without manual NPC offsets.

Four registered actor bindings have null selected graphics pointers: map0013 actor9 and map0029 actors5/6/7. Their full records and reasons are in unbound_actors.json. Initializer/script resource replacement, activation conditions and dynamic actors are not reconstructed.

### Partial resources

Each row preserves exact per-frame and per-sequence failures in resources.json / animations.json. These are decoder/structure rejections, not claims that the original game is broken. Possible unmodeled script controls, unused sequences or external tile allocation remain unconfirmed.

| Resource | Rejected frame indices | Other limitation |
|---|---|---|
| R_0013E60C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E65C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E66C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E6BC | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E6CC | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E84C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013E86C | 14 | One or more referenced frames rejected; exact reasons retained |
| R_0013E88C | 14 | One or more referenced frames rejected; exact reasons retained |
| R_0013E8CC | 14 | One or more referenced frames rejected; exact reasons retained |
| R_0013E92C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013EB7C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013EC5C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013EC6C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013F03C | 1,2,3,4,5,6,7,8,9,10,11,12,13 | One or more referenced frames rejected; exact reasons retained |
| R_0013F24C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013F25C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013F51C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013F52C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013F9FC | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013FEEC | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013FF0C | none | Empty sequence starts with FFFF; no initial frame modeled |
| R_0013FF1C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF2C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF3C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF4C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF5C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF6C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF7C | 1 | One or more referenced frames rejected; exact reasons retained |
| R_0013FF8C | 1 | One or more referenced frames rejected; exact reasons retained |

### Palette-unbound loaded resources

R_0013EADC, R_0013EF6C, R_0013F19C, R_0013F1AC, R_0013F1BC, R_0013F1EC, R_0013F20C, R_0013F22C, R_0013F66C, R_0013FAAC.

These ten descriptors are structurally understood but have no registered actor/player palette association. No palette is borrowed from a neighboring slot and no PNG is invented.

## Validation and provenance

Eight new field-sprite tests and nine existing field-map tests pass (17 total). The initial full field suite passed seven tests and failed a test expectation of 18 default frames; ROM sequences establish 14. That test also incorrectly expected a valid frame to fail; it was replaced by a controlled upload-length mutation. Only the corrected test was rerun, and passed; the seven earlier passing tests were unchanged. Full details and command outputs are in test_results.json.

Checks cover every PNG CRC, pixel/PNG SHA-256, dimensions and binary transparency; all recorded JP/English source spans; the 494-map/2987-actor census; three native-pixel fixtures (16x24,16x16,24x32); synthetic 1D quadrant ordering, flips and priority; known sequence steps; rejection of invalid pointers/tiles; deterministic native PNG generation; and overwrite refusal. All 494 map actor pointers match the latest maps.csv. The default-resource native PNG and its contact sheet were visually inspected as secondary checks. No runtime/screenshot validation is claimed.

Translation toolkit images.cpp:LoadCompressedTileset, tiles.cpp:Palette::Load and 4bpp packing routines were inspected. They corroborate palette/tile primitives, but their translated assets do not supply an independent exact field-actor fixture; unrelated signs/UI art were not used as false regressions. Pixel hashes in this run are static regression fixtures, not independent proof of named identities.

### Native address ledger

Each code range below is file [start,end), with derived bus range, raw instructions, source/tool symbol and hashes in structured evidence. Per-asset exact addresses/ranges are in the export evidence catalogs.

| File range | Purpose | Confidence |
|---|---|---|
| 0x000340C0..0x00034102 | Descriptor +3 raw tile count, +4 raw tile pointer; contiguous CpuFastSet upload | Confirmed static, scoped |
| 0x0003411C..0x00034170 | Effective header selection, default fallback, 16 graphics slots | Confirmed static, scoped |
| 0x000341F2..0x00034242 | Advance graphics prefix then copy 12 raw 16-color palettes | Confirmed static, scoped |
| 0x00034324..0x000343EE | Actor graphics slot low five bits; palette slot high nibble; descriptor pointer binding | Confirmed static, scoped |
| 0x0003459A..0x0003461E | Facing-selector map and descriptor +8/+C animation/frame tables into actor state | Confirmed static, scoped |
| 0x000347D8..0x00034812 | Default player actor slot 0 takes first resource; sequence/frame table binding | Confirmed static, scoped |
| 0x0003310C..0x0003318E | Sequence pointer selection, initial frame index, descriptor lookup | Confirmed static, scoped |
| 0x000331A4..0x00033202 | Explicit sequence-step selection | Confirmed static, scoped |
| 0x00033218..0x00033272 | Animation counter/threshold, four-byte step advancement, FFFF handling | Confirmed static, scoped |
| 0x00033288..0x000332D2 | Sequence wrap and new frame descriptor selection | Confirmed static, scoped |
| 0x000333C4..0x000334E4 | Field OBJ draw: signed coordinate wrapping, tile-base addition, palette-bank replacement; optional runtime affine path | Confirmed static, scoped |
| 0x00033508..0x00033540 | Field object count and OAM capacity gate | Confirmed static, scoped |
| 0x00034ED4..0x00034F50 | Copy 70-byte header and up to 15 10-byte actor records | Confirmed static, scoped |
| 0x00034F96..0x00034FF2 | DISPCNT=1E40 enables 1D OBJ mapping; player sequence mapping | Confirmed static, scoped |
| 0x0003F8A4..0x0003F8D8 | Map index -> 1C-byte record -> actor block+70 registration | Confirmed static, scoped |

Additional structures: file0062D3E4..006309EC is the map table; file00140180..001401F0 is the fallback 70-byte header; file00631920..00631930 is the facing-selector lookup. Descriptor/palette/sequence/frame ranges are resource-driven and enumerated with purpose/confidence/hashes in evidence.json, discovery_evidence.json and animations.json. RAM actor base03001BDC with stride30 has no ROM offset.

### Reproduction and integrity

```powershell
python -B tools/extract/extract_field_sprites.py --output NEW_DIRECTORY
python -B tools/extract/test_extract_field_sprites.py
python -B tools/extract/preview_field_sprites.py --output NEW_PREVIEW_DIRECTORY
```

Python standard library only. All outputs require fresh paths. The preview helper and tests use the canonical final_verified directory; the extractor accepts any new destination. New code: extract_field_sprites.py, preview_field_sprites.py, test_extract_field_sprites.py, audit_field_sprites_v1.py under tools/extract/. Earlier code, CSVs, reports and exports were not overwritten.

Before the first write, **9,105 protected files** were SHA-256 hashed with zero read errors using the established scope (all workspace files except .git, installed Ghidra, Python caches and generated api-classes/compile-libs). Final integrity.json rehashes those paths and checks the prior v6 baseline. changed_files.json lists every new file and any unexpected modification/missing path. New asset directories have local ignore files; nothing was committed or published.

The bounded stop is named companion identity binding, cardinal/idle/walk state transitions, palette-unbound resources and explicit invalid/unsupported sequences. No further enemy work or other graphics categories were started.
