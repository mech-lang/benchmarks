# Independent six-process reconciliation

[`apl_workspace_reconcile.py`](../../../../../tools/qualification/apl_workspace_reconcile.py)
validates the future full-size binary-trees cohort without importing its timing
producer or sampler. Its 14 synthetic test methods passed on 2026-10-15 UTC,
recorded in [the initial pure-validation record](../../../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). Actual file replay
and full-size measurements remain pending.

The accepted cohort has three fresh GNU APL processes and three fresh matched
Mech controls, in the reviewed alternating order. Both public APL source labels
refer to the same authored implementation and the same three observations. The
optimized label adds no native process or optimization claim. The complete
counted bundle is the unchanged 40-unit tree source plus the one-unit workspace
setup, for 41 canonical and physical units.

Every successful observation must retain the complete N=21 output byte count and
digest, exact validation receipt, process identities, cleanup evidence, original
source/runtime fingerprint and the exact APL shutdown diagnostic. Unknown or
missing diagnostics reject admission. The elapsed time includes interpreter
startup, parsing, workspace setup, construction, traversal, output and shutdown.
The frozen sampler discarded complete stdout after validation; reconciliation
does not claim to reconstruct that byte stream. RSS describes sampled process
groups and does not establish an unsampled maximum.

## Explicit evidence and held review

The caller supplies independently reviewed SHA256 identities for the actual
plan, report, terminal, durable terminal, producer source and this consumer.
No successful native evidence or future digest is embedded in this draft.
The durable job must be
`experiments/shared/owned-jobs-v1/owned-jobs/apl-binarytrees-full6-v1` and must
execute the retained Python with `-I -S -B`, followed by the original producer's
`run --plan … --plan-sha256 …` arguments. The target command has no `-u` option.

The `review_context(plan_ref, report_ref, terminal_ref, producer_sha,
durable_ref, consumer_sha, *, on_exit_failure=None,
final_consumer_check=None)` API yields `(review, files)`. References contain
absolute original paths and SHA256 digests. It holds the existing common mutex,
all four prior APL durable leases and the new full6 durable lease. The complete
original input pins, recorded named-path resolutions, absent loader/preference
paths and closed artifact inventories are checked before and after the consumer.
The original failed workspace observations remain bound as failed evidence.

The deterministic review contains:

- `references`: the plan, report, terminal and durable-terminal identities.
- `profiles`: the two real measured profiles, original metadata, three samples,
  independently calculated statistics and per-sample raw/supervisor/outer links.
- `source_aliases`: the optimized source/timing alias with zero additional samples.
- `source_counts` and `source_work`: exact prerequisite review references, plus
  their verified records and the replayed complete source-owner projection.
- `verified_file_pins`, retained failure links and the held lease names.

There is no verification timestamp. Repeating the same review produces the same
content. A consumer may add exact supplementary input pins through
`files.verify(path, sha256)`. Final consumer checks follow input replay while the
leases remain held. The restoration callback runs on either a consumer-body
failure or final-check failure; original and restoration errors are preserved.

## Command-line result

After a complete, closed cohort and source review, invoke the consumer using the
retained Python with `-I -S -B` and these explicit arguments:

```text
tools/qualification/apl_workspace_reconcile.py
  --plan PLAN --plan-sha256 PLAN_SHA256
  --report REPORT --report-sha256 REPORT_SHA256
  --terminal TERMINAL --terminal-sha256 TERMINAL_SHA256
  --durable-terminal DURABLE_TERMINAL --durable-terminal-sha256 DURABLE_SHA256
  --producer-sha256 REVIEWED_PRODUCER_SHA256
  --tool-sha256 REVIEWED_CONSUMER_SHA256
  --output experiments/apl/binarytrees-workspace-v1/full6-v1/reconciliation/actual-v1.json
```

The output must be fresh. Success is printed only after final input, output and
lease closure. A late failure removes only an output still owned by this
invocation; externally modified files are preserved and reported.

Reconciliation does not publish a catalog. Runtime-publication metadata review,
candidate export, the separate publication-root transaction and independent
9-to-10 workload history verification remain separate steps. The nine admitted
APL workloads, matched control catalog rows and prior failures are not changed.
New source-size or timing baselines require a separate reviewed normalization;
this packet does not authorize a baseline change.
