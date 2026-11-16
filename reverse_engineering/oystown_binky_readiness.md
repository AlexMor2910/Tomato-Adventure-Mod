# Oystown Binky exchange readiness

**Latest status:** Oystown arrival, introduction and one full-AWE exchange are
user-confirmed runtime successes. The original readiness table below is
historical; newer findings and artifact verification follow at the end.

Read-only investigation and environment preparation. No runtime experiment or
progression/party/AWE modification was performed. Confidence applies to each
specific fact, not to the requested gameplay state as a whole.

| Requirement | Evidence | Confidence / limitation |
| --- | --- | --- |
| Oystown node | `ta_menus_eng.txt`, BLOCKFIXED `49F61C`, row `08` names Oystown. | Confirmed source name/index. |
| Arrival | Switch `0x08088B04`, index 8 -> `0x08088BC8`; literal `0x08088BD4` supplies script `0x08130E4E`. Bytes `FE 7D 04 01 ...` encode map `0x0104`. | Confirmed static selection/bytes; Oystown arrival interpretation Probable pending manual entry. |
| Entry route | Node 7 left: `0x0808914C` tests flag `0x27`; `0x0808915A` returns node 8 if nonzero. Node 8 right at `0x0808922C` tests the same flag and returns 7. | Confirmed static route check. Story prerequisites and missing arrival initialization unresolved; not a safe skip recipe. |
| Other routes | Node 9 right `0x08089244` tests `0x28`, returns 8 at `0x08089252`. Node 8 left `0x08089164` tests `0x28`, returns 9; up `0x08088EC8` tests `0x28`, returns 16. | Confirmed static checks, not proof of story coherence. |
| Flag representation | Main bit bank `0x030032E7`: flag `0x27` is byte `0x030032EB`, mask `0x80`; flag `0x28` is `0x030032EC`, mask `0x01`. | Confirmed static accessor arithmetic; no edits proposed. |
| Party | `asm/menu_friends.asm` reads party size at `0x030035F0`; `symbols.md` documents character records `0x03001EDC`, stride `0x60`, and separate battle records `0x03000938`, stride `0x84`. | Confirmed source size and documented static record layout. Alessa identity field, active battle membership, join initialization and all side effects remain Unconfirmed. A single ID write is not justified. |
| AWE | `symbols.md` identifies label descriptor `0x08490590` and exchange messages, but no verified current/max storage or arithmetic. | Address, encoding, maximum, persistence and full-gauge test Unconfirmed. No numeric initialization proposed. |
| Exchange | Messages `4AA`/`4B8` require full AWE; `4B9` reports no full gauges; `4AC`/`4AE`-`4B4` select characters; `4B5` offers a variable quantity; `4BA`/`4BB` report stock/exhaustion. Original message pointer operands include `0x081086E3` (4AA) and `0x08107E9A` (4AC). | Confirmed translation text/pointer evidence; actual eligibility code, Oystown NPC location, story flags, stock/currency/inventory requirements unresolved. Alessa has not been proved mandatory for the exchange. |
| Checkpoints | Offline inspection found nine unique PNG checkpoint contents; maps `0001`, `0003`, `0008`, `0030`, `005C`, nodes 0/1/3, character-group count 1. Root `entry-stop.ss0` hash `d700a4a002adcc9554064b03b36510a4589ce15fc1668988d27c940bbe999a29`, map `0030`. | Confirmed saved bytes, not live reads. No suitable Oystown/Alessa/full-AWE checkpoint identified. Existing raw battery saves were preserved, not imported or treated as validated checkpoints; EEPROM decoding/selection remains unresolved. |

Environment: `reverse_engineering/mgba/isolated_oystown_binky/`, copied mGBA
0.10.5 and unmodified English baseline SHA-256
`8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`.
No checkpoint selected. The requested gameplay state has not been achieved.
Use a naturally progressed baseline checkpoint to preserve join and story effects;
normal gameplay is required if no such checkpoint can be supplied. Arbitrary route,
party, or AWE writes cannot establish coherent state from the available evidence.

Next single manual action: if the user's current normal-game session is already
immediately before Oystown entry, read `r/1 0x030035F0` while paused and return the
result with the visible party/location description. Otherwise report the current
location without moving or editing state. This establishes a starting point before
choosing further bounded analysis, not proof of all readiness conditions.

## Validated shortcut and exchange (reported 2026-10-13)

The user navigated the overworld after route flags 24–27 were enabled with combined
mask F0 (0B→CB→FB at 030032EB, unrelated bits preserved), entered Oystown normally
from Lab 3, and observed its original introduction including the Binky exchange
intro. No apparent errors/freezes occurred. With Alessa's persistent charge at
03001F94 set to 40 hex, one exchange accepted full AWE, added one Binky and reset
the gauge. **User-confirmed runtime**, limited to this successful transaction.
The earlier table's unconfirmed party/AWE/arrival status is superseded for this
tested scenario. Full charge and initialization are substantiated in the AWE and
recruitment reports.

Read-only inspection confirms actual root checkpoints `before_oystown.ss0` and
`after_exchange_oystown.ss0`. They have matchingrecruitmentROMidentity, party31,
preservedthreeGimmicks androuteFB. Preentry: map00DF/node07,1F4clear,charge05;
postexchange: map0104/node08,1F4set,charge00. The finalsavedcharge00 is newly
inspectedstatic evidence, not a consolemeasurement inventedfromtheuserreport.
Binkyfield/count is stillunmapped;oneadded is userobservation. No separate
postintroduction/preexchangecapture was found. Hashes/exactpaths andverified
formatdetails are in [the exchange/completion report](experiments/oystown_binky_exchange.md)
and [evidence](experiments/oystown_completion_evidence.json).

The successful party reached the tested functionality with 171/117 and earlier
boss/reward markers clear, Toy Parts 00 and variable 3C 00. Do not inject historical
flags to repair demonstrated success. Stock/exhaustion, repeat exchanges, Kaizo
rewards, physical save/reload and later story dependencies remain unresolved.
This is an experimental shortcut, not fully legitimate progression. Preserve
the original exchange code and successful control; do not replay Mayonen recruitment.

Prefer the pre-entry capture for completion, preserving its unconsumed introduction.
Missing core rewards are Dojo Pup, Puffer, SneaKar and RabiShoes. Recommend an
unchanged disposable checkpoint reload and intro reproduction first, then
separately preflighted atomic grants. No emulator action is requested now.
All 86 current protected artifacts remain unchanged, including the earlier environment.
