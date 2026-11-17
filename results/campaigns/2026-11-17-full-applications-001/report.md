# Full application campaign

Outcome: ok. Independent process forks: 3.

K-nucleotide consumes FASTA N=25,000,000. N-body and the JVM control each execute 50,000,000 steps. Deflate covers every maintained small stream, both boundary inputs and the entire 6,627,202-byte corpus in source and decoded forms.

Deflate calls preserve held input/prefix snapshots, publish a separately owned complete stream, and release all managed storage. Python zlib checks exact decompression, EOF and absence of trailing data. Mech and Roc match the pinned level-12 stream; libdeflate has its own valid stream.

Each Deflate fork compiles the complete program once, then invokes all corpus inputs. Compilation, input snapshot import, warmup and returned-output destruction are excluded from the call timer. The complete fork process is retained separately in raw supervision. Roc/libdeflate have different transport and allocation contracts; these observations do not establish an automatic cross-runtime speed ratio.

| Case | Backend | Median primary seconds |
| --- | --- | ---: |
| knucleotide | source-native | 0.6367321251891553 |
| deflate | program-jit | 1.866435208 |
| deflate | program-jit-bytecode | 1.8678405420000002 |
| deflate | roc | 0.758299000096 |
| deflate | libdeflate | 0.986525000073 |
| nbody | fused-native | 1.352372375316918 |
| jvm | jvm | 1.988411083817482 |
| deflate-empty | program-jit | 0.000100709 |
| deflate-empty | program-jit-bytecode | 9.9041e-05 |
| deflate-empty | roc | 9.9977478385e-07 |
| deflate-empty | libdeflate | 1.39996409416e-05 |
| deflate-one-stored | program-jit | 9.9667e-05 |
| deflate-one-stored | program-jit-bytecode | 9.9875e-05 |
| deflate-one-stored | roc | 1.00024044514e-06 |
| deflate-one-stored | libdeflate | 1.40001066029e-05 |
| deflate-seven-stored-prefix | program-jit | 9.9833e-05 |
| deflate-seven-stored-prefix | program-jit-bytecode | 9.8583e-05 |
| deflate-seven-stored-prefix | roc | 1.00024044514e-06 |
| deflate-seven-stored-prefix | libdeflate | 1.20000913739e-05 |
| deflate-eight-literals | program-jit | 0.000538334 |
| deflate-eight-literals | program-jit-bytecode | 0.000533292 |
| deflate-eight-literals | roc | 0.000450000166893 |
| deflate-eight-literals | libdeflate | 4.70001250505e-05 |
| deflate-eight-overlap | program-jit | 0.001383667 |
| deflate-eight-overlap | program-jit-bytecode | 0.001363458 |
| deflate-eight-overlap | roc | 0.000488999765366 |
| deflate-eight-overlap | libdeflate | 4.99999150634e-05 |
| deflate-320-overlap | program-jit | 0.001223084 |
| deflate-320-overlap | program-jit-bytecode | 0.001218375 |
| deflate-320-overlap | roc | 0.000475999899209 |
| deflate-320-overlap | libdeflate | 5.59999607503e-05 |
| deflate-eight-literals-prefix | program-jit | 0.000515125 |
| deflate-eight-literals-prefix | program-jit-bytecode | 0.000516458 |
| deflate-eight-literals-prefix | roc | 0.000459000002593 |
| deflate-eight-literals-prefix | libdeflate | 4.79998998344e-05 |
| deflate-128-biased-dynamic | program-jit | 0.001088208 |
| deflate-128-biased-dynamic | program-jit-bytecode | 0.001085 |
| deflate-128-biased-dynamic | roc | 0.000544000416994 |
| deflate-128-biased-dynamic | libdeflate | 5.00003807247e-05 |
| deflate-32-high-entropy-stored | program-jit | 0.001118416 |
| deflate-32-high-entropy-stored | program-jit-bytecode | 0.001131958 |
| deflate-32-high-entropy-stored | roc | 0.000481999944896 |
| deflate-32-high-entropy-stored | libdeflate | 5.10001555085e-05 |
| deflate-16384-distribution-change | program-jit | 0.003907542 |
| deflate-16384-distribution-change | program-jit-bytecode | 0.003929708 |
| deflate-16384-distribution-change | roc | 0.000919000245631 |
| deflate-16384-distribution-change | libdeflate | 0.000385000370443 |
| deflate-33027-periodic-window | program-jit | 0.004247042 |
| deflate-33027-periodic-window | program-jit-bytecode | 0.004204 |
| deflate-33027-periodic-window | roc | 0.00121100014076 |
| deflate-33027-periodic-window | libdeflate | 0.000505999661982 |
