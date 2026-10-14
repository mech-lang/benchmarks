# Two-command allocation diagnostic controller

`tools/qualification/apl_workspace_scoped.py` schedules exactly the
zero-allocation control followed by the scope-isolated allocation witness. Both
use the retained GNU APL launcher/runtime, the original workspace setup and the
reviewed diagnostic sources. The first mismatch stops the stage; no command is
retried. N=4, N=10, full-size timing, source counts and chart import are outside
this controller's scope.

The controller privately loads the frozen remaining-three controller and native
observer. The high-descriptor timing mutex, direct process-group observations,
raw stream retention, child reaping and empty-group checks remain in that frozen
observer. The common mutex and both retained durable leases are checked during
native monitoring and again around final prerequisite/artifact closure.

Preparation independently checks the saved configuration and readback through
the existing exact-byte disposition. Their original producer failure remains
recorded. The later allocation mismatch is also retained explicitly as a failed,
unqualified observation, with its exact report, terminal, raw output and closure.
Neither saved attempt is relabeled or rerun. Missing or altered old artifacts,
unknown output, extra stderr or a changed lease rejects the new stage.

Each new command has a 30-second timeout, a 10 GiB sampled-RSS guard, a 1 MiB
limit per output stream, and five seconds for cleanup. There is no sampler child,
no standard-input payload and no retry. Sampled RSS does not establish an unseen
peak bound. The exact 54-byte inherited-FD shutdown diagnostic is required;
additional or missing stderr fails. Both source-derived stdout contracts are
fixed in the controller, independently of the prepared plan.

The result ledger binds each complete raw capture. Finalization checks the exact
serialized report, immutable completed capture snapshots, all input pins, both
old artifact inventories and all named leases before writing its terminal.
Success means only that two bounded captures are ready for independent review.
Every source-work, count, native-syntax, allocation-ownership, full-timing and
chart-admission flag remains false even after capture success.

Source and fault-test preparation is separate from native preparation. There is
no plan or native run for this controller yet. After the serial lane is released
and source review passes, the metadata preparation command is:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/apl_workspace_scoped.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/scope-isolated-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/scope-isolated-v1/run-v1
```

The concrete plan must then be reviewed. Run only through the existing durable
launcher with a fresh owned job and the same controller's
`run --plan <path> --plan-sha256 <reviewed-sha>` command. Later N=4/N=10 checks may
be considered only after both actual diagnostic outputs pass and their closed
evidence is reviewed; this controller does not launch them.

The pure fault suite uses temporary synthetic receipts and small saved records.
It checks command order, independent oracles, preserved failed status, first-fault
stopping, exact two-capture closure, late mutation and retained-lease replacement.
It performs no native launch or runtime closure replay. While another timing
cohort runs, its execution remains deferred:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/test_apl_workspace_scoped.py
```
