# CSV Patcher Dry Run and Reference Verification

2026-10-11. Command from repository root:

```powershell
python tools/patch/gimmick_balance.py --dry-run
```

Observed output:

```text
Source SHA-256: 8d27aac43d50eab17d7ba8b4183cb7c70dbd74194d11b3f8c011c61d13b5adde
ID 1 Gear-Yo base_attack: 21 -> 22 file 0x0062c272, bus 0x0862c272
Verified differences: 1
Output SHA-256: 5cd1cc5c70dce892476d5162d49e0e1552600d37087181f79d0cc4e3d8120a8f
DRY RUN: no files created
```

Then ran `python tools/patch/gimmick_balance.py --apply --output-name gearyo-reference-validation`. This created a separate ignored ROM and manifest in `tools/patch/output/gearyo-reference-validation/`. Full-file differences are exactly `[0x0062C272]`, `0x15→0x16`, with unchanged 8,388,608-byte size. The new file was compared directly against `reverse_engineering/experiments/testing/gearyo-281d1d7030904d5684c2ff29d3e90c1b/B/rom/gearyo_attack_22.gba`: byte-for-byte identical. **No inconsistency with the reference experiment was found.**

All 10 synthetic tests passed with `python -m unittest discover -s tests -p test_gimmick_balance.py`; no copyrighted input is required for that suite. Independent checks confirm source Japanese/English hashes and the previous experimental ROM hash remain unchanged. The old experiment script was not edited. No emulator or translation build was run.

This is artifact reproduction, not a new gameplay test. The prior user-observed Gear-Yo A/B results (Attack 21/26→22/27, damage 16→17) apply to the identical reference bytes under the tested conditions. Other Gimmicks/settings remain untested. Usage, ID conventions and extension constraints are documented in [tools/patch/README.md](../../tools/patch/README.md).
