# Multipart enemy ownership and composition v6

2026-10-27. Bounded, read-only follow-up to v5. No ROM writes, emulator operation,
Ghidra analysis, gameplay work or NPC/player extraction. No completed enemy
extraction was rerun by the new analyzer. Historical regression suites were run
as tests; the new analyzer never decompresses enemy graphics.

## Finding and coverage

The proven base rendering path defines **one root-level shared composite**, not
separate child drawing objects. Each actor controls a tile upload selector, while
the complete root descriptor supplies all OBJ rectangles, including the base
block rectangles. The final submission helper does not receive child identity
and contains no child-specific rectangle filter or crop.

This resolves the distinction between resource dependence and draw ownership on
the traced path. It does **not** prove a semantic standalone silhouette for any
of the 25 child records. They are now classified as **context-dependent shared
composite participants; standalone partition unsupported**. The database remains
157 records with scoped sprite output and 25 without proven standalone output.
No complete-extraction claim is made.

Five representative root profiles are provided as explicitly labeled shared
composites: roots 43, 1A, 31, 5F and B3, associated with children 44, 1B, 33, 60
and B4 respectively. Their 18 native PNG frames are exact copies of already
validated v5 root OBJ exports, not new isolated child images or new extraction.
They show palette set 0, descriptor 0 and actor-state selectors 0. These are
static render configurations, with encounter reachability unproved; in
particular they are not asserted to be Death Lilby's initial state.

Canonical artifacts: `exports/enemy_sprites_v6/final/`. `coverage.csv/json`
reconciles all 182 records; `remaining25.csv` lists every remaining ID and reason;
`profiles.json` contains all root OBJ attributes, resource dependencies, common
anchors and modeled submission results; `composites.json` supplies dimensions,
component identities, source PNG/pixel hashes and inherited render limitations.
`native_evidence.json` contains the new bounded instruction evidence.

## Representative selection and generalization

The analyzer evaluates representatives before the other cases. The data-based
rule is then checked against all 25 typed formation links and their selected
root descriptors; no proximity/name-based links are inferred.

| Child | Root | Distinct structure exercised | Descriptor bus | OBJ count |
|---|---|---|---|---:|
| 44 Red Baby | 43 Conda Kid | Two actors, two-frame cycle; child-dependent single 32x32 OBJ | 080C5634 | 13 |
| 1B Miracle Mirror | 1A Oops | Three actors, four frames; child component references multiple palette banks | 080C5404 | 21 |
| 33 Big Donut | 31 Pompadour | Three actors; seven child-dependent OBJs use banks 6,7,9 | 080C5580 | 29 |
| 60 Death Lilby | 5F Death Lilby | Initializer changes child flags; selected-state profile differs from initial-state claim | 080C5910 | 11 |
| B4 Left Binky | B3 Abiwrath | Three actors; multipart limbs and mixed banks; alternate-descriptor mechanism exists | 080C5B44 | 24 |

All listed descriptor addresses are original Japanese and English baseline ROM
bus addresses. File offset is bus minus 08000000. The complete addressed source
spans were rehashed against the v5 evidence and compared between the two ROMs.
Name bytes are excluded. Confidence is **Confirmed static for the stated base
profile**, with runtime script reachability and semantic silhouette ownership
explicitly unproved.

## Actor identity to final OBJ chain

1. The typed formation links retained in v5 map root/child record pointers to
   actor slots. For example formation file 00455E64 maps root 31 and children
   32/33 to slots 0/1/2. Record 33 is file 00635E74. Its own graphics fields
   +34..4B are zero; it has no independent OBJ or animation pointer.
2. Root +34 selects a palette-set table; entry 0 initializes four palette
   pointers at RAM 0300091C..0300092B. Root +44 initializes the global OBJ table
   pointer at 0300092C; root +48 supplies the animation table.
3. Multipart setup binds that animation table and current OBJ table to global
   render state **S=03000B04**. In this state, +0 is animation table, +4 is OBJ
   descriptor table, +C flags, +D cycle, +10 tile offset, +12 common X, +14 common
   Y, +1A palette-bank delta, +1B priority override. These offsets are hex.
4. Each actor's target is T=03000A40+slot*38. Its flags T+0A bit 0800 select a
   state through root +3C -> state table -> part table[slot] -> frame table[cycle].
   The selected compact 6x8 block uploads at atlas x=12+6*slot, y=0, pitch 32
   tiles. The separate root base frame is 12x8 at atlas x=0. Root actor slot 0
   also controls part 0. A child changes a source block, not an OBJ sublist.
5. `0804C3D8` calls the generic animation/draw helper with S. That helper selects
   a descriptor from S+4 using the current animation descriptor index; supported
   six-byte base animation loops select index 0. All listed root descriptors
   have ordinary counts below 128 and no high-bit affine trailer.
6. `080406B0..080406D4` passes that one descriptor plus uniform adjustments to
   `08040424`. Its inner loop appends **every descriptor entry, in order**, to
   RAM OAM staging at 030014B8+8*cursor, cursor byte 030027ED, capped at 128 total
   entries. There is no actor ID, target rectangle, tile-block test, or ownership
   mask in this loop. It stops for descriptor count or exhausted global OAM
   capacity, not for child boundaries.

The same graph and accepted non-affine descriptor structure hold for all 25
records. This supports the shared-composite classification on the default path.
It does not establish that no other script can change the render state.

## Base blocks and silhouette ownership

All descriptors contain both base-dependent entries and child-dependent entries.
The base block is submitted as part of the same display list and remains present
independently of which actor selects a part stream. An OBJ's tile source tells
which uploaded resource it depends on; it does not carry a semantic enemy-owner
tag. Neither the final helper nor its caller partitions base rectangles among
children. Target geometry used for battle interaction is not passed into this
helper as a crop.

For Big Donut 33 the component-dependent OBJ indices are 4,5,6,7,8,25,26, using
banks 6,7,9. Every source tile in these entries belongs to part 2. Other descriptor
entries depend on the base or other parts and are submitted in the same call.
This demonstrates why palette bank cannot be used as ownership. It also leaves
unproved whether any constant art in those other blocks belongs semantically to
Big Donut. A guessed crop or a part-only PNG would resolve that uncertainty by
assumption, so none is labeled standalone here.

For Red Baby 44, one 32x32 entry (index 4) depends on part 1, but the same helper
still submits all 13 entries. The smaller dependency set is not evidence of a
separate actor draw. All 25 full dependency maps are in `profiles.json`.

## Coordinates, ordering and attributes

`submit_obj_attributes` implements the final native submission arithmetic for
the validated non-affine 4bpp profile:

- Y becomes (original Y + common Y) modulo 256; X becomes (original X + common X)
  modulo 512. Shape/size and flip fields are preserved. No per-child coordinate
  is applied in the inner loop.
- The tile number becomes (original tile + uniform tile offset) modulo 1024.
  The palette bank receives a uniform delta modulo 16. The base profile uses
  tile offset 0 and palette delta 0, preserving explicit banks 6..9.
- Priority override -1 preserves the descriptor priority; otherwise bits 10..11
  of attr2 are replaced. Mode override -1 preserves attr0; otherwise bits 10..11
  are replaced. Runtime blend effects are not modeled as new images.
- Entries retain descriptor order. The shared OAM cursor determines global
  order. Existing PNG composition assumes the validated equal-priority profile
  and no external actors/effects covering it; it is not a whole-screen render.
- No selected entry is affine. The helper can process an optional affine trailer
  when the descriptor header's high bit is set; that branch is documented but
  not admitted by this implementation. Rotation/scaling is not guessed.

Root common anchors initialize as X=8*(record[2D]>>4)+4*(record[2E]>>4),
Y=8*((record[2D]&15)+(record[2E]&15)). Exported images normalize the explicit OBJ
bounds; `profiles.json` separately preserves the common screen anchor and
submitted attributes. Those anchors are shared by all rectangles, including
children and base, and do not prove child-specific positioning.

## Runtime contexts and bounded stopping point

Newly inspected script handlers prove that base descriptors/palettes are not
universal for every battle state:

- `08041EF0..08041F32` reads two stream-supplied pointers, writes 0300092C and
  03000930, then calls the setup entry. The new values can replace the global
  OBJ table and BG layout.
- `08041F40..08041F6C` and `08041F88..08041FB4` install fixed alternate global
  tables/layouts. Their reachability for each of these 25 actors was not traced.
  The existence of the mechanism is confirmed; invoking it in a given encounter
  is not claimed.
- `08041D10` and its selector branches update palette pointers/banks. The
  animation update at `0804C560..0804C574` can also source an actor bank from
  palette-set entry 1. These paths can alter visible colors without assigning a
  standalone child display list.
- The root cycle and individual actor flag states alter selected source streams.
  Death Lilby-specific initialization sets child flags at 08048348..08048364.

The actual default submission behavior is established. What remains unresolved
is **encounter-specific dynamic descriptor/palette selection and any semantic
partition of base artwork into complete child silhouettes**. Bounded static
analysis stops here rather than expanding into the full battle script VM.

### Single smallest user-operated debugger observation

If further runtime evidence is wanted, use **one execution breakpoint at bus
08040424** (Thumb function entry, file 00040424), during a naturally reached
Pompadour/Big Donut formation. Do not modify memory. Record calls at this one
target just before and after Big Donut's first visible state/phase change. This
is one observation target over the transition, not a request to set multiple
watchpoints. No debugger command was executed by this task.

At entry, record:

- LR and R4. On the generic draw call LR is 080406D9. Global multipart state has
  R4=03000B04; another R4 value would identify a different render state.
- R0 points to draw parameters. Inspect u32[R0] (actual descriptor), then u16
  [R0+4] tile offset, u16[R0+6] common X, u16[R0+8] common Y, byte[R0+A] palette
  delta, signed bytes[R0+B] priority and [R0+C] mode. Inspect the descriptor count
  and its six-byte attr0/1/2 entries.
- Confirm u32[030008EC]=08635DDC (root 31). Record u32[03000B08] (current global
  OBJ table), byte[03000B11] (cycle), u16[03000ABA] (slot-2 child flags), and the
  four palette pointers at 0300091C..03000928. The unmodified base profile's
  descriptor is **080C5580**, count **29**.

Interpretation:

1. Same global R4, same descriptor/entries, changed child flag: supports atlas
   state replacement within one shared silhouette; no child crop emerges.
2. Same global R4 but changed descriptor or uniform parameters: proves a
   context-specific global composition; the captured table/state must be
   modeled separately before exporting that context.
3. An additional generic draw for this formation uses a distinct R4/descriptor
   attributable to the child: supports an independent child draw path and gives
   the exact render-state/descriptor target for the next bounded trace. Other
   party/effect calls must not be mistaken for that evidence.

This observation distinguishes dynamic geometry replacement from atlas-only
state changes. An unchanged shared draw cannot establish an artist's intended
semantic crop of immutable base pixels; such a crop must remain unsupported.
Only the user may operate mGBA, and no encounter or runtime outcome is asserted
here.

## Address and source ledger

All code ranges are exclusive-end file ranges and are byte-identical in the
fingerprinted Japanese and English ROMs. Add 08000000 for bus addresses. Source
symbol for disassembly: `thumb_inspect.inspect`. Decoding/model symbols:
`multipart_ownership_v6.submit_obj_attributes`, `resource_dependence`, `profile`.

| File range | Purpose | Evidence/confidence |
|---|---|---|
| 00040424..00040542 | Counted full OBJ submission, uniform adjustments, OAM append | Saved instructions and pure arithmetic model; Confirmed static |
| 00040542..000405E6 | Optional affine trailer | Header high-bit branch; absent in selected profiles; Confirmed bounded exclusion |
| 0004068E..000406DA | Draw parameter binding from one render state | Saved instructions; Confirmed static |
| 000481BA..0004822E | Shared anchor and state initialization | Saved instructions; Confirmed static |
| 0004831C..00048366 | Root palette/descriptor binding and special child flags | Saved instructions; Confirmed static |
| 0004BEA4..0004BED2 | Multipart setup binds one shared OBJ table | Saved instructions; Confirmed static |
| 0004C3D8..0004C41A, 0004C424..0004C4FC | Shared draw, root cycle, part state/upload selection | Saved instructions; Confirmed static |
| 00041EF0..00041F32, 00041F40..00041F6C, 00041F88..00041FB4 | Global descriptor/layout writers | Saved instructions; Confirmed mechanism, per-encounter reachability unproved |
| 00041D10..00041D56 and saved selector branch windows | Palette writers | Saved instructions; Confirmed mechanism, per-encounter reachability unproved |
| 0004C560..0004C574 | Alternate temporary actor palette source | Saved instructions; Confirmed bounded mechanism |
| Per-root descriptors and formation links | Resource dependence of every rectangle | v5 source hashes rechecked; profiles.json; Confirmed selected configuration |
| RAM 03000B04, 0300091C, 0300092C, 030014B8, 030027ED | Render state, palettes, table, OAM staging/cursor | Native resolved literals and access chain; no ROM file offset |

## Updated classifications and validation

Every remaining ID is classified in `remaining25.csv`:

`1B 1C 1E 2F 30 32 33 44 46 48 4A 4C 4D 5D 60 61 74 76 77 8D 8E B1 B2 B4 B5`

All remain unsupported as standalone silhouettes, with confirmed shared default
rendering and explicit actor-to-part resource dependencies. No child inherits a
whole root image as an alias. Coverage for the other 157 records is preserved.

Seven new tests cover wrapping and attribute-field preservation, overrides,
descriptor order/OAM capacity, all 25 dependency maps and uniform anchors,
palette-versus-resource identity, all 18 frozen composite PNG hashes and explicit
bounds, fresh-output determinism and overwrite refusal. All pass. The existing
39 tests also pass, unchanged: **46 tests total**. Results are retained in
`exports/enemy_sprites_v6/test_results.json`.

Reproduce only the new bounded work:

```powershell
python -B tools/analyze/multipart_ownership_v6.py --output NEW_DIRECTORY
python -B tools/analyze/test_multipart_ownership_v6.py
```

New files are the analyzer, its tests, the audit helper, this report, and v6
exports/evidence/logs. No pre-existing script, test, ROM, CSV, PNG or report was
modified. Before the first write, the established integrity procedure hashed
**9,070 protected files** with zero read errors. The final audit rehashes every
path; exact changed/missing/added paths and results are in v6 `integrity.json` and
`changed_files.json`. Extracted PNG copies remain local in an ignored output
directory. No files were committed or published.
