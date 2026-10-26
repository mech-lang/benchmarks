# Native compiler probes

This is the maintained home for manual Mech native compiler diagnostics. The
probes use the compiler's existing correctness-test supports in a disposable
checkout. The compiler repository needs no benchmark hook, ambient include, or
public API for them.

`probes.json` pins the original source from Mech commit
`01b8b397011b6a774b7d9f730578a4ef92bf30f6`. Each run pins the requested compiler
commit, the archived and installed probe sources, the runner and shared process
controller, inputs, executable, and raw process receipts. Existing identical
probes are reused; a changed function with the same name is rejected. After a
probe has been removed from Mech, the runner installs it only in the disposable
checkout. Timing imports are scoped to the installed function.

| Probe | Purpose | Required fixtures |
| --- | --- | --- |
| `window-kernel` | Compare selected and scalar query kernels | FASTA and exact k-nucleotide oracle |
| `histogram-kernel` | Compare banked, serial, and scalar histogram kernels | FASTA |
| `window-region` | Inspect original/decoded compiler regions | None |

Both kernel probes require exactly **10,000,000 bases** in the selected `>THREE`
record. Their raw output describes the excluded work and retains the original
alternating diagnostic samples. These samples do not qualify complete-program
k-nucleotide performance. In particular, they exclude selection, hosting,
accounting, output, and commit overhead. Every result records
`performance_qualified: false` and `primary_timing_samples: 0`.

## Run

Use a clean local Mech repository containing the exact requested commit. Evidence
must be a new directory outside both repositories. The runner leaves the source
repository unchanged and allocates its own Cargo target directory under the
evidence directory, avoiding artifacts reused across different checkouts.

First inspect the overlay without compiling:

```sh
python3 tools/native-compiler-probes/run.py \
  --workspace /path/to/mech \
  --commit 01b8b397011b6a774b7d9f730578a4ef92bf30f6 \
  --probe all --prepare-only \
  --evidence /tmp/native-probes-prepare-01b8
```

Compile and verify all three exact ignored test selections without running them:

```sh
python3 tools/native-compiler-probes/run.py \
  --workspace /path/to/mech --commit FULL_COMPILER_COMMIT \
  --probe all --compile-only \
  --evidence /tmp/native-probes-compile-RUN_ID
```

Run the compiler-region inspection, or replace `window-region` with `all` and
supply `--input /path/to/fasta.stdin --oracle /path/to/knucleotide.stdout`:

```sh
python3 tools/native-compiler-probes/run.py \
  --workspace /path/to/mech --commit FULL_COMPILER_COMMIT \
  --probe window-region \
  --evidence /tmp/native-probes-region-RUN_ID
```

Compilation uses locked, offline Cargo with `canonical-native-program`, one build
job, and `nightly-2026-03-03` by default. Select another installed toolchain using
`--toolchain`, or an absolute Cargo path using `--cargo`. `--environment` accepts
a JSON map of build environment strings when the compiler needs explicit native
library paths. Otherwise, only the documented build-related variables in
`environment()` are inherited. Diagnostic fixture variables are always supplied
from the explicit input arguments and pinned in the result.

The shared owned-process controller currently requires macOS and access to the
process table. The existing `/private/tmp/mech-clbg-timing.lock` is opened without
creating or replacing it; `--mutex` can select the shared lock on another machine.
Compilation, test selection, and execution all inherit that mutex, use owned
process groups, and retain cleanup receipts. Lock contention fails before
compilation. Compilation has a 1,800-second deadline, each selection 30 seconds,
and each diagnostic 120 seconds. Run this outside primary timing campaigns.

`result.json`, `test-overlay.patch`, Cargo JSON output, exact-selection output,
diagnostic stdout/stderr, and every `process.json` remain in the evidence
directory. A successful run must select and pass exactly one test per probe;
zero-test success is rejected. Failures retain their evidence. A new run requires
a new evidence directory; prepare/compile results are not silently promoted into
a completed diagnostic run.

Runner contract checks (no compiler or native process):

```sh
python3 -m unittest discover -s tools/native-compiler-probes -p 'test_*.py' -v
```
