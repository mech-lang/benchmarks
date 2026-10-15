# Exact Rebol source-count proposal

This unprepared packet describes canonical owners for ten authored Rebol mains,
four authored Rebol support files, and the additive corrected general C
extension. Its 12 pure test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). No actual source projection
has run. Source digests are deliberately unset;
no canonical count, compiler input, runtime, required work, timing, or chart
admission is qualified by this draft.

The [owner ledger](owner_ledger.py) applies the existing
[approved rule v2](../../../archive/validation/loc-normalization/20261012/PLAN.md)
through a finite source mapping. The
[checker](../../../tools/qualification/rebol_source_units.py) records exact byte
spans and requires complete, nonoverlapping coverage of every significant
character. Every nonblank row is explicitly listed; an omitted row fails. It is
not a general Rebol parser. The existing
[R owner checker](../../../tools/qualification/r_retained_source_units.py) and
[Lua C-helper review](../../lua/retained-pidigits-v1/c-helper-owner-review.json)
provide the same exact-source review pattern, not transferable numeric counts.

Each workload counts its actual `main.reb`, `clbg_io.reb`,
`clbg_primitives.reb`, and the entire corrected
[clbg_primitives.c](../extension-api-v2/clbg_primitives.c). Pidigits additionally
counts `clbg_big.reb`; regexredux additionally counts `clbg_regex.reb`.
There are eight four-file bundles and two five-file bundles, with fifteen
distinct physical files. A shared file is counted once within each bundle.
There is one authored main per workload and no invented second source form.
Nine mains and the shared Rebol support remain under
[`drafts/private-v1`](../../../archive/languages/rebol/20261013/drafts/private-v1/).
The new C file explicitly substitutes for the old C source in a future bundle;
the old file, profiles, contract, and observations remain unchanged. Both C
revisions are never added to the same bundle.

Fannkuch uses the additive [zero-size revision](../fannkuch-zero-v1/main.reb).
The archived main rejects `N=0`, which the existing shared corpus requires to
produce `0` and `Pfannkuchen(0) = 0` on separate lines. The new main accepts
0–12 and initializes its permutation total to zero only for zero-size input.
Every positive input retains the original factorial, permutation and flip
operations. Its loader points to the same retained IO facade. The original main
and corpus map remain unchanged; a future bounded plan must explicitly bind
both this main substitution and the corrected C substitution. Row 7 is one
composed value binding under the existing rule. The two mains are not counted
together. Native output verification remains pending.

The complete authored C helper remains counted even when a workload only uses
its IO commands. Unmodified GMP/PCRE2, the runtime, generated SDK headers, SDK
generators, build inputs/products and validation fixtures are disclosed
provenance, not additional authored application LOC. This follows the retained
[primitive contract](../../../archive/languages/rebol/20261013/drafts/private-v1/PRIMITIVE_CONTRACT.md)
and the
[generated-SDK scope](../../../archive/languages/rebol/20261013/revisions/actual-source-sdk-plan-v1/REVIEW.md).
Meaningful authored C directives remain counted.

Executable function/control headers contribute one unit, their openings zero,
independent body operations separately, and each written executable close one.
Function specifications, `/local` names, datatype lists, argument lists and
loop conditions remain structural. Thus the IO condition containing `chunk:`
and the regex conditions containing `hit:` are one loop header each. Every
explicit `func` body in these sources retains its header/body/close even when
the body is a single expression. The knucleotide comparator combines its
containing `sort/compare` prefix with the callback header, as in the approved
callback rule; it does not add another prefix unit.

The exact value-only `either` expressions retain one composed value, including
their containing binding/call. Multi-statement branches in pidigits and
fannkuch remain separate owners. The exact `base-code` switch has single
constant results and returns `none` on no match, matching retained
[`n-control.c`](../sdk-generation-v1/work-v1/source/src/core/n-control.c)
`REBNATIVE(switch)`. This is a source-specific decision, not a claim that the
existing generic value-form recognizer supports Rebol. Revcomp's `case`, its
written condition arms and all written closes are explicit owners, including
the empty comment arm. Literal/data wrapping in FASTA, nbody and regex tables
is retained rather than reformatted away.

The C ledger expands independent comma declarations, chained assignment
targets, packed labels and statements, and all nine enum constants. Loop-header
separators and macro argument lists are structural; macro expansions are not
added. `module_source` retains its declaration and every authored string row,
including the nine separate typed command declarations on rows 27–35. It is
authored C data, never generated SDK output, and is not counted again as a
second runtime-produced Rebol file.

The recorded focused test command and still-pending proposal command are:

```sh
PY=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
E=/private/tmp/mech-benchmark-completion
"$PY" -I -S -B "$E/tools/qualification/test_rebol_source_units.py"
"$PY" -I -S -B "$E/tools/qualification/rebol_source_units.py" propose \
  --root "$E" \
  --output "$E/experiments/rebol/source-counts-v1/proposal-v1.json"
```

The proposal output is exclusive-create and always unqualified. Its exact
fifteen source identities, complete spans, individual counts and bundle totals
need independent owner review before any digest freeze or separate admission
receipt. `count_source` rejects every current source while its reviewed digest
is unset. Even a frozen exact-source count does not itself grant admission.
Native compiler-input and primitive/runtime qualification are separate gates;
these fixtures execute neither Rebol nor C. The focused
[Rebol](fixtures/owners.reb) and [C](fixtures/owners.c) sources exercise packed
operations, callback ownership, structural conditions, enum constants,
declarations, embedded command strings and preserved data wrapping.
