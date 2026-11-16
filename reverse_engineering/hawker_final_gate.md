# Final Hawker implementation gate — 2026-10-16

**BLOCKED — NO ROM MODIFIED.** No patcher or Hawker ROM was produced. This is
a bounded follow-up, not proof that the proposed placements are impossible.
The five checks have partial static support, but none has a complete safety proof.
The user's conditional implementation authorization therefore has not activated.

Reproduce the read-only evidence with `python -B tools/analyze/hawker_final_gate.py`.
Saved output: `hawker_final_gate_evidence.json`. Historical reports and manifests
were not overwritten. The script reproduces both prior native-analysis datasets
(normalizing Python tuples to JSON arrays), hashes protected artifacts before and
after, and independently compares the current cumulative ROM with its Kaizo parent.

## Five safety checks

| Check | Result | Established evidence | Exact missing evidence and risk |
|---|---|---|---|
| Scratch binding | BLOCKED | Dispatcher writes clicked slot at `080697CA` to RAM `03003A32`; ordinary-interaction gates exist. | Complete write/alias audit of transitive dialogue, event and continuation paths, including interruption and cancellation. Locks exclude another ordinary interaction but do not exclude internal scratch writes. A substituted slot can animate another actor or index outside the intended records. |
| Scoped FE31 adapter | BLOCKED | Ten exact shared-command sites and dispatch pointer `0862B978` are known. | Concrete verified ownership discriminator, actual argument-cursor provenance, fallback and register contract. Map + command-site + scratch-slot equality does not independently prove ownership if scratch lifetime remains unproven. No adapter was assembled or installed. |
| Movement | BLOCKED | Targets `(407,111)` and `(231,127)` encode correctly and have base collision 00. | Full movement scheduling/completion and interaction-reach analysis with dynamic occupancy and door triggers for every reachable approach. New native trace shows command36 continuation decisions depend on downstream state. A walkable endpoint cannot exclude failed approach or control recovery problems. |
| Graphics lifetime | BLOCKED | Eleven frames, initialization format, free graphics slots, tile budgets and palette allocations reproduced. Mayonen palette5 stays reserved for doors. | Closure over room defaults, actor initializers and deferred/event resource writes through entry, interaction and re-entry. Initial capacity is not a lifetime guarantee; later writes could replace tiles/palette. Namp gesture opaque overlap remains unproven. |
| Persistent identity | BLOCKED | 15-NPC loader limit, append slots7/8 and absence of candidate IDs0BFE/0BFF in 2,987 map actor records reproduced. | Persistent-ID consumers, save/flag addressing and script references have not established that either ID is unused and in range. Table relocation needs complete pointer/size/allocation validation. Reusing an ID can inherit visibility/state; an invalid index can address unrelated state. |

These are missing proofs, not observed runtime failures. Accepted coordinates and
slots remain unchanged. No newly discovered address is labeled runtime-confirmed.

## Additional bounded native evidence

All bus addresses here are **English translated/cumulative ROM** addresses;
subtract `08000000` for file offsets. RAM has no ROM offset. No new Japanese-ROM
equivalence claim is made. Source symbols below are analysis-helper window names,
not recovered game symbols. Status is **Confirmed static instructions**, with
transitive effects explicitly unproven.

| Bus range, end exclusive | Helper window | Evidence and implication |
|---|---|---|
| `08029E20..08029E30` | FE C8 dialogue entry | Sets argument140 and calls `08029DAC`. |
| `08029D98..08029DA8` | FE66 dialogue entry | Sets argument0 and calls the same bridge. |
| `08029DAC..08029DBE` | shared dialogue bridge | Writes `03003E8B`, then calls `08028C48`. That call and downstream dialogue execution remain a concrete scratch-writer audit dependency; this window alone neither overwrites nor proves preservation of `03003A32`. |
| `08066476..080664A8` | movement deltas accepted or cleared | Accepted deltas and cleared deltas both lead to `080664A8`. |
| `080664A8..08066512` | movement scheduler entry | Reads actor/deltas from `030018F0`; branches to `08066528` or onward to `080669C8`. These destinations require bounded continuation analysis. |
| `08023CD2..08023D00` | command36 continuation decision | Calls movement setup then `0802FEF0`; the zero branch calls `0806A540` and `0806A5A0`. Completion cannot be inferred from endpoint collision alone. |

Exact bytes, per-window SHA-256 and disassembly are in the new JSON. Literal pools
are excluded from these instruction ranges. The custom disassembler is an existing
static helper, not an emulator or a complete control-flow verifier.

## Architecture and shortest safe next work

Retain the candidate architecture: room wrappers provide only X/Y; native FE01
passes the approach continuation to player0; all transaction/progression/reward
branches remain authoritative. Keep Mayonen graphics5/palette6 and Namp
graphics7/palette7, append actors8/7 respectively. Do not install a global FD
operand replacement. No code or data allocation has been approved by this report.

The next bounded static step is the transitive write audit rooted at `08028C48`
and its dialogue consumers, together with the exchange's native callees. Track
aliases and bulk copies covering `03003A32`, not only literal-address references.
In parallel only conceptually, close movement scheduling from `08066528` through
`080669C8` and its completion consumers. No whole-ROM disassembly is required.
Then audit the two rooms' reachable resource writers and persistent-ID consumers.
Do not repeat already established map identification, opcode semantics or capacity
inventories. A successful scratch audit alone would still leave the other gates.

If a runtime scratch observation is needed to guide that audit, the user can make
**one bounded read-only observation on the unchanged cumulative ROM**: watch writes
to halfword `03003A32` for one normal interaction with the existing Oystown Hawker,
choose cancellation, and stop recording as soon as player control returns. Expected
initial value is actor slot3; expected preservation is no later change away from3.
Record any later writer PC/value and stop immediately if it changes or the game
stalls. Do not edit RAM, gauges, saves or savestates. Remove the watchpoint afterward.
This samples cancellation only and cannot certify successful/capacity/other branches.
Codex did not execute this observation or operate mGBA.

## Baseline, integrity and regression results

Input: `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`,
16,777,216 bytes, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
Parent Kaizo ROM SHA-256:
`7e7603816afb0990eea51ed2c49ab4b4afd5596ff1c4211c656d608e94ed2aa2`.

Independent full-file parent comparison reproduced exactly two differences:
file `00638056`: `87 -> 78`; file `0063805A`: `26 -> 19`.
Thus all other parent bytes, including translation, Alessa wrapper, authoritative
two-Binky transaction, Kaizo reward conditions/IDs/flags, original Hawkers and
tutorial, are byte-identical. All 51 Kaizo ledger bytes were additionally read
back against its manifest. Detector reads120/25; Dragon reads262/54. GBA header
complement validates; this is not a whole-ROM checksum or a runtime guarantee.

115 scoped ROM/save/savestate artifacts retained their fingerprints across this
audit. The inventory includes .gba/.sav, .ss0..ss9 and files under savestates;
it does not claim to identify every possible checkpoint extension elsewhere.
No ROM bytes changed this run; no output identity/hash or Hawker difference ledger
exists because construction was withheld. Existing runtime coverage remains
historical; no new gameplay, re-entry or save/reload testing occurred.

## Manual acceptance after a future gate-passing build

Do not attempt added-Hawker acceptance on this unchanged ROM. Once a build passes
all gates, use disposable save files and record the mGBA version:

- Namp: exact placement, independent blue-NPC interaction, correct actor animation,
  approaches from each reachable side, exchange, control recovery, exit/re-entry.
- Mayonen: exact placement, both door groups accessible, every animation intact,
  approaches from each reachable side, exchange, exit/re-entry.
- Shared: every eligible character, exactly two Binkies, correct gauge reset,
  cancellation/insufficient charge/capacity/retirement branches, shared state and
  no duplicates; original Hawkers and original Oystown tutorial still work.
- Regression: Kaizo thresholds/rewards/conditions, Detector120/25, Dragon262/54,
  other NPCs/transitions, and disposable save/reload without interaction corruption.

**Final status: BLOCKED — NO ROM MODIFIED.**
