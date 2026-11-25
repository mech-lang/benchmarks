@codex review

Please review commit `69fa012102fdbc615eb7ec7fc1498da4bda19841`.

The width analysis walks every incoming value of each carried hash. The two entry captures need a width check, and each newly computed value fits in 16 bits. The specialization combines both checks with the existing phase span guard. Its refusal edge enters the checked continuation. Set `MECH_COMPACT_ADMIT_CARRIED_HALFWORDS=mech_compact_numeric_475_vector` on the short-append recipe and use the refreshed matcher register and layout profiles.

The fixed 18-case mean positive slowdown fell from **5.200127% to 4.712004%**, down **0.488122 percentage points**, against libdeflate 1.26 level 12. The candidate kept all protected wins and finished **70/81 in each order**. The verifier recomputed 1,965,312 observations across the two 96-block orders. The five 32 KiB cases are within 0.90% of libdeflate in their slower orders. The maximum paired gap moved from 22.011205% to 22.202025%.

The screen reproduced the mean improvement from 5.544061% to 5.082104%. The combined build with live-byte reuse missed the reverse 4 KiB natural case at screening. The standalone admission branch failed SSA verification, which led to the shared span guard.

The width proof passed 21,168 native differential calls including 10,800 checked refusals. Linked output and aliases passed 162 exact checks, plus six named errors and 12 recovery pairs. Checker and spill-inspection replays reproduced the object, bytecode and metadata. The deployed executables passed 324 independent inflation checks.

Median original source through final executable link took 2.195 s for the control, 2.205 s for the candidate and 0.481 s for libdeflate. Encoder text grew from 64,856 B to 65,192 B, and observed peak stack rose from 4,720 B to 4,880 B. Lookup data was 3,200 B, whole constants 17,728 B and stripped executable 210,024 B.

<details>
<summary>Fixed 18-case timings and margins</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Mean improvement (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 1.236255 / 1.204180 | 1.225109 / 1.218939 | 0.093771 / 0.091437 | 0.093625 / 0.092563 | 0.076312 / 0.076333 | -0.010601 |
| `prefix-natural-1024` | 1.163932 / 1.214949 | 1.166857 / 1.217230 | 0.068042 / 0.068291 | 0.068417 / 0.068375 | 0.058958 / 0.059125 | -0.014503 |
| `reymont-prefix-1024` | 1.157630 / 1.157381 | 1.166801 / 1.158986 | 0.068125 / 0.068083 | 0.068417 / 0.068209 | 0.058958 / 0.059042 | -0.029896 |
| `prefix-random-8192` | 1.183627 / 1.178993 | 1.163305 / 1.155260 | 0.148125 / 0.146562 | 0.145750 / 0.143250 | 0.125834 / 0.125188 | +0.122400 |
| `prefix-random-16384` | 1.077338 / 1.070579 | 1.064378 / 1.067923 | 0.254876 / 0.253958 | 0.251626 / 0.252708 | 0.237042 / 0.237770 | +0.043357 |
| `16384-distribution-change` | 1.040479 / 1.044398 | 1.022302 / 1.027344 | 0.500333 / 0.505562 | 0.494583 / 0.497042 | 0.483895 / 0.482542 | +0.097872 |
| `prefix-random-33027` | 1.018848 / 1.012454 | 1.008963 / 1.004771 | 0.544354 / 0.542000 | 0.539687 / 0.537812 | 0.532250 / 0.534355 | +0.048783 |
| `prefix-random-32767` | 1.014386 / 1.010975 | 1.007352 / 1.004700 | 0.528958 / 0.523791 | 0.523896 / 0.521313 | 0.519437 / 0.518562 | +0.036965 |
| `random-32769` | 1.014958 / 1.015086 | 1.004558 / 1.003380 | 0.537417 / 0.535249 | 0.531042 / 0.529167 | 0.527333 / 0.527271 | +0.061405 |
| `prefix-random-32769` | 1.015568 / 1.013811 | 1.002047 / 1.004099 | 0.537729 / 0.535396 | 0.532875 / 0.530667 | 0.527834 / 0.527605 | +0.064537 |
| `prefix-random-32768` | 1.014527 / 1.007596 | 1.002512 / 1.000092 | 0.527604 / 0.523396 | 0.522396 / 0.519022 | 0.519771 / 0.518458 | +0.054194 |
| `heldout-random-65537` | 0.999666 / 1.005242 | 0.996110 / 0.998970 | 1.147750 / 1.164458 | 1.145604 / 1.158333 | 1.145500 / 1.161979 | +0.013611 |
| `prefix-random-65535` | 0.993351 / 0.994154 | 0.991567 / 0.987562 | 1.155063 / 1.157458 | 1.153042 / 1.152250 | 1.159542 / 1.165604 | +0.000000 |
| `prefix-random-65537` | 0.993345 / 0.993943 | 0.991978 / 0.988061 | 1.166125 / 1.168979 | 1.162917 / 1.163063 | 1.170583 / 1.175104 | +0.000000 |
| `prefix-random-65536` | 0.994540 / 0.991488 | 0.989776 / 0.997578 | 1.157854 / 1.155125 | 1.153708 / 1.152958 | 1.164458 / 1.164625 | +0.000000 |
| `prefix-random-131072` | 0.964534 / 0.962660 | 0.964636 / 0.961246 | 2.386354 / 2.384605 | 2.389333 / 2.383563 | 2.471042 / 2.477937 | +0.000000 |
| `prefix-random-262144` | 0.962407 / 0.962025 | 0.963852 / 0.961571 | 4.865208 / 4.863270 | 4.873354 / 4.864771 | 5.054604 / 5.052021 | +0.000000 |
| `prefix-random-1048576` | 0.944755 / 0.944784 | 0.947507 / 0.946275 | 19.206916 / 19.203187 | 19.242479 / 19.228188 | 20.334521 / 20.340395 | +0.000000 |

</details>

Encoder object SHA-256 `c06e8c45836d77c34d9f60603b343fa8044a8e633f87e5f877182786dfd196f8`. Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`. Evidence archive SHA-256 `8a1fa9f04836302f924b6dc5788ad76214445d511dca7dfb0a867be757607796`.