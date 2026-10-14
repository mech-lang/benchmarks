# Authored-source count expectations

The ten retained typed sources have the following manual expectations under
the approved canonical source-unit rule. These are review targets for the
saved-AST replay, not admitted counts. Original sources and AST hashes are
bound by the [native artifact review](../native-stage-v1/independent-native-review-v1.json).
Formatted LOC remains unavailable.

| Workload | Nonblank noncomment rows | Canonical expectation | Change |
| --- | ---: | ---: | ---: |
| [Binary trees](../source-v1/binarytrees.ts) | 35 | 38 | +3 |
| [Fannkuch-redux](../source-v1/fannkuchredux.ts) | 55 | 76 | +21 |
| [FASTA](../source-v1/fasta.ts) | 73 | 81 | +8 |
| [K-nucleotide](../source-v1/knucleotide.ts) | 63 | 67 | +4 |
| [Mandelbrot](../source-v1/mandelbrot.ts) | 52 | 66 | +14 |
| [N-body](../source-v1/nbody.ts) | 124 | 126 | +2 |
| [Pi digits](../source-v1/pidigits.ts) | 41 | 43 | +2 |
| [Regex-redux](../source-v1/regexredux.ts) | 32 | 32 | 0 |
| [Reverse complement](../source-v1/revcomp.ts) | 75 | 81 | +6 |
| [Spectral norm](../source-v1/spectralnorm.ts) | 39 | 51 | +12 |

Binary trees expands the packed constructor row into its header, two authored
`readonly` parameter fields and written close: four units instead of one.
The multiline conditional return remains three physical rows. Ordinary class
and function rows require no additional change.

Fannkuch expands the unbraced initialization loop (+1), the four- and three-name
declarations (+3 and +2), two packed two-statement while loops (+3 each), the
packed three-statement swap (+2), one unbraced conditional (+1), and two packed
`if`/`else` pairs (+3 each). These sum to +21. Semicolon omission does not merge
distinct native statements.

FASTA expands its initial four-name declaration (+3), `seqi`/`lenOut` (+1),
three unbraced conditionals (+1 each), and the packed close/`else` header (+1).
The ALU strings and both probability objects preserve their physical wrapping;
object properties are data, not additional statement owners.

K-nucleotide expands the comment-skip, record-boundary and invalid-base
conditionals (+1 each), the packed close/`else` row (+1), and the declaration
followed by an `if` header (+1). Its two-row final `for` header collapses to one
header (-1). The tuple type alias and import each remain one declaration.
The `.sort` and `.map` expression arrows retain their physical expression rows.
The block callback in `seq_lines().then(...)` has one combined call/header and
one written close; its trailing `);` adds no unit.

Mandelbrot expands one throwing conditional (+1), `iter`/`limit` (+1), six
uninitialized typed variables (+5), `h`/`w` (+1), the four-way assignment chain
(+3), the unbraced bit conditional (+1), the close/`else if` row (+1), and the
final unbraced flush (+1). Their sum is +14.

N-body adds two units for the packed `px`, `py`, `pz` declarations. Its seven
explicit fields and seven constructor assignments already occupy separate
rows. Constructor formals add no fields. Every wrapped planet constructor
argument and data closing row is retained.

Pi digits adds one unit each for the zero-input return and the unbraced final
break. Its BigInt types, numeric literals and sequential arithmetic introduce
no other row expansion. Regex-redux has no packed executable units requiring
expansion; its regex array and replacement chain retain all physical rows.

Reverse complement adds four units for unbraced throwing/return/output
conditionals and two for the packed close/`else if` and close/`catch` rows.
Typed nullable state and the template error message remain within their
ordinary owners.

Spectral norm expands the compact `eval_A` (+2), the packed `eval_AtA_times_u`
body (+3), the `u`/`v` declarations (+1), two packed two-statement loops (+3
each), and `vBv`/`vv` (+1), while the detached opening brace of the ten-iteration
loop removes one physical unit (-1). In each of the two matrix-product
functions, two detached opening braces (-2), a two-name declaration (+1) and
an unbraced inner loop (+1) cancel. The overall change is +12.

The thirty fixture contracts additionally require 21 successful candidate
counts, seven explicit null review cases and two null parser rejections. Their
small saved-AST checks pass. Final admission still requires the locked complete
replay and review of its retained line/event/coverage records.
