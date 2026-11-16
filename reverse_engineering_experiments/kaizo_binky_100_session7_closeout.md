# Kaizo 100-Binky runtime closeout - Session 7

2026-10-15. **COMPLETE: 24/24 rewards, user-confirmed runtime success.**

## Evidence attribution

The user supplied the Session 7 milestone report in this conversation. This document records that report; it does not invent screenshots, console transcripts, an independently inspected final checkpoint or new emulator results. The ROM was independently rehashed during this static session. Historical construction output README/manifest may still say runtime untested: those are preserved construction-time records; this closeout supplies the newer runtime status.

ROM: `tools/patch/output/kaizo-binky-100-438325e1b0dd4d74a3eda1d9672f9fde/kaizo_binky_100.gba`  
SHA-256: `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`.

## Completed principal objective

| Stage | Prerequisite | Newly acquired rewards | Result |
|---|---|---|---|
| Before Hanzo Lab 4 | None of the four Hanzo gates | UFO-Cast, Lucky Cat | PASS, user-confirmed |
| Hanzo Lab 4 | 0x22B | Cyclooka, Rocket Pak, Kendama, Bouncer | PASS, user-confirmed |
| Hanzo Lab 5 | 0x22C | Bee Gatling, Pyramet, Fart Horn, Origami | PASS, user-confirmed |
| Hanzo Lab 6 | 0x22D | Popocon, BowlingRice, Bunny Hop, Shadowreel, SlotZooka | PASS, user-confirmed |
| Last Hanzo Lab 1 | 0x096 | Flame Doll, TwinDragon, SesameTop, Judgment, Mansnow, Dragonfire, Momotaro, StarScope, Choo-Choo | PASS, user-confirmed |

The user reports that the awarded Gimmicks registered and functioned in tested gameplay. Earlier stages included direct inventory/menu checks; later rewards were explicitly reported functional. This is principal acquisition/functionality coverage, not measurement of every battle or every numerical threshold boundary.

The user decided to retain the current order and distribution of all 24 Gimmicks, including the nine after the final prerequisite. No further Kaizo development or reward redistribution is planned.

## Native 94-Binky acquisition - runtime PASS

User-reported baseline: preserved post-Cyclooka checkpoint, six cumulative donations, no carried Binkies; ordinary inventory count 03 and records `27 01 0D 01 5F 01 00 00`. The prior static investigation identified the two post-Cyclooka workspace files as clean; this session does not identify an unreported final checkpoint.

The user entered through a normal Hawker exchange, stopped at `08029220`, verified pending ID `37` and quantity `02`, and changed only temporary acquisition argument `03003A35` to `5E` (94 decimal). At return breakpoint `0802922C`, acquisition succeeded, occupied-record count was 04, and exact records were `27 01 0D 01 37 5E 5F 01 00 00`. The exchange completed normally and the Items menu showed 94 Binkies.

The last directly reported cumulative-counter read was **030032B7 = 06 before donation**. Subsequent normal Kaizo interactions produced the remaining rewards as prerequisites were enabled. **No post-donation debugger readback of exactly 100 was provided.** Final rewards support successful progression, but are not a substitute for an independently measured counter. No dedicated save/reload result is claimed.

Ordinary inventory has count byte `030019D4` and movable ID/quantity records at `030019D5`, stride 2. In the clean checkpoint, `030019DA` was quantity for Hotpot ID `5F`, not Binky ID `37`. The earlier failed write therefore did not create Binkies. The successful native acquisition maintained insertion metadata and sorting.

## Controlled Hanzo prerequisite progression

- Lab 4: flag 22B, byte 0300332C, mask 08.
- Lab 5: flag 22C, same byte, mask 10; reported cumulative byte 18.
- Lab 6: flag 22D, same byte, mask 20; intended cumulative byte 38. Do not invent an additional exact readback.
- Last Lab 1: flag 096, byte 030032F9, mask 40; reported set value 40.

The user found these completion flags sufficient to unlock corresponding Kaizo stages in this controlled test. Later Hanzo reward Gimmick insertion was unnecessary. This does not establish safe normal-story skipping or absence of other Hanzo encounter effects. The earlier large manual Gimmick fixture crash remains historical evidence and is not a successful preparation method.

## Residual regression coverage

Duplicate claims, capacity boundaries, retirement/follow-up, dedicated save/reload and a separately measured final counter remain residual coverage. They do not reopen the completed principal 24-reward objective. Original reward order, Gimmick IDs, prerequisites, claims and whole-stack donation behavior remain the intended preserved implementation; no new edge-case runtime claim is made here.

## Objective status

- Kaizo 100-Binky reward objective: **COMPLETE**.
- Gimmick Palace ordinary enemy HP/base-mitigation investigation: **CURRENT**. See `../gimmick_palace_enemy_research.md` and its evidence JSON.
- Functional two-Binky Hawker in Mayonen first outdoor map 0048 and Namp Lagoon second screen: **DEFERRED - FINAL MAJOR OBJECTIVE**. Namp map/position and placement design still require verification. No placement work is authorized here.

Sources: user Session 7 report; active ROM hash; `../kaizo_binky_100_proposal.md` and `.json`; `../../session_handoffs/SESSION_HANDOFF_6.md`; prior native inventory investigation in this conversation. Detailed attributed evidence is in the adjacent JSON. No ROM, gameplay source, RAM, save or checkpoint was changed.
