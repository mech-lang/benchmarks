# Janet reverse-complement study

This packet compares the historical `source-v3/revcomp.janet` with two local
Janet derivatives. The historical parent reads the complete input and splits it
into lines; it does not satisfy the workload's explicit line-by-line input
requirement. It remains a performance reference, not an eligible final program.
Both candidates use the runtime's standard `file/lines`, grow a record buffer,
and reverse/complement every base in Janet. No file-size preallocation, custom
native helper, generated lookup result, periodic input shortcut or changed
runtime is used. A single exceptionally long LF-delimited line still requires
memory proportional to that line; complete records must be retained for reversal.

- `line-reader` changes input organization while preserving table lookup,
  uppercase normalization, reverse indexing and one output call per 60-base row.
- `block-rows` moves row-completion bookkeeping outside the per-byte loop; it
  has a separate follow-up cohort and does not demonstrate a useful speed gain.
- `dense-chunk` also uses a 256-byte complement table for upper/lowercase input,
  a descending offset and approximately 1 MiB output chunks containing complete
  60-base rows. Unknown bytes still fail in reverse traversal order, with the
  normalized byte and zero-based record position. Completed rows are flushed
  before an error; a partial row is not emitted, preserving the established
  partial-output contract.

The local parent/manifest identify Codex GPT-6 family authoring and the original
consulted source lineage. Exact serving model is unknown. All application helpers,
lookup initialization, input, error handling and output code count as source.
The standard Janet runtime is unchanged and external to application size.

## Validation and reproducibility

`qualify.py` runs the retained 61-case corpus plus seven additional cases per
source. Added cases cross one and two chunk flush boundaries, row tails, a
lowercase invalid character, an error before the next record, and an error after
one chunk was emitted. `common.py` provides an independent complete-byte oracle.
The initial three-source cohort has 204 application output/rejection checks and
174 separately instrumented success checks. The row-loop follow-up adds 68 and 58,
respectively, for totals of 272 and 232. Each witness reports the actual visited base count per record;
it does not replace full byte comparison or imply arbitrary-input correctness.
`qualification-v3` contains the final captures. Earlier attempts remain:

- `qualification-v1`: the witness accidentally included a second newline because
  `eprintf` supplies one; application output was correct.
- `qualification-v2`: the dense table's initial draft used `each` instead of
  `eachp` for key/value iteration and failed during loading. The failed draft is
  retained separately; it has no accepted timing or source-count status.

`reference.py` independently produces the complete full-size expected output
before timing. `reference-v1` records the command, input/output hashes and closed
owned process. Its moved payload is an ignored build artifact. The bounded oracle
handles CR/LF/comment/malformed variations; the full reference consumes the pinned
LF-delimited generated input and has no claim to arbitrary newline normalization.

`full.py` uses the unchanged owned-process implementation from the k-nucleotide
study, including independent exit observation and macOS `wait4` peak RSS. It holds
the shared timing mutex across every sequential, shuffled three-round cohort.
Startup, source compilation, VM work, all I/O and shutdown are included. Output
hashing, telemetry and cleanup happen outside the elapsed interval. The final
full capture directory is `run-v2`; `run-v1` contains only a sandbox-denied process
snapshot before any quantitative subject started. No runtime or power setting
was changed to bypass this restriction.

Full-size stdout is hashed after owned closure and then omitted, retaining its
complete size/hash receipt. Bounded stdout/stderr remain complete. The Mech AOT
reference is the retained same-input full-process median, not a freshly paired
control. Observed power settings and process snapshots do not prove continuous
frequency, temperature or a perfectly idle host. These exploratory results do
not change the public chart.

Reproduce in a clean output directory with the pinned runtime/input present:

```sh
python3 experiments/janet/revcomp-stream-v1/qualify.py
python3 experiments/janet/revcomp-stream-v1/prepare_full.py
python3 experiments/janet/revcomp-stream-v1/full.py
python3 experiments/janet/revcomp-stream-v1/qualify_block.py
python3 experiments/janet/revcomp-stream-v1/block_full.py
experiments/source-metrics/.build/venv39/bin/python experiments/janet/revcomp-stream-v1/measure.py --run
python3 experiments/janet/revcomp-stream-v1/verify.py
```

The [results](RESULTS.md) retain all measured tradeoffs.

The native lexical measure, physical rows, UTF-8 bytes, pinned BPE and deterministic
gzip are separate measures. Normalized logical and canonical formatted LOC remain
unqualified. No candidate is certified globally optimal.

Workload: https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/revcomp.html
Janet pair iteration: https://www.janet-lang.org/docs/loop.html
