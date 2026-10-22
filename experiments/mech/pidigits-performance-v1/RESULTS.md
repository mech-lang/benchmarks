# Mech pi-digits results

Sharing the extraction numerator reduces the Mech AOT median from **0.3128 seconds
(1.08× optimized Mech)** to **0.2901 seconds (1.00×)**: 7.3% less elapsed time,
or a 1.08× observed speedup. Both Mech candidates beat their within-round parent
in all seven shuffled rounds. This is a source-level optimization using existing
language operations; the compiler's quotient-only same-sign division path was
already implemented.

| Implementation | Median seconds | × optimized Mech AOT | Sample SD seconds |
|---|---:|---:|---:|
| Mech parent | 0.3128 | 1.08× | 0.0007 |
| Mech shared numerator | 0.2915 | 1.01× | 0.0008 |
| Mech compact shared numerator | 0.2901 | 1.00× | 0.0012 |
| Unchanged published Rust #3 | 0.3097 | 1.07× | 0.0016 |
| Janet positive division | 0.3083 | 1.06× | 0.0006 |

All 35 fresh-process observations use 10,000 digits, the same installed GMP
binary, and complete identical output. No samples are dropped or pooled with
older cohorts. The denominator is this cohort's compact Mech AOT median,
0.29006225 seconds. Raw JSON additionally retains multiples of the old Mech
reference and of the fresh unchanged Mech baseline. These are results for the
exact tested implementations, not a universal language ranking or proof of
optimality. The small gap between the two optimized Mech forms is not a broad
claim that removing a helper call always improves performance.

## Reused work

The parent constructs `3*q+r` and `4*q+r` separately. The candidate first divides
`3*q+r`, then adds the unchanged `q` to the preserved numerator and performs the
second division. The same sharing is visible in the qualified Janet source.
All spigot control and state transitions remain Mech; there is no native pi
kernel, quotient inference, cached output or narrowed integer state.

A diagnostic-only GMP interposer observes real division inputs and results for
40 bounded application runs. They match independent Python arbitrary-integer
traces exactly. At full size, all five programs perform **44,908 actual quotient
divisions**. Each optimized Mech form performs **142,081 GMP unsigned-scalar
multiplications**, versus **164,535** in the parent: exactly **22,454 saved
multiplications**. Complete output checks pass in all 45 work diagnostics.
The diagnostic library is absent from every timed environment.

Janet performs two fewer scalar multiplications at full size because it skips
updating the generator after the final emitted digit. That terminal-state update
remains in both Mech forms and unchanged Rust. Both required extraction calls
are preserved in every program. This difference is retained explicitly rather
than presenting the application instruction streams as identical.

The first interposer attempt failed before its first arithmetic trace and reached
its owned deadline. The process was killed, reaped and its group closed. Its
partial captures and source snapshot remain in `work-v1` and `attempts-v1`;
`failure-review.json` distinguishes them from accepted `work-v2` evidence.

## Source measures and scope

| Mech source | Physical rows | UTF-8 bytes | Deterministic gzip bytes | BPE tokens |
|---|---:|---:|---:|---:|
| Parent | 38 | 2,050 | 726 | 715 |
| Shared numerator | 39 | 2,127 | 733 | 738 |
| Compact shared numerator | 37 | 2,045 | 713 | 713 |

Every application helper is counted. The compact form writes the first
extraction directly in the step; it does not hide it in another library.
Physical rows are not normalized logical or canonical formatted LOC. Those
measures remain unqualified for these new sources.

The current upstream compiler checkpoint is `6de19875e`; relevant control,
bigint and emission files match the earlier saved baseline. Build commands,
feature selections, initial build failures, generated source, native objects,
compiler output and executable hashes are retained. Rust #3 application bytes
remain exactly the published retained source; original notices and lineage are
preserved. Five loader captures confirm the installed GMP 6.3.0 image.

The timing boundary starts before fresh process launch and ends at independently
observed exit, including startup, Janet bytecode/FFI compilation, complete
computation, all output, flushing and shutdown. Power/process snapshots occur
between subjects. AC power and low-power mode off are checked; CPU frequency
and thermal state are not continuously logged or controlled, and a perfectly
idle host is not claimed. Builds and other benchmark subjects do not overlap.

The 85 uninstrumented bounded output checks, 35 full-size measurements, 45 work
diagnostics and all owned process receipts are replayed by `verify.py`.
The historical catalog and website timings are unchanged; these new results are
retained as an independently reviewable study pending catalog admission.
