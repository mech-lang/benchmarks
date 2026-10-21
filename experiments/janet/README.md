# Janet benchmarks

Janet is being added across the ten suite workloads using Janet 1.42.1. The
official Apple Silicon distribution, archive digest, exact source revision and
MIT runtime license are retained in
[runtime-acquisition-v1.json](runtime-acquisition-v1.json).

All ten [active source drafts](source-v2/) pass compile-only checks with empty
stdout/stderr using the locally built runtime. The
[source manifest](source-manifest-v1.json) binds each exact source, every consulted
local predecessor, original Benchmarks Game citations and applicable notices
and licenses. These are newly authored adaptations or implementations, not
original Janet submissions to the Benchmarks Game.

The initial execution variant is the standard standalone Janet bytecode VM.
Fresh-process timing will include source parsing, bytecode compilation, VM
startup, complete input/computation/output and shutdown. A standalone executable
containing the VM is not classified as native AOT compilation of the application.

[plan-v1.json](plan-v1.json) tracks all ten workloads. Source implementations,
required-work checks, source-size measures, toolchain/library versions and
complete observations are required before plotted admission. Candidate source
files are newly authored Janet programs; specific consulted predecessor files,
original authors and licenses must accompany each source record. Current
authoring identifies Codex GPT-6; the exact serving model is unknown.

## Runtime and development validation

The downloaded executable stalled in macOS launch before returning a version.
The [owned launch observation](runtime-probe-v1/hang-observation.json) retains
its exact PID/group and the termination signal; it does not claim that the
uninterruptible process has exited. No security setting was changed. The
[local build result](local-runtime-build-result-v1.json) instead uses the
verified release's bundled C sources and header with Apple Clang. Its observed
version is `1.42.1-e1963cd`. Runtime compilation is preparation, outside any
benchmark interval.

The [initial compile-only attempt](syntax-v1/reconciliation.json) exposed a
constant-parameter assignment and an incorrect module search path. Janet's
`-k` command returned zero even when it printed these diagnostics. The original
snapshots, streams and producer result remain; the reconciliation rejects the
producer's exit-code-only success label. The corrected
[second attempt](syntax-v2/results.json) requires zero exit and empty streams
for every source. All ten meet that stronger development check. Compile-only
checks do not execute benchmark main functions or qualify their outputs/work.

Untimed runtime/flycheck development commands retain their explicit resource
reservation exception while the first `--version` launch remains uninterruptible.
Quantitative measurements require the unchanged common mutex and have not
started. Clean locked process/closure qualification remains a separate gate.

Regex-redux uses the unmodified published
[Spork regex module](dependencies-v1/spork/snapshot.json), which compiles its
supported regular expressions to Janet's PEG engine. Pi digit generation uses
Janet's ordinary FFI to call general GMP arithmetic operations; the spigot state,
decisions, loops and output remain in Janet. Every authored FFI declaration is
application source. The native GMP ABI and both workloads' complete outputs
still require qualification.

Implementations and dependencies remain local to this packet while qualification
is in progress. No Janet timing is yet admitted, and existing language results
remain unchanged. Every benchmark will run sequentially under the shared mutex.
