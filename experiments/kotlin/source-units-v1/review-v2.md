# Kotlin source-owner review v2

This is a direct review of the forty authored files in the completed [v3 native reader run](../source-counts-v3/run-v1/report.json): twenty application mains and their twenty application helpers. The expected source counts below come from reading the original saved source and assigning the approved source units. A separate pure Python comparison reconciled every exceptional source row with the v2 counter's native-PSI owner accounting. No Kotlin, JVM, compiler, application workload, or formatter ran during this review.

The [public methodology](../../../docs/methodology.md), [approved canonical boundary rules](../../../archive/validation/loc-normalization/20261012/canonical.py), and [approved remaining-source accounting](../../../archive/validation/loc-normalization/20261012/foreign_core.py) govern this review. Each explicit executable header is one unit, its opening brace adds no unit, each written executable close is one unit, and independent body statements/declarations count separately. Expression-only functions and scalar conditionals retain their physical source unit. Data and argument wrapping remain physical source rows. Constructor `val` fields are independent declarations. Lambda bodies retain their explicit header, body, and close.

This owner review supplies expected counts for the separate provenance/qualification stage. It does not itself qualify canonical LOC, supply formatted LOC, establish compiled required work, or admit timing data to charts. The v1 counter and failed replay remain preserved. The corrected implementation is [kotlin_source_units_v2.py](../../../tools/qualification/kotlin_source_units_v2.py), with grammar `kotlin-native-psi-owners-v2` and unchanged approved rule version `canonical-source-units-20261012-approved-rule-v2`.

## Independent artifacts and source aliases

For every benchmark, the compact and optimized `source.kt` bytes match exactly, and their complete native PSI node arrays match exactly. All twenty helper `source.kt` byte strings and complete PSI node arrays also match the common helper. In all forty authored files, the original `source.kt` equals its saved `psi-source.kt`; no authored-source newline transformation is needed. Each form nevertheless has its own retained `psi.json`, source path, source record, and counter result. The comparison does not substitute one form's artifact for another in the replay.

The source links below identify each independently retained main. The matching helper is in the same reader source inventory under `kotlin-BENCHMARK-FORM--application-helper/source.kt`.

| Benchmark | Compact source | Optimized source | Main physical | Main canonical | Helper physical | Helper canonical | Profile physical | Profile canonical |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| nbody | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-nbody-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-nbody-optimized--application/source.kt) | 55 | 77 | 23 | 26 | 78 | 103 |
| mandelbrot | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-mandelbrot-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-mandelbrot-optimized--application/source.kt) | 37 | 43 | 23 | 26 | 60 | 69 |
| spectralnorm | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-spectralnorm-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-spectralnorm-optimized--application/source.kt) | 28 | 43 | 23 | 26 | 51 | 69 |
| binarytrees | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-binarytrees-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-binarytrees-optimized--application/source.kt) | 22 | 26 | 23 | 26 | 45 | 52 |
| fannkuchredux | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-fannkuchredux-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-fannkuchredux-optimized--application/source.kt) | 39 | 60 | 23 | 26 | 62 | 86 |
| fasta | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-fasta-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-fasta-optimized--application/source.kt) | 38 | 53 | 23 | 26 | 61 | 79 |
| knucleotide | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-knucleotide-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-knucleotide-optimized--application/source.kt) | 43 | 56 | 23 | 26 | 66 | 82 |
| pidigits | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-pidigits-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-pidigits-optimized--application/source.kt) | 33 | 36 | 23 | 26 | 56 | 62 |
| regexredux | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-regexredux-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-regexredux-optimized--application/source.kt) | 32 | 35 | 23 | 26 | 55 | 61 |
| revcomp | [compact](../source-counts-v3/run-v1/native-reader/sources/kotlin-revcomp-compact--application/source.kt) | [optimized](../source-counts-v3/run-v1/native-reader/sources/kotlin-revcomp-optimized--application/source.kt) | 29 | 70 | 23 | 26 | 52 | 96 |

Each table row applies separately to both forms. Every profile includes its application helper; aliases do not remove authored files from the counted source closure.

## Handwritten row-unit ledger

The following ledger was assigned from the source before comparison with counter output. An entry `17:3` means original source line 17 owns three canonical units. Every nonblank source row not listed owns exactly one unit; blank rows own zero. These authored sources contain no comments requiring a different physical baseline. This ledger therefore specifies every source row's expected contribution, including rows with a standalone written close.

| Source, both forms | Rows whose contribution differs from one |
| --- | --- |
| nbody Main | `17:3, 30:2, 31:3, 34:2, 35:2, 36:2, 41:5, 50:3, 51:5, 52:3, 54:3` |
| mandelbrot Main | `13:2, 31:5, 34:2` |
| spectralnorm Main | `11:4, 16:4, 20:3, 23:4, 27:5` |
| binarytrees Main | `4:2, 17:4` |
| fannkuchredux Main | `7:4, 16:7, 24:3, 31:4, 35:7, 36:2` |
| fasta Main | `10:4, 14:6, 15:2, 24:2, 27:2, 29:2, 35:2, 36:2, 37:2` |
| knucleotide Main | `20:2, 21:3, 23:2, 33:3, 37:6, 39:2, 42:2` |
| pidigits Main | `21:2, 24:2, 25:2` |
| regexredux Main | `10:2, 28:2, 30:2` |
| revcomp Main | `5:8, 6:12, 7:10, 8:2, 14:9, 15:2, 23:2, 26:3, 28:2` |
| Every Support helper | `17:4` |

Every main's physical count, canonical count, and complete exceptional-row ledger matched its independently retained v3 PSI result under the v2 counter. All twenty helpers separately matched 23 physical and 26 canonical units.

## Source-owner decisions

### Common application helper

The common [compact helper](../source-counts-v3/run-v1/native-reader/sources/kotlin-nbody-compact--application-helper/source.kt) and its [optimized counterpart](../source-counts-v3/run-v1/native-reader/sources/kotlin-nbody-optimized--application-helper/source.kt) illustrate the identical source retained separately for all twenty forms. Its decomposition is four package/import units; two object header/close units; six units for `size`; three expression-only `input`, `text`, and `bytes` functions; four units for the block `write(bytes)` overload; one expression-only `write(text)` unit; five units for `fixed`; and one expression-only `lines` unit. Total: 26.

Line 10's initializer `if` and line 22's returned `if` are scalar expressions, so neither invents control headers, branch-body units, or closes. The line-22 then expression is the string template `"-$rounded"`. Actual PSI `THEN` container node 584 owns exactly one expression, template node 585, at UTF-16 offsets 983..994. Masking this literal for punctuation handling must not erase its native body identity. The template interpolation reads a scalar value; it introduces no block or independent statement. Line 24's character and string punctuation remains literal data. Only line 17 expands: function header, two output statements, and its written close.

### N-body

Main line 7 is one expression-only function, despite its long parameter and array argument lists. Packed declarations at lines 17, 30, 31, and 50 each count independently; packed updates at 34–36 and 52 also count independently. Each line-41/51 `for` owns one header, three assignments, and one written close. Line 54's `repeat` callback owns one combined call/lambda header, one `advance` statement, and one close. The array initializer at lines 44–49 retains all six physical rows, including its nested calls and trailing argument delimiters; it is not collapsed to one declaration row. The remaining function/loop headers, bodies, and written closes already occupy separate source rows. Total: 77 main units.

### Mandelbrot

The unbraced statement `if` at lines 13 and 34 owns a header and a separate body, without an invented close. Line 31 owns its `if` header, three statements, and written close. In contrast, line 29's `if` is a scalar operand in a single assignment; it remains one unit. The PBM header string on line 22 contains scalar interpolation and escaped newlines, not executable boundaries. Total: 43 main units.

### Spectral norm

Line 5 is one expression-only function. The scalar `if` inside line 11's sum assignment remains part of that assignment; the surrounding `while` contributes a header, the sum assignment, increment, and close, totaling four. The packed `ata` definition on line 16 also has four units. `DoubleArray(n) { 1.0 }` at line 20 retains its callback header, literal value body, and close: three units. The line-23 callback has a header, two calls, and close: four. Line 27's `while` has a header, three updates, and close: five. Total: 43 main units.

### Binary trees

Line 4's two promoted `val` constructor fields are two declaration units; there is no class body and no fabricated closing unit. The `tree` and `check` functions at lines 5–6 are scalar expression functions with scalar `if` alternatives, each one unit. Their nested function calls do not become separate statements. Line 17's packed `while` owns header, accumulation, increment, and close. String interpolation on lines 10, 18, and 21 contains scalar values/calls without independent block work, so it retains the surrounding statement's single physical unit. Total: 26 main units.

### Fannkuch-redux

The line-7 loop owns four units. Line 16's prefix-swap loop owns seven: header, local declaration, two assignments, two increments/decrements, and close. Line 24's `IntArray` callback owns three units. Line 31's count-reset loop owns four. Line 33's scalar conditional contributes to one checksum assignment. Line 35 owns seven units: outer loop header, rotation call, count decrement, unbraced `if` header, `break` body, `r` increment, and outer written close. Line 36 is another unbraced `if` header/body pair. Total: 60 main units.

### FASTA

The ALU literal and probability tables at lines 5–7 each occupy one physical data row. Character literal punctuation is masked and does not create statement boundaries. The returned map callback on line 10 has one combined expression/lambda header, the `sum` update, the returned pair expression, and a close: four units. Line 14's packed `while` has six units, including the nested unbraced `if` header/body and the single outer close. Lines 15, 24, 27, and 29 each have an unbraced control header and body. Lines 35–37 each contain two independent statements/declarations. Total: 53 main units.

### K-nucleotide

Line 20's unbraced `if` is two units. `takeWhile` on line 21 and `associateWith` on line 33 each retain callback header, value body, and close. Line 23 contains the written prior-branch close plus the `else if` header; its condition does not create an extra nested header. Line 25's uppercase selection is a scalar initializer and remains one unit. Line 37 owns two distinct callback header/body/close triples, one for `compareByDescending` and one for `thenBy`, totaling six; neither callback is suppressed as the other's scalar continuation. The trailing `)` is an argument delimiter, not another executable unit. Lines 39 and 42 are unbraced `for` header/body pairs; the destructured loop parameter on line 39 does not add body declarations. Total: 56 main units.

### Pi digits

Line 5 is one expression-only function. The two quotient declarations at 16–17 are separately written rows. Lines 21 and 24 each contain an unbraced statement `if` header/body pair. Line 25 contains the written then-branch close plus the explicit `else` header: two units. Assignment operators inside ordinary body statements remain one per independently written assignment. Literal output padding and interpolated digit counts add no control owner. Total: 36 main units.

### Regex-redux

The variant and replacement pattern tables at lines 5–6 each preserve one physical row. Brackets, bars, and escapes inside string literals do not create executable owners. The unbraced `while` on line 10 and `for` loops on lines 28 and 30 each own one header and one body. The destructured replacement pair is a loop parameter, not two extra declarations. Scalar calls in the output interpolation remain inside the output statement. All other function/loop bodies and closes already occupy separate rows. Total: 35 main units.

### Reverse complement

The complement function's `when` is an explicit branch owner: its header and written close contribute two units, and each of sixteen entries contributes one branch header and one body. Thus this function owns 34 units. The fifteen character-result branches are still bodies after literal punctuation is masked. The `'T', 'U'` alternatives share one entry/header and one body; they are not two branches. The `else -> error(...)` entry also owns two units. Lines 5–8 therefore contribute 8, 12, 10, and 2 units.

For the first entry, actual PSI node 64 spans `'A' -> 'T'`, with its condition before the arrow and its character body node 71 at UTF-16 offsets 118..121. Selecting direct native children after the arrow identifies exactly that body; a hidden literal root must not be mistaken for an absent body. The `record` function contributes 16 units, including nine at packed line 14 and two at unbraced line 15. Main contributes 18 units; line 26 has a prior written close and an unbraced `else if` header/body, totaling three. Including package/import gives `2 + 34 + 16 + 18 = 70` main units.

## Correction bounds and validation

The v2 correction is limited to native body selection. `Tree.semantic` defaults to excluding masked nodes as before. Only `Tree.role` and post-arrow `KtWhenEntry` selection include masked roots, and both still require exactly one native expression body. Literal content remains masked and its descendants are not traversed as ordinary executable source. Statement-versus-value `if` rules, explicit block/header/close accounting, independent callback ownership, physical data wrapping, and unsupported-owner diagnostics are unchanged.

The [pure regression suite](../../../tools/qualification/test_kotlin_source_units_v2.py) passed 48 tests. It retains the original synthetic tests and adds actual v3 helper and reverse-complement regressions, scalar-versus-statement literal controls, unbraced loop literals, mixed `when` alternatives, missing/multiple native body rejection, punctuation masking, and independent-work interpolation gating. It reproduces the actual replay in memory without writing a replay artifact, checks all forty authored candidates and all fourteen existing fixture expectations, and verifies that all eighteen previously passing authored results are unchanged except for the explicit grammar version. All probe/count qualification flags remain false, formatted counts remain null, and native terminal verification remains a separate qualification obligation.

The handwritten source ledger and expected totals above reconcile with all forty authored v2 results. No source-owner ambiguity remains in this exact authored inventory. Broader Kotlin syntax still requires its own supported-owner review; these results do not relax the counter's existing diagnostic gates.
