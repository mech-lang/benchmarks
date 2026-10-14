# Elixir bounded workload checks

The plan runs 156 serial correctness checks across twenty retained source forms
and ten workloads. The compact and optimized forms use ten distinct main-source
bodies; these aliases do not claim separate optimizations. Each form keeps its
authored main, support module, and launcher.

The 78 distinct reference cases come from the closed Prolog preparation corpus.
Their saved inputs, expected outputs, actual reference outputs, and validation
receipts are hash-bound. No reference generator or application compiler runs.
Output must match completely; N-body instead requires exactly two finite energy
lines within the retained 1e-8 tolerance.

Before invoking each unchanged main, the observer checks the retained BEAM
hashes, source/debug bindings, BEAM JIT runtime, scheduler count, and inherited
common mutex. The supervisor retains raw output and native ownership receipts,
enforces a 60-second deadline and 2 GiB process-group limit, and keeps the group
leader unreaped until owned descendants have terminated. Cleanup has a separate
five-second bound. A failed case stops the batch and retains its partial output.

`plan.json` freezes the exact sources, runtimes, reference cases, and controller.
The durable launcher is byte-identical to the previously used job owner and
stores its records under `owned-jobs/`. An existing result directory is never
reused automatically.

These checks do not provide full-workload timing samples or chart admission.
Compiled required-work witnesses, source-count qualification, and full sequential
measurements remain separate stages. `source-review.json` lists the outstanding
workload-specific evidence. `preflight-v1/` retains an earlier metadata-reader
failure before any native dispatch.

`results-v1/report.json` records all 156 cases passing in 156 native runtime
processes, with no subject recompilation or benchmark timing samples. The final
input and artifact integrity checks passed, and the durable owner recorded exit
zero. Raw per-case output and runtime observations remain alongside the report.
