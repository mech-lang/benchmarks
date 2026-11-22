# Native zero extensions: source, qualification and retained alternatives

**Selected: `m1-native-zero-extensions`, every named 81/81 Roc and 63/81 libdeflate win retained in both complete 81-case, 96-block orders.** Source lowering reuses clean upper bits already written by ARM64 I32 arithmetic and I8 loads. Fresh actual-count matcher weights and machine layouts repair the natural4KiB loss from the earlier word-only partial.

The selected encoder uses **63,832 B of code, 3,200 B of readonly lookup data and a 210,024-B stripped executable**. This costs 32 B of encoder text versus the qualified 63,800-B control; executable size and 4,736-B stack are unchanged. The separately full-qualified `byte-compare-sqrt` alternative uses **63,784 B of code**, the same 210,024-B executable and 4,864-B stack. It is retained for size-oriented combinations. The goal remains 1× libdeflate across all 81 cases; **no 64th win or confidence claim is added**.

The original **2,719-line Mech source and canonical bytecode are unchanged**. Compiler source is [`e112b5dcd5e01c22938aaf20dad49fad3d442a1e`](https://github.com/mech-lang/mech/commit/e112b5dcd5e01c22938aaf20dad49fad3d442a1e), bound to all 73 frozen producer inputs. There is no new LLVM dependency, operation interpreter, per-operation allocation or weaker admission.

## Compiler change

`MECH_ARM64_REUSE_I32_ARITHMETIC=add/sub/mul/all/1` reuses W-register arithmetic results for I32→I64 unsigned extension. `MECH_ARM64_REUSE_I8_DEFINITIONS=load/compare/all/1` reuses native unsigned byte loads or canonical scalar comparison results. The selected recipe uses `add` and `load`. Both controls remain off globally. Parameters, truncations, phis, signed loads and arbitrary narrow values keep their existing extensions. The byte-load hook retains the original load, address and flags; it does not sink or duplicate memory operations. Scalar comparisons are limited to the existing 8/16/32/64-bit CSet lowering, which writes 0 or 1.

The current 1 MiB scorer executes **57,451,769 instructions versus 60,448,921** in the qualified control; stack traffic is unchanged. The selected matcher executes **176,294,737 versus 177,335,052**, with unchanged stack-store count. These are actual native block counts, separate from elapsed-time measurements. The smaller combined/compare variants expose different spill tradeoffs; their data and slower trials remain included.

## Full-suite timings

Matched M1 measurements; ratios divide Mech elapsed time by peer time, so smaller is better. Both orders retain all required wins. Some other cases become slower, including distribution change for the selected variant; every result appears in [PARITY.md](PARITY.md).

| Order | Case | Mech ms | Matched control ms | Roc ms | C ms | Paired Mech/C | Mech reduction to parity |
|---|---|---:|---:|---:|---:|---:|---:|
| forward | prefix-random-1048576 | 22.274187 | 22.451874 | 28.817125 | 20.353396 | 1.095205 | 8.69% |
| forward | prefix-random-4096 | 0.103813 | 0.105875 | 0.373312 | 0.075584 | 1.381515 | 27.62% |
| forward | prefix-natural-4096 | 0.387833 | 0.390646 | 0.662021 | 0.392188 | 0.988990 | 0.00% |
| reverse | prefix-random-1048576 | 22.329896 | 22.495188 | 28.777313 | 20.383605 | 1.099229 | 9.03% |
| reverse | prefix-random-4096 | 0.103708 | 0.106770 | 0.368563 | 0.076500 | 1.370895 | 27.05% |
| reverse | prefix-natural-4096 | 0.386708 | 0.388917 | 0.660166 | 0.392292 | 0.992752 | 0.00% |

Across the eighteen remaining libdeflate losses, descriptive equal-case geometric Mech/control ratios are **0.990970 /0.989859** in the full orders, approximately 0.90% /1.01% less time. This does not assert a confidence interval or improve the score beyond 63.

## Complete builds and sizes

Twelve balanced serial orders use equally prebuilt compilers and fixed support. Every build starts a fresh process and includes original source through final executable linking; compiler construction and strip are separate. All runtime, native tests, counters, archives and Git jobs finish before these primary clocks.

| Actor | Source through final link s | Strip s | Stripped executable B |
|---|---:|---:|---:|
| mech-control-reference | 2.210357 | 0.010789 | 210,024 |
| mech-new-disabled | 2.202031 | 0.010677 | 210,024 |
| mech-byte-load-linear | 2.202810 | 0.010699 | 210,024 |
| mech-byte-compare-sqrt | 2.205487 | 0.010694 | 210,024 |
| roc | 2.986897 | 0.010760 | 191,912 |
| libdeflate | 0.481464 | 0.010692 | 155,752 |

Selected paired build time is **0.737406× Roc /4.576737× libdeflate**. Current options-off construction produces a similar complete-build time; no material compile-time gain is attributed to native extension reuse. Parse/frontend/native/link medians are **0.703178 /0.217862 /1.208404 /0.035189 s**; independently calculated phase medians do not add exactly.

## Verification and reproduction

All eighteen alternatives pass 162 success/output/alias/resource observations, six checked failures and twelve injected failure/recovery pairs. The largest actual stack is 4,864 B under the 5,280-B cap. Four fixed test environments each execute **48,960 byte-definition and 14,144 arithmetic native differential calls**, plus 79 maintained scalar tests; the enabled mode also passes the maintained admission, packet, range, select and SSA families. Focused probes verify the actual extension instructions disappear only when enabled. No full GPU suite is claimed.

**36 public normal/checked source replays** reproduce the entire object, metadata and bytecode exactly. Both actual main-builder invocations reproduce the selected default and retained prior default. **All 486 timed executable deployments** produce independently inflated streams. The portable verifier checks these records, all native count translations, every raw runtime observation (including zero durations), source/profile hashes and twelve complete-build orders.

From compiler source `e112b5dcd5e01c22938aaf20dad49fad3d442a1e`:

```sh
python3 build_compiler.py /tmp/mech-zero-extension-compiler
python3 reproduce.py /tmp/mech-zero-extension-compiler/release/compile_profile /tmp/mech-zero-extension-control --role control
python3 reproduce.py /tmp/mech-zero-extension-compiler/release/compile_profile /tmp/mech-zero-extension-candidate --role byte-load-linear --checked
python3 ../../rebuild.py /tmp/mech-zero-extension-executable --variant m1-native-zero-extensions
python3 verify.py
```

[All timings](PARITY.md) · [All source recipes](recipes.json) · [Archive hashes](archives.json) · [Verification totals](verification.json). The initial raw variants, register repairs, all slower trials and the single combined-linear reverse natural4KiB loss remain archived. The earlier word-only partial and its two failed broad reverse orders remain in [their evidence](../arm64-word-extensions/README.md).
