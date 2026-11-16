# Remaining two-Binky exchange tests

> **Session 5 closeout supersedes historical test-status labels below:** all six Alessa/Sofoubi/Relleck character/stage reward tests are now user-confirmed passed. Offline checkpoints were independently inspected. See [current closeout](binky_exchange_session5_closeout.md) and [evidence](binky_exchange_session5_evidence.json). Cancellation, partial-gauge, capacity and multiple-full-gauge regressions remain pending. Older construction evidence/manifests are retained unchanged.

2026-10-13. Bounded static inspection, artifact verification and future-test
planning only. No ROM/state construction, runtime write or emulator operation.

## Evidence and preserved implementation

**User-confirmed runtime:** the user loaded the patched16MiB ROM from a disposable
pre-Oystown checkpoint, entered Oystown successfully, retained the functional
DeMille–Alessa party, manually filled03001F94 to40 and completed an Alessa
exchange. Exactly two Binkies were awarded, AWE reset and no error occurred.
Original early Alessa previously awarded one with the same full-gauge requirement
and normal reset. This is a successful reported runtime A/B comparison, not a
frame-identical debugger replay. Separate sessions/checkpoint copies were used;
no new console transcript, screenshots or exact immediate readbacks were supplied.

**Codex-confirmed static:** both existing outputs were re-read, fingerprinted and
compared in full against their source/retained operation ledger using the existing
`verify_output` function. The builder/main were **not** invoked. Each still has
exactly118 differing bytes, five two-Binky endpoints, preserved header and unchanged
eligibility/selection/reset logic. The16MiB derivative retains the recruitment
redirect and full expansion unchanged. Manifests and patch-script hash match.
No implementation concern was discovered requiring a patch correction.

Read-only reproduction tool:
[binky_remaining_tests.py](../../tools/analyze/binky_remaining_tests.py), run
`python -B tools/analyze/binky_remaining_tests.py`.
[Evidence JSON](binky_remaining_tests_evidence.json) retains output checks, relevant
checkpoints/all four records, tier bytes, initializer windows and90 protected
hashes. Existing reports, handoffs, modding plan, patch script and relevant
party/AWE/event/inventory documentation were reviewed. All historical results
remain; latest runtime evidence supersedes their early-case untested status.

## Available checkpoints

All three root paths exist, pass PNG CRC/bounds, state/extended-data decompression,
version01000007 and known ROM title/ID/CRC checks. No load was performed here.

| Root path | SHA-256 | Saved state / compatibility |
| --- | --- | --- |
|`before_oystown.ss0`|d20fc78972641d76e1b56f23daa80c9fedd4c07fa22edb63e69d37371db21c53|RecruitmentCRC E9ACB98F; Lab3exterior00DF/node07; party31; charge05; introclear |
|`after_exchange_oystown.ss0`|aca4eb6751d66949e74a137217e92f79eaa0e85039f11f09d9821ea9a2cb5646|RecruitmentCRC E9ACB98F; Oystown0104/node08; party31; charge00; introset |
|`after_exchange_oystown_alessa_test.ss0`|85110875375c28ab412e4413e986d9cb65eb81353d1214f3b86e6d7b7a02f1cf|**PatchedCRC AB34C118**, matching16MiB testROM; Oystown0104/node08; party31; charge00; introset |

The new post-test file is **actually present**, not inferred from a recommendation.
It is the best future test source: matching patched ROM, already in Oystown,
intro consumed naturally and no need to replay recruitment or travel. Its ordinary
inventory contains BinkyID37/count04 at030019D9/DA. The old pre-entry contains02;
the old post-exchange contains03. Those saved endpoints corroborate reported
one-versus-two rewards but do not independently measure the complete transactions.

All three retain Gear-Yo/Erupter and Pop Horn, membership31/count02, and no enabled
interpreter slots (bitmap030039C1..C4 zero). They have tierbytes030032FE=00,
0300331F=00,03003326=00: BA,1C4 and1FC allclear. Alessa readiness00; absent
Sofoubi/Relleck charge/ready fields also00. Their records contain preinitialized
names/default stat data but empty inventories and absent membership; that is
**not evidence they have been recruited or are safe to activate manually**.
No initialized Sofoubi/Relleck checkpoint was identified in the current inventory.

### ROMs remain protected

Use the existing16MiB testROM:
`tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba`
SHA-256 `d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3`.
StandaloneROM remains
`b9967b15193b5aec701032742d322a1040373e76b176b1aeb1e65ce2c06078b6`.
The new post-test source has matching patched identity; the older sources only
support a controlled same-size CRC-warning load trial. The user has now confirmed
such loading/entry worked for the pre-entry source in the early Alessa test.
Do not extrapolate to arbitrary states or the8MiB standalone.

## Five paths: status and actual selector conditions

Exchangeentry08107E81, mainselection08107E90. Full eligibility is FEC0 reading
the selected persistentcharge followed by FD3B exact comparison to40hex. No
readiness-bit or direct party-membership check occurs in this bounded tree.
The NPC also checks exhaustionflag1FC, dialog response, Binky capacity and item
grant failure. Correct character initialization remains required even though
this particular tree does not validate it.

| Selector | Storage/mask | Verified script effect / meaning |
| --- | --- | --- |
|1FC|03003326 /10|At08107E90 branches to exhaustion/retirement dialogue; leaveclear for tests |
|BA|030032FE /04|At08107E9E selects three-character charge/menu tree08107FC0; narrative milestone **unresolved** |
|1C4|0300331F /10|At08107EA6 selects two-character tree08107ED7 if BAclear; narrative milestone **unresolved** |
|Neitherselector|No edit|Early single-Alessa tree08107EAE |

These flags' role as **exchange selectors** is Codex-confirmed static. Their
meaning as “What joined,” “Sofoubi joined,” “Relleck joined” or “Letitbi defeated”
remains Probable/unresolved; no corresponding scene outcome is simulated.
1C4 is not C4 and shares a byte with1C0(mask01); preserve all other bits.

| Endpoint / reset index | Original reward | Patched reward | Runtime status |
| --- | --- | --- | --- |
|08107F52 /1 Alessa, early|1|2|**User-confirmed runtime** under earlyconditions; endpoint identity additionally static inference from supplied state/flags, no live cursor trace |
|0810812E /1 Alessa, intermediate|2|2|Codex-confirmed static; **Untested** runtime |
|081080F7 /1 Alessa, late|3|2|Codex-confirmed static; **Untested** runtime |
|08107F89 /2 Sofoubi|1|2|Codex-confirmed static; **Untested** runtime in both selector trees |
|08108165 /3 Relleck|2|2|Codex-confirmed static; **Untested** runtime |

There is one Sofoubi transaction block reached from different selection contexts,
not a newly established separate Sofoubi two-rate progression block. Relleck's
one-rate hypothesis conflicts with the actual reset-index3 block's original02
operand. Preserve those distinctions and test the genuine branches rather than
inventing scenarios from reported milestones.

## Minimal Alessa tier simulations

**Candidate**, based on Codex-confirmed static branch traversal. No new character,
ROM patch or natural story playthrough is required. Source must be a disposable
copy of the new post-test checkpoint, outside dialogue/battle. Confirm live bytes
individually before any future write; saved values are not a substitute for that.

| Independent test | Proposed selector edit | Other confirmed prerequisites | Exact successful path / original→patched |
| --- | --- | --- | --- |
|Intermediate Alessa first|0300331F: B→B OR10; sourceexpected00→10, affects1C4 only|BAclear,1FCclear, party31, Alessa charge40, Sofoubi03001FF4=00|08107EA6→08107ED7; Alessa passes40, companion2 doesnot;08107F1C→0810812E, **2→2** |
|Late Alessa next, on a separate clean copy|030032FE: B→B OR04; sourceexpected00→04, affectsBA only|1FCclear, party31, Alessa charge40;03001FF4=00 and03002054=00|08107E9E→08107FC0→08107FE7; companions2/3 notfull;08108037→081080F7, **3→2** |

Only Alessa is offered along these particular zero-other-charge paths. Reading
absent companions' zerocharge fields does not initialize or grant their membership.
Do **not** fill an absent character's charge to expose an invalid menu choice.
Do not touch their readybits. Partial Alessa charge remains ineligible.

Scope containment: make the selector change only immediately before this NPC
conversation on an isolated branch; do not travel, start battles, interact with
other NPCs, use an in-game save or promote the altered state as story progression.
These flags may have other readers. Static evidence does not prove their global
side-effect freedom. Discard/reload the entire branch after observation rather
than clearing a flag after unknown events ran. Stop if other dialogue/actors change,
an absent character is offered, the interpreter is busy, or required bytes differ.

The intermediate test is smallest by risk: one selector bit and only one absent
companion charge read. The later one-bit test is more informative for the changed
three-rate reward but checks two absent slots. Test them independently in that order.
A full A/B late test would use the original recruitmentROM on its own separate
disposable old checkpoint plus the same narrowly verified selector conditions;
it is optional future evidence, not performed or necessary to replay now.

## Sofoubi and Relleck initialization requirements

Character/name mapping is source`ta_menus_eng.txt`, RESTRUCT630BDC. Persistent
record base03001EDC, stride60; membershipuppernibble uses10/20/40/80 for indices
0/1/2/3. Low nibble is the selected partner, not a count. Party count is derived.

| Character | Index /membership bit | Record/count/entries | Charge/ready |
| --- | --- | --- | --- |
|Alessa|1 /20|03001F3C /03001F43 /03001F44|03001F94/95 |
|Sofoubi|2 /40|03001F9C /03001FA3 /03001FA4|03001FF4/F5 |
|Relleck|3 /80|03001FFC /03002003 /03002004|03002054/55 |

### Verified generic initialization, not assumed FE49 semantics

FE49dispatch0862B8B4→080252F5; bounded handler080252F4..2536A proves:

- If membershipbit20 absent, initializeindex1 and set `(old & F0) |21`.
- Else if bit40 absent, OR40 into existingmembership and initializeindex2.
- Else, OR80 and initializeindex3. **There is no absent-bit80 guard** on this
  last branch: replay can reset an already recruited Relleck.
- Index stored in utility030018BC+9;08032BF0→08032CB8 initializes that index
  through parameter03001AD2. It does not rewrite the other character records.

Therefore from exact31, a **candidate future interpreter-driven FE49** initializes
Sofoubi and predicts31→71, preserving activepartner1. From a valid initialized71,
a subsequent separately tested FE49 initializesRelleck and predicts71→F1.
**Correction to any naive partner-switch expectation:** this is not31→72 or
71→F3; the second/third branches preserve the low nibble. No native call is made.
FE4A (08025374) only sets the supplied membershipbit; FE4B (080253A4) clearsit.
Neither calls the initializer and neither is a safe substitute for recruitment.

Initializer08032CB8 performs inventorycount/reset, table-driven stat/equipment
writes, ordinary clothing acquisition and charge/ready reset. Default descriptors
08630C14 (index2),08630C30(index3), stride1C are retained in evidence. Verified
writes include character+44/+46 from descriptor+14, +4A from+16, +4B from+17,
+4C from+18, derived+50, zero+54word, and zero+58/+59. It preserves the name
and does not indiscriminately erase every60-byte record field or every equipment
slot. Future preflight must verify zero/valid prior inventory/equipment, capacity
and names, not copy Alessa's record or fabricate stats.

**Blockers for actually testing these candidates:** no verified one-shot carrier
on the existing Oystown checkpoint; interpreter/return context and activation
must be preflighted. Normal scene-specific starting Gimmick grants and other
recruitment effects have not been mapped for these characters. Empty initialized
inventory may suffice for a narrowly scoped exchange-only test (the exchange does
not read Gimmicks), but that is a Candidate, not complete gameplay initialization.
No ordinary battle/partner-switch test should be claimed from that shortcut.
The historical FE49site081166B8 is a multi-reward preparation/warp sequence giving
Alessa's PopHorn, not a verified Sofoubi/Relleck recruitment scene; do not replay it.
No new carrier/payload or complete recruitment scene is authorized here.

After proper initialized-source verification, a future Sofoubi exchange can use
1C4set/BAclear, charge2=40 and othercharge0; later context usesBAset. Both reach
the same resetindex2 grantblock. Relleck requires the verified initializedindex3
source andBAset, charge3=40/othersnotfull to selectresetindex3. Active field
partner need not be changed merely to select a stored full gauge in this tree;
gameplay/menu correctness beyond that remains an independent runtime check.

## Exact recommended next experiment — deferred manual session

Starting ROM: existing16MiB testROM/hash above. Starting checkpoint:
root`after_exchange_oystown_alessa_test.ss0`, hash
`85110875375c28ab412e4413e986d9cb65eb81353d1214f3b86e6d7b7a02f1cf`.
Use a fresh isolated mGBA0.10.5 environment and disposable copies; preserve the
source, original ROMs and previous successful branches. Matching sourceCRC means
no expected version mismatch for this pair. Use independent save/state/patch/cheat
paths, loadStateExtdata=9, saveStateExtdata=9 and rewindEnable=0.

**Do not begin runtime work in this session.** When the next manual session starts,
load only the working copy, pause idle in the field, and perform just this first
debugger observation:

```text
r/1 0x0300331F
```

Expected00. Report it before any other command. An unexpectedbyte is a stop,
not permission to write a presumedconstant. Subsequent observations are requested
separately: BA/exhaustionbytes, membership, absentSofoubi charge, Alessa charge
and Binky inventory quantity. No batchscript or unsupported membershipedit.

After those observations are reviewed in the future session, the conditional
intermediate test would add onlymask10 at0300331F and separately set Alessa's
verified charge to40 by the already validated manual mechanism. Verify each write
with its own read, then interact only with the Hawker and selectAlessa. Expect
offer2, **count4→6** if the working inventory is unchanged, normal charge reset,
normal dialogue and no absent-character option. The original intermediate branch
also awards2, so this tests selection/coverage rather than a new rate delta.
The independentlate test expects original3 versuspatched2. Neither change is
performed or instructed as an immediate write now.

Stop on identity/load error, unexpected startingbits/charge, non-idle events,
party/inventory change, wrong offer/delta, wrong selected reset, freeze or unrelated
scene. Preserve a screenshot/one-command transcript if available under freshnames.
If capturing a successful branch later, export a new idle post-test file; never
overwrite the three protectedrootstates. Record ROMhash, startingstatehash,
exact live old/new byte and observed result. A recommended capture is not assumed
to exist until independently inspected.

## Integrity and scope

**90 current protected ROM/save/checkpoint files unchanged** before/after this
read-only investigation. Includes both exchange outputs and the new user-created
post-test state; all prior protected preflight hashes stillmatch. No ROM/state
builder invoked, no data transformed, no emulator operated. Changed files:
updatedruntime section in`binky_exchange_rate_two.md`; this new planning report;
new read-only analysis script and evidenceJSON. Previous manifests/evidence and
patch implementation preserved. New-character runtime tests remain blocked on
source/carrier preflight; the two Alessa selector simulations are supported
Candidates for a separately authorized user-operated session.
