# Missing pi diagnostic capture

This additive stage runs the unchanged emitted `pidigits.js` once at the prescribed input 10000. The original plan, failed stage report, terminal, capability listing and complete tree native artifacts are prerequisites. Both original native processes exited normally and were reaped; the stage failed in derived stdout parsing when native bytecode diagnostics interleaved with application lines. Neither original process is repeated, and this continuation does not promote the tree output or required-work evidence.

The exact saved `--v8-options` listing supports `--maglev-print-filter` (string) and `--maglev-print-feedback` (boolean). The pi invocation retains all original diagnostic options and adds `--maglev-print-filter=calculatePi --no-maglev-print-feedback` to narrow Maglev printing. Default per-isolate event and code trace filenames remain enabled. V8's observed “Concurrent maglev has been disabled for tracing” notice is a diagnostic scheduling effect; this capture is not a timing sample. The application source, input, Node binary, heap settings and GC policy are unchanged. No explicit optimization request is added.

The controller retains stdout and stderr byte-for-byte and hashes every artifact. A successful stage means the one native process exited normally, its identity and group were closed, and the raw streams and files match the terminal inventory. Application-output parsing, instruction semantics, required work, runtime dependency closure, timings and chart admission remain unqualified. Unexpected diagnostic text is retained for independent lossless post-processing; it does not cause a repeat invocation. Missing code logs similarly remain a review limitation rather than a reason to rerun automatically.

The frozen observer enforces 180 seconds, a 5-second cleanup bound, 10 GiB process-group RSS, 128 MiB per native file/stdout bound, and a 768 MiB/100-file stage inventory. Preparation and execution both own the existing common mutex continuously. The retained Python interpreter requires `-I -S -B`, with no optimization, and its exact path and SHA are checked inside the mutex. There are no automatic retries.

Prepare with the retained Python and absolute paths:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/typescript_single_entry_remaining.py prepare --plan /private/tmp/mech-benchmark-completion/experiments/typescript/single-entry-work-v1/plan-pi-v1.json --output /private/tmp/mech-benchmark-completion/experiments/typescript/single-entry-work-v1/run-pi-v1
```

Review the concrete plan, then use the same interpreter and controller with `run --plan <absolute plan> --plan-sha256 <prepared SHA-256>`. The output is fresh and the schedule contains only `00-pidigits`. Original evidence remains in `run-v1`; new evidence remains in `run-pi-v1`.
