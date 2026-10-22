# Janet FASTA measurements and source tradeoffs

All four programs generate the full N=25,000,000 workload. Each process writes
254,166,745 bytes with SHA-256
`3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa`, matching the
retained full-size reference in `tools/qualification/lean_run.py`. Twelve fresh
whole-process samples pass complete-output verification: three per source.

| Source | Median seconds | Sample SD seconds | × retained Mech AOT |
| --- | ---: | ---: | ---: |
| Parent | 38.648 | 0.175 | 71.4× |
| Batched linear search | 23.047 | 0.051 | 42.6× |
| Batched binary search | 32.531 | 0.432 | 60.1× |
| Compact sequence form | 51.455 | 0.793 | 95.1× |

The retained, equivalent-input Mech AOT denominator is **0.541193292 seconds
(1.0×)**, catalog program `fasta:mech-fasta-final-expanded-v2`. It is not a fresh
paired Mech control. The parent/linear/binary sources share three shuffled rounds
in `run-v1`; the compact source has three subsequent observations in
`compact-run-v1`, with the previous cohort hash pinned. Comparisons to the compact
source therefore span adjacent cohorts. All exact raw samples and medians remain
in the original reports.

Batched linear search improves the parent median by 1.68×. Ordinary binary search
is slower than the changed linear form here; it is not promoted merely because
its asymptotic search bound is smaller. These two forms also copy the fixed ALU
record in wrapped blocks, batch random output and inline the unchanged LCG. This
cohort measures that combined source change; it does not isolate the independent
effect of each edit.

The compact form uses ordinary Janet `loop`, `seq`, `find-index`, `apply` and
`string/from-bytes`. Its random draw closure retains every LCG update and a strict
floating-probability search; fixed ALU rows come from slices of a doubled fixed
input string. It is 1.33× slower than the parent, but smaller across every saved
text measure. There is no custom native workload executor.

| Source measure | Parent | Linear | Binary | Compact |
| --- | ---: | ---: | ---: | ---: |
| Physical rows, comments and blanks included | 55 | 70 | 76 | 44 |
| UTF-8 bytes | 2,019 | 2,702 | 2,858 | 1,755 |
| Deterministic gzip bytes | 894 | 1,156 | 1,198 | 854 |
| Pinned BPE tokens | 744 | 931 | 971 | 662 |
| Native grammar lexical tokens | 416 | 546 | 581 | 357 |

The compact source uses 14% fewer lexical tokens than the parent; the faster
linear form uses 31% more. These are observed tradeoffs, not proofs of minimum
source size or a fastest possible program. Logical normalized LOC and canonical
formatted LOC remain unavailable. Raw rows do not replace them. The pinned native
grammar recognizes each exact source, and all authored helpers remain counted.
The measured runtime and general library implementations remain dependencies.

## Algorithm and process evidence

`qualification-v1` contains 48 complete bounded outputs, 48 source-projected draw
witnesses and 279,951 source-extracted linear/binary search checks.
`compact-qualification-v1` adds 16 complete outputs and 16 actual-source draw
witnesses. Every diagnostic performs 8*N ordinary LCG updates and reaches the
independently iterated final seed while retaining the expected full stdout.
Both original alphabets, every possible normalized random state, equality and
duplicate thresholds are tested for the search alternatives. Test-time exhaustive
classification is not used as a production state-to-letter table.

The full samples run sequentially under the common mutex. AC power and Low Power
Mode off are checked before/after subjects and approximately every ten seconds.
Observed process inventories show no detected competing compiler. A Git process
appears in a snapshot immediately following the second linear sample; its exact
overlap cannot be reconstructed from that snapshot. Quiet-host confirmation
therefore remains pending for that cohort. Ordinary brief desktop activity and
thermal/frequency drift are not excluded by the sampling monitor. CPU and OS
receipts identify Apple M3, macOS 26.2 build 25C56.

All process groups close and direct children are reaped before the next subject.
The reused quantitative controller times from immediately before fork through
observed exit, with an independent 1ms polling observer. Parsing, bytecode
compilation/loading, VM startup, all input/work/output and shutdown are included;
output hashing and group cleanup follow the recorded interval. Scheduling can
add exit-observation latency. Power/process telemetry is outside the exit
observer, and no compilation or another benchmark runs concurrently.

Each full stdout is hashed in full after process closure, then the owned validated
payload is removed. `stdout-omitted.json` retains the exact byte count, hash and
removal policy. This avoids retaining over 3 GB for twelve generated payloads.
Complete bounded outputs, diagnostics, identities and cleanup receipts remain.
The live complete-output check is established by the pinned producer and
observation receipts; the removed full stdout cannot be rehashed from the archive.

## Status and reproduction

These are experimental candidates and are not admitted to the public chart.
Quiet-host confirmation, normalized source ownership rules, remaining Janet
full-size workloads and final admission review remain outstanding. Existing
sources, catalog entries and timings are unchanged.

The source manifest, exact parent attribution and licenses are retained in
`sources.json` and `compact-source.json`. The pinned runtime release/build and
shared corpus are linked through `../bounded-v1/plan-v1.json`. `full.py` and
`compact_full.py` preserve timed argv/environment, all source/runtime/controller
pins and the fixed workload. Native launch requires the shared mutex to be free.
Historical output directories are not overwritten; a replay must use a new
output version and retain its new controller identity.

`measure.py --check` uses the isolated pinned source-metrics environment and
checks saved native grammar captures without rerunning subjects. `verify.py`
checks exact sources, complete-output identities, process closure, all twelve
samples, source measures, the source preparation seal and preserved catalog SHA.
