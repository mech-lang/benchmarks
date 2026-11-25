@codex review

Please review [commit `47f8d5d3f1fa7ac0dc23637df66a1417c3234bd7`](https://github.com/mech-lang/mech/commit/47f8d5d3f1fa7ac0dc23637df66a1417c3234bd7).

The paired literal loop admits a full byte-indexed cost span at entry. A mask then checks both selectors and the upper bits of both literal indices together. Rejected pairs resume the checked scalar route with the same state and unwritten output. The timed recipe also uses the direct immutable cost-code table.

On Apple M1 with libdeflate 1.26 level 12, the encoder won **75/81 forward and 75/81 in reverse** in the full run with 96 balanced blocks per case per order. All 75 protected libdeflate wins and all 81 independent control wins held in both orders.

The freshly matched control also won 75 cases in each order. The closest remaining case, `16384-distribution-change`, was 0.72% behind libdeflate across the two orders and 0.52% and 0.92% behind in the individual runs.

The fixed 18-case average positive gap fell from **4.51290%** to **3.95373%**, a **0.55917 percentage-point** improvement. The largest paired gap moved from 23.81653% to 22.99982%. The worst-order average fell from 4.62131% to 4.02879%.

Matched source-through-executable-link medians were **2.20351 s control**, **2.20705 s candidate** and **0.48142 s libdeflate**.

Candidate encoder text was 65,176 B, lookup data 65,536 B, whole const 80,064 B, stripped executable 276,072 B and peak native stack 4,880 B.

Focused native tests covered the 255/256 literal boundary, short cost spans, wrapping biased costs, ordered errors, scalar tails, and overlapping and adjacent views. Checker and spill-inspection builds reproduced the selected image. The linked gates checked 162 exact outputs and aliases per image, six named errors, 12 recoveries and 324 deployment smoke runs. The release source reproduced the timed object and linked worker byte for byte.

The independently recomputed full timing result has SHA-256 `556cb1d7918fc190b5ac5c9528e08d2fa508f3d98db7e21ad62729f3ba71c4b6`.

### Fixed cohort

| Case | Control F/R (ms) | Candidate F/R (ms) | C F/R (ms) | Control paired × C | Candidate paired × C | Improvement (pp) |
|---|---:|---:|---:|---:|---:|---:|
| prefix-random-4096 | 0.093500/0.095125 | 0.093041/0.093417 | 0.076084/0.076229 | 1.23816529 | 1.22999816 | +0.045373 |
| prefix-random-8192 | 0.145666/0.147312 | 0.143625/0.144041 | 0.125396/0.125229 | 1.17465487 | 1.15393034 | +0.115136 |
| reymont-prefix-1024 | 0.068458/0.068334 | 0.067125/0.067042 | 0.059125/0.058959 | 1.16533170 | 1.14722702 | +0.100582 |
| prefix-natural-1024 | 0.068166/0.068334 | 0.066958/0.067167 | 0.059041/0.059000 | 1.16218407 | 1.14228384 | +0.110557 |
| prefix-random-16384 | 0.249396/0.250042 | 0.244208/0.243958 | 0.237500/0.237625 | 1.05239240 | 1.03103602 | +0.118647 |
| 16384-distribution-change | 0.493938/0.493875 | 0.489396/0.488750 | 0.483458/0.483291 | 1.01959278 | 1.00719568 | +0.068873 |
| prefix-random-33027 | 0.532917/0.529751 | 0.526999/0.517812 | 0.533895/0.534271 | 0.99239016 | 0.97679532 | +0.000000 |
| prefix-random-32767 | 0.514041/0.513042 | 0.507438/0.504000 | 0.519063/0.519896 | 0.98829985 | 0.97193753 | +0.000000 |
| random-32769 | 0.527208/0.520291 | 0.518125/0.509979 | 0.527479/0.527188 | 0.99166681 | 0.97461383 | +0.000000 |
| prefix-random-32769 | 0.525020/0.523770 | 0.519395/0.512104 | 0.527605/0.528688 | 0.98926231 | 0.97347431 | +0.000000 |
| prefix-random-32768 | 0.512146/0.510354 | 0.504438/0.501146 | 0.518292/0.520042 | 0.98405022 | 0.96855348 | +0.000000 |
| heldout-random-65537 | 1.130708/1.125626 | 1.115355/1.106416 | 1.148813/1.152562 | 0.98040969 | 0.96418303 | +0.000000 |
| prefix-random-65535 | 1.138729/1.131334 | 1.122167/1.112291 | 1.163146/1.163272 | 0.97626650 | 0.95919283 | +0.000000 |
| prefix-random-65537 | 1.143854/1.138833 | 1.128041/1.122875 | 1.170188/1.172166 | 0.97287756 | 0.95860778 | +0.000000 |
| prefix-random-65536 | 1.133187/1.127563 | 1.114583/1.110188 | 1.161542/1.163938 | 0.97050286 | 0.95538621 | +0.000000 |
| prefix-random-131072 | 2.350250/2.345583 | 2.318229/2.304416 | 2.471708/2.475542 | 0.94812779 | 0.93263040 | +0.000000 |
| prefix-random-262144 | 4.793251/4.784604 | 4.722626/4.709750 | 5.062542/5.053896 | 0.94623164 | 0.93214287 | +0.000000 |
| prefix-random-1048576 | 18.913771/18.910979 | 18.637041/18.640458 | 20.365730/20.359438 | 0.92979261 | 0.91557739 | +0.000000 |

<details><summary>All case margins and exact recipe changes</summary>

| Case | Control F % | Control R % | Candidate F % | Candidate R % |
|---|---:|---:|---:|---:|
| 128-biased-dynamic | -27.196540 | -27.568659 | -27.178554 | -27.468875 |
| 16384-distribution-change | +1.864136 | +2.054509 | +0.524404 | +0.915110 |
| 32-high-entropy-stored | -55.747419 | -55.456284 | -55.518672 | -55.662843 |
| 320-overlap | -7.429449 | -6.980525 | -7.587094 | -7.253984 |
| 33027-periodic-window | -32.586018 | -33.260592 | -33.697850 | -34.351261 |
| eight-literals | -61.475950 | -61.178307 | -61.500982 | -61.205072 |
| eight-literals-prefix | -61.355601 | -61.145362 | -61.277246 | -61.107565 |
| eight-overlap | -28.976027 | -29.245917 | -29.251338 | -29.339809 |
| empty | -99.334591 | -99.341793 | -99.324418 | -99.320475 |
| heldout-mixed-131073 | -16.444396 | -16.459335 | -18.303327 | -18.319343 |
| heldout-random-65537 | -1.852572 | -2.065374 | -3.243380 | -3.918832 |
| heldout-slides-65537 | -17.824357 | -18.082598 | -19.380415 | -19.716349 |
| heldout-window-32767 | -12.437009 | -12.610967 | -14.434689 | -14.619105 |
| heldout-window-32768 | -12.412823 | -12.619547 | -14.430989 | -14.578312 |
| one-stored | -99.303092 | -99.321048 | -99.319908 | -99.310539 |
| prefix-natural-1024 | +16.147913 | +16.288943 | +13.989260 | +14.468011 |
| prefix-natural-1048576 | -27.386565 | -27.361295 | -28.701469 | -28.650459 |
| prefix-natural-131072 | -26.196145 | -26.231922 | -27.606372 | -27.799960 |
| prefix-natural-16384 | -8.228113 | -8.211410 | -10.528614 | -10.362913 |
| prefix-natural-262144 | -27.271729 | -27.556261 | -28.568818 | -29.043926 |
| prefix-natural-32767 | -12.632484 | -12.647994 | -14.521953 | -14.614663 |
| prefix-natural-32768 | -12.496933 | -12.672927 | -14.419905 | -14.682391 |
| prefix-natural-32769 | -12.429952 | -12.462008 | -14.429487 | -14.365392 |
| prefix-natural-33027 | -12.314427 | -12.436377 | -14.359814 | -14.465253 |
| prefix-natural-4096 | -1.421277 | -0.820014 | -3.789848 | -3.561007 |
| prefix-natural-65535 | -17.465692 | -18.140847 | -19.342964 | -19.986086 |
| prefix-natural-65536 | -17.493134 | -18.002398 | -19.543709 | -19.959075 |
| prefix-natural-65537 | -17.500982 | -18.059859 | -19.403312 | -19.960089 |
| prefix-natural-8192 | -1.735714 | -1.363223 | -4.134027 | -3.758135 |
| prefix-periodic-1024 | -17.393677 | -17.639231 | -18.232358 | -18.340143 |
| prefix-periodic-1048576 | -37.754354 | -37.679033 | -38.985530 | -38.843488 |
| prefix-periodic-131072 | -35.496755 | -35.508397 | -36.471049 | -36.614492 |
| prefix-periodic-16384 | -31.140931 | -31.195555 | -32.685289 | -32.814159 |
| prefix-periodic-262144 | -35.763918 | -35.782980 | -36.892833 | -36.917663 |
| prefix-periodic-32767 | -33.694078 | -33.606134 | -35.130628 | -34.768532 |
| prefix-periodic-32768 | -34.077472 | -34.514001 | -35.601610 | -35.566719 |
| prefix-periodic-32769 | -32.433525 | -32.583323 | -34.020254 | -33.774485 |
| prefix-periodic-33027 | -32.783779 | -33.036932 | -34.356646 | -34.168922 |
| prefix-periodic-4096 | -23.150917 | -22.367700 | -25.300049 | -23.633024 |
| prefix-periodic-65535 | -34.245428 | -34.110564 | -35.473237 | -35.352734 |
| prefix-periodic-65536 | -34.755409 | -34.944434 | -36.192195 | -36.059008 |
| prefix-periodic-65537 | -33.811777 | -33.803178 | -34.901469 | -34.981377 |
| prefix-periodic-8192 | -28.257289 | -27.679251 | -30.042869 | -29.649468 |
| prefix-random-1024 | -22.048769 | -22.134846 | -21.949012 | -21.773486 |
| prefix-random-1048576 | -7.043066 | -6.998407 | -8.454886 | -8.429635 |
| prefix-random-131072 | -5.030098 | -5.344083 | -6.420810 | -7.052041 |
| prefix-random-16384 | +5.201877 | +5.276615 | +2.998107 | +3.209206 |
| prefix-random-262144 | -5.472683 | -5.280893 | -6.818215 | -6.753201 |
| prefix-random-32767 | -1.079162 | -1.260783 | -2.445361 | -3.165798 |
| prefix-random-32768 | -1.124125 | -2.063589 | -2.773290 | -3.514594 |
| prefix-random-32769 | -0.792693 | -1.354049 | -2.089005 | -3.212890 |
| prefix-random-33027 | -0.337522 | -1.182646 | -1.542919 | -3.091876 |
| prefix-random-4096 | +23.422370 | +24.211947 | +22.723050 | +23.277206 |
| prefix-random-65535 | -2.348638 | -2.398057 | -3.711278 | -4.448738 |
| prefix-random-65536 | -2.688452 | -3.210274 | -4.256168 | -4.666151 |
| prefix-random-65537 | -2.668989 | -2.755480 | -3.968489 | -4.309651 |
| prefix-random-8192 | +16.249700 | +18.693989 | +15.188727 | +15.597704 |
| prefix-repeated-1024 | -21.490122 | -20.899261 | -22.272078 | -22.002742 |
| prefix-repeated-1048576 | -25.022370 | -24.774444 | -26.113957 | -25.779494 |
| prefix-repeated-131072 | -22.198446 | -22.178662 | -23.249666 | -23.176639 |
| prefix-repeated-16384 | -19.427809 | -19.741716 | -20.840172 | -20.713297 |
| prefix-repeated-262144 | -22.620565 | -22.646515 | -23.644101 | -23.615955 |
| prefix-repeated-32767 | -21.891036 | -22.162378 | -23.104266 | -23.040802 |
| prefix-repeated-32768 | -21.378498 | -21.455565 | -22.723134 | -22.349532 |
| prefix-repeated-32769 | -21.447376 | -21.085397 | -22.560360 | -22.020375 |
| prefix-repeated-33027 | -21.180126 | -21.702050 | -22.503606 | -22.548966 |
| prefix-repeated-4096 | -15.457806 | -15.559127 | -17.315678 | -16.229788 |
| prefix-repeated-65535 | -22.870665 | -22.397635 | -23.822000 | -23.267687 |
| prefix-repeated-65536 | -22.182018 | -22.130049 | -23.257851 | -23.019909 |
| prefix-repeated-65537 | -22.405536 | -22.432420 | -23.369279 | -23.365695 |
| prefix-repeated-8192 | -18.568587 | -17.792596 | -20.251010 | -19.338893 |
| random-1024 | -22.402221 | -23.047033 | -22.235530 | -22.961860 |
| random-256 | -33.382462 | -33.942893 | -32.966982 | -33.428888 |
| random-32769 | -0.177033 | -1.485291 | -1.965478 | -3.108405 |
| random-64 | -51.403754 | -51.424410 | -51.180325 | -51.597465 |
| repeated-1024 | -21.269904 | -21.410130 | -22.222743 | -22.460680 |
| repeated-32769 | -21.224618 | -21.828188 | -22.411719 | -22.581569 |
| reymont-prefix-1024 | +16.657507 | +16.408966 | +15.050914 | +14.395425 |
| reymont-prefix-16384 | -8.251305 | -8.142184 | -10.500253 | -10.232341 |
| reymont-prefix-32769 | -12.524250 | -12.580645 | -14.474318 | -14.540490 |
| seven-stored-prefix | -99.276984 | -99.274123 | -99.278245 | -99.212729 |

Start with the previous qualified recipe and build the original codec using this commit. Enable the grouped byte check, remove the optional page-shift setting for the immutable cost codes, and replace the scorer register and block profiles. [Previous recipe](https://github.com/mech-lang/mech/pull/999#issuecomment-7105213384)

```sh
export MECH_CHECK_GROUPED_LITERAL_BYTES=1
unset MECH_COMPOSE_IMMUTABLE_COST_CODE_PAGE_SHIFT
```

Capture the pre-allocation VCode for `mech_compact_numeric_3009_no_growth_composed` with its existing profile entries removed. Use the text between the register-allocation markers as `expected_vcode` and the first JSON object for its hash and frequencies. Use the second object as the scorer block layout.

```json
{"expected_vcode_sha256":"0eefa35bee7a8ee98622f1c43fb92a03b0c011555bc379e7ea16fbb56ce1f9d7","block_frequencies":[2,2,2,2,2,125,125,125,125,125,125,125,125,125,125,125,2,2,123,123,123,123,123,123,123,123,123,123,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,1,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,1,1,1,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,98,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,1,1,1,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,184,1,1,1,1,184,184,184,184,184,184,184,184,184,162,25,162,162,184,42,22,3,20,17,3,19,11,7,19,78,78,19,22,184,16,178,178,178,184,184,184,184,184,184,184,184,184,184,123,184,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,123,98,25,98,98,98,98,98,98,98,98,98,98,98,98,98,98,25,4096,35,4096,35,4072,4072,4072,4096,35,35,35,25,34,25,10,10,1,10,25,25,10]}
{"order":[0,100,112,1144,1224,1408,1428,208,216,220,236,244,248,252,292,320,328,332,364,372,424,300,308,1120,1136,1200,128,132,476,1072,1116,380,504,704,724,820,864,984,1020,1044,1532,1548,1600,1512,1516,1552,512,568,636,736,648,1644,1652,1668,1676,1684,1692,1744,1756],"literal_offset":1760,"thread_jumps":true}
```

The selected object has SHA-256 `6d97f23a097d8d556866c4a171e12d0e0ff0964461adc69f4affd8ec85e16c81`. Canonical bytecode has SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.

</details>
