# Explicit linker-option continuation

The [first fixed19 attempt](../combined-intake-v1/FAILED-RUN.md) stopped during
diagnostic compilation: Clang 22 rejected `-fuse-ld=<absolute path>` under
`-Werror`. It created no compiler outputs and started no Rebol fixture process.
The failed plan, compiler streams, producer records and durable job are retained.

The [additive entrypoint](../../../../tools/qualification/rebol_primitive_fixtures_linker.py)
wraps the frozen combined intake. Its only command change replaces that exact
token with `--ld-path=<the same approved linker>`, the spelling already used by
the successful extension compilation. Compiler selection, warning policy,
official diagnostic header, C source, dependency capture and resource limits
remain unchanged. All eighteen fixture commands and the original observer,
capture checks, runner and finalizer are reused.

`load_controller(adapter_sha256)` returns the adapted original controller.
`intake_adapter` preserves the combined-adapter identity; `linker_adapter` and
`entrypoint` record the new invocation. `extension_inputs` continues to describe
the three extension jobs. `validate_prior_failure` separately returns the failed
fixed19 evidence and output closure, recorded as `prior_fixed19_failure`. Its
durable lease is the ninth inherited lease; it is never presented as a fourth
extension job. Downstream consumers must retain that separate closure and job.

Three focused synthetic methods check the complete nineteen-slot invocation
delta, rejection of ambiguous linker options, original runtime machinery and
preservation of the failed stage's status and inventories. Test results and any
prepared plan are recorded separately. No primitive or benchmark qualification
is inferred from this corrected invocation; native execution requires a fresh
plan and an explicit serial launch.
