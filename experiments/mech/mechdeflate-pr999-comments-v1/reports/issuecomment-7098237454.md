@codex review

Please review commit `9a36a6dc113ba279e0e333a55bb01bb3b3624242`.

The shared checked append uses a short entry for zero or one byte when the destination has capacity and the backing is uniquely owned. The 120-byte entry follows the existing checked bodies and calls the original body for other inputs. The compiler kept all 45 original symbol starts and redirected the four append calls. Add `MECH_COMPACT_SHORT_BYTE_APPENDS=1` to the pinned split-literal recipe to enable it.

Across 96 balanced blocks per case per order against libdeflate 1.26 level 12, the repeat lowered the fixed 18-case mean positive slowdown from **5.971183% to 5.007598%**, down **0.963585 percentage points**. The candidate held every protected win and finished at **70/81 in both orders**. The largest paired gap fell from 24.027419% to 22.690565%. The verifier recomputed 1,965,312 runtime observations.

The first complete run of this layout lowered the mean from 5.855557% to 5.051413%. The 65,537-byte random holdout was 0.083% behind libdeflate in reverse order, compared with 0.366% behind for the matched control. The unchanged-binaries repeat put the candidate 0.011% ahead in reverse order, with its control 0.273% behind.

Median original source through final executable link took 2.196 s for Mech control, 2.188 s for the candidate and 0.482 s for libdeflate. Compilers and host support were prebuilt. Encoder text grew from 64,728 B to 64,856 B. Lookup data was 3,200 B, whole constants 17,728 B, stripped executable 210,024 B and observed peak stack 4,720 B.

The generated append matched the checked body in 35,640 native probe calls. The linked image passed 162 exact output, independent inflation and alias checks, six named errors, 12 recovery pairs and the checker and spill-inspection replay. The deployment executables passed 324 independent inflation checks.

<details>
<summary>Fixed 18-case timings and margins</summary>

| Case | Control × libdeflate F/R | Candidate × libdeflate F/R | Control ms F/R | Candidate ms F/R | libdeflate ms F/R | Mean improvement (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-random-4096` | 1.242131 / 1.238420 | 1.223855 / 1.229964 | 0.094396 / 0.093687 | 0.093333 / 0.092937 | 0.076625 / 0.076229 | +0.074270 |
| `prefix-natural-1024` | 1.185933 / 1.196085 | 1.162482 / 1.163597 | 0.069625 / 0.070250 | 0.067917 / 0.068333 | 0.058958 / 0.059125 | +0.155330 |
| `reymont-prefix-1024` | 1.184216 / 1.194537 | 1.159892 / 1.158971 | 0.069625 / 0.070209 | 0.067958 / 0.068250 | 0.059000 / 0.059083 | +0.166298 |
| `prefix-random-8192` | 1.180075 / 1.196571 | 1.194757 / 1.166013 | 0.147146 / 0.149646 | 0.149438 / 0.146584 | 0.125812 / 0.125979 | +0.044428 |
| `16384-distribution-change` | 1.108363 / 1.126236 | 1.026653 / 1.039304 | 0.536396 / 0.542542 | 0.495229 / 0.500292 | 0.484000 / 0.484062 | +0.468361 |
| `prefix-random-16384` | 1.086998 / 1.077623 | 1.075138 / 1.076812 | 0.258250 / 0.255480 | 0.254605 / 0.254395 | 0.237229 / 0.237625 | +0.035143 |
| `prefix-random-32769` | 1.016981 / 1.014937 | 1.017247 / 1.014053 | 0.537521 / 0.536979 | 0.538083 / 0.536230 | 0.528250 / 0.528833 | +0.001719 |
| `prefix-random-33027` | 1.011904 / 1.016482 | 1.010641 / 1.015510 | 0.540833 / 0.544583 | 0.541500 / 0.544229 | 0.533708 / 0.534354 | +0.006209 |
| `random-32769` | 1.008721 / 1.017662 | 1.008052 / 1.013732 | 0.532229 / 0.536729 | 0.532645 / 0.535375 | 0.526583 / 0.527583 | +0.012745 |
| `prefix-random-32768` | 1.013545 / 1.010601 | 1.013422 / 1.012641 | 0.525708 / 0.526396 | 0.525958 / 0.527188 | 0.518730 / 0.519834 | -0.005330 |
| `prefix-random-32767` | 1.006742 / 1.015104 | 1.007629 / 1.012617 | 0.524771 / 0.526771 | 0.525146 / 0.526417 | 0.519292 / 0.519167 | +0.004411 |
| `heldout-random-65537` | 0.997263 / 1.002733 | 0.993736 / 0.999889 | 1.146125 / 1.151979 | 1.144459 / 1.149250 | 1.147042 / 1.147563 | +0.000000 |
| `prefix-random-65535` | 0.989877 / 0.994840 | 0.989481 / 0.992706 | 1.151396 / 1.156625 | 1.151521 / 1.156166 | 1.161187 / 1.164125 | +0.000000 |
| `prefix-random-65537` | 0.990293 / 0.995299 | 0.988333 / 0.990097 | 1.160104 / 1.167812 | 1.158854 / 1.163666 | 1.168542 / 1.173750 | +0.000000 |
| `prefix-random-65536` | 0.989676 / 0.994223 | 0.986356 / 0.990290 | 1.149937 / 1.159417 | 1.149646 / 1.156604 | 1.160251 / 1.165917 | +0.000000 |
| `prefix-random-131072` | 0.963630 / 0.964833 | 0.961101 / 0.962577 | 2.388625 / 2.392229 | 2.385730 / 2.389124 | 2.476583 / 2.480834 | +0.000000 |
| `prefix-random-262144` | 0.961171 / 0.962390 | 0.961421 / 0.961533 | 4.874750 / 4.866250 | 4.875437 / 4.859541 | 5.067271 / 5.054813 | +0.000000 |
| `prefix-random-1048576` | 0.944685 / 0.948274 | 0.944273 / 0.948546 | 19.251959 / 19.207270 | 19.244792 / 19.201708 | 20.365896 / 20.282813 | +0.000000 |

</details>

Encoder object SHA-256 `2f9755c8af791668114ea82873ef826c401bdf246f11ba1a0752aaecfc02273c`. Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`. Evidence archive SHA-256 `2a8eab3ab90d4b91b0f6210802cc4f45f1d047922b8a0c74002cf977960dccf4`.