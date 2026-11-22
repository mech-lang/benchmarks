# Packed-node histogram batching

The source compiler can now batch 4, 8 or 16 literal records and optionally commit them in four-record chunks. **The repaired sixteen-record arm preserves every named 81/81 Roc and 63/81 libdeflate win in both full81-case, 96-block orders.** This advances elapsed time on remaining random-input losses; it does not add a 64th libdeflate win. The original 2,719-line Mech codec and canonical bytecode are unchanged. There is no new LLVM dependency or native-byte patch.

The repaired encoder is **63,784 B**, 592 B larger than the retained 63,192-B control. The original all-or-nothing sixteen-record arm is 32 B smaller and slightly faster on random1MiB, but adds work on mixed records. The repair retains useful four-record prefixes when a later chunk contains a nonliteral, reducing that penalty. The 63,112-B immutable-word partial is also combined with both repaired group widths; those alternatives and all slower trials remain available.

## Full-suite runtime

Times are milliseconds per complete call. Ratios use paired block observations; rounded medians need not divide to the paired ratio. These are point estimates, with no formal confidence claim. Measured on Apple M1/macOS arm64. No compiler construction, tests, diagnostics, archives or Git work overlaps primary clocks.

| Case / order | Mech ms | Matched control ms | libdeflate ms | Mech ÷ C | Mech ÷ control | Mech reduction to C parity |
|---|---:|---:|---:|---:|---:|---:|
| prefix-random-1048576, forward | 22.558480 | 22.822229 | 20.358958 | 1.107937× | 0.988106× | 9.74% |
| prefix-random-4096, forward | 0.106604 | 0.107583 | 0.076562 | 1.397280× | 0.988095× | 28.43% |
| prefix-natural-1024, forward | 0.070542 | 0.070667 | 0.059000 | 1.196981× | 0.998408× | 16.46% |
| prefix-random-1048576, reverse | 22.561604 | 22.817062 | 20.356063 | 1.109546× | 0.988452× | 9.87% |
| prefix-random-4096, reverse | 0.105022 | 0.104937 | 0.077354 | 1.371579× | 0.995345× | 27.09% |
| prefix-natural-1024, reverse | 0.070709 | 0.070833 | 0.058958 | 1.203771× | 0.997128× | 16.93% |

The original 21-case discovery orders and all one-case screens are saved as well as the full qualification. Small slowdowns remain included. The score requires the original named wins, rather than substituting different cases.

## Actual instruction counts

These counters cover the complete packed-histogram phase across all calls for each fixture, outside all primary timing. The repaired sixteen-record arm keeps just four packed words live at a time, eliminating the original wider arm's loop spills. Function-local frames change; the complete measured peak remains **4,736 B**, below 5,280 B.

| Arm | Encoder B | Random1MiB instructions | Random1MiB stack loads | Natural1KiB instructions |
|---|---:|---:|---:|---:|
| control | 63,192 | 42,754,146 | 22 | 34,201 |
| narrow-8 | 63,368 | 36,512,865 | 44 | 49,222 |
| narrow-16 | 63,752 | 34,157,936 | 389,646 | 96,622 |
| progressive-8 | 63,416 | 39,026,328 | 44 | 34,818 |
| progressive-16 | 63,784 | 35,665,337 | 44 | 34,604 |

Keeping keys at I64 instead of narrowing and extending changes the instruction body at equal byte counts; it did not provide a demonstrated runtime improvement. Those alternatives are measured independently.

## All first-stage screens

These random1MiB measurements are from separate campaigns with matched controls. Cross-campaign absolute times alone do not prove improvement.

| Recipe | Encoder B | Random1MiB ms, forward / reverse |
|---|---:|---:|
| control | 63,192 | control |
| wide-4 | 63,192 | 22.85527 / 22.85544 |
| narrow-8 | 63,368 | 22.58473 / 22.58923 |
| wide-8 | 63,368 | 22.59483 / 22.61548 |
| narrow-16 | 63,752 | 22.49031 / 22.50260 |
| wide-16 | 63,752 | 22.51892 / 22.50929 |
| progressive-8 | 63,416 | 22.66348 / 22.66558 |
| progressive-wide-8 | 63,416 | 22.68196 / 22.69444 |
| progressive-16 | 63,784 | 22.55235 / 22.56012 |
| progressive-wide-16 | 63,784 | 22.55696 / 22.55781 |
| compact-progressive-8 | 63,336 | 22.95065 / 22.94015 |
| compact-progressive-16 | 63,704 | 22.83998 / 22.83494 |

## Proof and verification

The existing entry admits initialized current node/counter extents, nonoverflowing addresses and disjoint whole views. A selected source literal proves the first node read was valid. The four-visit prefix additionally proves `cursor < end`, `end - cursor >= 4` and `ordinal >= 3`. Every chunk checks all of its literal tags before its first increment. A larger extension is read only after its complete logical window is admitted. On a mixed chunk, execution resumes the original iteration boundary at that uncommitted chunk. Counters remain wrapping u32, and loads/stores stay ordered so repeated keys observe preceding increments. Checked source errors, partial writes, finite admission, allocations and cleanup are preserved.

The first policy tests execute **332,850 native calls**; expanded tests execute **618,180**, covering full-word keys, unsigned wrap, every group tail, collisions, short counter extents, checked partial writes and overlapping node/counter storage. Maintained scalar Bool/U64/I64/F64, select, range, current-predicate, SSA and increment families pass. Every one of the twelve retained arms passes 162 exact output/alias/resource observations, six checked failures and twelve injected failure/recovery pairs, with 4,736-B measured peak stack. **24 public normal/checked source replays** reproduce object, full metadata and bytecode exactly. The full GPU suite is not claimed.

`summary.json` contains the complete matched source-through-final-executable-link timings. Compilers and fixed support are equally prebuilt. Bootstrap and strip are separate. All six actual timed stripped executables are run on all 81 fixtures; all 486 raw output streams are saved and independently inflated.

```sh
python3 benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/packed-node-histogram/build_compiler.py /tmp/mech-histogram-compiler
python3 benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/packed-node-histogram/reproduce.py /tmp/mech-histogram-compiler/release/compile_profile /tmp/mech-histogram --role progressive-16
python3 benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/packed-node-histogram/verify.py
```

The new options are `MECH_GROUP_PACKED_HISTOGRAM_VISITS`, `MECH_GROUP_PACKED_HISTOGRAM_WIDE_KEYS` and `MECH_GROUP_PACKED_HISTOGRAM_PROGRESSIVE`. They remain off globally; the existing grouped path stays at four visits unless a measured recipe selects another policy.

**1× libdeflate across all 81 remains the goal; 64 wins is the next milestone.**

## Complete builds

| Actor | Source through final executable linking | Strip, separate |
|---|---:|---:|
| mech-control-reference | 2.215325 s | 0.010938 s |
| mech-new-disabled | 2.206352 s | 0.010955 s |
| mech-narrow-16 | 2.205781 s | 0.011018 s |
| mech-progressive-16 | 2.202964 s | 0.010833 s |
| roc | 2.988344 s | 0.010869 s |
| libdeflate | 0.481597 s | 0.010852 s |

Twelve balanced serial orders; equally prebuilt compilers and fixed support. Source, final linking and strip are recorded separately. Compiler construction is outside these clocks.
