# Janet reverse-complement results

Three local candidates were tested against the unchanged historical parent on
FASTA N=25,000,000: 254,166,745 input bytes, three records and 250,000,000 sequence
bases. Every full-size output matched the independent Python reference's complete
254,166,745-byte output (SHA-256
`e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e`).

| Implementation | Median seconds | × Mech AOT | Maximum peak RSS across three samples |
|---|---:|---:|---:|
| Historical whole-input parent | 13.380 | 89.6× | 1.42 GiB |
| Line reader, original table/row writes | 18.248 | 122.2× | 129 MiB |
| Dense complement table and output chunks | 12.712 | 85.2× | 129 MiB |
| Whole-row loop with the same chunks | 12.737 | 85.3× | 133 MiB |

Mech AOT is the retained same-input median of **0.149272625 seconds (1.0×)**,
profile `revcomp:mech-revcomp-optimized`. It was not remeasured alongside Janet.
The first three implementations have three shuffled sequential rounds in
`run-v2`; the row-loop candidate has three sequential follow-up samples in
`block-run-v1`, not a shared four-way shuffle. Raw observations, sample standard
deviations, CPU usage and process/power snapshots remain in those reports.

The dense/chunk form has a 1.05× observed speed improvement over the parent and
about **91% lower maximum peak RSS**. Its line-by-line growing input meets the
workload rule that the historical whole-input parent does not. The row-loop
variant does not demonstrate a useful runtime improvement; its difference from
the dense form is smaller than the observed sample variation. It uses slightly
fewer source tokens, so it remains a separate measured alternative.

This is primarily a memory/compliance improvement. It does not establish a
fastest possible Janet implementation. Parallel record/chunk work, avoiding
normalization/splitting on ordinary LF input, and other standard-library forms
remain potential experiments. Whole-record reversal still requires record-sized
storage, and a CR-only input may arrive as a single LF-delimited input line.

## Source size

All authored application code, comments and helpers are included. Unmodified
runtime code is excluded. Physical rows, BPE and grammar lexical tokens describe
different properties; none is relabeled as normalized logical LOC.

| Implementation | Physical rows | UTF-8 bytes | Deterministic gzip bytes | BPE tokens | Janet lexical tokens |
|---|---:|---:|---:|---:|---:|
| Parent | 30 | 1,214 | 580 | 376 | 248 |
| Line reader | 29 | 1,186 | 569 | 364 | 242 |
| Dense/chunk | 44 | 1,683 | 714 | 487 | 331 |
| Row loop | 43 | 1,626 | 711 | 466 | 314 |

The line-reader-only version is slightly smaller and substantially slower on this
input. The chunked forms trade more application code for lower memory and modest
runtime gains. Canonical formatted and normalized logical LOC remain unqualified;
the source qualification of other Janet programs is not silently extended here.
`source-measures.json` pins the exact files, native grammar, BPE implementation,
Python and gzip versions. `measure.py --check` reproduces these measures without
rerunning a benchmark.

## Correctness and controls

The final bounded captures contain 272 complete application output/rejection
checks across four exact sources, including 40 explicit malformed-input cases.
Another 232 instrumented executions verify complete stdout and each record's
visited base count. Added cases cross output chunk flush boundaries and invalid
positions after complete chunks or before a later record. The rejection checker
also rejects 280 deliberate capture corruptions. This establishes these cases,
not an arbitrary-input proof. All twelve full-size subject processes pass.

Every native execution is owned before exec, holds the common mutex, closes its
process group and reaps its child. No benchmark runs overlap. Full-process elapsed
time includes parsing, bytecode compilation, VM startup, input, complete
computation/output and shutdown. Resource usage comes from macOS `wait4`.
Full-output hash validation happens after exit; only then are the large subject
payloads omitted with size/hash/closure receipts. Small bounded captures remain
complete. The independent reference and shared input are retained as ignored
build artifacts, with their hashes committed.

AC power and Low Power Mode off are observed throughout. Ordinary host activity
is recorded; continuous thermal/frequency instrumentation and a pristine idle
host are not established. This study did not disable CPU throttling. The sandbox-denied
process snapshot in `run-v1` preceded all quantitative subject executions and
was retried using authorized read-only host access. Nothing was changed in power
settings or the runtime. These exploratory results do not enter the chart.

`verify.py` replays complete bounded bytes/rejections, record witnesses, native
ownership, source/input/controller pins, full-output receipts, raw/summary values,
power observations and the unchanged canonical catalog. `seal.json` hashes this
study's retained artifacts. The parent lineage, consulted original sources and
licenses are retained in `source-manifest.json`.
