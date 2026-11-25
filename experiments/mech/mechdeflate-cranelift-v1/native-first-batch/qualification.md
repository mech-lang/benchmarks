# First-batch qualification

The M1 checks use the published winning artifacts and the same full-corpus
benchmark protocols for all three compiler snapshots.

| Gate | Status | Evidence |
| --- | --- | --- |
| Stack integration and language semantics | Passed | #993 through #1000 reconciled. 11 source tests and 99 CI contract checks passed. The Wasm test passed duplicate rejection, state preservation and recovery. [Merge map](stack.tsv) · [Reconciled evidence](evidence/reconciled/) |
| Compiler configuration compatibility | Passed | The inventory covers 329 native compile, runtime-build and test inputs and the driver preload switch. Exact modes, OS strings, numeric defaults and conditional errors retain their previous interpretation. [Inputs](evidence/configured/native-compiler-inputs.md) |
| Configuration isolation | Passed | Alternating and concurrent AArch64 compiles use different alignments with their own expected objects. The malformed alignment only rejects on its applicable legacy route. Four profile/feature compilation checks and eight explicitly enabled backend tests passed. [Native test evidence](evidence/configured/native-test-summary.json) |
| Selected profiles | Passed | The full encoder emitted identical artifacts after the harness changed or deleted five copied profile files after capture. It used the pinned artifact data throughout. [Profile check](evidence/configured/configured-profile-and-worker-checks.json) |
| Workers and ordered errors | Passed | Counts 0, 1, 2 and 4 reproduced the same native object and canonical bytecode. Each count also reproduced its Frozen descriptor. The serial path retains the existing extra diagnostic details for a dense-scorer phase that is discarded before final output. Ordered cleanup and publication tests passed. [Worker checks](evidence/configured/configured-profile-and-worker-checks.json) |
| Host reporting | Passed | Reporting off and on reproduced the same artifacts. The driver captured real stage timings and macOS peak RSS. A separate instrumented run captured construction counts while retaining the artifacts. [Host report](evidence/configured/host-report.json) · [Construction census](evidence/configured/construction-census-report.json) |
| Artifact preservation | Passed | Fresh Frozen, Reconciled and Configured builds matched the winning native object, canonical bytecode and descriptor byte for byte. The recipes and rebuild receipts identify compiler and linked support for each actor. [Snapshot evidence](evidence/) |
| Native execution and resource bound | Passed | 1,378 native passes and seven existing ignored tests. The independently reproduced register-allocation dump double count was corrected in the test and retested. Both rebuilt endpoint actors passed 162 output and alias checks and 12 injected failures with exact recovery. Both measured 5,024 bytes of native stack against 5,280 bytes. [Native suite](evidence/configured/native-test-summary.json) · [Frozen probe](evidence/frozen/native-resource-recheck.json) · [Configured probe](evidence/configured/native-resource-checks.json) |
| Library specification | Delivered | The guarantee matrix records existing evidence, proposed guarantees and implementation gaps for the closed library boundary. [Contract](evidence/configured/native-closed-library.md) |
| x86_64 execution | Not run | The scalar and Program profiles passed cross-target compilation for x86_64 Linux. Runtime execution and qualification were performed on Apple arm64. |
| M3 Configured qualification | Unresolved | This work ran on M1. The separately published M3 Frozen retest had 80 of 81 fixture wins against libdeflate in each order and 11 and 12 Silesia wins. [M3 baseline](evidence/frozen/m3-reference/README.md) |

## M1 paired timing

Each cell lists the candidate time change in forward and reverse order.
The aggregate is the geometric mean of the individual paired case ratios.

| Candidate versus control | 81 fixtures | 12 Silesia files |
| --- | --- | --- |
| Reconciled versus Frozen | +0.0515%, −0.1041% | −0.0030%, +0.0423% |
| Configured versus Reconciled | +0.1257%, +0.1073% | −0.0752%, −0.0400% |
| Configured versus Frozen | −0.0808%, −0.0522% | −0.0109%, −0.0961% |

All six 81-case orders produced 81/81 wins for each timed Mech actor
against both reference encoders. The three pair manifests were independently
verified against 5,895,936 timing observations altogether. All direct
Silesia pairs had exact matching compressed streams and independent inflation
for every input.
[Comparison summary](evidence/comparison-summary.json)

The Configured encoder also won 12/12 against each reference in each
standalone Silesia order. Its aggregate time was 15.61% and 15.62% lower
than libdeflate. X-ray was the closest libdeflate comparison at 0.26%
and 0.27% less time. [Standalone Silesia scores](evidence/configured/silesia-reference-scores.json)

## Ordinary compiler process

The ordinary driver ran once per actor in each of the six actor
permutations after warmup. The external elapsed time includes subprocess
startup, compilation and emitted files. Peak RSS measures the full compiler
subprocess lifetime.

| Snapshot | Median elapsed | Median peak RSS |
| --- | --- | --- |
| Frozen | 2.175 s | 375.42 MiB |
| Reconciled | 2.171 s | 374.70 MiB |
| Configured | 2.174 s | 374.50 MiB |

The configured object has 66,268 bytes in emitted function symbols and
80,040 bytes in constant data definitions. The full object is 157,264 bytes.
The construction census is separately recorded.
[Primary compiler samples](evidence/compiler-process-summary.json) · [Object report](evidence/configured/host-report.json)

The [handoff instructions](README.md) identify the pinned worktrees, recipe
selection, independent paired comparisons and raw evidence locations.
