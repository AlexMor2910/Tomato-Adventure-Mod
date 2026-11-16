# Tomato Adventure - Session Handoff 7

Session date: 2026-10-15. Documentation and bounded static research only. No emulator/Ghidra operation, ROM/stat/RAM/save/checkpoint/gameplay-code changes or commits. Read AGENTS.md and the modding plan before future work.

## Objectives

- **COMPLETE:** Kaizo cumulative 100-Binky rewards, 24/24 user-confirmed acquisitions and functionality in tested gameplay. Preserve all 24 rewards and their current distribution, including nine final-prerequisite rewards.
- **CURRENT:** Gimmick Palace ordinary-enemy HP and base mitigation research. No final replacement values or balance patch is approved.
- **DEFERRED - FINAL MAJOR OBJECTIVE:** Functional two-Binky Hawker placement in Mayonen first outdoor map 0048 and Namp Lagoon second screen (exact map/position unresolved). Do not start placement now.

## Kaizo closeout

See `reverse_engineering/experiments/kaizo_binky_100_session7_closeout.md` and adjacent JSON. Active ROM SHA-256 remains `7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`.

The user verified the native 94-Binky acquisition by changing only pending quantity 03003A35 from 02 to 5E at 08029220, then confirming native success at 0802922C, four records `27 01 0D 01 37 5E 5F 01 00 00`, and menu quantity 94. All remaining Kaizo rewards were obtained through normal interactions as controlled Hanzo completion flags were enabled. Later associated Hanzo Gimmick injection was unnecessary. This does not justify normal-story skipping.

Last directly reported donation-counter read was 06 BEFORE the 94-Binky donation. Do not invent a final 100 readback, final-checkpoint hash or dedicated save/reload result. Duplicate/capacity/retirement/save regressions are residual coverage, not failure of the completed principal objective. Preserve old construction manifests as historical records.

## Enemy findings

See `reverse_engineering/gimmick_palace_enemy_research.md` and `gimmick_palace_enemy_evidence.json`: 18 ordinary-actor species records, 11 descriptors, 114 authored actor references in scoped map tables. Every listed translated name was checked against ROM data; stat fields match Japanese, English baseline and Kaizo ROM.

Enemy record = 08634F50 + ID*4C. HP = u16(+0A)&7FFF; base mitigation = u16(+0E), copied by 080482E4..080482E8 to target+14. Existing damage path subtracts bounded target+14 + target+18. This establishes base Defense-equivalent for that path, not universal immutable Defense or Choo-Choo-specific resistance.

Top candidates: Rattlin' Dragon 9C HP262/mitigation54; Mystery Bolt 99 140/68; Detector A5 135/38; Great Boronga A7/A6/A8 180/50,150/40,140/50. The Great Boronga entries are explicit members of repeated ordinary-actor formations; do not generalize by display name to boss/event instances. Brikkypress 9A 110/90 is excluded pending ordinary/boss/hazard classification. Boss/event candidates are not proposed for balancing.

**Annoying Siren is ATTACK 93, not an enemy name.** Cybercop 62 and Detector A5 reference it. Detector occurs in the inspected palace-associated ordinary formations and is the probable match to the user's memory; exact identification and Choo-Choo interaction remain unresolved.

Named palace anchors: map01B4 actor08156AD4 -> message892/top-floor transfer081242FA -> map01E3. Map01E3 actor08159530 -> message891/entrance transfer08124218 -> map01B4. Ordinary exits associate entrance rooms and a large interior component. Full bridging of a separate late-room component and exact floor labels remain probable/unresolved; see report rather than assuming every adjacent map belongs. No Tomato Palace alias was established in inspected sources.

## Safe next step

User reviews bestiary before any separately approved balancing experiment. Prioritize measuring damage/pacing for a specific ordinary species and formation. No replacement HP/Defense numbers selected. User alone operates mGBA; do not launch/control it, execute debugger commands or start Ghidra. Keep changes reproducible and isolated if later authorized.

Documentation created this session: the two enemy research files, the two Kaizo closeout files, and this handoff. A before/after digest check covering 42 selected ROM/save/checkpoint artifacts passed during enemy documentation generation; this is a scoped audit, not a whole-workspace audit.
