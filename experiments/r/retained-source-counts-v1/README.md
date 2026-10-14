# Canonical owners for six retained R sources

This packet reviews the exact six R source identities associated with the completed N-body, binary-trees and fannkuch workloads in the [retained coverage inventory](../../shared/retained-coverage-audit-v1/report-inventory.json). It does not apply to other files with similar compact or optimized names. In particular, the measured fannkuch sources are `array-compact.R` and `array-batched.R`.

The [checker](../../../tools/qualification/r_retained_source_units.py) applies the approved `canonical-source-units-20261012-approved-rule-v2` semantics to explicitly reviewed source owners. It is an exact-source mapping, not a general R parser. Every source must match its recorded SHA-256. The owner ledger assigns every significant noncomment character, preserves literal spelling, records explicit zero-unit opening braces and one-unit written closers, and rejects changed or unrelated bytes.

| Retained source | Physical code rows | Canonical units |
| --- | ---: | ---: |
| N-body compact | 19 | 19 |
| N-body optimized | 24 | 24 |
| Binary trees compact | 15 | 15 |
| Binary trees optimized | 20 | 21 |
| Fannkuch array compact | 30 | 31 |
| Fannkuch array batched | 37 | 38 |

The count increases arise from three specific packed rows:

- Binary trees optimized line 7 has an unbraced `for (...)` header followed by the independent `total <- ...` body binding: two units.
- Fannkuch array compact line 10 and array batched line 14 each contain an outer `if (...)` header and an inner `for (...)` header: two units. The following written opening brace adds no unit; the later written closer contributes its own unit.

All other noncomment rows have one reviewed owner. N-body's `energy <- function() ...` is one expression-function binding. The tree `make` and `check` definitions also retain their expression bodies, including the value-producing `if/else`; wrapping the same expression function in `compiler::cmpfun(...)` does not invent an executable block. The `function(i) check(make(d))` argument to `vapply` remains inside the enclosing `total` binding.

Named call arguments such as `byrow=`, `each=`, `by=`, `envir=`, `sep=`, `mc.cores=` and `mc.preschedule=` are structural arguments, not independent assignments. The packed-row expansions concern actual control owners, not these equals signs. Numeric/vector/matrix literals and quoted or backtick-delimited values remain in their enclosing owners.

The governing retained implementations are [canonical.py](../../../archive/validation/loc-normalization/20261012/canonical.py), [normalizer.py](../../../archive/validation/loc-normalization/20261012/normalizer.py) and [value_forms.py](../../../archive/validation/loc-normalization/20261012/value_forms.py). Their explicit header/closer rules, R named-argument handling and expression-function conditional ownership are recorded as policy dependencies. This packet does not execute those lexer-dependent tools or substitute a different lexer.

[Owner proposals](owner-proposals-v1.json) contain exact spans, source excerpts, named-argument records and the complete six-source identity mapping. The [independent review](qualified-source-counts-v1.json) qualifies all six canonical counts after reading the complete sources, replaying their owner ledgers and checking every source and policy pin. Formatted LOC remains unavailable. This source-count packet grants no required-work, runtime, timing or chart admission and launches no R process. Native evidence and existing completed samples must be reconciled separately.

The [four focused pure tests](../../../tools/qualification/test_r_retained_source_units.py) verify all six source hashes, complete character coverage, the three exact packed rows, expression-function and named-argument ownership, and rejection of source mutations or wrong identities.
