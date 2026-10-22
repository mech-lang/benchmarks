# Completed-buffer reuse results

Seven shuffled serial rounds, 250 million generated bases per fresh process.
Times include startup and complete stdin/stdout. The denominator is the new
four-partition **Mech Cranelift AOT median, 0.122859292 s = 1.00×**.

| Execution variant | Median (s) | SD (s) | × Mech AOT | Peak RSS (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Original Mech, 4 partitions | 0.14332 | 0.00133 | 1.167× | 248.4 |
| Compacted Mech, 4 partitions | 0.12934 | 0.00122 | 1.053× | 244.4 |
| Reused Mech, 4 partitions | 0.12286 | 0.00152 | 1.000× | 125.1 |
| Reused Mech, 8 partitions | 0.12330 | 0.00114 | 1.004× | 125.1 |
| Published Rust #1, 8 workers | 0.11070 | 0.00115 | 0.901× | 125.1 |

Buffer reuse reduces elapsed time **5.0%** relative to compaction alone. Combined
compaction and reuse reduce time **14.3%** relative to the original, a **1.17×
speedup**. Both improvements hold in every paired round. Peak RSS is **49.6%
lower** than the original, essentially reaching Rust's observed peak in this
cohort. Four/eight-partition differences do not prove an optimal worker policy.

Rust still uses 9.9% less elapsed time than new Mech; equivalently Mech uses
11.0% more time than Rust. The remaining gap is not attributed to a proven cause.
These are exact fresh controls; no older absolute timings are pooled.

All 35 complete timed outputs and five official bounded outputs pass. All 61
old/new bounded behaviors match; eleven existing broader FASTA source limitations
remain disclosed in the [study](README.md). Ten runtime tests pass, including
2,736 parser cases with recycled storage. A test-only refinement rebuild is
byte-identical to the measured executable.

The machine is the same Apple M3, on AC power with low-power mode disabled and
default power settings. Swap remains nonzero: 1,889.12 MiB before the cohort and
1,865.12 MiB afterward. Unlike the earlier compaction cohort, it is not stable.
Frequency and temperature are not traced; no disabled-throttling or pristine-idle
claim is made. Short runtimes, background system behavior and this single machine
limit generalization. Compiler processes were excluded by process preflight,
and benchmark subjects ran serially under the shared lock.

Exact samples, SD, ratios, paired effects, input/output hashes, environments and
process closure receipts are retained in [run-v1/results.json](run-v1/results.json)
and [analysis.json](analysis.json). These results remain experimental; the
canonical catalog and website endpoints are unchanged by this packet.
