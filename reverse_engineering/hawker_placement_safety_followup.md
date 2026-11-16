# Hawker placement: implementation safety follow-up

Subsequent resolution: [hawker_dependency_resolution.md](hawker_dependency_resolution.md)
establishes FE31's animation-controller meaning and the movement coordinate
encoding. It **corrects this report's FE01 body/continuation ownership claim**:
actor0 receives the approach continuation; the original interaction context keeps
the exchange body. Consult that newer report before implementing a wrapper.

2026-10-15. **Stopped before ROM patching under the user's critical-dependency
stop condition.** This is an extension of `hawker_placement_investigation.md`,
not an implemented placement experiment. No new gameplay ROM or patcher was
produced. The final Hawker objective remains incomplete.

## Confirmed scope

The service question in the earlier investigation is resolved: reuse the existing
full eligible AWE gauge exchange, which **awards two Binkies**. Do not introduce a
two-Binky payment, shop stock, new dialogue, new eligibility rules, or a relocated
tutorial. Kaizo is complete; Detector remains 120 HP / 25 base mitigation;
Rattlin' Dragon remains 262 / 54.

Input is `tools/patch/output/detector-hp120-mit25/detector_rebalance.gba`,
16 MiB, SHA-256
`124c04798e3e9769381f6105fc602794a249c169290b4fc86d735592ae8d9db0`.
It was read only. All bus addresses below use the English cumulative input;
subtract `08000000` for ROM file offsets. RAM addresses are not file offsets.

## Established targets

| Map | Map record bus / file | Actor block bus / file | Candidate cell | Existing actors |
|---|---|---|---|---:|
| Namp 005F | 0862DE48 / 0062DE48 | 08145010 / 00145010 | (25,5) | 6 |
| Mayonen 004D | 0862DC50 / 0062DC50 | 08144388 / 00144388 | (14,6) | 7 |

**Confirmed static:** the original records, dimensions, occupants, base-collision
bytes and screenshot/background matches are documented in the initial report
and JSON. Both cells have base collision 00 and no initially coincident actor.
**Not yet certified:** full Hawker sprite footprint, facing and interaction
accessibility at these cells. The coordinates have not been changed or rejected.

## Newly established actor-context hazard

**Confirmed static:** the authoritative exchange at `08107E81..081081DA`
contains ten literal `FE31 03 01` commands. Five are in successful transaction
blocks, five in advice/refusal/cancel/capacity/retirement paths:

`08107F56`, `08107F8D`, `081080FB`, `08108132`, `08108169`,
`0810819C`, `081081A8`, `081081B4`, `081081C0`, `081081CC`.

FE31 dispatches to `08028ED0`, fetches its first argument, and calls actor resolver
`08022798`. That resolver leaves literal 03 unchanged. Its special cases are FF
(current event context at `030039C0`), FE (context-linked actor), FD (scratch
halfword +14), and FC (scratch halfword +12), not a reinterpretation of literal03.
The second argument is fetched separately. Native `08065E4C..08065E76` computes:

```
record = 03001BDC + 0x30 * actor_argument
record[3] = (record[3] & 0xF8) | state_argument
```

Consequently this command updates actor3's low state bits to 1 at RAM
`03001C6F`. The precise gameplay meaning of state1 is **unresolved**; do not call
it a facing direction, visibility bit, sound effect, or harmless no-op.

The map actor loader at `0803424C..08034292` starts its runtime slot counter at1,
uses that counter to index `03001BDC`, and advances it once per 16-byte actor
record at `08034696..080346B2`. Therefore, in Namp, literal3 refers to the
existing blue NPC at `(26,5)`, record `081450A0`, interaction `081130ED`.
In Mayonen it refers to the existing third record `08144418`, rather than a newly
appended eighth actor. Appending a seventh/eighth Hawker and directly reusing the
exchange cannot be certified to preserve the existing actors' behavior.

This is evidence of a dependency, **not runtime evidence of corruption**. Some
original exchange users also occupy slots other than3, so intentional original
semantics must be understood before rewriting the shared command.

Do not blindly replace 03 with FF: the exchange starts with `FE01 00` pointing
to body `08107E90`. FE01's native handler `0802886C..08028928` installs an event
for its explicit actor argument. The body is thus associated with actor0;
current-event context is not proven to mean the interacting Hawker.

## Wrapper operands are not safely portable constants

**Confirmed static:** existing wrappers at `08102D27`, `08102D37`, `08102D47`,
and `08102D57` each set FD01/FD02 halfwords, call the same `08107E81` entry,
and return. FD01 handler `080266F4..08026712` writes scratch
`03003A24+6`; FD02 handler `0802671C..0802673A` writes scratch +8.
These are separate from the shared donation/progression flags and inventory.

Entry bytes at `08107E88` are `FD84 00 36 06 08`. FD84's bounded native trace
shows argument indirection into scratch, through `08022A84`, followed by command
dispatch. Main command36's table entry at `0862B5D4` is Thumb pointer
`08023CA5` (code starts `08023CA4`). It consumes four argument bytes and calls
`080663C0`. That routine compares two halfword targets against actor fields
+28 and +30 and feeds the resulting deltas into `080664A8`.

**Probable:** the wrapper halfwords are positional/movement targets used for the
player's exchange approach sequence. Their values differ across original rooms:
Oystown 0086/0087, map00D7 0036/0071, map0149 0077/0070,
map015D 009E/0078. Exact coordinate units, origin, actor movement constraints,
and safe new values remain **unresolved**. Copying an original wrapper could
direct movement toward a position belonging to another room. No replacement
halfwords are proposed without resolving those details.

## Graphics evidence and remaining resource work

Actor initialization `08034324..080343A4` extracts byte1's low five bits for an
allocation lookup, byte2's low nibble into actor field+4, and byte2's high nibble
into field+9. These are **confirmed operations**. Interpreting the first and last
indices as graphics and palette bindings is **Probable**, supported by these
matching original Hawker records:

| Map / actor | Record bus | Candidate graphics entry -> descriptor | Candidate palette entry -> data |
|---|---|---|---|
| 00D7 / 4 | 0814B390 | 0814B300 -> 0813F77C | 0814B340 -> 0843C3CC |
| 0104 / 3 | 0814D4C4 | 0814D440 -> 0813F77C | 0814D480 -> 0843C3CC |
| 015D / 5 | 081521C8 | 0815212C -> 0813F77C | 0815216C -> 0843C3CC |

Descriptor `0813F77C` contains
`08 08 00 33 6C C9 40 08 78 1E 45 08 60 48 44 08`.
Do not interpret its 08/08 fields as certified pixel dimensions. The fourth
exchange actor, map0149 / actor3, instead initially binds descriptor `0813F42C`
and palette `0843B1EC`; it is not evidence that all initial actor records are
interchangeable. Complete loading/animation/state-dependent rebinding and palette
allocation capacity have not been certified for either destination room.

## Tutorial and transaction preservation

**Previously confirmed static:** the Oystown introduction at `081084CA`, guard
1F4, and its flag setter at `081086F0` are separate from the exchange entry.
No tutorial relocation or automatic new-room activation is necessary merely to
call the exchange. No introduction script was changed.

The existing exchange retains retirement flag1FC, BA/1C4 selection branches,
full AWE checks, five two-Binky grant endpoints, capacity checks, and selected
gauge resets. The evidence captures the current authoritative script bytes.
**User-confirmed runtime:** the prior exchange and Kaizo milestone remain the
accepted baseline. **Unverified:** either new location; neither was installed.

## Safest implementation path, once the dependency is resolved

Keep a single transaction implementation and the separate Oystown introduction.
First establish why the original exchange sets actor3's state and how to bind
that operation safely for an appended NPC without changing original behavior.
Then establish the movement-target encoding and verify both complete approach
sequences, sprite/palette loading, footprint and interaction range. Actor
persistence IDs and available resource slots also require validation.

The previously proposed relocation of each complete actor block remains a
**Candidate architecture**: retain all original actor bytes and header bindings,
append one actor/resources in verified capacity, and redirect only each map's
+14 actor-block pointer. Do not consume neighboring bytes at the old terminator
or renumber existing actors to force a literal3 reference to work.

## Reproduction and verification

Run `python -B tools/analyze/hawker_placement_safety.py`. It accepts only the
exact cumulative input hash and emits JSON to stdout. It disassembles 16
explicit, bounded native instruction windows and decodes five explicit script
ranges; it does not emulate or modify any ROM. Evidence is saved separately as
`hawker_placement_safety_evidence.json`, including hashes and original records.

The before/after hash ledger covers **43 existing ROM/save/checkpoint artifacts**;
all matched. Input hash was independently reread after analysis. Detector and
Rattlin' Dragon fields were read back as 120/25 and 262/54. No game artifact was
written, so there are **zero changed ROM regions**. No new-build static regression
or runtime success is claimed. No emulator or Ghidra was launched.

New artifacts: this report, the adjacent safety evidence JSON, and the bounded
analysis helper. The initial placement report receives only a pointer to this
follow-up; existing enemy research remains intact. Inputs consulted include
AGENTS.md, the modding plan, both initial Hawker investigation artifacts,
`experiments/binky_exchange_rate_two.md`, `experiments/detector_hp120_mit25.md`,
`tools/patch/detector_rebalance.py`, `tools/patch/alessa_recruitment_wrapper.py`,
`tools/analyze/binky_exchange_rate.py`, `pre_oystown_progression.py`,
`thumb_inspect.py`, `tomatotrans-1.1.1/asm/name_long.asm`, and
`tomatotrans-1.1.1/notes/SCRIPT.md`, plus the fingerprinted cumulative ROM.

## Runtime checklist after a statically verified build exists

1. On disposable save copies, enter each room from every normal entrance; verify
   Hawker appearance at the agreed cell, original NPCs, exits and door access.
2. Interact from each accessible side; watch the player approach, nearby blue NPC,
   original room actors and all return/cancel paths for unintended changes.
3. Exercise a successful full-AWE exchange, non-full refusal, cancellation and
   inventory-capacity refusal; verify exactly two awarded Binkies and only the
   selected gauge consumed on success. Repeat across original/new Hawkers.
4. Verify shared progression/retirement behavior and absence of tutorial activation
   in the new rooms. Test Oystown's original first-visit introduction separately
   with an appropriate pre-tutorial save, then its post-tutorial exchange.
5. Leave/reenter, save/reload, and check occupants/navigation and shared exchange
   state again. Runtime validation is user-operated and has not occurred here.
