# Reverse-complement results

Seven shuffled serial rounds, 250 million generated bases per fresh process.
Times include startup and complete stdin/stdout. Ratios use the new four-partition
**Mech Cranelift AOT median, 0.128275542 s, as 1.00×**. Lower is faster.

| Execution variant | Median (s) | SD (s) | × Mech AOT | Peak RSS (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Mech parent, 4 partitions | 0.14371 | 0.00445 | 1.120× | 248.2 |
| Mech parent, 8 partitions | 0.14394 | 0.00200 | 1.122× | 248.4 |
| Mech compacted input, 4 partitions | 0.12828 | 0.00056 | 1.000× | 244.4 |
| Mech compacted input, 8 partitions | 0.12981 | 0.00145 | 1.012× | 244.4 |
| Published Rust #1, 8 workers | 0.10974 | 0.00150 | 0.855× | 125.1 |

At four partitions the runtime change reduces elapsed time **10.7%**, a **1.12×
speedup**. The candidate is faster than its paired parent in all seven rounds.
Rust still uses 14.5% less time than the new Mech endpoint; equivalently Mech
uses 16.9% more time than Rust. This does not establish an optimal worker count
or globally fastest implementation.

The change removes the input compaction pass. Existing compiler last-use handling
already enables in-place reverse/translation when the byte buffer has unique
ownership. No additional full-buffer copy was identified in that path; the cause
of the remaining RSS difference is not isolated. The compute object is
byte-identical, so this result is attributed to runtime input handling.

All 35 complete timed outputs and five official bounded outputs pass. All 61
old/new bounded behaviors match; eleven broader reference-contract limitations
predate this change and remain disclosed in the [study](README.md).

The machine is an Apple M3 with AC power and low-power mode disabled. Default
power settings were retained. Swap usage was nonzero and stable at 2025.12 MiB
in the first and last snapshots. CPU frequency and temperature were not traced;
no disabled-throttling, zero-swap or pristine-idle claim is made. Samples were
serial and process snapshots detect no competing compiler. These conditions and
the short execution duration limit extrapolation to other machines or cohorts.

[analysis.json](analysis.json) retains exact ratios, paired effects, SD and RSS;
[run-v2/results.json](run-v2/results.json) retains every sample. The failed initial
launch was closed before any timing samples and is preserved separately. The
canonical dataset and website endpoints are unchanged by this study.
