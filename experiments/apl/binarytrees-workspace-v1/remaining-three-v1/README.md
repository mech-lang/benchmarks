# Remaining bounded workspace checks

This continuation preserves the original five-command attempt and schedules only
its three unstarted commands: allocation ownership, complete binary trees at N=4,
and complete binary trees at N=10. The original configuration observation reports
Value/Cell/header sizes of 464/24/176 bytes. The original readback reports workspace
scale 90 followed by 200. Its producer status remains `failed`: the original
empty-stderr contract rejected the shutdown diagnostic.

[The diagnostic disposition](shutdown-diagnostic-review-v1.json) binds that exact
54-byte stderr, the complete readback stdout, the closed native receipts, and the
retained GNU APL source explanation. The launcher inherits FD3 as application
output. GNU APL registers it as `pipe-to_client` at startup; opening `/dev/fd/3`
creates a separate handle. The readback closes that separate handle correctly.
Normal OFF cleanup closes the original FD3 and emits the recorded diagnostic.
The configuration command exits directly and does not use normal OFF cleanup.

The new contract requires the exact diagnostic, exact application stdout, exit
zero and the original process-ownership checks. It retains every output byte.
An extra warning, application error, missing diagnostic, changed stdout, timeout,
cleanup problem or ownership mismatch fails the continuation. No stderr is
stripped. The old report, terminal, source files and runtime remain unchanged.

The controller privately reuses the frozen observer, high-descriptor timing
mutex and limits: one native group, 30/30/60 seconds, 10 GiB RSS guard, 1 MiB per
stream, five seconds for cleanup, no retries. The original durable lease is held
through preparation and execution. Original prerequisite and artifact identities
are checked again, including the failed result and its raw diagnostics. Sampled
RSS remains an incomplete observation and does not prove an unseen peak bound.

No continuation plan, native output or admission exists yet. Preparation must
wait for the shared lane, and the concrete plan must be reviewed before running:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/apl_workspace_remaining.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/remaining-three-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/apl/binarytrees-workspace-v1/remaining-three-v1/run-v1
```

Run the same controller with `run --plan <prepared-path> --plan-sha256 <reviewed-sha>`
through the existing durable owner using a fresh job directory. All source-work,
source-count, full-timing and chart-admission flags remain false. The setup file
still requires an admitted source count, and bounded results do not establish
full-size feasibility or a performance result.
