# Mechdeflate: confirmed 81/81 on M3

The unchanged **243,209-byte, 2,719-line** compressor wins **81/81 against Roc and 81/81 against libdeflate in both orders of two complete M3 runs**. Independent verification recomputed all **3,930,624 timed observations**. [Compiler PR #1000](https://github.com/mech-lang/mech/pull/1000) · [Exact recipe](recipe.json) · [Every case margin](case-margins.json).

| Build on this M3 | Forward Roc | Forward libdeflate | Reverse Roc | Reverse libdeflate |
|---|---:|---:|---:|---:|
| Frozen M1 winner from #999 | 78/81 | 80/81 | 81/81 | 78/81 |
| LLVM root, primary | 81/81 | 81/81 | 81/81 | 81/81 |
| Same executable, confirmation | 81/81 | 81/81 | 81/81 | 81/81 |

The M1 encoder object, canonical bytecode, and metadata reproduced byte for byte before measuring its frozen workers on M3. The source fix is Mech `5fecc795fb4862aeecc11a811d148a7f9a13c351`, based on #999 at `2b301734f`. The benchmark base is `233e20174`. [Environment and tools](environment.json) · [Source/artifact parity](checks/source-commit.json).

## What changed

LLVM optimizes the outer control function while the specialized compression kernels retain their checked Cranelift profiles. The compiler now preserves their selected machine settings, supports the existing 1–8-word register-return ABI, names shared private tables, and admits exact addresses of declared module-owned helpers. The witnessed U32 sort can borrow unused invocation-local snapshot space. The language grammar and compressor source are unchanged.

| Measurement | Original M1 encoder | M3 LLVM encoder |
|---|---:|---:|
| Native object | 156,616 bytes | **148,720 bytes** |
| Main function frame | 3,312 bytes | **1,552 bytes** |
| Measured peak native stack | 5,184 bytes | **3,440 bytes** |

Source through the complete timing executable took **3.304, 3.182, and 3.216 seconds**; median **3.216 s**, with compiler and host/runtime dependencies prebuilt. This includes frontend work, LLVM optimization, object assembly, and Rust worker compilation/linking. The M1 handoff used a separate final deployment adapter. [Complete build observations](checks/source-to-executable.json).

The four profiles and all 225 encoder settings are pinned; the build driver selects the installed LLVM bin directory separately. All 162 correctness observations preserve the original resource counters, capacity, input aliases and borrowed-output aliases, and produce exact Roc bytes with independent inflation. The runtime passes 26 tests. Cross-backend tests check 1–8 return values over 10,000 inputs per arity in both directions; mixed layouts, nine-word returns and malformed function addresses remain refused. **477 fault/recovery pairs per backend** match exactly, including 390 checked allocation errors, source origins, accounting, caller discard and subsequent successful recovery. [Accounting](checks/resource-equivalence.json) · [Fault recovery](checks/fault-recovery.json) · [Native stack](checks/native-stack.json) · [ABI tests](checks/register-abi-tests.log).

## Rebuild and replay

Use Apple Silicon macOS, Python 3.11+, Rustup, and the recorded Apple toolchain. The recorded machine is an M3 on macOS 26.2 with CLT clang 15 / SDK 14.4 and Rust nightly 2026-03-03 / LLVM 22.1.0. The recipe verifies the compiler inputs, four profile hashes, LLVM executables, and all three emitted encoder artifacts.

```sh
git -C /path/to/mech fetch origin codex/m3-deflate-81
git -C /path/to/mech switch --detach 5fecc795fb4862aeecc11a811d148a7f9a13c351
rustup toolchain install nightly-2026-03-03 --profile minimal --component llvm-tools
python3 experiments/mech/mechdeflate-m3-81-v1/rebuild.py \
  --mech-root /path/to/mech --output /tmp/mechdeflate-m3-build
python3 experiments/mech/mechdeflate-m3-81-v1/replay.py \
  --output /tmp/mechdeflate-m3-replay
```

`rebuild.py` builds the compiler, matching 12-record host runtime, and complete executable at `bound/mech-worker`. Runtime tests and all encoder hashes must pass. `replay.py` uses the pinned workers and restores the original fixtures, peers, oracle and controller from the M1 packet. Add `--candidate-bound /tmp/mechdeflate-m3-build/bound` to measure the rebuilt executable, or `--prepare-only` to restore inputs without starting clocks. Rebuilt Rust executables record their own hashes; qualification uses the exact pinned executable. Exact object checks use the recorded LLVM and Apple linker versions.

```sh
python3 experiments/mech/mechdeflate-m3-81-v1/verify.py \
  --output /tmp/mechdeflate-m3-evidence-check
```

This verifies every archive/file hash and independently recomputes both full qualification runs. `--all-studies` also recomputes the saved exploratory studies. [79-study catalog](studies.json) · [Raw observations and as-run diagnostics](evidence/manifest.json).

## Boundary and unsuccessful work

Each full order uses the original 81 fixtures and 96 balanced blocks per case, with all permutations of four actors repeated four times. A win requires a paired geometric-mean ratio strictly below one. The peers are the original pinned Roc worker and libdeflate 1.26. Primary runs retain the original sequential warmups and ordinary scheduling.

The timer includes heap/owner-storage construction, the complete compact native call, final allocation transfer, counter reads and private cleanup. Preparation, validation, independent inflation and destruction of previous output slots are excluded. This is the published diagnostic entry; ordinary exact resource-admission/accounting/publication recovery is omitted.

All completed exploratory studies, narrow losses, failed preparations and null controls are retained. The first incomplete-recipe result is excluded from M1 transport conclusions. Identical-executable short screens differed by as much as 7.9%; concurrent warmups and priority changes did not reliably remove that variation. Those scheduling experiments are separate from qualification. The two final full runs use the same executable and unchanged original timing protocol.

The earlier stripped deployment link on this M3 was 16 bytes larger than its M1 hash despite all three original encoder artifacts matching. That failed gate is retained in [the original reproduction receipt](checks/m1-encoder-reproduction.json); the final M3 result measures the pinned complete timing executable.
