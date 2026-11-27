# M1 direct runtime comparison

Before is O (`0bde021f93bd752ebf5e85ba2aaa29f84872caeb`). After is F (`3a66a014c853e082ad907ed4db1673c9dadf0c69`). Both used their frozen executables and the pinned libdeflate level-12 peers.
Three complete sessions ran on the Apple M1. Each session used both case orders and both O/F slot mappings. Each fixture leg retained two full permutation cycles with the existing four workers. Each Silesia leg included O, F and libdeflate together in all six permutations. Every timing block includes both Mech builds and libdeflate.

The existing correctness checks verified the fixture output and independently inflated every Silesia file. All Silesia streams matched the pinned output size and digest. The fixture timer measures closed compression through output acquisition and heap cleanup. The Silesia timer measures one level-12 encode with preloaded input. The record contains 5,895,936 timed fixture calls and 2,592 timed Silesia calls, plus warmups. These direct results are separate from the sealed qualification campaigns. [Input identities and schedule](inputs.json) · [Raw evidence receipt](archive-receipt.json)

Counts are wins/losses/ties. A negative percentage means the first actor took less time. Percentages use the geometric mean of paired time ratios across cases. The summaries weight each included session, order and slot mapping equally. Absolute times are medians of the selected leg medians per case. The absolute suite column sums those case medians.

## 81 fixtures

| Session | Order | O / libdeflate | F / libdeflate | F / O | O / F / libdeflate (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| session-1 | forward | 81/0/0 (-40.921%) | 81/0/0 (-40.900%) | 44/37/0 (+0.036%) | 344.360907 / 344.197585 / 484.025632 |
| session-1 | reverse | 81/0/0 (-41.043%) | 81/0/0 (-41.037%) | 49/32/0 (+0.010%) | 344.141574 / 344.178832 / 484.672000 |
| session-1 | both | 81/0/0 (-40.982%) | 81/0/0 (-40.969%) | 49/32/0 (+0.023%) | 344.219907 / 344.188617 / 484.306354 |
| session-2 | forward | 81/0/0 (-41.036%) | 81/0/0 (-40.892%) | 47/34/0 (+0.244%) | 344.138824 / 344.072906 / 484.217669 |
| session-2 | reverse | 81/0/0 (-40.980%) | 81/0/0 (-40.878%) | 62/19/0 (+0.171%) | 343.906259 / 343.879693 / 485.527971 |
| session-2 | both | 81/0/0 (-41.008%) | 81/0/0 (-40.885%) | 61/20/0 (+0.207%) | 344.059760 / 343.998256 / 484.636003 |
| session-3 | forward | 81/0/0 (-40.902%) | 81/0/0 (-40.976%) | 42/39/0 (-0.125%) | 345.921470 / 345.777760 / 485.890527 |
| session-3 | reverse | 81/0/0 (-41.038%) | 81/0/0 (-41.017%) | 33/48/0 (+0.036%) | 344.128927 / 344.243225 / 484.611639 |
| session-3 | both | 81/0/0 (-40.970%) | 81/0/0 (-40.996%) | 42/39/0 (-0.044%) | 344.127854 / 344.210091 / 484.502416 |
| pooled | forward | 81/0/0 (-40.953%) | 81/0/0 (-40.923%) | 43/38/0 (+0.052%) | 344.232094 / 344.146085 / 484.109811 |
| pooled | reverse | 81/0/0 (-41.020%) | 81/0/0 (-40.978%) | 48/33/0 (+0.073%) | 344.122541 / 344.144033 / 484.704032 |
| pooled | both | 81/0/0 (-40.987%) | 81/0/0 (-40.950%) | 52/29/0 (+0.062%) | 344.109982 / 344.147169 / 484.503928 |

## 12 Silesia files

| Session | Order | O / libdeflate | F / libdeflate | F / O | O / F / libdeflate (s) |
| --- | --- | ---: | ---: | ---: | ---: |
| session-1 | forward | 12/0/0 (-15.591%) | 12/0/0 (-15.601%) | 9/3/0 (-0.011%) | 27.849959 / 27.851203 / 33.651676 |
| session-1 | reverse | 12/0/0 (-15.580%) | 12/0/0 (-15.628%) | 10/2/0 (-0.057%) | 27.858481 / 27.846368 / 33.654287 |
| session-1 | both | 12/0/0 (-15.586%) | 12/0/0 (-15.615%) | 8/4/0 (-0.034%) | 27.851917 / 27.847909 / 33.652105 |
| session-2 | forward | 12/0/0 (-15.597%) | 12/0/0 (-15.613%) | 6/6/0 (-0.019%) | 27.855991 / 27.847886 / 33.659384 |
| session-2 | reverse | 12/0/0 (-15.784%) | 12/0/0 (-15.739%) | 6/6/0 (+0.053%) | 27.844368 / 27.897347 / 33.757409 |
| session-2 | both | 12/0/0 (-15.690%) | 12/0/0 (-15.676%) | 6/6/0 (+0.017%) | 27.852129 / 27.848379 / 33.682281 |
| session-3 | forward | 12/0/0 (-15.577%) | 12/0/0 (-15.528%) | 4/8/0 (+0.059%) | 27.876066 / 27.864946 / 33.649451 |
| session-3 | reverse | 12/0/0 (-15.619%) | 12/0/0 (-15.518%) | 5/7/0 (+0.120%) | 28.541792 / 28.532102 / 34.487453 |
| session-3 | both | 12/0/0 (-15.598%) | 12/0/0 (-15.523%) | 4/8/0 (+0.089%) | 27.878879 / 27.871046 / 33.652891 |
| pooled | forward | 12/0/0 (-15.588%) | 12/0/0 (-15.580%) | 6/6/0 (+0.009%) | 27.849935 / 27.846974 / 33.650681 |
| pooled | reverse | 12/0/0 (-15.661%) | 12/0/0 (-15.629%) | 6/6/0 (+0.039%) | 27.850543 / 27.852035 / 33.680072 |
| pooled | both | 12/0/0 (-15.625%) | 12/0/0 (-15.605%) | 5/7/0 (+0.024%) | 27.851597 / 27.847412 / 33.656106 |

| File | O (s) | F (s) | libdeflate (s) | O / libdeflate | F / libdeflate | F / O |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dickens | 1.032071 | 1.031862 | 1.316038 | -21.604% | -21.633% | -0.037% |
| mozilla | 5.220887 | 5.219621 | 6.121319 | -14.749% | -14.708% | +0.047% |
| mr | 2.231283 | 2.230664 | 2.267659 | -1.590% | -1.445% | +0.147% |
| nci | 7.689856 | 7.688310 | 9.127303 | -15.777% | -15.826% | -0.057% |
| ooffice | 0.432240 | 0.432189 | 0.512679 | -15.635% | -15.525% | +0.130% |
| osdb | 0.721077 | 0.720793 | 0.833860 | -13.624% | -13.573% | +0.059% |
| reymont | 0.822238 | 0.821927 | 1.147453 | -28.376% | -28.371% | +0.007% |
| samba | 2.822392 | 2.822458 | 3.494091 | -19.243% | -19.291% | -0.059% |
| sao | 0.351307 | 0.351356 | 0.383307 | -8.259% | -8.298% | -0.042% |
| webster | 5.195513 | 5.195481 | 6.885578 | -24.589% | -24.486% | +0.136% |
| x-ray | 0.342845 | 0.342753 | 0.343800 | -0.435% | -0.527% | -0.092% |
| xml | 0.989888 | 0.989999 | 1.223018 | -19.051% | -19.011% | +0.049% |

## Close, inconsistent and losing cases

Close means within 1% of parity after pooling both orders. A sign change means at least one win and one loss across the six session-by-order estimates. The observed range covers those six estimates. Every pooled loss or tie is included.

| Suite and comparison | Case | Pooled time change | Observed range | Finding |
| --- | --- | ---: | ---: | --- |
| fixtures, F/O | `empty` | +3.176% | -1.690% to +11.873% | sign change, loss |
| fixtures, F/O | `one-stored` | +3.133% | -2.640% to +9.637% | sign change, loss |
| fixtures, F/O | `seven-stored-prefix` | +2.849% | -3.667% to +9.705% | sign change, loss |
| fixtures, F/O | `32-high-entropy-stored` | +0.307% | -0.255% to +0.750% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-16384` | +0.195% | -0.170% to +0.977% | close, sign change, loss |
| fixtures, F/O | `prefix-random-262144` | +0.156% | -0.042% to +0.450% | close, sign change, loss |
| fixtures, F/O | `prefix-random-16384` | +0.126% | -0.717% to +0.582% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-4096` | +0.118% | -0.711% to +0.761% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-32769` | +0.117% | -0.011% to +0.284% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-131072` | +0.105% | -0.123% to +0.283% | close, sign change, loss |
| fixtures, F/O | `33027-periodic-window` | +0.098% | -0.337% to +0.643% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-33027` | +0.079% | -0.411% to +0.244% | close, sign change, loss |
| fixtures, F/O | `prefix-natural-262144` | +0.067% | +0.011% to +0.158% | close, loss |
| fixtures, F/O | `prefix-repeated-131072` | +0.057% | -0.101% to +0.262% | close, sign change, loss |
| fixtures, F/O | `heldout-random-65537` | +0.035% | -0.071% to +0.083% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-1048576` | +0.035% | -0.038% to +0.173% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-16384` | +0.033% | -0.365% to +0.410% | close, sign change, loss |
| fixtures, F/O | `prefix-random-65537` | +0.031% | -0.167% to +0.272% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-32767` | +0.027% | -0.378% to +0.347% | close, sign change, loss |
| fixtures, F/O | `prefix-natural-65537` | +0.026% | -0.071% to +0.142% | close, sign change, loss |
| fixtures, F/O | `reymont-prefix-32769` | +0.024% | -0.074% to +0.158% | close, sign change, loss |
| fixtures, F/O | `prefix-random-131072` | +0.013% | -0.077% to +0.207% | close, sign change, loss |
| fixtures, F/O | `prefix-natural-1048576` | +0.013% | -0.058% to +0.052% | close, sign change, loss |
| fixtures, F/O | `prefix-random-1048576` | +0.010% | -0.141% to +0.096% | close, sign change, loss |
| fixtures, F/O | `prefix-random-32768` | +0.010% | -0.204% to +0.301% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-32768` | +0.008% | -0.355% to +0.258% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-65537` | +0.006% | -0.231% to +0.336% | close, sign change, loss |
| fixtures, F/O | `prefix-repeated-1048576` | +0.004% | -0.173% to +0.094% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-32768` | +0.001% | -0.134% to +0.223% | close, sign change, loss |
| fixtures, F/O | `prefix-periodic-65535` | -0.001% | -0.169% to +0.213% | close, sign change |
| fixtures, F/O | `heldout-mixed-131073` | -0.003% | -0.196% to +0.177% | close, sign change |
| fixtures, F/O | `prefix-periodic-33027` | -0.009% | -0.431% to +0.385% | close, sign change |
| fixtures, F/O | `prefix-repeated-32769` | -0.012% | -0.288% to +0.409% | close, sign change |
| fixtures, F/O | `prefix-repeated-8192` | -0.018% | -0.914% to +0.846% | close, sign change |
| fixtures, F/O | `prefix-periodic-65537` | -0.024% | -0.166% to +0.377% | close, sign change |
| fixtures, F/O | `prefix-periodic-65536` | -0.025% | -0.306% to +0.264% | close, sign change |
| fixtures, F/O | `repeated-32769` | -0.027% | -0.308% to +0.597% | close, sign change |
| fixtures, F/O | `prefix-repeated-65535` | -0.027% | -0.236% to +0.100% | close, sign change |
| fixtures, F/O | `reymont-prefix-16384` | -0.030% | -0.128% to +0.070% | close, sign change |
| fixtures, F/O | `eight-overlap` | -0.041% | -0.185% to +0.069% | close, sign change |
| fixtures, F/O | `prefix-natural-32767` | -0.043% | -0.249% to +0.335% | close, sign change |
| fixtures, F/O | `prefix-random-32767` | -0.044% | -0.240% to +0.285% | close, sign change |
| fixtures, F/O | `prefix-natural-65536` | -0.047% | -0.145% to +0.037% | close, sign change |
| fixtures, F/O | `prefix-natural-1024` | -0.051% | -0.337% to +0.480% | close, sign change |
| fixtures, F/O | `prefix-random-1024` | -0.054% | -0.584% to +0.454% | close, sign change |
| fixtures, F/O | `prefix-repeated-65536` | -0.055% | -0.277% to +0.299% | close, sign change |
| fixtures, F/O | `random-256` | -0.061% | -0.384% to +0.194% | close, sign change |
| fixtures, F/O | `prefix-periodic-262144` | -0.061% | -0.177% to +0.032% | close, sign change |
| fixtures, F/O | `prefix-natural-65535` | -0.061% | -0.241% to +0.109% | close, sign change |
| fixtures, F/O | `prefix-repeated-262144` | -0.063% | -0.134% to +0.051% | close, sign change |
| fixtures, F/O | `random-32769` | -0.065% | -0.426% to +0.249% | close, sign change |
| fixtures, F/O | `prefix-random-33027` | -0.065% | -0.387% to +0.160% | close, sign change |
| fixtures, F/O | `eight-literals` | -0.071% | -0.339% to +0.197% | close, sign change |
| fixtures, F/O | `prefix-random-32769` | -0.083% | -0.372% to +0.220% | close, sign change |
| fixtures, F/O | `prefix-natural-32768` | -0.088% | -0.286% to +0.052% | close, sign change |
| fixtures, F/O | `prefix-random-65535` | -0.089% | -0.215% to +0.134% | close, sign change |
| fixtures, F/O | `prefix-natural-16384` | -0.089% | -0.136% to -0.030% | close |
| fixtures, F/O | `reymont-prefix-1024` | -0.090% | -0.283% to +0.064% | close, sign change |
| fixtures, F/O | `repeated-1024` | -0.091% | -0.186% to +0.047% | close, sign change |
| fixtures, F/O | `prefix-periodic-1024` | -0.091% | -0.235% to +0.018% | close, sign change |
| fixtures, F/O | `prefix-natural-32769` | -0.096% | -0.308% to +0.176% | close, sign change |
| fixtures, F/O | `heldout-window-32768` | -0.103% | -0.293% to -0.011% | close |
| fixtures, F/O | `heldout-slides-65537` | -0.104% | -0.269% to +0.027% | close, sign change |
| fixtures, F/O | `320-overlap` | -0.131% | -0.322% to +0.185% | close, sign change |
| fixtures, F/O | `heldout-window-32767` | -0.140% | -0.467% to +0.094% | close, sign change |
| fixtures, F/O | `prefix-periodic-32767` | -0.151% | -0.596% to +0.520% | close, sign change |
| fixtures, F/O | `prefix-random-4096` | -0.163% | -0.634% to +0.531% | close, sign change |
| fixtures, F/O | `random-64` | -0.173% | -0.430% to +0.357% | close, sign change |
| fixtures, F/O | `random-1024` | -0.179% | -0.316% to +0.064% | close, sign change |
| fixtures, F/O | `eight-literals-prefix` | -0.193% | -0.381% to +0.174% | close, sign change |
| fixtures, F/O | `prefix-natural-8192` | -0.196% | -0.585% to +0.424% | close, sign change |
| fixtures, F/O | `prefix-periodic-4096` | -0.206% | -0.772% to +0.664% | close, sign change |
| fixtures, F/O | `prefix-natural-131072` | -0.217% | -0.991% to +0.089% | close, sign change |
| fixtures, F/O | `prefix-natural-33027` | -0.222% | -0.451% to -0.053% | close |
| fixtures, F/O | `prefix-repeated-1024` | -0.222% | -0.963% to +0.067% | close, sign change |
| fixtures, F/O | `prefix-periodic-8192` | -0.233% | -0.507% to +0.391% | close, sign change |
| fixtures, F/O | `16384-distribution-change` | -0.242% | -0.802% to +0.280% | close, sign change |
| fixtures, F/O | `prefix-random-65536` | -0.243% | -0.391% to -0.097% | close |
| fixtures, F/O | `prefix-random-8192` | -0.251% | -1.006% to +0.400% | close, sign change |
| fixtures, F/O | `128-biased-dynamic` | -0.290% | -0.692% to +0.246% | close, sign change |
| fixtures, F/O | `prefix-natural-4096` | -0.358% | -0.696% to +0.175% | close, sign change |
| silesia, O/libdeflate | `x-ray` | -0.435% | -1.070% to -0.020% | close |
| silesia, F/libdeflate | `x-ray` | -0.527% | -1.241% to -0.250% | close |
| silesia, F/O | `mr` | +0.147% | -0.126% to +0.745% | close, sign change, loss |
| silesia, F/O | `webster` | +0.136% | -0.054% to +0.840% | close, sign change, loss |
| silesia, F/O | `ooffice` | +0.130% | -0.318% to +0.955% | close, sign change, loss |
| silesia, F/O | `osdb` | +0.059% | -0.114% to +0.342% | close, sign change, loss |
| silesia, F/O | `xml` | +0.049% | -0.079% to +0.147% | close, sign change, loss |
| silesia, F/O | `mozilla` | +0.047% | -0.021% to +0.285% | close, sign change, loss |
| silesia, F/O | `reymont` | +0.007% | -0.099% to +0.138% | close, sign change, loss |
| silesia, F/O | `dickens` | -0.037% | -0.070% to -0.013% | close |
| silesia, F/O | `sao` | -0.042% | -0.128% to +0.035% | close, sign change |
| silesia, F/O | `nci` | -0.057% | -0.302% to +0.030% | close, sign change |
| silesia, F/O | `samba` | -0.059% | -0.270% to +0.012% | close, sign change |
| silesia, F/O | `x-ray` | -0.092% | -0.569% to +0.119% | close, sign change |

### Individual leg losses and ties against libdeflate

| Session | Order and slot mapping | Suite | Case | Actor | Time change | Actor / libdeflate (ns) |
| --- | --- | --- | --- | --- | ---: | ---: |
| session-1 | reverse-B | silesia | `x-ray` | O | +0.230% | 342756104.500 / 343792770.500 |
| session-3 | forward-B | fixtures | `prefix-natural-1024` | O | +0.809% | 61834.000 / 62125.000 |
| session-3 | forward-B | fixtures | `prefix-natural-1024` | F | +1.715% | 61916.500 / 62125.000 |

[All case results by session and order](cases.csv) · [Machine-readable summary](summary.json)

## Collection records

| Session | Start UTC | End UTC | SHA-256 of record |
| --- | --- | --- | --- |
| session-1 | `2026-11-27T16:21:05.680304+00:00` | `2026-11-27T17:20:45.428277+00:00` | `ae30645c1a771d47aff289eee1f7bb749ebf26eaa988a8c6e5b0258e07a2a16b` |
| session-2 | `2026-11-27T17:20:45.783946+00:00` | `2026-11-27T18:20:27.921161+00:00` | `718b3722f4142c793ccf5b970b4d85e834b4c4e4506aaea3964fe6c975f344e5` |
| session-3 | `2026-11-27T18:20:28.252219+00:00` | `2026-11-27T19:20:41.560300+00:00` | `dfce9158b9d9edd02102e80169405e4649cdb3d6bfecf31d73ba56cf8779eda1` |
