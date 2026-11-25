@codex review

Please review commit `93e684909475b4d58e0c683efdbe6ce78deca44c`.

The compiler recognizes when a literal histogram covers the tally's current input window. It emits a packed tally that checks four literal records at a time, subtracts match-covered source bytes and retains the checked length and offset updates. The fallback restores the counters before retrying. The entry selects the checked tally for windows below 2 KiB.

The Apple M1 run used 96 balanced blocks per case in each of the two orders across the original 81 cases, against libdeflate 1.26 level 12. Run the candidate with `MECH_COMPACT_SEEDED_HISTOGRAM=1` and use the same compiler with the flag disabled for the matched control. The candidate held all 66 protected wins in each order. The matched control won 64 in forward and 66 in reverse. The fixed 18-case mean positive gap fell from 8.382% to 7.150%. The maximum paired gap rose from 23.561% to 23.655%.

| Case | Control F / R | Candidate F / R | Improvement in fixed mean (pp) |
| --- | ---: | ---: | ---: |
| `prefix-random-1048576` | -1.969% / -1.903% | -3.612% / -3.463% | +0.0000 |
| `prefix-random-131072` | +0.047% / -0.102% | -1.642% / -1.504% | +0.0000 |
| `prefix-random-262144` | +0.553% / -0.280% | -1.019% / -1.983% | +0.0075 |
| `prefix-random-65536` | +2.918% / +2.928% | +0.750% / +1.011% | +0.1135 |
| `prefix-random-65537` | +2.731% / +3.122% | +0.872% / +1.201% | +0.1050 |
| `prefix-random-65535` | +3.421% / +3.294% | +1.076% / +2.218% | +0.0951 |
| `heldout-random-65537` | +6.115% / +4.129% | +2.330% / +2.191% | +0.1587 |
| `prefix-random-32768` | +5.101% / +5.055% | +2.850% / +3.373% | +0.1093 |
| `prefix-random-32767` | +4.525% / +5.618% | +2.677% / +3.618% | +0.1068 |
| `prefix-random-32769` | +4.818% / +5.925% | +2.946% / +3.842% | +0.1098 |
| `random-32769` | +5.158% / +5.822% | +3.263% / +4.891% | +0.0787 |
| `prefix-random-33027` | +5.239% / +5.731% | +6.640% / +4.241% | +0.0028 |
| `prefix-random-16384` | +12.643% / +11.601% | +10.142% / +9.846% | +0.1182 |
| `16384-distribution-change` | +14.349% / +15.170% | +12.856% / +13.659% | +0.0834 |
| `prefix-natural-1024` | +19.438% / +18.928% | +19.111% / +18.469% | +0.0218 |
| `prefix-random-8192` | +20.530% / +20.280% | +19.277% / +18.170% | +0.0935 |
| `reymont-prefix-1024` | +20.064% / +19.714% | +19.471% / +19.119% | +0.0330 |
| `prefix-random-4096` | +23.571% / +23.551% | +23.458% / +23.852% | -0.0052 |

The compiler checker reproduced the selected artifacts. The linked checks covered 162 exact output and alias observations, six named errors and 12 recoveries. The captured native tests exercised 176 entry declines, 44 literal rollbacks and 44 checked-error rollbacks. Six altered plans kept the checked path. Peak stack was 4,720 B against the 5,280 B cap. Encoder text grew by 1,296 B to 64,568 B. The stripped executable measured 210,024 B in both builds. Across 32 matched source-through-link builds, median build time was 2.190 s for the candidate and 2.194 s for the control.