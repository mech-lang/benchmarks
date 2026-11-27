# Shared-fixture M1 qualification

**Compiler prerequisite unresolved.** The full compiler scope completed and the independent verifier reproduced its assessment. F passed both peak-memory gates and elapsed-time nonregression against R. Elapsed time against O remained unresolved.

The estimate against O was -0.0669%. Its simultaneous 95% interval ran from -0.2795% to +0.1460% against a calibrated limit of +0.1212%. The interval spans the limit, so the campaign stopped before runtime calibration.

## Identities and scope

The tooling commit is `0108617d529244d87e34fcbda26fb64170333f44`. The campaign manifest has SHA-256 `cd79ad7fd3ce2e07d22fe42af401728a6bebd96fcf56ff466102a6685d54dc83`. The measured host was Apple M1 on Macmini9,1 with native arm64, macOS 15.6.1 (24G90), Python 3.14.6, and Rust nightly-2026-03-03 at `ec818fda361ca216eb186f5cf45131bd9c776bb4`. The untimed Mach timebase read returned status 0, numerator 125 and denominator 3. [Campaign manifest](campaign.json)

| Role | Source commit |
| --- | --- |
| R | `8ce620d1b165b868210378ef260945ee3c398d05` |
| O | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` |
| N | `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea` |
| F | `3a66a014c853e082ad907ed4db1673c9dadf0c69` |

The sole staging change prepares one immutable fixture stage for the full campaign. Its active controller and case JSON are shared across all planned runtime legs, while each leg has its own result directory. The original actor, fixture and Silesia boundaries and the scheduled work were preserved. The shared stage was prepared and verified before the compiler scope. The recorded preparation command documents the actual canonical checkout and run paths. [Stage receipt](fixture-stage.json), [preparation command](preparation/fixture-stage-command.txt)

| Role | Compiler SHA-256 | Fixture worker SHA-256 | Silesia executable SHA-256 |
| --- | --- | --- | --- |
| R | `2f429836ccd4dc1bbcdb0f897d1a2d0bc92d90cd2a30a42b509bbf4c3f69f4e8` | `a1d911e785c1af81f3f3c2e2b93619954cee67c80801aafb5fa08f2a7d298af4` | `521d2e0e0ef937614702a20cba072a278f9960808fe4fb692130983efcebb156` |
| O | `c2afe0f29e47e67aade3ee91f9c03af61c5f2329d01db8fa4d86109935654b06` | `db5bda52092b9aef0f169bbd06ab773ca22b840ee8560ad77deff445a6646c17` | `03ad00438745e7469b45bb486b0ad9f5f9d2f736752141f73a7189ccb693aafa` |
| F | `002bd482028fdffc9ee9b470f0a00d689dac931c5db08eaabd81e83ca5117b1a` | `e1e626492ba2171d7bef0c8c43d0cb342d3c0707b4012f811f1cdfdaf57bd605` | `2aa76eb8d6f7add5241999ca39fb2fdb23702e3edbc34e4f943b9927fd92e9e7` |

All bound hashes and effective configurations match the qualified builds. The F recipe bytes match the earlier campaign. The already verified correctness and resource receipts apply to the unchanged actors. [Prepared bindings](prepared-bindings.json), [F recipe](candidate-recipe.json), [historical correctness and resource assessment](../F-m1-20261126T181433Z/assessment.md)

## Compiler results

All 252 compiler invocations completed across six calibration, three qualification and three confirmation sessions. Both calibration families included zero for elapsed time and peak RSS. Absolute medians use the 36 measured blocks per compiler. [Independent compiler verification](compiler-verification.json)

| Role | Median elapsed (ms) | Median peak RSS (bytes) |
| --- | ---: | ---: |
| R | 2,160.7312 | 393,183,232 |
| O | 2,159.5928 | 392,970,240 |
| F | 2,159.1823 | 392,790,016 |

| Same-build control | Elapsed 95% interval | Peak RSS 95% interval |
| --- | ---: | ---: |
| R | -0.1208% to +0.1238% | -0.0125% to +0.0102% |
| O | -0.0017% to +0.1210% | -0.0123% to +0.0146% |

| Comparison | Metric | Estimated change | Simultaneous 95% interval | Decision limit | Gate |
| --- | --- | ---: | ---: | ---: | --- |
| F / R | Elapsed | -0.1295% | -0.2279% to -0.0310% | +0.1247% | pass |
| F / R | Peak RSS | -0.1222% | -0.1327% to -0.1117% | +0.0126% | pass |
| F / O | Elapsed | -0.0669% | -0.2795% to +0.1460% | +0.1212% | unresolved |
| F / O | Peak RSS | -0.0614% | -0.0734% to -0.0493% | strictly below 0% | pass |

Fresh paired median peak RSS fell 475,136 bytes (464 KiB) versus R and 180,224 bytes (176 KiB) versus O. The earlier integrated run's **historical** paired median reduction versus O was 188,416 bytes (184 KiB). [Fresh compiler assessment](compiler/assessment.json), [historical compiler assessment](../F-m1-20261126T181433Z/compiler/assessment.md)

## Runtime disposition

The campaign stopped at the fresh compiler prerequisite. Runtime calibration and candidate timing each recorded zero sessions. Both runtime calibration decisions, per-case timing margins, absolute runtime durations and the final 81/81 and 12/12 counts remain unmeasured for this campaign. The historical precision reference was verified before measurement and its planned checks are listed below.

| Control | Precision coordinate | Historical log interval | Historical log width | Current log interval and width |
| --- | --- | --- | ---: | --- |
| reviewed | `fixtures/forward/prefix-natural-65536` | `[8.497303196423287e-05, 0.00094803033365611585]` | `0.00086305730169188304` | Unmeasured |
| reviewed | `fixtures/reverse/prefix-random-4096` | `[0.0047616984773046437, 0.010722000831248279]` | `0.0059603023539436355` | Unmeasured |
| reviewed | `fixtures/reverse/repeated-32769` | `[0.00061312981618819864, 0.0047832601206857697]` | `0.0041701303044975706` | Unmeasured |
| previous | `fixtures/forward/empty` | `[-0.023916524900737746, -0.0050763482156012639]` | `0.018840176685136482` | Unmeasured |
| previous | `fixtures/forward/prefix-periodic-65535` | `[0.0012370230100834326, 0.0022896081950609954]` | `0.0010525851849775628` | Unmeasured |
| previous | `fixtures/forward/prefix-random-1024` | `[0.00013144873872599828, 0.0022095005684843304]` | `0.0020780518297583324` | Unmeasured |
| previous | `fixtures/forward/suite-geomean` | `[-0.00071373251823431919, -8.3727915820432965e-05]` | `0.00063000460241388623` | Unmeasured |
| previous | `fixtures/reverse/prefix-random-1048576` | `[1.3874912100119699e-05, 0.0014757889648345252]` | `0.0014619140527344055` | Unmeasured |

The frozen integrated stack remains unverified for final runtime qualification. Linux cross-compilation passed in the earlier correctness run. Native x86 and M3 execution remain unverified. [Verified archive receipt](archive-receipt.json)
