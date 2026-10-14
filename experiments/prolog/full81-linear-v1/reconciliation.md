# Independent continuation reconciliation

[`prolog_linear_reconcile.py`](../../../tools/qualification/prolog_linear_reconcile.py)
reviews the closed 81-process continuation together with the nine qualified
regex-redux samples preserved from the cancelled original study. It does not
execute a runtime, compile a program, acquire a timing sample, or modify native
receipts. The current script is prepared for the eventual closed cohort; its
existence does not establish a successful reconciliation.

The exact prepared plan and the original cancellation evidence are fixed inputs.
The schedule contains 90 sample slots: nine retained regex samples and 81 new
slots. Only the two reverse-complement source profiles change. Both use the same
qualified linear implementation and QLF artifact; the optimized label is an
explicit source alias, not a separate optimization claim. All other source
profiles, inputs, sample rotations, runtime settings and matched Mech controls
retain the original plan's contracts.

The reviewer independently replays the raw sample, owned sampler and outer
supervisor records. It checks sample ordering, exact process identities and
commands, normal cleanup, output fingerprints, environment qualification,
three-sample statistics, failures and the permitted subsequent skips. Attempt
numbers remain local to their original or continuation directory. Original
attempt 10 remains cancelled and excluded; it supplies no timing or timeout
result. The 27 preserved regex receipt digests must match the cancellation seal.

File-mode review requires the continuation's durable owner lease, the original
durable lease, the Prolog study lease and the unchanged common mutex. It verifies
the complete plan and terminal artifact closures, rejects additional or missing
files, binds every validated receipt to the terminal inventory, and rechecks
file and lease identities before returning. No runtime or full-closure hashing
occurs when importing the script or running its pure tests. File-mode review is
reserved for after the native cohort and durable worker close.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/prolog_linear_reconcile.py --output /private/tmp/mech-benchmark-completion/experiments/prolog/full81-linear-v1/reconciliation-v1.json
```

The output must be new and outside `run-v1`. A failed review retains an additive
failure receipt. A successful review qualifies the recorded sample evidence and
file closure only: runtime publication metadata, full timing admission and chart
admission remain false pending their separate reviews and explicit import.

[`test_prolog_linear_reconcile.py`](../../../tools/qualification/test_prolog_linear_reconcile.py)
uses the actual prepared plan and preserved regex receipts, plus clearly
synthetic continuation receipts. Its twelve cases cover closure, schedule,
failure, alias, digest, environment, command and admission mutations. Passing
these tests is not evidence that the new native cohort has completed.
