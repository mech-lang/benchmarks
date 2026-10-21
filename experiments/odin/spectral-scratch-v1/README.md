# Odin spectral-norm scratch reuse

This uncompiled candidate moves the temporary length-N vector from the
`AᵀA` helper into `main`, reusing it across the twenty helper calls. It also
explicitly frees all three vectors before process exit. The forty matrix-vector
passes, coefficient expression, inner reduction order, ten power iterations,
final dot products and nine-decimal output remain the same in the source.

The comparison preserves the exact
[local predecessor](../../../archive/comparisons/zig-odin-roc-elm-comparison/20261010/sources/spectralnorm-odin-1-faithful.odin).
Its original implementation is cited at
[Programming Language Benchmarks](https://github.com/hanabi1224/Programming-Language-Benchmarks/blob/ad18b203dd1769724f4eea94fc3ac1e99f6593e0/bench/algorithm/spectral-norm/1.odin).
The upstream MIT notice is retained as [LICENSE.upstream](LICENSE.upstream).
Local changes carry the repository's Apache-2.0 terms. Original authorship and
the unknown historical serving model remain as recorded in the source lineage;
current changes identify Codex GPT-6, with the exact serving model unknown.

The hypothesis is less allocator traffic. No native compilation, generated-code
inspection, output/work qualification, count qualification or performance result
is claimed. Allocation removal could have little effect beside the quadratic
arithmetic. The full shared spectral-norm cases and complete full-size output
must pass before a serial, preselected fresh-process comparison is admitted.

The complete authored file remains application source. Native normalized and
formatted counts are pending; raw rows, bytes, gzip and pinned BPE measures are
retained separately. Existing source counts, timings and chart selections are
unchanged.
