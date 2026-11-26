# Round 1 native compiler memory repair

B passed both M1 memory gates and the elapsed-time gate against R. **Elapsed time against O remains unresolved.** The compiler-only assessment reproduced independently from the sealed records. Round 2 requires the complete compiler gate to pass.

| Attempt | Source | Paired median RSS change vs R | Paired median RSS change vs O | Assessment |
| --- | --- | ---: | ---: | --- |
| A · skip zero-edge repair walks | `e6a999505a7d90733d621fc6e0fc9559ebf4f752` | -56 KiB | +208 KiB | O memory improvement unsupported and elapsed A/A calibration unresolved |
| B · reconstruct changed branch lists | `805ab41d6b2c2ae6ae62a09647cd31eb51be8661` | -368 KiB | -280 KiB | Memory passed and elapsed versus O unresolved |

Each attempt used all 252 predeclared compiler invocations. R and O ran from the pinned builds. B's paired RSS change was -376,832 bytes versus R and -286,720 bytes versus O. Against O the pooled RSS estimate was -0.0742%, with a simultaneous 95% interval from -0.0842% to -0.0642%.

B's elapsed estimate versus O was +0.0485%, with a simultaneous 95% interval of +0.0062% to +0.0909%. The calibrated limit was +0.0525%. Both B calibrations passed. All A results remain in the archive, including the positive memory interval against O and the elapsed calibration exclusions. [A assessment](e6a999505a7d90733d621fc6e0fc9559ebf4f752/A-m1-20261126T152205Z/compiler-summary.md) · [B assessment](805ab41d6b2c2ae6ae62a09647cd31eb51be8661/B-m1-20261126T160556Z/compiler-summary.md)

## Correctness

Apple M1 arm64 used the locked Rust nightly-2026-03-03 toolchain. The native kernels exercised their retained focused tests and the new handle-stability and shared-list regressions. The initial B test build exposed three missing fixture imports. The B commit in the table includes the correction, and the archive preserves the initial compile failure separately.

| Selection | A passed | B passed |
| --- | ---: | ---: |
| Loop-edge repair | 11 | 12 |
| Identity-route repair | 7 | 8 |
| Route sequence | 3 | 3 |
| Compilation inputs | 3 | 3 |
| Compilation report | 5 | 5 |
| Compile jobs | 4 | 4 |
| Compact object | 4 | 4 |
| Serialized route census | 1 | 1 |
| Explicit ignored encoder qualification | 1 | 1 |

The compilation report family left the single ignored encoder test for the explicit execution below it. The ordinary builds matched the encoder source, object, bytecode and parallel descriptor pins. The explicit test also covered workers 0, 1, 2 and 4, report on/off, selected-profile mutation, error and retry behavior. The exact command ledgers, probe outputs and sealed measurements are in the archive. [A encoder receipt](e6a999505a7d90733d621fc6e0fc9559ebf4f752/A-m1-20261126T152205Z/source-validation/encoder.json) · [B encoder receipt](805ab41d6b2c2ae6ae62a09647cd31eb51be8661/B-m1-20261126T160556Z/source-validation/encoder.json)

## Elapsed-time diagnosis

The ordinary telemetry localized the difference versus O primarily to native compilation. B averaged 2.227 ms longer in that phase across the 36 matched blocks, and the native-stage delta was positive in all six session means. Instrumented reports independently localized the difference to lowering and definition. The route requests, graph reuses and edge rewrites matched.

A separate diagnostic identified 31,914 inactive block visits. Skipping those visits and iterating the remaining instructions directly saved 2.052 ms in median whole-process time and 2.142 ms in the native phase using a single diagnostic binary. Peak RSS rose 152 KiB in median paired blocks within that probe. All probe outputs retained the pinned artifacts. The refinement remains a diagnostic result pending a separate qualification. [Phase diagnosis](diagnostics/elapsed/diagnosis.md) · [Repair-walk probes](diagnostics/stream-walk/diagnosis.md)

## Tooling and next gate

The committed scope tooling retains the existing estimator and v1 entry points. It separates compiler and runtime records, verifies the passing compiler prerequisite for runtime and checks crossover mappings and balanced cycles. Fourteen Python tests passed. An original v1 fixture and Silesia comparison also verified with the maintained reader. Runtime was outside the Round 1 schedule. The source handoff stops at the measured B commit.

The three frozen source input refs were fetched by their exact recorded SHAs. The observed heads for #995, #999 and #1000 matched the brief at inspection. Final integration, its source gates and the full runtime qualification remain pending the Round 1 elapsed gate. [Tool tests](diagnostics/focused-tools.txt) · [Archive and bundle checksums](archives.json)

The original M1 evidence release also contains the exact R and O builds used as controls. [Control archive](https://github.com/mech-lang/benchmarks/releases/tag/mech-native-route-m1-evidence-20261126)
