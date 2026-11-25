## Selected decreasing sorter indices

The compiler proves loop indices stay below the captured end by checking all incoming loop arguments and each unsigned subtraction. The existing fixed writable capacity gate also checks the end against the current length. A failed admission reaches the checked continuation. The admitted sorter removes three comparisons and shrinks from 336 B to 272 B. [Source](https://github.com/mech-lang/mech/commit/29b13a3f74fef2636d4acd76bc43a21ec28f730e)

The fixed 18-case mean positive slowdown fell from **9.382042%** to **8.853314%**, a reduction of **0.528727 percentage points**. The average using each case’s slower order fell from 9.645631% to 9.043245%. The maximum paired gap fell from 30.312457% to 28.085307%.

| Order | Matched Mech control wins vs libdeflate | Candidate wins vs libdeflate |
|---|---:|---:|
| Forward | 65/81 | 66/81 |
| Reverse | 66/81 | 66/81 |

Every protected win held. Random 128 KiB took 0.090% and 0.152% less time than libdeflate in forward and reverse order. Random 256 KiB took 0.252% and 0.290% less time. The certified floor is 66 named libdeflate wins in both orders. The full runs used 96 balanced blocks on the original 81 fixtures against pinned libdeflate 1.26 level 12 on Apple M1. The verifier recomputed 1,965,312 observations.

The native gates passed 162 exact output and alias checks, six checked errors and 12 recovery pairs. Peak stack was 4,720 B against the 5,280 B cap. Encoder text was 63,272 B, lookup data 3,200 B, the whole constants section 17,728 B and the stripped executable 210,024 B. Median source-through-link times were 2.188 s for the candidate, 2.189 s for the matched Mech control and 0.483 s for libdeflate. The build study timed 32 builds and passed 324 deployment inflation checks.

<details>
<summary>Fixed 18-case qualification</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Contribution improvement pp |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.316768 / 1.289622 | 1.280867 / 1.280839 | 0.099417 / 0.097833 | 0.097062 / 0.096209 | 0.075791 / 0.076000 | +0.123731 |
| `prefix-random-8192` | 1.249934 / 1.236898 | 1.235545 / 1.204873 | 0.156855 / 0.154625 | 0.154458 / 0.150187 | 0.125229 / 0.125479 | +0.129367 |
| `prefix-natural-1024` | 1.193294 / 1.194238 | 1.189028 / 1.188352 | 0.070125 / 0.070125 | 0.069833 / 0.069750 | 0.059000 / 0.058959 | +0.028201 |
| `reymont-prefix-1024` | 1.192496 / 1.194145 | 1.191844 / 1.187469 | 0.070125 / 0.070125 | 0.069750 / 0.069750 | 0.059000 / 0.059000 | +0.020364 |
| `16384-distribution-change` | 1.144029 / 1.158525 | 1.148788 / 1.158899 | 0.554625 / 0.560021 | 0.556105 / 0.559979 | 0.484292 / 0.483000 | -0.014325 |
| `prefix-random-16384` | 1.145156 / 1.137277 | 1.129301 / 1.128972 | 0.272479 / 0.269021 | 0.268437 / 0.266666 | 0.237521 / 0.237209 | +0.067074 |
| `prefix-random-33027` | 1.068021 / 1.064623 | 1.064588 / 1.061050 | 0.570833 / 0.569354 | 0.570312 / 0.565917 | 0.532479 / 0.532645 | +0.019461 |
| `random-32769` | 1.062312 / 1.067131 | 1.057632 / 1.061543 | 0.561437 / 0.561708 | 0.558645 / 0.559770 | 0.527041 / 0.526208 | +0.028517 |
| `prefix-random-32769` | 1.062254 / 1.064163 | 1.058866 / 1.057769 | 0.562021 / 0.561312 | 0.560437 / 0.558104 | 0.526646 / 0.526833 | +0.027169 |
| `prefix-random-32767` | 1.061350 / 1.064636 | 1.060901 / 1.059135 | 0.552584 / 0.550313 | 0.551021 / 0.547500 | 0.517813 / 0.517167 | +0.016521 |
| `prefix-random-32768` | 1.064230 / 1.059335 | 1.058330 / 1.054446 | 0.551229 / 0.549312 | 0.548875 / 0.544875 | 0.516875 / 0.517188 | +0.029963 |
| `heldout-random-65537` | 1.044179 / 1.044202 | 1.042783 / 1.040506 | 1.197771 / 1.199292 | 1.198750 / 1.197396 | 1.145396 / 1.150000 | +0.014147 |
| `prefix-random-65537` | 1.031602 / 1.036295 | 1.030889 / 1.032618 | 1.212771 / 1.214375 | 1.214125 / 1.213021 | 1.170416 / 1.170854 | +0.012180 |
| `prefix-random-65535` | 1.032921 / 1.034882 | 1.030009 / 1.032033 | 1.202208 / 1.204292 | 1.201792 / 1.201500 | 1.161813 / 1.162791 | +0.016002 |
| `prefix-random-65536` | 1.029945 / 1.033334 | 1.028912 / 1.030637 | 1.200584 / 1.201917 | 1.201020 / 1.198688 | 1.162167 / 1.162938 | +0.010356 |
| `prefix-random-131072` | 1.000553 / 0.999275 | 0.999100 / 0.998475 | 2.481730 / 2.477833 | 2.480708 / 2.476521 | 2.476354 / 2.475667 | +0.000000 |
| `prefix-random-262144` | 0.998861 / 0.998671 | 0.997483 / 0.997103 | 5.058958 / 5.057229 | 5.054604 / 5.057834 | 5.053667 / 5.059062 | +0.000000 |
| `prefix-random-1048576` | 0.980118 / 0.980989 | 0.980127 / 0.980297 | 19.939417 / 19.933417 | 19.924895 / 19.923917 | 20.342292 / 20.358875 | +0.000000 |

</details>

<details>
<summary>Source replay</summary>

Build the compiler from `29b13a3f74fef2636d4acd76bc43a21ec28f730e` and start with the earlier `byte-sixteen` recipe. Set `MECH_COMPACT_ADMIT_DECREASING_INDICES=mech_compact_numeric_3956_vector` and replace that sorter's entry in `MECH_COMPACT_PHASE_BLOCK_LAYOUT` with the profile derived from block counts on the original 18 cases.

```json
{
  "order": [
    0,
    208,
    212,
    232,
    236,
    252,
    168,
    188,
    196,
    200,
    244,
    68,
    160,
    220,
    176,
    152,
    40,
    76,
    84,
    64
  ],
  "literal_offset": null,
  "thread_jumps": true
}
```

- Profile SHA-256 `d670454109123fb17854ee27728b8a2ee21c681d6704cadf167ae473167c16d4`
- `program.o` SHA-256 `23a7c723474469ce4a019d11bd016dd8f8ca0ed6fdb91f0f26175ea4a36b23fd`
- `metadata.json` SHA-256 `15026c3a2dd98ae6f317a45d6a1b6b479013ab0277ad5376d3d44566fa6b3fbd`
- `program.mecb` SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`
- `compile_profile` SHA-256 `b2f03d738cecec6fadf0e827281fcd48ba3dc0cf2a197100fbd3f1020a45a3c2`
- Evidence archive SHA-256 `9d5ca1508d10487d4cd62484284a1f26dafffd537f7a16dc8f5b1bc86e0f7390` for 1,100 verified files

</details>

## Earlier qualification of `byte-sixteen`

`byte-sixteen` was qualified at `c8ec66b97e088d19bf43c1342cd97ba644ce392b`. For an admitted key mask of 255, the compiler extracts the low byte of each shifted vector lane and zero-extends it into the bin index. Wider keys still use the full masked lane. The stream checks the entire group before incrementing its bins in source order. [Source](https://github.com/mech-lang/mech/commit/c8ec66b97e088d19bf43c1342cd97ba644ce392b)

The mean positive slowdown across the original 18 cases fell from **9.59292%** to **9.20504%**, a reduction of **0.38788 percentage points**. The maximum gap fell from 28.50406% to 27.25726%.

| Order | Wins vs libdeflate | Missing protected wins |
|---|---:|---|
| Forward | 64/81 | None |
| Reverse | 66/81 | None |

Random 128 KiB took 0.099% longer in forward order and 0.138% less time in reverse. Random 256 KiB took 0.121% longer in forward order and 0.207% less time in reverse. The shared protected floor is 64 libdeflate wins. Both full orders used 96 balanced blocks on the original 81 fixtures with the pinned libdeflate 1.26 level-12 build on Apple M1. The verifier recomputed 1,965,312 observations.

The diagnostic packed-node histogram retired 196,107 fewer instructions on random 256 KiB. Four focused native tests covered byte and wider keys, mixed groups, wraparound, and disjoint and overlapping views. The differential and alias tests exercised 2,077,920 and 1,260 calls, respectively.

Encoder text is 63,288 B, lookup data 3,200 B, the whole constants section 17,728 B and the stripped executable 210,024 B. Peak stack is 4,832 B against the 5,280 B cap.

Complete source-through-link medians were 2.185 s for the candidate, 2.186 s for the matched control and 0.480 s for libdeflate. The 32 timed builds passed 324 deployment inflation checks. The linked worker passed 162 exact output and alias checks, six named errors and 12 recovery pairs.

<details>
<summary>Fixed 18-case qualification</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Contribution improvement pp |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.261265 / 1.309265 | 1.258535 / 1.286767 | 0.096875 / 0.099271 | 0.097104 / 0.097229 | 0.077583 / 0.076083 | +0.069267 |
| `prefix-random-8192` | 1.218320 / 1.243837 | 1.219621 / 1.240523 | 0.153437 / 0.155458 | 0.152874 / 0.153937 | 0.126271 / 0.125375 | +0.005470 |
| `reymont-prefix-1024` | 1.196631 / 1.196887 | 1.197913 / 1.194780 | 0.070250 / 0.070375 | 0.070291 / 0.070125 | 0.058958 / 0.059000 | +0.002295 |
| `prefix-natural-1024` | 1.199151 / 1.195333 | 1.195775 / 1.192096 | 0.070333 / 0.070291 | 0.070250 / 0.070042 | 0.059000 / 0.059000 | +0.018369 |
| `16384-distribution-change` | 1.153174 / 1.157574 | 1.159512 / 1.153038 | 0.557520 / 0.558813 | 0.561937 / 0.555479 | 0.483249 / 0.483125 | -0.004990 |
| `prefix-random-16384` | 1.146321 / 1.141737 | 1.134179 / 1.138201 | 0.272292 / 0.270520 | 0.269645 / 0.269292 | 0.237333 / 0.237187 | +0.043548 |
| `random-32769` | 1.076522 / 1.066248 | 1.071414 / 1.063877 | 0.567250 / 0.562229 | 0.564604 / 0.561229 | 0.525791 / 0.526938 | +0.020742 |
| `prefix-random-33027` | 1.071856 / 1.071751 | 1.068452 / 1.066067 | 0.573125 / 0.573209 | 0.571083 / 0.569333 | 0.532792 / 0.534042 | +0.025248 |
| `prefix-random-32769` | 1.067611 / 1.068554 | 1.067147 / 1.062936 | 0.564854 / 0.564541 | 0.565396 / 0.561479 | 0.528021 / 0.528291 | +0.016906 |
| `prefix-random-32767` | 1.064485 / 1.070040 | 1.064384 / 1.065392 | 0.552938 / 0.554001 | 0.553229 / 0.552187 | 0.518333 / 0.518250 | +0.013173 |
| `prefix-random-32768` | 1.064626 / 1.061094 | 1.061570 / 1.056780 | 0.551813 / 0.551562 | 0.552167 / 0.549104 | 0.517771 / 0.518750 | +0.020478 |
| `heldout-random-65537` | 1.047876 / 1.050524 | 1.043680 / 1.044459 | 1.206667 / 1.205896 | 1.203958 / 1.197666 | 1.148937 / 1.146666 | +0.028499 |
| `prefix-random-65537` | 1.039287 / 1.039268 | 1.035869 / 1.033962 | 1.236916 / 1.217875 | 1.230021 / 1.212458 | 1.187000 / 1.171000 | +0.024234 |
| `prefix-random-65536` | 1.039447 / 1.040320 | 1.034886 / 1.033835 | 1.210396 / 1.205625 | 1.207146 / 1.201708 | 1.162959 / 1.161312 | +0.030684 |
| `prefix-random-65535` | 1.037519 / 1.040742 | 1.034931 / 1.033521 | 1.208333 / 1.208166 | 1.207083 / 1.200541 | 1.160250 / 1.160625 | +0.027244 |
| `prefix-random-131072` | 1.006449 / 1.003157 | 1.000989 / 0.998623 | 2.490000 / 2.484646 | 2.478792 / 2.472729 | 2.472021 / 2.474105 | +0.026675 |
| `prefix-random-262144` | 1.004313 / 1.002903 | 1.001206 / 0.997932 | 5.081292 / 5.072875 | 5.059521 / 5.045375 | 5.059063 / 5.056604 | +0.020041 |
| `prefix-random-1048576` | 0.984248 / 0.982432 | 0.979505 / 0.979060 | 19.993229 / 19.983396 | 19.920624 / 19.921021 | 20.358105 / 20.361750 | +0.000000 |

</details>

<details>
<summary>Discovery comparisons</summary>

The discovery panel covered all 18 original losses and seven protected cases with 24 balanced blocks per order. The paired stream checks two adjacent four-record vectors together and commits a complete first vector when only the second has mixed tags. The 16-visit paired byte build won random 256 KiB in both discovery orders and reproduced its exact artifact hashes.

| Recipe | Mean gap before | Mean gap after | Improvement (pp) |
|---|---:|---:|---:|
| `byte-sixteen` | 9.57502% | 9.20136% | +0.37366 |
| `byte-eight` | 9.67365% | 9.29365% | +0.38000 |
| `paired-byte-sixteen` | 9.37402% | 9.23497% | +0.13905 |
| `paired-byte` | 9.26327% | 9.33453% | -0.07125 |
| `paired` | 9.67728% | 9.85119% | -0.17391 |

</details>

<details>
<summary>Source replay</summary>

Build the compiler from `c8ec66b97e088d19bf43c1342cd97ba644ce392b`. Use the earlier `vector-stream-eight` recipe and its layout profiles with these two overrides.

```sh
export MECH_GROUP_PACKED_HISTOGRAM_VISITS=16
export MECH_GROUP_PACKED_HISTOGRAM_BYTE_KEYS=1
```

- `program.o` SHA-256 `06fba2dda46d0fb1a0a0bf5e4fe0318d4d6d6e2d6de0e3c709cb78559d1595f6`
- `metadata.json` SHA-256 `fd3ed1cf05dc51f2c6e51f8aa1430aab18a004e35128decd66a95d918dfbb84b`
- `program.mecb` SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`
- `compile_profile` SHA-256 `a5cbe9b9b478fa7bbc6fb0002ea9004a957fec9fe3e00d4e9ae42287eb656598`
- Evidence archive SHA-256 `774862c60675f078ce9e1b5f4977bfb1d08ccc31029cdaacd39ae4481ec72455` for 988 verified files

</details>

## Earlier qualification of `vector-stream-eight`

`vector-stream-eight` was selected at `d4625ab975e85b6d15330b9f736d2635f82d3974`. The checked prefix commits its first four literal visits. The compiler bounds the stream by the remaining iterations and the initialized node extent. AArch64 checks four packed tags at a time and applies increments in source order. On a mixed group, the checked loop resumes at the first uncommitted visit. [Source](https://github.com/mech-lang/mech/commit/d4625ab975e85b6d15330b9f736d2635f82d3974)

The mean positive slowdown across the original 18 names fell from **10.96547%** to **9.01864%**, a reduction of **1.94682 percentage points**. The maximum gap fell from 29.36823% to 25.40343%.

| Order | Wins vs libdeflate | Missing protected wins |
|---|---:|---|
| Forward | 64/81 | None |
| Reverse | 64/81 | None |

Both orders used 96 balanced blocks on the original 81 fixtures with the pinned libdeflate 1.26 level-12 build on Apple M1. The verifier recomputed 1,965,312 observations for each full candidate. The first attempt ended mid-order. Both complete comparisons restarted with RAM-backed output and logs.

Random 256 KiB is the closest remaining case at **1.003417× / 1.001848× libdeflate** in forward and reverse order. A further **0.341%** reduction in elapsed time would put the slower order at parity. The 16-visit alternative gained 1.53259 percentage points against its own matched control and won 66/81 forward and 64/81 reverse. It preserved every protected win. The eight-visit build delivered the larger matched improvement in discovery and qualification.

The diagnostic packed-node histogram retired 3,222,547 fewer instructions and made 391,788 fewer payload loads on random 256 KiB. It added 98,870 branch instructions. Focused native tests exercised 1,404,000 differential calls and 840 overlapping-view calls.

Encoder text is 63,304 B, lookup data 3,200 B, the whole constants section 17,728 B and the stripped executable 210,024 B. Peak stack is 4,832 B against the 5,280 B cap.

Complete source-through-link medians were 2.205 s for the candidate, 2.194 s for the matched control and 0.482 s for libdeflate. The 32 timed builds passed 324 deployment inflation checks. The linked worker passed 162 exact output and alias checks, six named errors and 12 recovery pairs.

<details>
<summary>Fixed 18-case qualification</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Contribution improvement pp |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.288292 / 1.299095 | 1.252609 / 1.255461 | 0.098521 / 0.098895 | 0.096375 / 0.094750 | 0.077480 / 0.076541 | +0.220267 |
| `prefix-random-8192` | 1.238419 / 1.260004 | 1.198111 / 1.226696 | 0.156229 / 0.156750 | 0.151541 / 0.151000 | 0.126292 / 0.124979 | +0.204696 |
| `reymont-prefix-1024` | 1.195613 / 1.198370 | 1.196349 / 1.197695 | 0.070375 / 0.070292 | 0.070334 / 0.070250 | 0.059000 / 0.059000 | -0.000174 |
| `prefix-natural-1024` | 1.194736 / 1.196371 | 1.195079 / 1.197639 | 0.070250 / 0.070291 | 0.070334 / 0.070292 | 0.059041 / 0.059000 | -0.004476 |
| `16384-distribution-change` | 1.165351 / 1.168569 | 1.152907 / 1.159965 | 0.564604 / 0.564812 | 0.560271 / 0.558167 | 0.483271 / 0.484001 | +0.058491 |
| `prefix-random-16384` | 1.171773 / 1.162161 | 1.127798 / 1.121171 | 0.278271 / 0.275729 | 0.268229 / 0.265729 | 0.237979 / 0.237355 | +0.235987 |
| `random-32769` | 1.083560 / 1.092208 | 1.061862 / 1.074294 | 0.571854 / 0.575396 | 0.560250 / 0.564687 | 0.526875 / 0.527188 | +0.110086 |
| `prefix-random-33027` | 1.090684 / 1.091521 | 1.064525 / 1.067699 | 0.583333 / 0.583833 | 0.568167 / 0.569937 | 0.532937 / 0.534021 | +0.138841 |
| `prefix-random-32769` | 1.085087 / 1.091977 | 1.060604 / 1.069836 | 0.574083 / 0.577042 | 0.561562 / 0.563354 | 0.528417 / 0.528709 | +0.129535 |
| `prefix-random-32767` | 1.084847 / 1.089105 | 1.058768 / 1.065242 | 0.566062 / 0.565021 | 0.552458 / 0.553291 | 0.518813 / 0.518521 | +0.138743 |
| `prefix-random-32768` | 1.084977 / 1.085468 | 1.058883 / 1.062144 | 0.563916 / 0.563021 | 0.550521 / 0.551542 | 0.518021 / 0.518562 | +0.137279 |
| `heldout-random-65537` | 1.063956 / 1.063182 | 1.046673 / 1.044969 | 1.223083 / 1.224042 | 1.203187 / 1.204812 | 1.145292 / 1.149895 | +0.098603 |
| `prefix-random-65535` | 1.053111 / 1.057938 | 1.035878 / 1.039660 | 1.225688 / 1.225437 | 1.205021 / 1.207062 | 1.161000 / 1.160000 | +0.098634 |
| `prefix-random-65537` | 1.053505 / 1.057181 | 1.035661 / 1.035443 | 1.234354 / 1.239521 | 1.214438 / 1.217354 | 1.169604 / 1.172333 | +0.109941 |
| `prefix-random-65536` | 1.052929 / 1.052494 | 1.032764 / 1.034496 | 1.224313 / 1.224042 | 1.203271 / 1.205355 | 1.160980 / 1.162084 | +0.106008 |
| `prefix-random-131072` | 1.021032 / 1.021093 | 1.006508 / 1.004325 | 2.526479 / 2.527583 | 2.495188 / 2.486792 | 2.473396 / 2.474728 | +0.086928 |
| `prefix-random-262144` | 1.015878 / 1.017264 | 1.003417 / 1.001848 | 5.145437 / 5.142437 | 5.079292 / 5.070188 | 5.056146 / 5.056062 | +0.077434 |
| `prefix-random-1048576` | 0.996585 / 0.997565 | 0.983208 / 0.983198 | 20.269146 / 20.274709 | 19.998354 / 19.985584 | 20.343521 / 20.358396 | +0.000000 |

</details>

<details>
<summary>Source replay</summary>

Use the earlier `packed-eight` byte histogram recipe and its layout profiles. Build the compiler from `d4625ab975e85b6d15330b9f736d2635f82d3974` and add these compiler options before compiling the canonical codec.

```sh
export MECH_GROUP_PACKED_HISTOGRAM_VISITS=8
export MECH_GROUP_PACKED_HISTOGRAM_VECTOR_CHUNKS=1
export MECH_GROUP_PACKED_HISTOGRAM_STREAM_CHUNKS=1
```

- `program.o` SHA-256 `2aa3a5064556c0b28c6c6695e249ffbe307a027a6586ee7f341f19f2997ec86c`
- `metadata.json` SHA-256 `4c2449bf57b4f6cb07932e74212496fb92d27310c04a3786a93e04f1849596fb`
- `program.mecb` SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`
- `compile_profile` SHA-256 `011fc5697388c6ca28b9e7c184c636d7e31426d8282ff5e6809274ed20bb8a02`
- Evidence archive SHA-256 `1ad0342bc906817fe44f0166e5575a80dfaecab49eaca901996f37ad0dcbf9ef` for 1,131 verified files

</details>

## Earlier qualification of `packed-eight`

The earlier selected recipe was `packed-eight` at `cf3db28cb70cbdc72efe66622ab6d1bbc8179c8f`. The compiler emits an eight-byte load after proving disjointness of the input and counter ranges and capacity for every increment. The updates commit in source order. The existing checked path handles a guard failure. [Source](https://github.com/mech-lang/mech/commit/cf3db28cb70cbdc72efe66622ab6d1bbc8179c8f)

The mean positive slowdown over the fixed 18 names fell from **11.03433%** to **10.56932%**, an improvement of **0.46501 percentage points**. The maximum gap fell from 30.21184% to 29.92798%.

The Apple M1 comparison used the pinned libdeflate 1.26 level-12 build, with 96 balanced blocks for each of the original 81 cases in each direction. The raw records verified 1,965,312 observations.

| Order | Wins vs libdeflate | Missing protected wins |
|---|---:|---|
| Forward | 64/81 | None |
| Reverse | 64/81 | None |

Random 256 KiB is the closest remaining case. Its gap fell from 1.479% to **1.170%** forward and from 1.716% to **1.277%** reverse. A further elapsed-time reduction of just over 1.261% would take it below parity in both orders. The measured random 1 MiB lead was 0.559% forward and 0.521% reverse.

The separately instrumented byte histogram executed 229,363 fewer instructions and 229,376 fewer payload loads on random 256 KiB. The five focused native histogram tests cover seeded overflows, aliased views, exact partial writes and short tails.

Encoder text is 63,656 B. Lookup data is 3,200 B, the whole constants section is 17,728 B, and the stripped executable is 210,024 B. Peak native stack was 4,832 B against a 5,280 B cap.

Complete source-through-link medians were 2.199 s for the candidate, 2.182 s for the matched control and 0.490 s for libdeflate. Across 32 timed builds, the deployed encoders passed 324 inflation checks.

The linked worker passed 162 exact output and alias observations, six named errors and 12 recovery pairs. Object, metadata and canonical bytecode matched across normal, checked, inspection and source replay modes.

<details>
<summary>Fixed 18-case qualification</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Contribution improvement pp |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.303710 / 1.300529 | 1.302470 / 1.296097 | 0.098146 / 0.097875 | 0.098229 / 0.097271 | 0.075563 / 0.075500 | +0.015770 |
| `prefix-random-8192` | 1.260704 / 1.286586 | 1.257060 / 1.271194 | 0.156146 / 0.157772 | 0.155230 / 0.156271 | 0.124021 / 0.123312 | +0.052622 |
| `reymont-prefix-1024` | 1.189702 / 1.208921 | 1.192710 / 1.199251 | 0.070083 / 0.070833 | 0.070292 / 0.070708 | 0.059000 / 0.059208 | +0.018318 |
| `prefix-natural-1024` | 1.197430 / 1.199500 | 1.195497 / 1.193632 | 0.070208 / 0.070500 | 0.070292 / 0.070334 | 0.059000 / 0.059083 | +0.021668 |
| `prefix-random-16384` | 1.169100 / 1.167965 | 1.162856 / 1.160623 | 0.276771 / 0.285146 | 0.276188 / 0.283375 | 0.235854 / 0.245480 | +0.037742 |
| `16384-distribution-change` | 1.160908 / 1.170694 | 1.158341 / 1.163929 | 0.560312 / 0.561063 | 0.559250 / 0.559125 | 0.483355 / 0.482104 | +0.025882 |
| `prefix-random-33027` | 1.086452 / 1.086249 | 1.080503 / 1.084241 | 0.577771 / 0.580417 | 0.575063 / 0.580959 | 0.531000 / 0.534729 | +0.022110 |
| `prefix-random-32769` | 1.083727 / 1.087783 | 1.078309 / 1.083746 | 0.570271 / 0.602688 | 0.567875 / 0.600438 | 0.525750 / 0.553334 | +0.026272 |
| `prefix-random-32767` | 1.085356 / 1.083904 | 1.078009 / 1.080351 | 0.560937 / 0.563208 | 0.558479 / 0.561437 | 0.517188 / 0.519771 | +0.030281 |
| `prefix-random-32768` | 1.082092 / 1.084628 | 1.077921 / 1.079218 | 0.561354 / 0.590624 | 0.559021 / 0.591500 | 0.518063 / 0.546812 | +0.026608 |
| `random-32769` | 1.081553 / 1.084669 | 1.074982 / 1.080712 | 0.571584 / 0.573979 | 0.567812 / 0.573521 | 0.527062 / 0.528855 | +0.029260 |
| `heldout-random-65537` | 1.059503 / 1.060932 | 1.056339 / 1.056066 | 1.217396 / 1.219021 | 1.215417 / 1.216708 | 1.145896 / 1.148958 | +0.022304 |
| `prefix-random-65535` | 1.051271 / 1.058425 | 1.045245 / 1.051017 | 1.224126 / 1.233250 | 1.217604 / 1.228500 | 1.160792 / 1.164979 | +0.037305 |
| `prefix-random-65537` | 1.050021 / 1.054123 | 1.045978 / 1.049291 | 1.229916 / 1.234146 | 1.225979 / 1.229958 | 1.168104 / 1.169292 | +0.024646 |
| `prefix-random-65536` | 1.050450 / 1.051655 | 1.045076 / 1.046147 | 1.218459 / 1.220959 | 1.213000 / 1.216104 | 1.156562 / 1.160125 | +0.030227 |
| `prefix-random-131072` | 1.021189 / 1.020940 | 1.016885 / 1.016885 | 2.524813 / 2.521354 | 2.516916 / 2.515271 | 2.468583 / 2.472124 | +0.023218 |
| `prefix-random-262144` | 1.014789 / 1.017158 | 1.011699 / 1.012767 | 5.130667 / 5.133896 | 5.115916 / 5.112666 | 5.049458 / 5.050792 | +0.020777 |
| `prefix-random-1048576` | 0.998183 / 0.997341 | 0.994410 / 0.994788 | 20.263604 / 20.259396 | 20.200875 / 20.196250 | 20.310834 / 20.320625 | +0.000000 |

</details>

<details>
<summary>Source replay</summary>

Build the compiler at the source revision above. Use the `packed-zeroes-visits` options and layout profiles documented in the earlier qualification below. Add the following override before compiling the original codec.

```sh
export MECH_HISTOGRAM_GROUP_BYTE_VISITS=packed-eight
```

- `program.o` SHA-256 `210c956933301f81dc2bffc6096188757e8fe7ba0a7bcc90d84a867087d1027d`
- `metadata.json` SHA-256 `d8dc2fe15fbc5748e5ea0a575f330fe08353b0d82298a535bc560ed7d4d68238`
- `program.mecb` SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`

</details>

## Earlier qualification of `packed-zeroes-visits`

## Compiler changes

Forward private vector phase edges, lower checked compound comparisons on AArch64, and share equivalent wrapping prefetch address adds. The opt-in emission passes invert in-place conditional sets, reuse condition flags, remove repeated private zero moves, and select the low bit for a branch after verifying both intermediate values have one use. The layout profiles are rebuilt against each emitted phase. The matcher combines adjacent zero stores using the writable view's bounds and a single path between the two writes.

## Mechdeflate qualification

Selected recipe is `packed-zeroes-visits`.

Apple M1 at libdeflate level 12, with 96 balanced blocks per case in each order. A disk write failure interrupted an earlier run. Both measured orders restarted with RAM-backed output. Random 1 MiB changed by **-0.037%** forward and **-0.015%** reverse versus libdeflate.

| Order | Wins vs libdeflate | Missing protected wins |
|---|---:|---|
| forward | 64/81 | None |
| reverse | 64/81 | None |

The mean positive slowdown over the 18 named cases changed from **11.54659%** to **11.50599%**. The change was **+0.04060 percentage points** of improvement. The largest remaining gap changed from **30.51298%** to **30.73019%**.

Encoder text is 63,480 B. Lookup data is 3,200 B, total constants are 17,728 B, the stripped executable is 210,024 B, and peak stack is 4,832 B.

Source through final link medians were 2.194 s for the candidate, 2.192 s for the matched control and 0.485 s for libdeflate. The linked deployments passed 324 inflation checks.

The worker passed 162 exact output, inflation and alias checks, 6 named errors and 12 recovery pairs. Normal, checked and inspection modes produced identical object, metadata and canonical bytecode.

<details>
<summary>Fixed 18-case timing table</summary>

| Case | Control × C F/R | Candidate × C F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Contribution improvement, pp |
|---|---:|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.285459 / 1.325102 | 1.284102 / 1.330921 | 0.097250 / 0.103313 | 0.097583 / 0.102854 | 0.076438 / 0.077959 | -0.012067 |
| `prefix-random-8192` | 1.216079 / 1.351876 | 1.239679 / 1.364694 | 0.153125 / 0.177812 | 0.155750 / 0.179271 | 0.125770 / 0.135730 | -0.102802 |
| `prefix-random-16384` | 1.151984 / 1.215516 | 1.159335 / 1.236357 | 0.271771 / 0.303396 | 0.275000 / 0.308416 | 0.237374 / 0.258374 | -0.077241 |
| `reymont-prefix-1024` | 1.198393 / 1.200090 | 1.196497 / 1.196758 | 0.070417 / 0.070542 | 0.070333 / 0.070291 | 0.059000 / 0.059000 | +0.014523 |
| `prefix-natural-1024` | 1.204249 / 1.200984 | 1.196427 / 1.195740 | 0.070542 / 0.070584 | 0.070250 / 0.070208 | 0.059000 / 0.059041 | +0.036289 |
| `16384-distribution-change` | 1.159667 / 1.156634 | 1.169897 / 1.172191 | 0.558687 / 0.557458 | 0.566438 / 0.568833 | 0.484542 / 0.484708 | -0.071632 |
| `prefix-random-32767` | 1.081851 / 1.120895 | 1.084405 / 1.092124 | 0.562812 / 0.615188 | 0.565416 / 0.618938 | 0.519792 / 0.566584 | +0.071904 |
| `random-32769` | 1.088957 / 1.089848 | 1.087973 / 1.088369 | 0.575562 / 0.576229 | 0.575312 / 0.575666 | 0.528104 / 0.528021 | +0.006841 |
| `prefix-random-33027` | 1.090900 / 1.082067 | 1.087386 / 1.088908 | 0.583437 / 0.579480 | 0.583187 / 0.582270 | 0.533291 / 0.533563 | -0.009292 |
| `prefix-random-32769` | 1.083993 / 1.080611 | 1.083719 / 1.086979 | 0.573355 / 0.571896 | 0.574979 / 0.575355 | 0.527333 / 0.528146 | -0.016929 |
| `prefix-random-32768` | 1.086357 / 1.079152 | 1.082839 / 1.084890 | 0.562729 / 0.560334 | 0.563271 / 0.562750 | 0.517271 / 0.518042 | -0.006195 |
| `heldout-random-65537` | 1.067926 / 1.067727 | 1.063596 / 1.062997 | 1.227291 / 1.227688 | 1.222396 / 1.224062 | 1.146855 / 1.150000 | +0.025167 |
| `prefix-random-65537` | 1.058881 / 1.060409 | 1.053313 / 1.056568 | 1.241334 / 1.240646 | 1.236770 / 1.238750 | 1.169584 / 1.171187 | +0.026140 |
| `prefix-random-65535` | 1.060305 / 1.058912 | 1.055372 / 1.053676 | 1.233000 / 1.230146 | 1.228125 / 1.227438 | 1.160500 / 1.161396 | +0.028248 |
| `prefix-random-65536` | 1.057768 / 1.059081 | 1.051684 / 1.055242 | 1.231166 / 1.227500 | 1.225437 / 1.228229 | 1.160521 / 1.161667 | +0.027570 |
| `prefix-random-131072` | 1.029956 / 1.027221 | 1.024026 / 1.022150 | 2.549188 / 2.542458 | 2.536729 / 2.532938 | 2.471729 / 2.475250 | +0.030557 |
| `prefix-random-262144` | 1.024944 / 1.025424 | 1.019822 / 1.018204 | 5.191187 / 5.191562 | 5.159646 / 5.157458 | 5.053437 / 5.066042 | +0.034283 |
| `prefix-random-1048576` | 1.007161 / 1.005525 | 0.999632 / 0.999850 | 20.449979 / 20.445583 | 20.334416 / 20.328958 | 20.364854 / 20.336209 | +0.035237 |

</details>

<details>
<summary>Source and replay values</summary>

Start with the published `shared-bases-linear-4096` recipe. Apply these options and replace the layout profile for each listed phase. [Base recipe](https://github.com/mech-lang/benchmarks/blob/05fdb530b1836527ca60f5ec4f509511ac54f136/experiments/mech/mechdeflate-phase-routes-v1/README.md)

```sh
export MECH_PACK_PRIVATE_HALFWORD_STORES=zero:mech_compact_numeric_475_vector
export MECH_COMPACT_FOLD_INVERTED_CSET=select
```

`mech_compact_numeric_3956_vector` layout SHA-256 `bb97392992bad7f1f2d03bfba3aa8fd1b356b820bf1578800c76f782c2e06620`.

```json
{
  "order": [
    0,
    244,
    248,
    268,
    272,
    280,
    296,
    184,
    204,
    212,
    224,
    236,
    288,
    68,
    160,
    176,
    180,
    256,
    76,
    152,
    40,
    64,
    192,
    216,
    84,
    168,
    304
  ],
  "literal_offset": null,
  "thread_jumps": true
}
```

`mech_compact_numeric_475_vector` layout SHA-256 `481429ba1439c42a2420122b1b402812f8d5e208ddf2327af3784a3d597e5df5`.

```json
{
  "order": [
    0,
    3248,
    236,
    248,
    288,
    356,
    372,
    584,
    2184,
    2204,
    2248,
    2256,
    2284,
    2316,
    2344,
    2360,
    2516,
    2520,
    2524,
    2532,
    2568,
    2584,
    2596,
    2600,
    2604,
    2640,
    2656,
    2704,
    2716,
    3384,
    3396,
    3416,
    3436,
    3440,
    3472,
    3476,
    3156,
    3160,
    3240,
    3268,
    3132,
    3140,
    3148,
    596,
    636,
    1436,
    1452,
    1472,
    1484,
    1508,
    2012,
    2020,
    2076,
    2100,
    380,
    412,
    416,
    432,
    448,
    2044,
    2724,
    2748,
    2768,
    2780,
    456,
    484,
    488,
    504,
    2124,
    3324,
    3328,
    3344,
    3352,
    3368,
    3104,
    3276,
    3296,
    3304,
    3316,
    2860,
    2864,
    2876,
    2896,
    2916,
    4016,
    4032,
    2784,
    2804,
    2824,
    2832,
    2840,
    2852,
    1516,
    1524,
    1668,
    1688,
    1880,
    1884,
    1900,
    1916,
    1928,
    1964,
    1984,
    1988,
    2008,
    520,
    524,
    540,
    552,
    2264,
    2276,
    2324,
    2904,
    2912,
    1908,
    1712,
    1732,
    1852,
    3648,
    3656,
    3744,
    3480,
    3488,
    2408,
    2428,
    2452,
    2484,
    2492,
    2500,
    2924,
    2940,
    2952,
    2976,
    2996,
    3056,
    3072,
    3088,
    3100,
    3112,
    4620,
    2796,
    1756,
    1768,
    1780,
    1788,
    1812,
    3164,
    3184,
    3192,
    3208,
    3216,
    3232,
    512,
    3964,
    3968,
    3984,
    4004,
    3464,
    648,
    652,
    668,
    688,
    700,
    736,
    760,
    800,
    808,
    944,
    1044,
    1056,
    1184,
    1388,
    1428,
    2292,
    2556,
    2612,
    2644,
    344,
    3584,
    3588,
    3604,
    3616,
    3632,
    3492,
    3536,
    3556,
    3564,
    3576,
    3664,
    3684,
    3692,
    3708,
    3720,
    3736,
    3008,
    3032,
    4560,
    272,
    1064,
    1092,
    1096,
    1104,
    4044,
    3500,
    3516,
    3768,
    2696,
    936,
    832,
    844,
    852,
    868,
    880,
    896,
    908,
    916,
    1552,
    1556,
    1568,
    1580,
    1596,
    1608,
    1620,
    1632,
    1640,
    2144,
    2176,
    2592,
    768,
    792,
    1196,
    1216,
    1220,
    1240,
    1244,
    1252,
    1308,
    1336,
    956,
    1168,
    1276,
    1820,
    1844,
    3428,
    3448,
    3460,
    3752,
    3760,
    404,
    476,
    532,
    660,
    696,
    876,
    904,
    984,
    1000,
    1004,
    1028,
    1084,
    1112,
    1136,
    1144,
    1208,
    1232,
    1356,
    1444,
    1480,
    1604,
    1628,
    1660,
    1680,
    1976,
    2000,
    2472,
    2816,
    3176,
    3288,
    3548,
    3676,
    4180,
    5028,
    4204,
    4224,
    4244,
    4264,
    4284,
    4308,
    4332,
    4352,
    4372,
    4396,
    4420,
    4440,
    4460,
    4480,
    4500,
    4520,
    4540,
    4580,
    4600,
    4640,
    4660,
    4684,
    4708,
    4728,
    4752,
    4776,
    4796,
    4816,
    4836,
    4860,
    4884,
    4904,
    4928,
    4952,
    4972,
    4992,
    5012
  ],
  "literal_offset": null,
  "thread_jumps": true
}
```

`mech_compact_numeric_475_vector` register profile SHA-256 `ba3fdfafd90d9c46d5a01d10cf42b5a44ef46f018f70b67f3e114d6be7744434`.

Compile once with this phase's layout and register profile entries omitted. Set `MECH_INSPECT_PHASE_REGISTER_PROFILE` to a `.vcode` path with the phase name as its stem. Copy the complete text between the two `REGALLOC_INPUT` marker lines into `expected_vcode`, including the final newline.

The captured VCode text has SHA-256 `c583aedbf561581015375b38417a3b13c3f64126d54bd18993486586a9647320`. The remaining fields are below.

```json
{"expected_vcode":"","block_frequencies":[1,4096,4096,4096,4096,4096,4096,4096,4096,4096,4096,4096,5,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,203,3889,3889,2753,1136,1136,1136,1136,1136,1136,1136,1136,1,1136,1136,1136,1136,1136,1136,1136,739,739,599,139,139,139,1,139,139,139,139,139,139,139,139,1,1,1,1,1,1,1,1,397,397,397,397,398,398,398,398,398,1,398,398,398,398,398,398,1,1,398,398,398,398,398,398,398,398,398,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,4091,1253,1050,203,203,203,203,1,203,203,203,203,203,203,203,203,1,203,203,203,203,203,203,203,203,1,203,203,203,203,203,203,203,203,203,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,203,203,203,203,203,1,1,203,3,3,3,1,3,3,241,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,200,200,1,1,1,1,200,1,1,1,200,200,200,200,200,200,241,241,241,241,241,203,38,38,38,38,38,38,38,38,38,1,38,38,38,38,38,38,203,203,203,203,38,38,38,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,203,203,203,203,203,203,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,203,203,203,203,203,203,203,203,203,203,203,203,203,203,203,203,203,203,4091,4091,4091,4091,1490,1490,1490,2,1490,1490,1490,1490,1490,1490,1490,1490,1,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1490,1489,528,528,528,528,528,528,1,1,528,1,1,1,1,1,1,6,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,528,1,528,207,207,280,2,280,75,280,2,2,2,2,2,2,6,6,6,6,6,528,4,4,4,4,4,4,4,4,4,4,4,4,4,4,528,528,528,528,4,4,4,1,1,1,1,1,1,1,1,526,1,1,1,205,321,526,526,526,526,526,526,528,528,528,528,528,526,377,377,377,377,377,377,377,1,1,377,377,377,377,377,377,377,377,377,377,377,377,526,526,526,526,1,526,526,526,526,526,526,526,526,1,526,526,526,1489,1489,1489,1489,1489,1489,1489,733,755,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1489,1049,1049,1049,1049,1049,1049,1049,1049,1049,440,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4091,4091,2839,2839,2839,2839,2839,4091,4091,4096,4096,4096,3698,398,1,1,398,4096,4096,4096,4096,206,3890,3890,328,3561,3561,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,3522,40,40,40,40,1,40,40,40,40,40,40,40,40,1,40,40,40,40,40,40,40,1,40,40,40,40,40,40,40,40,40,1,1,40,40,40,3561,3561,3890,3890,4096,4096,4096,4096,4096,4096,4096,4096,4096,4096,1,1,4096,4096,4096,206,206,3890,3890,3890,3890,3888,2,2,3890,3890,4096,4096,4096,4096,4096,4096,4096,4096,3890,206,206,206,4096,4096,4096,4096,4096,206,3890,3890,3890,3890,1,3888,2557,1331,1331,1331,865,466,466,466,466,466,462,4,4,4,4,1,45,45,45,4,41,41,1,41,41,41,41,41,1,41,41,41,41,41,41,1,41,41,41,41,41,1,41,41,41,27,27,27,18,1,18,18,45,45,45,4,1,4,1,4,4,4,1,4,4,4,4,4,4,1,1,1,1,1,1,1,4,4,4,4,1,4,4,1,4,4,1,4,4,4,4,4,4,46,46,46,4,1078,1,1078,1078,1078,4,1074,1074,1,1074,1074,1074,1074,1074,1074,1071,2,2,1,2,2,2,2,2,1,2,2,1,1,2,2,2,2,1,1,2,2,1078,1078,1078,1078,1078,4,1074,1074,1074,41,41,1,41,41,41,41,41,41,1,41,41,41,41,41,1,41,41,1,1,41,41,41,41,1,1,41,41,41,41,41,41,41,41,3885,3885,3885,3885,3885,3885,1,1,1,1,1,1,1,1,1,1,1,1,7,7,7,1,1,1,1,1,291,291,291,1,12,12,12,1,1,1,1,11,11,1,11,11,11,11,11,11,1,11,11,11,11,11,1,11,11,1,1,11,11,11,11,1,1,11,11,11,11,11,11,11,11,290,290,290,290,290,290,290,290,290,290,9,9,1,9,9,9,9,9,1,9,9,1,1,9,9,9,9,1,1,9,9,290,290,290,290,290,290,290,1,1,1,1,1,1,1,1,1,1,1,7,1,7,7,7,7,7,7,7,7,7,7,7,7,1,7,7,7,7,7,7,7,3884,3884,41,41,1,1,41,41,1],"scope":"Declared weighted share of nine cases, mapped through the complete static CFG; absent block visits remain zero before the frequency floor. linear-4096","power":1.0,"maximum":4096,"cases":["320-overlap","16384-distribution-change","random-32769","reymont-prefix-1024","heldout-random-65537","prefix-natural-1024","prefix-natural-4096","prefix-natural-8192","prefix-random-4096","prefix-random-8192","prefix-random-16384","prefix-random-32767","prefix-random-32768","prefix-random-32769","prefix-random-33027","prefix-random-65535","prefix-random-65536","prefix-random-65537","prefix-random-131072","prefix-random-262144","prefix-random-1048576"],"training_object_sha256":"9c0fc6c04ce5ec450c508d548627c1cdecd4afccf6c8398b8ea68980036a61f4","training_vcode_sha256":"ca7b9ef0d897b4d9209bb36b3dc6b042b46f125f0aedf21ff51d8b327a33176e","block_counts_sha256":"07e5eac8b8625ebff950979f56eb87496c7590a0b5248e96231cc6163ac8140d"}
```

Encoder object SHA-256 `ec87e367bade30538cc01a8ae8060899180b53ae31d9cb3349e360c2f7ddda0e`. Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`. [Compiler source](https://github.com/mech-lang/mech/commit/c4df96f4bde03a113bdae677deacdc9778044def)

</details>

## Independent recheck of the 64th win

The selected `packed-zeroes-visits` build repeated all 64 libdeflate wins in both original-suite orders. Random 1 MiB took **0.134% less time forward** and **0.083% less time reverse** than libdeflate. Both orders used 96 balanced blocks per case. Recomputing the raw records verified 1,965,312 observations.

The Huffman defaulted-load experiment held all named wins. Its fixed 18-case average positive slowdown increased from **11.28350%** to **11.33782%**. The maximum gap increased from 32.24589% to 32.42589%. The selected recipe is `packed-zeroes-visits`.

The Huffman variant added an eight-byte fallback constant. Two lookup tables moved eight bytes in the executable. The 16-byte matcher shift applied to the object file. The matcher entry address in the linked worker was identical. Sharing the phase constant in a follow-up emitted the same Huffman code size and moved those tables a further eight bytes.

<details>
<summary>Fixed 18-case recheck</summary>

| Case | Selected × libdeflate F/R | Huffman × libdeflate F/R | Selected ms F/R | Huffman ms F/R | libdeflate ms F/R |
|---|---:|---:|---:|---:|---:|
| `prefix-random-4096` | 1.334963 / 1.310071 | 1.329418 / 1.319120 | 0.100354 / 0.097687 | 0.100292 / 0.098521 | 0.076229 / 0.075209 |
| `prefix-random-8192` | 1.284209 / 1.295660 | 1.279560 / 1.292192 | 0.160521 / 0.158438 | 0.159354 / 0.158562 | 0.124563 / 0.123105 |
| `reymont-prefix-1024` | 1.196089 / 1.200358 | 1.196255 / 1.201115 | 0.070250 / 0.070209 | 0.070291 / 0.070125 | 0.059000 / 0.058959 |
| `prefix-natural-1024` | 1.196542 / 1.197315 | 1.197189 / 1.194511 | 0.070334 / 0.070167 | 0.070375 / 0.070084 | 0.059000 / 0.058959 |
| `prefix-random-16384` | 1.176202 / 1.170162 | 1.171257 / 1.177011 | 0.277979 / 0.277770 | 0.276521 / 0.279270 | 0.235958 / 0.236250 |
| `16384-distribution-change` | 1.161830 / 1.165400 | 1.172122 / 1.170064 | 0.564354 / 0.559562 | 0.569708 / 0.562520 | 0.484917 / 0.481333 |
| `random-32769` | 1.090422 / 1.085834 | 1.090794 / 1.086131 | 0.575125 / 0.572063 | 0.575604 / 0.572521 | 0.526520 / 0.527334 |
| `prefix-random-33027` | 1.091623 / 1.083221 | 1.089762 / 1.085551 | 0.581979 / 0.578313 | 0.582667 / 0.579729 | 0.532333 / 0.533188 |
| `prefix-random-32769` | 1.086681 / 1.080949 | 1.088340 / 1.081107 | 0.574792 / 0.570416 | 0.576062 / 0.571625 | 0.528083 / 0.527958 |
| `prefix-random-32767` | 1.082342 / 1.083178 | 1.088144 / 1.082413 | 0.563667 / 0.560854 | 0.565500 / 0.561188 | 0.518437 / 0.518084 |
| `prefix-random-32768` | 1.086126 / 1.077109 | 1.088863 / 1.080624 | 0.561958 / 0.559459 | 0.563979 / 0.561458 | 0.518500 / 0.519729 |
| `heldout-random-65537` | 1.064145 / 1.060946 | 1.064251 / 1.058584 | 1.224500 / 1.220646 | 1.224895 / 1.217291 | 1.148270 / 1.150229 |
| `prefix-random-65535` | 1.052745 / 1.055599 | 1.056567 / 1.051727 | 1.225416 / 1.226520 | 1.228792 / 1.223645 | 1.160980 / 1.161375 |
| `prefix-random-65537` | 1.051308 / 1.055130 | 1.054423 / 1.052761 | 1.235229 / 1.232646 | 1.238541 / 1.233229 | 1.171209 / 1.170812 |
| `prefix-random-65536` | 1.049947 / 1.050974 | 1.052628 / 1.050416 | 1.221688 / 1.221875 | 1.227542 / 1.220374 | 1.162062 / 1.161520 |
| `prefix-random-131072` | 1.023363 / 1.022489 | 1.021583 / 1.020439 | 2.536229 / 2.529687 | 2.535417 / 2.525959 | 2.474438 / 2.473813 |
| `prefix-random-262144` | 1.018528 / 1.020811 | 1.017610 / 1.019209 | 5.159209 / 5.153271 | 5.162542 / 5.151771 | 5.060416 / 5.054792 |
| `prefix-random-1048576` | 0.998661 / 0.999165 | 0.997936 / 0.999447 | 20.324063 / 20.316229 | 20.337812 / 20.316083 | 20.363959 / 20.368750 |

</details>

## Silesia level-12 control

This control compares `9cefa8a7f` with `c4df96f4b` on the 12 full Silesia files.

The 64-win build took **0.16% less time on the median file** than the 63-win build. It won **9/12** against libdeflate level 12, down from **10/12**. The win counts hold separately in both directions.

`sao` crossed from a narrow win to a narrow loss against libdeflate. Both Mech builds and libdeflate produced the same raw DEFLATE bytes on every file. Each stream independently inflated to the pinned input in both directions.

Four interleavings per file balanced actor positions across the two directions. The clock measures the encoder call on the Apple M1. The table uses paired elapsed-time ratios, so a value below one favors the first encoder.

| Full Silesia file | 64-win / 63-win | 63-win / libdeflate | 64-win / libdeflate |
|---|---:|---:|---:|
| `dickens` | 0.993597× | 0.808310× | 0.803134× |
| `mozilla` | 1.001055× | 0.899223× | 0.900172× |
| `mr` | 1.006475× | 1.079221× | 1.086209× |
| `nci` | 0.996261× | 0.852288× | 0.849102× |
| `ooffice` | 1.008091× | 0.897016× | 0.904273× |
| `osdb` | 0.998455× | 0.898075× | 0.896687× |
| `reymont` | 0.997714× | 0.734176× | 0.732498× |
| `samba` | 0.996900× | 0.836552× | 0.833959× |
| `sao` | 1.006780× | 0.994145× | 1.000885× |
| `webster` | 0.998396× | 0.774985× | 0.773742× |
| `x-ray` | 0.999591× | 1.153289× | 1.152817× |
| `xml` | 0.995251× | 0.815609× | 0.811735× |

The sum of the per-file median times changed from 28.9576 s to 28.9154 s. The inventory SHA-256 is `43a4bd756c15eb336f7adba9d0b3a3764efbc8d3cd6ab91d505f3827a03aad67`.
