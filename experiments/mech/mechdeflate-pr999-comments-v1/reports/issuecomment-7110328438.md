@codex review

Please review [commit `f37b86d2216e62c90f6756aea22828e038d2c612`](https://github.com/mech-lang/mech/commit/f37b86d2216e62c90f6756aea22828e038d2c612).

The checked short-append fast path is inlined at four call sites. Each slow edge still calls the original checked continuation. The composed scorer shares its biased load addresses after rematerialization. The address addition is pure and the memory operations stay in place. The scorer reuses its admitted cost length for two lower-bound checks. Byte pairs prove disjointness for the cost prefix they can actually read.

On Apple M1 with libdeflate 1.26 level 12, the encoder won **76/81 forward and 76/81 in reverse** with 96 balanced blocks per case per order. All 75 protected libdeflate wins and all 81 independent control wins held in both orders.

The freshly matched control won 75 cases forward and 75 in reverse. `16384-distribution-change` took 0.88590% less time across the two orders, with leads of 1.24023% forward and 0.53030% in reverse.

The fixed 18-case average positive gap fell from **3.37119%** to **3.31234%**, a **0.05886 percentage-point** improvement. The largest paired gap moved from 18.38338% to 17.76332%. The worst-order average fell from 3.44728% to 3.33239%.

Matched source-through-executable-link medians were **2.19525 s control**, **2.21456 s candidate** and **0.48150 s libdeflate**.

Candidate encoder text was 65,464 B, lookup data 65,536 B, whole const 80,064 B, stripped executable 276,072 B and peak native stack 4,864 B.

Focused native tests covered wrapping additions, guarded loads and stores, and reuse of a dominating base. The checked short-append fallback remains reachable from all four call sites. Checker and spill-inspection builds reproduced the selected image. The linked gates checked 162 exact outputs and aliases per image, six named errors, 12 recoveries and 324 deployment smoke runs. The release source reproduced the timed object and linked worker byte for byte.

The independently recomputed full timing result has SHA-256 `c5c214535b68867a3c783644737cbc95541e3c57555a81d862b8c66caab3f9bc`.

### Fixed cohort

| Case | Control F/R (ms) | Candidate F/R (ms) | C F/R (ms) | Control paired × C | Candidate paired × C | Improvement (pp) |
|---|---:|---:|---:|---:|---:|---:|
| prefix-random-4096 | 0.088688/0.090166 | 0.088374/0.088875 | 0.075646/0.076230 | 1.18383380 | 1.17763318 | +0.034448 |
| prefix-natural-1024 | 0.066958/0.066917 | 0.066625/0.066708 | 0.059000/0.059042 | 1.14046766 | 1.13538321 | +0.028247 |
| reymont-prefix-1024 | 0.067000/0.066875 | 0.066667/0.066625 | 0.059042/0.059083 | 1.13898376 | 1.13430632 | +0.025986 |
| prefix-random-8192 | 0.138458/0.140416 | 0.139958/0.140000 | 0.124479/0.124834 | 1.12093041 | 1.12716914 | -0.034660 |
| prefix-random-16384 | 0.239791/0.242125 | 0.241667/0.241521 | 0.236437/0.238042 | 1.01579560 | 1.02172870 | -0.032962 |
| 16384-distribution-change | 0.487438/0.491563 | 0.478854/0.481542 | 0.484667/0.484938 | 1.00680337 | 0.99114099 | +0.037797 |
| prefix-random-33027 | 0.523833/0.521959 | 0.520292/0.519437 | 0.531980/0.534708 | 0.97787703 | 0.97245087 | +0.000000 |
| prefix-random-32767 | 0.505562/0.503958 | 0.503208/0.501583 | 0.517334/0.519146 | 0.97140643 | 0.96810043 | +0.000000 |
| random-32769 | 0.516167/0.514458 | 0.514395/0.513126 | 0.528124/0.527334 | 0.97579640 | 0.97154296 | +0.000000 |
| prefix-random-32769 | 0.514229/0.516271 | 0.512292/0.513458 | 0.527541/0.528917 | 0.97527237 | 0.97005369 | +0.000000 |
| prefix-random-32768 | 0.501709/0.503333 | 0.501521/0.501333 | 0.517417/0.519458 | 0.96600124 | 0.96430111 | +0.000000 |
| heldout-random-65537 | 1.111812/1.112416 | 1.109228/1.108063 | 1.148875/1.149250 | 0.96738282 | 0.96246242 | +0.000000 |
| prefix-random-65535 | 1.121375/1.114771 | 1.113229/1.112854 | 1.162042/1.162062 | 0.96183430 | 0.95703217 | +0.000000 |
| prefix-random-65537 | 1.128021/1.123833 | 1.123437/1.120562 | 1.171480/1.172292 | 0.95815005 | 0.95464868 | +0.000000 |
| prefix-random-65536 | 1.114437/1.112646 | 1.111646/1.110146 | 1.161125/1.162167 | 0.95677982 | 0.95497948 | +0.000000 |
| prefix-random-131072 | 2.314521/2.315354 | 2.309584/2.305187 | 2.474166/2.476271 | 0.93399452 | 0.93051667 | +0.000000 |
| prefix-random-262144 | 4.721167/4.729167 | 4.710333/4.706041 | 5.055709/5.057833 | 0.93388118 | 0.92990148 | +0.000000 |
| prefix-random-1048576 | 18.631187/18.653520 | 18.602937/18.600021 | 20.356375/20.365229 | 0.91735399 | 0.91442582 | +0.000000 |

<details><summary>All case margins and exact recipe changes</summary>

| Case | Control F % | Control R % | Candidate F % | Candidate R % |
|---|---:|---:|---:|---:|
| 128-biased-dynamic | -27.885156 | -27.735828 | -27.471045 | -27.321595 |
| 16384-distribution-change | +0.313995 | +1.048018 | -1.240233 | -0.530298 |
| 32-high-entropy-stored | -55.673218 | -55.519952 | -55.476821 | -55.810887 |
| 320-overlap | -7.646652 | -7.449042 | -6.782435 | -6.335274 |
| 33027-periodic-window | -34.490113 | -34.505183 | -34.652172 | -34.678754 |
| eight-literals | -61.242657 | -61.184834 | -61.199977 | -61.213389 |
| eight-literals-prefix | -61.156667 | -61.030105 | -60.901647 | -61.110252 |
| eight-overlap | -29.315292 | -29.398519 | -28.922508 | -29.197248 |
| empty | -99.324968 | -99.324069 | -99.335161 | -99.334764 |
| heldout-mixed-131073 | -18.239232 | -18.280555 | -18.812510 | -18.844569 |
| heldout-random-65537 | -3.307606 | -3.215809 | -3.746097 | -3.761420 |
| heldout-slides-65537 | -19.468563 | -19.615065 | -20.227506 | -20.539329 |
| heldout-window-32767 | -14.417921 | -14.609482 | -15.168235 | -15.493915 |
| heldout-window-32768 | -14.532783 | -14.489586 | -15.201348 | -15.223968 |
| one-stored | -99.328622 | -99.327277 | -99.328670 | -99.299956 |
| prefix-natural-1024 | +14.059670 | +14.033863 | +13.565108 | +13.511540 |
| prefix-natural-1048576 | -28.706397 | -28.694225 | -29.647344 | -29.574936 |
| prefix-natural-131072 | -27.735257 | -27.855216 | -28.843925 | -28.808475 |
| prefix-natural-16384 | -10.319114 | -10.529200 | -10.559180 | -10.637183 |
| prefix-natural-262144 | -28.634619 | -29.015541 | -29.684914 | -29.904124 |
| prefix-natural-32767 | -14.461601 | -14.439925 | -15.207367 | -15.309291 |
| prefix-natural-32768 | -14.484952 | -14.574392 | -15.203558 | -15.352431 |
| prefix-natural-32769 | -14.376247 | -14.413821 | -15.064676 | -15.275088 |
| prefix-natural-33027 | -14.446820 | -14.401762 | -15.124575 | -15.219857 |
| prefix-natural-4096 | -3.840662 | -2.482134 | -4.085240 | -3.456891 |
| prefix-natural-65535 | -19.467771 | -19.963502 | -20.561879 | -20.991120 |
| prefix-natural-65536 | -19.567743 | -19.968871 | -20.615209 | -20.917414 |
| prefix-natural-65537 | -19.472797 | -19.924344 | -20.439349 | -20.982798 |
| prefix-natural-8192 | -4.417094 | -3.960509 | -4.442177 | -4.334567 |
| prefix-periodic-1024 | -18.899627 | -17.977856 | -18.332808 | -17.485209 |
| prefix-periodic-1048576 | -39.097989 | -38.817920 | -39.227119 | -39.052616 |
| prefix-periodic-131072 | -36.642638 | -36.634733 | -36.889397 | -36.836365 |
| prefix-periodic-16384 | -32.657603 | -32.873916 | -32.597838 | -32.809937 |
| prefix-periodic-262144 | -36.993106 | -36.822718 | -37.107294 | -36.978749 |
| prefix-periodic-32767 | -35.337346 | -34.867726 | -35.420119 | -35.097194 |
| prefix-periodic-32768 | -35.567021 | -35.596439 | -35.895126 | -35.813099 |
| prefix-periodic-32769 | -34.197470 | -34.298531 | -34.240084 | -34.515062 |
| prefix-periodic-33027 | -34.267903 | -34.547882 | -34.427305 | -34.654307 |
| prefix-periodic-4096 | -23.840087 | -25.919120 | -23.570217 | -25.226507 |
| prefix-periodic-65535 | -35.761130 | -35.379259 | -35.961288 | -35.823700 |
| prefix-periodic-65536 | -36.116963 | -36.082286 | -36.294695 | -36.401229 |
| prefix-periodic-65537 | -35.221990 | -34.906062 | -35.457764 | -35.224303 |
| prefix-periodic-8192 | -29.007027 | -29.551123 | -29.486678 | -29.387991 |
| prefix-random-1024 | -22.298244 | -22.386066 | -22.105807 | -22.268007 |
| prefix-random-1048576 | -8.501317 | -8.027272 | -8.611432 | -8.503372 |
| prefix-random-131072 | -6.668495 | -6.532552 | -7.027444 | -6.869155 |
| prefix-random-16384 | +1.706548 | +1.452730 | +2.337537 | +2.008468 |
| prefix-random-262144 | -6.782564 | -6.440887 | -7.115359 | -6.904225 |
| prefix-random-32767 | -2.709872 | -3.008613 | -3.144103 | -3.235789 |
| prefix-random-32768 | -3.338121 | -3.461592 | -3.383347 | -3.756071 |
| prefix-random-32769 | -2.661538 | -2.283623 | -3.109438 | -2.879687 |
| prefix-random-33027 | -1.938592 | -2.485238 | -2.679583 | -2.830185 |
| prefix-random-4096 | +18.132558 | +18.634734 | +17.716435 | +17.810221 |
| prefix-random-65535 | -3.783828 | -3.849301 | -4.407534 | -4.185903 |
| prefix-random-65536 | -4.365555 | -4.278461 | -4.619904 | -4.384054 |
| prefix-random-65537 | -4.324421 | -4.045367 | -4.575649 | -4.494597 |
| prefix-random-8192 | +11.506186 | +12.682984 | +12.671890 | +12.761956 |
| prefix-repeated-1024 | -22.060016 | -22.332713 | -22.039920 | -21.950259 |
| prefix-repeated-1048576 | -26.032867 | -25.872655 | -26.208098 | -25.938057 |
| prefix-repeated-131072 | -23.232167 | -23.360097 | -23.378110 | -23.555371 |
| prefix-repeated-16384 | -21.366786 | -20.904674 | -21.424988 | -21.239870 |
| prefix-repeated-262144 | -23.667942 | -23.363976 | -23.751104 | -23.730524 |
| prefix-repeated-32767 | -23.356736 | -23.032045 | -23.445537 | -22.903865 |
| prefix-repeated-32768 | -22.625511 | -22.648511 | -22.873169 | -22.739246 |
| prefix-repeated-32769 | -22.158352 | -22.257613 | -22.488312 | -22.703714 |
| prefix-repeated-33027 | -22.505991 | -22.587338 | -22.737985 | -23.017454 |
| prefix-repeated-4096 | -17.283405 | -16.624172 | -17.649714 | -16.442658 |
| prefix-repeated-65535 | -23.834546 | -23.547667 | -23.993103 | -23.932979 |
| prefix-repeated-65536 | -23.041863 | -23.112449 | -23.427916 | -23.429854 |
| prefix-repeated-65537 | -23.080814 | -23.832117 | -23.263410 | -23.906466 |
| prefix-repeated-8192 | -20.598846 | -19.539077 | -20.335160 | -19.506945 |
| random-1024 | -23.203049 | -22.830275 | -22.728780 | -22.593639 |
| random-256 | -33.845773 | -33.622587 | -33.154019 | -33.316026 |
| random-32769 | -2.524515 | -2.316094 | -2.832459 | -2.858947 |
| random-64 | -51.218561 | -51.429859 | -51.222170 | -51.404474 |
| repeated-1024 | -22.107094 | -22.413382 | -21.840617 | -21.712133 |
| repeated-32769 | -22.359090 | -22.600097 | -22.815049 | -22.361705 |
| reymont-prefix-1024 | +13.919084 | +13.877672 | +13.353078 | +13.508239 |
| reymont-prefix-16384 | -10.585038 | -10.619115 | -10.830545 | -10.791075 |
| reymont-prefix-32769 | -14.472587 | -14.412538 | -15.222440 | -15.270225 |
| seven-stored-prefix | -99.273564 | -99.221956 | -99.269056 | -99.265399 |

Start with the previous qualified recipe and build the original codec using this commit. Set the flags below and replace the scorer register and block profiles. [Previous recipe](https://github.com/mech-lang/mech/pull/999#issuecomment-7107987476)

```sh
export MECH_COMPACT_INLINE_SHORT_BYTE_APPENDS=1
export MECH_COMPACT_HOIST_INDEXED_LOAD_BASES=mech_compact_numeric_3009_no_growth_composed
export MECH_COMPOSE_FOLD_ADMITTED_COST_MINIMUM=1
export MECH_GROUPED_LITERAL_PREFIX_SPAN=1
```

Capture the pre-allocation VCode for `mech_compact_numeric_3009_no_growth_composed` with its existing profile entries removed. Use the text between the register-allocation markers as `expected_vcode` and the first JSON object for its hash and frequencies. Use the second object as the scorer block layout.

```json
{"expected_vcode_sha256":"06cde8f81ab484c59c491305fcd3be42c51b1b4d32ded4c05d2ee8867aa4e211","block_frequencies":[2,2,2,2,2,125,125,125,125,125,125,125,125,125,125,125,2,2,123,123,123,123,123,123,123,123,123,123,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,1,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,98,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,1,1,1,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,1,1,1,1,184,184,184,184,184,184,184,184,184,162,25,162,162,184,42,22,3,20,17,3,19,11,7,19,78,78,19,22,184,16,178,178,178,184,184,184,184,184,184,184,184,184,184,123,184,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,98,25,98,98,98,98,98,98,98,98,98,98,98,98,98,98,25,4096,35,4096,35,4072,4072,4072,4096,35,35,35,25,34,25,10,10,1,10,25,25,10]}
{"order":[0,104,116,1152,1232,1372,1392,216,224,228,244,252,256,260,304,332,340,344,372,380,432,312,320,1128,1144,1208,132,136,484,1080,1124,388,512,712,732,828,872,992,1028,1052,1492,1508,1560,1472,1476,1512,520,576,644,744,656,1604,1612,1628,1636,1644,1652,1704,1716,1720,1724],"literal_offset":1728,"thread_jumps":true}
```

The selected object has SHA-256 `36afdbc14d93735dc1c55eb94839fde7b11086f142605c52ea3085464add85e1`. Canonical bytecode has SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.

</details>
