# Optional ARM64 word extensions: retained partial results

The optional compiler change reuses the zero upper word already written by scalar I32 addition, subtraction and multiplication. It removes 2,997,152 instructions from the actual random 1 MiB scorer: 60,448,921 → 57,451,769, with unchanged branch and stack counts. This is approximately 5% fewer scorer instructions, not a 5% end-to-end speedup.

**The qualified default is unchanged: 81/81 Roc and 63/81 libdeflate wins at `832e5103a`.** Two new 27-case panels narrowly miss natural 4 KiB in their reverse order. These partial gains are retained for repair and combination; no new score, full81 qualification or confidence claim is made. Some natural inputs become slower while still beating peers. One linear/plain screening order also misses natural4KiB.

Compiler source: [`35cfc3694080ffa8d6eaa061d55f41d36cf4cc96`](https://github.com/mech-lang/mech/commit/35cfc3694080ffa8d6eaa061d55f41d36cf4cc96). `MECH_ARM64_REUSE_I32_ARITHMETIC=add/sub/mul/all/1` is globally off. Parameters, reductions, signed loads and arbitrary I32 values retain their normal extension. The original 2,719-line codec and canonical bytecode are unchanged; no LLVM dependency is added.

The measured source is bound to all 71 frozen compiler inputs. Both modes pass 14,144 actual native differential calls, the add machine-code probe and 79 scalar tests; the enabled mode also passes maintained lookup/admission/packet/range/SSA families. The focused calls cover wrapping arithmetic, immediate/shifted/fused forms, dirty upper input bits, signed and unsigned uses, shared packed stores, reductions, a phi and signed loads. No full GPU suite is claimed.

All fifteen alternatives reproduce the complete object, metadata and bytecode in normal and checked public replays (30 replays). Each passes 162 output/alias/resource observations, six checked failures and twelve injected failure/recovery pairs. Stack is 4,736 B under the 5,280-B cap. Final layouts use 63,800 B of encoder text and unchanged 3,200-B readonly lookup storage; raw layouts use 63,816 B. No isolated source-through-link timing or deployed executable size is claimed for these optional candidates yet. The existing qualified default remains 2.213 s and 210,024 B; those are prior measurements.

Measurements below use the M1 and matched qualified-control workers. Ratios divide Mech elapsed time by peer time; smaller is better. Offline counters, test construction and source replays are separate from primary runtime clocks. Zero-duration observations and every partial result remain included.

| Candidate | Order | Cases | Mech 1 MiB ms | C ms | Paired Mech/C | Paired Mech/control | Missing required wins |
|---|---|---:|---:|---:|---:|---:|---|
| add-linear-preserved | forward | 27 | 22.306709 | 20.359167 | 1.098816 | 0.995198 | {'roc': [], 'libdeflate': []} |
| add-linear-preserved | reverse | 27 | 22.328354 | 20.329667 | 1.100216 | 0.994424 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| add-sqrt-preserved | forward | 27 | 22.312104 | 20.346480 | 1.096431 | 0.993664 | {'roc': [], 'libdeflate': []} |
| add-sqrt-preserved | reverse | 27 | 22.316833 | 20.304542 | 1.100033 | 0.994658 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| add-linear-plain | forward | 5 | 22.314896 | 20.318124 | 1.098210 | 0.993487 | {'roc': [], 'libdeflate': []} |
| add-linear-plain | reverse | 5 | 22.312417 | 20.334583 | 1.098521 | 0.993639 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| add-linear-preserved | forward | 5 | 22.301354 | 20.319188 | 1.098039 | 0.993574 | {'roc': [], 'libdeflate': []} |
| add-linear-preserved | reverse | 5 | 22.315959 | 20.324397 | 1.099250 | 0.994176 | {'roc': [], 'libdeflate': []} |
| add | forward | 5 | 22.307978 | 20.310500 | 1.099374 | 0.994437 | {'roc': [], 'libdeflate': []} |
| add | reverse | 5 | 22.313375 | 20.316208 | 1.098873 | 0.993919 | {'roc': [], 'libdeflate': []} |
| add-sqrt-plain | forward | 5 | 22.316875 | 20.317291 | 1.098725 | 0.993960 | {'roc': [], 'libdeflate': []} |
| add-sqrt-plain | reverse | 5 | 22.327375 | 20.311250 | 1.100558 | 0.994493 | {'roc': [], 'libdeflate': []} |
| add-sqrt-preserved | forward | 5 | 22.315853 | 20.330791 | 1.097381 | 0.994195 | {'roc': [], 'libdeflate': []} |
| add-sqrt-preserved | reverse | 5 | 22.315062 | 20.329730 | 1.099070 | 0.994238 | {'roc': [], 'libdeflate': []} |

## Reproduce

Build from source commit `35cfc3694080ffa8d6eaa061d55f41d36cf4cc96`, then run:

```sh
python3 build_compiler.py /tmp/mech-word-extension-compiler
python3 reproduce.py /tmp/mech-word-extension-compiler/release/compile_profile /tmp/mech-word-extension-control --role control
python3 reproduce.py /tmp/mech-word-extension-compiler/release/compile_profile /tmp/mech-word-extension-candidate --role add-sqrt-preserved --checked
python3 verify.py
```

[All timings](PARITY.md) · [Portable recipes](recipes.json) · [Raw archive hashes](archives.json) · [Verification totals](verification.json). The archives include both source producers and native test transcripts, complete normal/checked artifacts, strict native gates and recovery results, actual native block counts, profile derivations, thirty source replays and every raw runtime observation. No compiler/test executable is required to verify the saved evidence.
