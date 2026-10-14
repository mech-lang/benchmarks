# Historical evidence

This archive contains benchmark source snapshots, measurements, validation reports, and experimental studies. Current sources and results are indexed in [`programs/`](../programs/) and [`results/current/`](../results/current/).

| Directory | Evidence |
| --- | --- |
| `workloads/` | Original single-workload studies |
| `languages/` | Language-specific ports, runtime qualification, LOC audits and timings |
| `comparisons/` | Studies that compared several languages together |
| `compiler/` | Mech native/interpreter and optimization experiments |
| `validation/` | Required-work, source-count and conformance audits |
| `qualification/` | Historical execution/review receipts, grouped by language or topic |
| `site/` | Original explorer source, exports and publication evidence |
| `studies/` | NumPy/EKF study |
| `earlier-studies/` | Earlier retained compute experiments |
| `legacy-tools/` | Original scripts, indexes and optimization studies |

Measurement records retain original relative and host paths. The [path map](../migration/reorganization-paths.tsv) resolves historical file locations. Resolve an old reference with `python3 tools/resolve_archive.py <old-path>` from the repository root. Files recovered from the retained V worktree have a separate [source/hash map](../migration/recovered-v-sources.json).

Do not execute historical workers assuming they are portable. Their recorded commands may depend on ignored toolchains, executables and absolute paths on the original host. New studies should use a workload/language/date structure and preserve exact source, compiler, arguments, output checks and raw samples. Current navigation does not depend on historical job names.
