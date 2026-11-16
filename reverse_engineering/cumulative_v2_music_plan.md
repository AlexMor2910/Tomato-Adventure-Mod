# Cumulative v2 music plan and findings — 2026-10-28

**Cumulative v2 — Incomplete Experimental Build.** Implemented improvement:
87 confirmed room selectors and one ordinary-music restore operand, covering
all five requested area families. Three alternate records still lack proven
active-entry provenance. Do not claim exhaustive region coverage or runtime success.

## Inputs and evidence

Independently read v1's manifest, complete 194-byte ledger, BPS and actual ROM.
Rebuilt v1 in memory using its unchanged source pipeline; bytes match. The old
independent verifier passes, including 2,304 Attack comparisons. V1 is 8 MiB,
SHA-256 `1a605f633dd483d8f7b47bd439690a77b9827e81a0ea641def86f5451e87201f`.
Japanese and English originals match their protected reported fingerprints.
No historical source, manifest, ROM, save or extracted asset was edited.

Sources reused: AGENTS.md, modding plan, historical handoffs (especially 3 and
the sprite closeout), v1 investigation/README, Mayonen experiment/source,
map_extraction.md, map_extraction_evidence.json, all 494 catalog records,
864 retained directed transitions, translation text/pointer lists and original
map records. Existing background PNGs were reviewed; no sprite work or new map
extraction was performed. Local review sheets compose only retained PNGs.

The user explicitly confirmed that “Captain Grocko Ship” means translated
Sunken Ship/Cap'n Garco, and “The Vault” means Soy Bank's Secret Safe.
“Oops Mannor” is retained as the requested track name; the original translated
location-title table calls its source Oops Manor, Japanese メゾンドウープス.

## New title-field proof — Confirmed static

File `0062D3E4`, 494 records, stride `1C`. Byte +2 contains a location-title
index in its upper six bits; lower two bits are separate flags. This is not a
new inference from numerical map order:

- Bus `08033E12..08033E1C` loads record+2, shifts right two, adds one, writes
  RAM `03001B25` when the arrival title-display flag is set.
- `0806BBBC..0806BBD4` masks the title-display byte with 7F, subtracts one,
  multiplies by four and indexes the original pointer list at bus `08649A08`.
- `ta_menus_eng.txt` directive `POINTERLIST 649A08 04 24 31` provides the actual
  translated titles for that table. Zero title fields on interior records do
  **not** independently establish Spillage ownership; graphics and script/exit
  evidence are required there.

These native windows match Japanese, English and v1 byte-for-byte. Native byte
hashes and direct music-handler CFGs are retained in local `music_evidence.json`.
All addresses below are ROM bus addresses unless explicitly called file offsets;
file offset equals bus minus `08000000`.

## Destination tracks

| Requested track | Selector | Playback ID | Authored reference |
|---|---:|---:|---|
| Pokypine Forest | 0D | D5 | Maps0008/000C title1, Pokypine Wood; prior user identification of selector0D |
| Mayonen | 07 | CF | Map0048 title3, Mayonen Land; prior user audible confirmation |
| Namp Lagoon | 24 | EC | Map0060 title4, NampLagoon; node6 arrival script08130E34 |
| Oystown | 10 | D8 | Maps0104/01EC title5; original overworld arrivals |
| Oops Mannor | 08 | D0 | Map0038 title15, Oops Manor; original manor background and NPC dialogue |

Selectors and titles were read from actual original map records, not inferred
from soundtrack order. Nearby maps sharing a selector are supporting context,
not independent proof of a song name. All references remain unmodified. The
normal playback path at `08065FD4` adds decimal200 to RAM selector `03001972`
before `08092E70`. Map selection at `0803F824..0803F894` reads byte+5 &3F;
the separate high-bit handling at `08033E48..54` is preserved.

CSV: `cumulative_v2_music_tracks.csv`, including original script roots and
remaining audible-test limits. Apart from Mayonen/Pokypine's historical user
observations, these are original named-map **static** soundtrack anchors.

## Confirmed rooms and boundaries

Every included row in `cumulative_v2_music_rooms.csv` combines authored identity
with graphics/resource and script/transition evidence. No inclusion uses only
adjacency or a common song value. Generic interior names are left blank.

| Requested region | Confirmed room IDs | Count | Replacement |
|---|---|---:|---:|
| Dropper Village | 0001–0007,001D | 8 | 0D |
| Mayonen Caverns | 001E–002B,002E | 15 | 07 |
| Captain Grocko Ship | 0099–009C,00E2–00FA | 29 | 24 |
| Oyster Sewers | 008F–0098,0169–016C | 14 | 10 |
| The Vault | 0124–012B,0150–0157,015B,01E7–01EA | 21 | 08 |

**Village:** actual node0 arrival0003 identifies The Spillage. Translated
dialogue identifies the tomato-hating Droppers living there. Reviewed retained
backgrounds show its exterior and house/shop interiors. The ordinary exit
component is exactly0001–0007/001D. Forest0008, system0000 and scripted departure
005C are excluded. Alternate village-looking records012C/0158 are not silently
classified as active village rooms.

**Caverns:** 001E/001F explicitly select title14, The Mayo Hole; 001E's original
identity has user confirmation. The unique cave tileset at bus081B6628 is shared
by exactly001F–002B. The entry has tileset081B317C and the bridge room002E has
081BA098; retained backgrounds and cave palette/exit connections establish the
same location. The ordinary component is exactly these15 rooms. This proves
additional rooms0023–0029, not merely the seven old candidates. The retained
unsupported PNG status for several rooms reflects missing initial supplemental
tiles, not missing ROM records; no missing pixels were guessed or re-rendered.
002C/002D are different empty/interior resources and remain unchanged.

**Ship:** title19 at00E2 identifies Sunken Ship. Messages712–717, referenced by
actual ship scripts, identify Garco's party and five diary entries. The entire
unique ship tileset bus081C59FC is used by exactly the29 listed rooms. Reviewed
backgrounds show cabins, corridors, shifting floors, portrait puzzles and event
rooms; the authored exit graph links these to the ship entrance. Ouch Dome0089–
008E, Namp maps0081–0087/00FD–00FE and Lagoon Station0062 are excluded, even
where the broader graph connects them. This boundary uses distinct titles,
graphics and content, not just an exit-component flood fill.

**Sewers:** title1B at008F/0094 and title1C at0095/0098 identify Sewers1/2.
Retained backgrounds and unique sewer graphics distinguish them from Oystown's
streets/buildings. Four additional lower channel views0169–016C share the second
sewer resource. Actual Oystown scripts transfer into these at file10562E,
10582A,105975,105ACC; their registered scripts transfer back to010C–010F at
105D77,105DC1/105E0B,105E4E/105E98,105EE2. Destination operands and backgrounds
were independently read. Town maps0104,010B–010F and0105 remain unchanged.
Record016D resembles a sewer channel but has no proven incoming entry and is
excluded pending that proof.

**Vault:** title27 at0124 identifies Secret Safe; user resolved the requested
alias. Original bank/special-juice dialogue44D–44F and safe/key puzzle messages
17D/184/185/B72/B73 corroborate the setting. Gold safe tileset bus082266D4 is
used by exactly these21 records, including the blue vestibule0153, which is
physically connected between bank007D and vault0150. Retained backgrounds and
ordinary exits establish the puzzle rooms/treasure halls. Confirmed scene
transfers additionally link0124/0125/0128/0129/012A/012B to01E7–01EA,0154,
0156 and0157: file12C89A/12C8AE/12C8C8/12C8DC/12C8F4/12C908/12C944/
12C982/12C9C0. File100557 links0127→0157;130842 returns0156→0128;
12FBF5 links0157→015B, with12FC0F returning to0127. Ordinary exit0156→0155
accounts for the otherwise isolated side room. Bank007D, subway009D and later
story destination00BC are excluded. Record0158 is a village-looking alternate
with an outgoing exit to0127 but no proven incoming entry; it stays unchanged.

## Music commands and local override decisions

FE dispatch table is file0062B8B4; argument-size table0062B736. Native handlers
were compared against the unmodified originals:

| Command | Native entry | Arguments | Established behavior |
|---|---|---|---|
| FE A7 | 0802653C | selector byte | Store03001972, immediately play selector+200 |
| FE A8 | 08026578 | selector byte | Same relevant selector/start sequence as A7 |
| FE A9 | 080265B4 | selector byte | Store selector; call08065FF4 with timing16, which uses8 after shifting |
| FE AB | 08026608 | none | Stop current selector via08066024; stop IDs0–199 via0806609C; set selectorFF |

FEAA is a timing-based fade helper without a new selector. FEAC/AD/AE stop the
lower sound-ID set; FEAF stops the current selector and sets event state. None
is globally modified. FE2D's operand goes to030018F0/0806716C, not this music
selector path, and is left intact.

For all87 confirmed rooms, registration roots include defaults, rectangles,
ordinary interactions and actor initializers. A bounded conservative pointer
closure follows script-range operand pointers, calls/branches and inline actor
continuations, stopping at returns and map transfers. It intentionally includes
false paths; a discovered hit is not automatically a feasible runtime event.
No root budget was exhausted. The only encountered FD84 forms stage fixed
primary movement opcodes2D/3B; they do not stage FE music commands. Their native
decoder and exact raw arguments are retained. Global event continuation contracts
and arbitrary native-script reachability are not exhaustively solved here.

| Context | Command address | Original | Action |
|---|---|---|---|
| AWE lesson start, map0024 default08128D5A | 08128D76/78 | FEAB; FEA904 | Preserve deliberate temporary cue |
| AWE lesson after training battle | 08128E7A/7C | FEAB; FEA904 | Preserve deliberate temporary cue |
| AWE lesson return to ordinary area | 08128F08/0A | FEAB; FEA90D | Change only file00128F0C,0D→07 |
| Ship disco pearl story sequence | 08117C21 | FEA709 | Preserve intentional disco cue; message778 identifies disco pearl |

The AWE scene window08128D5A..08128F48 was decoded linearly using actual command
lengths; the return commandFD7C is at08128F14. The restore operand is thus a
specific ordinary-area restore, not a replacement of the lesson's special music.
No battle descriptor, boss music, victory cue, handler or global selector is
changed. The normal map reinitialization path rereads each room's new selector;
battle/re-entry runtime timing still requires user testing.

## Exact proposal and construction

`cumulative_v2_music_plan.json` records88 guarded one-byte operations:87 map
selectors and the AWE restore. It includes old English-baseline bytes, current v1
bytes, bus/file addresses, map/area, meaning, confidence and evidence. V1 already
contains001E→07, so only86 additional map bytes plus one override differ from v1.
No overlapping or contradictory operation is allowed. Upper two metadata bits
are preserved. All four previous feature groups are reused verbatim.

Canonical construction starts from the hash-gated English baseline, reuses v1's
non-music operations unchanged, and applies this music plan. An independent
incremental build from hash-gated v1 must match every byte. New output has281
differences from English,87 from v1. No old ROM or patch is overwritten.

Independent verification uses separately encoded room/selector sets and the
documentary CSV; it does not import the v2 builder, planner or traversal. Restoring
only its approved87 v1-to-v2 differences must reproduce exact v1 and pass the
existing independent v1 verifier. Both baseline and incremental BPS decoders must
reproduce v2. Checks cover every map's other metadata and upper bits, intentional
cues, excluded candidates, full-file differences and all prior feature groups.

## Precise remaining blockers

| Record/context | Missing fact | Evidence examined | Smallest follow-up | Decision |
|---|---|---|---|---|
| 012C, village-looking alternate | Any normal-play incoming entry and whether this is a village or Vault illusion/debug copy | Shared village tileset, original0E music, placeholder/default roots; no ordinary incoming edge or literal FE7C/7D/FD74 destination in field scripts0F9000..13D1EC | Bound saved/dynamic map-destination writers for the relevant Vault scene; alternatively a user-observed natural entry identifying012C | Omitted |
| 0158, village-looking alternate | Active incoming path from Vault puzzle/story, if any | Outgoing exit to0127, village graphics, original0E; no ordinary incoming/literal transfer found | Resolve the0127 puzzle's indirect/saved destination writers; user natural-entry observation if needed | Omitted |
| 016D, sewer view | Whether this is an active Oystown channel or unused variant | Same sewer tileset as0095/0169–016C, original0E; registered default/interaction inspected; no incoming ordinary/literal transfer | Bound Oystown saved-destination writersFD73/74/75 for channel transitions; user natural-entry observation if needed | Omitted |
| Event closure | Exhaustive feasible contexts for global continuations/native effects | Bounded registered-root closure and known music handlers, no budget exhaustion; false paths retained | Context-sensitive continuation audit only where a manual mismatch is observed, rather than global interpreter edits | No speculative override edits |

All five destinations are established. The unresolved issue is exhaustive room
and context coverage, not a missing guessed soundtrack number. The build is a
substantial improvement over v1 and is intentionally labeled incomplete.
