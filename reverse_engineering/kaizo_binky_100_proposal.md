# Kaizo cumulative 100-Binky proposal ? static audit, not constructed

Input: `tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`, SHA-256 `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3`, size0x01000000. Japanese and English baseline hashes were independently checked. Numeric operands below match both original Japanese and translated English bytes at the same offsets; translated dialogue pointers/data differ. Source is the unchanged validated two-Binky + Alessa recruitment ROM, without either temporary companion guard.

Confidence: Confirmed static original bytes/control flow; proposed replacements are authorized numerical specifications, not runtime-validated behavior. No ROM output, patch script or new experimental directory has been created. This document and JSON are the exact reviewable proposal.

## All 48 threshold operands

Each row replaces BOTH displayed scratch threshold (`FD 0B 14 lo hi`) and comparison (`FD 1F lo hi`). Values are uint16 little endian; high byte00 remains unchanged. Before comparison `FD 0D 30` reads cumulative donations. `FD46` exits when total is below the requirement. The display value supplies the next-gift and gift-award dynamic `[NUMBER]` text.

| Gimmick | Old?new | Bytes at EACH operand | Display file / bus | Compare file / bus | Packed reward (owner, ID) | Claimed flag; extra prerequisite |
|---|---|---|---|---|---|---|
| UFO-Cast | 4?2 | `04 00`?`02 00` | `0x000FC7CA` / `0x080FC7CA` | `0x000FC7D1` / `0x080FC7D1` | 0x60 (1, 0x20) | 0x195; none in reward block |
| Lucky Cat | 7?4 | `07 00`?`04 00` | `0x000FC7FE` / `0x080FC7FE` | `0x000FC805` / `0x080FC805` | 0x2A (0, 0x2A) | 0x196; none in reward block |
| Cyclooka | 10?6 | `0A 00`?`06 00` | `0x000FC832` / `0x080FC832` | `0x000FC839` / `0x080FC839` | 0x96 (2, 0x16) | 0x197; 0x22B |
| Rocket Pak | 13?7 | `0D 00`?`07 00` | `0x000FC872` / `0x080FC872` | `0x000FC879` / `0x080FC879` | 0x62 (1, 0x22) | 0x198; none in reward block |
| Kendama | 17?9 | `11 00`?`09 00` | `0x000FC8A6` / `0x080FC8A6` | `0x000FC8AD` / `0x080FC8AD` | 0x02 (0, 0x02) | 0x199; none in reward block |
| Bouncer | 21?12 | `15 00`?`0C 00` | `0x000FC8DA` / `0x080FC8DA` | `0x000FC8E1` / `0x080FC8E1` | 0xA4 (2, 0x24) | 0x19A; none in reward block |
| Bee Gatling | 26?14 | `1A 00`?`0E 00` | `0x000FC90E` / `0x080FC90E` | `0x000FC915` / `0x080FC915` | 0x54 (1, 0x14) | 0x19B; 0x22C |
| Pyramet | 31?17 | `1F 00`?`11 00` | `0x000FC94E` / `0x080FC94E` | `0x000FC955` / `0x080FC955` | 0x1C (0, 0x1C) | 0x19C; none in reward block |
| Fart Horn | 37?21 | `25 00`?`15 00` | `0x000FC982` / `0x080FC982` | `0x000FC989` / `0x080FC989` | 0x6C (1, 0x2C) | 0x19D; none in reward block |
| Origami | 43?24 | `2B 00`?`18 00` | `0x000FC9B6` / `0x080FC9B6` | `0x000FC9BD` / `0x080FC9BD` | 0x04 (0, 0x04) | 0x19E; none in reward block |
| Popocon | 50?28 | `32 00`?`1C 00` | `0x000FC9EA` / `0x080FC9EA` | `0x000FC9F1` / `0x080FC9F1` | 0x98 (2, 0x18) | 0x19F; 0x22D |
| BowlingRice | 57?32 | `39 00`?`20 00` | `0x000FCA2A` / `0x080FCA2A` | `0x000FCA31` / `0x080FCA31` | 0x28 (0, 0x28) | 0x1A0; none in reward block |
| Bunny Hop | 65?36 | `41 00`?`24 00` | `0x000FCA5E` / `0x080FCA5E` | `0x000FCA65` / `0x080FCA65` | 0x48 (1, 0x08) | 0x1A1; none in reward block |
| Shadowreel | 73?41 | `49 00`?`29 00` | `0x000FCA92` / `0x080FCA92` | `0x000FCA99` / `0x080FCA99` | 0xF2 (3, 0x32) | 0x1A2; none in reward block |
| SlotZooka | 81?45 | `51 00`?`2D 00` | `0x000FCAC6` / `0x080FCAC6` | `0x000FCACD` / `0x080FCACD` | 0x8C (2, 0x0C) | 0x1A3; none in reward block |
| Flame Doll | 90?50 | `5A 00`?`32 00` | `0x000FCAFA` / `0x080FCAFA` | `0x000FCB01` / `0x080FCB01` | 0xDA (3, 0x1A) | 0x1A4; 0x096 |
| TwinDragon | 99?55 | `63 00`?`37 00` | `0x000FCB3A` / `0x080FCB3A` | `0x000FCB41` / `0x080FCB41` | 0x06 (0, 0x06) | 0x1A5; none in reward block |
| SesameTop | 109?61 | `6D 00`?`3D 00` | `0x000FCB6E` / `0x080FCB6E` | `0x000FCB75` / `0x080FCB75` | 0xE6 (3, 0x26) | 0x1A6; none in reward block |
| Judgment | 119?66 | `77 00`?`42 00` | `0x000FCBA2` / `0x080FCBA2` | `0x000FCBA9` / `0x080FCBA9` | 0x4A (1, 0x0A) | 0x1A7; none in reward block |
| Mansnow | 130?72 | `82 00`?`48 00` | `0x000FCBD6` / `0x080FCBD6` | `0x000FCBDD` / `0x080FCBDD` | 0xB0 (2, 0x30) | 0x1A8; none in reward block |
| Dragonfire | 141?78 | `8D 00`?`4E 00` | `0x000FCC0A` / `0x080FCC0A` | `0x000FCC11` / `0x080FCC11` | 0x12 (0, 0x12) | 0x1A9; none in reward block |
| Momotaro | 153?85 | `99 00`?`55 00` | `0x000FCC3E` / `0x080FCC3E` | `0x000FCC45` / `0x080FCC45` | 0xCE (3, 0x0E) | 0x1AA; none in reward block |
| StarScope | 165?92 | `A5 00`?`5C 00` | `0x000FCC72` / `0x080FCC72` | `0x000FCC79` / `0x080FCC79` | 0x6E (1, 0x2E) | 0x1AB; none in reward block |
| Choo-Choo | 180?100 | `B4 00`?`64 00` | `0x000FCCA6` / `0x080FCCA6` | `0x000FCCAD` / `0x080FCCAD` | 0x1E (0, 0x1E) | 0x1AC; none in reward block |

Reward identity operands are `FD 0B 1C packed 00`, owner=packed>>6, Gimmick ID=packed&3F. Existing name/ID mappings are in symbols.md and translated menu rows. Each corresponding claimed flag is checked by FD35 and set by FD49 after the original shared acquisition call to08124B33. Claimed flags195..1AC are reward completion flags, not Binky totals or thresholds. Their membership/ownership side effects are preserved, not repurposed.

Additional prerequisite checks occur at bus080FC841 (22B, Cyclooka), 080FC91D (22C, Bee Gatling), 080FC9F9 (22D, Popocon), 080FCB09 (096, Flame Doll): `FD36 flagLE 4C CD 0F 08` branches to the original refusal when clear. Exact narrative meaning of every flag is not newly proven; dialogue associates missing prerequisites with Hanzo creations. No additional numeric stage/party requirement was found in this bounded ladder; surrounding original story/event activation remains required. Claim, story and gift IDs are immutable.

## Cumulative donation storage and cap

Persistent byte variable30 is RAM030032B7 =03003287+30. Ordinary carried Binkies are separate item37 at the usual inventory list (count030019D4, ID/count pairs030019D5). No general inventory capacity change is proposed.

| Bus / file | Original context | Meaning |
|---|---|---|
| 080FC77D /000FC77D | FE 5C 37 | Read entire carried Binky quantity into halfword accumulator03003A24 |
| 080FC793 /000FC793 | FD 14 14 | Save quantity to scratch halfword03003A38 |
| 080FC796 /000FC796 | FD 0D 30 | Read cumulative byte into halfword accumulator |
| 080FC799 /000FC799 | FD 11 14 | Add saved stack quantity to halfword accumulator |
| 080FC79C /000FC79C | FD 0E 30 | Store low byte to cumulative total; full accumulator remains |
| 080FC79F /000FC79F | FE 56 37 FF A7 C7 0F 08 | Remove WHOLE carried Binky stack; continuation stays080FC7A7 |
| 080FC7A7 /000FC7A7 | FD 1F B4 00 | Compare retained full halfword sum with180 |
| 080FC7AB /000FC7AB | FD 45 D5 CC 0F 08 | If sum>=cap, jump to clamp |
| 080FCCD5 /000FCCD5 | FD 4D 30 B4 | Set persistent cumulative byte to180 |
| 080FCCD9 /000FCCD9 | FD 30 B1 C7 0F 08 | Reread clamped total and process rewards normally |

Exact additional edits:

| Role | File / bus | Old?new |
|---|---|---|
| Cap comparison operand (uint16 LE) | 000FC7A9 /080FC7A9 | `B4 00`?`64 00` |
| Persistent clamp operand (uint8) | 000FCCD8 /080FCCD8 | `B4`?`64` |

Both are necessary. Changing only the clamp would fail for101..179. Native FD0D0802693C reads a byte; FD0E08026978 stores a byte without overwriting accumulator03003A24; FD1108026AB8 adds halfwords; FD1408026B2C saves the halfword. FD1F08029AAC records signed difference state, FD450802984C branches on the nonnegative case, and FD4D0802A004 writes a byte literal. The verified FD dispatch table is0862BC30; FE dispatch0862B8B4. FE560802565C?08025684?08080550?0808059C uses FF as whole-stack removal at080805E0..080805FC and shifts inventory records; no accumulator03003A24 store occurs on this ordinary-item path. Interpreter argument readers/continuation preserve the accumulator. These are static findings, not emulator traces.

### Overshoot and donation policy requiring approval

At99 donated with5 carried: halfword sum104, stored104, remove all5, compare104>=100, clamp100, reread100, run original unclaimed reward ladder. Only1 contributes to the retained total;4 surplus Binkies are removed without credit. Retaining this original whole-stack behavior is the proposed minimum patch. There is no remainder refund or partial-stack acceptance. Such a change would require a separate reviewed behavioral patch and is NOT implicitly authorized by the numerical specification.

For valid new totals0..100 plus carried0..99, sums are at most199, so the transient byte store cannot wrap. For legacy total180 plus99, the transient byte would wrap279?23, but the preserved halfword sum279 triggers clamp100. The sum/compare model was checked for all18,100 pairs total0..180, stock0..99. A previously completed save with claimed flag1AC set bypasses donation/cap entirely and may retain a historical total180. This proposal does not migrate completed saves or change flags. No guarantee is made for corrupted quantities/states.

At total100 with a missing original prerequisite, stored credit remains100 but reward processing can stop at the gated reward. Later gifts, including Choo-Choo, remain gated until original conditions are met. Additional carried stacks can still be removed on subsequent interactions before final completion despite yielding zero new credit. Once1AC is claimed, entry080FC775 jumps to retirement and stops donation handling. These are existing control-flow consequences requiring clear acceptance, not bugs to repair by modifying prerequisites.

## Final reward, retirement and English text

Choo-Choo remains packed1E (DeMille ID1E), shared grant08124B33 through FE54 at08124BA3, claimed flag1AC. Its proposed compare100 and cumulative cap100 make100 the exact numerical unlock, subject to preserved preceding rewards/prerequisites and valid receiving inventory. There is no separate180 retirement comparison to modify. Entry080FC775 and reward-block080FCC9B check1AC; retirement080FCD0C checks1AE,080FCD14 sets1AE once, then F9/Fa dialogue. No changes to these flags, reward calls, condition branches or inventory code are proposed.

The only literal180 target reference identified in the English Kaizo donation/retirement dialogue is message0FA, source ta_script_eng.txt:1114:

`Kaizo: I wonder if I can[BREAK]make 180 friends...[WAIT]Heh-heh-heh...[SIMPLEWAIT][END]`

Proposed: replace180 with100. Literal digit8 has font encoding78;0 is70. ROM edit: file0064FE13 /bus0864FE13 `78`?`70`. Full message starts file0064FDF3 /bus0864FDF3, length65 bytes, ends exclusive0064FE34; exact source encoding matched the ROM. Pointer at000FCD26 /080FCD26 remains `F3 FD 64 08`. pointers1.dat lists only message0FA for this exact string pointer. Same-length substitution preserves allocation, pointers, wrapping and every control code. No text relocation/rebuild is needed. An eventual source-text change would update only this digit in ta_script_eng.txt so a future translation rebuild stays consistent; that toolkit file has NOT been changed during this proposal.

Messages0ED,0F4,0F5,0F8 use dynamic NUMBER for current stack, cumulative total and thresholds; their formatting/pointers stay unchanged. 0F9 retirement has no literal180. Source occurrences180-E (a message identifier), MENU218007 and180lb are unrelated and must not be edited. The friends joke is the only literal target string found, rather than a second independent Binky requirement.

## Isolated reproducible patch architecture

After separate authorization, create tools/patch/kaizo_binky_100.py and a fresh UUID output directory under tools/patch/output. Hash-gate ONLY the input above; reject any Sofoubi/Relleck guard ROM, already-Kaizo-patched input, wrong size or mismatched original byte. Keep the existing exchange patch/script unchanged. The independent Kaizo ledger contains48 uint16 threshold writes, one uint16 cap compare, one byte clamp and one text byte:51 operations covering100 operand bytes, with exactly51 ACTUAL differing bytes. Every changed position is explicitly enumerated in kaizo_binky_100_proposal.json. Each threshold's high byte is written identically; it is not an additional difference.

Require preflight original bytes AND command context/gift/flag predicates, nonoverlap and approved list equality. Generate no output until all checks pass. Write with exclusive creation, re-read output, perform an independent full-file comparison against the allowlist, record source/output SHA-256, size, exact before/after bytes and a complete diff. Header0..BF, all nonallowlisted bytes, Alessa extension and recruitment redirect, native FE49 handler/dispatch, all five exchange transaction blocks and patched exchange advice must be byte-identical to input. No ROM allocation/relocation is needed. Verify protected fingerprints before/after. Preserve earlier manifests rather than changing their historical runtime status. Output hash will be computed only after authorized construction; none is claimed now.

## Verification and manual runtime plan

Completed read-only checks:48 originals and both command encodings, original reward/claimed flags and four extra gates, identical original numeric operands in Japanese/English/source, approved round-to-nearest old*100/180 values, strict monotonicity, final100,50 numeric changed bytes plus one dialogue byte, original text exact encoding/pointer ownership, and18,100 arithmetic pairs. The arithmetic model is not game execution and does not prove acquisition or event scheduling.

After construction approval, synthetic patcher tests must reject wrong hash/size/original context, overlapping edits, incorrect reward/claim flag, swapped threshold display/check, existing output path and unexpected extra output difference. Verify all24 boundaries t-1,t,t+1 with matching displayed/compare values; final99 rejects and100 accepts numerically. Test model overshoots0+99?99,99+1?100,99+5?100,100+5?100 (before completion),180+99?100 legacy incomplete; claimed1AC must follow unchanged bypass. Simulate multiple threshold crossings, already-claimed skips, missing prerequisite stop and later resumption. These tests assert the ledger/model; receiving-capacity and original acquisition behavior still need runtime evidence.

A future separately authorized user session should use disposable naturally coherent Kaizo-accessible checkpoints, whose actual filenames/hashes/flags/inventories must first be audited. None has been certified as the final runtime fixture here. Test each gift at just-below/exact threshold, whole-stack overshoot99+5, multiple gifts in one visit, missing prerequisite/return, repeated interaction without duplication,100/Choo-Choo/follow-up retirement, saving/reloading, English dialogue, and unchanged ordinary inventory99/exchange capacity behavior. Do not set claim/story flags just to bypass gates. Supply only one debugger action at a time after separate runtime authorization.

Stop on any source/context mismatch, additional difference, wrong cap, absent prerequisite/invalid receiving inventory, unexpected claim/party changes, duplicate/missing gift, broken dialogue/return or save discrepancy. Gift acquisition capacity/failure behavior and burst rewards at new thresholds have not been runtime-validated; no guarantee of all edge cases is inferred from unchanged code. No invented recovery edits.

## Next approval

Authorize offline construction of exactly this51-actual-byte Kaizo add-on from source d356... using the approved24 thresholds, BOTH cumulative cap edits and the single retirement-text digit, explicitly accepting unchanged whole-stack removal and uncredited surplus. Include the reproducible script, synthetic tests, manifest/diff and protected-file audit; no emulator/runtime work. If surplus must instead be retained/refunded, do not authorize this construction: request a separate static donation-behavior design first.
