# Indexed table addresses

Source: [Mech PR #995 at `de6774576`](https://github.com/mech-lang/mech/pull/995/commits/de67745764a7cfc124c6bad8ed51c36ad11e1883). The current qualified recipe is `address-focus`; see [recommended-recipe.json](recommended-recipe.json) and the central [latest pointer](../mechdeflate-latest.json).

The matcher repeatedly calculated addresses such as `base + ((index * 2 + 0x20000) * 2)`. The new compiler pass expresses this as `(base + 0x40000) + index * 4`, allowing simpler indexed loads. It distributes only wrapping I64 arithmetic; casts, masks and other operations remain opaque. It retains every address modulo 2^64, memory offset/flag, source guard and effect order. Analysis has a fixed work limit. `MECH_COMPACT_NORMALIZE_INDEXED_ADDRESSES=local` or `hoisted` enables the experiment; it remains off globally.

No Mechdeflate source was rewritten, canonical bytecode is unchanged, and no LLVM dependency was added. With the pass disabled, the standard, paired and word-arithmetic images reproduce all three reference artifacts exactly. The source change is available to other compiler agents as a normal Git revision.

## Qualified result

Apple M1, macOS 15.6.1, arm64. Both full81 runs use 96 balanced blocks per case. Every named **81 Roc / 63 libdeflate win** holds in both orders. There is no 64th C win yet.

| Random 1 MiB | Forward | Reverse |
| --- | ---: | ---: |
| Qualified word control | 21.940417 ms | 21.885084 ms |
| Indexed addresses | 21.338000 ms | 21.276188 ms |
| libdeflate | 20.338542 ms | 20.310021 ms |
| Candidate / libdeflate, paired blocks | 1.048437× | 1.048818× |

The candidate takes about **2.7–2.8% less Mech time** than the matched control. Another **4.62–4.65% reduction in Mech time** is needed for parity on this closest losing case. These are point estimates; no formal confidence claim is added.

| Artifact | Word control | Indexed addresses |
| --- | ---: | ---: |
| Encoder text | 64,088 B | **64,040 B** |
| Readonly data | 3,200 B | 3,200 B |
| Stripped executable | 210,024 B | 210,024 B |
| Actual total stack | 4,736 B | 4,736 B |

## Complete builds

Eight balanced serial orders, fresh process/output/cache for each build, unchanged original sources through final executable linking. All compilers and identical fixed support are prebuilt equally. Compiler construction and stripping are separate. Every Mech object, metadata file and bytecode image matches its qualified hash in every build.

| Source through final executable link | Time |
| --- | ---: |
| Qualified word control | 2.178721 s |
| Indexed addresses | **2.183069 s** |
| Roc | 2.976984 s |
| libdeflate | 0.479167 s |

Paired median build ratios: **1.0011× control**, **0.7311× Roc**, **4.5443× C**. Build time is effectively unchanged. Candidate median phases: parse 0.6761 s, frontend 0.2224 s, native 1.2077 s, final link 0.0351 s; stripping is another 0.0106 s. Peer stripped executables are 191,912 B for Roc and 155,752 B for C. All four timed warmup executables pass all81 standalone checks: 324 independently inflated outputs, with raw streams retained.

## Retained partial result

`address-balanced` is smaller (**64,008 B**) and slightly faster on random1M (**21.271–21.300 ms**, **1.0476–1.0482× C**) in its six-case screen. It loses `prefix-natural-4096` in reverse order at **1.001844× C**, about 0.184% above parity in paired blocks. It remains available for repair or combination. It has not replaced the qualified `address-focus` image. All source recipes, captures, counts, gates and screen observations are retained, including the identical local/hoisted raw images.

The next repair can combine the balanced allocation with a declared natural4K/random1M-weighted block order, or with another source improvement. Do not drop this candidate merely for one loss.

## Checks and replay

Two actual JIT differential tests cover wrapping addresses, negative biases, casts, masks, shared memory effects and invalid-base guard paths. The two option modes also pass 166 scalar/append test executions. The final qualified matcher executes **170,329,253 instructions** on random1M, versus **174,177,704** in its word control, about 2.2% fewer. Both retain 28,766,024 branches and 2,097,082 prefetch hints. These counters come from diagnostic clones of the exact images and are separate from elapsed-time measurements.

Six candidate images each pass 162 codec output/inflation/alias/resource/cleanup observations, six named checked errors and 12 recovery pairs. Normal, register-checked and inspection emissions match. Warning policy, formatting and the unsafe-boundary audit pass. Full GPU tests and full CI are not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/indexed-replay \
  --target-dir /tmp/indexed-target
python3 reproduce.py --mech-root /path/to/mech --output /tmp/indexed-checked \
  --compiler /tmp/indexed-replay/compile_profile --checked
python3 verify.py
```

The default replay emits the control and qualified candidate; `--role` selects any retained alternative. It constructs the compiler from the linked source unless a compiler is supplied, and checks exact object, metadata and canonical bytecode hashes. All profiles are content-addressed. Historical absolute paths remain in the raw records. Replaying the full timing campaign additionally requires the pinned peer compilers and fixed support described there.
