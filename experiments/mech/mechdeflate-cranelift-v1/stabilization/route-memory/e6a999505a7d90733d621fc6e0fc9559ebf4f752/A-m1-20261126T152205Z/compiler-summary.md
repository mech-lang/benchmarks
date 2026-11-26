# M1 compiler assessment

Independently verified decision **unresolved**. All 252 fixed compiler invocations completed.

Tooling `ff7b0ff8c492e6a86c3e54de6a5938d50cdf593e`. Manifest SHA-256 `bf0480cd79eb03874ae01bf1f36cb4db8013884de0493ab24509e6504dfb451d`.

| Role | Source | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | --- | ---: | ---: |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` | 2,157.955 | 393,175,040 |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` | 2,155.694 | 392,953,856 |
| A | `e6a999505a7d90733d621fc6e0fc9559ebf4f752` | 2,155.174 | 393,166,848 |

| Control | Metric | A/A estimate | Simultaneous 95% interval | Resolution | Calibration |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | +0.1108% | +0.0840% to +0.1377% | +0.1392% | excludes zero |
| R | maximum_resident_bytes | +0.0007% | -0.0271% to +0.0285% | +0.0300% | includes zero |
| O | elapsed_ns | +0.1162% | +0.0505% to +0.1820% | +0.1858% | excludes zero |
| O | maximum_resident_bytes | -0.0016% | -0.0123% to +0.0091% | +0.0130% | includes zero |

| Control | Metric | Candidate change | Simultaneous 95% interval | Decision threshold | Gate |
| --- | --- | ---: | --- | ---: | --- |
| R | elapsed_ns | -0.1154% | -0.2127% to -0.0181% | +0.1392% | unresolved |
| R | maximum_resident_bytes | -0.0224% | -0.0376% to -0.0073% | +0.0300% | unresolved |
| O | elapsed_ns | -0.0157% | -0.1077% to +0.0764% | +0.1858% | unresolved |
| O | maximum_resident_bytes | +0.0397% | +0.0285% to +0.0510% | < 0% | unresolved |

- Paired median candidate peak RSS change vs R was -57,344 bytes (-56 KiB).
- Paired median candidate peak RSS change vs O was +212,992 bytes (+208 KiB).

Percent changes use the paired-log estimates. The table of absolute medians uses the 36 measured blocks and excludes warmups. The assessment retains the six individual session ratios.

A's peak RSS interval is above zero against O, so the measurements do not support the required strict improvement. Both time calibrations excluded zero. Comparing the controller's clock to the compiler's own total places the elapsed discrepancies mostly in the native phase of the identical builds. The sealed records show the effect and leave its cause unresolved.
