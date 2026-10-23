# Rejected native text-output buffering policies

This experiment tests a real duplicate copy in Mech's generic output path. The
native wrapping kernel writes roughly 256 KiB spans. A surrounding 1 MiB
`BufWriter` copies these spans into its own buffer before writing. The installed
Rust implementation and a pointer/call witness with real generated kernels
confirm that spans at least as large as the outer capacity can bypass that copy.

**All four tested policies are rejected.** They preserve exact output and native
work, but none improves median whole-process elapsed time. Production remains
runtime commit `fca1ba1f7462a555eb56833ad32135408a140a72`, with the original
256 KiB wrap budget and 1 MiB stream buffer. The selected benchmark dataset and
website are unchanged. [Results](RESULTS.md) retain both separate cohorts.

## Candidates and progression

The first cohort compares the original historical-runtime binary, current
compaction/reuse runtime, 2 MiB and 4 MiB native wrapping budgets with the existing
1 MiB stream buffer, and unchanged published Rust. Small input allocates only its
actual first-span output size in each candidate; large spans end at complete
line boundaries. Both larger policies regress despite proven copy avoidance.

The second cohort separates copy avoidance from larger write grouping. It tests
256 KiB wrapping with a 128 KiB stream buffer, and 1 MiB wrapping with a 512 KiB
stream buffer, against the same current Mech binary and unchanged Rust. Both
policies also regress. Their preselected build plan and rationale are retained
in `build-v2/results.json`; the first cohort was complete before preparing them.

No application or emitted native object changes, and no benchmark-specific
alphabet, line width or expected output is hardcoded in production changes.
The generic eligibility limits remain widths 1–256 and separator lengths up to
eight UTF-8 bytes. Original source counts, authorship, license gaps and sources
are unchanged. These are runtime I/O policy experiments, not compiler codegen
speedups, shorter applications or new source-size qualifications.

## Qualification and raw evidence

All four policies pass the same thirteen release runtime tests. Three new tests
use the real Cranelift wrapping emitter, not a simulated native implementation:

- 24 generated width/separator configurations, each checked at ten input lengths
  around empty, partial-line and output-span boundaries (240 checks per policy).
- Actual inner-writer pointer/call observations showing full large spans bypass
  the outer buffer, preserving the preceding header and trailing partial span.
- Short-write and interrupted-write retries, plus exact output-prefix/error
  propagation when the writer fails.

Both native comparison passes preserve every parent/candidate stdout, stderr and
exit status across all 61 retained cases: **366 complete bounded captures** total.
The same eleven pre-existing broader FASTA source limitations remain explicit;
these are not claimed as successful general FASTA reference checks. All nine
per-cohort official N=1000 output checks pass.
All **63 timed full outputs** match the complete reference. Full output is actually
written, hashed after owned-process closure, then omitted with size/hash receipts.
All 781 owned processes are closed and reaped, including tests, builds, telemetry
and expected malformed-input exits.

`build.py` and `build_balanced.py` retain serial build/test commands, environments,
exact runtime source snapshots/patches, source/object identity and binary hashes.
They use the frozen emitter CLI at `6de19875e` and the existing pinned Rust/Cargo
and GMP build environment. Generated applications link each captured runtime at
build time. Build projects/binaries remain ignored, while compact native objects
and descriptors are retained. The protected Rust application is untouched.

`qualify.py` / `qualify_balanced.py` capture bounded comparisons. `run.py` /
`run_balanced.py` conduct preselected seven-round shuffled serial cohorts under
the common timing mutex. Compilation, tests and benchmarks do not overlap.
Timing includes full fresh-process startup, input, work, all output, flush and
shutdown. The existing trusted legacy I/O path is unchanged; secured activation
is not newly timed. No phase profiler or diagnostic flag is enabled in timing.

`analysis.json` retains per-cohort denominators, all paired effects, SD, RSS,
child CPU usage and swap snapshots. `writer-contract.json` pins the inspected
installed Rust source; its upstream URL could not be fetched by the web tool and
is not represented as a newly verified upstream capture. The generated-kernel
pointer witness independently verifies the buffer-bypass behavior.

`working-state-not-measured.rs` preserves the final temporary development state;
it is explicitly not another measured variant. The isolated compiler checkout
was restored cleanly to the selected runtime, as recorded in
`restored-production.json`. No candidate was added to the compiler PR.
`verify.py` replays retained proof without launching subjects and checks omitted
full-output hash receipts rather than reconstructing deleted bytes. `seal.json`
binds every retained study artifact. All outliers remain; no samples are trimmed,
pooled across cohorts or used to replace the published timings.
