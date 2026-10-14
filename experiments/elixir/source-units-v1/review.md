# Elixir source-count review

The completed source-reader and ownership review support canonical source counts
for all twenty retained Elixir forms. Each bundle includes its complete main,
shared application helper, and launcher: **60 physical authored inputs** across
all ten workloads. Both compact and optimized forms have the counts below.
No remaining source-ownership ambiguity was found in these bundles.

| Workload | Original physical LOC | Canonical LOC | Formatted physical LOC |
| --- | ---: | ---: | ---: |
| Binary trees | 78 | 86 | 96 |
| Fannkuch-redux | 93 | 105 | 126 |
| FASTA | 90 | 100 | 143 |
| k-nucleotide | 93 | 109 | 119 |
| Mandelbrot | 79 | 87 | 98 |
| n-body | 114 | 130 | 186 |
| Pi digits | 73 | 81 | 92 |
| Regex-redux | 89 | 101 | 130 |
| Reverse complement | 80 | 90 | 100 |
| Spectral norm | 80 | 90 | 99 |

Physical LOC excludes blank and comment-only rows. Canonical LOC applies the
[published unit rule](../../../docs/methodology.md): expand packed independent
statements and assignments, count explicit executable headers and written
closers, and retain literal/data wrapping. Expression-only definitions and
keyword conditionals gain no artificial block units. Destructuring is one
binding. Each canonical bundle includes **61 helper units and one launcher
unit**, including authored helper code irrespective of which functions a main
uses. Their formatted physical counts are 68 and one, respectively.

The native formatter was Elixir **1.20.4**, using `Code.format_string!/2` with
line length 98. It preserved each successfully parsed source's AST after
location metadata was removed. Formatted physical LOC is a separate metric;
canonical LOC uses the original source. Applying canonical normalization to
formatted text can give a different number because argument, expression, and
data wrapping remains physical source. The reviewed n-body, k-nucleotide, and
helper differences were traced to those retained rows, with executable owners
preserved.

## Continuation ownership correction

A scalar continuation belonging to the same native AST expression contributes
no additional unit on its explicit closer's row. A continuation on another
physical row retains that row's unit. This rule applies consistently to `fn`
values and value-producing `if`, `unless`, `case`, `cond`, `for`, `with`, `try`,
and `receive` blocks. Module and named-function declarations are excluded.
Native sequence, clause, and branch boundaries prevent the rule from absorbing
the next independent statement. Tails containing assignments, independent
expression sequences, or another executable owner remain review cases.

The original spectral-norm source writes `end |> List.to_tuple()` on one row.
Its native AST places the `for` block inside that pipeline expression. The
initial counter counted the scalar tail separately while suppressing equivalent
tails after `fn`. The correction makes the original main **28 rather than 29
units**, and each complete spectral-norm bundle **90 rather than 91**. Its
formatted main remains 29 units because the formatter places the pipeline on a
separate row. All other original and formatted counts remain unchanged.

The [initial replay and counter binding](replay-v1-evidence.json) preserve that
earlier result. The [corrected replay](replay-v2.json) records all twenty revised
bundle totals. Forty-nine pure counter tests include all 120 original/formatted
application source/AST pairs and the fourteen native fixture outcomes. The
fixtures include eleven countable cases, one parsed interpolation deliberately
left for review, and two expected syntax rejections. The correction required no
additional native execution.

## Execution and evidence

The [reader plan](../source-counts-v1/plan-v1.json) binds the sixty application
inputs to the retained bounded-output cohort. The
[completed reader report](../source-counts-v1/run-v1/report.json) records one
reader process, sixty application files, and fourteen grammar fixtures, with
no application-source evaluation or recompilation. Its
[process receipt](../source-counts-v1/run-v1/source-reader.json) records exit zero,
the owned child reaped, an empty process group, and no monitor or cleanup errors.
The [terminal](../source-counts-v1/run-v1/terminal.json) retains the 372-file
artifact inventory and report linkage; the
[durable terminal](../source-counts-v1/owned-jobs/native-reader-v1/terminal.json)
also records exit zero.

This review supports source-count qualification. It does not qualify compiled
required work, full-workload timings, or chart admission. The reader and replay
artifacts retain their original unqualified flags; a separate qualification
record must bind the reviewed sources, artifacts, counter, and counts.
