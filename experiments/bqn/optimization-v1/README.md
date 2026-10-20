# BQN k-nucleotide implementation audit

The audit compares the retained faithful BQN port with source-level alternatives,
using the same pinned CBQN rebuild on one Apple M3 Mac. Original saved timings
and source remain unchanged. The historical runtime executable had been removed;
this is a matched new comparison, not a claim of binary identity with that run.

## Repeated full-workload result

All rows below have three independent fresh-process samples in
[`full-matched-v1/report.json`](full-matched-v1/report.json). Startup, input,
up to eight worker processes, native runtime work, output and process exit are
inside the timer. Compilation, validation and diagnostic tracing are outside.
The common benchmark mutex prevents overlapping suite runs. Candidate order is
shuffled deterministically between rounds. All fifteen complete outputs match
the independent full-output digest.

| Implementation | Median seconds | Original / candidate |
| --- | ---: | ---: |
| Original faithful source | 11.573 | 1.00× |
| Frame packing, ordinary numeric keys in boxed storage, native occurrence counting | **3.548** | **3.26×** |
| Shared window composition, chunks of 100,000 starts | 5.437 | 2.13× |
| Shared window composition, chunks of 250,000 starts | 4.830 | 2.40× |
| Shared window composition, chunks of 1,000,000 starts | 3.970 | 2.92× |

The winning candidate's samples are 3.548158042, 3.560848792 and 3.539333041
seconds (sample SD 0.010815601 seconds). The initial
[`full-pilot-v1`](full-pilot-v1/report.json) also measures hoisted map methods,
vector Horner key construction and scalar-enclosed occurrence keys. Those
single-run ablations are exploratory, not repeated ranking evidence. Several
failed syntax/edge prototypes are retained with failed receipts; none is an
admitted chart result. This finite search establishes a better implementation,
not a proof that no faster BQN program exists.

## Required work and correctness

The workload requires growing built-in or third-party hash tables and counting
**all** overlapping keys at widths 1, 2, 3, 4, 6, 12 and 18. Counting only the
five printed queries or replacing maps with dense frequency arrays would change
that work. See the [primary workload rules](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/knucleotide.html).

The winning source keeps all frame/piece partitions and uses CBQN's native
occurrence-count primitive. Appending and then dropping a character creates
boxed numeric storage without individually enclosing every scalar key. On the
pinned runtime this selects the generic growing hash-table path; bare numeric
occurrence counting can instead select dense/radix shortcuts and is not used.
Every key's occurrence ordinal is computed; extraction of final requested counts
occurs only after all updates. Pieces with one key explicitly call ordinary
HashMap Get/Set because the primitive otherwise bypasses a table for that size.

A **separate instrumented executable**, never used in timing samples, verifies
one native lookup and count write per key, insertions/increments, an initial
64-slot table and observed growth. The
[`full work trace`](work-witness/full-native-keys-v1/validation.json) covers
all 368 frame/piece jobs and **874,999,961** updates, with 2,472 growths.
The [source-delta receipt](work-witness/frame-native-keys-source-delta-v1.json)
proves that removing diagnostic markers reproduces the timed source exactly.
[`native-keys-bounded-v1`](native-keys-bounded-v1/report.json) verifies fourteen
independent retained cases, including empty/missing records, comments, exact
header boundaries, line endings, ties and short sequences. Additional
[reference payloads](reference-inputs/manifest.json) retain exact compressed
inputs and Counter-based expected outputs for pilot reproduction.

The parser repair is included in candidate qualification: the original's
six-character header-prefix behavior and short/empty-input behavior are not
silently rewritten in historical records.

## Source size and provenance

The winning source is 43 noncomment physical rows and **48 application LOC under
the retained BQN manual policy**, versus 36 and 39 for the original. The full
[per-line ownership review](source-ownership-v1/ordinal-horner-grouped-v5-native-keys-v1-counts.json)
retains the old counting convention and independently reviews the added packed
statements. The proposed logical-owner policy is separate and unqualified for
BQN. This speed candidate does not replace the shorter retained source.

The optimization is newly suite-authored over the retained faithful port; the
older port's original lineage remains unresolved. It is not an unchanged
Benchmarks Game submission. General-purpose BQN FFI/process bindings are copied
unchanged and pinned separately; no new C nucleotide kernel is introduced.
The [release build receipt](release-build.json) binds compiler, SDK, CBQN commit,
submodules, runtime binary, generic bindings and linked library artifacts.

## Reproduction

Restore the exact Homebrew/compiler/SDK dependencies recorded in the build
receipt. The builder uses a separate diagnostic tree for the witness:

```sh
python3 tools/qualification/build_bqn.py --output /tmp/bqn-release-build.json
python3 tools/qualification/build_bqn.py --witness --output /tmp/bqn-witness-build.json
python3 tools/qualification/bqn_reference_inputs.py
python3 tools/qualification/bqn_knucleotide_corpus.py --sources ordinal-horner-grouped-v5-native-keys-v1.bqn --output experiments/bqn/optimization-v1/bounded-replay
python3 tools/qualification/bqn_knucleotide_run.py --sources baseline.bqn ordinal-horner-grouped-v5-native-keys-v1.bqn --input experiments/lean4/.build/inputs/n25000000.fasta --samples 3 --output experiments/bqn/optimization-v1/full-replay
```

Use a fresh output directory. The full input is the suite's retained FASTA
N=25,000,000 input; its exact 254,166,745-byte SHA-256 is recorded in every full
report. Do not run other benchmarks, compilers or browsers during measurements.
The run controller needs Python 3.11+ for its hashing API. The witness README
explains tracing and validation; instrumented elapsed times are diagnostics.
Canonical admission additionally requires the fail-closed publication importer.
