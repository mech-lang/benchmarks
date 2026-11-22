# Initialized private-packet motion: retained experiments

The selected default remains `m1-packed-node-progressive-16`: **63,784 B of encoder text, all 81 Roc and 63 libdeflate wins** qualified in the earlier full 81-case, both-order campaign. This study adds no 64th win and does not promote a new default. The original 2,719-line Mech codec and canonical bytecode are unchanged. There is no new LLVM dependency.

## What changed

`MECH_MOVE_PHASE_INPUT_PACKET` permits motion only for direct fixed-offset I64 loads from a fully initialized, aligned, immutable, nonescaping private invocation packet. The complete function is validated before flags change. Pointer escapes, writes, derived addresses, wrong widths and out-of-range offsets decline. This does not extend the permission to ordinary array loads protected by bounds branches. The option is globally off and accepts an exact `only:symbol,...` scope.

The source also wires requested register-frequency profiles into composed/grouped child phases and captures their CLIF/VCode without constructing unrelated general SSA. A deliberately mismatched expected-VCode profile fails closed. Two historical V2 child-profile requests were silently ignored: `scorer-linear-raw` and `scorer-sqrt-raw` are recorded as ignored trials, not trained allocation gains. Their public V3 recipes omit only the ignored request to reproduce the actual historical objects. Original flags, sources and logs are retained.

## Runtime: every measured alternative

These are 21-case discovery panels, 96 blocks in each order, against the identical published 63,784-B control. They do not establish full 81-case win counts. Ratios are paired Mech/libdeflate times; lower is better. All required named wins within these panels held. No confidence claim is made.

| Candidate | Order | Text B | Mech 1 MiB ms | C ms | Paired Mech/C | Mech time reduction to parity |
|---|---|---:|---:|---:|---:|---:|
| movable-linear | forward | 63,672 | 22.525958 | 20.306396 | 1.109159 | 9.84% |
| movable-linear | reverse | 63,672 | 22.528146 | 20.332688 | 1.109789 | 9.89% |
| movable-sqrt | forward | 63,672 | 22.543917 | 20.302354 | 1.110431 | 9.94% |
| movable-sqrt | reverse | 63,672 | 22.513021 | 20.325667 | 1.109374 | 9.86% |
| scorer-preserved-linear | forward | 63,752 | 22.761187 | 20.312042 | 1.121275 | 10.82% |
| scorer-preserved-linear | reverse | 63,752 | 22.712750 | 20.317646 | 1.119457 | 10.67% |
| scorer-preserved-sqrt | forward | 63,752 | 22.761834 | 20.308125 | 1.120961 | 10.79% |
| scorer-preserved-sqrt | reverse | 63,752 | 22.752083 | 20.317792 | 1.120280 | 10.74% |

Matcher motion plus fresh allocation saves 112 B but changes 1 MiB time only slightly; natural 8 KiB and distribution-change cases slow by about 2%. Broader scorer motion adds hot-loop spills. Actual register weights and the earlier preserved-register preference recover part of that cost, but the repaired scorer still slows the shipping workload. All variants are retained below and in the raw archive.

## Fresh-process complete builds

Twelve balanced serial orders, six actors, equally prebuilt compilers and fixed support. Each timed source build produces the original codec and links a final executable. Compiler construction and strip are separate. No CPU-heavy diagnostics, construction, Git or archive work overlaps primary clocks.

| Actor | Source through final link s | Strip s | Stripped executable B |
|---|---:|---:|---:|
| mech-control-reference | 2.205773 | 0.011149 | 276,072 |
| mech-new-disabled | 2.213907 | 0.011225 | 276,072 |
| mech-movable-linear | 2.216622 | 0.011286 | 276,072 |
| mech-scorer-preserved-linear | 2.213950 | 0.011196 | 276,072 |
| roc | 2.991459 | 0.010939 | 191,912 |
| libdeflate | 0.482200 | 0.010947 | 155,752 |

## Reproduce and verify

Build the compiler from this checkout, then replay any named role:

```sh
python3 build_compiler.py /tmp/mech-private-packet-compiler
python3 reproduce.py /tmp/mech-private-packet-compiler/release/compile_profile /tmp/mech-private-packet-control --role control
python3 reproduce.py /tmp/mech-private-packet-compiler/release/compile_profile /tmp/mech-private-packet-candidate --role movable-linear --checked
python3 verify.py
```

All twenty recipes replay in both normal and checked modes: exact object, full metadata and bytecode. Native checks cover 162 success/output/alias/resource observations, six checked errors and twelve injected failure/recovery pairs per role. Stack is 4,736 B except the all-phase experiment at 4,880 B; both are below 5,280 B. Focused packet tests execute 25,344 actual native calls, and maintained scalar/select/range/SSA families pass. The full GPU suite is not claimed. The portable verifier recomputes raw runtime observations, actual native counter totals, source identities and the 486 deployed stripped-executable outputs.

[All timings and parity gaps](PARITY.md), [recipes](recipes.json), [verification totals](verification.json), and [hashed archive manifest](archives.json).

## Next broader target

The actual scorer has a 65,536-byte readonly code table, separate from encoder machine code. `analyze_dense_codes.py` checks all 65,536 values against its 256-byte codebook/index formula and reports page-deduplication alternatives. This is an analytical proof, not an implemented compression or runtime improvement. A smaller representation must be emitted, checked across the domain and benchmarked before any gain is claimed.

## All source alternatives

| Role | Text B | Peak stack B |
|---|---:|---:|
| all-control-raw | 63,736 | 4,736 |
| all-movable-raw | 63,608 | 4,880 |
| control-raw | 63,720 | 4,736 |
| control | 63,784 | 4,736 |
| mf-huffman-raw | 63,512 | 4,736 |
| mf-scorer-raw | 63,624 | 4,736 |
| movable-linear | 63,672 | 4,736 |
| movable-linear-raw | 63,672 | 4,736 |
| movable-raw | 63,496 | 4,736 |
| movable-sqrt | 63,672 | 4,736 |
| movable-sqrt-raw | 63,688 | 4,736 |
| scorer-linear-raw | 63,800 | 4,736 |
| scorer-preserved-linear | 63,752 | 4,736 |
| scorer-preserved-linear-raw | 63,768 | 4,736 |
| scorer-preserved-max-raw | 63,768 | 4,736 |
| scorer-preserved-sqrt | 63,752 | 4,736 |
| scorer-preserved-sqrt-raw | 63,768 | 4,736 |
| scorer-sqrt-raw | 63,800 | 4,736 |
| scorer-v3-linear-raw | 63,784 | 4,736 |
| scorer-v3-sqrt-raw | 63,784 | 4,736 |
