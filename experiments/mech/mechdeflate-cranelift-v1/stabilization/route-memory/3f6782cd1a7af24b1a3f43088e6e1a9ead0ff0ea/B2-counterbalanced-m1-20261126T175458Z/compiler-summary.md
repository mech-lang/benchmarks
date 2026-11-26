# M1 compiler assessment

Independently verified decision **pass**. All 252 fixed compiler invocations completed.

Tooling `522da9237cc941880934339e403781b21fe89741`. Manifest SHA-256 `d73e9a607ec86707dfa33cf8f87a260ec6a7e2dc790dcf0f8a45f5748b57e094`.

| Role | Source | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | --- | ---: | ---: |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` | 2,158.646 | 393,150,464 |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` | 2,157.003 | 392,953,856 |
| B2 | `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea` | 2,154.730 | 392,757,248 |

| Control | Metric | A/A estimate | Simultaneous 95% interval | Resolution | Calibration |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | +0.0175% | -0.0066% to +0.0416% | +0.0492% | includes zero |
| R | maximum_resident_bytes | +0.0042% | -0.0186% to +0.0269% | +0.0340% | includes zero |
| O | elapsed_ns | -0.3160% | -0.7027% to +0.0722% | +0.7731% | includes zero |
| O | maximum_resident_bytes | -0.0014% | -0.0076% to +0.0049% | +0.0087% | includes zero |

| Control | Metric | Candidate change | Simultaneous 95% interval | Decision threshold | Gate |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.1947% | -0.3013% to -0.0879% | +0.0492% | pass |
| R | maximum_resident_bytes | -0.1293% | -0.1380% to -0.1206% | +0.0340% | pass |
| O | elapsed_ns | -0.1246% | -0.1693% to -0.0798% | +0.7731% | pass |
| O | maximum_resident_bytes | -0.0699% | -0.0800% to -0.0599% | < 0% | pass |

- Paired median candidate peak RSS change vs R was -499,712 bytes (-488 KiB).
- Paired median candidate peak RSS change vs O was -229,376 bytes (-224 KiB).

Percent changes use the paired-log estimates. The table of absolute medians uses the 36 measured blocks and excludes warmups. The assessment retains the six individual session ratios.
