# Separate native CPU samples

Five-second, 1 ms native samples. Exclusive counts include only encoder-root descendants and subtract child counts once. Compiler boundaries differ; these are guides rather than exact matched phase times. None of these runs supplies primary latency.

| Input | Mech matching | Mech scoring | Mech packed histogram | Mech byte histogram | Mech Huffman |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random 1 MiB | 74.32% | 14.36% | 7.28% | 1.32% | 0.42% |
| Random 4 KiB | 42.01% | 3.23% | 8.02% | 2.05% | 15.24% |

Exact per-function Mech and libdeflate root totals, counts and shares are in [sampling.json](sampling.json). The original reports and all 200,800 independently checked diagnostic observations are archived. Historical sampling fractions are not reused for the new matcher.

| Input | C near-optimal encoder | C path scorer | C memset | C Huffman |
| --- | ---: | ---: | ---: | ---: |
| Random 1 MiB | 68.81% | 25.66% | 0.05% | 0.53% |
| Random 4 KiB | 44.81% | 21.91% | 20.09% | 8.19% |

These C functions do not have identical boundaries to the Mech phases; their percentages are not interchangeable elapsed times.
