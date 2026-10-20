# Source measurements v1

This additive packet measures the exact retained application and submitted
source text without running benchmarks or changing canonical LOC/timings.
See [the metric definitions, normalization audit and qualification plan](../../../docs/source-metrics.md).

- `metrics.json`: hash-bound catalog/tool, scope rules, availability, eight retained-counter probes and full per-program/per-file measurements.
- `metrics.csv`: flattened program measures for analysis, including explicit formatter status and separate submitted/application scopes.
- `cl100k_base.tiktoken`: pinned upstream BPE vocabulary for offline tokenization.
- `TIKTOKEN-LICENSE.txt`: upstream MIT notice.
- `requirements.txt`: optional tokenizer's exact package/dependency versions.

Run `tools/source_metrics.py --require-tokenizer --check` with those dependencies
and the saved zlib version to verify both generated reports. The report
explicitly leaves uniform logical LOC and language-lexer tokens unavailable;
the old source-count policies differ and the included probes demonstrate gaps.
