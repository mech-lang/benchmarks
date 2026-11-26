# Native compiler route qualification

## Gate summary

The candidate resolves selected profiles on the compact compilation coordinator and shares each read result across both direct-literal attempts. It consolidates the adjacent route searches and reuses CFG and dominance after an enabled loop search rewrites zero edges.

The pinned Apple M1 encoder emitted identical object, bytecode and matching per-worker descriptors at I, C, S and O. The candidate eliminated 28 CFG constructions and 28 dominance constructions on the pinned encoder in every worker mode. At two workers, the serialized construction census changed from 1,539 to 1,511 CFG builds and from 1,430 to 1,402 dominance builds. Both runs performed 940 full verifications.

The C and O resource probes recorded 5,024 bytes of stack against the 5,280-byte ceiling. Each probe verified 162 successful output and alias observations, 12 failed calls and all 12 recoveries.

The M1 correctness, artifact and native stack gates passed. Across the six candidate sessions, the pooled result was 81/81 fixtures and 12/12 Silesia against each pinned reference in both orders.

**The M1 merge qualification failed.** Against R, peak compiler RSS increased 0.0822% with a simultaneous 95% interval of +0.0736% to +0.0908%, above the calibrated +0.0229% resolution. The candidate used a median 304 KiB more in paired compiler blocks. Compiler-process elapsed time remained unresolved against both controls. Both runtime nonregression gates remained unresolved because the same-build runtime calibrations excluded zero at nine comparison coordinates in total.

The prescribed local implementation, campaign and independent verification are complete. Native M3 and x86_64 execution remain open. The completed M1 campaign is the evidence for these decisions.

## Source stack and tooling

| Checkpoint | Source pin |
| --- | --- |
| Updated #993 | `bb554dcc30c15725d3f23ba54873fb5bee0576bf` |
| #994 base | `1696944e6ef97882675b6301fd8d32f3bde689aa` |
| Historical Frozen | `35784003b9149fe8059fa83dd5d0aff10dbcd631` |
| Historical Reconciled | `5b9f252fc7e775bf8e4d850ca368da581e9f5386` |
| Recorded reconciled #993 | `a9a72bd067708a879c890b338d1d8b6d02ac641e` |
| Recorded reconciled #995 | `39da704d07a9177bdfa18cfe93e94ab2c434338d` |
| Recorded reconciled #999 | `fba109a136684cf41f6c1d5011881cec9e830f5d` |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` |
| Local #995 | `9349006bfd9aff8abd4315216421a07c5008e131` |
| Local #999 | `b831580d2455175882d5a42dcafaf12d3692a618` |
| I | `55427555fa2f574a350e69095500de292cb6ab46` |
| C0 | `b3b0b3214c962c1380b990b6520e07154a09cf7e` |
| C1 | `95dd29af8a29d5762c19a1b73beca9095a012d81` |
| C | `fbbd3100658a44ae19481df43f9158c89329cf72` |
| S | `92182965629f792ddc8f915955bef86ac92e24ae` |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` |
| Review tip and CI inventory correction | `146626d6f9bad465efaa2993f49da4a674b993a9` |
| Benchmark baseline | `f9eb6c48905ff02e2a5771d1812f6bb42598a57f` |
| Benchmark tooling | `ca927855d46f3c0c63dacacae3f7d7c39a7e1970` |
| Initial benchmark evidence | `5e13b79110efd74a9fa16ff8a4b20b1e151dea92` |

Reconciliation applied the pinned four-file #993 delta and retained the descendant parser fixture and vendored fingerprint. The effective R-to-I tree delta is the workflow and its inventory assertion. The M1 inventories selected 666, 675 and 676 tests in stack order. The pinned compiler at O selected 679 tests in the M1 libtest listing and 650 in the compiler-generated x86_64 Linux registry. All 29 differences appeared only in the M1 listing. The separate review-tip commit updates the Ubuntu inventory gate and its Python assertion. Its compiler tree is identical to O. The x86_64 Linux cross-check passed. Native x86 execution remains open.

At I, all 16 parser-limit tests and 141 workflow and inventory tests passed. Both value-system contracts passed.

During qualification, Mech PR #1000 moved to `8e68da6afa7983a307c8389f0682283fbc90789a` and benchmarks PR #12 moved first to `d0e9f0fc97d798124f7466de105776e51f21f09b` and then `f4fd369995cd4becaa7a16af62793d5728be9ac5`. A subsequent fetch observed Mech PR #995 at `2fe7b7c906b50464e6df271bc2047afb0a1580f1`. The campaign binds the source and tooling commits in its manifest.

A host restart interrupted validation. The source and benchmark commits were restored with their original Git object hashes in persistent storage. The Silesia corpus was downloaded again and verified against its manifest. The reviewed control was rebuilt at R.

## Responsibilities

| Owner | Responsibility |
| --- | --- |
| Raw compilation configuration | Captures lossless environment settings and preserves typed AArch64 and independent per-setting parsing. |
| Compact coordinator | Resolves a reached profile at its existing consumer and retains the bytes or captured error across the attempt boundary. |
| Host compilation report | Records the raw and resolved input digests and attempt-scoped route work. Separately owned worker counters record actual machine entries. |
| Route sequence | Owns loop and identity scheduling, the one-use graph reuse and the required verification boundaries. |
| Proof kernels and native backend | Derive current use inventories and apply the existing proofs and final machine optimization. |
| Benchmark packet | Pins rebuilds and measurements, retains observations and verifies the predeclared calibration and assessment. |

Raw setting families remain owned by the compiler entry, AArch64 backend projection, compact pass controls, phase layout and spill settings, and machine worker and reporting inputs. The source design documents record the individual settings. The closed-library contract remains proposed and compact execution remains diagnostic. The next boundary is bounded IR-unit construction with explicit stage and proof ownership.

## Correctness and resource evidence

Validation uses Rust `nightly-2026-03-03`, locked dependencies, and Apple M1 arm64 macOS 15.6.1 (24G90), unless the evidence identifies a different target. The explicitly selected encoder test ran independently of the ordinary unit suite.

| Selection | Result |
| --- | --- |
| C0 staged guard fixture and guard on the staged brief | 1 unit test passed and the guard exited successfully |
| C1 input, phase-layout and report tests | 10 passed, 1 ignored |
| C1 pinned full encoder at the corrected commit | 1 explicitly ignored test passed |
| C isolation, worker-report, body/cleanup and error-order tests | 6 passed |
| C pinned full encoder | 1 explicitly ignored test passed |
| S focused tests | 193 passed, 1 ignored |
| S pinned full encoder | 1 explicitly ignored test passed |
| S serialized full encoder with construction census | 1 explicitly ignored test passed |
| O pinned full encoder | 1 explicitly ignored test passed |
| O serialized full encoder with construction census | 1 explicitly ignored test passed |
| O affected workflow and parser checks | 141 workflow tests and 16 parser tests passed. Both value contracts and the native-codegen guard exited successfully. |
| O broad native library | 1,391 passed, 8 ignored, 35 filtered out |
| O exact body-sharing, owned cleanup and ordered ticket-error tests | 1 passed for each of the three selections |
| O ordinary native integration targets | 47 passed across seven binaries, 1 ignored in the iteration binary |
| O native architecture equivalence | 1 passed |
| O release `canonical_artifact_program` | 509 passed, 8 ignored |
| O six separate Cargo feature checks | 6 checks exited successfully |
| O exact route construction census | 1 passed |
| O linked program, iteration, scalar, cast and match | 1 explicitly selected ignored test passed for each gate |
| Benchmark decision and runner tests | 7 passed |

| O integration binary | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| `canonical_artifact_native` | 9 | 0 | 0 |
| `canonical_artifact_i64` | 4 | 0 | 0 |
| `canonical_artifact_f64` | 5 | 0 | 0 |
| `canonical_artifact_cast` | 4 | 0 | 0 |
| `canonical_artifact_bits` | 3 | 0 | 0 |
| `canonical_artifact_match` | 10 | 0 | 0 |
| `canonical_artifact_iteration` | 12 | 0 | 1 |

The first debug encoder run exposed a redundant block switch at the first terminal append candidate. C1 repaired the Mech builder call. Later encoder tests exercised worker counts 0, 1, 2 and 4 with report on and off, selected-file overwrite and deletion, a stale register profile, and a real two-attempt error from one cached read. A new compilation reread the recreated profile. The NUMERIC worker report recorded a positive native worker entry count under its selected invocation.

| Pinned encoder artifact | SHA-256 |
| --- | --- |
| Encoder source | `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299` |
| Object | `e4325602c6a5a4507ba637eee5d34ada9bda77bbb334fefb8ff53324d720e214` |
| Bytecode | `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3` |
| Descriptor, zero workers | `3c88e31701d637597d456d4717b210bd9b19cc5b92b9846eb3bd5ab3414f6ea3` |
| Descriptor, 1, 2 or 4 workers | `c2448f4197863733301810dca0e8d721d1932afa32b5172e933843b07e2464ef` |

| Workers | Loop and identity searches | Loop and identity edges rewritten | Explicit CFG builds, S to O | Explicit dominance builds, S to O | Graph-pair reuses, S to O | Full verifications, each |
| ---: | --- | --- | --- | --- | --- | ---: |
| 0 | 37 and 39 | 14 and 265 | 76 to 48 | 76 to 48 | 0 to 28 | 974 |
| 1, 2 or 4 | 35 and 37 | 10 and 261 | 72 to 44 | 72 to 44 | 0 to 28 | 940 |

The encoder report records 66,268 function-symbol bytes including inline literals, 80,040 constant-data-definition bytes and a 157,264-byte object file. Each column uses the same scope at S and O. The census counts include graph constructions across the compiler and are recorded separately from the explicit route-search builds.

The eager profile capture and duplicate route scheduling were removed. Selected profile, scalar execution, route proof, ordered error, linked application and independent-inflation witnesses stay in their maintained test owners. The benchmark script entry points retain the legacy mode, and the fixed campaign uses their manifest-driven mode.

The campaign manifest pins the machine, corpus, tooling and the three builds. The prepared bindings identify the complete executables and runtime support. [Campaign manifest](records/campaign.json) · [Prepared bindings](records/prepared-bindings.json)

The matched route-work records retain counts and hashes for all four worker modes. The Linux inventory records cross-build evidence. [Route-work comparison](records/route-work-comparison.json) · [Linux composition inventory](records/x86-composition-inventory.json)

The fixture and Silesia suites are regression controls for this same-output change. The final two Silesia cases informed earlier development. The historical tiny-case observations of 7.58% and 6.25% retain their original status under the earlier protocol. The new calibration applies to this campaign.

## Fixed M1 performance campaign

The independently verified performance decision is **fail**. The campaign manifest SHA-256 is `cded594f55bd62e9e119a4a7ac413e14addc424170cbff94d49453180552d2c6`. The sealed records contain six calibration sessions and six comparison sessions. Percent changes are relative to the corresponding control. Positive values indicate more elapsed time or memory.

| Control | A/A runtime | A/A compiler | O runtime | O compiler |
| --- | --- | --- | --- | --- |
| C | unresolved | pass | unresolved | unresolved |
| R | unresolved | pass | unresolved | fail |

### Runtime suite geometric means

| Comparison | Suite and order | Change | Simultaneous 95% interval | Calibrated resolution |
| --- | --- | --- | --- | --- |
| O/C | fixtures/forward | -0.043% | -0.133% to +0.047% | +0.264% |
| O/C | fixtures/reverse | -0.101% | -0.382% to +0.180% | +0.388% |
| O/C | silesia/forward | +0.020% | -0.052% to +0.091% | +0.112% |
| O/C | silesia/reverse | +0.003% | -0.044% to +0.049% | +0.108% |
| O/R | fixtures/forward | -0.015% | -0.167% to +0.137% | +0.285% |
| O/R | fixtures/reverse | -0.068% | -0.167% to +0.031% | +0.288% |
| O/R | silesia/forward | -0.007% | -0.074% to +0.060% | +0.162% |
| O/R | silesia/reverse | -0.007% | -0.064% to +0.050% | +0.167% |

### Source-through-object compiler process

| Comparison | Metric | Change | Simultaneous 95% interval | Calibrated resolution |
| --- | --- | --- | --- | --- |
| O/C | elapsed ns | +0.610% | -0.591% to +1.827% | +0.233% |
| O/C | maximum resident bytes | -0.015% | -0.032% to +0.002% | +0.023% |
| O/R | elapsed ns | +0.580% | -0.696% to +1.872% | +0.266% |
| O/R | maximum resident bytes | +0.082% | +0.074% to +0.091% | +0.023% |

| Comparison | Session | Elapsed change | Peak RSS change |
| --- | --- | --- | --- |
| O/C | 1 | +0.020% | +0.003% |
| O/C | 2 | -0.104% | -0.025% |
| O/C | 3 | -0.019% | -0.028% |
| O/C | 4 | +3.690% | +0.017% |
| O/C | 5 | +0.056% | -0.037% |
| O/C | 6 | +0.075% | -0.019% |
| O/R | 1 | +0.133% | +0.085% |
| O/R | 2 | -0.171% | +0.081% |
| O/R | 3 | -0.081% | +0.099% |
| O/R | 4 | +3.812% | +0.083% |
| O/R | 5 | -0.056% | +0.068% |
| O/R | 6 | -0.096% | +0.076% |

### Reference wins

| Comparison | Suite and order | Reference | Control wins | Candidate wins | Gate |
| --- | --- | --- | --- | --- | --- |
| O/C | fixtures/forward | libdeflate | 81/81 | 81/81 | pass |
| O/C | fixtures/forward | pinned reference | 81/81 | 81/81 | pass |
| O/C | fixtures/reverse | libdeflate | 81/81 | 81/81 | pass |
| O/C | fixtures/reverse | pinned reference | 81/81 | 81/81 | pass |
| O/C | silesia/forward | libdeflate | 12/12 | 12/12 | pass |
| O/C | silesia/forward | pinned reference | 12/12 | 12/12 | pass |
| O/C | silesia/reverse | libdeflate | 12/12 | 12/12 | pass |
| O/C | silesia/reverse | pinned reference | 12/12 | 12/12 | pass |
| O/R | fixtures/forward | libdeflate | 81/81 | 81/81 | pass |
| O/R | fixtures/forward | pinned reference | 81/81 | 81/81 | pass |
| O/R | fixtures/reverse | libdeflate | 81/81 | 81/81 | pass |
| O/R | fixtures/reverse | pinned reference | 81/81 | 81/81 | pass |
| O/R | silesia/forward | libdeflate | 12/12 | 12/12 | pass |
| O/R | silesia/forward | pinned reference | 12/12 | 12/12 | pass |
| O/R | silesia/reverse | libdeflate | 12/12 | 12/12 | pass |
| O/R | silesia/reverse | pinned reference | 12/12 | 12/12 | pass |

### Shortest fixture durations

Each number is the median of the six per-session file medians, in nanoseconds. The raw assessment retains every case, all 190 runtime intervals per comparison, the individual session wins and the sums of standalone Silesia file medians.

| Comparison | Order | Case | Control ns | Candidate ns |
| --- | --- | --- | --- | --- |
| O/C | forward | empty | 41.0 | 41.0 |
| O/C | forward | one-stored | 41.0 | 41.0 |
| O/C | forward | seven-stored-prefix | 42.0 | 42.0 |
| O/C | forward | eight-literals | 7,834.0 | 7,854.5 |
| O/C | forward | eight-literals-prefix | 7,875.0 | 7,875.0 |
| O/C | reverse | empty | 41.0 | 41.0 |
| O/C | reverse | one-stored | 41.5 | 42.0 |
| O/C | reverse | seven-stored-prefix | 42.0 | 42.0 |
| O/C | reverse | eight-literals | 7,875.0 | 7,875.0 |
| O/C | reverse | eight-literals-prefix | 7,875.0 | 7,875.0 |
| O/R | forward | empty | 41.0 | 41.0 |
| O/R | forward | one-stored | 41.5 | 41.0 |
| O/R | forward | seven-stored-prefix | 42.0 | 42.0 |
| O/R | forward | eight-literals-prefix | 7,854.5 | 7,854.5 |
| O/R | forward | eight-literals | 7,854.5 | 7,864.8 |
| O/R | reverse | empty | 41.0 | 41.0 |
| O/R | reverse | one-stored | 42.0 | 42.0 |
| O/R | reverse | seven-stored-prefix | 42.0 | 42.0 |
| O/R | reverse | eight-literals | 7,875.0 | 7,875.0 |
| O/R | reverse | eight-literals-prefix | 7,875.0 | 7,875.0 |

M3 and native x86 execution were unavailable for this campaign. The x86_64 Linux build and test inventory are recorded in the correctness evidence.

### Calibration exclusions

These simultaneous 95% same-build intervals excluded zero. The remaining coordinates and the full calibrated resolutions are in the sealed record. [Calibration](records/calibration.json)

| Control | Coordinate | A/A change | Simultaneous 95% interval |
| --- | --- | --- | --- |
| C | `fixtures/forward/prefix-random-4096` | -1.411% | -2.320% to -0.494% |
| C | `fixtures/forward/prefix-random-65535` | -0.309% | -0.596% to -0.022% |
| C | `fixtures/forward/random-64` | -0.497% | -0.946% to -0.046% |
| C | `fixtures/reverse/prefix-periodic-262144` | -0.158% | -0.291% to -0.025% |
| R | `fixtures/reverse/33027-periodic-window` | -0.495% | -0.894% to -0.094% |
| R | `fixtures/reverse/prefix-random-65536` | -0.321% | -0.626% to -0.015% |
| R | `fixtures/reverse/prefix-random-65537` | -0.233% | -0.376% to -0.089% |
| R | `fixtures/reverse/prefix-repeated-65537` | -0.247% | -0.445% to -0.049% |
| R | `fixtures/reverse/suite-geomean` | -0.174% | -0.269% to -0.080% |

The ordinary compiler estimate uses paired log ratios across balanced cycles. In the first confirmation session, the elapsed estimates were +3.690% versus C and +3.812% versus R. That session stays in the pooled estimates. Both pooled elapsed intervals span zero. Peak RSS nonregression passed against C. It failed against R, where all six session point estimates were positive.

### Session inventory

The first session started on November 25 at 17:50:07 UTC. Timing finished on November 26 at 10:37:23 UTC, and independent verification finished at 10:47:24 UTC. Each row retains its start marker, sealed raw-file inventory and full observations. [Qualification seal](records/qualification.json) · [Confirmation seal](records/confirmation.json) · [Independent verification](records/verification.json) · [Supervisor timeline](records/campaign-timeline.txt)

| Stage | Session | Start UTC | End UTC | Raw files |
| --- | --- | --- | --- | ---: |
| calibrate | closeout-1 | Nov 25 17:50:07 | Nov 25 18:38:00 | 733 |
| calibrate | closeout-2 | Nov 25 18:38:15 | Nov 25 19:26:05 | 733 |
| calibrate | closeout-3 | Nov 25 19:26:20 | Nov 25 20:14:11 | 733 |
| calibrate | reviewed-1 | Nov 25 20:14:25 | Nov 25 21:02:16 | 733 |
| calibrate | reviewed-2 | Nov 25 21:02:31 | Nov 25 21:50:21 | 733 |
| calibrate | reviewed-3 | Nov 25 21:50:36 | Nov 25 22:38:51 | 733 |
| qualify | session-1 | Nov 25 22:42:17 | Nov 26 00:40:48 | 1,344 |
| qualify | session-2 | Nov 26 00:41:18 | Nov 26 02:39:49 | 1,344 |
| qualify | session-3 | Nov 26 02:40:19 | Nov 26 04:38:49 | 1,344 |
| confirm | session-1 | Nov 26 04:40:58 | Nov 26 06:39:27 | 1,344 |
| confirm | session-2 | Nov 26 06:39:57 | Nov 26 08:38:25 | 1,344 |
| confirm | session-3 | Nov 26 08:38:54 | Nov 26 10:37:23 | 1,344 |

The candidate met all reference targets in each session. C recorded four standalone 11/12 Silesia results against libdeflate on `x-ray` in qualification 1 reverse, confirmation 2 forward, and confirmation 3 in both orders. All contributed to the pooled C result of 12/12 in each order. [Per-case durations, intervals, resolutions and session scores](records/assessment.json)

### Rebuild and evidence

Use the recorded source and benchmark tooling commits with the pinned recipes, profile hashes, corpus and ordinary rebuild command. The M1 campaign manifest binds the original absolute paths for read-only verification. A separate host uses its own manifest and calibrations. [Pinned rebuild and verifier instructions](README.md) · [Archive locations, contents and hashes](records/archives.json)
