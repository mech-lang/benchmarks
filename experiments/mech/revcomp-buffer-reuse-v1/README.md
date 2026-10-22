# Reuse completed streamed-record storage

This study extends [direct record compaction](../revcomp-streaming-v1/README.md)
with generic runtime allocation reuse. After a mapped result has been written,
only uniquely owned byte storage is reclaimed. The streaming reader retains at
most one largest allocation, clears its logical length and grows it normally for
later records. Live aliases and captures remain untouched; bytes still needed by
a later consumer are never mutated. Stored-record cursors do not retain spares.

The application and emitted Cranelift compute object stay byte-identical. No
FASTA alphabet, record length, input file size or expected result is encoded in
the new code. No benchmark operation moves out of the application. The existing
in-place reverse/translation and lazy wrapping behavior remain intact.

[Results](RESULTS.md) report another 5.0% reduction from compaction alone, 14.3%
from the original parent within this cohort, and roughly half the peak RSS.
Rust remains faster. This packet does not replace canonical website timings.

## Identity and validation

- Base runtime: `6634f1f4d59c0a2eebee44065f236f8647703464`.
- Candidate: `fca1ba1f7462a555eb56833ad32135408a140a72` in
  [compiler PR #910](https://github.com/mech-lang/mech/pull/910).
- Frozen emitter CLI remains `6de19875e2266f39c93712800c400672a44b98c9`;
  generated AOT applications link the current runtime source at build time.
- [compiler.json](compiler.json) and `build-v1/` pin exact source, runtime,
  environment, commands, native object and executable identities. Inherited
  Rust/toolchain identities remain in the sealed prior study. The published Rust
  application is not edited.
- Ten release runtime tests pass. New tests check actual pointer reuse, cleared
  input contents, live aliases, shared formatting views, nested results and the
  largest-buffer retention policy. The existing 2,736 differential parser cases
  now return completed storage between records, covering prefixes, separators,
  CRLF, EOF and buffer boundaries. Read interruption/error tests remain intact.
- All 61 old/new bounded behaviors match exactly, including stdout, stderr and
  exit status. Eleven existing differences from the broader shared FASTA oracle
  remain explicit. These are not successful general FASTA conformance checks.
- All five execution variants pass the official N=1000 output. All 35 complete
  full-size outputs match the reference.

Recycling a result after `write_all` returns is safe because the writer no longer
borrows its input. Reclamation additionally requires `Arc::try_unwrap` on both
formatting views and byte storage. A shared reference is dropped without taking
or modifying its allocation. At most one completed vector is retained per
streaming reader; this can keep a formerly large capacity alive through later
small records until the stream closes. It is not a universal memory-policy claim.

## Reproduction and evidence

`prepare.py` serially runs relevant release tests and builds the candidate under
the common mutex. `qualify.py` compares the exact frozen previous binary and new
binary over the retained corpus. `run.py` preselects five execution variants for
seven shuffled serial rounds: original Mech at four partitions, compacted Mech at
four, reused Mech at four/eight, and unchanged Rust at eight workers. Fresh-process
timing includes startup, input, native work, all output, flush and shutdown;
compilation and output validation are excluded. The same trusted legacy I/O path
is used; secured capability activation is not newly measured.

The FASTA N=25,000,000 input is 254,166,745 bytes. Complete outputs are written,
then hashed after owned-process closure, then removed with size/hash receipts.
Bounded outputs, all raw samples, binary/environment/input pins, process receipts
and power/memory snapshots are retained. Independent processes are never timed
simultaneously. No phase-instrumentation flag is enabled in the quantitative run.
The [phase diagnostics](../revcomp-phases-v1/README.md) remain a separate packet.

After timing, the test-only collector was extended to return completed storage
in every differential case. `refine_tests.py` reran all ten tests successfully,
but its rebuild was refused because the retained generated-project directory
already existed. That closed non-benchmark failure remains recorded in
`test-refinement-v1/`. `rebuild_refined.py` preserved the old project under a new
name and successfully rebuilt at the identical output path. The new executable
is byte-for-byte identical to the timed binary; no repeat timing is needed.
Both runtime snapshots, patches, attempts and proof are retained.

`python3 experiments/mech/revcomp-buffer-reuse-v1/verify.py` replays the retained
source, output, test, statistics and closure evidence without running benchmarks.
It checks complete-output hash receipts for omitted full stdout; it does not
reconstruct deleted bytes. Reproduction requires restoring dependencies/input
caches and adapting the absolute checkout paths recorded in the controllers.
`seal.json` binds all retained artifacts. Historical sources and results remain
unchanged; application source size is unchanged (seven physical rows), with no
new normalized or canonical formatted LOC claim.
