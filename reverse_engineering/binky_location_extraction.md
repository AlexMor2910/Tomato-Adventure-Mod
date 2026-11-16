# Fixed Binky location extraction

2026-10-20. Bounded read-only static analysis. No ROM, save, savestate, RAM,
gameplay, patch, emulator, debugger, Ghidra, or Git-commit changes were made.

## Result and completeness

**74 individually identified, registered fixed actor pickups award 74 Binkies.**
This is a complete census of that verified structure within the established
494 map descriptors and 2,987 initial actor registrations. It is **not a complete
game-wide fixed collectible total**. Scripted rewards, containers using other
mechanisms, dynamically created actors, enemy drops, and shop stock are not
fully decoded. Seven additional grant-pattern candidates remain unresolved.

The 74 collection IDs are distinct. Each verified pickup awards one item;
there are no multi-Binky quantities in this particular structure. The Python
aggregator supports larger quantities and keeps conditional rewards separate.

Node ownership is incomplete: **35 of the 74 pickups have a Probable node
association; 39 are unassigned**. The latter remain in an explicitly named
unassigned pool. No room or node all-source total is claimed complete.

## Inputs, sources, and addresses

Read `AGENTS.md`, `tomato_adventure_modding_plan.md`, existing extraction
utilities, and relevant findings in:

- `gimmick_palace_enemy_research.md`: map descriptors, actor blocks, exit records.
- `hawker_stage2b.md` and `hawker_stage2b_registration_followup.md`: existing
  actor identity, collection-bank helpers and save serialization. These were
  reused as references; placement analysis was not reopened.
- `hawker_dependency_resolution.md`: prior coordinate-unit evidence.
- `hanzo_lab1_progression.md`, `pre_oystown_progression.md`,
  `oystown_binky_readiness.md`: field maps, overworld arrivals, cached node context.
- `experiments/binky_exchange_rate_two.md`: original exchange grant sites and
  inventory command encoding, used only to exclude renewable rewards.
- `tools/analyze/pre_oystown_progression.py` and existing extraction utilities:
  bounded native inspection, fingerprints, CSV/no-overwrite conventions.

The source ROM for the published outputs is original Japanese:
`Tomato Adventure (Japan).gba`, SHA-256
`0d44380a3eed065b6ca0992d80a248ab001b978e925f7687d5dfcf1ae70e5c12`.
The untouched English baseline SHA-256 is
`8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`.
Both are 8 MiB. Integration tests independently extract both: location,
subtotal, mapping, and candidate outputs agree, and retained native instruction
windows are byte-identical. These equivalences apply to these two baselines,
not later cumulative mod ROMs.

ROM **bus address = file offset + 0x08000000**. For example `08069C0C` means
file `00069C0C`. RAM addresses have no ROM offset. JSON includes both address
forms for native evidence and the actual source hash. English node names come
from `ta_menus_eng.txt`, `BLOCKFIXED 49F61C 10 11 0A`; translated text data is
not interpreted as original Japanese inline strings. Room names remain blank.

## Pickup/object encoding

Map table: file `0062D3E4`, bus `0862D3E4`, stride `1C`, 494 records,
exclusive end file `006309EC` (followed by verified `39` padding). IDs in the
CSV are **table indices**, not an assumption that the first record halfword
is a globally unique room identity.

| Field | Encoding | Purpose / evidence |
| --- | --- | --- |
| Map +0C | u32le bus pointer | Ordinary exit list, 10-byte records, first-byte FF terminator |
| Map +14 | u32le bus pointer | Actor/graphics block; actors start at block+70 |
| Actor record | 16 bytes, at most 15 loaded | First byte FF terminates list; prior table census establishes 2,987 registrations |
| Actor +1 bit 7 | bitfield | Selects native pickup interaction at `08069780..8C` |
| Actor +3 / +4 | unsigned bytes | Encoded X / Y grid coordinates; reader `0803440E..26` |
| Actor +6 | u32le bus pointer | Initializer/control script |
| Actor +0A | u32le bus pointer | Pickup payload pointer; first byte is item ID |
| Actor +0E | u16le | Global persistent collection identity |

`0803F8A4..D6` derives the current map descriptor and installs its actor pointer
plus `70` into `03001948`. `0806974A..58` selects actor record
`base + (interaction_slot-1)*10h` and stores it in `03001AD8`.
The following instructions reconstruct the unaligned actor+0A word byte by byte.
`08069784..8C` tests byte1 bit7 and calls `08069C0C`.

The native pickup handler dereferences the payload and reads **one unsigned
item byte** at `08069C2C..34`. For Binky this is `37` hex. It sets quantity
**1** at `08069C4A..4C`, constructs inventory arguments at `030018F0`, and
calls inventory acquisition `08080424` at `08069C8C`. The ordinary inventory
path uses ID/quantity pairs at `030019D5`; Binky is an inventory item, distinct
from a cumulative donation variable. The payload's later bytes are not treated
as a quantity or an event script.

Coordinates are the **registered grid location**, not a screenshot pixel
position or a proof that the actor never moves. Prior initialization evidence
maps grid X/Y to pixel centers with actor-specific offsets; this export keeps
the raw X/Y bytes and labels their units. It does not invent room names or
derive coordinates for unlocated scripted rewards.

## Collection state and representative trace

**Confirmed static** encoding, using generic helpers `08069F60/08069F8C` and
actor-bank wrappers `0806AFB8/0806B02C`:

```text
id = u16le(actor + 0x0E)
byte_address = 0x03003107 + (id >> 3)
mask = ROM.u8[0x0863A01C + (id & 7)] = 1 << (id & 7)
```

The mask table is `01 02 04 08 10 20 40 80`. IDs are global across maps; the
map number does not enter the calculation. Prior save tracing establishes
384 actor-bank bytes staged to `02001905` and restored from decoded save-slot
`+105` (`0802EF0E..36`, `0802F490..B4`). This is reused static persistence
evidence; no save file was opened or operated in this investigation.

Native handler `08069C1A..2A` reads the record's collection bit and returns
without an award if already set. After acquisition succeeds (result byte zero),
`08069CA2..AA` sets that same bit. Failure branches at `08069C9A` bypass the
setter. The success branch also invokes actor cleanup `08072544`. This proves
one successful award disables further acquisition through this handler; exact
visual timing is not independently measured.

All 74 initializers share this local control shape:

```text
01 FD71 C2 01
FD5B <u16 collection ID> <u32 bus 08100D9D>
00 FD71 04 00
FD30 <loop-start bus address>
```

The branch destination is **`08100D9D`** (file `00100D9D`), encoded
`9D 0D 10 08`. FD5B's handler `08027778..A8` reads the same bank bit and
takes the pointer when nonzero. The shared branch bytes begin
`01 5C FE 0E FD ...`; its full rendering/callback semantics are not decoded.
The established bit check and no-reaward path do not depend on naming those
later operations. Four scripts have leading `01 FD71 E1 00` before this same
guard; the loop returns to initializer+5. That extra configuration is retained
as raw evidence and is not assigned an unsupported meaning.

Representative: map **0003**, descriptor bus **0862D438**, actor record
**08140510** / file **00140510**, registered position **(10,6)**,
initializer **08100699**, collection ID **0015**. ID 0015 selects RAM
**03003109**, mask **20**. Its actor block registration, pickup class bit,
payload `37`, native quantity 1, collection read, success-only setter, and
initializer branch constitute the trace. The stable exported ID is
`actor-flag-0015`: an analyst namespace built from an actual game identity,
not an invented universal Binky index.

A bounded immediate-operand census for FD53/FD54 over file
`[000F9000,0015BA3C)` found **no matches for these 74 collection IDs**.
This supports the fixed interpretation but is not a whole-engine or dynamic
flag-writer proof. New-game resets and modified/corrupt states are outside the
one-collection claim.

## Reward categories and unresolved records

Only the registered pickup structure is counted in fixed subtotals.
The separate script reward command has encoding:

```text
FE55 <u8 item> <u8 quantity> <u32 failure/continuation target>
```

Handler `08025634..52` fetches item and quantity into `03003A34/35` and calls
`080291D4`; the existing inventory/exchange report establishes continuation
handling. Such a command can award multiple items, unlike this native pickup
path. A raw `FE55 37` sequence is **not sufficient to establish a collectible**.

The bounded event-domain census finds 12 patterns. Five are the previously
decoded repeatable AWE exchange endpoints at file
`00107F73`, `00107FAA`, `00108118`, `0010814F`, `00108186`. Their original
baseline award quantities are 1/1/3/2/2. They are exported as renewable sources
and excluded from fixed/conditional completion totals. No exchange or placement
investigation was reopened.

The other seven sites are file `000FDE3D`, `00102CC0`, `00108448`, `0010A06C`,
`0011522B`, `0011E3EC`, `0012238E`, with raw quantity operands
10/4/4/2/5/10/3. They are **Candidate** command matches, not verified one-time
rewards. Their exact script boundaries, room invocation, path conditions,
collection flags, and repeatability remain unresolved. Quantity operands are
retained as evidence; their sum is not added to any collectible total.

Enemy drops, purchases, event-created rewards, and alternate container paths
have no claimed census in this task. No enemy statistics, donation progression,
maps/graphics extraction, or gameplay work was started. The precise remaining
dependency for each candidate is a typed script/root-to-award control-flow trace
and a persistent one-time guard. Counts for those unknown categories stay blank.

## Map-to-overworld-node association

`030035F4` is retained/committed overworld context, not a field-map ID and not
a continuously updated cursor. No map ownership is inferred from RAM snapshots
or numerical map proximity.

This extraction uses two real relationship types:

1. Arrival dispatch at **08088B04**, 17 switch entries. Cases select scripts
   by actual PC-relative loads. First FE7C/FE7D operands supply destination
   u16 map IDs, consumed by `0802A0A0` / `0802A134` and stored at `03001936`.
   Node **0F** returns directly at `08088C3E`, has an empty translated title,
   and supplies no arrival seed. No arrival or map is invented for it.
2. Ordinary map exit records. Destination high bit selects overworld;
   `08069A2A..54` computes `(destination & 255)-1` and stores `030035F4`.
   Other destinations link field maps.

Direct arrival/return relationships are **Confirmed static**. A map's exclusive
ownership by one node is a different claim. For useful partial grouping, the
extractor computes **undirected connected components of ordinary field exits**
and unions their arrival/return-node seeds. Exactly one observed node yields
a **Probable** association. Zero or multiple observed nodes leaves `node_id`
blank, retaining alternatives in `node_candidates`. Undirected connectivity
is association evidence, not a guarantee of bidirectional playable travel.

There are 111 maps with unique observed node candidates and 383 unassigned
maps. Event-script transitions, teleports, and story-dependent connections are
not added as speculative edges. This explains why many dungeon rooms remain
unassigned even when their entrance node is known. Missing edges can conceal
additional node associations; Probable grouping is explicitly provisional.
Interior/event-only/shared maps are treated by the same rules. No map range
is automatically assigned to an area.

## Duplicate prevention and subtotal meaning

Canonical identity is the collection-bit ID, not the payload pointer, item ID,
coordinates, or script pointer. Repeated registrations sharing an ID count once.
Conflicting quantities/categories for an identity raise an error. If one identity
is registered across multiple maps, its canonical row retains all registration
addresses and possible maps, leaves room/node ownership blank, and is excluded
from assigned subtotals. No such Binky aliases occur in these baselines.

Per-room CSV has all 494 map IDs; per-node CSV has 17 node IDs plus a clearly
labeled **unassigned pool**, which is not a fabricated node. All fixed quantities
sum to 74 in both aggregations. A zero means **zero in the fully scanned registered
actor subtype**, not zero Binkies from every possible source. The extra
`complete_total_quantity` column is always blank. Conditional quantities and
unresolved room/node candidate counts remain blank where the missing control
paths prevent association; the seven explicit unknown sources are kept separately.
No repeatable reward contributes to room completion.

## Files and reproduction

- `tools/extract/extracted_data/binky_locations.csv`: 74 canonical locations.
- `binkies_per_room.csv`: 494 registered-actor room subtotals.
- `binkies_per_node.csv`: partial node subtotals plus unassigned pool.
- `binky_map_nodes.csv`: 494 map association rows with candidates/confidence.
- `binky_other_sources.csv`: five known renewable exchange sites.
- `binky_unresolved.csv`: seven unclassified script-pattern candidates.
- `reverse_engineering/binky_location_extraction_evidence.json`: exact
  registrations, initializer bytes, collection bits, exits, arrival cases,
  bounded native instructions, field formulas, coverage limits, input hashes.
- `tools/extract/extract_binky_locations.py` and
  `tests/test_extract_binky_locations.py`.

From workspace root, use new output paths:

```powershell
python -B tools/extract/extract_binky_locations.py --rom "Tomato Adventure (Japan).gba" --menus tomatotrans-1.1.1/ta_menus_eng.txt --output-dir NEW_OUTPUT_DIR --evidence-output NEW_EVIDENCE.json
python -B -m unittest discover -s tests -p test_extract_binky_locations.py
```

The standard-library script reuses the existing local Thumb decoder. It checks
baseline fingerprint/size, map-table boundary, pointers, bounded list traversal,
actor census, bank ID bounds, initializer guard/loop, arrival formats and unique
keys. It hashes inputs before/after and opens outputs exclusively; a repeat
invocation refuses all preexisting destinations before writing.

**Validation: 10 tests passed.** Synthetic tests cover quantity aggregation,
duplicates, conflicting quantities, cross-map aliases, conditional/renewable
rewards, absent and ambiguous node seeds. Integration tests cover the
representative pickup, all 74 IDs, four initializer variants, Japanese/English
equivalence, CSV/JSON consistency, fingerprint rejection, fresh CLI extraction
and overwrite refusal. No game-wide completeness or new runtime observation
is claimed. Investigation stops at these deliverables.
