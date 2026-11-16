# Cumulative v1 investigation — 2026-10-28

Status: **INCOMPLETE / Experimental / Runtime Validation Pending**. Four feature
groups are implemented; the five-area music group remains partial. This is not
a complete final release candidate. No emulator, debugger, save or savestate was
operated or modified. Sprite extraction and Hawker placement were not resumed.

## Verified ancestry and clean reconstruction

Original Japanese and English files are 8,388,608 bytes and match the user-specified
SHA-256 values. The retained Alessa wrapper, rate-two recruitment derivative,
Kaizo derivative and Detector derivative are each 16,777,216 bytes. All four were
reconstructed in memory using the retained source patchers and compared against
the complete corresponding stored file; all comparisons and reported hashes pass.
See the new manifest's `ancestry` array for paths, hashes and sizes.

The original wrapper changes Hanzo's call pointer at file `0010D69F..0010D6A2`
to bus `08800000`, appends its 21-byte recruitment payload at file `00800000`,
and fills the remaining extension with FF. The Detector ancestor has exactly
that fixture, the 118 rate-two differences, the 51 approved Kaizo differences,
and the two Detector differences. There are no additional fixture changes in
that chain. Separate Gear-Yo, Hanzo, Mayonen, Sofoubi and Relleck experiments
were not inherited.

The new ROM starts again from the English baseline. Rate-two's existing baseline
profile proves its independence from recruitment. Kaizo's approved operands and
English text allocation also match this baseline. Their ranges are disjoint from
the recruitment redirect/extension. The normal Hanzo call and natural Mayonen
recruitment scene remain intact. This establishes exclusion of the shortcut
without changing the exchange code. Normal story availability is still runtime
untested on this new ROM.

## Hanzo Lab 2 — Confirmed static

All bus addresses below subtract `08000000` for file offsets. Map `0031`'s event
table pointer is bus `08159D24`; its default is `08111CE6`. This agrees with the
retained `pre_oystown_progression.py` `SCRIPT_SCOPES` Lab2 entry. The whole bounded
scene `08111CE6..08111EAB` was decoded with actual command-length tables.

At `08111CE6`, `FD35 2902` branches to the completed interaction at `08111E8D`.
The successful scene prepares parameter 1A with 0088 at `08111E40`, then sets
parameter 1C using `FD 0B 1C 29 00` at `08111E45`. **The operand is file
`00111E48`; 29 becomes 1B.** Both packed values have recipient bits 6–7 zero:
DeMille. The subsequent call at `08111E4A` is `FD2F 334B1208`.
Its second gift `005F` at `08111E59` (character 1, ID 1F) is unchanged.
Flag setters `FD49 2500` at `08111E7C` and `FD49 2902` at `08111E80` remain
unchanged. No flags, inventory structures, savedata or equip logic were patched.

The shared block `08124B33..08124BF2` is unchanged. At `08124B9F` it reads
parameter 1C; `FE54` at `08124BA3` invokes normal acquisition. The dynamic reward
message is downstream of the same parameter, so names follow the chosen ID.
Lab2 messages 661–668 were joined through actual `pointers1.dat` references:
message 666 says “these 2 new Gimmicks” without a hard-coded Dojo Pup name.
The decoded scene has no other direct comparison against ID29. This bounds the
identity-dependency check; no claim of exhaustive arbitrary indirect-script
reachability is made. Long-term progression and save/reload require manual tests.

Lab1 changes only file `0010D69B` from 1B to 29, using the previously tested
operand. The shared normal call remains `FD2F 334B1208`.

## Attack fields — Confirmed static, conditional battle scope

Erupter ID27's record starts file `0062CB40`; Dojo Pup ID41 starts `0062D010`.
Both original Japanese and English Attack-field slices match. The records have
base Attack 40 and 47; both upgrade caps are 45. Their record +27 flags are 20
and 30 respectively: both type nibbles are zero and neither has bit7 set.

The smallest field swap is +22 and the nine unsigned percentage bytes at
+28,+2A,+2C,+2E,+30,+32,+34,+36,+38 in each record. Exactly 20 bytes change.
Erupter's percentages are 120,125,135,150,170,195,250,250,250; Dojo Pup's are
112,115,118,121,124,127,130,130,130. Every auxiliary byte is zero in both
records and remains untouched. All caps, flags, names, owners, pointers,
animations, effects and other record fields remain byte-identical.

The retained native windows were independently hashed against
`gimmick_difficulty_scaling_evidence.json` for both source ROMs. M1 at
`08075970..08075AEC` uses `floor((base + upgrade)*percentage/100)` for these
and all valid records. L1 at `08065518` decodes zero auxiliary bytes to zero;
their downstream quantity names remain unresolved and are unnecessary to this
swap. U1 at `08081188..080811C8` retains byte wrapping before cap 45. All normal
upgrade bytes 0–45, difficulties 1–7 and implemented slots 8–9 are compared in
`attack_comparisons.csv`. Robustness checks also cover arithmetic upgrade bytes
46–255, without claiming they are normal obtainable states.

| Difficulty | Erupter original | Dojo Pup original | Erupter patched | Dojo Pup patched |
|---|---:|---:|---:|---:|
| 1 | 48 | 52 | 52 | 48 |
| 2 | 50 | 54 | 54 | 50 |
| 3 | 54 | 55 | 55 | 54 |
| 4 | 60 | 56 | 56 | 60 |
| 5 | 68 | 58 | 58 | 68 |
| 6 | 78 | 59 | 59 | 78 |
| 7 | 100 | 61 | 61 | 100 |

This table is upgrade zero. At upgrade 45, original Erupter is
102,106,114,127,144,165,212; original Dojo Pup is 103,105,108,111,114,116,119.
Patched arrays exchange exactly. The CSV includes every intermediate upgrade.

B1 at `080485B0..0804881C` independently rereads base/percentage from ROM.
Its documented conditional calculation has the corresponding swapped
pre-subtraction values for matching action inputs. The new synthetic battle test
checks 16,560 comparisons: upgrade 0–45, nine slots, scaling enabled/disabled,
five subtraction quantities, suppression on/off and both directions. Both records
have the optional bit7 post-subtraction multiplier disabled. Target mitigation,
minimum damage and suppression logic remain unchanged. This does **not** prove
the two Gimmicks select identical action inputs, minigame performance or damage
paths. Persistent upgrade-to-battle-input provenance and universal dispatch remain
the previously documented gaps. Neither Gimmick has new runtime damage evidence.

## Music — partial; explicit blockers

Read and cross-checked all 494 catalog music selectors against the actual English
ROM; read the 864-edge transition graph and partial map/node associations. These
catalogs intentionally lack verified room names and exclusive area membership.
Graph reachability alone does not prove a complete area, particularly with 1,799
unsupported registered script-prefix stops. Translated location titles include
The Spillage, Pokypine Wood, Oops Manor, Sewers 1/2 and Secret Safe; no unproved
equivalence to the user's “Vault” or ship designation is introduced.

The proven Caverns entry `001E` changes file `0062D731` from 0D to 07, preserving
upper bits. Mayonen source map0048's byte at `0062DBC9` is 07; selector+200 gives
sound CF. Both that desired track and the Caverns entry change have prior user
runtime evidence. Pokypine map0008 at `0062D4C9` also contains 0D. Other inspected
ordinary map selectors were Namp arrival0060 = 24 hex and Oystown0104 = 10 hex.
Those bytes alone do not establish every desired soundtrack under event control.

Candidates 001F,0020,0021,0022,002A,002B,002E stay unchanged. The known natural
recruitment scene `081271E9..081275B6` contains no FEA7/FEA8/FEA9/FEAB commands
on its decoded boundaries. That does not exclude transitive, registered actor or
other story overrides. No event music command was changed. A later event can
still override the map selector; complete override coverage remains unproved.

Named-source leads were checked through actual translation pointer sites:
message36B identifies an Oystown Sewer sign; AC7/AC8 identify Oops Manor NPC
dialogue. They are retained as Candidate leads in `investigation.json`, not
promoted to complete room ownership or a verified track. The machine music
ledger records each confirmed/candidate Caverns map and explicit null fields
for unresolved areas. No global ID substitution or adjacent map edit occurred.

Smallest follow-up: establish named room anchors and the complete room sets for
Dropper Village, ship, sewers and Vault; establish Oops Manor's target track and
the precise Vault identity; then traverse their registered event/call paths for
music overrides and close the seven Caverns candidate memberships. A user room
list with verified map IDs or named entry observations can provide anchors, but
will still need static boundary/override checks. No speculative ROM changes were
substituted for these missing proofs.

## Evidence and confidence

New source: `tools/analyze/cumulative_v1_evidence.py`; output:
`tools/patch/output/cumulative-v1-20261028/build/investigation.json` and
`music_ledger.json`. Existing evidence and manifests were preserved unchanged.
The independent verifier imports no builder or existing feature patcher. It
compares the complete output against a separately assembled allowlist from
retained evidence and independently encoded new fields. Static PASS is bounded
to the actual implemented changes, not the unresolved music package or gameplay.
