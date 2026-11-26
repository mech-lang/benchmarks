# M1 compiler assessment

Independently verified decision **unresolved**. All 252 fixed compiler invocations completed.

Tooling `ff7b0ff8c492e6a86c3e54de6a5938d50cdf593e`. Manifest SHA-256 `64336a4b54c3d65c7d84b40befeb0ae124c0ffe8b391103f0bb150268a1e6859`.

| Role | Source | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | --- | ---: | ---: |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` | 2,158.666 | 393,183,232 |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` | 2,155.447 | 393,166,848 |
| B2 | `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea` | 2,154.718 | 392,765,440 |

| Control | Metric | A/A estimate | Simultaneous 95% interval | Resolution | Calibration |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.0999% | -0.1641% to -0.0356% | +0.1650% | excludes zero |
| R | maximum_resident_bytes | +0.0067% | -0.0251% to +0.0386% | +0.0389% | includes zero |
| O | elapsed_ns | -0.0929% | -0.2670% to +0.0816% | +0.2949% | includes zero |
| O | maximum_resident_bytes | -0.0107% | -0.0253% to +0.0040% | +0.0276% | includes zero |

| Control | Metric | Candidate change | Simultaneous 95% interval | Decision threshold | Gate |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.1659% | -0.2368% to -0.0950% | +0.1650% | unresolved |
| R | maximum_resident_bytes | -0.1276% | -0.1409% to -0.1144% | +0.0389% | unresolved |
| O | elapsed_ns | +0.0218% | -0.0160% to +0.0595% | +0.2949% | pass |
| O | maximum_resident_bytes | -0.0802% | -0.0899% to -0.0706% | < 0% | pass |

- Paired median candidate peak RSS change vs R was -442,368 bytes (-432 KiB).
- Paired median candidate peak RSS change vs O was -368,640 bytes (-360 KiB).

Percent changes use the paired-log estimates. The table of absolute medians uses the 36 measured blocks and excludes warmups. The assessment retains the six individual session ratios.
