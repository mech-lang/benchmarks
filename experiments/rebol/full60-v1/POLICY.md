# Distinct-program Rebol timing cohort

The cohort measures the ten authored Rebol programs, with three fresh complete
processes per program and three matched Mech AOT controls per workload: thirty
Rebol observations and thirty controls, run serially under the common timing
mutex. All ten workloads use their existing full-size inputs and complete-output
contracts.

Each workload has one canonical Rebol program record. The earlier unused
ninety-process proposal assigned both `compact` and `optimized` labels to the
same main, helpers, runtime, extension image, command, environment and source
counts. These labels do not identify distinct implementations. The new cohort
publishes the single measured implementation; it may be selected for both the
fastest and fewest-lines endpoints. It creates no second program, copied sample
record or distinct optimization claim. The original proposal remains preserved.

For each workload, the three rounds alternate subject/control order:

1. Rebol, Mech control.
2. Mech control, Rebol.
3. Rebol, Mech control.

Every subject observation includes runtime startup, authored source and helper
evaluation, extension loading, input, all required computation, complete output
and shutdown. Compilation, harness file setup, input hashing, environment waits
and output validation remain outside the measured interval. The frozen sampler
and independent supervisor retain their existing measurement boundaries.

Independent pre-timing qualification must bind the corrected source bundles,
all 149 bounded output contracts, all eighteen primitive contracts, the extension
ABI and complete required-work evidence. A retained failed diagnostic remains a
failure; its successful predecessors may be used through their independently
verified records. The map observation qualifies complete bounded histogram
contents without claiming measured storage capacities or full-size allocation
traces. Runtime-source equivalence remains a declared limitation.

The full-run limits remain 21,600 seconds and 10,240 MiB RSS per process, with
the existing outer-supervisor deadline. An isolated full-size profile failure
retains its raw evidence and skips that profile's remaining slots; it does not
acquire a median or chart endpoint. Other qualified workloads may complete.
Integrity or process-ownership failures stop the cohort. There is no automatic
retry or rerun of previously published language cohorts.

The producer, independent reconciler, exporter and catalog admission must agree
on ten subject records, ten control records and sixty scheduled processes.
Planning or a zero producer exit does not itself grant timing or chart admission.
