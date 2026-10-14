# Remaining small binary-tree cases

This additive controller schedules only the original complete-subject N=4 and
N=10 cases. The subject, workspace setup, runtime, launcher, expected output,
environment, process ownership and limits are unchanged. The N=4 case retains
the subject's minimum-depth behavior. No full-size timing or chart admission is
performed.

Preparation requires the saved configuration/readback, the preserved failed
allocation witness, and both actual scope-isolated captures. The latter must pass
their original exact output contracts and retain the independent
[bounded ownership disposition](../scope-isolated-v1/actual-ownership-review-v1.json).
The disposition qualifies the tiny diagnostic only. It does not promote source
counts, the complete scored workload, full timings or memory observations. Both
older producer failures remain unchanged and unqualified.

The controller independently joins the actual two captures, complete raw
artifacts, report, terminal, serial process ledger and physical closure. It holds
the original timing mutex plus all three retained durable leases during
preparation and execution. Native monitoring checks those identities through
the frozen observer. The new run's final report, complete capture snapshots,
prerequisite pins and all retained artifact inventories are checked before its
terminal is written.

N=4 retains a 30-second timeout; N=10 retains 60 seconds. Each command has the
existing 10 GiB sampled-RSS guard, 1 MiB per stream and five-second cleanup period.
The exact known inherited-FD shutdown diagnostic is required. Changed stdout,
additional stderr, a timeout, ownership failure or cleanup failure stops the
stage. No retry occurs. Sampled RSS does not prove an unseen peak bound.

The source has not been prepared or executed. After source review and serial
lane release, prepare with:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/apl_workspace_subject.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/whole-subject-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/whole-subject-v1/run-v1
```

Review the resulting exact plan digest before using a fresh durable job with the
same controller's `run --plan <path> --plan-sha256 <reviewed-sha>` command. Capture
success alone keeps every qualification flag false pending independent actual
review. Full-size timing needs a separate decision and run.

The pure fault suite is
`tools/qualification/test_apl_workspace_subject.py`. It covers both retained
diagnostic prerequisites, the independent bounded disposition, exact N4/N10
schedule and oracles, first-failure stopping, final artifact/report mutation and
retained-lease replacement. It uses small saved records and temporary synthetic
receipts; it launches no native subject and replays no full runtime closure.
