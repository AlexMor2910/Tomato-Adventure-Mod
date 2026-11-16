# Translation Toolkit Symbols and Research Leads

## Runtime-confirmed subtraction GY-SUB-16 (2026-10-11)

Evidence: user's manual mGBA report, interpreted against the bounded Thumb disassembly. At `0x08048794`, `sub r1,r1,r0`, r1 was `0x1A` (26), r0 was `0x0A` (10); stepping produced r1=`0x10` (16). At `0x08048796`, `strh r1,[r2,#0]`, r2 was `0x03000BF8`; stepping stored `0x0010`. Subtraction, intermediate result and scratch write are **Confirmed (runtime)** for this Gear-Yo replay. The previously confirmed HP write at `0x08046E02` changed target HP `0x03000A4E` from 24 to 8, a reduction of 16. These are successive user-reported experiments, not a newly supplied continuous console transcript.

The captured battle pre-subtraction value equals the independently confirmed displayed Attack 26. The measured arithmetic is `26 - 10 = 16`; call the 10-point operand **target subtraction quantity**, not Defense. Individual source-field values were not reported. No minigame or RNG modifier is confirmed by this equality. Source tracing and the remaining conditional modifiers are documented in [battle_damage_candidates.md](battle_damage_candidates.md).

## Gear-Yo battle runtime confirmation (2026-10-11)

| Address | Evidence / confidence |
| --- | --- |
| `0x03000BF8` (RAM) | Confirmed runtime calculated damage scratch, 16 for tested Gear-Yo action |
| `0x03000A4E` (RAM), target `0x03000A40` +0x0E | Confirmed runtime target HP: 24 before, 8 after store at `0x08046E02` |
| `0x08048794` / ROM offset `0x00048794` | Confirmed static `sub r1,r1,r0`; next instruction stores scratch. Runtime-confirmed operands 26 and 10, result 16; scratch store at 0x08048796 confirmed |

Record +0x22, selected even +0x28..+0x38, and +0x27 bit 7 feed this static damage path. Runtime does not yet isolate their individual effects. Performance/RNG inputs are not established. See [battle_damage_candidates.md](battle_damage_candidates.md).

## Battle candidate path after negative watchpoint (2026-10-11)

Source: `tools/analyze/ghidra/TraceGimmickBattle.java`; reproducibility, excerpts and limits in [battle_damage_candidates.md](battle_damage_candidates.md). User's read watchpoint at `0x03003F9D` produced no hit; BIOS `0x00000188` was not a hit.

| Address / file offset | Evidence / interpretation | Confidence |
| --- | --- | --- |
| `0x0802BA3A` / `0x0002BA3A` | Reads work +0x69 at `0x03003F9D`, uses percentage arithmetic, stores utility output and calls renderer with VRAM destination. Timing before checkpoint not measured. | Confirmed static reader; display role Probable |
| `0x080485B0` / `0x000485B0`, return `0x0804881C` | Original record +0x22 plus battle-side byte, selected ROM coefficient, target-quantity subtraction, conditional scaling/clamps; writes `0x03000BF8`. | Confirmed static arithmetic; Confirmed runtime Gear-Yo damage output 16; intermediate modifiers unmeasured |
| `0x08046DE6` / `0x00046DE6`, within `0x08046D60` | Verified direct BL to preceding routine; scratch read at `0x08046DEA`, passed to `0x0804B2F0`. | Confirmed static call/handoff; display callee role Probable |
| `0x08046E02` / `0x00046E02`; conditional clamp `0x08046E0A` | `strh r1,[r4,#0x0E]` after subtracting scratch; r4 is `0x03000A40 + 0x38*target`. | Confirmed runtime Gear-Yo target HP write: r4=03000A40, r1=8, HP 24?8 |
| `0x080484CC` / `0x000484CC` | Battle action selector byte plus 2 when auxiliary flag is nonzero; feeds coefficient switch. | Confirmed static adjustment; gameplay meaning Unconfirmed |

No invented gameplay routine names are assigned. Damage/HP confirmation is limited to the user-reported Gear-Yo action. These concrete instruction stops supersede repetition of the negative coefficient-watchpoint probe.

## Gear-Yo runtime evidence (2026-10-11)

Evidence: user-reported manual mGBA 0.10.5 stops, plus read-only checkpoint inspection. See [gimmick_runtime_tests.md](gimmick_runtime_tests.md). No gameplay symbol names are assigned.

| Address / source | New evidence | Confidence / scope |
| --- | --- | --- |
| `0x08075970` / file `0x00075970`; `TraceGimmickCalculations.java` | Gear-Yo, difficulty 1, upgrade 0: base 21, selected coefficient 124, quotient 26 matches displayed Attack. | Confirmed runtime for this case; other Gimmicks/settings and battle damage untested |
| `0x08075ABC` / file `0x00075ABC`; decoded `strh r0,[r7,#10]` | User observed Thumb r0=`0x1A` immediately before the output store. | Confirmed runtime quotient at this stop; raw CPSR/transcript not supplied |
| `0x02014CF8` (P), `0x02014D02` (P+0x0A), EWRAM | At code `0x08075AE8`, user read stored halfword `0x001A` at P+0x0A. P+0 read was `0x000A`, a distinct output field. | Confirmed runtime stored result for this run; addresses are not universal allocations |
| `0x03003F56` (work +0x22), `0x03003F9D` (work +0x69), IWRAM; `TraceGimmickLoader.java` and battle checkpoint | Saved work base byte is 21; selected coefficient byte is 124. Work record non-text bytes match Gear-Yo's original record. +0x69 comes from the statically decoded indexed-pair read. | Confirmed checkpoint values/static provenance; battle reader and gameplay arithmetic not yet established |

That read-watchpoint probe subsequently produced no hit. The next targets are the static battle candidate path documented above; damage, subtraction and HP write are now runtime-confirmed for Gear-Yo; RNG remains unconfirmed.

## Calculation consumers and state writers (2026-10-10)

New evidence from `tools/analyze/ghidra/TraceGimmickCalculations.java` and [gimmick_calculations.md](gimmick_calculations.md). No new gameplay function names are assigned. These static facts strengthen the historical entries below without supplying runtime confirmation.

| ROM bus / file offset | Evidence / purpose | Confidence |
| --- | --- | --- |
| `0x08075970` / `0x00075970`, return `0x08075AEC` / `0x00075AEC` | Complete 136-instruction Thumb body, embedded literal/switch data excluded. r0=low-byte ID, r1=17-byte output pointer. Original `+0x22` plus mutable S[2], then difficulty-selected even coefficient divided by 100, populate menu Attack values. Epilogue returns through a saved address in r0. | Confirmed static buffer/arithmetic/display flow; attack semantics Probable, battle damage Unconfirmed |
| Calls `0x08076E46`, `0x0807715E`, `0x08078604`, `0x08078ABE`, `0x08078D76`, `0x0807997E`, `0x08080EB4` (file offsets bus minus `0x08000000`) | Seven verified Thumb BL calls to `0x08075970`, all pass dynamic menu cache `read32(0x03004FF8+8)+0x5AE8`. Numeric/gauge consumers, not a scalar return chain. No raw constant pointer to target/Thumb-tagged target found at any alignment. | Confirmed static calls; indirect graph remains incomplete |
| `0x08079AE4` / `0x00079AE4`, body ends `0x08079B62` | Adjusts selected state byte S[1] using key masks `0x100/0x200`, ordinary range 1..7; calls meter target `0x08079B78`. Caller at `0x0807929C`; source help labels refer to L/R difficulty adjustment. | Confirmed static writer; difficulty setting Probable |
| `0x08081188` / `0x00081188`, body ends `0x080811CA` | ID/increment in r0/r1; lookup S; write byte S[2], compare against original record `+0x23`, cap after byte truncation. Called at `0x08080D8C` from item action dispatcher. | Confirmed static cap; battery/upgrade progression Probable |
| `0x080742B8` / `0x000742B8`, body ends `0x08074308` | Decimal sprite loop: coordinates r0/r1, integer r2, attribute r3; divide/remainder by 10, digit table `0x08456C70`, sprite target `0x080744FC`. | Confirmed static display path; decimal-library helper roles Probable |
| `0x080744FC` / `0x000744FC`, body ends `0x080745B8` | Coordinates/attributes applied to sprite records, copied into OAM staging IWRAM `0x030014B8`; caller subsequently DMA-copies staging to `0x07000000`. | Confirmed static display sink |
| `0x08081340` / `0x00081340`, body ends `0x08081400` | Fixed-point ratio gauge from numerator/denominator r1/r2, halfword patterns and DMA3 destination derived from r0; consumes result `+4/+6`. | Confirmed static gauge arithmetic/display; Battery meaning Probable |
| `0x08079B78` / `0x00079B78`, body ends `0x08079BFA` | Seven-halfword meter construction/DMA from low-byte selector r1; consumes result `+0x0C`. | Confirmed static meter; Difficulty meaning Probable |

Original `+0x23` now has a confirmed cap operation rather than merely a byte-copy role. Original even `+0x28..+0x38` have a confirmed percentage calculation and a probable difficulty-related interpretation. No AWE/Kaizo or enemy HP consumer is established by these paths.

## Ghidra static evidence follow-up (2026-10-10)

The historical source-only entries below retain their original scope. [ghidra_loader_trace.md](ghidra_loader_trace.md) supplies additional Japanese-ROM disassembly evidence; [ghidra_analysis.md](ghidra_analysis.md) records the input hash and exact reproducible workflow. No new gameplay names or runtime-confirmed semantics are assigned.

| Address / file offset | Source or script location | New evidence and purpose | Confidence |
| --- | --- | --- | --- |
| `0x08065518` / `0x00065518` through return `0x080656C0` / `0x000656C0` | `TraceGimmickLoader.java`, loader seeds; translation `asm/gimmick_text.asm:69-144` | Complete Thumb loader: executable spans end at `0x080655D4` and `0x080656C2`, skipping literal pool `0x080655D4..E4`. Copies original record and derives extended RAM bytes. | Confirmed static instructions; gameplay meanings unresolved |
| `0x0806ACA0` / `0x0006ACA0`; call `0x0806ACFE` / `0x0006ACFE` | `TraceGimmickLoader.java`, targeted caller window | Direct Thumb BL to loader; utility bytes `+1/+5/+4` feed RAM parameter bytes `0x03001AD2..D4`. | Confirmed static caller and argument writes; not an exhaustive caller graph |
| `0x08075970` / `0x00075970` | `TraceGimmickLoader.java`, arithmetic consumer windows | Reads original `+0x22/+0x23`; selects nine even bytes `+0x28..+0x38`, applies integer multiply/divide-by-100 scaling into output halfword `+0x0A`. Computed switch cases seeded from explicit address words. | Confirmed arithmetic; Candidate gameplay scaling, quantity unknown |
| `0x080754B0` / `0x000754B0` | `TraceGimmickLoader.java`, accessor window | Nonzero ID indexes original stride-0x58 record and returns low nibble of `+0x27`; zero ID path returns `0xFF`. | Confirmed static accessor; meaning Unconfirmed |
| `0x080F7B08` / `0x000F7B08` | `TraceGimmickLoader.java`, helper window | Thumb sign-normalizing shift/subtract integer quotient used with divisor 100 by arithmetic consumer. | Confirmed static quotient operation; no gameplay meaning assigned |
| `0x0807565C` / `0x0007565C`; RAM `0x03001EDC`, count `0x030035F0` | `TraceGimmickLoader.java`, lookup-helper window | Searches up to 20 three-byte ID entries per stride-0x60 group starting at group +8; returns matching entry address or zero. Entry +1/+2 feed arithmetic selector/additive byte. | Confirmed static lookup; Candidate owned-Gimmick state |
| `0x03003F34` (IWRAM) and original table `0x0862C250` / `0x0062C250` | Loader and consumer listings in linked trace | Verified literal bases; computed record lookup and pointer `+0x3C` byte-stream consumption. `+0x40..+0x57` additional consumers remain unidentified. | Confirmed static addresses/accesses; stream purpose Candidate |

The original `+0x27` byte load differs from the English patch's unaligned word load. See the linked trace before interpreting retained-code registers. The nine-case selector comes from state returned by `0x0807565C`; difficulty/Kaizo identity needs runtime evidence.

## Naming and confidence

This catalogue describes source declarations and access patterns; original functions generally have research names, not recovered developer symbols. Sources are relative to `tomatotrans-1.1.1/`. ROM entries include CPU bus addresses and file offsets; RAM has no file offset. Confidence definitions and scope are in [translation_project_overview.md](translation_project_overview.md). The full address occurrence inventory is in [memory_map.md](memory_map.md).

## Original routine entry points referenced by patches

| Research name | ROM bus / file offset | Evidence and purpose | Confidence |
| --- | --- | --- | --- |
| GameMemcpy | `0x080F954C` / `0x000F954C` | Multiple patches pass destination/source/count in r0/r1/r2; comments explicitly identify memcpy. | Probable |
| GameMemset | `0x080F95AC` / `0x000F95AC` | Save-info initialization uses fill byte and count. | Probable |
| UtilityCopy | `0x0806A00C` / `0x0006A00C` | Formatter sets shared utility source, destination and byte count before calling. Also in legacy event parser trace. | Probable |
| UtilityTrimStringLength | `0x0806A0D8` / `0x0006A0D8` | Gimmick/default-name formatting computes length in utility byte `+1`. | Probable |
| UtilityFormatNumber | `0x080715A4` / `0x000715A4` | Obtained quantity converted into text for “2x” prefix. | Probable |
| ReadMainScriptFlag | `0x0806AE2C` / `0x0006AE2C` | Save-info routine passes flag IDs `0x28` and `0x2D0` via utility word `+4`, reads byte `+1`. No flag array base known. | Probable |
| PlayDialogueSound | `0x08065FC0` / `0x00065FC0` | Called after sound ID written to utility halfword `+4`. BGM/SFX dispatch relationship unknown. | Probable SFX; Candidate music lead |
| LoadSaveSlot | `0x0802F34C` / `0x0002F34C` | Save slot passed in utility byte `+1`; comment says copies save to EWRAM. | Probable |
| ValidateLoadedSave | `0x0802EC2C` / `0x0002EC2C` | Receives EWRAM save pointer; returns save type. | Probable |
| LoadSavedPlace | `0x080758AC` / `0x000758AC` | Called with slot index; comment associates returned byte with save-relative `+0x285`. | Probable |
| IsItemUsable | `0x08075040` / `0x00075040` | Menu uses returned value to choose enabled/disabled text color. | Probable |
| CanCharacterEquipClothing | `0x080756FC` / `0x000756FC` | Character and clothing ID supplied; filters equipment list. | Probable |
| BattleMessageStateRead/Write | `0x08048574` / `0x00048574`; `0x08048584` / `0x00048584` | Sleep/enemy status-message visibility checks and updates; exact state semantics tentative. | Candidate |
| UpdateBattleFlags | `0x0804A148` / `0x0004A148` | Multiple message routines pass bitmasks; upstream comments uncertain. | Candidate |
| CpuFastSet/CpuSet wrappers | `0x080942E0` / `0x000942E0`; `0x080942E4` / `0x000942E4` | Named by comments and used with BIOS-style transfer flags. | Probable |

## Gimmick record schema and IDs

The focused source audit is in [gimmicks.md](gimmicks.md). It distinguishes original ROM fields, translated text slots and the extended IWRAM work structure. The 50-entry count is the toolkit's supported count; physical table completeness and literal-pool contents still require ROM inspection. Candidate pointer/pair subdivisions below come from an explicitly guessed upstream struct, not verified gameplay types.

Original ROM bus `0x0862C250` (file `0x0062C250`), stride `0x58`, 50 indexed entries. `asm/gimmick_text.asm:1-24` calls its struct layout “guesses”; keep field meanings provisional. `RESTRUCT` text directives and the loader's multiply/copy independently support stride/name offsets. Table end derived as `0x0862D380`. This does not prove no additional unused entries exist.

| Record offset | Size | Meaning / evidence | Confidence |
| --- | --- | --- | --- |
| `+0x00` | 8 | Original embedded name; menu RESTRUCT copies it; translated name lives in GimmickText at `index*0x40`. | Confirmed source layout |
| `+0x08` | 26 | Original description; translated copy starts at `GimmickText + index*0x40 + 0x10`. | Confirmed source layout |
| `+0x22`, `+0x23` | 1 each | Commented `atk`, `maxBattery`; no damage/gauge consumer traced. | Candidate |
| `+0x24` | 1 | Unknown. | Unconfirmed |
| `+0x25` | 1 | Commented `uses`; patched loader masks low 7 bits into work-buffer `+0x70` and shifts the original into `+0x6F`. | Probable uses; high-bit meaning Unconfirmed |
| `+0x26`, `+0x27` | 1 each | Unknown byte and commented flags. Loader prepares an unaligned word load at work-record `+0x27` before branching into unsupplied original code; its width does not establish a four-byte field here. See `asm/gimmick_text.asm:130-133`. | Unconfirmed / Candidate; Confirmed load address |
| `+0x28`–`+0x39` | 18 | Commented nine pairs `levels[9]`; could be difficulty-dependent values. No formula/consumer verified. | Candidate |
| `+0x3A`, `+0x3B` | 1 each | Unknown. | Unconfirmed |
| `+0x3C`, `+0x40`, `+0x48`, `+0x4C`, `+0x50`, `+0x54` | 4 each | Commented pointers; `+0x40` suspected palette; `+0x48/+0x4C` suspected pointer lists. Validate pointed-to types. | Candidate |
| `+0x44` | 4 | Choo-Choo image inserter can write a relocated compressed tileset bus pointer at file `0x0062CC8C`, which is record index `0x1D`, field `+0x44`. See `inserter/images.cpp:780-782,167-180,92-96`. Other record targets remain unknown. | Confirmed source pointer-write site; Probable general image-pointer field |

The game loader at `0x08065518` uses **1-based** IDs; translation menu rows below use zero-based record indices. Conversion `gameID = index + 1` is supported for this loader and obtained-item formatter, not proven universal across all scripts. Tagged obtained Gimmick IDs are decoded as `0xC0 | gameID` by `FormatObtainedItem`. Name evidence comes from `ta_menus_eng.txt:1303-1353`; record addresses below are derived from its source formula, not ROM reads.

## Gimmick loader and consumer cross-references

Added by the focused source audit, 2026-10-09. Numeric entries identify existing routines, patch sites or literal slots; they are not fabricated symbol names. Confirmed means source operands/data flow, not tested gameplay semantics. No original loader caller graph is recoverable from these partial patches alone.

| Existing symbol or source location | ROM bus / file offset | Cross-reference and purpose | Evidence / confidence |
| --- | --- | --- | --- |
| Unnamed routine; prefix patch | `0x08065518` / `0x00065518` | Reads ID; copies `0x58` bytes; replaces work-record name with translated pointer; reads `+0x25`, prepares load at `+0x27`. No `.func` declaration. | `asm/gimmick_text.asm:69-133`; Confirmed instructions, Probable loader role. |
| Retained continuation | `0x0806556C` / `0x0006556C` | Branch target after `ldr r1,[r0]` at work-record `+0x27`; original body absent. | `asm/gimmick_text.asm:130-133`; Confirmed target, behavior Unconfirmed. |
| Loader epilogue replacement | `0x080656B8` / `0x000656B8` | Restores r8/registers after shortened prefix. Region ends at bus `0x080656C2`, file `0x000656C2`. | `asm/gimmick_text.asm:137-144`; Confirmed source range. |
| Loader literal slots | `0x080655D4`, `0x080655D8`, `0x080655DC`, `0x080655E0` / `0x000655D4`, `0x000655D8`, `0x000655DC`, `0x000655E0` | Expected utility, ID, biased table and work-buffer pointers. Slot `DCh` is commented as `0x0862C250-0x58`; no slot is written by this patch. | `asm/gimmick_text.asm:77-92`; Confirmed references, actual values Unconfirmed. |
| Existing helper call | `0x080F954C` / `0x000F954C` | r0=work buffer, r1=record, r2=88; probable memcpy. | `asm/gimmick_text.asm:89-96`; Confirmed call, Probable copy semantics. |
| Existing helper call | `0x0806A0D8` / `0x0006A0D8` | Name pointer/16-byte limit in utility parameters; result goes to work `+0x68`. Does not decode power/flags. | `asm/gimmick_text.asm:107-115`; Confirmed call/result handling; precise trim semantics untested. |
| Name consumer patch in comment-described routine `0x0802B7F0` | `0x0802B868` / `0x0002B868` | Work `+0` pointer and `+0x68` byte feed text renderer; resumes at bus `0x0802B882`, file `0x0002B882`. | `asm/gimmick_text.asm:48-66`; Confirmed accesses; containing routine/comment linkage Probable. |
| Existing renderer call | `0x0802BEF0` / `0x0002BEF0` | Called by preceding name patch; comment says handles length `FF`. Renderer body absent. | `asm/gimmick_text.asm:64-65`; Confirmed target; renderer role Probable. |
| Comment-described battle-name consumer | `0x0804AA5C` / `0x0004AA5C` | Text pointer/stride/length patches at `0x0804AB7C`, `0x0804AAC4`, `0x0804AAD0` (file `0x0004AB7C`, `0x0004AAC4`, `0x0004AAD0`). | `asm/gimmick_text.asm:34-43`; Probable entry role; Confirmed patch sites. |
| Description pointer stores | `0x0804DE32`, `0x0804DF46`, `0x0804DFCA`, `0x0804E7D0` / `0x0004DE32`, `0x0004DF46`, `0x0004DFCA`, `0x0004E7D0` | Write translated instruction pointer into message buffer `+4`, consumed by `battle_message.asm` long-message drawing path. These are patch sites, not four asserted function entries. | `asm/gimmick_text.asm:146-210`; `asm/battle_message.asm:14-86`; Confirmed source accesses. |
| `FormatObtainedItem` | `0x0806B27C` / `0x0006B27C` | Tagged obtained Gimmick ID selects 16-byte translated name, with one-based indexing; no gameplay-record load. | `asm/dialog_item.asm:17-26,64-106`; Confirmed source behavior. |
| Legacy name path, unnamed | `0x0806AD60` / `0x0006AD60` | Bypassed in patched formatter; body and current callers unknown. | `asm/gimmick_text.asm:45-46`; `asm/dialog_item.asm:91-96`; Candidate original role. |
| `MenuStatusGimmickPickWho` | `0x08078C18` / `0x00078C18` | Uses text descriptor `0x084904B8` / `0x004904B8` and character name; does not establish a Gimmick restriction flag. | `asm/menu_gimmicks.asm:5-83`; Confirmed text/name operations. |
| `InsertChooChooAnimationTiles` (host C++ function) | No ROM function address; record pointer slot bus `0x0862CC8C` / file `0x0062CC8C` | Edits translated sign tiles; can relocate compressed tileset and rewrite record `0x1D:+0x44`. Calls existing host helpers `SaveCompressedTileset` and `WriteRelocs`. Original tileset bus `0x08577A1C` / file `0x00577A1C`; palette bus `0x085ED7EC` / file `0x005ED7EC`. | `inserter/images.cpp:754-786,167-180,92-96`; Confirmed source operands/data flow, runtime graphics association Probable. |

Extended IWRAM work fields are described in [gimmicks.md](gimmicks.md#ram-work-structure-versus-original-rom-record): source name pointer at `+0`, name length at `+0x68`, shifted uses-related byte at `+0x6F`, masked byte at `+0x70`. The last three lie outside an original `0x58`-byte ROM record. No maximum-power, RNG, special-effect, character-restriction or Kaizo-specific function has been identified by this audit.

## Other data formats

- **Menu text descriptor**: pointer32 at `+0`; width byte at `+4`, height at `+5`, translation clear-width override at `+6`, alignment flags at `+7` (bit 0 centers buffered renderer). `InsertMenuStuff2` changes width and clear width; VWF readers use the full metadata word. Fields are Confirmed replacement-source behavior, original unused-byte meanings remain unknown.
- **Enemy/attack name field**: translated `{little-endian bus pointer32, length8, zero8, zero8, zero8}` replaces original `char[8]`. Remaining record fields retain original data. `text.cpp:676-828` and `battle_enemies.asm` provide Confirmed source evidence.
- **Battle command 43 message**: original pointed-to 16-byte string, or translated `FF copyLength alignment textLength ...`. Inline text is at packet `+4` for lengths up to `0x1A`. Longer form is `FF 08 alignment length 00 00 ptr32` (ten bytes); copying eight bytes after the header places pointer at RAM buffer `+4`. See `text.cpp:903-931` and `BattleScript43Message` for Confirmed encoding/decoding.
- **Dialogue text**: `FF` introduces display control codes, `FE` kanji; `FF 80` inserts a generated number, `FF 81`–`84` names, `FF 85` an obtained object name. `notes/SCRIPT.md` describes these, not the story-event interpreter. `FF 1A/1B` sound-related meanings remain Candidate.
- **Event bytecode**: legacy FD/FE command families and possible `0x1C`/`0x10` record layers are Candidate structures only. The toolkit translates pointer targets; it does not provide a complete event assembler or opcode schema.
- **Maps**: tileset pointer stride 4; three chipset pointer slots per map at stride 12. A chip encodes four 16-bit tile entries; chipmaps encode 16-bit chip indices. Palette, tilemap and compression details are implemented in `images.cpp`, `tiles.cpp`, `lz77.cpp`, `rle.cpp`; no music field is demonstrated.
- **Character data**: IWRAM `0x03001EDC`, stride `0x60`; separate battle statuses at `0x03000938`, stride `0x84`. Do not conflate persistent character level `+0x4A` with battle status or an AWE segment value.

## Mod objective entry points

| Objective | Existing evidence | What is still missing | Confidence |
| --- | --- | --- | --- |
| Music | Dialogue sound byte `0x03003E8B`, sound call `0x08065FC0`; `notes/SCRIPT.md` sound flag codes. | Engine, song table, map BGM assignment, event overrides, sequence/bank formats. | Candidate leads |
| Gimmick balance/Kaizo | Original Gimmick table/loader and proposed fields above; Kaizo dialogue `0E6`, `0ED`–`0FA`. | Verified power/RNG/difficulty consumers; actual reward thresholds; distinction between Binky progression and minigame difficulty. | Probable record base; Candidate gameplay fields |
| AWE | Menu descriptor bus `0x08490590` / file `0x00490590`; fixed battle label `BattleMenuText+0x12`; exchange strings. | Gain/max/segment arithmetic and character-specific storage. “Cool” in patch names is a display label. | Confirmed labels; Unconfirmed mechanics |
| AWE-to-Binky exchange | Dialogue IDs `4A9`–`4BB`: full gauge, character choices, variable offers, stock/exhaustion messages. Their pointer slots are listed below. | NPC/event/map and enabling flag; exchange formula, depletion state and Mayonen unlock point. | Confirmed text; Candidate event associations |
| Binky collection counter | UI label pointer slot bus `0x080781DC` / file `0x000781DC`; menu name row `36` under descriptor `0x084903F8`; Kaizo and pickup dialogue. | Unique pickup IDs, save flags, world-vs-traded Binkies, area grouping and counts. Item-name row is not proof of collection storage. | Confirmed text; Unconfirmed collection model |
| Hanzo reward | Hanzo sign maps `002F`, `00DE`, `00DF`, `00E0`, `00E1`, `0168`; dialogue rewards using `[ITEM]`. | Specific pre-Mayonen event, granted Gimmick ID and eligibility tests. Signs do not identify reward scripts. | Confirmed graphics IDs; Candidate story relationship |
| Events/progression | Flag reader; `MainScriptHandle2C`; character initialization and save metadata. Overworld/save-place label tables contain Mayonen (row `04`). | Flag bank, event ownership, map-group IDs, reward commands and progression dependencies. | Candidate leads |

## Next evidence to collect

Record input ROM hashes/revisions before any binary analysis. Read and cross-reference the original Gimmick records and loader first, then use the selected dialogue pointer slots below to locate exchange/Kaizo event callers. Dialogue content suggests behavior but cannot establish script conditions. Obtain an assembly symbol listing in a later authorized build to resolve helper placement, and compare source-built output with the existing English patch before layering changes.

## Assembly declaration catalogue

The generated catalogue below covers all `.func` declarations. A first function immediately following a literal `.org` has a source-declared entry; subsequent functions report the containing region only, because emitted instruction/pool lengths and conditionals determine their actual entries. `.autoregion` functions have no assigned address here. Runtime roles suggested by names are Probable until traced.

| Symbol (source name) | Source | Entry bus / file offset or placement | Evidence / confidence |
| --- | --- | --- | --- |

| BattleStatEnemyStatusMsg | `asm/battle_enemies.asm:120` | `0x080502A4` / `0x000502A4` | Confirmed source entry declaration; role Probable. |
| BattleUpdateCoolIndicator | `asm/battle_menu.asm:110` | `0x0804ADE0` / `0x0004ADE0` | Confirmed source entry declaration; role Probable. |
| BattleScript43Message | `asm/battle_message.asm:92` | `0x08042484` / `0x00042484` | Confirmed source entry declaration; role Probable. |
| BattleStatPlayerStatusMsg | `asm/battle_sleep.asm:10` | `0x0804D978` / `0x0004D978` | Confirmed source entry declaration; role Probable. |
| CreditsDrawNextLine | `asm/credits.asm:14` | `0x0802B08C` / `0x0002B08C` | Confirmed source entry declaration; role Probable. |
| CopyString8x12ToVRAM | `asm/credits.asm:177` | `0x0802B43C` / `0x0002B43C` | Confirmed source entry declaration; role Probable. |
| GetNext8x12Char | `asm/credits.asm:245` | `0x0806F9C4` / `0x0006F9C4` | Confirmed source entry declaration; role Probable. |
| CalcLengthAppendWidth | `asm/dialog_center.asm:12` | `0x0806E7EC` / `0x0006E7EC` | Confirmed source entry declaration; role Probable. |
| CalcLengthDialog | `asm/dialog_center.asm:29` | `0x0806E80C` / `0x0006E80C` | Confirmed source entry declaration; role Probable. |
| CalcLengthDialog80Number | `asm/dialog_center.asm:217` | Within replacement region starting `0x0806E80C`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| Calc8x12PixelWidth | `asm/dialog_center.asm:264` | Within replacement region starting `0x0806E80C`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CalcLengthDialog8xName | `asm/dialog_center.asm:294` | Within replacement region starting `0x0806E80C`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| FormatObtainedItem | `asm/dialog_item.asm:17` | `0x0806B27C` / `0x0006B27C` | Confirmed source entry declaration; role Probable. |
| HandleDialog85Item | `asm/dialog_item.asm:139` | `0x0806DBD8` / `0x0006DBD8` | Confirmed source entry declaration; role Probable. |
| CalcLengthDialog85Item | `asm/dialog_item.asm:158` | Build-dependent `.autoregion`; exact entry Unconfirmed | Confirmed declaration; role Probable from source body/name. |
| HandleDialog81Name1 | `asm/dialog_name.asm:8` | `0x0806DB58` / `0x0006DB58` | Confirmed source entry declaration; role Probable. |
| HandleDialog81Name2 | `asm/dialog_name.asm:13` | Within replacement region starting `0x0806DB58`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| HandleDialog81Name3 | `asm/dialog_name.asm:18` | Within replacement region starting `0x0806DB58`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| HandleDialog81Name4 | `asm/dialog_name.asm:23` | Within replacement region starting `0x0806DB58`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| HandleDialog8xName | `asm/dialog_name.asm:28` | Within replacement region starting `0x0806DB58`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| DialogDecideNextLetter | `asm/dialog_speed.asm:3` | `0x0806CCBC` / `0x0006CCBC` | Confirmed source entry declaration; role Probable. |
| DialogAddLetterAndBeep | `asm/dialog_speed.asm:40` | `0x0806CC1C` / `0x0006CC1C` | Confirmed source entry declaration; role Probable. |
| MenuKeyItemsDrawSpecialList | `asm/item_text.asm:124` | `0x0807C268` / `0x0007C268` | Confirmed source entry declaration; role Probable. |
| MenuDrawNameSprites | `asm/menu.asm:8` | `0x08072F70` / `0x00072F70` | Confirmed source entry declaration; role Probable. |
| MenuEquipmentListParams | `asm/menu_equipment.asm:5` | `0x0807A3D4` / `0x0007A3D4` | Confirmed source entry declaration; role Probable. |
| MenuEquipmentDrawList | `asm/menu_equipment.asm:41` | `0x0807A310` / `0x0007A310` | Confirmed source entry declaration; role Probable. |
| MenuEquipmentScrollListUp | `asm/menu_equipment.asm:167` | `0x0807A410` / `0x0007A410` | Confirmed source entry declaration; role Probable. |
| MenuEquipmentScrollListDown | `asm/menu_equipment.asm:229` | `0x0807A470` / `0x0007A470` | Confirmed source entry declaration; role Probable. |
| FriendsMenuDrawSidebarNames | `asm/menu_friends.asm:42` | `0x08072FBC` / `0x00072FBC` | Confirmed source entry declaration; role Probable. |
| MenuStatusGimmickPickWho | `asm/menu_gimmicks.asm:10` | `0x08078C18` / `0x00078C18` | Confirmed source entry declaration; role Probable. |
| MenuItemsDrawList | `asm/menu_items.asm:5` | `0x080778FC` / `0x000778FC` | Confirmed source entry declaration; role Probable. |
| MenuItemsScrollListUp | `asm/menu_items.asm:95` | `0x080779E4` / `0x000779E4` | Confirmed source entry declaration; role Probable. |
| MenuItemsScrollListDown | `asm/menu_items.asm:160` | `0x08077A54` / `0x00077A54` | Confirmed source entry declaration; role Probable. |
| ShopItemsDrawList | `asm/menu_items.asm:224` | `0x0807DED0` / `0x0007DED0` | Confirmed source entry declaration; role Probable. |
| ShopItemsListParams | `asm/menu_items.asm:303` | `0x0807DF7C` / `0x0007DF7C` | Confirmed source entry declaration; role Probable. |
| ShopItemsScrollListUp | `asm/menu_items.asm:339` | `0x0807DFB4` / `0x0007DFB4` | Confirmed source entry declaration; role Probable. |
| ShopItemsScrollListDown | `asm/menu_items.asm:413` | `0x0807E04C` / `0x0007E04C` | Confirmed source entry declaration; role Probable. |
| InitCharData | `asm/name_long.asm:12` | `0x08032C10` / `0x00032C10` | Confirmed source entry declaration; role Probable. |
| CopyCharNameFromBuffer | `asm/name_long.asm:55` | Within replacement region starting `0x08032C10`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CopyCharName8x8ToVRAMClearR1 | `asm/name_long.asm:105` | Within replacement region starting `0x08032C10`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CopyCharName8x8ToVRAM | `asm/name_long.asm:118` | Within replacement region starting `0x08032C10`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| NamingScreenLoadName | `asm/name_long.asm:142` | `0x0802D338` / `0x0002D338` | Confirmed source entry declaration; role Probable. |
| CopyCharNameToBuffer | `asm/name_long.asm:161` | Within replacement region starting `0x0802D338`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| NamingScreenSaveName | `asm/name_long.asm:210` | `0x0802D398` / `0x0002D398` | Confirmed source entry declaration; role Probable. |
| MainScriptHandle2C | `asm/name_long.asm:360` | `0x0803E650` / `0x0003E650` | Confirmed source entry declaration; role Probable. |
| NamingScreenUpdateButtons | `asm/naming_screen.asm:184` | `0x0802D220` / `0x0002D220` | Confirmed source entry declaration; role Probable. |
| NamingScreenCanAddCurrent | `asm/naming_screen.asm:259` | Within replacement region starting `0x0802D220`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| NamingScreenCanAddLetter | `asm/naming_screen.asm:267` | Within replacement region starting `0x0802D220`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| NamingScreenCanAddMore | `asm/naming_screen.asm:304` | Within replacement region starting `0x0802D220`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| NamingScreenUpdateName | `asm/naming_screen.asm:320` | `0x0802D2F0` / `0x0002D2F0` | Confirmed source entry declaration; role Probable. |
| NamingScreenQueueHighlight | `asm/naming_screen.asm:367` | `0x0802E5DC` / `0x0002E5DC` | Confirmed source entry declaration; role Probable. |
| NameScreenUpdateMessage | `asm/naming_screen.asm:445` | `0x0802E578` / `0x0002E578` | Confirmed source entry declaration; role Probable. |
| NamingScreenUpdateCursor | `asm/naming_screen.asm:512` | `0x0802E2CC` / `0x0002E2CC` | Confirmed source entry declaration; role Probable. |
| NamingScreenAddLetter | `asm/naming_screen.asm:613` | `0x0802E00C` / `0x0002E00C` | Confirmed source entry declaration; role Probable. |
| NamingScreenGetLetter | `asm/naming_screen.asm:635` | Within replacement region starting `0x0802E00C`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| SavingLoadSaveInfo | `asm/saving_screen.asm:7` | `0x08075AFC` / `0x00075AFC` | Confirmed source entry declaration; role Probable. |
| SavingRenderName | `asm/saving_screen.asm:217` | Build-dependent `.autoregion`; exact entry Unconfirmed | Confirmed declaration; role Probable from source body/name. |
| ShopUpdateItemDescription | `asm/shop_messages.asm:8` | `0x0807D2E8` / `0x0007D2E8` | Confirmed source entry declaration; role Probable. |
| GetNext8x8Char | `asm/vwf_8x8.asm:10` | `0x0806FA50` / `0x0006FA50` | Confirmed source entry declaration; role Probable. |
| CopyChar8x8ToVRAM | `asm/vwf_8x8.asm:75` | `0x080713D0` / `0x000713D0` | Confirmed source entry declaration; role Probable. |
| Calc8x8PixelWidth | `asm/vwf_8x8.asm:265` | Within replacement region starting `0x080713D0`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CalcFixedStringLength | `asm/vwf_8x8.asm:345` | Within replacement region starting `0x080713D0`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| Handle8x8Code8xName | `asm/vwf_8x8.asm:365` | Within replacement region starting `0x080713D0`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| Calc8x8PixelWidthName | `asm/vwf_8x8.asm:444` | Build-dependent `.autoregion`; exact entry Unconfirmed | Confirmed declaration; role Probable from source body/name. |
| Draw8x8FixedStrIndexed | `asm/vwf_8x8.asm:515` | `0x080748BC` / `0x000748BC` | Confirmed source entry declaration; role Probable. |
| Draw8x8StrSetColorModeR2 | `asm/vwf_8x8.asm:688` | Within replacement region starting `0x080748BC`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CopyString8x8CenterR0 | `asm/vwf_8x8.asm:722` | Within replacement region starting `0x080748BC`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| Draw8x8FixedStrIndexedToVRAM | `asm/vwf_8x8.asm:745` | `0x080749B8` / `0x000749B8` | Confirmed source entry declaration; role Probable. |
| CopyString8x8ToVRAM | `asm/vwf_8x8.asm:845` | `0x08071748` / `0x00071748` | Confirmed source entry declaration; role Probable. |
| CopyString8x8Clear8 | `asm/vwf_8x8.asm:1014` | Within replacement region starting `0x08071748`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CopyString8x8ClearR0 | `asm/vwf_8x8.asm:1019` | Within replacement region starting `0x08071748`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |
| CopyString8x8Clear10 | `asm/vwf_8x8.asm:1028` | Within replacement region starting `0x08071748`; exact entry Unconfirmed | Confirmed declaration; preceding emitted code controls placement. |

## Address aliases and source constants

Aliases are source declarations; local `@` names are qualified by filename. Allocated ROM aliases are translated data, not original Japanese symbols. Scalar name limits and strides are not addresses.

| Alias | Value / expression | Source evidence | Confidence |
| --- | --- | --- | --- |

| `BattleMenuText` (addresses.inc) | `.definelabel BattleMenuText,0x087F0000` | `asm/addresses.inc:2` | Confirmed declaration; meaning per source/comment |
| `GimmickText` (addresses.inc) | `.definelabel GimmickText,0x087F001E` | `asm/addresses.inc:3` | Confirmed declaration; meaning per source/comment |
| `ItemTextName` (addresses.inc) | `.definelabel ItemTextName,0x087F0C9E` | `asm/addresses.inc:4` | Confirmed declaration; meaning per source/comment |
| `ItemTextDesc` (addresses.inc) | `.definelabel ItemTextDesc,0x087F12AE` | `asm/addresses.inc:5` | Confirmed declaration; meaning per source/comment |
| `ClothesText` (addresses.inc) | `.definelabel ClothesText,0x087F15DE` | `asm/addresses.inc:6` | Confirmed declaration; meaning per source/comment |
| `BattleAilmentsText` (addresses.inc) | `.definelabel BattleAilmentsText,0x087F17DE` | `asm/addresses.inc:7` | Confirmed declaration; meaning per source/comment |
| `NamingScreenText` (addresses.inc) | `.definelabel NamingScreenText,0x087F183E` | `asm/addresses.inc:8` | Confirmed declaration; meaning per source/comment |
| `DefaultNamesText` (addresses.inc) | `.definelabel DefaultNamesText,0x087F1980` | `asm/addresses.inc:9` | Confirmed declaration; meaning per source/comment |
| `MechaText` (addresses.inc) | `.definelabel MechaText,0x087F19A0` | `asm/addresses.inc:10` | Confirmed declaration; meaning per source/comment |
| `MBattleEnemyWorkArea` (addresses.inc) | `MBattleEnemyWorkArea equ 0x02038000` | `asm/addresses.inc:15` | Confirmed declaration; meaning per source/comment |
| `MFontClearSize` (addresses.inc) | `MFontClearSize equ 0x02038030` | `asm/addresses.inc:16` | Confirmed declaration; meaning per source/comment |
| `MFontXOffset` (addresses.inc) | `MFontXOffset equ 0x02038032` | `asm/addresses.inc:17` | Confirmed declaration; meaning per source/comment |
| `MFontControlCodeData` (addresses.inc) | `MFontControlCodeData equ 0x02038034` | `asm/addresses.inc:18` | Confirmed declaration; meaning per source/comment |
| `MLongCharNameWorkArea` (addresses.inc) | `MLongCharNameWorkArea equ 0x02038038` | `asm/addresses.inc:19` | Confirmed declaration; meaning per source/comment |
| `MSaveLongNames` (addresses.inc) | `MSaveLongNames equ 0x02038040` | `asm/addresses.inc:20` | Confirmed declaration; meaning per source/comment |
| `@WorkArea` (battle_enemies.asm) | `@WorkArea equ MBattleEnemyWorkArea` | `asm/battle_enemies.asm:11` | Confirmed declaration; meaning per source/comment |
| `@AilmentStride` (battle_enemies.asm) | `@AilmentStride equ 0x18` | `asm/battle_enemies.asm:15` | Confirmed declaration; meaning per source/comment |
| `@AilmentStride` (battle_sleep.asm) | `@AilmentStride equ 0x18` | `asm/battle_sleep.asm:2` | Confirmed declaration; meaning per source/comment |
| `@ItemTextPtr` (battle_spoils.asm) | `@ItemTextPtr equ 0x08639CAD` | `asm/battle_spoils.asm:2` | Confirmed declaration; meaning per source/comment |
| `@ItemTextLen` (battle_spoils.asm) | `@ItemTextLen equ 4` | `asm/battle_spoils.asm:3` | Confirmed declaration; meaning per source/comment |
| `@FoundTextPtr` (battle_spoils.asm) | `@FoundTextPtr equ 0x08639CB1` | `asm/battle_spoils.asm:4` | Confirmed declaration; meaning per source/comment |
| `@FoundTextLen` (battle_spoils.asm) | `@FoundTextLen equ 6` | `asm/battle_spoils.asm:5` | Confirmed declaration; meaning per source/comment |
| `@NameLen` (battle_spoils.asm) | `@NameLen equ 0x10` | `asm/battle_spoils.asm:8` | Confirmed declaration; meaning per source/comment |
| `@WidthIndex` (dialog_center.asm) | `@WidthIndex equ 0x08649D4D` | `asm/dialog_center.asm:5` | Confirmed declaration; meaning per source/comment |
| `@WorkArea` (dialog_item.asm) | `@WorkArea equ MBattleEnemyWorkArea` | `asm/dialog_item.asm:6` | Confirmed declaration; meaning per source/comment |
| `@TutorialTextLength` (gimica_tutorial.asm) | `@TutorialTextLength equ 48` | `asm/gimica_tutorial.asm:1` | Confirmed declaration; meaning per source/comment |
| `@NameLen` (gimmick_text.asm) | `@NameLen equ 0x10` | `asm/gimmick_text.asm:26` | Confirmed declaration; meaning per source/comment |
| `@DescLen` (gimmick_text.asm) | `@DescLen equ 0x30` | `asm/gimmick_text.asm:27` | Confirmed declaration; meaning per source/comment |
| `@Stride` (gimmick_text.asm) | `@Stride equ (@NameLen + @DescLen)` | `asm/gimmick_text.asm:28` | Confirmed declaration; meaning per source/comment |
| `@NameLen` (item_text.asm) | `@NameLen equ 0x10` | `asm/item_text.asm:6` | Confirmed declaration; meaning per source/comment |
| `@DescLen` (item_text.asm) | `@DescLen equ 0x30` | `asm/item_text.asm:7` | Confirmed declaration; meaning per source/comment |
| `@NameLen` (mecha_text.asm) | `@NameLen equ 0x18` | `asm/mecha_text.asm:5` | Confirmed declaration; meaning per source/comment |
| `@DescLen` (mecha_text.asm) | `@DescLen equ 0x30` | `asm/mecha_text.asm:6` | Confirmed declaration; meaning per source/comment |
| `@Stride` (mecha_text.asm) | `@Stride equ (@NameLen + @DescLen)` | `asm/mecha_text.asm:7` | Confirmed declaration; meaning per source/comment |
| `@GimmickStatusBlock` (menu_gimmicks.asm) | `@GimmickStatusBlock equ 0x084904B8` | `asm/menu_gimmicks.asm:5` | Confirmed declaration; meaning per source/comment |
| `NameMaxLength` (name_long.asm) | `.definelabel NameMaxLength,7` | `asm/name_long.asm:1` | Confirmed declaration; meaning per source/comment |
| `NameMaxTiles` (name_long.asm) | `.definelabel NameMaxTiles,5` | `asm/name_long.asm:2` | Confirmed declaration; meaning per source/comment |
| `@ButtonText` (naming_screen.asm) | `@ButtonText equ NamingScreenText` | `asm/naming_screen.asm:1` | Confirmed declaration; meaning per source/comment |
| `@ButtonLength` (naming_screen.asm) | `@ButtonLength equ 8` | `asm/naming_screen.asm:2` | Confirmed declaration; meaning per source/comment |
| `@MessageText` (naming_screen.asm) | `@MessageText equ (NamingScreenText + @ButtonLength * 4)` | `asm/naming_screen.asm:3` | Confirmed declaration; meaning per source/comment |
| `@WidthIndex` (vwf_8x8.asm) | `@WidthIndex equ 0x08649C4C` | `asm/vwf_8x8.asm:6` | Confirmed declaration; meaning per source/comment |
| `@@mode` (vwf_8x8.asm) | `@@mode equ 2` | `asm/vwf_8x8.asm:523` | Confirmed declaration; meaning per source/comment |
| `@@mode` (vwf_8x8.asm) | `@@mode equ 2` | `asm/vwf_8x8.asm:754` | Confirmed declaration; meaning per source/comment |

## Gimmick name/index catalogue

Names/index ordering is Confirmed translation source data. Derived record addresses and loader IDs are Probable until verified against ROM contents. Each source row is evidence; there is no claim that a named Gimmick has a confirmed balance field.

| Index | Loader game ID | Name | Original ROM bus / file offset | Translated name bus / file offset | Source | Confidence |
| --- | --- | --- | --- | --- | --- | --- |

| `0x00` | `0x01` | Gear-Yo | `0x0862C250` / `0x0062C250` | `0x087F001E` / `0x007F001E` | `ta_menus_eng.txt:1304` | Confirmed names; Probable ID/address association |
| `0x01` | `0x02` | Kendama | `0x0862C2A8` / `0x0062C2A8` | `0x087F005E` / `0x007F005E` | `ta_menus_eng.txt:1305` | Confirmed names; Probable ID/address association |
| `0x02` | `0x03` | Chomper | `0x0862C300` / `0x0062C300` | `0x087F009E` / `0x007F009E` | `ta_menus_eng.txt:1306` | Confirmed names; Probable ID/address association |
| `0x03` | `0x04` | Origami | `0x0862C358` / `0x0062C358` | `0x087F00DE` / `0x007F00DE` | `ta_menus_eng.txt:1307` | Confirmed names; Probable ID/address association |
| `0x04` | `0x05` | Shell Fist | `0x0862C3B0` / `0x0062C3B0` | `0x087F011E` / `0x007F011E` | `ta_menus_eng.txt:1308` | Confirmed names; Probable ID/address association |
| `0x05` | `0x06` | TwinDragon | `0x0862C408` / `0x0062C408` | `0x087F015E` / `0x007F015E` | `ta_menus_eng.txt:1309` | Confirmed names; Probable ID/address association |
| `0x06` | `0x07` | RabiShoes | `0x0862C460` / `0x0062C460` | `0x087F019E` / `0x007F019E` | `ta_menus_eng.txt:1310` | Confirmed names; Probable ID/address association |
| `0x07` | `0x08` | Bunny Hop | `0x0862C4B8` / `0x0062C4B8` | `0x087F01DE` / `0x007F01DE` | `ta_menus_eng.txt:1311` | Confirmed names; Probable ID/address association |
| `0x08` | `0x09` | Cupid Bow | `0x0862C510` / `0x0062C510` | `0x087F021E` / `0x007F021E` | `ta_menus_eng.txt:1312` | Confirmed names; Probable ID/address association |
| `0x09` | `0x0A` | Judgment | `0x0862C568` / `0x0062C568` | `0x087F025E` / `0x007F025E` | `ta_menus_eng.txt:1313` | Confirmed names; Probable ID/address association |
| `0x0A` | `0x0B` | Electric Eel | `0x0862C5C0` / `0x0062C5C0` | `0x087F029E` / `0x007F029E` | `ta_menus_eng.txt:1314` | Confirmed names; Probable ID/address association |
| `0x0B` | `0x0C` | SlotZooka | `0x0862C618` / `0x0062C618` | `0x087F02DE` / `0x007F02DE` | `ta_menus_eng.txt:1315` | Confirmed names; Probable ID/address association |
| `0x0C` | `0x0D` | Seed Bomb | `0x0862C670` / `0x0062C670` | `0x087F031E` / `0x007F031E` | `ta_menus_eng.txt:1316` | Confirmed names; Probable ID/address association |
| `0x0D` | `0x0E` | Momotaro | `0x0862C6C8` / `0x0062C6C8` | `0x087F035E` / `0x007F035E` | `ta_menus_eng.txt:1317` | Confirmed names; Probable ID/address association |
| `0x0E` | `0x0F` | Mag-Mitt | `0x0862C720` / `0x0062C720` | `0x087F039E` / `0x007F039E` | `ta_menus_eng.txt:1318` | Confirmed names; Probable ID/address association |
| `0x0F` | `0x10` | A-B Glove | `0x0862C778` / `0x0062C778` | `0x087F03DE` / `0x007F03DE` | `ta_menus_eng.txt:1319` | Confirmed names; Probable ID/address association |
| `0x10` | `0x11` | Tail Wag | `0x0862C7D0` / `0x0062C7D0` | `0x087F041E` / `0x007F041E` | `ta_menus_eng.txt:1320` | Confirmed names; Probable ID/address association |
| `0x11` | `0x12` | Dragonfire | `0x0862C828` / `0x0062C828` | `0x087F045E` / `0x007F045E` | `ta_menus_eng.txt:1321` | Confirmed names; Probable ID/address association |
| `0x12` | `0x13` | Fumigator | `0x0862C880` / `0x0062C880` | `0x087F049E` / `0x007F049E` | `ta_menus_eng.txt:1322` | Confirmed names; Probable ID/address association |
| `0x13` | `0x14` | Bee Gatling | `0x0862C8D8` / `0x0062C8D8` | `0x087F04DE` / `0x007F04DE` | `ta_menus_eng.txt:1323` | Confirmed names; Probable ID/address association |
| `0x14` | `0x15` | Super Fan | `0x0862C930` / `0x0062C930` | `0x087F051E` / `0x007F051E` | `ta_menus_eng.txt:1324` | Confirmed names; Probable ID/address association |
| `0x15` | `0x16` | Cyclooka | `0x0862C988` / `0x0062C988` | `0x087F055E` / `0x007F055E` | `ta_menus_eng.txt:1325` | Confirmed names; Probable ID/address association |
| `0x16` | `0x17` | Zap Drum | `0x0862C9E0` / `0x0062C9E0` | `0x087F059E` / `0x007F059E` | `ta_menus_eng.txt:1326` | Confirmed names; Probable ID/address association |
| `0x17` | `0x18` | Popocon | `0x0862CA38` / `0x0062CA38` | `0x087F05DE` / `0x007F05DE` | `ta_menus_eng.txt:1327` | Confirmed names; Probable ID/address association |
| `0x18` | `0x19` | Yokozuna | `0x0862CA90` / `0x0062CA90` | `0x087F061E` / `0x007F061E` | `ta_menus_eng.txt:1328` | Confirmed names; Probable ID/address association |
| `0x19` | `0x1A` | Flame Doll | `0x0862CAE8` / `0x0062CAE8` | `0x087F065E` / `0x007F065E` | `ta_menus_eng.txt:1329` | Confirmed names; Probable ID/address association |
| `0x1A` | `0x1B` | Erupter | `0x0862CB40` / `0x0062CB40` | `0x087F069E` / `0x007F069E` | `ta_menus_eng.txt:1330` | Confirmed names; Probable ID/address association |
| `0x1B` | `0x1C` | Pyramet | `0x0862CB98` / `0x0062CB98` | `0x087F06DE` / `0x007F06DE` | `ta_menus_eng.txt:1331` | Confirmed names; Probable ID/address association |
| `0x1C` | `0x1D` | SneaKar | `0x0862CBF0` / `0x0062CBF0` | `0x087F071E` / `0x007F071E` | `ta_menus_eng.txt:1332` | Confirmed names; Probable ID/address association |
| `0x1D` | `0x1E` | Choo-Choo | `0x0862CC48` / `0x0062CC48` | `0x087F075E` / `0x007F075E` | `ta_menus_eng.txt:1333` | Confirmed names; Probable ID/address association |
| `0x1E` | `0x1F` | Puffer | `0x0862CCA0` / `0x0062CCA0` | `0x087F079E` / `0x007F079E` | `ta_menus_eng.txt:1334` | Confirmed names; Probable ID/address association |
| `0x1F` | `0x20` | UFO-Cast | `0x0862CCF8` / `0x0062CCF8` | `0x087F07DE` / `0x007F07DE` | `ta_menus_eng.txt:1335` | Confirmed names; Probable ID/address association |
| `0x20` | `0x21` | Spider Gun | `0x0862CD50` / `0x0062CD50` | `0x087F081E` / `0x007F081E` | `ta_menus_eng.txt:1336` | Confirmed names; Probable ID/address association |
| `0x21` | `0x22` | Rocket Pak | `0x0862CDA8` / `0x0062CDA8` | `0x087F085E` / `0x007F085E` | `ta_menus_eng.txt:1337` | Confirmed names; Probable ID/address association |
| `0x22` | `0x23` | Sun Beam | `0x0862CE00` / `0x0062CE00` | `0x087F089E` / `0x007F089E` | `ta_menus_eng.txt:1338` | Confirmed names; Probable ID/address association |
| `0x23` | `0x24` | Bouncer | `0x0862CE58` / `0x0062CE58` | `0x087F08DE` / `0x007F08DE` | `ta_menus_eng.txt:1339` | Confirmed names; Probable ID/address association |
| `0x24` | `0x25` | Firehog | `0x0862CEB0` / `0x0062CEB0` | `0x087F091E` / `0x007F091E` | `ta_menus_eng.txt:1340` | Confirmed names; Probable ID/address association |
| `0x25` | `0x26` | SesameTop | `0x0862CF08` / `0x0062CF08` | `0x087F095E` / `0x007F095E` | `ta_menus_eng.txt:1341` | Confirmed names; Probable ID/address association |
| `0x26` | `0x27` | NanaBoard | `0x0862CF60` / `0x0062CF60` | `0x087F099E` / `0x007F099E` | `ta_menus_eng.txt:1342` | Confirmed names; Probable ID/address association |
| `0x27` | `0x28` | BowlingRice | `0x0862CFB8` / `0x0062CFB8` | `0x087F09DE` / `0x007F09DE` | `ta_menus_eng.txt:1343` | Confirmed names; Probable ID/address association |
| `0x28` | `0x29` | Dojo Pup | `0x0862D010` / `0x0062D010` | `0x087F0A1E` / `0x007F0A1E` | `ta_menus_eng.txt:1344` | Confirmed names; Probable ID/address association |
| `0x29` | `0x2A` | Lucky Cat | `0x0862D068` / `0x0062D068` | `0x087F0A5E` / `0x007F0A5E` | `ta_menus_eng.txt:1345` | Confirmed names; Probable ID/address association |
| `0x2A` | `0x2B` | Pop Horn | `0x0862D0C0` / `0x0062D0C0` | `0x087F0A9E` / `0x007F0A9E` | `ta_menus_eng.txt:1346` | Confirmed names; Probable ID/address association |
| `0x2B` | `0x2C` | Fart Horn | `0x0862D118` / `0x0062D118` | `0x087F0ADE` / `0x007F0ADE` | `ta_menus_eng.txt:1347` | Confirmed names; Probable ID/address association |
| `0x2C` | `0x2D` | Love Song | `0x0862D170` / `0x0062D170` | `0x087F0B1E` / `0x007F0B1E` | `ta_menus_eng.txt:1348` | Confirmed names; Probable ID/address association |
| `0x2D` | `0x2E` | StarScope | `0x0862D1C8` / `0x0062D1C8` | `0x087F0B5E` / `0x007F0B5E` | `ta_menus_eng.txt:1349` | Confirmed names; Probable ID/address association |
| `0x2E` | `0x2F` | Hotafant | `0x0862D220` / `0x0062D220` | `0x087F0B9E` / `0x007F0B9E` | `ta_menus_eng.txt:1350` | Confirmed names; Probable ID/address association |
| `0x2F` | `0x30` | Mansnow | `0x0862D278` / `0x0062D278` | `0x087F0BDE` / `0x007F0BDE` | `ta_menus_eng.txt:1351` | Confirmed names; Probable ID/address association |
| `0x30` | `0x31` | ShuriGun | `0x0862D2D0` / `0x0062D2D0` | `0x087F0C1E` / `0x007F0C1E` | `ta_menus_eng.txt:1352` | Confirmed names; Probable ID/address association |
| `0x31` | `0x32` | Shadowreel | `0x0862D328` / `0x0062D328` | `0x087F0C5E` / `0x007F0C5E` | `ta_menus_eng.txt:1353` | Confirmed names; Probable ID/address association |

## Selected dialogue cross-reference seeds

Use these original pointer-slot bus addresses to find event streams that display the selected message. The source text establishes the theme; the slot data establishes where the translation repoints it. Both are Confirmed source facts. Specific unlock/reward/collection semantics and ownership by a map are Candidate until the surrounding executable script is decoded. Original string payload addresses remain unconfirmed here.

| Dialogue ID | Theme | Text source | Pointer-slot ROM bus (file offsets) | Evidence/confidence |
| --- | --- | --- | --- | --- |

| `4A9` | AWE-to-Binky exchange | `ta_script_eng.txt:5060` | `0x081086B0` (`0x001086B0`) | `pointers1.dat:1194`; Confirmed slots/text; Candidate event association |
| `4AA` | AWE-to-Binky exchange | `ta_script_eng.txt:5065` | `0x081086E3` (`0x001086E3`) | `pointers1.dat:1195`; Confirmed slots/text; Candidate event association |
| `4AB` | AWE-to-Binky exchange | `ta_script_eng.txt:5070` | `0x081086C5` (`0x001086C5`) | `pointers1.dat:1196`; Confirmed slots/text; Candidate event association |
| `4AC` | AWE-to-Binky exchange | `ta_script_eng.txt:5075` | `0x08107E9A` (`0x00107E9A`) | `pointers1.dat:1197`; Confirmed slots/text; Candidate event association |
| `4AD` | AWE-to-Binky exchange | `ta_script_eng.txt:5079` | No slot in manifest | `pointers1.dat:1198`; Confirmed slots/text; Candidate event association |
| `4AE` | AWE-to-Binky exchange | `ta_script_eng.txt:5084` | `0x08107EC1` (`0x00107EC1`), `0x08107F1E` (`0x00107F1E`), `0x08108039` (`0x00108039`) | `pointers1.dat:1199`; Confirmed slots/text; Candidate event association |
| `4AF` | AWE-to-Binky exchange | `ta_script_eng.txt:5090` | `0x08107F06` (`0x00107F06`), `0x08108051` (`0x00108051`) | `pointers1.dat:1200`; Confirmed slots/text; Candidate event association |
| `4B0` | AWE-to-Binky exchange | `ta_script_eng.txt:5096` | `0x08108069` (`0x00108069`) | `pointers1.dat:1201`; Confirmed slots/text; Candidate event association |
| `4B1` | AWE-to-Binky exchange | `ta_script_eng.txt:5102` | `0x08107F36` (`0x00107F36`), `0x08108081` (`0x00108081`) | `pointers1.dat:1202`; Confirmed slots/text; Candidate event association |
| `4B2` | AWE-to-Binky exchange | `ta_script_eng.txt:5109` | `0x0810809F` (`0x0010809F`) | `pointers1.dat:1203`; Confirmed slots/text; Candidate event association |
| `4B3` | AWE-to-Binky exchange | `ta_script_eng.txt:5116` | `0x081080BD` (`0x001080BD`) | `pointers1.dat:1204`; Confirmed slots/text; Candidate event association |
| `4B4` | AWE-to-Binky exchange | `ta_script_eng.txt:5123` | `0x081080DB` (`0x001080DB`) | `pointers1.dat:1205`; Confirmed slots/text; Candidate event association |
| `4B5` | AWE-to-Binky exchange | `ta_script_eng.txt:5131` | `0x08107F5C` (`0x00107F5C`), `0x08107F93` (`0x00107F93`), `0x08108101` (`0x00108101`), `0x08108138` (`0x00108138`), `0x0810816F` (`0x0010816F`) | `pointers1.dat:1206`; Confirmed slots/text; Candidate event association |
| `4B6` | AWE-to-Binky exchange | `ta_script_eng.txt:5137` | `0x081081BA` (`0x001081BA`) | `pointers1.dat:1207`; Confirmed slots/text; Candidate event association |
| `4B7` | AWE-to-Binky exchange | `ta_script_eng.txt:5139` | `0x08107F80` (`0x00107F80`), `0x08107FB7` (`0x00107FB7`), `0x08108125` (`0x00108125`), `0x0810815C` (`0x0010815C`), `0x08108193` (`0x00108193`), `0x0812DDD0` (`0x0012DDD0`) | `pointers1.dat:1208`; Confirmed slots/text; Candidate event association |
| `4B8` | AWE-to-Binky exchange | `ta_script_eng.txt:5141` | `0x081081A2` (`0x001081A2`) | `pointers1.dat:1209`; Confirmed slots/text; Candidate event association |
| `4B9` | AWE-to-Binky exchange | `ta_script_eng.txt:5151` | `0x08108027` (`0x00108027`), `0x081081AE` (`0x001081AE`) | `pointers1.dat:1210`; Confirmed slots/text; Candidate event association |
| `4BA` | AWE-to-Binky exchange | `ta_script_eng.txt:5158` | `0x081081C6` (`0x001081C6`) | `pointers1.dat:1211`; Confirmed slots/text; Candidate event association |
| `4BB` | AWE-to-Binky exchange | `ta_script_eng.txt:5164` | `0x081081D2` (`0x001081D2`) | `pointers1.dat:1212`; Confirmed slots/text; Candidate event association |
| `0E6` | Kaizo/Binky reward progression | `ta_script_eng.txt:1001` | `0x080FC681` (`0x000FC681`) | `pointers1.dat:231`; Confirmed slots/text; Candidate event association |
| `0ED` | Kaizo/Binky reward progression | `ta_script_eng.txt:1037` | `0x080FC78F` (`0x000FC78F`) | `pointers1.dat:238`; Confirmed slots/text; Candidate event association |
| `0EE` | Kaizo/Binky reward progression | `ta_script_eng.txt:1044` | No slot in manifest | `pointers1.dat:239`; Confirmed slots/text; Candidate event association |
| `0EF` | Kaizo/Binky reward progression | `ta_script_eng.txt:1048` | `0x080FCD35` (`0x000FCD35`) | `pointers1.dat:240`; Confirmed slots/text; Candidate event association |
| `0F0` | Kaizo/Binky reward progression | `ta_script_eng.txt:1055` | `0x080FCD53` (`0x000FCD53`) | `pointers1.dat:241`; Confirmed slots/text; Candidate event association |
| `0F1` | Kaizo/Binky reward progression | `ta_script_eng.txt:1061` | `0x080FCCE8` (`0x000FCCE8`) | `pointers1.dat:242`; Confirmed slots/text; Candidate event association |
| `0F2` | Kaizo/Binky reward progression | `ta_script_eng.txt:1067` | No slot in manifest | `pointers1.dat:243`; Confirmed slots/text; Candidate event association |
| `0F3` | Kaizo/Binky reward progression | `ta_script_eng.txt:1073` | `0x080FCD5E` (`0x000FCD5E`) | `pointers1.dat:244`; Confirmed slots/text; Candidate event association |
| `0F4` | Kaizo/Binky reward progression | `ta_script_eng.txt:1080` | `0x080FC7BB` (`0x000FC7BB`), `0x080FCCF1` (`0x000FCCF1`) | `pointers1.dat:245`; Confirmed slots/text; Candidate event association |
| `0F5` | Kaizo/Binky reward progression | `ta_script_eng.txt:1083` | `0x080FCD02` (`0x000FCD02`), `0x080FCD3B` (`0x000FCD3B`) | `pointers1.dat:246`; Confirmed slots/text; Candidate event association |
| `0F6` | Kaizo/Binky reward progression | `ta_script_eng.txt:1089` | `0x080FCDDF` (`0x000FCDDF`) | `pointers1.dat:247`; Confirmed slots/text; Candidate event association |
| `0F7` | Kaizo/Binky reward progression | `ta_script_eng.txt:1091` | `0x080FCDED` (`0x000FCDED`) | `pointers1.dat:248`; Confirmed slots/text; Candidate event association |
| `0F8` | Kaizo/Binky reward progression | `ta_script_eng.txt:1093` | `0x080FCDC5` (`0x000FCDC5`) | `pointers1.dat:249`; Confirmed slots/text; Candidate event association |
| `0F9` | Kaizo/Binky reward progression | `ta_script_eng.txt:1098` | `0x080FCD1A` (`0x000FCD1A`) | `pointers1.dat:250`; Confirmed slots/text; Candidate event association |
| `0FA` | Kaizo/Binky reward progression | `ta_script_eng.txt:1113` | `0x080FCD26` (`0x000FCD26`) | `pointers1.dat:251`; Confirmed slots/text; Candidate event association |
| `16E` | Binky pickup message | `ta_script_eng.txt:1538` | `0x080FDE4E` (`0x000FDE4E`), `0x0811E3F9` (`0x0011E3F9`) | `pointers1.dat:367`; Confirmed slots/text; Candidate event association |

## Target subtraction source writers (bounded static follow-up)

| Address / ROM offset | Evidence | Confidence |
| --- | --- | --- |
| `0x080418C0` / `0x000418C0`, store `0x080418F4` | Two bytes from incoming cursor become target +0x14; advanced cursor saved to context pointer array | Confirmed static writer; input-stream setter Candidate; particular replay writer Unconfirmed |
| `0x08041CDE` / `0x00041CDE` | Zero store to target +0x18 during reset | Confirmed static |
| `0x080498BC`, `0x080498FA`, `0x08049926` / bus minus `0x08000000` | Scoped block clears +0x18 or adds/removes twice byte [r7+8] | Confirmed static operations; source/meaning unresolved |
| `0x0804876C`, `0x0804876E` / `0x0004876C`, `0x0004876E` | Read target +0x18 and +0x14 to form bounded subtraction quantity | Confirmed static source; combined operand 10 Confirmed runtime |

See [battle_damage_candidates.md](battle_damage_candidates.md); no Defense/status name is assigned.
