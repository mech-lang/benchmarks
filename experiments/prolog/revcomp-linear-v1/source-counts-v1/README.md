# Linear reverse-complement source counting

This additive preparation reuses the qualified original Prolog reader and
canonical owner counter. No source-count native command has run for this
candidate, and no candidate count is admitted.

The frozen V5 files are:

| Component | Path | SHA-256 |
| --- | --- | --- |
| Original source reader | `archive/validation/loc-normalization/20261013/prolog-proposal-v5/scan_source.pl` | `b48e07039914d448e4f313235f347f4604269d0a9802896f0d019ed3e7c52021` |
| Canonical counter | `archive/validation/loc-normalization/20261013/prolog-proposal-v5/foreign_prolog.py` | `6b20c429b56acc923f72615438d99ec2fa67c08f550d36510fe7c1fede787ed8` |

The existing qualification is retained in
`archive/languages/prolog/20261013/source-counts/original22-replay-v1` and
`experiments/prolog/qualified-original22-v2`.
`tools/qualification/prolog_seal.py` seals that fixed historical cohort: its
22-source/20-profile expectations and comment-free source assertions are not a
generic interface for this new source. The reader and counter themselves
already support comments and exclude their text from physical and canonical
counts. The seven native-fixture inputs below exercise this again.

## One additional ordinary builtin

The candidate introduces four written `string_codes/2` calls. V5 has no selected
binding for that predicate, so its unchanged counter correctly refuses to
produce a canonical total for those calls. The
[adapter](../../../../tools/qualification/prolog_revcomp_source_units.py)
inherits V5's complete parsing, owner, control, literal and meta-flow rules and
adds only resolution to `system:string_codes/2`. Existing written definitions
and imports take precedence. No other name, arity or module is added, and this
builtin has no meta-argument slots.

The retained official SWI-Prolog 10.0.2 source supports this classification:
`src/pl-string.c:161–166` implements `string_codes/2` by calling `string_x` with
`PL_CODE_LIST`; `:610` registers it with flags zero. Its arguments are string
and code-list data, not executable goals. The source root is the retained
`prolog-comparison/20261013/.build/swi-runtime-directory-v1/official-source/swipl-10.0.2`
under the compiler worktree. Before the adapter is used, the new
[metadata diagnostic](inspect_targets.pl) must record the exact retained
runtime and `built_in=true`, `foreign=true`, `defined=true`,
`meta_predicate=false` for this one target. Source inspection does not replace
that native receipt.

The original parser covers the remaining candidate syntax: one module,
`initialization(run, main)`, ordinary clauses and facts, lists and strings,
`is`, comparisons, unification, cuts and parenthesized conditionals. Existing
formal meta-flow inference follows `execute/1` through `run_checked/1` to
`call/1`; the `catch/3` handler has its own written goal. The candidate is never
consulted by the source reader, so its initializer and benchmark bodies cannot
run during counting. `formatted_loc` remains null because this pipeline has no
qualified formatter.

## Native invocation after bounded conformance closes

The [serialized controller and invocation protocol](EXECUTION.md) implement
the nine-reader stage. Its source review and sixteen pure tests are complete;
plan preparation, native execution and candidate owner review remain pending.

Use the exact retained binary and environment from the successful bounded
candidate plan. Hold the existing common mutex continuously, verify all input
and runtime pins, and use the existing owned process observer for every command.
Retain native start/active/final receipts, stdout/stderr, source bytes and their
complete artifact closure. A command list alone grants no qualification.

The adapter exports these exact argv constructors:

```python
metadata_command(retained_binary)
# swipl -q -f none -l <packet>/inspect_targets.pl
#       -g prolog_linear_loc_targets:main --

reader_command(retained_binary, original_source)
# swipl -q -f none -l <frozen-v5>/scan_source.pl
#       -g prolog_source_scan_v1:main -- <original-source.pl>
```

Require native exit zero, empty stderr and complete JSON stdout. Run the
metadata command once, then the unchanged reader once for each of the seven
fixture sources and once for the candidate: nine native processes total. The
reader argv matches the previously qualified original-source scanner. Do not
load the candidate as a script or invoke its main goal.

The source-only [fixture manifest](fixtures-v1/manifest.json) was generated with
the pinned isolated Python using:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/prolog_revcomp_source_units.py --write-fixtures experiments/prolog/revcomp-linear-v1/source-counts-v1/fixtures-v1
```

This command only writes seven `.pl` inputs and their manifest; it starts no VM.
The [command draft](command-draft-v1.json) records the nine exact native argv
arrays and the small source-file pins. It is not a verified execution plan;
the bounded prerequisite and runtime closure must still be bound under the lock.
The native fixture expectations are 4 canonical units for ordinary,
system-qualified and commented calls; 5 when a written local definition shadows
the builtin; and null counts with explicit diagnostics for another module,
another builtin, or a control-valued data argument. All seven must pass against
the actual new reader packets before the adapter is qualified.

For each retained packet, `project(source_bytes, packet, metadata, runtime_home)`
calls the unchanged V5 counter using the narrowly extended bundle context.
For the actual candidate, `project_candidate` additionally requires original
bytes to equal the compiled source from the bounded stage and reconciles the
reader's written predicate inventory against that stage's inspected WAM. It
retains full source-owner expansions and leaves admission flags false.

Before admitting a count, independently review every candidate owner span and
the exact compiler-source/QLF/WAM bridge. Bind the successful bounded terminal,
both compiler metadata receipts, the candidate and compiled source hashes,
reader/counter/adapter/metadata/fixture hashes, retained 31-fixture qualification,
new native receipts and new owner-review evidence in the additive closure.
Do not rerun the historical 31 fixtures or 22 source readers; their code is
unchanged. Pure saved-AST regression tests are separate evidence.
