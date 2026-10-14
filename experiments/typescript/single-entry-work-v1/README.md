# TypeScript tree and pi execution evidence

This stage captures the unchanged emitted binary-trees and pi-digits programs
once each at the prescribed inputs, 21 and 10000. The
[static review](../required-work-v1/static-review-v1.json) records 27 passing
source/emission contracts across all ten applications. The closed 149-case
correctness and native AST/compiler packets are prerequisites; this stage does
not repeat either. No timing is admitted from diagnostic processes.

[typescript_single_entry.py](../../../tools/qualification/typescript_single_entry.py)
first retains the exact Node executable's `--v8-options` listing, then directly
starts the two existing JavaScript mains. There is no wrapper, preload, source
edit, forced optimization, altered heap size or altered collector/tiering policy.
The typed tree is sequential; its only import is `node:process`.

The [native API review](native-api-review.json) cites the Node 24.19.0 release
source at a fixed commit. Each subject retains V8 code/function events, optimized
and Maglev instructions, source positions, safepoint/deoptimization metadata,
OSR/optimization/deoptimization traces and GC lines. Only pi requests the
`BigIntDivide*` builtin disassembly. The bytecode filter selects the single cold
outer function (`mainThread` or `calculatePi`). All per-isolate logs retain V8's
default process/isolate names within the fresh owned working directory.

Unfiltered `log-code-disassemble` would also dump runtime builtins and is not
used. `print-code` is also excluded: Sparkplug's implementation prints outside
CodeTracer. Baseline identities remain in the event log; any baseline execution
must be reviewed against the original bytecode and the retained V8 execution
path. Diagnostic presence alone does not prove that an optimized version was
entered. The capture must support the actual invocation and its tier transitions.

Raw stdout is preserved. V8's explicitly recognized GC envelopes are retained
in `gc.bin`; the one generated-bytecode prefix is retained in `bytecode.bin`.
The remaining output must be the complete 455-byte tree or 16893-byte pi oracle,
which is also retained in `subject.bin`. No unknown warning is stripped. Native
stderr must be empty. Code/event files and all process receipts are included in
the final closed artifact inventory.

## Ownership and resource limits

The immutable Kotlin v2 observer supplies atomic native registration, birth
identity checks, inherited common-lock ownership, pipe/file retention and
bounded group cleanup. It is loaded into a separate namespace so existing
30-second/2GiB/8MiB bounded receipts retain their original interpretation.
This diagnostic policy permits 180 seconds per process, 5 seconds for cleanup,
10 GiB process-group RSS and 128 MiB per native file/pipe, with a 768 MiB stage artifact
ceiling. The 10 GiB monitoring ceiling matches the retained full-size diagnostic
policy; it does not raise Node's heap limit. The larger file ceiling accommodates
generated-code text while avoiding a full builtin-disassembly dump. It is a
conservative capture bound, not a previously measured trace-size claim.

Preparation and execution hold the established common mutex continuously and
verify its inode 79859134. Preparation checks the exact compiled/source/runtime
pins and prior closed receipts. Execution rebuilds the plan from those frozen
inputs, uses fresh directories, performs no retry, retains unsuccessful attempts,
and closes only after all registered children have been reaped. A stopped,
truncated, unsupported or semantically inconclusive capture remains unqualified.

```text
<retained-python> -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/typescript_single_entry.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/typescript/single-entry-work-v1/plan-v1.json --output /private/tmp/mech-benchmark-completion/experiments/typescript/single-entry-work-v1/run-v1
<retained-python> -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/typescript_single_entry.py run --plan /private/tmp/mech-benchmark-completion/experiments/typescript/single-entry-work-v1/plan-v1.json --plan-sha256 <reviewed-prepared-plan-sha256>
```

The retained Python path is
`/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`.
The existing shared durable launcher may own the second command, without `-u`;
the target controller owns the common mutex. The three processes are one option
listing and two application mains, with no compiler invocation or benchmark
sample. Actual required-work, loaded-runtime and chart admission remain false
until separate review of the saved evidence.
