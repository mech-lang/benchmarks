# Kotlin source counts

Canonical source counts are qualified for all twenty retained forms. Each
bundle includes the complete application main and shared application helper.
The [qualification record](qualified-source-counts.json) binds forty authored
inputs, all fourteen native parser fixtures, the complete native artifact and
runtime closure, and the [manual source-owner review](review-v2.md).

The [v2 counter](../../../tools/qualification/kotlin_source_units_v2.py) consumes
the original source, saved Kotlin PSI, and its explicitly bound parser text.
It applies the [published source-unit rule](../../../docs/methodology.md),
using native node ownership and UTF-16 ranges. Packed independent statements,
executable headers and written closers expand into separate units; physical
data wrapping remains. Unsupported ownership still produces a null candidate.

The first counter masked literal content before selecting control bodies. That
also hid valid string/character body roots in the common helper and reverse
complement. V2 retains those roots when selecting native bodies, while keeping
literal punctuation masked. The original [replay](replay-v1.json) and counter
remain unchanged; the [corrected replay](replay-v2.json) covers every authored
file. The manual review records each exceptional row and its expected count.

Forty-eight pure counter tests include actual saved PSI and malformed-body
regressions. Eighteen qualification tests check source membership, unresolved
owners, fixtures, process identity, commands, environment and resource policy.
Qualification reproduces the replay and rechecks all evidence under the shared
timing lock without launching a JVM or compiler.

This native reader supplies no formatter evidence, so formatted LOC remains
null. Source-work qualification, full-size measurements and chart admission are
separate stages. The [stage metadata](stage.json) and
[review manifest](review-manifest-v2.json) retain the exact source-count inputs.
