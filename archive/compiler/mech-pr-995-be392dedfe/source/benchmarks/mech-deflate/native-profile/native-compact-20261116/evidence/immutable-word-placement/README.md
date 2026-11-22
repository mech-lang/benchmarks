# Immutable input-word placement experiments

Measurements use Apple M1, macOS 15.6.1, arm64. Ratios compare elapsed time;
smaller is faster.

The qualified default remains **63,192 B, 81/81 Roc wins and 63/81 libdeflate
wins**, established in both full 81-case, 96-block orders. The next win is still
random 1 MiB: **22.82 ms Mech /20.34–20.36 ms libdeflate**, about **1.122× C**,
requiring **10.8–10.9% less Mech time**. See the qualified
[complete parity table](../matcher-scalar-choices/PARITY.md).

The optional compiler implementation at
[`03f992974`](https://github.com/mech-lang/mech/commit/03f992974ee708735b261a43ac8ff37f52dc5c62)
schedules one immutable four-byte prefix beside an earlier overlapping input
read. Only a private fixed immutable view may qualify. A full-word logical
bound selects the input address or immutable zero storage; source guards,
errors, effects and resource accounting stay in place. The original 2,719-line
Mech codec and canonical bytecode are unchanged. The option is off globally:
`MECH_COMPACT_SCHEDULE_IMMUTABLE_WORDS=mech_compact_numeric_475_vector`.

## First measured attempt

All four alternatives pass both 21-case, 96-block discovery orders without
losing a required named panel win. These are discovery panels, **not new
full 81-case qualifications or a 64th C win**. The added guard costs elapsed time:

| Alternative | Encoder B | Mech 1 MiB ms, forward/reverse | Paired Mech÷C, forward/reverse |
| --- | ---: | ---: | ---: |
| Scheduled, linear | 63,272 | 23.260563 /23.255625 | 1.145718 /1.145419× |
| Scheduled, square root | 63,288 | 23.316708 /23.318250 | 1.148451 /1.148648× |
| Scheduled + range proof, linear | 63,208 | 23.269896 /23.268792 | 1.146207 /1.146483× |
| Scheduled + range proof, square root | 63,240 | 23.314938 /23.313584 | 1.148677 /1.146823× |

Complete fresh-process source-through-final-executable linking, 12 balanced
serial orders with equally prebuilt compilers/support:

| Compiler/recipe | Seconds | Paired time÷Roc | Paired time÷C |
| --- | ---: | ---: | ---: |
| Mech matched qualified control | 2.204909 | 0.738549× | 4.586948× |
| Mech scheduling, linear | 2.204371 | 0.738319× | 4.587002× |
| Mech scheduling + range proof, linear | 2.207356 | 0.739832× | 4.594592× |
| Roc | 2.983681 | — | — |
| libdeflate | 0.480550 | — | — |

No compile-time gain is established. Parsing/frontend/native/link medians for
the scheduling arm are 0.703216 / 0.218471 /1.210954 / 0.035306s; independent
medians need not add. Bootstrap and strip are separate. Primary clocks exclude
all other builds, tests, sampling, counters, archives and Git work.

Every raw, weighted and final scheduling candidate passes 162 exact
output/inflation/alias/resource checks, six checked errors and 12 injected
recoveries. Peak stack is 4,736 B, under the 5,280 B cap. Two new unit tests pass,
including 5,712 actual before/after native boundary calls. Maintained scalar,
select, range, predicate and SSA families pass; the full GPU suite is not
claimed. Both raw training arms have nine actual counter cases, followed by
fresh register weights and four fresh machine layouts.

A first early-hook repair matched zero reads and reproduced its no-schedule
controls' object, metadata and bytecode exactly. That is a proof miss, not a
guard-removal or runtime improvement. An early normalization attempt also
matched zero reads. The current repair keeps the successful later placement
and refines its bounds using the already-admitted entry span. It matches one
read and removes both added guards. All four repaired layouts pass strict
native checks, with a smallest encoder of **63,112 B** and peak stack of
**4,736 B**. Two new refinement tests
pass, including **120,960 native boundary/error/effect calls**. The new compiler
also reproduces all ten older public normal/checked source replays exactly.
All partial alternatives remain retained.

Both discovery orders preserve the required named panel wins for every
repair, but all four remaining-loss aggregates are slower than their matched
Mech controls. The 63,112-B alternative is retained for further repair;
the qualified default is unchanged. Smaller absolute 4 KiB times in some runs
do not establish a gain: their matched Mech controls are faster too.

| Span-refined alternative | Encoder B | Mech 1 MiB ms, forward/reverse | Paired Mech÷C, forward/reverse |
| --- | ---: | ---: | ---: |
| Linear | 63,224 | 22.945458 /22.946667 | 1.131160 /1.130498× |
| Square root | 63,224 | 23.069125 /23.067292 | 1.136222 /1.136935× |
| Range proof, linear | 63,192 | 23.015333 /23.002458 | 1.133754 /1.133066× |
| Range proof, square root | 63,112 | 23.104750 /23.096729 | 1.138142 /1.138587× |

Complete source-through-final-link builds take **2.206614 s linear /
2.210303 s compact /2.988301 s Roc /0.483477 s C**, paired 0.738559 /
0.739152× Roc and 4.563712 /4.571125× C. These 12 balanced serial orders
establish no compile-time gain. A later-placement experiment will shorten the
moved word's live range without weakening its bounds or ownership proof.

## Later placement

The next version advances only through total integer calculations and
single-predecessor unconditional edges, stopping before a load, effect, trap
or conditional branch. A 128-instruction limit bounds the search. Both early
and later placements pass 11,424 before/after native calls, with the IR order
checked explicitly. Seeded-span and maintained scalar/proof tests also pass.
The new compiler reproduces all 18 earlier public source replays exactly.

Both measured alternatives preserve all required named wins in both 21-case,
96-block discovery orders, but still trail the qualified control:

| Later placement | Encoder B | Mech 1 MiB ms, forward/reverse | Paired Mech÷C, forward/reverse |
| --- | ---: | ---: | ---: |
| Linear | 63,224 | 22.935416 /22.932917 | 1.129419 /1.129625× |
| Range proof, square root | 63,112 | 23.089187 /23.089395 | 1.136503 /1.137708× |

Fresh complete builds take **2.213197 s linear /2.214189 s compact /
2.992220 s Roc /0.481315 s C**, in 12 balanced serial orders. Bootstrap and strip
remain separate. No compile-time improvement or 64th C win is established.
All four later layouts pass native/error/recovery checks at 4,736 B stack; only
the two alternatives above have fresh elapsed-time measurements. Two existing
packet-qualifier combinations change metadata alone: native objects,
bytecode, every function body and register-allocation inputs are identical,
so no new timing is inferred from them.

The [cache-bound census](cache-bound-census.json) identifies 1,052,471 actual
cache-length comparisons in the qualified random 1 MiB matcher. Its cache-length
register is loaded once at entry and otherwise only restored at exit. This
is an instruction/work count, not a cycle-saving estimate. The next broader
investigation retains the original 1,500,000 cache stop condition and examines
whether the real 1,500,513-cell extent plus proved per-position increments
admits these accesses. First-iteration, wrapping, effects, budgets and errors
must remain checked; the limit is not fuel. Packed-node histogram guards remain
a separate broader target. The qualified default is unchanged.

## Source reproduction and raw timings

Five [source recipes](recipes.json) include the qualified control and all four
measured alternatives. Ten normal/checked public replays reproduce the object,
complete metadata and bytecode exactly. From this directory:

```sh
python3 build_compiler.py /tmp/mech-immutable-compiler
python3 reproduce.py /tmp/mech-immutable-compiler/release/compile_profile /tmp/mech-immutable-replay --role scheduled-refined-linear --checked
python3 verify_runtime.py
python3 verify_runtime.py --span
python3 verify_runtime.py --delay
```

The [original samples](runtime-manifest.json) recompute all eight panel orders
and paired ratios: **5,741,568 observations**, including **938,711 retained
zero-duration samples**. Every four-actor order occurs equally often. The
verifier checks fixture sizes, C's pinned output oracle, unchanged aliases,
inflation, cleanup and every required named panel win. This verifies the
reported slower trials; it does not add a full-suite win or confidence claim.
The second command verifies the separate [span-repair samples](span-runtime-manifest.json)
and [measured tables](span-results.json). Four additional `span-*` source
recipes reproduce the repaired objects and their original metadata/bytecode.
The `--delay` command checks the separate [later-placement samples](delay-runtime-manifest.json)
and [measured tables](delay-results.json); the two `delay-*` recipes reproduce
those timed encoders from source.

## Instruction-address profiles

The checked-in [profile inputs](profile-data/manifest.json) contain the exact
qualified Mech and pinned libdeflate workers, raw timer-PC tables, symbolicated
tables and 1,000 verified encodes per actor. Mech matching/scoring account for
74.26% /14.01% of encoder sample weight; C's near-optimal encoder/minimum-cost
path account for 68.96% /25.85%. Function boundaries differ, so these are sampled
function shares, not comparable exact phase elapsed times.

The hottest Mech neighborhood includes the current input-prefix read at
matcher offset 0x530 (14.56% of encoder sample weight at that PC). Asynchronous
samples can skid; this does not assign exact cycle cost to that instruction.
Both implementations already prefetch. Trace bundles and environment
inventories are excluded from this capsule.

On macOS with `otool`, reproduce both complete mappings and verify all saved
profile observations:

```sh
python3 verify_profiles.py
```

The verifier binds every input hash, checks raw-PC versus symbolication
addresses, handles duplicate C outline symbols, validates assembly and
reproduces both derived reports exactly. The register-profile helper
[validates zero-data relocations](derive_register_weights.py) while retaining
the existing no-call/no-indirect/no-literal CFG decoder requirements.
