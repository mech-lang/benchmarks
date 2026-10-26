# Native architecture consolidation

This study adopts baseline I at `17539acd704e622c5f8ad90e001e20227535d53f`
and final cleanup F at `01b8b397011b6a774b7d9f730578a4ef92bf30f6`, before
any primary measurement. Fresh build receipts remain required. The earlier
I at `8aafe1e16b50b333d7990dd107e79124405bb71b` and intermediate F receipts
are retained as historical evidence.

`plan.json` predeclares both complete four-subject schedules, paired analysis,
seed and acceptance policy. `retained-controls.json` verifies the exact W/R
files and winning object, without rebuilding them. No primary observations
have been collected. Final F pins and correctness gates are still required.

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

Compiler PR #934 has since received CI repairs. Before primary measurements,
the final plan and build receipts must adopt its exact revised base and the
rebased cleanup head, while preserving the earlier I/F receipts. Generated
process gates and the two final timing sessions remain pending. There are zero
primary samples. Historical W timings are not measurements of I or F.

`analyze.py` reports **statistical acceptance only**. It always reports
`performance_qualified: false`; favorable numbers do not validate source pins,
correctness gates or process receipts. A performance claim also requires a
separate evidence qualification step. The synthetic analysis self-checks are
not campaign evidence.

`qualify.py` is that separate gate: it verifies frozen source and executable
pins, prerequisite receipts, the committed pre-sample plan/controllers, both
complete sessions and every raw owned-process duration, output and cleanup
receipt before combining evidence validation with statistical acceptance.
`measure.py` uses the same prerequisite gate before starting a primary sample.

`build-baseline.py` and `build-candidate.py` now require `--workspace` and
`--target-dir`, and optionally accept a fresh `--run-id`. Each invocation builds
the compiler and public AOT executable into new paths, preserving all committed
and previous build receipts. The printed receipt must be explicitly adopted
as `baseline_receipt` or `candidate_receipt` in `plan.json`; running the builder
does not change the adopted subject. These repair builds collect no timings.
