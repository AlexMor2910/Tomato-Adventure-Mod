# Mayonen Caverns one-map music experiment

## Static verification

Script: `tools/patch/mayonen_caverns_music.py`. English baseline SHA-256:
`8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde`.
Output: `tools/patch/output/mayonen-caverns-map001e-86d6efb0c6824c9c851fb5602c4e4746/mayonen_caverns_map001e.gba`.
Output SHA-256: `7fc50105e340510079158ca74e61f778b63b3276793ec9b6ffbe29c2af75c761`.

Confirmed static: full original map record checked; output readback and full-ROM
comparison established exactly one changed byte: file `0x0062D731`, bus
`0x0862D731`, `0D -> 07`. Map ID `0x001E`, record bus `0x0862D72C`.
The low six bits select music; sound playback uses selector + decimal 200.
No event scripts, other maps or Hanzo reward operand were changed.

## User-confirmed runtime result

The user reports successful manual testing in isolated mGBA 0.10.5:

- Emulator launched without warnings.
- Mayonen theme played in the first Mayonen area.
- Entering Mayonen Caverns normally preserved the Mayonen theme.
- The selector change works in-game for map `0x001E`.

Status: **Confirmed runtime, user report**; Codex did not operate the emulator.
Other connected Caverns maps were not tested. This does not validate the entire
dungeon. The earlier unsuccessful save-state test has no established cause.
No expansion of the patch is authorized.

Separate experiment: the user previously confirmed Hanzo -> Dojo Pup acquisition,
inventory registration/presence, and successful battle use. That experiment is
independent and is not combined with this ROM. Its script and ROM remain unchanged.
