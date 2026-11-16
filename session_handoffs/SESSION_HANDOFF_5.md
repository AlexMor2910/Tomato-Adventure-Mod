# Tomato Adventure ? Session Handoff 5

Status: documentation closeout and read-only Kaizo proposal. No construction/runtime authorization is conveyed by this handoff. Read AGENTS.md and the modding plan before resuming.

## Completed two-Binky milestone

All six requested reward-rate scenarios are user-confirmed passed: Alessa early/intermediate/late, Sofoubi early/late, Relleck applicable late. Each full0x40 exchange awards2, consumes the selected gauge and completes normally. Relleck final was4?6, membershipF1, BAset. See [complete closeout](../reverse_engineering/experiments/binky_exchange_session5_closeout.md) and [offline checkpoint evidence](../reverse_engineering/experiments/binky_exchange_session5_evidence.json) for exact paths, sizes, hashes, identities, flags and recorded poststates. Snapshots do not prove prior gauge/counts or exchange causation.

Active unchanged ROM: tools/patch/output/binky-rate-two-recruitment-test-aaee9ff3918c42aabf6d9bec7cff611f/binky_exchange_rate_two.gba, SHA-256 d356a6979c497524d1e94306989e09cf8dfe96334a22c664eb3a9570f3ab3ea3. Full-file read-only revalidation confirms118 actual differences against Alessa recruitment source. Do not replace it with a guarded recruitment ROM.

New final Relleck root checkpoint: relleck_initialized_guarded_successful.ss0, SHA-2569de814b789f88989c1a4f0330ff024d4b0d81a7031e15d4c3c2c2bf55ec5ec9c,26683bytes, CRCAB34C118, membershipF1, BAset/1C4clear, Binkies6, all AWEcharge/readiness00, idle interpreter. All character records equal guarded pre-exchange records. Guarded initialization/replay protection and working Relleck Gimmicks were user-confirmed.

Pending exchange regressions: cancellation, partial gauge rejection, inventory-capacity97/98/99, multiple full gauges/nonselected preservation, dedicated save/reload. Do not call these passed. The standalone8MiB rate-two ROM remains a separate static-verified artifact, not the six-test ROM.

## Kaizo approved numbers, exact proposal, no ROM yet

The user approved24 proportional thresholds ending100, preserving order. [Exact static proposal](../reverse_engineering/kaizo_binky_100_proposal.md) and [complete operation/byte ledger](../reverse_engineering/kaizo_binky_100_proposal.json) identify all48 uint16 displayed/comparison operands, original/new bytes, flags, rewards, two cumulative cap edits and one English retirement digit. Expected51 actual changed bytes, no relocation/size change. No Kaizo patch script or ROM was constructed.

Persistent cumulative donations variable30 at030032B7 is distinct from item37 inventory. Change cap comparison000FC7A9 B400?6400 AND clamp000FCCD8 B4?64. General inventory capacity and exchange cutoffs remain unchanged. Message0FA literal180friends?100friends needs only0064FE13 78?70; pointer and65-byte formatting unchanged.

Unchanged whole-stack donations remove5 at99, retain credit100, discard4 surplus. This policy needs explicit acceptance in construction authorization. Missing original prerequisites can delay Choo-Choo even at100 and permit further zero-credit whole-stack donations before finalclaim. Keep all flags/reward IDs unchanged. Completed legacy saves bypass cap and are not migrated. Numeric unlock100 is conditional on original gates/valid inventory, not a blanket story unlock.

Read-only checks passed all original operands/contexts and18,100 arithmetic cases. No runtime Kaizo outcomes are claimed. Receiving-capacity, multi-gift bursts, prerequisites and return/save behavior require later manual tests from an audited Kaizo-accessible checkpoint.

## Protected state and next action

388 preexisting protected ROMs, saves, checkpoints, scripts, manifests and old outputs fingerprinted before work; final equality audit is recorded in the closeout. Documentation-only updates are authorized; earlier artifacts and historical manifests remain preserved. No mGBA/RAM/gameplay/Git action, no Kaizo or early-NPC ROM modification.

Next: request explicit OFFLINE construction approval for the exact51-byte Kaizo proposal, including acceptance of unchanged whole-stack surplus behavior. Runtime needs a separate authorization. Never reuse contaminated unguarded Sofoubi state. Silent companion initializers are non-atomic; interruption means discard/restart clean, not guessed repair. User performs all emulator actions, one debugger command at a time. Early-area exchange NPC work remains deferred.
