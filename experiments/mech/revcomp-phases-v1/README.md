# Reverse-complement runtime phase diagnostics

Nine serial instrumented full-input executions use the already-built parent and
compacted-input binaries from the [matched study](../revcomp-streaming-v1/README.md).
No compiler, source or executable bytes change. `MECH_BYTE_PROFILE=1` enables the
existing three per-record clocks; all nine complete outputs match the reference.
These are diagnostics, not additional quantitative benchmark observations.

Four-partition compacted Mech has median summed record clocks of **0.05609 s**
reading, **0.00534 s** computing and **0.05159 s** writing. These are respectively
**0.437×, 0.042× and 0.402×** the accepted whole-process Mech AOT median of
**0.12828 s (1.000×)**. They are fractions of that reference, not independent
program speed ratios, and do not include every process phase. Per-phase medians
need not sum to a whole-process median. Eight partitions show a similar split.

The original input path's read clock is **0.07172 s (0.559× that same complete
Mech AOT reference)**. The write and compute clocks change little. This supports
the attribution of the previous gain to input compaction; it does not identify
every cause of the remaining gap to Rust.

Source inspection identifies a new body allocation per record. Reusing completed,
uniquely owned output storage for a later record is a separate hypothesis. This
packet does not establish its safety, effect or an allocation trace. No published
Rust source changes and no new website timings are admitted.

`run.py` retains binary/input/output pins, the shared mutex, explicit environment,
AC/low-power/process preflight, closed process receipts, three records per subject
and complete diagnostic stderr. Full stdout is written and hashed after process
closure, then omitted with size/hash receipts. `verify.py` replays retained proof
checks and produces `analysis.json`; it launches no benchmark.
