# M1 compiler assessment

Independently verified decision **pass**. All 252 fixed compiler invocations completed.

Tooling `522da9237cc941880934339e403781b21fe89741`. Manifest SHA-256 `8bdb9b6759a4e45407ba31542aceac87149d15c079eeb8baf8d957288ef27088`.

| Role | Source | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | --- | ---: | ---: |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` | 2,158.646 | 393,175,040 |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` | 2,156.929 | 392,962,048 |
| F | `3a66a014c853e082ad907ed4db1673c9dadf0c69` | 2,157.625 | 392,790,016 |

| Control | Metric | A/A estimate | Simultaneous 95% interval | Resolution | Calibration |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.0926% | -0.3147% to +0.1299% | +0.3161% | includes zero |
| R | maximum_resident_bytes | -0.0058% | -0.0160% to +0.0044% | +0.0160% | includes zero |
| O | elapsed_ns | +0.0396% | -0.1080% to +0.1874% | +0.2075% | includes zero |
| O | maximum_resident_bytes | -0.0116% | -0.0245% to +0.0014% | +0.0263% | includes zero |

| Control | Metric | Candidate change | Simultaneous 95% interval | Decision threshold | Gate |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.0376% | -0.0938% to +0.0187% | +0.3161% | pass |
| R | maximum_resident_bytes | -0.1149% | -0.1257% to -0.1042% | +0.0160% | pass |
| O | elapsed_ns | +0.0482% | -0.0406% to +0.1372% | +0.2075% | pass |
| O | maximum_resident_bytes | -0.0607% | -0.0725% to -0.0488% | < 0% | pass |

- Paired median candidate peak RSS change vs R was -409,600 bytes (-400 KiB).
- Paired median candidate peak RSS change vs O was -188,416 bytes (-184 KiB).

Percent changes use the paired-log estimates. The table of absolute medians uses the 36 measured blocks and excludes warmups. The assessment retains the six individual session ratios.
