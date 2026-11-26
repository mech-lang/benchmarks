# M1 compiler assessment

Independently verified decision **unresolved**. All 252 fixed compiler invocations completed.

Tooling `ff7b0ff8c492e6a86c3e54de6a5938d50cdf593e`. Manifest SHA-256 `950ea8b1a0b611a04e34aa8d96c81be9acb5372ddccb54c180fbd9bac0b6ddf5`.

| Role | Source | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | --- | ---: | ---: |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` | 2,158.361 | 393,150,464 |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` | 2,154.789 | 393,068,544 |
| B | `805ab41d6b2c2ae6ae62a09647cd31eb51be8661` | 2,155.290 | 392,773,632 |

| Control | Metric | A/A estimate | Simultaneous 95% interval | Resolution | Calibration |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | +0.0249% | -0.0970% to +0.1468% | +0.1627% | includes zero |
| R | maximum_resident_bytes | +0.0086% | -0.0134% to +0.0306% | +0.0334% | includes zero |
| O | elapsed_ns | +0.0110% | -0.0264% to +0.0485% | +0.0525% | includes zero |
| O | maximum_resident_bytes | -0.0236% | -0.0500% to +0.0028% | +0.0529% | includes zero |

| Control | Metric | Candidate change | Simultaneous 95% interval | Decision threshold | Gate |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.1696% | -0.2482% to -0.0910% | +0.1627% | pass |
| R | maximum_resident_bytes | -0.1100% | -0.1192% to -0.1007% | +0.0334% | pass |
| O | elapsed_ns | +0.0485% | +0.0062% to +0.0909% | +0.0525% | unresolved |
| O | maximum_resident_bytes | -0.0742% | -0.0842% to -0.0642% | < 0% | pass |

- Paired median candidate peak RSS change vs R was -376,832 bytes (-368 KiB).
- Paired median candidate peak RSS change vs O was -286,720 bytes (-280 KiB).

Percent changes use the paired-log estimates. The table of absolute medians uses the 36 measured blocks and excludes warmups. The assessment retains the six individual session ratios.
