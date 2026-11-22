# All measured shared-page timings

Paired ratios below are elapsed Mech time divided by peer time. Smaller is better. These discovery panels do not replace full 81 qualification.

| Candidate | Order | Case | Mech ms | Matched control ms | Roc ms | C ms | Paired Mech/C | Median Mech/control | Required named wins missing |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| pages-12 | forward | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007075 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007184 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | seven-stored-prefix | 0.000042 | 0.000041 | 0.000042 | 0.004208 | 0.007544 | 1.024390 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | eight-overlap | 0.015542 | 0.015541 | 0.286542 | 0.021083 | 0.709312 | 1.000064 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | 320-overlap | 0.026563 | 0.027000 | 0.297916 | 0.027625 | 0.957397 | 0.983796 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | 16384-distribution-change | 0.586417 | 0.581062 | 0.846854 | 0.485833 | 1.203659 | 1.009216 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | random-32769 | 0.632084 | 0.637938 | 1.074520 | 0.527979 | 1.194343 | 0.990824 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | reymont-prefix-1024 | 0.071541 | 0.070542 | 0.334250 | 0.059000 | 1.216739 | 1.014162 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | heldout-random-65537 | 1.350958 | 1.359667 | 1.950959 | 1.149417 | 1.173918 | 0.993595 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-natural-1024 | 0.071542 | 0.070459 | 0.334250 | 0.058959 | 1.216483 | 1.015371 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-natural-4096 | 0.389645 | 0.377938 | 0.662479 | 0.393063 | 0.991293 | 1.030979 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-natural-8192 | 0.874521 | 0.846812 | 1.126459 | 0.907979 | 0.960333 | 1.032721 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-1024 | 0.028000 | 0.028084 | 0.307917 | 0.033166 | 0.849103 | 0.997009 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-4096 | 0.108354 | 0.107479 | 0.371521 | 0.076458 | 1.421804 | 1.008141 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-8192 | 0.173750 | 0.174563 | 0.451813 | 0.125417 | 1.380761 | 0.995343 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-16384 | 0.307083 | 0.309312 | 0.640896 | 0.238417 | 1.283880 | 0.992792 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-32767 | 0.622542 | 0.626896 | 1.059896 | 0.519125 | 1.197160 | 0.993054 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-32768 | 0.619000 | 0.624376 | 1.058291 | 0.519042 | 1.189386 | 0.991391 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-32769 | 0.631583 | 0.637521 | 1.074688 | 0.529083 | 1.190375 | 0.990687 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-33027 | 0.640479 | 0.647042 | 1.083333 | 0.534896 | 1.195219 | 0.989858 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-65535 | 1.356604 | 1.364459 | 1.978583 | 1.161292 | 1.163157 | 0.994244 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-65536 | 1.353500 | 1.359708 | 1.977917 | 1.159604 | 1.162899 | 0.995434 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-65537 | 1.364104 | 1.371542 | 1.991084 | 1.170083 | 1.162314 | 0.994577 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-131072 | 2.787146 | 2.804333 | 3.848854 | 2.472333 | 1.124340 | 0.993871 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-262144 | 5.683333 | 5.705875 | 7.516687 | 5.053479 | 1.122872 | 0.996049 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-random-1048576 | 22.443500 | 22.553792 | 28.769105 | 20.346417 | 1.104176 | 0.995110 | {'roc': [], 'libdeflate': []} |
| pages-12 | forward | prefix-periodic-1024 | 0.039167 | 0.039125 | 0.324625 | 0.045291 | 0.873227 | 1.001073 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-periodic-1024 | 0.039166 | 0.039209 | 0.321792 | 0.045291 | 0.873419 | 0.998903 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-1048576 | 22.449438 | 22.557979 | 28.796416 | 20.310834 | 1.106142 | 0.995188 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-262144 | 5.677166 | 5.711875 | 7.514166 | 5.071584 | 1.120312 | 0.993923 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-131072 | 2.786646 | 2.804417 | 3.847374 | 2.472459 | 1.125689 | 0.993663 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-65537 | 1.365291 | 1.369458 | 1.990104 | 1.171479 | 1.161259 | 0.996957 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-65536 | 1.354771 | 1.361417 | 1.974375 | 1.161521 | 1.162853 | 0.995118 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-65535 | 1.356188 | 1.362688 | 1.975021 | 1.161979 | 1.164389 | 0.995230 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-33027 | 0.641875 | 0.644292 | 1.080125 | 0.534959 | 1.197143 | 0.996249 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-32769 | 0.630771 | 0.635187 | 1.072646 | 0.529500 | 1.191946 | 0.993046 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-32768 | 0.619562 | 0.624833 | 1.057062 | 0.519792 | 1.193162 | 0.991563 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-32767 | 0.620771 | 0.624979 | 1.059125 | 0.519687 | 1.194146 | 0.993267 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-16384 | 0.302770 | 0.304667 | 0.641917 | 0.238375 | 1.274961 | 0.993777 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-8192 | 0.170896 | 0.174480 | 0.451416 | 0.125855 | 1.361598 | 0.979459 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-4096 | 0.106125 | 0.106750 | 0.373562 | 0.076770 | 1.403258 | 0.994145 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-random-1024 | 0.028000 | 0.028125 | 0.305250 | 0.033166 | 0.850709 | 0.995556 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-natural-8192 | 0.874646 | 0.846917 | 1.129145 | 0.908500 | 0.964729 | 1.032741 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-natural-4096 | 0.386354 | 0.376938 | 0.663250 | 0.392875 | 0.991055 | 1.024982 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | prefix-natural-1024 | 0.071500 | 0.070583 | 0.332084 | 0.058917 | 1.218126 | 1.012992 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | heldout-random-65537 | 1.346917 | 1.356062 | 1.947625 | 1.148958 | 1.172100 | 0.993256 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | reymont-prefix-1024 | 0.071500 | 0.070625 | 0.332166 | 0.058917 | 1.219679 | 1.012389 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | random-32769 | 0.632042 | 0.635291 | 1.073167 | 0.528604 | 1.195344 | 0.994885 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | 16384-distribution-change | 0.579520 | 0.572896 | 0.841187 | 0.483375 | 1.199413 | 1.011563 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | 320-overlap | 0.027042 | 0.027083 | 0.297041 | 0.027625 | 0.953204 | 0.998486 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | eight-overlap | 0.015583 | 0.015542 | 0.286625 | 0.021209 | 0.711507 | 1.002638 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | seven-stored-prefix | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007367 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007101 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-12 | reverse | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006866 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006902 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006987 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | seven-stored-prefix | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007322 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | eight-overlap | 0.015541 | 0.015500 | 0.291834 | 0.021125 | 0.707611 | 1.002645 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | 320-overlap | 0.027041 | 0.027000 | 0.302333 | 0.027625 | 0.955117 | 1.001519 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | 16384-distribution-change | 0.583187 | 0.574896 | 0.843791 | 0.484479 | 1.200787 | 1.014423 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | random-32769 | 0.634604 | 0.638041 | 1.074271 | 0.527417 | 1.200099 | 0.994613 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | reymont-prefix-1024 | 0.071458 | 0.070500 | 0.337000 | 0.058958 | 1.216155 | 1.013589 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | heldout-random-65537 | 1.349376 | 1.355667 | 1.950812 | 1.149167 | 1.170894 | 0.995359 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-natural-1024 | 0.071417 | 0.070625 | 0.337167 | 0.058958 | 1.214442 | 1.011214 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-natural-4096 | 0.391021 | 0.377062 | 0.664062 | 0.391813 | 0.995594 | 1.037020 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-natural-8192 | 0.881583 | 0.849687 | 1.130417 | 0.909250 | 0.967761 | 1.037539 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-1024 | 0.028042 | 0.028083 | 0.310437 | 0.033125 | 0.850671 | 0.998540 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-4096 | 0.109874 | 0.110458 | 0.375292 | 0.076624 | 1.430098 | 0.994717 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-8192 | 0.175292 | 0.175083 | 0.450854 | 0.126333 | 1.388733 | 1.001191 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-16384 | 0.307687 | 0.311063 | 0.641480 | 0.238166 | 1.289369 | 0.989148 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-32767 | 0.624604 | 0.627042 | 1.062063 | 0.518500 | 1.200971 | 0.996113 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-32768 | 0.622646 | 0.625020 | 1.061562 | 0.518167 | 1.199362 | 0.996201 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-32769 | 0.634333 | 0.636396 | 1.077917 | 0.528480 | 1.199132 | 0.996759 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-33027 | 0.643875 | 0.645145 | 1.082667 | 0.533604 | 1.202150 | 0.998031 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-65535 | 1.358521 | 1.365250 | 1.978855 | 1.161375 | 1.165945 | 0.995071 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-65536 | 1.354792 | 1.362542 | 1.979125 | 1.161104 | 1.164152 | 0.994312 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-65537 | 1.366375 | 1.371438 | 1.992855 | 1.169792 | 1.164115 | 0.996309 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-131072 | 2.791438 | 2.809750 | 3.850500 | 2.471312 | 1.127612 | 0.993483 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-262144 | 5.681687 | 5.709271 | 7.517437 | 5.053999 | 1.122503 | 0.995169 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-random-1048576 | 22.419833 | 22.543062 | 28.750896 | 20.340312 | 1.102885 | 0.994534 | {'roc': [], 'libdeflate': []} |
| pages-6 | forward | prefix-periodic-1024 | 0.039291 | 0.039333 | 0.323000 | 0.045667 | 0.868592 | 0.998932 | {'roc': [], 'libdeflate': []} |
| pages-6 | reverse | prefix-periodic-1024 | 0.039334 | 0.039375 | 0.320750 | 0.045334 | 0.876271 | 0.998959 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-1048576 | 22.441208 | 22.585438 | 28.805937 | 20.322667 | 1.105803 | 0.993614 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-262144 | 5.683166 | 5.711500 | 7.514062 | 5.068084 | 1.119086 | 0.995039 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-131072 | 2.787312 | 2.807812 | 3.843958 | 2.474230 | 1.127515 | 0.992699 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-65537 | 1.359959 | 1.370917 | 1.993021 | 1.172521 | 1.160575 | 0.992006 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-65536 | 1.351771 | 1.359292 | 1.976792 | 1.164354 | 1.158870 | 0.994467 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-65535 | 1.348104 | 1.356437 | 1.973250 | 1.161750 | 1.159748 | 0.993856 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-33027 | 0.636834 | 0.641645 | 1.077521 | 0.534062 | 1.191440 | 0.992501 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-32769 | 0.629542 | 0.635084 | 1.070646 | 0.527937 | 1.190605 | 0.991274 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-32768 | 0.621251 | 0.628625 | 1.058042 | 0.518999 | 1.196344 | 0.988269 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-32767 | 0.622521 | 0.628208 | 1.059292 | 0.519333 | 1.197857 | 0.990946 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-16384 | 0.306708 | 0.308396 | 0.641833 | 0.238459 | 1.281967 | 0.994528 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-8192 | 0.171104 | 0.175292 | 0.451479 | 0.124875 | 1.383177 | 0.976111 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-4096 | 0.107854 | 0.108416 | 0.373042 | 0.075666 | 1.433355 | 0.994812 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-random-1024 | 0.028042 | 0.028083 | 0.308500 | 0.033166 | 0.848425 | 0.998540 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-natural-8192 | 0.878375 | 0.849729 | 1.133333 | 0.908771 | 0.967434 | 1.033713 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-natural-4096 | 0.391917 | 0.379354 | 0.664979 | 0.393521 | 1.003104 | 1.033117 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | prefix-natural-1024 | 0.071500 | 0.070583 | 0.337459 | 0.058958 | 1.217420 | 1.012992 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | heldout-random-65537 | 1.349063 | 1.358791 | 1.948208 | 1.148937 | 1.172475 | 0.992840 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | reymont-prefix-1024 | 0.071541 | 0.070541 | 0.335708 | 0.058917 | 1.219069 | 1.014176 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | random-32769 | 0.634313 | 0.637958 | 1.076292 | 0.529187 | 1.197740 | 0.994286 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | 16384-distribution-change | 0.584104 | 0.575500 | 0.840979 | 0.483896 | 1.208223 | 1.014950 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | 320-overlap | 0.026583 | 0.026812 | 0.302604 | 0.027667 | 0.955348 | 0.991441 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | eight-overlap | 0.015584 | 0.015542 | 0.292250 | 0.021084 | 0.712981 | 1.002702 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | seven-stored-prefix | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007302 | 1.000000 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007074 | 1.000000 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6 | reverse | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006850 | 1.000000 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-plain | forward | 16384-distribution-change | 0.589188 | 0.579916 | 0.846313 | 0.486167 | 1.203265 | 1.015987 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | forward | prefix-natural-1024 | 0.071500 | 0.070500 | 0.332875 | 0.059000 | 1.216088 | 1.014184 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | forward | prefix-natural-4096 | 0.388813 | 0.377896 | 0.662251 | 0.392021 | 0.990781 | 1.028888 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | forward | prefix-natural-8192 | 0.879854 | 0.848938 | 1.129458 | 0.909855 | 0.964513 | 1.036418 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | forward | prefix-random-1048576 | 22.445791 | 22.552104 | 28.784729 | 20.313271 | 1.105801 | 0.995286 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | prefix-random-1048576 | 22.443500 | 22.557042 | 28.776166 | 20.333416 | 1.105535 | 0.994966 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | prefix-natural-8192 | 0.876834 | 0.846708 | 1.126791 | 0.909250 | 0.967826 | 1.035580 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | prefix-natural-4096 | 0.389958 | 0.377583 | 0.663624 | 0.393187 | 0.998703 | 1.032774 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | prefix-natural-1024 | 0.071583 | 0.070542 | 0.335917 | 0.059000 | 1.216781 | 1.014757 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain | reverse | 16384-distribution-change | 0.582521 | 0.577042 | 0.839792 | 0.484979 | 1.201311 | 1.009495 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-plain-raw | forward | 16384-distribution-change | 0.616354 | 0.576771 | 0.846125 | 0.486020 | 1.262230 | 1.068629 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | forward | prefix-natural-1024 | 0.072375 | 0.070625 | 0.336250 | 0.059000 | 1.231585 | 1.024779 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | forward | prefix-natural-4096 | 0.409354 | 0.375187 | 0.664855 | 0.390708 | 1.041540 | 1.091066 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | forward | prefix-natural-8192 | 0.914750 | 0.843145 | 1.130375 | 0.907438 | 1.006932 | 1.084925 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | forward | prefix-random-1048576 | 22.523708 | 22.557042 | 28.780396 | 20.330333 | 1.108578 | 0.998522 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | prefix-random-1048576 | 22.518354 | 22.562271 | 28.792188 | 20.313000 | 1.110350 | 0.998054 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | prefix-natural-8192 | 0.922354 | 0.847583 | 1.131125 | 0.908980 | 1.020277 | 1.088217 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | prefix-natural-4096 | 0.408562 | 0.376062 | 0.658000 | 0.390562 | 1.050575 | 1.086422 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | prefix-natural-1024 | 0.072500 | 0.070500 | 0.333792 | 0.058916 | 1.236940 | 1.028369 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-plain-raw | reverse | 16384-distribution-change | 0.614187 | 0.571875 | 0.841188 | 0.483729 | 1.268837 | 1.073988 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved | forward | 16384-distribution-change | 0.582291 | 0.569937 | 0.843417 | 0.482812 | 1.199437 | 1.021675 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | forward | prefix-natural-1024 | 0.071542 | 0.070541 | 0.334208 | 0.059000 | 1.216875 | 1.014190 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | forward | prefix-natural-4096 | 0.387292 | 0.375771 | 0.660730 | 0.392312 | 0.985796 | 1.030658 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | forward | prefix-natural-8192 | 0.876229 | 0.846938 | 1.128667 | 0.908042 | 0.960881 | 1.034586 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | forward | prefix-random-1048576 | 22.442667 | 22.551250 | 28.765437 | 20.341021 | 1.104261 | 0.995185 | {'roc': [], 'libdeflate': []} |
| pages-6-linear-preserved | reverse | prefix-random-1048576 | 22.447354 | 22.560458 | 28.779875 | 20.314750 | 1.105725 | 0.994987 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved | reverse | prefix-natural-8192 | 0.877334 | 0.847625 | 1.129687 | 0.908104 | 0.967295 | 1.035050 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved | reverse | prefix-natural-4096 | 0.391104 | 0.377083 | 0.665104 | 0.391813 | 1.005012 | 1.037184 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved | reverse | prefix-natural-1024 | 0.071625 | 0.070667 | 0.335458 | 0.058916 | 1.219465 | 1.013557 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved | reverse | 16384-distribution-change | 0.583438 | 0.576083 | 0.843229 | 0.483896 | 1.205088 | 1.012767 | {'roc': [], 'libdeflate': ['prefix-natural-4096']} |
| pages-6-linear-preserved-raw | forward | 16384-distribution-change | 0.611625 | 0.571187 | 0.840896 | 0.483876 | 1.259743 | 1.070796 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | forward | prefix-natural-1024 | 0.072333 | 0.070334 | 0.332750 | 0.058958 | 1.228485 | 1.028422 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | forward | prefix-natural-4096 | 0.409771 | 0.374271 | 0.661875 | 0.390646 | 1.044575 | 1.094853 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | forward | prefix-natural-8192 | 0.913854 | 0.838750 | 1.124437 | 0.905125 | 1.008789 | 1.089543 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | forward | prefix-random-1048576 | 22.453500 | 22.506708 | 28.736812 | 20.296833 | 1.106560 | 0.997636 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | prefix-random-1048576 | 22.516083 | 22.559375 | 28.798313 | 20.320437 | 1.109037 | 0.998081 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | prefix-natural-8192 | 0.916437 | 0.844562 | 1.127729 | 0.907459 | 1.015695 | 1.085103 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | prefix-natural-4096 | 0.408125 | 0.377188 | 0.663062 | 0.391500 | 1.050085 | 1.082022 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | prefix-natural-1024 | 0.072416 | 0.070750 | 0.334458 | 0.059042 | 1.230449 | 1.023548 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-linear-preserved-raw | reverse | 16384-distribution-change | 0.613646 | 0.574792 | 0.844167 | 0.483646 | 1.270260 | 1.067597 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain | forward | 16384-distribution-change | 0.578021 | 0.569125 | 0.839271 | 0.484146 | 1.191999 | 1.015631 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-1024 | 0.071708 | 0.070667 | 0.331542 | 0.059041 | 1.216899 | 1.014731 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-4096 | 0.386750 | 0.373896 | 0.659125 | 0.392041 | 0.986778 | 1.034379 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-8192 | 0.875708 | 0.847354 | 1.126417 | 0.910770 | 0.960089 | 1.033462 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-1048576 | 22.432209 | 22.545209 | 28.755021 | 20.337500 | 1.102788 | 0.994988 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-1048576 | 22.444834 | 22.562750 | 28.761521 | 20.315229 | 1.105807 | 0.994774 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-8192 | 0.876437 | 0.849062 | 1.130646 | 0.908917 | 0.968467 | 1.032241 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-4096 | 0.387813 | 0.375229 | 0.662875 | 0.392020 | 0.993052 | 1.033537 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-1024 | 0.071667 | 0.070542 | 0.334375 | 0.059000 | 1.219591 | 1.015948 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 16384-distribution-change | 0.581687 | 0.575458 | 0.841042 | 0.482833 | 1.202578 | 1.010824 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain-raw | forward | 16384-distribution-change | 0.615125 | 0.572520 | 0.844291 | 0.484146 | 1.266973 | 1.074416 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | forward | prefix-natural-1024 | 0.072333 | 0.070625 | 0.336708 | 0.058959 | 1.229558 | 1.024184 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | forward | prefix-natural-4096 | 0.408729 | 0.376771 | 0.664020 | 0.391812 | 1.040009 | 1.084821 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | forward | prefix-natural-8192 | 0.915751 | 0.842208 | 1.128667 | 0.906834 | 1.010117 | 1.087321 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | forward | prefix-random-1048576 | 22.510166 | 22.557042 | 28.768459 | 20.303125 | 1.108849 | 0.997922 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | prefix-random-1048576 | 22.515355 | 22.568313 | 28.804834 | 20.313645 | 1.109267 | 0.997653 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | prefix-natural-8192 | 0.915084 | 0.842729 | 1.119834 | 0.907667 | 1.012588 | 1.085857 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | prefix-natural-4096 | 0.408854 | 0.375312 | 0.658792 | 0.391834 | 1.048093 | 1.089370 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | prefix-natural-1024 | 0.072375 | 0.070667 | 0.328916 | 0.059000 | 1.229431 | 1.024170 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain-raw | reverse | 16384-distribution-change | 0.610667 | 0.567042 | 0.835042 | 0.483083 | 1.264610 | 1.076933 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved | forward | 16384-distribution-change | 0.582521 | 0.571896 | 0.844834 | 0.483563 | 1.202066 | 1.018579 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | forward | prefix-natural-1024 | 0.071625 | 0.070625 | 0.335875 | 0.058959 | 1.218128 | 1.014159 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | forward | prefix-natural-4096 | 0.389166 | 0.376771 | 0.663021 | 0.391313 | 0.993973 | 1.032899 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | forward | prefix-natural-8192 | 0.877521 | 0.849395 | 1.127292 | 0.907979 | 0.963181 | 1.033112 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | forward | prefix-random-1048576 | 22.445145 | 22.569000 | 28.776854 | 20.325854 | 1.104549 | 0.994512 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | prefix-random-1048576 | 22.437917 | 22.557083 | 28.762646 | 20.318105 | 1.104639 | 0.994717 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | prefix-natural-8192 | 0.878896 | 0.848395 | 1.128812 | 0.911416 | 0.966090 | 1.035951 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | prefix-natural-4096 | 0.390541 | 0.378437 | 0.664791 | 0.392896 | 0.999170 | 1.031986 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | prefix-natural-1024 | 0.071500 | 0.070583 | 0.335375 | 0.058959 | 1.216820 | 1.012992 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved | reverse | 16384-distribution-change | 0.581937 | 0.577646 | 0.845499 | 0.484604 | 1.200079 | 1.007429 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-preserved-raw | forward | 16384-distribution-change | 0.614375 | 0.571230 | 0.841854 | 0.483479 | 1.266595 | 1.075531 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | forward | prefix-natural-1024 | 0.072584 | 0.070834 | 0.331875 | 0.059042 | 1.233553 | 1.024706 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | forward | prefix-natural-4096 | 0.407646 | 0.376041 | 0.659083 | 0.392791 | 1.035553 | 1.084045 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | forward | prefix-natural-8192 | 0.914729 | 0.841187 | 1.125875 | 0.907728 | 1.006922 | 1.087426 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | forward | prefix-random-1048576 | 22.455167 | 22.495542 | 28.739187 | 20.310875 | 1.107343 | 0.998205 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | prefix-random-1048576 | 22.524917 | 22.557042 | 28.789916 | 20.384813 | 1.104650 | 0.998576 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | prefix-natural-8192 | 0.917979 | 0.846376 | 1.126938 | 0.905875 | 1.017908 | 1.084600 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | prefix-natural-4096 | 0.406146 | 0.379021 | 0.662292 | 0.390375 | 1.052056 | 1.071566 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | prefix-natural-1024 | 0.072333 | 0.070667 | 0.332625 | 0.059000 | 1.228894 | 1.023575 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-preserved-raw | reverse | 16384-distribution-change | 0.615396 | 0.576083 | 0.841604 | 0.484000 | 1.271358 | 1.068241 | {'roc': [], 'libdeflate': ['prefix-natural-4096', 'prefix-natural-8192']} |
| pages-6-sqrt-plain | forward | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006862 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007160 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | seven-stored-prefix | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007266 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | eight-literals | 0.008334 | 0.008333 | 0.289000 | 0.021333 | 0.390124 | 1.000120 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | eight-overlap | 0.015542 | 0.015541 | 0.288791 | 0.021208 | 0.719229 | 1.000064 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | 320-overlap | 0.027000 | 0.027041 | 0.298917 | 0.027583 | 0.958148 | 0.998484 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | eight-literals-prefix | 0.008334 | 0.008333 | 0.288792 | 0.021333 | 0.390103 | 1.000120 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | 128-biased-dynamic | 0.015875 | 0.015875 | 0.288625 | 0.020333 | 0.769480 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | 32-high-entropy-stored | 0.009625 | 0.009666 | 0.291937 | 0.022042 | 0.438580 | 0.995758 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | 16384-distribution-change | 0.583187 | 0.574312 | 0.845625 | 0.483250 | 1.202317 | 1.015453 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | 33027-periodic-window | 0.398708 | 0.400042 | 1.261958 | 0.593521 | 0.674215 | 0.996667 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | random-64 | 0.011000 | 0.010916 | 0.292750 | 0.022291 | 0.494513 | 1.007695 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | random-256 | 0.017500 | 0.017500 | 0.299000 | 0.025875 | 0.693100 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | random-1024 | 0.027625 | 0.027584 | 0.310500 | 0.032917 | 0.844223 | 1.001486 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | repeated-1024 | 0.038958 | 0.039000 | 0.328875 | 0.046291 | 0.832927 | 0.998923 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | random-32769 | 0.635854 | 0.637979 | 1.076083 | 0.529062 | 1.198396 | 0.996669 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | repeated-32769 | 0.451688 | 0.450916 | 1.345084 | 0.691292 | 0.653717 | 1.001711 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | reymont-prefix-1024 | 0.071708 | 0.070542 | 0.335666 | 0.059000 | 1.218896 | 1.016529 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | reymont-prefix-16384 | 1.951188 | 1.880688 | 2.161896 | 2.148813 | 0.906794 | 1.037486 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | reymont-prefix-32769 | 4.182000 | 4.048979 | 4.352520 | 4.802313 | 0.870845 | 1.032853 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | heldout-window-32767 | 4.171208 | 4.037521 | 4.347938 | 4.790854 | 0.869564 | 1.033111 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | heldout-window-32768 | 4.166041 | 4.033583 | 4.341750 | 4.791979 | 0.869040 | 1.032839 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | heldout-slides-65537 | 8.289958 | 8.078500 | 8.890146 | 10.124833 | 0.817543 | 1.026175 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | heldout-random-65537 | 1.355104 | 1.363375 | 1.947250 | 1.148833 | 1.174434 | 0.993933 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | heldout-mixed-131073 | 6.266271 | 6.164959 | 8.402437 | 7.254354 | 0.863068 | 1.016434 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-1024 | 0.071667 | 0.070542 | 0.335750 | 0.058959 | 1.220950 | 1.015948 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-4096 | 0.391104 | 0.380250 | 0.664937 | 0.392105 | 0.994131 | 1.028544 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-8192 | 0.878687 | 0.851583 | 1.133291 | 0.909458 | 0.964468 | 1.031828 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-16384 | 1.953583 | 1.881771 | 2.161209 | 2.151396 | 0.906360 | 1.038162 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-32767 | 4.179771 | 4.051812 | 4.343708 | 4.792042 | 0.871968 | 1.031581 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-32768 | 4.176146 | 4.047458 | 4.338854 | 4.791416 | 0.871211 | 1.031795 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-32769 | 4.183187 | 4.052833 | 4.359083 | 4.801876 | 0.870711 | 1.032164 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-33027 | 4.224375 | 4.094959 | 4.397604 | 4.851167 | 0.870425 | 1.031604 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-65535 | 10.365208 | 10.030729 | 10.752646 | 12.753334 | 0.813094 | 1.033345 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-65536 | 10.368896 | 10.032875 | 10.748667 | 12.768833 | 0.812299 | 1.033492 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-65537 | 10.377000 | 10.046834 | 10.757354 | 12.755917 | 0.813332 | 1.032863 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-131072 | 19.745583 | 19.145458 | 22.311479 | 27.101709 | 0.728741 | 1.031346 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-262144 | 40.281480 | 39.092083 | 45.341667 | 55.941042 | 0.720178 | 1.030426 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-natural-1048576 | 144.114937 | 140.447729 | 161.123000 | 199.682875 | 0.721885 | 1.026111 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-1024 | 0.028125 | 0.028084 | 0.309166 | 0.033208 | 0.852252 | 1.001460 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-4096 | 0.107917 | 0.109270 | 0.372334 | 0.076208 | 1.418006 | 0.987609 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-8192 | 0.174562 | 0.173875 | 0.451354 | 0.125396 | 1.392025 | 1.003954 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-16384 | 0.308396 | 0.308625 | 0.641104 | 0.237937 | 1.292970 | 0.999258 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-32767 | 0.626938 | 0.629333 | 1.062021 | 0.519813 | 1.197816 | 0.996193 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-32768 | 0.621792 | 0.625604 | 1.058876 | 0.518417 | 1.199654 | 0.993907 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-32769 | 0.634000 | 0.638125 | 1.071354 | 0.527646 | 1.197205 | 0.993535 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-33027 | 0.645375 | 0.646563 | 1.080334 | 0.533709 | 1.207452 | 0.998163 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-65535 | 1.355271 | 1.364459 | 1.973854 | 1.160208 | 1.164938 | 0.993267 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-65536 | 1.352854 | 1.360917 | 1.977042 | 1.160979 | 1.161685 | 0.994076 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-65537 | 1.365083 | 1.374396 | 1.988021 | 1.171437 | 1.161812 | 0.993224 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-131072 | 2.792626 | 2.807271 | 3.848104 | 2.471229 | 1.127089 | 0.994783 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-262144 | 5.690667 | 5.720167 | 7.518333 | 5.053041 | 1.124299 | 0.994843 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-random-1048576 | 22.439792 | 22.552729 | 28.771771 | 20.334146 | 1.105437 | 0.994992 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-1024 | 0.039208 | 0.039208 | 0.326146 | 0.045291 | 0.873106 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-4096 | 0.080125 | 0.079875 | 0.424459 | 0.100979 | 0.803696 | 1.003130 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-8192 | 0.130375 | 0.129938 | 0.558563 | 0.175104 | 0.747454 | 1.003367 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-16384 | 0.208062 | 0.207854 | 0.762083 | 0.299709 | 0.695468 | 1.001003 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-32767 | 0.384625 | 0.385208 | 1.242312 | 0.577959 | 0.667035 | 0.998487 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-32768 | 0.383896 | 0.382146 | 1.241667 | 0.577187 | 0.664680 | 1.004579 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-32769 | 0.397125 | 0.397000 | 1.255792 | 0.585583 | 0.677947 | 1.000314 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-33027 | 0.402166 | 0.399541 | 1.263479 | 0.592875 | 0.678728 | 1.006570 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-65535 | 0.752229 | 0.751917 | 2.205646 | 1.141937 | 0.658604 | 1.000416 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-65536 | 0.745125 | 0.744312 | 2.206583 | 1.141520 | 0.653302 | 1.001092 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-65537 | 0.764270 | 0.764250 | 2.216979 | 1.152416 | 0.662603 | 1.000027 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-131072 | 1.466688 | 1.463417 | 4.135042 | 2.274208 | 0.645045 | 1.002235 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-262144 | 2.905708 | 2.902063 | 7.993209 | 4.527583 | 0.640766 | 1.001256 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-periodic-1048576 | 11.420625 | 11.425333 | 31.278291 | 18.474501 | 0.618132 | 0.999588 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-1024 | 0.038917 | 0.039000 | 0.329709 | 0.046375 | 0.831893 | 0.997872 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-4096 | 0.085729 | 0.085812 | 0.436062 | 0.113709 | 0.762026 | 0.999027 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-8192 | 0.142937 | 0.142501 | 0.580583 | 0.200146 | 0.715955 | 1.003067 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-16384 | 0.236396 | 0.235250 | 0.813354 | 0.351479 | 0.674343 | 1.004871 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-32767 | 0.436646 | 0.436708 | 1.332312 | 0.679542 | 0.643546 | 0.999857 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-32768 | 0.440520 | 0.440021 | 1.336166 | 0.679521 | 0.649344 | 1.001135 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-32769 | 0.450584 | 0.449146 | 1.344438 | 0.689979 | 0.651584 | 1.003201 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-33027 | 0.452916 | 0.455687 | 1.354167 | 0.695125 | 0.653096 | 0.993919 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-65535 | 0.857125 | 0.857895 | 2.388646 | 1.350916 | 0.636607 | 0.999102 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-65536 | 0.870084 | 0.870270 | 2.395000 | 1.353417 | 0.641940 | 0.999785 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-65537 | 0.874042 | 0.873062 | 2.403271 | 1.359438 | 0.643311 | 1.001122 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-131072 | 1.711354 | 1.709354 | 4.499271 | 2.684333 | 0.638165 | 1.001170 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-262144 | 3.395354 | 3.397979 | 8.724500 | 5.363145 | 0.632844 | 0.999227 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | forward | prefix-repeated-1048576 | 13.287041 | 13.266834 | 34.208354 | 21.757312 | 0.610873 | 1.001523 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-1048576 | 13.273542 | 13.268000 | 34.202521 | 21.683563 | 0.612217 | 1.000418 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-262144 | 3.401729 | 3.400333 | 8.724604 | 5.370646 | 0.633555 | 1.000411 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-131072 | 1.717729 | 1.717875 | 4.510125 | 2.690896 | 0.636426 | 0.999915 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-65537 | 0.871395 | 0.871271 | 2.397437 | 1.358834 | 0.642274 | 1.000142 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-65536 | 0.861313 | 0.861000 | 2.386687 | 1.350687 | 0.638743 | 1.000362 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-65535 | 0.855396 | 0.856334 | 2.385063 | 1.350979 | 0.633511 | 0.998905 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-33027 | 0.452230 | 0.453292 | 1.351145 | 0.695813 | 0.649670 | 0.997657 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-32769 | 0.450167 | 0.450396 | 1.344791 | 0.690500 | 0.651380 | 0.999492 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-32768 | 0.436875 | 0.437625 | 1.333541 | 0.678646 | 0.645169 | 0.998286 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-32767 | 0.434229 | 0.434959 | 1.333979 | 0.679083 | 0.640988 | 0.998323 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-16384 | 0.233625 | 0.233604 | 0.811188 | 0.350896 | 0.666856 | 1.000090 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-8192 | 0.141896 | 0.141771 | 0.580396 | 0.200938 | 0.709708 | 1.000882 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-4096 | 0.084146 | 0.084834 | 0.433854 | 0.113980 | 0.748410 | 0.991896 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-repeated-1024 | 0.039084 | 0.038959 | 0.329125 | 0.046583 | 0.832438 | 1.003209 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-1048576 | 11.423334 | 11.420792 | 31.299063 | 18.415021 | 0.620443 | 1.000223 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-262144 | 2.904501 | 2.903208 | 7.996167 | 4.526812 | 0.642304 | 1.000445 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-131072 | 1.464500 | 1.468354 | 4.131583 | 2.273146 | 0.644365 | 0.997375 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-65537 | 0.761417 | 0.762437 | 2.217333 | 1.152438 | 0.661337 | 0.998662 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-65536 | 0.742875 | 0.742792 | 2.204167 | 1.142895 | 0.649797 | 1.000112 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-65535 | 0.751729 | 0.750771 | 2.203438 | 1.143083 | 0.657618 | 1.001275 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-33027 | 0.400771 | 0.398687 | 1.261979 | 0.593125 | 0.675218 | 1.005227 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-32769 | 0.393480 | 0.393666 | 1.252063 | 0.585729 | 0.673333 | 0.999525 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-32768 | 0.392396 | 0.392083 | 1.269667 | 0.596625 | 0.660179 | 1.000798 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-32767 | 0.380416 | 0.381583 | 1.235958 | 0.577750 | 0.660303 | 0.996942 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-16384 | 0.204812 | 0.205521 | 0.764645 | 0.300187 | 0.684116 | 0.996550 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-8192 | 0.128499 | 0.129542 | 0.558084 | 0.175271 | 0.735108 | 0.991956 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-4096 | 0.079105 | 0.079833 | 0.424604 | 0.101584 | 0.789551 | 0.990875 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-periodic-1024 | 0.039291 | 0.039166 | 0.325875 | 0.045625 | 0.869899 | 1.003192 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-1048576 | 22.447979 | 22.568521 | 28.761020 | 20.361208 | 1.104388 | 0.994659 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-262144 | 5.678396 | 5.712041 | 7.521916 | 5.053479 | 1.122782 | 0.994110 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-131072 | 2.792021 | 2.804813 | 3.847667 | 2.472541 | 1.127530 | 0.995439 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-65537 | 1.363687 | 1.373480 | 1.993604 | 1.172896 | 1.159790 | 0.992871 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-65536 | 1.350271 | 1.356917 | 1.977917 | 1.162333 | 1.159902 | 0.995102 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-65535 | 1.351500 | 1.358229 | 1.979313 | 1.162146 | 1.160307 | 0.995045 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-33027 | 0.639646 | 0.644437 | 1.081104 | 0.534667 | 1.195311 | 0.992565 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-32769 | 0.632500 | 0.636333 | 1.073542 | 0.528709 | 1.193386 | 0.993976 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-32768 | 0.619313 | 0.624792 | 1.060312 | 0.519084 | 1.192150 | 0.991230 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-32767 | 0.620979 | 0.628167 | 1.058688 | 0.519334 | 1.193491 | 0.988558 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-16384 | 0.303583 | 0.307458 | 0.642126 | 0.237750 | 1.278441 | 0.987395 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-8192 | 0.171083 | 0.175375 | 0.452125 | 0.125583 | 1.371414 | 0.975527 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-4096 | 0.107459 | 0.110959 | 0.372980 | 0.076250 | 1.415905 | 0.968457 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-random-1024 | 0.028041 | 0.028083 | 0.309917 | 0.033166 | 0.849015 | 0.998504 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-1048576 | 144.129917 | 140.479916 | 161.144895 | 199.562854 | 0.722307 | 1.025982 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-262144 | 40.268479 | 39.094709 | 45.351062 | 56.143021 | 0.717334 | 1.030024 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-131072 | 19.787396 | 19.182750 | 22.347459 | 27.230916 | 0.728637 | 1.031520 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-65537 | 10.353958 | 10.023167 | 10.798770 | 12.902958 | 0.806335 | 1.033003 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-65536 | 10.353500 | 10.020750 | 10.789250 | 12.909334 | 0.806467 | 1.033206 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-65535 | 10.376688 | 10.034584 | 10.800166 | 12.848500 | 0.807059 | 1.034093 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-33027 | 4.229729 | 4.092563 | 4.392938 | 4.852479 | 0.871057 | 1.033516 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-32769 | 4.182125 | 4.049937 | 4.351917 | 4.799625 | 0.871000 | 1.032640 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-32768 | 4.168230 | 4.033104 | 4.336666 | 4.790521 | 0.870572 | 1.033504 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-32767 | 4.165855 | 4.033646 | 4.338604 | 4.791021 | 0.869696 | 1.032777 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-16384 | 1.959959 | 1.883291 | 2.165709 | 2.156729 | 0.906935 | 1.040709 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-8192 | 0.879917 | 0.849979 | 1.135396 | 0.911250 | 0.968534 | 1.035222 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-4096 | 0.388749 | 0.378021 | 0.663312 | 0.392000 | 0.997714 | 1.028381 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | prefix-natural-1024 | 0.071584 | 0.070458 | 0.336605 | 0.058958 | 1.218315 | 1.015981 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | heldout-mixed-131073 | 6.264104 | 6.166250 | 8.406500 | 7.257500 | 0.863972 | 1.015869 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | heldout-random-65537 | 1.346250 | 1.359833 | 1.951021 | 1.150083 | 1.170122 | 0.990011 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | heldout-slides-65537 | 8.287375 | 8.070688 | 8.888750 | 10.121230 | 0.816498 | 1.026849 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | heldout-window-32768 | 4.168500 | 4.035479 | 4.337500 | 4.791646 | 0.870769 | 1.032963 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | heldout-window-32767 | 4.170083 | 4.034730 | 4.337229 | 4.791812 | 0.870797 | 1.033547 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | reymont-prefix-32769 | 4.179958 | 4.050833 | 4.352208 | 4.801291 | 0.870174 | 1.031876 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | reymont-prefix-16384 | 1.951416 | 1.878583 | 2.164645 | 2.153416 | 0.905504 | 1.038770 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | reymont-prefix-1024 | 0.071708 | 0.070500 | 0.336625 | 0.059000 | 1.221194 | 1.017135 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | repeated-32769 | 0.450208 | 0.449583 | 1.346459 | 0.690770 | 0.650523 | 1.001391 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | random-32769 | 0.631208 | 0.635437 | 1.075292 | 0.529167 | 1.193705 | 0.993344 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | repeated-1024 | 0.039084 | 0.039083 | 0.326375 | 0.046333 | 0.837637 | 1.000026 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | random-1024 | 0.027583 | 0.027542 | 0.307646 | 0.032875 | 0.842401 | 1.001489 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | random-256 | 0.017542 | 0.017542 | 0.297500 | 0.025875 | 0.690749 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | random-64 | 0.011042 | 0.010958 | 0.291083 | 0.022333 | 0.492084 | 1.007666 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 33027-periodic-window | 0.398209 | 0.399687 | 1.264895 | 0.592562 | 0.672333 | 0.996300 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 16384-distribution-change | 0.581041 | 0.573396 | 0.840001 | 0.483833 | 1.201067 | 1.013334 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 32-high-entropy-stored | 0.009666 | 0.009625 | 0.290042 | 0.021625 | 0.445867 | 1.004260 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 128-biased-dynamic | 0.015958 | 0.015875 | 0.288791 | 0.020209 | 0.776751 | 1.005228 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | eight-literals-prefix | 0.008417 | 0.008375 | 0.288916 | 0.021292 | 0.392800 | 1.005015 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | 320-overlap | 0.027083 | 0.027000 | 0.300125 | 0.027666 | 0.954959 | 1.003074 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | eight-overlap | 0.015583 | 0.015542 | 0.288917 | 0.021208 | 0.705700 | 1.002638 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | eight-literals | 0.008416 | 0.008375 | 0.288792 | 0.021375 | 0.392039 | 1.004896 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | seven-stored-prefix | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.007247 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | one-stored | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006907 | 1.000000 | {'roc': [], 'libdeflate': []} |
| pages-6-sqrt-plain | reverse | empty | 0.000041 | 0.000041 | 0.000042 | 0.004208 | 0.006697 | 1.000000 | {'roc': [], 'libdeflate': []} |
