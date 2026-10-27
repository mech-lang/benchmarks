# Native architecture consolidation

The shared controller now serves this study and
`post-native-architecture-cleanup-v1` through a fixed `--study` choice. The
architecture study remains the default. Plans, build receipts, qualification
manifests and primary-session directories are separate; the measurement,
evidence checks and statistics have one implementation in this directory.
Controller hashes refer to these source files regardless of the selected study.

Both plans are frozen before their first primary observation. The three published
compiler heads and their exact public AOT files are fixed. Collection can precede
remaining compiler verification; final performance qualification still requires
every correctness, process and artifact gate. `sampling-readiness.json` pins
completed public-build/oracle/wide proofs, and the future final attestation must
bind the unchanged sampling plan to the completed qualification manifest. Both plans must also
adopt the same explicit `runtime_environment_receipt` before changed-input checks
or primary sampling; the
controller no longer silently substitutes the selected I build's environment.
Both plans now adopt `runtime-environment-v1.json` by its exact hash, sharing one
task-owned temporary directory and runtime environment across all four subjects.
The field can identify an
existing build receipt or a separately recorded environment receipt containing
an `environment` map. A shared reference has exactly
`{"study_id": "native-architecture-consolidation-v1", "path": "relative/receipt.json", "sha256": "actual SHA-256"}`.
Only the two named study directories are accepted. Adopt a real, verified
receipt in both plans before freezing; do not copy placeholder pins.

The current prospective sources are baseline I at
`a093aea452340a70c1e72a1f58bd831f1edef70f` (#934) and architecture F at
`7543c56d5efc4df30d0b60961922024d74caa9d7` (#935). The test-only base repair
passes all 422 tests across the nine original canonical source CI suites. The
architecture preserves the complete prepared patch and published history.
Fresh public builds at all three published heads have passed independent
validation and their receipts are adopted. All six ordinary guest artifacts
are byte-identical. Exact-head correctness/process/artifact qualification
continues; no runtime acceptance result is available yet.

The earlier `ddf8cbc`/`a3e805a` public builds and fourteen changed-input
executions remain historical evidence at their original pins, alongside the
older `b05a3f8` prospective subject. No result is relabelled for a later source.
Zero primary observations have been collected.

At the published heads, `changed-inputs-published-7543c56-v1/` and the cleanup's
`changed-inputs-published-a68fb2e-v1/` each pass seven direct-oracle cases and
fourteen exact F/I executions. Their independent validators check every raw
command, output, update count, source/executable pin and terminal process receipt.
`supplemental-wide-slot-published-v1/` passes all six source/decoded builds at
I=a093, A=7543 and C=a68; both studies' mandatory wide-artifact gates accept it.
The archived descriptors and disassembly establish the selected 68-bit key and
24-byte emitted slot addressing. These are correctness/artifact results, not
primary observations. `published-public-builds-v1/build-metrics.json` separately
records executable sizes and observed build costs with their concurrency limits.

`artifact_equivalence.py snapshots` runs the preserved, exact-one-test snapshot
harness for an explicitly adopted `--subject I` or `--subject F`. At the baseline,
which predates the harness, it installs only a hash-pinned temporary test overlay,
accounts for that source status, and removes it after the process group closes.
Later heads use the identical tracked harness. It requires
matching source/cache provenance and records all 32 named source/decoded files.
`compare` requires pinned snapshot receipts for both actual before/after heads;
the cleanup reuses architecture F as its I. The older ddf8 snapshot archive is
an additional byte-level reference, not a substitute for the actual before head.
The receipt validator rechecks the exact workspace/test command, process owner,
archived execution inputs, clean source, overlay cleanup and one-test stdout.
Both receipt archives must be committed before final performance qualification.

Before primary sampling, `wide_slot.py` also requires the six public wide-slot
builds (three source heads, each source/decoded). It checks the four-bit domain,
68-bit key, 24-byte slot, all six guest artifacts, actual source/compiler pins,
owned AOT/disassembly receipts and committed archive bytes. Neither the six
ordinary public artifacts nor the 32 representatives replace this separate gate.
All three subjects must agree with both studies' adopted public receipts. The
selected width comes from the range operands in the actual descriptor; the
selected packed loop must emit 24-byte addressing with high-key/value loads.

`baseline-prerequisites-ddf8-v1/` records the repaired baseline's five prerequisite
suites: 415 native tests (two existing ignored diagnostics), 82 facts, 30 line,
36 worker-credit and one catalog test. Its one snapshot test produced 32 artifacts
byte-identical to the preserved baseline. The temporary snapshot overlay was
removed and the final source state is clean. These are correctness receipts;
the current public build and timing gates remain separate.

Historical baseline I at `17539acd704e622c5f8ad90e001e20227535d53f`
and F at `01b8b397011b6a774b7d9f730578a4ef92bf30f6` retain their actual
public AOT builds and raw comparison evidence below. The earlier
I at `8aafe1e16b50b333d7990dd107e79124405bb71b` and intermediate F receipts
are retained as historical evidence.

`plan.json` predeclares both complete four-subject schedules, paired analysis,
seed and acceptance policy. `retained-controls.json` verifies the exact W/R
files and winning object, without rebuilding them. No primary observations
have been collected. Prospective source heads are adopted; fresh executable
receipt adoption remains pending. Final
correctness/process/artifact coverage and both timing sessions remain required.

`baseline/public-aot.json` records the actual public CLI build of I, its clean
source, compiler/environment/executable pins, and owned process receipt. Its
bytecode and guest object match the retained winning pins. This is not timing
qualification. `baseline/native-tests.json` records 415 actual native passes
and two pre-existing ignores at I. The setup-work diagnostic was already
archived by #929; it is not restored as production instrumentation.

Four representative source/decoded fixtures retain complete flat descriptor
images, bytecode, metadata and guest disassembly. The initial preparation
refactor produces byte-identical objects and metadata for these fixtures;
this is targeted equivalence evidence, not an exhaustive final code audit.

The intermediate candidate at `d4672186304325df2fdd2f50e37225bf34fd0adb`
has the same six canonical object, bytecode, descriptor, identity and resource
files as I; its guest object also matches W. `candidate/code-inspection.json`
records the actual disassembly, including the paired loads in both long hashed
loops. Assembly agreement alone is not a runtime performance qualification.

`changed-inputs-v1/results.json` retains seven independent direct string-window
oracles and fourteen successful pinned F/I AOT executions. The native test-name
coverage companion accounts for every one of the 417 baseline test functions,
including names printed on lines with inline diagnostics in the original log.
The cleanup's broad native run executes 426 passes and two existing ignores.

`qualification-history/` retains the broad correctness run and its diagnostics,
including unsuccessful attempts. The Python environment retry uses the existing
CI YAML parser environment; the process-supervision retry has the process-table
access those existing checks require. Source-contract corrections and their
verification are retained separately. These historical receipts do not claim
that final process qualification or CI has completed.

The historical completed builds are `baseline-builds/final-17539-v1/public-aot.json`
and `candidate-builds/final-01b8-v1/public-aot.json`. Their six guest Object,
bytecode, descriptor, identity and resource artifacts are byte-identical,
including the retained W guest object. `exact-head-equivalence-v1/` archives
both sets of raw files and all 32 representative source/decoded artifacts;
each representative artifact also matches exactly.

`changed-inputs-final-01b8-17539-v1/results.json` records the seven independent
oracles and fourteen successful executions of those historical pinned F/I files.
Historical comparisons above remain preserved. Required final correctness and
generated-process receipts are still being completed, including the original
failed policy compile deadline and its serial retry. Zero primary samples have
been collected; historical W timings do not qualify I or F.

The separate `../post-native-architecture-cleanup-v1/` study records the deletion
audit following this architecture. Its before subject must be the final repaired
#935 candidate, explicitly adopted after repairs and rebasing. The earlier
`01b8` receipt above is preserved as historical evidence. Evidence from one pair
of compiler revisions does not qualify a later cleanup.

`analyze.py` reports **statistical acceptance only**. It always reports
`performance_qualified: false`; favorable numbers do not validate source pins,
correctness gates or process receipts. A performance claim also requires a
separate evidence qualification step. The synthetic analysis self-checks are
not campaign evidence.

`qualify.py` is that separate gate: it verifies frozen source and executable
pins, prerequisite receipts, the committed pre-sample plan/controllers, both
complete sessions and every raw owned-process duration, output and cleanup
receipt before combining evidence validation with statistical acceptance.
`measure.py` checks the frozen collection prerequisites before starting a primary
sample. `qualify.py` always requires the full verification gate; collecting or
statistically analyzing timings cannot qualify performance. The prospective
ordering correction is recorded in `sampling-order-adoption-v1/receipt.json`.

`build-baseline.py` and `build-candidate.py` now require `--workspace` and
`--target-dir`, and optionally accept a fresh `--run-id`. Each invocation builds
the compiler and public AOT executable into new paths, preserving all committed
and previous build receipts. The printed receipt must be explicitly adopted
as `baseline_receipt` or `candidate_receipt` in `plan.json`; running the builder
does not change the adopted subject. These repair builds collect no timings.

Every entrypoint accepts `--study native-architecture-consolidation-v1` or
`--study post-native-architecture-cleanup-v1` before its existing arguments.
For example, after final pins and gates are adopted:

```sh
python3 experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1/measure.py \
  --study post-native-architecture-cleanup-v1
```

An unrecognized or repeated study choice fails. A baseline may reference the
other study's immutable public AOT receipt using the structured reference above;
the candidate must use a local receipt. Referenced before-build and environment
receipts are hash-checked and included in the committed pre-sampling evidence.
All primary observations and their raw process files remain confined to the
selected study. Finish and review shared-controller changes before freezing
either plan; changing controller files after sampling changes their pins.

`qualification-history/superseded-pre-launcher-repair-v1/` preserves all raw
logs and terminal evidence from the superseded b05/569 and earlier stack attempts,
including the controlled interruptions and sandbox cleanup limitation. These
attempts do not satisfy the final qualification gates.

`secondary-prefix-preparation-v1/` retains the independent oracle, reviewed
controller source hash and 54 counter validation checks. It contains zero new
benchmark observations.

## Final build metrics and secondary prefix diagnostic

`public-build-metrics-final-v1.json` records actual pinned executable sizes and
separate compiler/public AOT build durations, with exact raw receipt references.
The values retain their original cache and concurrent-build conditions. Retained
W/R historical build scopes are listed separately in that record.

| Subject | Executable bytes | Compiler build (s) | Public AOT build (s) |
| --- | ---: | ---: | ---: |
| F (`a3e805a`) | 5,550,864 | 602.947 | 199.701 |
| I (`ddf8cbc`) | 5,517,760 | 712.255 | 187.877 |

`secondary-prefix-protocol.json` prospectively pins the original million-base
THREE input, independently verified exact output, native counters, final F/I/W/R
executables and unchanged primary policy. The shared `secondary-prefix.py`
entrypoint validates all four completed primary sessions before it can execute
its single 16-observation block. It records all observations and per-subject
medians, without warmups, exclusions, replacement samples or a performance
acceptance claim. The entrypoint has not been run; prefix time remains pending.

After both primary campaigns validate, use:

```sh
python3 experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1/secondary-prefix.py \
  --study native-architecture-consolidation-v1
```
