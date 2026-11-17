# Paired Rust task controls

Full K-nucleotide uses the complete fresh-process boundary. All 12 compressor inputs use a complete checked compressor call, including output allocation and scratch destruction. Input import, compilation, one warmup and returned-output destruction are outside the call. Mech level 12 and Rust zlib-rs level 9 may produce different streams: inspect output size with time.

| Task / Mech path | Mech seconds | Rust seconds | Mech / Rust |
| --- | ---: | ---: | ---: |
| knucleotide / source-native | 0.909183625 | 0.688167625 | 1.321 |
| deflate-empty / program-jit | 9.9583e-05 | 6.5e-06 | 15.320 |
| deflate-empty / program-jit-bytecode | 9.9458e-05 | 6.5e-06 | 15.301 |
| deflate-one-stored / program-jit | 9.9833e-05 | 7.917e-06 | 12.610 |
| deflate-one-stored / program-jit-bytecode | 9.9708e-05 | 7.917e-06 | 12.594 |
| deflate-seven-stored-prefix / program-jit | 9.8791e-05 | 7.958e-06 | 12.414 |
| deflate-seven-stored-prefix / program-jit-bytecode | 9.9e-05 | 7.958e-06 | 12.440 |
| deflate-eight-literals / program-jit | 0.000539958 | 8.125e-06 | 66.456 |
| deflate-eight-literals / program-jit-bytecode | 0.000538042 | 8.125e-06 | 66.221 |
| deflate-eight-overlap / program-jit | 0.001379791 | 7.875e-06 | 175.212 |
| deflate-eight-overlap / program-jit-bytecode | 0.001375042 | 7.875e-06 | 174.609 |
| deflate-320-overlap / program-jit | 0.001216625 | 8.167e-06 | 148.968 |
| deflate-320-overlap / program-jit-bytecode | 0.001241 | 8.167e-06 | 151.953 |
| deflate-eight-literals-prefix / program-jit | 0.000516625 | 8.042e-06 | 64.241 |
| deflate-eight-literals-prefix / program-jit-bytecode | 0.000516042 | 8.042e-06 | 64.168 |
| deflate-128-biased-dynamic / program-jit | 0.001093667 | 9.416e-06 | 116.150 |
| deflate-128-biased-dynamic / program-jit-bytecode | 0.001102875 | 9.416e-06 | 117.128 |
| deflate-32-high-entropy-stored / program-jit | 0.001123708 | 8.875e-06 | 126.615 |
| deflate-32-high-entropy-stored / program-jit-bytecode | 0.001140584 | 8.875e-06 | 128.517 |
| deflate-16384-distribution-change / program-jit | 0.00393575 | 0.000153083 | 25.710 |
| deflate-16384-distribution-change / program-jit-bytecode | 0.003976208 | 0.000153083 | 25.974 |
| deflate-33027-periodic-window / program-jit | 0.004230833 | 3.7416e-05 | 113.076 |
| deflate-33027-periodic-window / program-jit-bytecode | 0.004257542 | 3.7416e-05 | 113.789 |
| deflate / program-jit | 1.87150646 | 0.177674417 | 10.533 |
| deflate / program-jit-bytecode | 1.87390158 | 0.177674417 | 10.547 |

| Compression case | Mech output bytes | Rust output bytes |
| --- | ---: | ---: |
| deflate-empty | 5 | 2 |
| deflate-one-stored | 6 | 3 |
| deflate-seven-stored-prefix | 14 | 11 |
| deflate-eight-literals | 10 | 10 |
| deflate-eight-overlap | 5 | 5 |
| deflate-320-overlap | 7 | 7 |
| deflate-eight-literals-prefix | 12 | 12 |
| deflate-128-biased-dynamic | 65 | 70 |
| deflate-32-high-entropy-stored | 37 | 37 |
| deflate-16384-distribution-change | 11394 | 13384 |
| deflate-33027-periodic-window | 151 | 151 |
| deflate | 1696488 | 1826397 |
