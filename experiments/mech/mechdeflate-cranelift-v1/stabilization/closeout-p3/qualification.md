# Native compiler route qualification

## Gate summary

The candidate resolves selected profiles on the compact compilation coordinator and shares each read result across both direct-literal attempts. It consolidates the adjacent route searches and reuses CFG and dominance after an enabled loop search rewrites zero edges.

The pinned Apple M1 encoder emitted identical object, bytecode and matching per-worker descriptors at I, C, S and O. The candidate eliminated 28 CFG constructions and 28 dominance constructions on the pinned encoder in every worker mode. At two workers, the serialized construction census changed from 1,539 to 1,511 CFG builds and from 1,430 to 1,402 dominance builds. Both runs performed 940 full verifications.

The C and O resource probes recorded 5,024 bytes of stack against the 5,280-byte ceiling. Each probe verified 162 successful output and alias observations, 12 failed calls and all 12 recoveries.

The broad native library and release Program suites are in progress. The fixed M1 campaign is queued behind those gates. Compiler elapsed time, RSS and reference win counts require the completed campaign.

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
| O ordinary native integration targets | 47 passed across seven binaries, 1 ignored in the iteration binary |
| O native architecture equivalence | 1 passed |
| O six separate Cargo feature checks | 6 passed |
| O exact route construction census | 1 passed |
| O linked program, iteration, scalar, cast and match | 1 explicitly selected ignored test passed for each gate |
| Benchmark decision and runner tests | 7 passed |

The first debug encoder run exposed a redundant block switch at the first terminal append candidate. C1 repaired the Mech builder call. Later encoder tests exercised worker counts 0, 1, 2 and 4 with report on and off, selected-file overwrite and deletion, a stale register profile, and a real two-attempt error from one cached read. A new compilation reread the recreated profile. The NUMERIC worker report recorded a positive native worker entry count under its selected invocation.

| Pinned encoder artifact | SHA-256 |
| --- | --- |
| Encoder source | `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299` |
| Object | `e4325602c6a5a4507ba637eee5d34ada9bda77bbb334fefb8ff53324d720e214` |
| Bytecode | `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3` |
| Descriptor, zero workers | `3c88e31701d637597d456d4717b210bd9b19cc5b92b9846eb3bd5ab3414f6ea3` |
| Descriptor, 1, 2 or 4 workers | `c2448f4197863733301810dca0e8d721d1932afa32b5172e933843b07e2464ef` |

| Workers | Loop and identity searches | Loop and identity edges rewritten | Explicit CFG builds, S to O | Explicit dominance builds, S to O | Full verifications, each |
| ---: | --- | --- | --- | --- | ---: |
| 0 | 37 and 39 | 14 and 265 | 76 to 48 | 76 to 48 | 974 |
| 1, 2 or 4 | 35 and 37 | 10 and 261 | 72 to 44 | 72 to 44 | 940 |

The encoder report records 66,268 function-symbol bytes including inline literals, 80,040 constant-data-definition bytes and a 157,264-byte object file. Each column uses the same scope at S and O. The census counts include graph constructions across the compiler and are recorded separately from the explicit route-search builds.

The eager profile capture and duplicate route scheduling were removed. Selected profile, scalar execution, route proof, ordered error, linked application and independent-inflation witnesses stay in their maintained test owners. The benchmark script entry points retain the legacy mode, and the fixed campaign uses their manifest-driven mode.

The [campaign manifest](records/campaign.json) pins the machine, corpus, tooling and the three builds. [Complete executable and runtime bindings](records/prepared-bindings.json)

The [matched route-work records](records/route-work-comparison.json) retain counts and hashes for all four worker modes. [Linux composition inventory](records/x86-composition-inventory.json)
