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
