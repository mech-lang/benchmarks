# Mech interpreted whole-process measurements

This experiment measures the fifteen retained interpreted source programs at the
ten canonical full workloads, with three fresh processes per program. It uses the
same interpreter executable and source bytes as the integration cohort. A fixed
shuffled schedule runs all 45 processes sequentially under the shared timing lock.

The stopwatch starts immediately before process launch and stops after process
exit. Startup, parsing, graph preparation, interpretation, input, complete output,
flush and shutdown are included. Output validation and prerequisite hashing occur
outside that interval. Internal preparation and execution diagnostics are retained
but never substitute for a whole-process sample.

The runner checks the complete output against the retained full-workload oracle,
records an explicit environment, monitors power and competing compilers, and pins
the runtime, sources and input files. There is no automatic retry or selection of
faster samples. An incomplete or failed cohort cannot replace published results.

`tools/rerun_mech_interpreted.py --output ABSOLUTE_FRESH_DIRECTORY` creates a plan,
report, terminal record, and one process receipt per attempt. Large stdout files
remain local; their complete byte counts and SHA-256 hashes are retained in the
receipts. Raw stderr diagnostics and all elapsed observations are preserved.

The publication importer selects fastest and fewest-LOC endpoints over all fifteen
fresh candidates. Earlier interpreted records remain attached as historical
measurements. Other language profiles, Mech AOT and JIT, workload definitions and
fixed chart baselines are preserved.
