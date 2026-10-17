# Reproducing recorded measurements

The explorer's **Data** tab lists every distinct recorded run. **Versions**,
**Input**, **Platform**, **Recorded**, **Original source** and **Reproduce** are
sortable and searchable. Open Reproduce for the recorded build stages, timed
argument vector, working directory, environment, compiler/runtime evidence,
dependency pins, input records, executable hash and output checks.

Export all rows, filtered rows or checked rows as JSON or CSV. Both contain the
structured reproduction record, original-source citations and source hashes.
JSON also contains every counted application source and helper in the selection.
The source bundle includes the measured adaptations; downloading only the
upstream submission may produce a different program.

The chart's initial dataset contains only compact version and coverage summaries.
Full reproduction records load once when opening Data or a source inspector;
exports wait for those source-bound records. This avoids adding the full build
and dependency inventory to ordinary chart loading.

To repeat a profile:

1. Export its rows and save its counted source files. Verify each file's SHA-256.
2. Install the recorded compiler, runtime, SDK and libraries on the matching
   platform. Read each version's evidence scope: a prior build report is distinct
   from a version captured in the timing cohort. Development commits and binary
   hashes identify snapshots where numbered releases were not recorded.
3. Relocate the recorded paths and reproduce every build stage and flag outside
   the timed interval. Preserve floating-point settings, worker limits, heap/GC
   settings, helpers and linkage. Do not substitute the upstream Linux build
   flags for the locally recorded build.
4. Prepare the full input outside timing. For stdin workloads, preserve the
   recorded FASTA generator size and verify the input byte count and hash. The
   input must be read within the measured process. Verify complete output against
   the retained checks before accepting a source.
5. Follow the cohort's warmup, order, environment, power and timing policy. Run
   profiles sequentially with no competing benchmark or compilation. Each sample
   is a fresh process, timed through exit, with startup, runtime compilation,
   input, complete output and shutdown included. Offline builds and post-exit
   validation are excluded. Use the recorded sample count and repeat full output
   validation for every sample.
6. Store new observations with their actual versions, environment, inputs,
   commands and source hashes. Recompute the median and sample standard deviation;
   preserve the historical observations as a separate cohort.

**Recorded recipe** means the indexed fields were recovered, not that the recipe
was replayed successfully on a clean machine. **Gaps** lists missing historical
information. An unrecorded compiler release, OS version, dependency or complete
build cannot be recreated by substituting the current installation and claiming
an exact historical reproduction. The original reports remain linked for further
recovery. No benchmark executions are performed when building this index.

`python3 tools/build_reproducibility.py` regenerates
`data/reproducibility.json`; `--check` detects stale records. Extraction matches
measurement rows by implementation identity and exact sample arrays. Build
receipts for Julia applications and optimized Lean programs are matched by
executable hash. `python3 tools/test_reproducibility.py` verifies those boundaries.
