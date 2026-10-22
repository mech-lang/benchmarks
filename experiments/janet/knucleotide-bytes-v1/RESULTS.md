# Janet k-nucleotide runtime, memory and source tradeoffs

Six exact sources each have three full-size whole-process observations. Every
sample reads the same 254,166,745-byte FASTA fixture, selects 125,000,000 THREE
bases, and produces the complete 259-byte reference output with SHA-256
`f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7`.
All seven ordinary histograms remain, with 874,999,961 required window updates.

| Source | Median seconds | × retained Mech AOT | Maximum observed RSS, GiB |
| --- | ---: | ---: | ---: |
| Parent numeric arrays | 73.965 | 143.9× | 3.26 |
| Byte buffer, remainder | 69.548 | 135.4× | 1.52 |
| Line reader, remainder | 75.150 | 146.3× | 0.14 |
| Byte buffer, standard modulo | 60.092 | 116.9× | 1.52 |
| Line reader, standard modulo | 64.720 | 126.0× | 0.14 |
| Seven-worker modulo | 24.651 | 48.0× | 1.80 |

The denominator is the retained same-input Mech AOT median, **0.51382825 seconds
(1.0×)**, `knucleotide:mech-compact-final-std1-simd0-p4`. It is not a newly paired
Mech control. RSS is the maximum across the source's three observations, in
binary GiB; the low-memory line-reader/modulo form peaks at about 145 MiB.
Raw seconds, sample SD, CPU time and exact RSS bytes are retained per sample.

The byte-buffer candidate removes intermediate numeric arrays. The line reader
also removes the normalized whole-input/split-line object graph on the ordinary
LF input. It uses about 96% less peak RSS than the parent, but is slightly slower
until the separate modulo change. An arbitrarily long LF-delimited line, including
a large CR-only file, is not claimed to have a fixed line-buffer bound.

## Standard operator and threading changes

Replacing the hot `%` expression with standard `mod` is a one-operator source
delta. The pinned VM uses fmod for numeric remainder and floor/divide/multiply/
subtract for numeric modulo. Every key calculation here is a nonnegative integer
below 2^38, with a power-of-four divisor at most 2^36. The binary-scaled quotient,
its floor product and the remaining integer are exactly representable in
binary64. Thus this substitution preserves all 36 key bits in the actual domain;
it is not a claim about arbitrary signed or floating operands.

This change improves the byte-buffer median from 69.548s (135.4× Mech AOT) to
60.092s (116.9×), and the line reader from 75.150s (146.3×) to 64.720s (126.0×).
No cached input period, bounded-width truncation, query-only count or dense fixed
counter table replaces the ordinary seven maps.

The threaded candidate uses the unmodified standard `ev/thread` and
`ev/thread-chan` APIs. Seven application workers each build one complete map.
The ordinary supervisor message returns the table and task ID; the parent checks
unique expected widths and waits for all seven before producing summaries.
Worker errors propagate to the main task. This remains within eight application
threads, including the orchestrating parent. Standard Janet thread startup,
separate VM heaps, input serialization/copies, full map transfer, join and final
cleanup are inside the fresh-process interval. The runtime keeps the process
alive until the outstanding native thread callbacks complete.

The observed overall improvement is 3.00× versus the parent. Compared with the
serial line-reader/modulo form it spends more memory and aggregate CPU time to
reduce wall time. Source names reflect measured alternatives, not a globally
fastest or minimum-memory implementation proof. The normal
[Janet threading API](https://janet-lang.org/api/ev.html) is a general runtime
facility; there is no added native benchmark executor or application kernel.

## Native evidence and cohort limits

The first cohort has three shuffled rounds of parent, byte-buffer and line-reader
sources. The second has three rounds of the two one-operator modulo derivatives;
the third has three threaded observations. They are adjacent cohorts, not a new
single shuffled six-way experiment. Their prior-cohort hashes are linked, and
all runtime/source/controller identities remain pinned. Cross-cohort speedups
therefore retain the usual scheduling/thermal drift limitation.

All eighteen complete outputs match. The bounded runs independently validate
84 complete outputs and every key/count pair in 588 complete histograms, not just
the five printed queries. The two scalar opcode candidates also pass 72,360
native arithmetic-domain checks and a pure binary64-domain check. The threaded
variant passes an injected worker failure with normal nonzero exit, expected
diagnostic, no partial stdout and complete process closure. No diagnostic helper
is present in the measured application sources.

The owned wait4 controller records resource usage for the whole Janet process,
including its threads. Native tests cover normal exit, timeout/reaping/group
closure, an independent exit clock during slow telemetry, and a known 32 MiB
allocation to check macOS RSS units. Quantitative subjects explicitly set their
measurement flag; telemetry/diagnostics do not. Each measured process is reaped with a closed group before the next measured
subject. Monitoring children have their own bounded ownership and cleanup.

Power and process inventories are captured before/after samples and approximately
every ten seconds. All retain AC power and Low Power Mode off, with no detected
competing compiler. The host is Apple M3, 16 GiB RAM, macOS 26.2 build 25C56.
Ordinary brief desktop/metadata activity can occur, and temperature/frequency are
not continuously captured. These exploratory cohorts do not establish fixed
clocks, absence of throttling or an independently certified idle host.

The input was prepared once outside timing with the already validated FASTA
program, checked against the full reference hash and retained under ignored
`.build/inputs` for subsequent stdin workloads. Each subject opens a fresh input
handle. The full 259-byte outputs and all bounded streams are retained. Startup,
source parsing/bytecode compilation, input, all maps, output and process shutdown
are timed; input generation, build work, output hashing and group-closure checking
are outside the elapsed interval.

## Complementary source measurements

| Source | Physical rows | UTF-8 bytes | Gzip bytes | BPE tokens | Lexical tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parent | 54 | 2,067 | 908 | 626 | 490 |
| Byte buffer | 57 | 2,130 | 917 | 654 | 506 |
| Line reader | 55 | 2,146 | 949 | 647 | 490 |
| Byte/modulo | 57 | 2,132 | 918 | 655 | 506 |
| Line/modulo | 55 | 2,148 | 950 | 648 | 490 |
| Threaded/modulo | 66 | 2,623 | 1,140 | 787 | 602 |

Every authored parser, histogram, decoder, formatter and orchestration helper is
included. Whole-file text measures include comments and blank rows; native grammar
lexical tokens exclude whitespace/comments. The standard runtime/library bodies
remain dependencies. The low-memory form keeps the parent's lexical count; the
faster threaded form uses about 23% more lexical tokens. Logical normalized LOC
and canonical formatted LOC remain unqualified, rather than borrowing physical
rows or guessing counts. No Janet source or timing is admitted to the public
chart by this packet.

`verify.py` replays the bounded stdout and full histogram witnesses with the
independent Python oracle, checks all eighteen full outputs, samples/resource
receipts, input/source pins and preserved canonical catalog identity without
launching a benchmark. `measure.py --check` and `measure_threaded.py --check` use
the pinned source-metrics environment and saved native lexical captures. The
source manifests retain all parent citations and notices. Historical input,
qualification and timing directories are not overwritten; reproduction requires
new output-version directories and corresponding producer identities.
