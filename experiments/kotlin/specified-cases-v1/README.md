# Kotlin specified bounded cases

This source-only packet adds the original Kotlin specification's missing output
cases. Preparation and native execution have not run. The existing 156-case
controller and corpus remain unchanged. This packet requires their actual
completed report and terminal hashes before it can prepare its own references.
It reconciles all 156 saved case validation/process hashes with the original
terminal inventory, requires their exact input/output artifacts, and checks
that the retained output bytes reproduce the saved output validation. This
binds existing output evidence; it launches no native process and proves no
additional runtime arithmetic, allocation or JIT behavior.

`gap-analysis.json` records the source comparison against the immutable
`source-owner-review-v1/bounded-checks.json` and the closed 78-reference corpus.
The supplement contains 15 references and 30 independent form executions:

| Workload | Additional cases |
| --- | --- |
| Pi digits | 100 |
| FASTA | 19, 20, 21, 59, 1000 |
| Mandelbrot | 64 |
| N-body | 10, 1000 |
| Spectral norm | 10 |
| Reverse complement | One multi-record fixture at lengths 0, 1, 59, 60, 61, 121, with standalone CR, LF, CRLF, comments, both ambiguity-symbol cases and final EOF without newline |
| Regex redux | All 50 concrete words from the nine count patterns, uppercase copies, and a separate overlapping-candidate fixture |
| K-nucleotide | Two combined fixtures, using space and tab descriptions, with a THREE-like decoy, comments, mixed case, wrapped selected sequence and a following record |

The original corpus already contains every specified fannkuch size. Its reverse
complement record lengths are 0, 1, 8, 16, 32 and 208, and it has no standalone
CR delimiter. Its regex fixtures only produce positive counts for the first
pattern, and none distinguish overlapping candidates from nonoverlapping
matches. Its K-nucleotide cases cover the individual features separately;
the new fixtures exercise their required combination.

## Independent expectations

Numeric and DNA expectations reuse the existing independent Python reference
source at `archive/languages/c3/20261012/revisions/private-v1/references.py`,
SHA-256 `6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3`.
That source predates the scored Kotlin forms and imports no scored code.
Preparation pins its bytes and generates each expected output once under the
shared mutex. The separate reference directory, input bytes, expected bytes,
source hashes and precise fixture IDs become plan/report inputs.

Regex expectations also have a new independent implementation in `oracles.py`.
It enumerates 50 explicit eight-byte words, scans literal windows, and advances
by eight after a match. The words are distinct and each belongs to only its
listed pattern. `Z` separates all words, preventing cross-word matches. The
uppercase copies cannot match the case-sensitive lowercase patterns. The count
vector is therefore `[2,6,6,6,6,6,6,6,6]`.

The overlap fixture contains `agggtaaagggtaaa` and `tttaccctttaccct`, separated by
`Z`. Each has two overlapping first-pattern candidates, but only one match
survives advancing by eight. Its expected vector is `[2,0,0,0,0,0,0,0,0]`, versus
four candidates in the independent overlapping-window scan.

The regex byte alphabet is restricted to `ACGTacgtZ`. Of the first three ordered
substitutions, only literal `at` can match; it becomes `<2>` and then `|` in the
fourth pass. A simple byte scanner performs the fifth pass over nonempty
`|...|` pairs. The new expected output uses that literal implementation,
including all three lengths. Preparation requires its complete output to agree
with the retained regex oracle. The prior 156 cases continue to supply the
other substitution-pattern and boundary checks. No Kotlin regex implementation
is used to generate these expectations.

N-body retains the closed corpus's two finite energy-line comparison within
`1e-8`; complete actual and expected byte streams remain available. All other
supplemental outputs require complete byte equality. Outputs establish bounded
behavior only, and do not establish required internal arithmetic or allocation
work.

## Execution and evidence

The new controller imports the immutable atomic observer at
`kotlin_bounded.py` SHA-256
`916a94f68e191cce8d074121859121351517c8ab2132bb5953ebc62621ba710e`.
It compiles only an unchanged copy of `BoundedProbe.java`, with the original
retained `javac`. No Kotlin source, helper or subject class is recompiled.
All twenty original profile bindings, forty authored main/helper inputs,
complete retained class inventories and ten explicit compact/optimized alias
pairs remain in the plan. Sixteen forms have supplemental cases; the original
156 checks continue to cover all twenty forms.

Each of the 30 cases gets a fresh JVM and the exact retained class directory,
original stdlib and isolated subject loader. Actual main/helper class origins,
owner resources, runtime flags, G1 logs, stdin and complete stdout are checked.
The original flags remain `-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`.
The process observer retains its 30-second deadline, five-second cleanup bound,
2 GiB observed process-group RSS limit, 8 MiB native file limit, bounded pipes,
atomic launch registration and unreaped-child ownership. The timing mutex at
`/tmp/mech-clbg-timing.lock`, inode 79859134, is held by preparation and run.
Neither command may overlap benchmark timing.

Native launch requests, actual starts, observed main invocations/returns and
qualified output cases are counted separately. Success requires 31 clean
native receipts: one diagnostic compiler and 30 JVMs. Failures stop the batch,
retain available streams and artifacts, reconcile actual starts against saved
process receipts, and write terminal status under the mutex. There is no retry
or automatic resume. Reference generation is separate from native execution.
Clean receipts include exact ownership, exit, cleanup, monitor counts, observed
RSS, stream hashes and the original timeout/file bounds. Each successful
command's complete required artifact inventory is snapshotted when validated;
the terminal scan must retain those same files, sizes and hashes. Changed or
missing validated output, diagnostics or process receipts clear qualification.

A successful report qualifies only the additional specified output coverage.
The original 156 cases plus these 30 cases supply 186 form checks over 93
references. `kotlin_work.py` requires explicit hashes for both completed report
and terminal pairs and validates all 30 supplemental cases before preparing
required-work/JIT diagnostics. This packet leaves source-work, JIT, actual
runtime dependency closure, LOC, full timing and chart gates unqualified.

## Deferred commands

After the actual 156-case bounded run succeeds:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_supplement.py prepare \
  --bounded-report experiments/kotlin/bounded-work-v1/run-v1/report.json \
  --bounded-report-sha256 ACTUAL_COMPLETED_BOUNDED_REPORT_SHA256 \
  --bounded-terminal-sha256 ACTUAL_COMPLETED_BOUNDED_TERMINAL_SHA256 \
  --plan experiments/kotlin/specified-cases-v1/plan-v1.json \
  --output experiments/kotlin/specified-cases-v1/run-v1
```

Preparation creates `plan-v1-references/` beside the plan. It requires all three
paths to be fresh. A failed preparation can retain a partial reference directory;
use a reviewed new plan path rather than overwriting evidence.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_supplement.py run \
  --plan experiments/kotlin/specified-cases-v1/plan-v1.json \
  --plan-sha256 ACTUAL_PREPARED_PLAN_SHA256
```

Thirteen small pure tests cover exact numeric gaps and both forms, all literal regex
alternatives and overlap semantics, the reverse-complement boundary inventory,
both combined K-nucleotide records, completed-report requirements, failed
post-launch native accounting, clean/resource receipts, artifact/traversal
failures, 31 command snapshots and binding all 156 original saved case proofs.
They run without JVMs, numeric workload generators, full runtime hashes or
preflight. Native validation remains pending. Independent review should check
these new sources, the explicit fixture bytes, literal oracle derivation,
immutable-supervisor reuse and the work-stage prerequisite change.
