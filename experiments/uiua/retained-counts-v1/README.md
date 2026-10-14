# Retained Uiua tree and n-body source counts

The two n-body v3 implementations each contain **21 canonical source units**:
19 independent bindings and two output statements. The binary-trees source
contains **15 units**: 11 independent bindings, one record declaration and three
output statements. Its compact and fast labels have identical source bytes and
share the retained timing observations.

These are exact-source owner counts under the existing array-language rule:
each independent binding, data declaration or output statement counts once.
The checker enumerates every owner and accepts only the three reviewed source
hashes. It does not infer counts for other Uiua programs or treat an unknown
program's physical line count as a canonical count.

| Source | Bindings | Records | Outputs | Canonical units |
| --- | ---: | ---: | ---: | ---: |
| N-body compact v3 | 19 | 0 | 2 | 21 |
| N-body fast v3 | 19 | 0 | 2 | 21 |
| Binary trees | 11 | 1 | 3 | 15 |

Each complete owner occupies one line in these three files. Their long numeric
arrays are literal values within a binding. The n-body `Fixed` binding contains
a boxed formatter expression, not extra independent bindings. Tacit function
arguments, branching expressions, signatures and recursion remain within their
named owner. The `Tree` fields describe one record; they do not execute separate
assignments. `Long` is a separate binding and both its construction and final
output are counted. The tree batch output is a top-level statement calling the
independently counted `Batch` binding.

There are no comments, blank lines, detached delimiters, imports or authored
auxiliary modules in these exact complete files. Every line is enumerated by
[`uiua_retained_source_units.py`](../../../tools/qualification/uiua_retained_source_units.py).
The two n-body sources differ in the expression owned by `Advance`; that change
does not add or remove a source owner. The unchanged tree alias requires no
second source-count policy or additional native observation.

This packet concerns source counts only. The retained timing reports, original
work reviews, discarded observations and source provenance still require their
separate publication reconciliation. Formatted LOC is unavailable. Neither this
packet nor its pure tests admits data to the chart or runs Uiua.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -I -S -B tools/qualification/test_uiua_retained_source_units.py
```
