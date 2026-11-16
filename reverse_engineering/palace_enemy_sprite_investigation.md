# Detector and Rattlin' Dragon sprite extraction

2026-10-15. Separate extension to the Session 7 enemy investigation. No changes to
the bestiary, ROM, saves, enemy data, scripts, formations or gameplay code. No
emulator or Ghidra operation. Kaizo remains complete; Hawker placement deferred.

## Result and confidence

Both enemies were successfully extracted as two distinct, transparent RGBA PNG
frames each. Native resolution and nearest-neighbor 4x copies are provided.
Both frames of each enemy were visually inspected and form coherent artwork.
Enemy-to-image identity is **Confirmed static** through each enemy record, not a
visual guess or a scan for plausible graphics. Whether these are the enemies the
user remembers remains for the user to confirm. No runtime screenshot comparison
or animation playback was performed.

Source ROM: `tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba`.
SHA-256: `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`.
All addresses below are ROM bus addresses; file offset = bus minus `08000000`.

## Exact enemy graphics references

Enemy record formula, established by `inserter/text.cpp:EnemyInfoAddress` and the
bestiary: `08634F50 + enemyID*4C`. These two enemies use direct frame references,
not an additional graphics-index lookup. Record byte +2F selects dimensions.

| Property | Detector A5 | Rattlin' Dragon 9C |
|---|---|---|
| Record bus / file | `0863804C` / `0063804C` | `08637DA0` / `00637DA0` |
| +2F size-index field bus / value | `0863807B` / 0 | `08637DCF` / 2 |
| Dimension table entry bus / file | `08486548` / `00486548` | `08486550` / `00486550` |
| Dimensions, 8x8 tiles | 5 x 5 | 10 x 5 |
| Dimensions, pixels | 40 x 40 | 80 x 40 |
| +34 palette-pointer field bus | `08638080` | `08637DD4` |
| Palette bus / file | `0851FC34` / `0051FC34` | `08520194` / `00520194` |
| +38 frame-0 pointer field bus | `08638084` | `08637DD8` |
| Frame 0 bus / file | `085A81CC` / `005A81CC` | `085B4D0C` / `005B4D0C` |
| +3C frame-1 pointer field bus | `08638088` | `08637DDC` |
| Frame 1 bus / file | `085A8410` / `005A8410` | `085B514C` / `005B514C` |
| +40 layout-pointer field bus | `0863808C` | `08637DE0` |
| Layout bus / file | `085E9A90` / `005E9A90` | `085E9B28` / `005E9B28` |
| Decompressed bytes per frame | 800 | 1600 |

Every field location and meaning above is **Confirmed static** by the loader and
matching data. Exact compressed consumed ranges, decompressed SHA-256 values and
output names are in `exports/palace_enemy_sprites/extraction.json`. The last
compressed byte need not be the byte immediately before the next pointer because
alignment padding may follow a stream.

## Graphics pipeline and reconstruction

1. `0804C674-0804C684` reads enemy +2F and uses four-byte entries copied from
   `08486548`; each entry is two little-endian halfwords, width and height in tiles.
2. `0804C6F4-0804C708` reads the raw palette pointer from enemy +34 and DMA-copies
   eight words (32 bytes, 16 colors) to OBJ palette bank `6 + enemy slot`, starting
   at `050002C0` for slot zero. The fallback branch at `0804C7D0-0804C7EC` copies
   the same palette to BG palette bank `6 + slot`, starting at `050000C0`.
3. `0804C70A-0804C718` selects frame pointer `enemy+38+4*frameIndex`. The frame
   index is target byte +29 hex, not the enemy size index. Two pointer fields are
   evidenced. `0804C034-0804C03E` and `0804C2FE-0804C308` toggle the index with XOR
   1; reset paths such as `0804C0F0-0804C0F2` set it to zero.
4. `08040014-08040060` reads the compression header and dispatches type 10 hex to
   BIOS LZ77 through `080942F0`. Type 30 RLE is also supported by that helper but
   is **not used by these four streams**. Each stream starts with `10` followed
   by a 24-bit little-endian decompressed length: `000320` for Detector and
   `000640` for Rattlin' Dragon. Decode MSB-first flag bits; literal or backref
   length `(firstByte>>4)+3`, distance `((firstByte&15)<<8 | secondByte)+1`, with
   overlapping backreferences allowed. All four streams decode to the exact
   dimension-derived size without out-of-range references or overrun.
5. `0803FFA0-08040008` copies tile rows: source stride `width*32` bytes,
   destination stride 1024 bytes (32 tiles). Thus compressed data is a compact
   row-major rectangle of 8x8, 4bpp tiles, not already padded to VRAM's row stride.
   `0804C728-0804C73C` loads this into OBJ tile storage; the fallback uses
   `0600C000` at `0804C80A-0804C81C`. The exporter reconstructs the compact image,
   rather than copying VRAM padding into the image.
6. For both +40 layout arrays, every halfword is exactly
   `6200 + 32*y + x` over the verified rectangle: Detector 25 entries/50 bytes,
   Dragon 50 entries/100 bytes. This independently corroborates the row/column
   layout, nominal palette bank 6 and absence of per-tile H/V flips. Dynamic
   slot relocation does not change the extracted palette colors. No extra body
   parts or separate composition were needed to reconstruct these base frames.
7. Decode each tile as 32 bytes: four bytes per pixel row, low nibble first,
   then high nibble. Palette halfwords are GBA BGR555 (red bits 0..4, green
   5..9, blue 10..14; ignore bit 15). Five-bit channels expand as
   `(value<<3)|(value>>2)`. Palette index zero has alpha 0; all other indices
   have alpha 255. The RGB stored under transparent pixels may be pink/blue;
   that is not an opaque background in the exported RGBA PNGs. No LCD color
   correction, battle flash, status recoloring or blending is simulated.

Native instruction excerpts, source byte comparisons and PNG checks are retained
in `exports/palace_enemy_sprites/verification.json`. Offsets in this pipeline are
hexadecimal unless explicitly described as decimal byte counts.

## Output images

Directory: `reverse_engineering/exports/palace_enemy_sprites/`.

| Enemy | Native transparent frames | 4x transparent previews |
|---|---|---|
| Detector | `detector_A5_frame0.png`, `detector_A5_frame1.png` | `detector_A5_frame0_4x.png`, `detector_A5_frame1_4x.png` |
| Rattlin' Dragon | `rattlin_dragon_9C_frame0.png`, `rattlin_dragon_9C_frame1.png` | `rattlin_dragon_9C_frame0_4x.png`, `rattlin_dragon_9C_frame1_4x.png` |

Frame numbers describe the verified pointer order, not speculative idle/attack
pose names. Detector's frames visibly change the raised appendage/upper shape;
Dragon's frames shift the head/body silhouette. These are useful identification
views. Frame timing, battle-script state meaning, movement/effect overlays and
which pose accompanies Annoying Siren remain **Unresolved**. Two base graphics
frames do not imply that a complete attack animation has only two visual states.
No new encounter-rate or combat-mechanic conclusion follows from this extraction.

## Reproduction, preservation and scope

`python -B tools/analyze/extract_palace_enemy_sprites.py --output NEW_DIRECTORY`

The standard-library-only exporter gates the ROM SHA-256 and refuses an existing
output directory; PNGs and manifest use exclusive creation. It writes only new
extraction outputs, never ROM data. No package installation is required. PNGs
are locally ignored by an output-directory `.gitignore`; no extracted asset is
committed. Existing bestiary/research and ROM hashes were preserved.

Inspected: `AGENTS.md`, modding plan, existing palace research/evidence context,
`tools/analyze/thumb_inspect.py`, translation `inserter/lz77.cpp`, tile decoder
source search references, and the active ROM's two enemy records, four compressed
streams, palettes, dimension/layout arrays and the explicitly cited native code
windows. Japanese and English baseline ROM bytes were compared only for the
relevant asset spans. No whole-ROM auto-analysis or graphical approximation.
