# Independent full-workload reconciliation

`tools/qualification/prolog_reconcile.py` reviews the completed original22 Prolog
study without executing the benchmark, importing its sampler, or changing its
retained evidence. The prepared plan is fixed at SHA-256
`55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a`.

The review checks all 90 rotated schedule slots, the exact source and executable
fingerprints, complete-output validation receipts, power and resource records,
native process ownership, cleanup, nonoverlapping measurement intervals, and
three-sample medians and sample standard deviations. Ratios use the matching
Mech control from the same workload. An isolated workload failure retains its
completed observations, explains skipped later slots, and receives no median or
ratio. A failed control also prevents ratios for its workload.

The durable worker, controller, sampler, and native process records are linked
by their retained identities. A kernel identity that was unavailable is reported
as an observation gap, never reconstructed. Successful native registration and
owned-child reaping remain required. The sampler's pre-`setsid` group identity
can legitimately differ from its later process group.

File review acquires the existing durable-worker lease, Prolog cohort lease, and
common timing mutex without waiting. It therefore refuses an active cohort,
including gaps between samples. Only then does it hash the full input closure,
bind the terminal/report and all attempt artifacts, and recheck file contents
and directory inventory. The only accepted completed output files are the report,
terminal, and each registered attempt's raw, supervisor, and outer-supervisor
receipts. The independent review must be saved outside that closed directory.

Run after the durable job is terminal, from the repository root:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/prolog_reconcile.py \
  --plan experiments/prolog/full90-v1/plan.json \
  --plan-sha256 55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a \
  --durable-directory experiments/prolog/full90-v1/owned-jobs/full90 \
  --output experiments/prolog/reconciliation-v1/review.json
```

The checker reuses hash-bound, independently authored JSON, fingerprint,
statistics, and durable-job validation primitives from `pony_reconcile.py`.
It imports no measurement controller or runtime. The two `test_prolog_reconcile*`
files exercise synthetic success, isolated failure, and corrupted-evidence cases;
they do not constitute a completed native study or file-integrity review.

Successful stdout was checked and discarded by the frozen sampler. Retained
byte counts, hashes, and validator receipts establish its output evidence;
complete stdout is not recoverable here. N-body's two finite energies are checked
again against the frozen tolerance. RSS is an observed process-group peak, not
an unsampled maximum. Source-work and LOC semantics, runtime publication
metadata, catalog integration, and website validation remain separate gates.
Reconciliation always leaves chart admission and runtime qualification false.
