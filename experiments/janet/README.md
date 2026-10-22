# Janet benchmarks

Janet 1.42.1 is being qualified across the ten suite workloads using its standard
standalone register-based bytecode VM. Fresh-process timing includes source
parsing, bytecode compilation, VM startup, complete input/computation/output and
shutdown. Bundling this VM in an executable is not native AOT compilation of the
application.

The [active source overlays](source-overlays-v1.json) identify seven v2 programs
and the v3 regex-redux, spectral-norm and reverse-complement programs. These are
locally authored implementations or adaptations, with original consulted sources,
contributors and licenses in the preserved [source manifest](source-manifest-v1.json).
Local authoring identifies Codex GPT-6 family; the exact serving model is unknown.
Every authored helper and GMP FFI declaration remains application source.

## Current validation and timing

All 149 bounded corpus contracts pass for the active source set: 142 complete
success-output contracts and seven explicit invalid-IUPAC rejection contracts.
The [original native capture](native-v1/README.md) retains the initial overlapping
regex-count defect and its correction. The
[reverse-complement review](native-v1/rejection-review.md) records valid cases,
invalid-byte/position diagnostics, partial stdout and rejection-adapter tests.
These checks do not establish full-size correctness for every workload.

The [spectral-norm candidate](native-v1/spectral-review.md) reuses three vectors
and advances exact coefficient denominators. Seven bounded output cases and 14
source-projected native work checks pass. Six sequential
[full-size process observations](spectral-full-v1/README.md) at N=5500 validate
complete output. Parent median: 66.827 seconds (776.4× retained Mech AOT).
Candidate median: 16.531 seconds (192.1×), an observed 4.04× improvement. The
retained, same-input Mech AOT median is 0.086075292 seconds (1.0×); it was not
remeasured in this cohort. Substantial macOS background activity is recorded.
These exploratory observations require quiet-host confirmation and do not enter
the public chart.

The [FASTA study](fasta-search-v1/RESULTS.md) adds three measured alternatives.
Batched linear search has a 23.047s median (42.6× retained Mech AOT), versus the
parent's 38.648s (71.4×): a 1.68× improvement. Ordinary binary search is slower
here. A compact sequence form uses 357 lexical tokens versus the parent's 416,
but takes 51.455s (95.1×). All twelve full-size samples match complete output;
all ordinary LCG updates and probability searches remain in Janet. These are
experimental candidates with explicit cohort and source-count limitations.

The [k-nucleotide study](knucleotide-bytes-v1/RESULTS.md) measures five alternatives
against the parent with all seven complete maps retained. Standard byte input,
positive modulo and seven ordinary Janet workers give a 24.651s median
(48.0× retained Mech AOT), versus 73.965s (143.9×): a 3.00× observed improvement.
A serial line-reader/modulo form takes 64.720s (126.0×) with about 145 MiB peak RSS,
about 96% below the parent's peak. All eighteen full outputs and 588 bounded full
histograms pass. Normalized source counts and admission remain pending.

The [reverse-complement study](revcomp-stream-v1/RESULTS.md) adds three native-counted
alternatives. Dense complement lookup and chunked output measure 12.712s
(85.2× retained Mech AOT), versus the historical parent's 13.380s (89.6×), with
about 91% lower peak RSS. The candidates meet line-by-line input requirements;
the historical whole-input parent does not. All twelve full-size outputs and
272 bounded output/rejection checks pass. A whole-row loop shows no useful
additional speed gain. Normalized LOC and chart admission are still pending.

The [n-body study](nbody-access-v1/RESULTS.md) measures three alternatives. Standard
Janet macros retain state in VM scalar registers and preserve all pair arithmetic,
reducing the median from 105.393s (101.4× retained Mech AOT) to 23.864s (23.0×),
a 4.42× improvement. All twelve full outputs match exactly, and canonical plus
perturbed-state captures preserve complete state bits. This costs 902 lexical
tokens versus the parent's 705; no normalized LOC benefit is claimed.
Five Janet workloads remain without full-size studies.

The [array-access candidates](array-access-v1/README.md) add three unmeasured
alternatives for binary-trees and fannkuch. Thirty-five complete bounded outputs
and 35 complete-work witnesses pass, including distinct tree allocations and
every permutation/flip through N=8. Across all packets, native lexical measures
now cover 30 unique Janet application sources. These checks are not full-size
performance or normalized-LOC admission.

The [telemetry-boundary clarification](measurement-boundary-review-v1.json)
records that periodic power/process snapshots occur inside live subject windows.
Their host contention is included in observed wall time; post-exit callbacks do
not extend the independent exit timestamp. It disambiguates earlier shorthand
without changing any elapsed values or prior sealed captures.

The [measurement metadata reconciliation](measurement-metadata-reconciliation-v1.json)
corrects an inherited receipt label on eighteen earlier spectral/FASTA experimental
observations. Their recorded elapsed values and full-process boundaries are
unchanged. New quantitative subject receipts explicitly set the measurement flag.

[Complementary source measures](source-overlay-measures-v1.json) retain exact
physical rows, UTF-8 bytes, code points, deterministic gzip and pinned BPE tokens
for all three overlays and their parents. They include comments, whitespace and
every application helper. The [native source qualification](source-qualification-v1/README.md) adds
qualified grammar-level lexical token counts for all thirteen sources, with
hand-counted layout probes. Both formatting experiments pass reader round-trips,
compilation and all 149 contracts, but neither row measure supplies normalized
statement LOC. Native normalized and canonical formatted counts remain pending;
raw rows, formatter rows, lexical tokens and BPE remain separate measures.
Run the [source measurement tool](source_overlay_measures.py) in the pinned
source-metrics environment to reproduce or check the packet.

## Runtime and library boundaries

The [release acquisition](runtime-acquisition-v1.json) pins the official archive,
exact revision and MIT license. The original downloaded executable stalled before
returning a version; its [owned observation](runtime-probe-v1/hang-observation.json)
retains the failed launch and termination attempt. No security setting was changed.
The retained [local build](local-runtime-build-result-v1.json) instead compiles the
verified release's bundled C sources with Apple Clang. Restoring those inputs
reproduced the exact same runtime SHA-256 and version `1.42.1-e1963cd`.
The downloaded executable was not relaunched.

The [first syntax attempt](syntax-v1/reconciliation.json) printed diagnostics
while returning zero. The corrected [second attempt](syntax-v2/results.json)
requires zero exit and empty stdout/stderr. Historical compile-only evidence and
the [149-case preparation](bounded-v1/README.md) remain unchanged. The preparation's
old blocked status describes that earlier stage; native results are separate.

Regex-redux uses the unmodified published
[Spork regex module](dependencies-v1/spork/snapshot.json), which compiles supported
regular expressions to Janet PEGs. The application explicitly advances beyond
each eight-byte motif for non-overlapping counts. Pi digits uses ordinary FFI to
call general GMP arithmetic leaves; the full spigot, both digit extractions,
control and output remain in Janet.

Required-work review across the remaining workloads, complete library-loader
closure, qualified source counts, remaining full-size outputs and timing cohorts,
and chart admission remain pending. All native cases and quantitative subjects
run sequentially under the common mutex. Existing language results and sources
are preserved; no Janet profile is yet admitted.
