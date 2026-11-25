@codex review

Review [2b301734fb43a4abff0d38d68d881e2bf85bd969](https://github.com/mech-lang/mech/commit/2b301734fb43a4abff0d38d68d881e2bf85bd969) against [ac44d607b6dbf626ddc850c93b896390837afb09](https://github.com/mech-lang/mech/commit/ac44d607b6dbf626ddc850c93b896390837afb09). [Parent review request](https://github.com/mech-lang/mech/pull/999#issuecomment-7120604501).

The compiler proves a checked loop writes a constant byte at each index read from a byte view. It groups eight iterations once the source span and the full destination byte range are in bounds. Interleaved loads and stores preserve overlapping views. The scalar loop handles the tail, small spans, and original failure paths.

The terminal runtime copies borrowed prefixes shorter than 16 bytes with exact-width loads and stores. Longer prefixes use the existing general copy. The result retains its allocation capacity and ownership.

The encoder fixture is `hosts/gpu/tests/fixtures/native/compact-compiler-regression.mec`. Use the parent code-generation options and enable `MECH_COMPACT_CHECKED_BYTE_SCATTER=1`.

### Runtime results

Each full measurement paired both Mech workers with libdeflate and the independent reference on all 81 inputs, with 96 balanced blocks per case in each execution order. A positive margin below means less elapsed time than libdeflate, calculated as 100 × (1 − paired time ratio).

An intervening repeat stopped after 37 forward cases. The 96-block paired result on `prefix-natural-1024` was 1.23% slower than libdeflate. The raw observations show a nine-block interval in which both Mech workers slowed.

**First full run**. Candidate wins against libdeflate were 81/81 forward, 81/81 reverse and 81/81 in both. The matched control won 79/81 forward, 81/81 reverse and 79/81 in both. The candidate also won all 81 against the independent reference in each order.

The fixed-18 mean positive slowdown fell from 0.031151% to 0.000000%, an improvement of 0.031151 percentage points.

The candidate’s worst paired cohort deficit was 0.000000%. The mean using the slower order of each cohort case was 0.000000%.

| 1 KiB case | Order | Control µs | Candidate µs | libdeflate µs | Control margin | Candidate margin | Change (pp) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-natural-1024` | forward | 58.875 | 58.166 | 58.959 | -1.28333% | +0.01361% | +1.29694 |
| `prefix-natural-1024` | reverse | 58.625 | 57.792 | 58.959 | +0.19971% | +1.64339% | +1.44368 |
| `reymont-prefix-1024` | forward | 58.708 | 57.875 | 58.959 | -0.10400% | +1.07362% | +1.17762 |
| `reymont-prefix-1024` | reverse | 58.667 | 57.792 | 58.958 | +0.06066% | +1.41585% | +1.35519 |

| Short prefix vs independent reference | Control ns | Candidate ns | Reference ns | Control margin | Candidate margin |
| --- | ---: | ---: | ---: | ---: |
| `seven-stored-prefix`, forward | 42.000 | 41.000 | 42.000 | +3.83775% | +9.64766% |
| `seven-stored-prefix`, reverse | 42.000 | 41.000 | 42.000 | +5.30022% | +11.79101% |

<details><summary>All 81 matched margins against libdeflate for full</summary>

| Case | Control forward | Control reverse | Candidate forward | Candidate reverse |
| --- | ---: | ---: | ---: | ---: |
| `128-biased-dynamic` | +38.84388% | +39.32335% | +39.09069% | +39.12344% |
| `16384-distribution-change` | +5.28911% | +3.56500% | +5.21555% | +5.14738% |
| `32-high-entropy-stored` | +58.77197% | +58.86352% | +58.80977% | +58.92948% |
| `320-overlap` | +22.52934% | +22.08500% | +22.11945% | +21.76287% |
| `33027-periodic-window` | +37.10460% | +37.90400% | +36.17250% | +36.73477% |
| `eight-literals` | +63.52484% | +63.39691% | +63.56517% | +63.58218% |
| `eight-literals-prefix` | +63.43257% | +63.40828% | +63.37834% | +63.56946% |
| `eight-overlap` | +43.23360% | +43.54197% | +43.21261% | +43.66956% |
| `empty` | +99.30580% | +99.31189% | +99.33240% | +99.32448% |
| `heldout-mixed-131073` | +20.78911% | +20.75514% | +20.82849% | +20.51034% |
| `heldout-random-65537` | +7.14359% | +7.19619% | +7.10658% | +7.04826% |
| `heldout-slides-65537` | +20.17115% | +20.47306% | +20.22449% | +20.28252% |
| `heldout-window-32767` | +15.78553% | +15.87693% | +15.80576% | +15.74026% |
| `heldout-window-32768` | +15.83116% | +15.86606% | +15.79943% | +15.74309% |
| `one-stored` | +99.28978% | +99.29100% | +99.31033% | +99.31621% |
| `prefix-natural-1024` | -1.28333% | +0.19971% | +0.01361% | +1.64339% |
| `prefix-natural-1048576` | +29.37762% | +29.29299% | +29.13304% | +29.11257% |
| `prefix-natural-131072` | +28.51726% | +28.45911% | +28.77226% | +28.55592% |
| `prefix-natural-16384` | +12.65641% | +12.36614% | +12.86707% | +12.59237% |
| `prefix-natural-262144` | +29.41218% | +29.38244% | +29.35388% | +29.43096% |
| `prefix-natural-32767` | +15.69381% | +15.86981% | +15.69015% | +15.84509% |
| `prefix-natural-32768` | +15.69707% | +15.86150% | +15.75327% | +15.70369% |
| `prefix-natural-32769` | +15.79618% | +15.64278% | +15.72150% | +15.53630% |
| `prefix-natural-33027` | +15.72489% | +15.58762% | +15.70966% | +15.63625% |
| `prefix-natural-4096` | +8.59956% | +8.23907% | +9.47360% | +8.90465% |
| `prefix-natural-65535` | +20.51159% | +20.78152% | +20.54066% | +20.77280% |
| `prefix-natural-65536` | +20.47409% | +20.80427% | +20.53127% | +20.88034% |
| `prefix-natural-65537` | +20.33417% | +20.79917% | +20.60084% | +20.65077% |
| `prefix-natural-8192` | +6.63605% | +5.89881% | +7.12105% | +6.73868% |
| `prefix-periodic-1024` | +28.09784% | +31.19445% | +29.56428% | +32.25702% |
| `prefix-periodic-1048576` | +42.62273% | +42.30014% | +40.89294% | +40.68322% |
| `prefix-periodic-131072` | +39.93372% | +39.82209% | +38.23101% | +38.15682% |
| `prefix-periodic-16384` | +36.07079% | +36.77612% | +35.77499% | +35.88673% |
| `prefix-periodic-262144` | +40.01564% | +39.90950% | +38.32042% | +38.22894% |
| `prefix-periodic-32767` | +39.05229% | +39.14192% | +38.14629% | +38.24463% |
| `prefix-periodic-32768` | +38.95597% | +39.07821% | +37.95583% | +38.08582% |
| `prefix-periodic-32769` | +37.47227% | +38.42760% | +36.53444% | +37.49487% |
| `prefix-periodic-33027` | +37.90318% | +37.47258% | +37.16454% | +37.43593% |
| `prefix-periodic-4096` | +29.78282% | +31.24735% | +32.63095% | +33.07049% |
| `prefix-periodic-65535` | +39.47349% | +39.58143% | +38.04585% | +38.10941% |
| `prefix-periodic-65536` | +38.94387% | +39.38109% | +37.86180% | +37.97920% |
| `prefix-periodic-65537` | +38.83148% | +38.56364% | +37.34618% | +37.05502% |
| `prefix-periodic-8192` | +34.86907% | +34.71724% | +35.61282% | +35.23613% |
| `prefix-random-1024` | +31.80952% | +32.60693% | +33.65884% | +36.65745% |
| `prefix-random-1048576` | +10.74517% | +10.62307% | +10.17853% | +10.27729% |
| `prefix-random-131072` | +10.21213% | +10.07484% | +9.99734% | +9.75661% |
| `prefix-random-16384` | +11.61764% | +12.06159% | +12.63528% | +14.10670% |
| `prefix-random-262144` | +10.09110% | +9.54483% | +8.71300% | +9.27159% |
| `prefix-random-32767` | +11.25018% | +11.24631% | +11.52453% | +11.76613% |
| `prefix-random-32768` | +11.42377% | +11.06971% | +11.75385% | +10.84507% |
| `prefix-random-32769` | +10.72255% | +10.41726% | +11.15242% | +10.83857% |
| `prefix-random-33027` | +10.24626% | +9.34751% | +10.88910% | +10.42645% |
| `prefix-random-4096` | +7.76765% | +7.95244% | +11.79088% | +11.39308% |
| `prefix-random-65535` | +9.05104% | +8.81267% | +9.11348% | +8.92440% |
| `prefix-random-65536` | +9.07992% | +8.96791% | +9.13153% | +9.10527% |
| `prefix-random-65537` | +8.86308% | +8.74455% | +8.87969% | +8.73239% |
| `prefix-random-8192` | +10.56221% | +11.04557% | +14.63436% | +13.08729% |
| `prefix-repeated-1024` | +31.42168% | +31.05549% | +32.49689% | +32.46797% |
| `prefix-repeated-1048576` | +29.13741% | +28.71387% | +27.74821% | +27.45758% |
| `prefix-repeated-131072` | +26.04904% | +26.36211% | +25.01590% | +25.01217% |
| `prefix-repeated-16384` | +17.93939% | +24.54506% | +20.46627% | +24.16834% |
| `prefix-repeated-262144` | +26.34706% | +26.75851% | +25.40493% | +25.38626% |
| `prefix-repeated-32767` | +26.12637% | +25.85533% | +25.08087% | +25.08263% |
| `prefix-repeated-32768` | +25.97057% | +26.01643% | +25.02656% | +25.17989% |
| `prefix-repeated-32769` | +25.37588% | +25.03789% | +24.43784% | +23.67433% |
| `prefix-repeated-33027` | +25.34122% | +25.46097% | +24.30590% | +24.53330% |
| `prefix-repeated-4096` | +22.29369% | +20.45269% | +24.48924% | +23.75894% |
| `prefix-repeated-65535` | +26.38374% | +26.20461% | +25.10256% | +25.09202% |
| `prefix-repeated-65536` | +26.25687% | +26.15957% | +25.05234% | +25.11138% |
| `prefix-repeated-65537` | +25.84276% | +25.87152% | +24.58357% | +24.69386% |
| `prefix-repeated-8192` | +24.65598% | +23.82926% | +25.17732% | +24.49794% |
| `random-1024` | +34.92988% | +34.96196% | +37.20552% | +37.33614% |
| `random-256` | +41.52295% | +40.06909% | +41.63520% | +39.57069% |
| `random-32769` | +10.13849% | +9.90603% | +10.43500% | +10.56898% |
| `random-64` | +55.68612% | +55.53516% | +55.55755% | +55.55832% |
| `repeated-1024` | +32.34611% | +32.21826% | +33.20252% | +33.17434% |
| `repeated-32769` | +24.68036% | +25.05944% | +23.51586% | +24.16816% |
| `reymont-prefix-1024` | -0.10400% | +0.06066% | +1.07362% | +1.41585% |
| `reymont-prefix-16384` | +12.46200% | +12.29225% | +12.79651% | +12.48323% |
| `reymont-prefix-32769` | +15.73842% | +15.69998% | +15.50067% | +15.62595% |
| `seven-stored-prefix` | +99.20451% | +99.21417% | +99.25257% | +99.26803% |

</details>

<details><summary>All 81 matched margins against the independent reference for full</summary>

| Case | Control forward | Control reverse | Candidate forward | Candidate reverse |
| --- | ---: | ---: | ---: | ---: |
| `128-biased-dynamic` | +95.45020% | +95.45412% | +95.46856% | +95.43914% |
| `16384-distribution-change` | +45.64609% | +44.77639% | +45.60387% | +45.68254% |
| `32-high-entropy-stored` | +96.76108% | +96.76012% | +96.76405% | +96.76531% |
| `320-overlap` | +92.84623% | +92.82667% | +92.80838% | +92.79702% |
| `33027-periodic-window` | +70.49240% | +70.72167% | +70.05510% | +70.17038% |
| `eight-literals` | +97.10635% | +97.11165% | +97.10955% | +97.12627% |
| `eight-literals-prefix` | +97.12095% | +97.11818% | +97.11668% | +97.13087% |
| `eight-overlap` | +95.59058% | +95.59840% | +95.58895% | +95.60835% |
| `empty` | +10.52931% | +12.54012% | +13.95719% | +14.13975% |
| `heldout-mixed-131073` | +31.57771% | +31.60376% | +31.61173% | +31.39248% |
| `heldout-random-65537` | +45.15934% | +45.19644% | +45.13748% | +45.10909% |
| `heldout-slides-65537` | +8.89020% | +9.50748% | +8.95108% | +9.29067% |
| `heldout-window-32767` | +7.25987% | +7.15735% | +7.28216% | +7.00651% |
| `heldout-window-32768` | +7.60120% | +7.13236% | +7.56637% | +6.99663% |
| `one-stored` | +19.48673% | +19.77377% | +21.81738% | +22.62699% |
| `prefix-natural-1024` | +81.85449% | +82.23694% | +82.08684% | +82.49389% |
| `prefix-natural-1048576` | +12.29088% | +12.47421% | +11.98712% | +12.25086% |
| `prefix-natural-131072` | +13.27540% | +13.20907% | +13.58477% | +13.32652% |
| `prefix-natural-16384` | +13.01694% | +12.93674% | +13.22673% | +13.16149% |
| `prefix-natural-262144` | +12.96803% | +12.61854% | +12.89614% | +12.67857% |
| `prefix-natural-32767` | +7.25609% | +7.00086% | +7.25206% | +6.97354% |
| `prefix-natural-32768` | +7.04516% | +7.06701% | +7.10713% | +6.89270% |
| `prefix-natural-32769` | +7.13709% | +7.07657% | +7.05473% | +6.95928% |
| `prefix-natural-33027` | +7.39920% | +7.00588% | +7.38246% | +7.05945% |
| `prefix-natural-4096` | +45.78662% | +45.98673% | +46.30505% | +46.37851% |
| `prefix-natural-65535` | +5.65057% | +5.82770% | +5.68508% | +5.81734% |
| `prefix-natural-65536` | +5.52485% | +5.96936% | +5.59278% | +6.05968% |
| `prefix-natural-65537` | +5.33541% | +5.92137% | +5.65229% | +5.74509% |
| `prefix-natural-8192` | +24.59875% | +24.39113% | +24.99045% | +25.06596% |
| `prefix-periodic-1024` | +89.98822% | +90.43691% | +90.19241% | +90.58460% |
| `prefix-periodic-1048576` | +66.15777% | +66.08163% | +65.13750% | +65.13114% |
| `prefix-periodic-131072` | +66.92893% | +66.86261% | +65.99146% | +65.94562% |
| `prefix-periodic-16384` | +75.02407% | +75.11064% | +74.90850% | +74.76051% |
| `prefix-periodic-262144` | +65.96179% | +65.95359% | +64.99983% | +65.00141% |
| `prefix-periodic-32767` | +71.51356% | +71.53847% | +71.09010% | +71.11883% |
| `prefix-periodic-32768` | +71.53341% | +71.55583% | +71.06702% | +71.09248% |
| `prefix-periodic-32769` | +70.67910% | +70.96055% | +70.23933% | +70.52065% |
| `prefix-periodic-33027` | +70.87043% | +70.52898% | +70.52393% | +70.51171% |
| `prefix-periodic-4096` | +83.12708% | +83.08470% | +83.81147% | +83.53325% |
| `prefix-periodic-65535` | +68.61458% | +68.65078% | +67.87429% | +67.88700% |
| `prefix-periodic-65536` | +68.36724% | +68.51671% | +67.80663% | +67.78862% |
| `prefix-periodic-65537` | +68.21867% | +68.02084% | +67.44696% | +67.23556% |
| `prefix-periodic-8192` | +79.47197% | +79.15929% | +79.70638% | +79.32494% |
| `prefix-random-1024` | +92.58085% | +92.74588% | +92.78205% | +93.18187% |
| `prefix-random-1048576` | +37.02992% | +36.87664% | +36.63014% | +36.63243% |
| `prefix-random-131072` | +42.38785% | +42.17237% | +42.25003% | +41.96773% |
| `prefix-random-16384` | +67.31163% | +67.30228% | +67.68801% | +68.06271% |
| `prefix-random-262144` | +39.49101% | +39.20942% | +38.56355% | +39.02579% |
| `prefix-random-32767` | +56.63116% | +56.55673% | +56.76522% | +56.81117% |
| `prefix-random-32768` | +56.81987% | +55.86960% | +56.98078% | +55.75812% |
| `prefix-random-32769` | +56.22530% | +55.75203% | +56.43608% | +55.96013% |
| `prefix-random-33027` | +55.58494% | +55.11287% | +55.90306% | +55.64711% |
| `prefix-random-4096` | +81.08885% | +80.95842% | +81.91376% | +81.67017% |
| `prefix-random-65535` | +46.46127% | +46.46565% | +46.49802% | +46.53125% |
| `prefix-random-65536` | +46.61653% | +46.47487% | +46.64683% | +46.55563% |
| `prefix-random-65537` | +46.37755% | +46.22193% | +46.38732% | +46.21476% |
| `prefix-random-8192` | +74.94274% | +75.21344% | +76.08361% | +75.78235% |
| `prefix-repeated-1024` | +90.30609% | +90.08616% | +90.45808% | +90.28927% |
| `prefix-repeated-1048576` | +54.96800% | +54.79523% | +54.08519% | +53.99858% |
| `prefix-repeated-131072` | +55.85379% | +56.05780% | +55.23704% | +55.25224% |
| `prefix-repeated-16384` | +62.86650% | +67.06119% | +64.00995% | +66.89673% |
| `prefix-repeated-262144` | +54.67834% | +54.97132% | +54.09861% | +54.12766% |
| `prefix-repeated-32767` | +62.27103% | +62.00146% | +61.73707% | +61.60545% |
| `prefix-repeated-32768` | +62.12242% | +62.09677% | +61.63941% | +61.66819% |
| `prefix-repeated-32769` | +61.70103% | +61.64334% | +61.21961% | +60.94564% |
| `prefix-repeated-33027` | +61.58960% | +61.62780% | +61.05695% | +61.15024% |
| `prefix-repeated-4096` | +79.56287% | +79.00606% | +80.14031% | +79.87864% |
| `prefix-repeated-65535` | +58.36157% | +58.27694% | +57.63691% | +57.64790% |
| `prefix-repeated-65536` | +58.26744% | +58.19384% | +57.58577% | +57.60039% |
| `prefix-repeated-65537` | +58.09013% | +57.99034% | +57.37850% | +57.32294% |
| `prefix-repeated-8192` | +73.92476% | +73.63534% | +74.10519% | +73.86679% |
| `random-1024` | +93.08995% | +93.06048% | +93.33161% | +93.31380% |
| `random-256` | +94.92613% | +94.74184% | +94.93587% | +94.69811% |
| `random-32769` | +56.19187% | +55.82436% | +56.33643% | +56.14942% |
| `random-64` | +96.44553% | +96.41780% | +96.43522% | +96.41967% |
| `repeated-1024` | +90.46912% | +90.40167% | +90.58977% | +90.53706% |
| `repeated-32769` | +61.47837% | +61.48876% | +60.88279% | +61.03074% |
| `reymont-prefix-1024` | +82.30216% | +82.27435% | +82.51035% | +82.51471% |
| `reymont-prefix-16384` | +12.92897% | +12.85204% | +13.26169% | +13.04179% |
| `reymont-prefix-32769` | +7.26834% | +7.04407% | +7.00669% | +6.96244% |
| `seven-stored-prefix` | +3.83775% | +5.30022% | +9.64766% | +11.79101% |

</details>

Timing SHA-256 `b2e26dd96b420cbd0079ceaa5a8b9fdb802dc5a3a80a6081081558f529511501`. Raw-observation verification SHA-256 `2e2417f5d34cfabf1711333c1afb005b357df5408f015179b0b2e9a57cf000e2`.

**Confirmation run**. Candidate wins against libdeflate were 81/81 forward, 81/81 reverse and 81/81 in both. The matched control won 80/81 forward, 79/81 reverse and 79/81 in both. The candidate also won all 81 against the independent reference in each order.

The fixed-18 mean positive slowdown fell from 0.008715% to 0.000000%, an improvement of 0.008715 percentage points.

The candidate’s worst paired cohort deficit was 0.000000%. The mean using the slower order of each cohort case was 0.000000%.

| 1 KiB case | Order | Control µs | Candidate µs | libdeflate µs | Control margin | Candidate margin | Change (pp) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix-natural-1024` | forward | 58.500 | 57.750 | 58.958 | +0.43897% | +1.74505% | +1.30608 |
| `prefix-natural-1024` | reverse | 58.667 | 57.833 | 58.917 | -0.12280% | +1.39877% | +1.52157 |
| `reymont-prefix-1024` | forward | 58.541 | 57.750 | 59.000 | -0.00104% | +1.83310% | +1.83413 |
| `reymont-prefix-1024` | reverse | 58.667 | 57.916 | 59.000 | -0.31293% | +1.43956% | +1.75249 |

| Short prefix vs independent reference | Control ns | Candidate ns | Reference ns | Control margin | Candidate margin |
| --- | ---: | ---: | ---: | ---: |
| `seven-stored-prefix`, forward | 42.000 | 42.000 | 42.000 | +11.01158% | +9.89730% |
| `seven-stored-prefix`, reverse | 41.000 | 41.000 | 42.000 | +12.02762% | +11.15283% |

<details><summary>All 81 matched margins against libdeflate for qualify</summary>

| Case | Control forward | Control reverse | Candidate forward | Candidate reverse |
| --- | ---: | ---: | ---: | ---: |
| `128-biased-dynamic` | +37.94229% | +39.06837% | +38.04405% | +39.33469% |
| `16384-distribution-change` | +4.81297% | +3.32962% | +4.89482% | +4.80221% |
| `32-high-entropy-stored` | +58.45606% | +58.80887% | +58.39139% | +58.74893% |
| `320-overlap` | +22.57934% | +21.89412% | +22.50610% | +21.54391% |
| `33027-periodic-window` | +37.55019% | +37.51458% | +36.25560% | +36.28288% |
| `eight-literals` | +63.54353% | +63.39090% | +63.78805% | +63.45566% |
| `eight-literals-prefix` | +63.27357% | +63.56022% | +63.41799% | +63.65612% |
| `eight-overlap` | +43.55806% | +43.78971% | +43.79297% | +43.78786% |
| `empty` | +99.30697% | +99.30799% | +99.31901% | +99.32463% |
| `heldout-mixed-131073` | +20.96339% | +20.72420% | +20.88667% | +20.80708% |
| `heldout-random-65537` | +7.16996% | +7.05661% | +7.17792% | +7.24151% |
| `heldout-slides-65537` | +20.25935% | +20.58600% | +20.16734% | +20.47921% |
| `heldout-window-32767` | +15.84641% | +15.89494% | +15.72665% | +15.81771% |
| `heldout-window-32768` | +15.91595% | +15.82370% | +15.76203% | +15.74734% |
| `one-stored` | +99.28793% | +99.28218% | +99.30554% | +99.30988% |
| `prefix-natural-1024` | +0.43897% | -0.12280% | +1.74505% | +1.39877% |
| `prefix-natural-1048576` | +29.34348% | +29.26107% | +29.20620% | +29.24924% |
| `prefix-natural-131072` | +28.66826% | +28.63827% | +28.61700% | +28.67387% |
| `prefix-natural-16384` | +12.48911% | +12.38695% | +12.71707% | +12.57115% |
| `prefix-natural-262144` | +29.39374% | +29.55249% | +29.28557% | +29.58562% |
| `prefix-natural-32767` | +15.66019% | +15.81802% | +15.80004% | +15.76265% |
| `prefix-natural-32768` | +15.63979% | +15.90611% | +15.78327% | +15.86312% |
| `prefix-natural-32769` | +15.84444% | +15.66714% | +15.70241% | +15.61626% |
| `prefix-natural-33027` | +15.65113% | +15.55320% | +15.52537% | +15.53316% |
| `prefix-natural-4096` | +8.37673% | +7.67167% | +9.49642% | +8.56307% |
| `prefix-natural-65535` | +20.65887% | +21.03338% | +20.61816% | +21.02938% |
| `prefix-natural-65536` | +20.62737% | +21.02567% | +20.73426% | +21.18451% |
| `prefix-natural-65537` | +20.42224% | +20.99832% | +20.58444% | +21.02986% |
| `prefix-natural-8192` | +6.61701% | +5.82531% | +7.39428% | +6.57825% |
| `prefix-periodic-1024` | +29.24169% | +30.88354% | +30.42269% | +31.59341% |
| `prefix-periodic-1048576` | +42.57871% | +42.30043% | +40.83810% | +40.59885% |
| `prefix-periodic-131072` | +39.31686% | +39.35238% | +37.75721% | +37.84084% |
| `prefix-periodic-16384` | +35.28460% | +35.64270% | +34.91484% | +34.87167% |
| `prefix-periodic-262144` | +39.88237% | +39.71104% | +38.09494% | +37.99239% |
| `prefix-periodic-32767` | +38.60879% | +38.46062% | +37.38183% | +37.04879% |
| `prefix-periodic-32768` | +38.50776% | +38.47004% | +37.37819% | +37.03597% |
| `prefix-periodic-32769` | +37.79433% | +37.39631% | +36.85682% | +36.22564% |
| `prefix-periodic-33027` | +37.57877% | +37.77565% | +36.41948% | +36.56672% |
| `prefix-periodic-4096` | +27.55018% | +28.93727% | +29.67905% | +30.29973% |
| `prefix-periodic-65535` | +39.03650% | +39.02397% | +37.46879% | +37.55035% |
| `prefix-periodic-65536` | +38.89190% | +38.94192% | +37.38705% | +37.66042% |
| `prefix-periodic-65537` | +38.57855% | +38.46345% | +37.07954% | +37.11678% |
| `prefix-periodic-8192` | +33.18573% | +32.87997% | +33.80991% | +33.39956% |
| `prefix-random-1024` | +34.74288% | +34.43992% | +37.26657% | +37.06322% |
| `prefix-random-1048576` | +10.34973% | +10.52953% | +9.89385% | +10.34101% |
| `prefix-random-131072` | +9.80788% | +9.41012% | +9.78938% | +9.45095% |
| `prefix-random-16384` | +10.80605% | +12.10528% | +13.11309% | +13.59511% |
| `prefix-random-262144` | +9.59374% | +9.33166% | +9.16763% | +9.14812% |
| `prefix-random-32767` | +11.07775% | +10.79725% | +11.40660% | +11.25898% |
| `prefix-random-32768` | +10.92758% | +10.81441% | +11.34539% | +11.21282% |
| `prefix-random-32769` | +10.11798% | +9.86764% | +10.38755% | +10.58061% |
| `prefix-random-33027` | +9.73110% | +9.70297% | +9.99579% | +10.26568% |
| `prefix-random-4096` | +6.35308% | +5.06698% | +9.79938% | +10.44564% |
| `prefix-random-65535` | +8.90811% | +8.55969% | +8.80787% | +8.68784% |
| `prefix-random-65536` | +8.94528% | +8.45375% | +8.96419% | +8.80139% |
| `prefix-random-65537` | +8.33361% | +8.33176% | +8.46802% | +8.37896% |
| `prefix-random-8192` | +12.38847% | +9.06791% | +13.36919% | +13.03793% |
| `prefix-repeated-1024` | +32.28692% | +32.61277% | +33.31939% | +33.61371% |
| `prefix-repeated-1048576` | +29.14084% | +28.99980% | +27.60820% | +27.50471% |
| `prefix-repeated-131072` | +26.18483% | +26.22134% | +24.82256% | +24.73022% |
| `prefix-repeated-16384` | +23.55200% | +24.00071% | +23.29947% | +23.21637% |
| `prefix-repeated-262144` | +26.67429% | +26.62753% | +25.20495% | +25.20877% |
| `prefix-repeated-32767` | +25.44040% | +25.61266% | +24.54449% | +24.32583% |
| `prefix-repeated-32768` | +25.47528% | +25.73936% | +24.41353% | +24.52214% |
| `prefix-repeated-32769` | +24.87362% | +24.90623% | +23.69404% | +24.02009% |
| `prefix-repeated-33027` | +24.95905% | +24.76836% | +24.00749% | +23.71676% |
| `prefix-repeated-4096` | +19.91518% | +20.97490% | +21.97486% | +21.78828% |
| `prefix-repeated-65535` | +26.04140% | +26.00086% | +24.68385% | +24.80833% |
| `prefix-repeated-65536` | +25.78543% | +25.90105% | +24.69469% | +24.82218% |
| `prefix-repeated-65537` | +25.78055% | +25.73243% | +24.15295% | +24.51206% |
| `prefix-repeated-8192` | +23.29577% | +22.82150% | +23.67103% | +23.09951% |
| `random-1024` | +33.29975% | +34.59176% | +35.78413% | +37.16116% |
| `random-256` | +40.74183% | +41.63657% | +40.73488% | +41.56187% |
| `random-32769` | +9.85940% | +9.25614% | +10.40994% | +9.48631% |
| `random-64` | +55.57110% | +55.75607% | +55.44840% | +55.64558% |
| `repeated-1024` | +29.87324% | +32.02655% | +32.23553% | +33.14745% |
| `repeated-32769` | +24.87300% | +24.53295% | +23.91837% | +23.59375% |
| `reymont-prefix-1024` | -0.00104% | -0.31293% | +1.83310% | +1.43956% |
| `reymont-prefix-16384` | +12.60773% | +12.45863% | +12.93980% | +12.64838% |
| `reymont-prefix-32769` | +15.92711% | +15.69297% | +15.76563% | +15.64400% |
| `seven-stored-prefix` | +99.26354% | +99.26915% | +99.25431% | +99.26188% |

</details>

<details><summary>All 81 matched margins against the independent reference for qualify</summary>

| Case | Control forward | Control reverse | Candidate forward | Candidate reverse |
| --- | ---: | ---: | ---: | ---: |
| `128-biased-dynamic` | +95.44255% | +95.41903% | +95.45002% | +95.43905% |
| `16384-distribution-change` | +45.38144% | +44.73068% | +45.42841% | +45.57260% |
| `32-high-entropy-stored` | +96.76834% | +96.75276% | +96.76331% | +96.74803% |
| `320-overlap` | +92.87193% | +92.79027% | +92.86519% | +92.75794% |
| `33027-periodic-window` | +70.58848% | +70.62625% | +69.97878% | +70.04724% |
| `eight-literals` | +97.14738% | +97.10471% | +97.16651% | +97.10983% |
| `eight-literals-prefix` | +97.13014% | +97.11689% | +97.14143% | +97.12448% |
| `eight-overlap` | +95.62848% | +95.59213% | +95.64667% | +95.59199% |
| `empty` | +11.48037% | +11.21427% | +13.01787% | +13.34942% |
| `heldout-mixed-131073` | +31.70800% | +31.61203% | +31.64171% | +31.68352% |
| `heldout-random-65537` | +45.16549% | +45.30414% | +45.17019% | +45.41296% |
| `heldout-slides-65537` | +8.98571% | +9.43604% | +8.88070% | +9.31427% |
| `heldout-window-32767` | +7.73738% | +7.27133% | +7.60609% | +7.18618% |
| `heldout-window-32768` | +7.26504% | +7.25510% | +7.09529% | +7.17096% |
| `one-stored` | +19.39003% | +18.19376% | +21.38363% | +21.35166% |
| `prefix-natural-1024` | +82.43550% | +82.30269% | +82.66592% | +82.57164% |
| `prefix-natural-1048576` | +12.43219% | +12.36024% | +12.26205% | +12.34558% |
| `prefix-natural-131072` | +13.32999% | +13.27050% | +13.26771% | +13.31376% |
| `prefix-natural-16384` | +12.99312% | +12.94759% | +13.21977% | +13.13062% |
| `prefix-natural-262144` | +12.91021% | +12.77106% | +12.77679% | +12.81209% |
| `prefix-natural-32767` | +7.27239% | +7.14702% | +7.42615% | +7.08595% |
| `prefix-natural-32768` | +7.21083% | +7.20076% | +7.36865% | +7.15333% |
| `prefix-natural-32769` | +7.12547% | +7.07891% | +6.96873% | +7.02285% |
| `prefix-natural-33027` | +7.25357% | +6.88994% | +7.11528% | +6.86784% |
| `prefix-natural-4096` | +45.58181% | +45.70677% | +46.24683% | +46.23096% |
| `prefix-natural-65535` | +5.61444% | +5.97659% | +5.56601% | +5.97182% |
| `prefix-natural-65536` | +5.45614% | +5.87927% | +5.58346% | +6.06857% |
| `prefix-natural-65537` | +5.38501% | +5.76991% | +5.57786% | +5.80753% |
| `prefix-natural-8192` | +24.73456% | +24.50292% | +25.36103% | +25.10653% |
| `prefix-periodic-1024` | +90.44746% | +90.44739% | +90.60690% | +90.54550% |
| `prefix-periodic-1048576` | +66.10341% | +66.01805% | +65.07590% | +65.01591% |
| `prefix-periodic-131072` | +66.58738% | +66.56628% | +65.72862% | +65.73300% |
| `prefix-periodic-16384` | +74.61149% | +74.81389% | +74.46643% | +74.51215% |
| `prefix-periodic-262144` | +65.92086% | +65.80907% | +64.90761% | +64.83439% |
| `prefix-periodic-32767` | +71.42351% | +71.39241% | +70.85238% | +70.73609% |
| `prefix-periodic-32768` | +71.36437% | +71.34358% | +70.83836% | +70.67569% |
| `prefix-periodic-32769` | +70.74677% | +70.69502% | +70.30589% | +70.14702% |
| `prefix-periodic-33027` | +70.67477% | +70.70278% | +70.13014% | +70.13358% |
| `prefix-periodic-4096` | +82.76893% | +83.02317% | +83.27525% | +83.34866% |
| `prefix-periodic-65535` | +68.42332% | +68.37565% | +67.61131% | +67.61138% |
| `prefix-periodic-65536` | +68.33537% | +68.39022% | +67.55559% | +67.72679% |
| `prefix-periodic-65537` | +68.02620% | +67.97647% | +67.24587% | +67.27566% |
| `prefix-periodic-8192` | +79.01340% | +78.92213% | +79.20946% | +79.08530% |
| `prefix-random-1024` | +93.01046% | +92.96628% | +93.28077% | +93.24773% |
| `prefix-random-1048576` | +36.73436% | +36.66909% | +36.41265% | +36.53565% |
| `prefix-random-131072` | +41.97005% | +41.80081% | +41.95815% | +41.82704% |
| `prefix-random-16384` | +67.15764% | +67.47151% | +68.00712% | +68.02287% |
| `prefix-random-262144` | +39.25340% | +39.06132% | +38.96708% | +38.93797% |
| `prefix-random-32767` | +56.40592% | +56.35675% | +56.56714% | +56.58266% |
| `prefix-random-32768` | +56.42075% | +56.33862% | +56.62516% | +56.53366% |
| `prefix-random-32769` | +55.77908% | +55.71755% | +55.91171% | +56.06784% |
| `prefix-random-33027` | +55.50172% | +55.33106% | +55.63219% | +55.60943% |
| `prefix-random-4096` | +80.97565% | +80.73086% | +81.67577% | +81.82260% |
| `prefix-random-65535` | +46.52123% | +46.32338% | +46.46238% | +46.39861% |
| `prefix-random-65536` | +46.44679% | +46.38358% | +46.45791% | +46.58718% |
| `prefix-random-65537` | +45.99127% | +46.11542% | +46.07046% | +46.14317% |
| `prefix-random-8192` | +75.61682% | +74.89995% | +75.88976% | +75.99579% |
| `prefix-repeated-1024` | +90.48129% | +90.38607% | +90.62643% | +90.52887% |
| `prefix-repeated-1048576` | +54.99572% | +54.92916% | +54.02231% | +53.98008% |
| `prefix-repeated-131072` | +55.93415% | +56.01851% | +55.12091% | +55.12961% |
| `prefix-repeated-16384` | +66.84632% | +67.05473% | +66.73681% | +66.71472% |
| `prefix-repeated-262144` | +54.91957% | +54.89785% | +54.01622% | +54.02574% |
| `prefix-repeated-32767` | +61.90750% | +62.00089% | +61.44978% | +61.34354% |
| `prefix-repeated-32768` | +62.01050% | +62.05212% | +61.46926% | +61.43011% |
| `prefix-repeated-32769` | +61.70873% | +61.37517% | +61.10751% | +60.91938% |
| `prefix-repeated-33027` | +61.46577% | +61.30965% | +60.97713% | +60.76883% |
| `prefix-repeated-4096` | +79.09805% | +79.27681% | +79.63562% | +79.49011% |
| `prefix-repeated-65535` | +58.17550% | +58.15625% | +57.40779% | +57.48192% |
| `prefix-repeated-65536` | +58.09037% | +58.05641% | +57.47442% | +57.44571% |
| `prefix-repeated-65537` | +57.94841% | +57.86085% | +57.02624% | +57.16842% |
| `prefix-repeated-8192` | +73.52045% | +73.26583% | +73.65000% | +73.36213% |
| `random-1024` | +92.83069% | +93.00325% | +93.09772% | +93.27811% |
| `random-256` | +94.76306% | +94.87755% | +94.76245% | +94.87099% |
| `random-32769` | +55.67539% | +55.33866% | +55.94611% | +55.45194% |
| `random-64` | +96.45149% | +96.40572% | +96.44169% | +96.39674% |
| `repeated-1024` | +90.07756% | +90.33966% | +90.41181% | +90.49896% |
| `repeated-32769` | +61.24743% | +61.48165% | +60.75500% | +61.00228% |
| `reymont-prefix-1024` | +82.31309% | +82.29016% | +82.63749% | +82.59955% |
| `reymont-prefix-16384` | +12.94712% | +12.92575% | +13.27791% | +13.11449% |
| `reymont-prefix-32769` | +7.59648% | +7.13858% | +7.41901% | +7.08464% |
| `seven-stored-prefix` | +11.01158% | +12.02762% | +9.89730% | +11.15283% |

</details>

Timing SHA-256 `c0b05ea03a7556165b9245148b699b1ca5a357c8873a68a46b57fc282411a060`. Raw-observation verification SHA-256 `01e78bb037e3d891ac756635ba4556691e12c00ac6d9a47b716e3149895f1450`.

### Phase 362 and correctness

The emitted encoder phase grew from 224 to 368 bytes. Other encoder symbol bodies matched. The table gives dynamic instructions and branches per encode.

| Case | Calls | Instructions, control → candidate | Branches, control → candidate |
| --- | ---: | ---: | ---: |
| `prefix-natural-1024` | 1 | 20,500 → 3,615 | 7,170 → 131 |
| `reymont-prefix-1024` | 1 | 20,500 → 3,615 | 7,170 → 131 |
| `prefix-random-4096` | 1 | 81,940 → 14,367 | 28,674 → 515 |
| `heldout-window-32767` | 2 | 163,880 → 28,734 | 57,348 → 1,030 |
| `320-overlap` | 0 | 0 → 0 | 0 → 0 |

The captured phase passed 139,608 differential executions, with identical output words, final storage, status, and fault sites. They included 25,944 overflow faults and 28,937 destination bounds faults. The source regressions exercised forwarding of entry values, failing recurrence proofs and overlapping views.

The replay preserved canonical bytecode, source origins and checked continuations. It reproduced the encoder and worker bytes for the parent and candidate. The parent and candidate runtime each passed 23 tests at all four inline-owner counts. The tests check exact and spare capacity, prefix and span contents, counters, aliasing, and invalid allocation. Native checks covered 162 exact outputs and aliases, six named errors and 12 same-process recoveries. All four linked actors passed independent inflation and exact output checks on all 81 deployment fixtures (324 runs).

### Artifact binding

- Encoder text 67,416 B, lookup data 65,536 B, const data 80,064 B, stripped executable 291,768 B, peak stack 5,184 B.
- Codec source SHA-256 `653597f08f889908c48610e90aa65e94a77847fb34500d0cc3a046f83cd3d299`.
- Canonical bytecode SHA-256 `c6529d934f020f07f8e59f13fab40927e066649e202269818ad3f009a942a8c3`.
- Encoder and worker SHA-256 `58c9177ccf6158d352d5a8f888cdb34f0897b4bd5aaeeb53e187b371dd89c553` and `19df74b864ef19f0689dab908fa7f8b8fb5af60577c773fea0530aef824fa356`.
- Metadata SHA-256 `980e9c35249cfd37c9866b7be9c70f664bc0e78a55feaf5f415d866ef5a78de7`.
- Candidate runtime library and deployment archive SHA-256 `e220113ac6dc0e92f0410f122cc23319a321c8ac8618d2ff89b442eb1e609edc` and `1110ad67f4f4292b1669862bee784a73e17c90bfd50a61006aad00bd78f85838`.
- Parent deployment archive SHA-256 `50dfe9a3f86cd5a625dbdaa084a6c8dba59cc43a55a27a4d3cc92372f2f89489`.

### Source-through-link builds

Median seconds across eight complete builds with each actor’s prebuilt compiler and qualified host support.

| Actor | Source | Link | Source through link | Strip | Source through strip |
| --- | ---: | ---: | ---: | ---: | ---: |
| Control | 2.171381 | 0.037620 | 2.209050 | 0.010898 | 2.220423 |
| Candidate | 2.174919 | 0.039167 | 2.216811 | 0.010930 | 2.228155 |
| libdeflate | 0.446413 | 0.034644 | 0.481448 | 0.010672 | 0.492259 |
| Independent reference | 2.951786 | 0.035347 | 2.987400 | 0.010695 | 2.998217 |
