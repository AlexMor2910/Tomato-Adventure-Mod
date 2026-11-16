# Enemy sprite finalization v5

2026-10-27. Bounded static follow-up to v4, restricted to the 25 multipart participants and Chekkit. No gameplay, NPC/player extraction, ROM writes, save/state writes, emulator execution, whole-ROM scanning or Ghidra analysis. All earlier files remain protected.

## Result and limits

**Newly supported: 8C Chekkit, four transparent 80x80 OBJ frames and four 4x previews.** The prior 156-record extraction was not rerun: all 652 existing PNGs (326 native plus previews) were copied byte-for-byte, and all 326 old frame metadata entries were retained exactly. Existing regression tests were rerun as validation.

Across all 182 records: **124 distinct decoded resources + 33 shared decoded records = 157 records with scoped base-frame output; 25 standalone reconstructions remain unsupported.** There are 330 native frames and 330 previews. Zero records remain without an evidence-backed classification; this does **not** mean all 182 are extracted. Chekkit is an OBJ-only render projection with actor flags 0, palette set 0, descriptor 0; animation effects, other palettes/states and runtime memory side effects are excluded.

Canonical output is `exports/enemy_sprites_v5/final_verified/`. The retained first run `final/` has identical PNGs but less complete participant pointer-span accounting. Use final_verified for metadata. `coverage.csv/json` accounts for all 182 records; `frames.json` retains earlier metadata and appends Chekkit; `participants.json` inventories all 25 unsupported cases; `chekkit_evidence.json` records every used span, token accounting, descriptor and output discrepancy.

## Multipart findings

ROM/file addresses below apply to both Japanese and English baselines. Bus = file + 08000000. Each per-record palette/table/stream/descriptor range, purpose-bearing field, source hash and JP/English equality is in participants.json. Original inline name bytes +0..7 differ and are excluded. All 25 participants have zero own graphics fields +34..4B, including +44 OBJ and +48 animation pointers. Their resource selection is through typed formation slots and the root record; no per-enemy offsets were guessed.

At bus 0804BDD0..0804BDE6 formation header bit 40 chooses multipart setup 0804BEA4, whereas the ordinary branch loops separate actors. Multipart setup places root +48 into global render state at target-base+C4 (03000B04); the root palette table initializes 0300091C and root +44 initializes 0300092C at 0804831C..0804833A. The generic draw helper receives that one root descriptor, not a descriptor assigned independently to the null-pointer child.

Root +3C -> state table[(target[slot].flags & 0800) != 0] -> part table[slot] -> frame table[cycle]. The loader at 0804C952..0804C99E reads each actor flag, increments target address by 38 and uploads a 6x8 block at x=12+6*slot, y=0 in a 32-tile-pitch atlas. The root base block is 12x8 at x=0, and part 0 belongs to root actor slot 0. Root +34 -> palette set 0 supplies four raw BGR555 banks 6..9. OBJ entries select the actual bank; bank identity is not necessarily component identity.

All 25 inventories now enumerate both actor states, their 164 compressed frame-stream references, 77 referencing OBJ entries, exact signed coordinates, shape/size, flips, priority, tiles, palette addresses, and component-reference bounds. Coordinates below are root descriptor coordinates before normalization. They describe a resource layer in the global sprite and do not establish a complete standalone child silhouette. All these OBJ rectangles reference tiles wholly within the indicated component; this proves their resource dependency, not that the component contains every pixel belonging semantically to that child.

In particular 1B uses banks 7/8, 33 uses 6/7/9, 4C uses 7/8, and arm/Binky cases also use mixed banks. Splitting by palette bank would omit valid component pixels. Conversely, splitting by uploaded block could omit constant child artwork stored in the base or another block; the traced draw path provides no child-to-descriptor-subset assignment. Formation target bounds at 08048196..0804822C are separate from the root OBJ canvas and are not a documented image crop.

The six established OBJ-only roots 1D,2E,43,45,47,49 were bounded references for descriptor format and global ownership. Their PNGs were preserved; no accepted sprite was corrected or re-extracted. Death Lilby 5F has initializer-specific child flag bits at 08048348..08048364, so enumerated state-0 resources are not claimed to be every encounter's initial state.

### Exact unsupported record inventory

Common remaining blocker for every row: a complete child silhouette and any base/other-block contribution lack a proved child-specific draw/crop rule. Own graphics/OBJ/animation pointers are all zero. No guessed standalone PNG or root-image alias is emitted. Detailed OBJ attributes and all frame pointers are in participants.json.

| ID | Root / part | Upload tile x | Base cycle | OBJ indices | Banks | Referencing-object bounds (left,top,right,bottom) |
|---|---|---|---:|---|---|---|
| 1B | 0x1A / 1 | 18..23 | 4 | 9,10,11,19,20 | [7, 8] | [8, -72, 40, -40] |
| 1C | 0x1A / 2 | 24..29 | 4 | 12,13 | [9] | [-24, -40, 24, -8] |
| 1E | 0x1D / 1 | 18..23 | 2 | 5,6 | [8] | [-4, -24, 28, 0] |
| 2F | 0x2E / 1 | 18..23 | 2 | 17,18,19,20 | [8] | [4, -56, 28, -32] |
| 30 | 0x2E / 2 | 24..29 | 2 | 0,1 | [9] | [-20, -32, -4, -8] |
| 32 | 0x31 / 1 | 18..23 | 4 | 9 | [8] | [-40, -80, -8, -48] |
| 33 | 0x31 / 2 | 24..29 | 4 | 4,5,6,7,8,25,26 | [6, 7, 9] | [-8, -40, 24, -8] |
| 44 | 0x43 / 1 | 18..23 | 2 | 4 | [8] | [-20, -80, 12, -48] |
| 46 | 0x45 / 1 | 18..23 | 2 | 4 | [8] | [-20, -80, 12, -48] |
| 48 | 0x47 / 1 | 18..23 | 2 | 4 | [8] | [-20, -80, 12, -48] |
| 4A | 0x49 / 1 | 18..23 | 2 | 7 | [8] | [8, -32, 40, 0] |
| 4C | 0x4B / 1 | 18..23 | 4 | 9,10,11,12 | [7, 8] | [-40, -48, -8, -16] |
| 4D | 0x4B / 2 | 24..29 | 4 | 16,17,18,19 | [6, 9] | [-8, -32, 40, 0] |
| 5D | 0x5C / 1 | 18..23 | 2 | 5 | [8] | [8, -40, 40, -8] |
| 60 | 0x5F / 1 | 18..23 | 4 | 1 | [8] | [-24, -80, 8, -48] |
| 61 | 0x5F / 2 | 24..29 | 4 | 2 | [9] | [8, -80, 40, -48] |
| 74 | 0x73 / 1 | 18..23 | 2 | 9 | [8] | [-12, -32, 20, 0] |
| 76 | 0x75 / 1 | 18..23 | 4 | 7 | [8] | [8, -80, 40, -48] |
| 77 | 0x75 / 2 | 24..29 | 4 | 6 | [9] | [-40, -40, -8, -8] |
| 8D | 0x8C / 1 | 18..23 | 4 | 12,13,14,15,16,17,18,19,20,21 | [6, 8] | [8, -56, 40, -8] |
| 8E | 0x8C / 2 | 24..29 | 4 | 11,22,23,24,25,26 | [6, 9] | [-40, -48, -8, -8] |
| B1 | 0xB0 / 1 | 18..23 | 4 | 19,20,21,22,23 | [6, 8] | [8, -64, 40, -32] |
| B2 | 0xB0 / 2 | 24..29 | 4 | 5,6,7 | [6, 9] | [-40, -40, -8, -8] |
| B4 | 0xB3 / 1 | 18..23 | 4 | 1,2,3,4,5,6,7 | [7, 8] | [8, -80, 40, -48] |
| B5 | 0xB3 / 2 | 24..29 | 4 | 8,9,10,11,12 | [7, 9] | [-40, -32, -8, 0] |

## Chekkit: format and justified upload projection

Chekkit root record: file 006378E0, bus 086378E0. Its four-frame base table starts at file 00634D8C; frame-2 pointer field 00634D94 selects 005D2BA8. The source header is 30 00 0C 00: RLE type 30, declared length 000C00 = 3072. The game reads the 32-bit word then shifts right by 8 at 0804001A..0804001E, so there is no alternate size interpretation in this path. The scratch allocation uses that size, rounded to words; 3072 is already aligned. RLE dispatch calls bus 080942FC -> SWI 14 at 08040042..08040046.

The stream contains 96 tokens, consumes 654 bytes, and ends at file 005D2E36, before the next stream at 005D2E38. Its last token at 005D2E34 is FE 00: (FE & 7F)+3 = 129 zero bytes. It begins after output byte count 3071 and thus reaches 3200 bytes, 128 past the header length. The reason for the authoring anomaly is unknown; no claim of intentional padding or a corrected header is made. Full-token source SHA-256 is 0a45e52441dcf0e84a0aabbf1bdf96fc6748572a5b18cdc03942dcc36d17caf2.

Boundary references were inspected as source only. mGBA 0.10.5 `_unRl` stops an inner run at the remaining advertised byte count; it yields 3072 bytes here. This is emulator implementation evidence, not original-hardware proof. [Source](https://github.com/mgba-emu/mgba/blob/0.10.5/src/gba/bios.c#L783).

The Cult-of-GBA BIOS assembly finishes a run before checking remaining length, yielding 3200 bytes for this stream. Its assembly, rather than inconsistent pseudocode comments, was inspected. It is corroborating implementation evidence; no supplied original BIOS fingerprint was analyzed. [Source](https://github.com/Cult-of-GBA/BIOS/blob/master/bios_calls/decompression/running_length.s#L40).

Both policies write the same first 3072 bytes. Crucially, the ROM independently configures a 12x8-tile upload with source coordinates (0,0) at 0804C900..0804C926. Row-copy routine 0803FFA0..0804000E reads eight source rows of 12*32=384 bytes and no later data: exactly source [0,3072). Destination pitch is 1024 bytes. Thus the image upload is invariant to the extra 128 bytes. Exact original BIOS overflow effects outside the upload remain unsupported; no runtime memory-safety or successful encounter execution is asserted.

New `exception_projection` is gated to this exact source, hash, pointer field and 3072-byte upload. It records the original header unchanged, obtains complete-token length from the existing ledger, and replays all tokens through the existing strict decoder using a temporary analysis-only length view. It records the 3200-byte replay hash and excess zeros, then explicitly selects the native upload range. This is an extraction projection, not a repaired stream or a relaxed general decoder. The existing field-map/strict RLE decoder remains unchanged and still rejects this stream.

All four Chekkit frames compose through 27 native non-affine 4bpp OBJ entries on an 80x80 canvas. BG and OBJ visible pixels agree for frames 0,1,3; frame 2 differs by 10 pixels. The four exported PNGs consistently use the OBJ path, following the earlier scoped OBJ-only precedent. That discrepancy remains explicit and is not fixed by selecting a more plausible picture. The enlarged frame-2 export was visually inspected as a secondary check; identity and composition rest on pointer/descriptor evidence.

## Bounded native evidence ledger

Each interval below is file [start,end), with instruction bytes, resolved literals, SHA-256, JP/English equality and confidence retained in enemy_sprite_finalization_v5_evidence.json. Individual asset ranges are listed separately in participants.json / chekkit_evidence.json.

| File range | Purpose | Confidence |
|---|---|---|
| 0x00048196..0x0004822E | Multipart target bounds versus global renderer bounds | Confirmed static, bounded path |
| 0x0004831C..0x000483AC | Root palette/descriptor ownership and special initial child flags | Confirmed static, bounded path |
| 0x0004BDD0..0x0004BDE6 | Formation bit 40 selects one multipart setup | Confirmed static, bounded path |
| 0x0004BDEC..0x0004BE04 | Ordinary branch loops three separate actors | Confirmed static, bounded path |
| 0x0004BEA4..0x0004BED2 | Multipart branch initializes global render state at target base+C4 | Confirmed static, bounded path |
| 0x0004BEE4..0x0004BEFC | Global BG descriptor pointers | Confirmed static, bounded path |
| 0x0004BF04..0x0004BF0C | Global optional descriptor cleared | Confirmed static, bounded path |
| 0x0004C3D8..0x0004C41A | Animation draw call uses global 03000B04 | Confirmed static, bounded path |
| 0x0004C424..0x0004C4FC | Two/four cycle, root frames and actor flag-selected component uploads | Confirmed static, bounded path |
| 0x0004C88A..0x0004C9DC | Root palette banks and 12x8/6x8 OBJ upload configuration | Confirmed static, bounded path |
| 0x0004068E..0x000406DA | Descriptor selected once, full OBJ descriptor passed to draw | Confirmed static, bounded path |
| 0x0003FFA0..0x0004000E | Compact source rows and explicit upload dimensions | Confirmed static, bounded path |
| 0x00040014..0x0004006C | Header size >>8, scratch allocation, SWI dispatch, upload, free | Confirmed static, bounded path |
| 0x000942FC..0x00094300 | RLE WRAM SWI 14 wrapper | Confirmed static, bounded path |
| 0x0002CBDA..0x0002CBF8 | Scratch allocator rounds requested bytes to words | Confirmed static, bounded path |

## Tests, preservation and reproduction

All **32 existing tests and 7 focused new tests pass (39 total)**. New checks cover all 182 IDs; frozen 326 metadata entries and 652 old PNG bytes; Chekkit dimensions/object count/four pixel hashes and BG discrepancy; exact exception token/length/consumption and native row-read range; refusal of changed hashes/other sizes/sources; all 25 component graphs, states, attributes and source equality; refusal to overwrite and a fresh deterministic export. The 156 completed records are not re-extracted by the new pipeline, including its repeatability test.

Commands from workspace root:

```powershell
python -B tools/extract/finalize_enemy_sprites_v5.py --output NEW_DIRECTORY
python -B tools/extract/test_finalize_enemy_sprites_v5.py
```

Keep the versioned prior decoder modules and v4 final exports as dependencies. No old script/report/test was modified. New code files: finalize_enemy_sprites_v5.py, test_finalize_enemy_sprites_v5.py, audit_enemy_sprites_v5.py under tools/extract/. New report/evidence: this file and enemy_sprite_finalization_v5_evidence.json. All new local PNGs/catalogs/manifests/test logs/integrity results live under exports/enemy_sprites_v5/. The exact added-file list is in changed_files.json; modified pre-existing file list is empty if integrity passes.

Before the first write, the established all-workspace scope hashed **7,723 files**, with zero read errors. Exclusions: .git, installed Ghidra, Python caches, generated api-classes/compile-libs. Final integrity.json rehashes every original path, compares earlier v4 integrity expectations, counts preserved PNGs, and detects missing/changed files. Asset output directories contain local ignore files; no files were committed or published. No NPC/player extraction was begun.
