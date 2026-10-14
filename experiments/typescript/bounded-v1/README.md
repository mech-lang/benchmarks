# TypeScript bounded output qualification

The [controller](../../../tools/qualification/typescript_bounded.py) prepares
149 serial fresh Node processes from the ten JavaScript files emitted by the
closed [strict compile/AST stage](../native-stage-v1/independent-native-review-v1.json).
This controller has not executed any application. Its exact compiled report,
terminal, prepared plan and independent artifact review are pinned; the source
TypeScript, staged source, emitted JavaScript, source maps, compiler packages,
Node executable and native compile/reader receipts remain bound throughout.
There is no recompilation, transpile-only fallback or JavaScript benchmark reuse.

The [shared corpus](../../shared/bounded-corpus-v1/README.md) supplies 149 cases:
142 complete successful outputs and seven invalid-IUPAC rejections. Every input,
argument and expected output is retained. The frozen
[checker](../../../tools/qualification/scala_typescript_outputs.py) requires
complete byte equality except N-body's two finite nine-decimal energy lines,
compared within ten integer nanounits. The seven reverse-complement rejections
must exit normally with code 1, output exactly `>r\n`, and emit exactly
`Invalid IUPAC byte: <expected-byte>\n` on stderr. An unrelated error, timeout,
signal or cleanup problem cannot satisfy a rejection.

Each command invokes the pinned Node executable directly on the retained
emitted `.js` path, with the original numeric argument for numeric cases and
complete pipe input for stream cases. Node uses its default VM flags, a fresh
home and temporary directory, and an explicit environment with
`UV_THREADPOOL_SIZE=8`; no ambient `NODE_OPTIONS`, `NODE_PATH`, preload or
module wrapper is inherited. The authored programs use one computation thread.
Their emitted imports name only `node:` standard modules. The compiled local
`package.json` selecting CommonJS is also pinned. This stage does not assert a
complete runtime image closure or a full-input memory/performance policy.

The frozen observer enforces a 30-second process deadline, five-second cleanup,
2 GiB observed process-group RSS, and an 8 MiB native-file bound. Commands remain
serial under common mutex inode 79859134. Expected exit-1 observer failures are
retained verbatim and replayed against the strict output and lifecycle contract.
Signals enter owned-group cleanup; no automatic retry or resume is supported.
Finalization checks registered processes, reaping and empty groups, exact
accepted artifact snapshots, all source/runtime/oracle pins, the compiled
artifact closure and the held mutex before writing the terminal receipt.

Use the retained Python executable with `-I -S -B` (optional `-u` is harmless),
physical absolute paths and a fresh plan outside the fresh output directory:

```text
typescript_bounded.py prepare --compiled-report <native-stage-v1/run-v1/report.json> --compiled-report-sha256 ec6fb9979e5de31cd8496f01e338fef80f322f118def9923d61b8c3b5ca9e83b --compiled-terminal-sha256 2abf7814b6063b15561af165bed377d77f6616597d555ec7f4d967c421372038 --plan <bounded-v1/plan-v1.json> --output <bounded-v1/run-v1>
typescript_bounded.py run --plan <reviewed-plan.json> --plan-sha256 <reviewed-sha256>
```

Preparation and execution both acquire the common mutex and verify the exact
Python identity. The shared durable launcher may own the controller; the
controller itself owns the timing mutex. After a successful closed run,
bounded output correctness is the only admitted property. Required surviving
work, canonical/formatted source counts, full-input timings, runtime image
closure and chart admission remain unqualified.
