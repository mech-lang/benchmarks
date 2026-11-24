@codex review

Please review [commit `f0cf9ac3552d43deafb461afec5288e585781279`](https://github.com/mech-lang/mech/commit/f0cf9ac3552d43deafb461afec5288e585781279).

The packed scorer now proves that immediate bitwise fields contribute zero where it carries the low cost. The pair loop uses a rebased cost-table pointer and limit after checking the original spans and positive bias. The scalar recovery route consumes the same checked values.

On Apple M1 with libdeflate 1.26 level 12, the encoder won **75/81 forward and 75/81 in reverse** in the full run with 96 balanced blocks per case per order. All 70 previously protected libdeflate wins and all 81 independent control wins held in both orders.

The five additional wins in both orders were `prefix-random-32767`, `prefix-random-32768`, `prefix-random-32769`, `prefix-random-33027` and `random-32769`. The freshly matched control won 69 cases in each order. Its held-out random 65,537-byte case was above parity in each order.

The fixed 18-case average positive gap fell from **5.00254%** to **4.38150%**, a **0.62103 percentage-point** improvement. The largest paired gap moved from 22.54687% to 22.30890%. The worst-order average fell from 5.13445% to 4.49082%.

Matched source-through-executable-link medians were **2.20339 s control**, **2.21022 s candidate** and **0.48119 s libdeflate**.

Candidate encoder text was 65,208 B, lookup data 3,200 B, whole const 17,728 B, stripped executable 210,024 B and peak native stack 4,880 B.

Focused native tests covered immediate high fields, wrapping biased costs, ordered errors, scalar tails, and overlapping and adjacent views. Checker and spill-inspection builds reproduced the selected image. The linked gates checked 162 exact outputs and aliases per image, six named errors, 12 recoveries and 324 deployment smoke runs. The release source reproduced the timed object and linked worker byte for byte.

The independently recomputed full timing result has SHA-256 `0b156999e8fbc62e7722ecd32c9ec202d4eed99516f9605f3e93c15cc4cc57d7`.

### Fixed cohort

| Case | Control F/R (ms) | Candidate F/R (ms) | C F/R (ms) | Control paired × C | Candidate paired × C | Improvement (pp) |
|---|---:|---:|---:|---:|---:|---:|
| prefix-random-4096 | 0.093896/0.093625 | 0.093375/0.093666 | 0.076771/0.077333 | 1.22546868 | 1.22308901 | +0.013220 |
| prefix-random-8192 | 0.148063/0.148896 | 0.147501/0.145459 | 0.125562/0.126167 | 1.17908492 | 1.16489237 | +0.078847 |
| reymont-prefix-1024 | 0.068500/0.068500 | 0.068334/0.068166 | 0.058917/0.059000 | 1.16941572 | 1.16311527 | +0.035002 |
| prefix-natural-1024 | 0.068375/0.068458 | 0.068375/0.068083 | 0.058958/0.059000 | 1.16486410 | 1.16240249 | +0.013676 |
| prefix-random-16384 | 0.254562/0.255416 | 0.251438/0.250375 | 0.237229/0.238312 | 1.07305820 | 1.05578389 | +0.095968 |
| 16384-distribution-change | 0.496437/0.499750 | 0.489562/0.496563 | 0.482250/0.484729 | 1.03061969 | 1.01938775 | +0.062400 |
| prefix-random-33027 | 0.543375/0.543063 | 0.532416/0.532624 | 0.533042/0.535229 | 1.01464451 | 0.99490900 | +0.081358 |
| prefix-random-32767 | 0.523499/0.523458 | 0.513917/0.514542 | 0.518188/0.518667 | 1.00950741 | 0.99152471 | +0.052819 |
| random-32769 | 0.535500/0.535855 | 0.524791/0.523562 | 0.527895/0.527001 | 1.01527303 | 0.99505758 | +0.084850 |
| prefix-random-32769 | 0.533875/0.533021 | 0.525188/0.523125 | 0.526709/0.528791 | 1.00979310 | 0.99185355 | +0.054406 |
| prefix-random-32768 | 0.521958/0.521687 | 0.511250/0.512875 | 0.518521/0.518520 | 1.00568840 | 0.98819886 | +0.031602 |
| heldout-random-65537 | 1.152375/1.151063 | 1.129708/1.134646 | 1.146271/1.148771 | 1.00303889 | 0.98434311 | +0.016883 |
| prefix-random-65535 | 1.153500/1.157334 | 1.135312/1.138167 | 1.160583/1.164375 | 0.99293076 | 0.97597822 | +0.000000 |
| prefix-random-65537 | 1.164688/1.161604 | 1.142771/1.146729 | 1.169458/1.172479 | 0.99197191 | 0.97486528 | +0.000000 |
| prefix-random-65536 | 1.153187/1.151771 | 1.131750/1.134208 | 1.160480/1.163979 | 0.99122382 | 0.97316842 | +0.000000 |
| prefix-random-131072 | 2.390917/2.391792 | 2.352895/2.349813 | 2.473542/2.475688 | 0.96555119 | 0.94804250 | +0.000000 |
| prefix-random-262144 | 4.876166/4.874583 | 4.799187/4.790604 | 5.059187/5.058292 | 0.96328218 | 0.94846579 | +0.000000 |
| prefix-random-1048576 | 19.206563/19.207438 | 18.912979/18.920479 | 20.345042/20.350041 | 0.94453581 | 0.93034342 | +0.000000 |

<details><summary>All case margins and exact recipe changes</summary>

| Case | Control F % | Control R % | Candidate F % | Candidate R % |
|---|---:|---:|---:|---:|
| 128-biased-dynamic | -27.289427 | -27.029536 | -27.239188 | -27.263539 |
| 16384-distribution-change | +2.761979 | +3.362835 | +1.474268 | +2.405409 |
| 32-high-entropy-stored | -55.641962 | -55.345742 | -55.545783 | -55.446042 |
| 320-overlap | -6.791836 | -6.514208 | -7.042356 | -6.999333 |
| 33027-periodic-window | -31.784639 | -31.425840 | -32.835514 | -32.719572 |
| eight-literals | -61.244434 | -61.016735 | -61.335998 | -61.200180 |
| eight-literals-prefix | -61.215971 | -60.970569 | -61.223353 | -61.105205 |
| eight-overlap | -29.256422 | -29.159456 | -29.241545 | -29.455303 |
| empty | -99.316163 | -99.326320 | -99.334119 | -99.336731 |
| heldout-mixed-131073 | -15.789130 | -15.828401 | -16.536557 | -16.522395 |
| heldout-random-65537 | +0.436941 | +0.171013 | -1.629709 | -1.501627 |
| heldout-slides-65537 | -17.637717 | -17.677697 | -17.815937 | -17.886839 |
| heldout-window-32767 | -12.470098 | -12.150658 | -12.654788 | -12.427131 |
| heldout-window-32768 | -12.373525 | -12.165678 | -12.518120 | -12.448726 |
| one-stored | -99.289885 | -99.300356 | -99.303731 | -99.307244 |
| prefix-natural-1024 | +16.431075 | +16.541772 | +16.404332 | +16.076398 |
| prefix-natural-1048576 | -27.146842 | -27.280785 | -27.409008 | -27.388112 |
| prefix-natural-131072 | -26.106912 | -26.156963 | -26.236859 | -26.216052 |
| prefix-natural-16384 | -8.038117 | -8.444783 | -8.316351 | -8.431194 |
| prefix-natural-262144 | -27.004834 | -27.376948 | -27.190020 | -27.491659 |
| prefix-natural-32767 | -12.473580 | -12.265628 | -12.468262 | -12.507689 |
| prefix-natural-32768 | -12.426190 | -12.358885 | -12.362420 | -12.573324 |
| prefix-natural-32769 | -12.382395 | -12.312744 | -12.628175 | -12.553608 |
| prefix-natural-33027 | -12.271279 | -12.187318 | -12.531939 | -12.376760 |
| prefix-natural-4096 | -1.468907 | -0.226616 | -1.811365 | -0.109104 |
| prefix-natural-65535 | -17.485269 | -17.928831 | -17.574539 | -17.994012 |
| prefix-natural-65536 | -17.444849 | -17.916565 | -17.571230 | -18.051524 |
| prefix-natural-65537 | -17.411293 | -17.942029 | -17.594823 | -18.044661 |
| prefix-natural-8192 | -1.883739 | -1.329631 | -1.871002 | -1.180773 |
| prefix-periodic-1024 | -17.072017 | -16.877003 | -17.758822 | -17.775061 |
| prefix-periodic-1048576 | -36.842779 | -36.652402 | -37.901431 | -37.761000 |
| prefix-periodic-131072 | -34.220476 | -34.334589 | -35.372022 | -35.457795 |
| prefix-periodic-16384 | -29.779806 | -30.386455 | -31.251031 | -31.695339 |
| prefix-periodic-262144 | -34.590518 | -34.455509 | -35.742708 | -35.636199 |
| prefix-periodic-32767 | -32.581155 | -32.502521 | -33.805963 | -33.783107 |
| prefix-periodic-32768 | -33.197638 | -33.338456 | -34.019064 | -34.493687 |
| prefix-periodic-32769 | -31.768297 | -31.226395 | -33.058278 | -32.622889 |
| prefix-periodic-33027 | -31.671608 | -31.868009 | -32.860809 | -33.097240 |
| prefix-periodic-4096 | -21.826223 | -22.108854 | -23.426004 | -23.711679 |
| prefix-periodic-65535 | -33.067634 | -33.204013 | -34.277261 | -34.348336 |
| prefix-periodic-65536 | -33.570925 | -33.769230 | -34.875357 | -35.120273 |
| prefix-periodic-65537 | -32.532360 | -32.739397 | -33.969843 | -33.949878 |
| prefix-periodic-8192 | -27.129912 | -26.829368 | -28.492731 | -28.298593 |
| prefix-random-1024 | -22.239708 | -22.018528 | -21.966061 | -22.200052 |
| prefix-random-1048576 | -5.584428 | -5.508395 | -7.032450 | -6.898817 |
| prefix-random-131072 | -3.439860 | -3.449901 | -5.107021 | -5.284395 |
| prefix-random-16384 | +7.241404 | +7.370274 | +5.544305 | +5.612483 |
| prefix-random-262144 | -3.655476 | -3.688085 | -5.004737 | -5.301872 |
| prefix-random-32767 | +0.819831 | +1.081821 | -1.229082 | -0.464502 |
| prefix-random-32768 | +0.418360 | +0.719546 | -1.434886 | -0.924684 |
| prefix-random-32769 | +1.084823 | +0.873907 | -0.698237 | -0.930917 |
| prefix-random-33027 | +1.597535 | +1.331542 | -0.559716 | -0.458457 |
| prefix-random-4096 | +23.002812 | +22.092614 | +22.614796 | +22.003769 |
| prefix-random-65535 | -0.741084 | -0.672752 | -2.521558 | -2.282652 |
| prefix-random-65536 | -0.804529 | -0.950652 | -2.760805 | -2.605449 |
| prefix-random-65537 | -0.709745 | -0.895786 | -2.619122 | -2.407707 |
| prefix-random-8192 | +17.578043 | +18.239870 | +17.394874 | +15.590587 |
| prefix-repeated-1024 | -19.993177 | -20.409898 | -21.046559 | -21.416839 |
| prefix-repeated-1048576 | -24.176971 | -23.870130 | -25.091931 | -24.832643 |
| prefix-repeated-131072 | -20.896134 | -21.222036 | -22.097496 | -22.283176 |
| prefix-repeated-16384 | -18.978480 | -19.189791 | -19.866133 | -20.289764 |
| prefix-repeated-262144 | -21.692437 | -21.516854 | -22.635908 | -22.578226 |
| prefix-repeated-32767 | -20.926332 | -21.308722 | -22.264549 | -22.306807 |
| prefix-repeated-32768 | -20.522944 | -20.535335 | -21.481243 | -21.493621 |
| prefix-repeated-32769 | -20.667820 | -20.709715 | -21.759559 | -21.572013 |
| prefix-repeated-33027 | -20.268324 | -20.594376 | -21.515130 | -21.517146 |
| prefix-repeated-4096 | -14.198552 | -15.108007 | -14.927772 | -16.229421 |
| prefix-repeated-65535 | -21.658357 | -21.558679 | -22.708557 | -22.668473 |
| prefix-repeated-65536 | -20.858871 | -21.303060 | -21.967161 | -22.390054 |
| prefix-repeated-65537 | -21.279840 | -21.223663 | -22.297622 | -22.355504 |
| prefix-repeated-8192 | -16.614810 | -17.267498 | -17.540126 | -18.705926 |
| random-1024 | -22.903521 | -22.627235 | -22.619912 | -22.824486 |
| random-256 | -33.433818 | -32.184864 | -33.388499 | -32.952801 |
| random-32769 | +1.162185 | +1.893740 | -0.648097 | -0.340150 |
| random-64 | -51.697540 | -51.498791 | -51.723983 | -51.164188 |
| repeated-1024 | -20.092954 | -20.220742 | -20.977338 | -21.117738 |
| repeated-32769 | -20.201231 | -20.138394 | -21.168842 | -21.437517 |
| reymont-prefix-1024 | +16.795210 | +17.088117 | +16.402911 | +16.220216 |
| reymont-prefix-16384 | -8.197508 | -8.377415 | -8.431105 | -8.357952 |
| reymont-prefix-32769 | -12.316264 | -12.256530 | -12.502012 | -12.438187 |
| seven-stored-prefix | -99.268367 | -99.218141 | -99.271094 | -99.277363 |

Start with the previous qualified recipe and build the original codec using this commit. Set the two flags below and replace the scorer register and block profiles. [Previous recipe](https://github.com/mech-lang/mech/pull/999#issuecomment-7102280001)

```sh
MECH_FOLD_NARROW_PACKED_WORDS=immediates
MECH_PAIR_REBASE_LITERAL_COSTS=1
```

Capture the pre-allocation VCode for `mech_compact_numeric_3009_no_growth_composed` with its existing profile entries removed. Use the text between the register-allocation markers as `expected_vcode` and the first JSON object for its hash and frequencies. Use the second object as the scorer block layout.

```json
{"expected_vcode_sha256":"089e080174de092e937d951d58980e422fc25f738fd090d35f9ba8821e67adb3","block_frequencies":[2,2,2,2,2,171,171,171,171,171,171,171,171,171,171,171,2,2,169,169,169,169,169,169,169,169,169,169,169,1,1,1,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,1,169,1,1,1,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,1,1,1,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,138,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,1,1,1,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,262,1,1,1,1,262,262,262,262,262,262,262,262,262,231,36,231,231,262,62,31,4,29,25,4,26,16,10,26,99,99,26,31,262,23,259,259,259,262,262,262,262,262,262,262,262,262,262,169,262,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,169,138,31,138,138,138,138,138,138,138,138,138,138,138,138,138,138,31,4096,43,4096,43,4066,43,4066,4066,4096,43,43,43,31,42,31,12,12,1,12,31,31,12]}
{"order":[0,100,112,1168,1248,1416,1436,1464,208,216,220,236,244,248,252,292,320,328,332,388,396,448,300,308,1144,1160,1224,128,132,500,1096,1140,404,528,728,748,844,888,1008,1044,1068,1556,1572,1624,1536,1540,1576,536,592,660,760,672,1668,1676,1692,1700,1708,1716,1768,1780,1784,1788],"literal_offset":1792,"thread_jumps":true}
```

The selected object has SHA-256 `96b6e21baa3a9b53861d638ebe96d9df889e42c8915eb7f49f2b660da041919c`. Canonical bytecode has SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.

</details>
