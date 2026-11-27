# Round 2 integrated compiler qualification

The integrated compiler at `3a66a014c853e082ad907ed4db1673c9dadf0c69` passed the required correctness checks and the compiler elapsed-time and memory gates on Apple M1. Runtime qualification is blocked at the same-build calibration. The record contains six completed calibration sessions and zero candidate timing sessions. The final 81-fixture and 12-file Silesia win counts remain unverified.

## Source and build

| Role | Commit |
| --- | --- |
| Reviewed compiler R | `8ce620d1b165b868210378ef260945ee3c398d05` |
| Previous measured compiler O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` |
| Qualified memory repair N | `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea` |
| Integrated compiler F | `3a66a014c853e082ad907ed4db1673c9dadf0c69` |
| Benchmark tooling | `522da9237cc941880934339e403781b21fe89741` |

F incorporates the frozen heads of [PR #995](https://github.com/mech-lang/mech/pull/995), [PR #999](https://github.com/mech-lang/mech/pull/999), and [PR #1000](https://github.com/mech-lang/mech/pull/1000). The captured heads matched the integration inputs. The new checked-root register profile reaches the existing selected-profile cache at the original emission point. The full-encoder test verifies stale-profile rejection and a single file read across retries. The timed recipe omits both new emitter options, and the qualification verifies that the existing register-profile names select no new root. [Frozen inputs and rebuild receipt](qualification/)

F produced the exact pinned object, bytecode and per-worker descriptors. Its own compiler, linked fixture worker, Silesia executable, runtimes and allocator each have verified hashes in the actor bindings. The rebuilt release encoder matched the reference output and independent inflation on 162 resource observations. It used 5,024 stack bytes against the 5,280-byte limit. All 12 injected failures reached their expected status and origin and recovered exactly. [Actor bindings](prepared-bindings.json), [recipe](candidate-recipe.json), [resource summary](qualification/resource-summary.json)

## Correctness

| Selection | Results |
| --- | ---: |
| Broad native library | 1,399 passed, 8 ignored |
| Three exact native ownership checks | 3 passed |
| Seven scalar/native integration binaries | 47 passed, 1 ignored |
| Native architecture equivalence | 1 passed |
| Release Program integration | 509 passed, 8 ignored |
| Explicit linked Program, iteration, scalar, cast and match | 5 passed |
| Explicit full encoder and serialized route census | 1 passed each |
| Independent Cargo feature boundaries | 6 passed |
| Workflow contract and inventory tests | 141 passed |
| Parser limits | 16 passed |
| Native code generation and both value system guards | 3 passed |

The workflow's x86_64 Linux registry contains 1,374 tests and selects 652 composition contracts. The Linux registry was captured at `72fdd7baafa47447b05e02a6b7c43f0a137e396e`, and the change to F updated two CI assertion files with the measured count. The cross-check passed at F. The M1 registry selected 681 composition contracts, all covered by the broad native library suite. Apple M3 and native x86_64 execution remain unavailable for this qualification. [Qualification audit](qualification/qualification-audit.json), [Linux inventory](qualification/linux-composition-inventory.json), [M1 inventory](qualification/m1-composition-inventory.json)

## Compiler assessment

The independent verifier reproduced the passing assessment from all 252 invocations. The two calibration families passed. Both elapsed-time comparisons passed the calibrated nonregression rule, and the RSS interval against O fell entirely below zero.

| Control | Elapsed change | Peak RSS change | Median paired peak RSS change |
| --- | ---: | ---: | ---: |
| R | −0.0376% | −0.1149% | −409,600 bytes (−400 KiB) |
| O | +0.0482% | −0.0607% | −188,416 bytes (−184 KiB) |

The complete assessment contains the simultaneous confidence intervals, absolute medians and original session ratios. [Compiler assessment](compiler/assessment.md), [independent compiler verification](compiler/verification.json)

## Runtime calibration

Both controls completed three same-build crossover sessions. The independently reproduced calibration found eight fixture coordinates with 95% intervals excluding zero across the two 190-coordinate families. This includes seven cases and one aggregate. All Silesia calibration intervals included zero. [Calibration seal](runtime/calibration.json), [independent runtime verification](runtime/verification.json)

| Control | Order | Coordinate | Estimated difference | Simultaneous 95% interval |
| --- | --- | --- | ---: | ---: |
| R | Forward | prefix-natural-65536 | +0.0517% | +0.0085% to +0.0948% |
| R | Reverse | prefix-random-4096 | +0.7772% | +0.4773% to +1.0780% |
| R | Reverse | repeated-32769 | +0.2702% | +0.0613% to +0.4795% |
| O | Forward | empty | −1.4392% | −2.3633% to −0.5063% |
| O | Forward | prefix-periodic-65535 | +0.1765% | +0.1238% to +0.2292% |
| O | Forward | prefix-random-1024 | +0.1171% | +0.0131% to +0.2212% |
| O | Forward | Suite geometric mean | −0.0399% | −0.0713% to −0.0084% |
| O | Reverse | prefix-random-1048576 | +0.0745% | +0.0014% to +0.1477% |

Reconstruction from the raw observations reproduced all eight estimates. Both cycles in each of the three sessions had the same sign at every excluded coordinate even as leg order alternated. O's forward empty calls averaged 30.51 ns. Of 294,912 timed calls at that coordinate, 28.24% recorded zero and 99.18% fell into the zero, 41 ns or 42 ns bins. The other excluded coordinates include calls much longer than a timer tick. [Raw calibration diagnostic](runtime/runtime-calibration-diagnostic.json), [timer witness and diagnostic summaries](runtime/runtime-calibration-findings.json)

Two short empty-case diagnostics tested whether the ordering of permutations or the fixture root explained the same-build effect. Balancing positions every four blocks shifted the diagnostic estimate from −0.844% to −0.694%. The shared-root diagnostic estimated +0.069% versus +0.626% for separate roots, with mixed signs across the paired sessions. Those trials left the qualification calibration unresolved. The empty fixture gives a concrete starting point for testing finer timer resolution at the existing call boundary. A targeted same-build diagnostic can then check the other affected coordinates before a new full qualification. [Permutation chronology diagnostic](runtime/diagnostic-permutation-chronology.json), [fixture root diagnostic](runtime/diagnostic-fixture-root.json)

The archive preserves the source bundle, bound F actors, the full compiler and control-only runtime campaigns, qualification logs and both bounded diagnostics. [Archive receipt](archive-receipt.json)
