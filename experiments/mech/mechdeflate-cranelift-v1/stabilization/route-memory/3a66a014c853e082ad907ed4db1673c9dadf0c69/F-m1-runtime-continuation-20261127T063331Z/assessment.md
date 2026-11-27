# M1 runtime continuation

The independent verifier reproduced the parent compiler assessment and the new runtime calibration.
Runtime calibration remained unresolved. Collection stopped before candidate qualification and confirmation.

| Scope | Decision |
| --- | --- |
| Compiler assessment (verified parent) | `unresolved` |
| Runtime calibration | `unresolved` |
| Runtime assessment | `not_run` |
| Combined assessment | `unresolved` |

[Independent runtime verification](runtime-calibration-verification.json) · [Machine-readable disposition](disposition.json)

## Identities

| Identity | Pin |
| --- | --- |
| Compiler parent campaign | `F-m1-shared-fixtures-20261127T044557Z` |
| Parent tooling | `0108617d529244d87e34fcbda26fb64170333f44` |
| Parent evidence | `d827ea55471c2d7000cd2addc9b105a15699e2ec` |
| Continuation campaign | `F-m1-runtime-continuation-20261127T063331Z` |
| Continuation tooling (T_cont) | `08ec4cafb287f541dfbbd10e2be825d19a8a5bc5` |
| Benchmark baseline | `3936f4b1d693aa7a26cd7954ba8cb011ee7cbed7` |
| R source | `8ce620d1b165b868210378ef260945ee3c398d05` |
| O source | `0bde021f93bd752ebf5e85ba2aaa29f84872caeb` |
| N source | `3f6782cd1a7af24b1a3f43088e6e1a9ead0ff0ea` |
| F source | `3a66a014c853e082ad907ed4db1673c9dadf0c69` |
| Parent manifest SHA-256 | `cd79ad7fd3ce2e07d22fe42af401728a6bebd96fcf56ff466102a6685d54dc83` |
| Parent compiler assessment SHA-256 | `5bbaf85c64f5b8bca8407fbe9173ebb57881554dd0f5910ee83cf641f8cc2acc` |
| Parent and continuation prepared bindings SHA-256 | `bb29424e5012a5c576d6e6be5765d43b22504f0ce0f3d6cb12a91403ab472283` |
| Continuation manifest SHA-256 | `b9e351338ca2c472e402f3f569fbfcc0765cc787149326f6b48e0b8bc38e63ae` |
| Continuation runtime calibration SHA-256 | `dc3f64a5035ada050cd66fc1714b1d6c7a56d8be70d21769f28d9c3ae31bbb67` |

The parent and continuation ran on the same native Apple M1 Macmini9,1, arm64, macOS 15.6.1 (24G90), Python 3.14.6, and Rust nightly-2026-03-03 at `ec818fda361ca216eb186f5cf45131bd9c776bb4`. The Mach clock timebase recorded status 0 and ratio 125/3. The exact R, O, and F actor binaries, recipes, configuration, and pinned Silesia inputs matched. The frozen actors were reused.

The fresh shared stage contains 257 files. Its fixture payloads, actors and controllers match the parent byte for byte. Three JSON files changed to record the new absolute paths. The path-bearing fixture inventory SHA-256 is `91c9c5823b2d0714d32c9f5e961af875a0afff638155045eae9dff35e5f539c8`, compared with `4a9d26216623e3c7299b5315ac48b6136ed77f1adf3802c2f18a5dc65f63f9cf` at the parent’s canonical path. [Campaign manifest](campaign.json) · [Prepared bindings](prepared-bindings.json) · [Fixture relocation receipt](preparation/fixture-relocation.json)

## Reconstructed compiler assessment

The verifier reconstructed 252 existing invocations (126 calibration, 63 qualification, 63 confirmation), including the prescribed warmups. The continuation collected zero new compiler timings. All 30 tooling tests passed, including the 22 existing tests. [Parent verification receipt](parent-verification.json) · [Tooling tests](preparation/tooling-tests.log)

Absolute medians use the 36 measured qualification and confirmation blocks per actor.

| Actor | Median compile elapsed (ms) | Median peak RSS (bytes) |
| --- | ---: | ---: |
| R | 2,160.7312290 | 393,183,232 |
| O | 2,159.5928125 | 392,970,240 |
| F | 2,159.1822920 | 392,790,016 |

The sealed values below are paired log ratios. The F / O peak RSS gate requires the upper endpoint to be strictly below zero.

| Comparison | Metric | Estimate | Simultaneous 95% interval | Decision limit | Gate |
| --- | --- | ---: | --- | ---: | --- |
| F / R | Elapsed | `-0.0012956589147392957` | `[-0.0022812327509547287, -0.00031008507852386263]` | `0.0012464558926936406` | pass |
| F / R | Peak RSS | `-0.0012228407193049765` | `[-0.001328183901036109, -0.001117497537573844]` | `0.0001258887811062173` | pass |
| F / O | Elapsed | `-0.000669613996795728` | `[-0.002798560273008051, 0.0014593322794165951]` | `0.0012114838057063046` | unresolved |
| F / O | Peak RSS | `-0.0006139136356450044` | `[-0.0007344058756462639, -0.0004934213956437449]` | `strictly below 0` | pass |

F / O elapsed was estimated at -0.066939%. Its interval spanned -0.279465% to +0.146040% and crossed the +0.121222% limit. Both peak-memory gates and F / R elapsed passed.

## Runtime calibration

Six sessions sealed in the prescribed alternating order. They contain 24 fixture legs and 11,791,872 timed fixture calls plus warmups, 24 paired Silesia legs, and 12 standalone Silesia session-order records. The controls compared each binary with itself through the A/B crossover.

| Session | UTC start | UTC end |
| --- | --- | --- |
| reviewed-1 | `2026-11-27T06:34:43.433603+00:00` | `2026-11-27T07:39:56.614116+00:00` |
| previous-1 | `2026-11-27T07:40:11.210837+00:00` | `2026-11-27T08:45:24.102266+00:00` |
| reviewed-2 | `2026-11-27T08:45:38.674810+00:00` | `2026-11-27T09:50:51.243668+00:00` |
| previous-2 | `2026-11-27T09:51:05.815719+00:00` | `2026-11-27T10:56:18.467886+00:00` |
| reviewed-3 | `2026-11-27T10:56:33.031218+00:00` | `2026-11-27T12:01:43.250757+00:00` |
| previous-3 | `2026-11-27T12:01:57.846178+00:00` | `2026-11-27T13:07:10.633326+00:00` |

| Control | Family size | 95% intervals excluding zero | Silesia 95% intervals including zero | Decision |
| --- | ---: | ---: | ---: | --- |
| R | 190 | 3 | 26 of 26 | unresolved |
| O | 190 | 4 | 26 of 26 | unresolved |

| Control | Coordinate | Log estimate | Simultaneous 95% log interval excluding zero |
| --- | --- | ---: | --- |
| R | `fixtures/forward/suite-geomean` | `0.0005103765361551079` | `[2.0006376513557892e-05, 0.001000746695796658]` |
| R | `fixtures/reverse/heldout-window-32767` | `0.0007501594121691853` | `[6.48321608000648e-06, 0.001493835608258364]` |
| R | `fixtures/reverse/prefix-periodic-16384` | `0.0035116882102355536` | `[0.0006358889954855731, 0.006387487424985534]` |
| O | `fixtures/forward/prefix-random-16384` | `0.00446010406869923` | `[0.000873356406949253, 0.008046851730449207]` |
| O | `fixtures/reverse/16384-distribution-change` | `-0.0030523358583196755` | `[-0.005881023428207694, -0.00022364828843165693]` |
| O | `fixtures/reverse/prefix-natural-32767` | `-0.0014650725988177482` | `[-0.0027116414938550535, -0.00021850370378044288]` |
| O | `fixtures/reverse/repeated-32769` | `-0.003411645078231895` | `[-0.006727848623909856, -9.54415325539336e-05]` |

The eight width caps come from the separate `F-m1-20261126T181433Z` runtime calibration seal with SHA-256 `f0997aa7c72b92e70ade50ad55d84e7260e56b15c75926c197059d8102b913e4`. All eight current intervals exceeded their cap.

| Control | Coordinate | Reference 95% log interval | Reference log width (cap) | Current 95% log interval | Current log width |
| --- | --- | --- | ---: | --- | ---: |
| R | `fixtures/forward/prefix-natural-65536` | `[8.497303196423287e-05, 0.0009480303336561159]` | `0.000863057301691883` | `[-0.0009138136817016975, 0.0013066876280174958]` | `0.002220501309719193` |
| R | `fixtures/reverse/prefix-random-4096` | `[0.004761698477304644, 0.01072200083124828]` | `0.0059603023539436355` | `[-0.013986667384987607, 0.013952030362825883]` | `0.02793869774781349` |
| R | `fixtures/reverse/repeated-32769` | `[0.0006131298161881986, 0.00478326012068577]` | `0.004170130304497571` | `[-0.0021181345944347825, 0.007652316120792576]` | `0.009770450715227358` |
| O | `fixtures/forward/empty` | `[-0.023916524900737746, -0.005076348215601264]` | `0.018840176685136482` | `[-0.0089430190744985, 0.038254686897690064]` | `0.047197705972188565` |
| O | `fixtures/forward/prefix-periodic-65535` | `[0.0012370230100834326, 0.0022896081950609954]` | `0.0010525851849775628` | `[-0.004764173284435955, 0.0038167560734948826]` | `0.008580929357930837` |
| O | `fixtures/forward/prefix-random-1024` | `[0.00013144873872599828, 0.0022095005684843304]` | `0.0020780518297583324` | `[-0.005810455994197021, 0.0040536878256214]` | `0.00986414381981842` |
| O | `fixtures/forward/suite-geomean` | `[-0.0007137325182343192, -8.372791582043296e-05]` | `0.0006300046024138862` | `[-0.0004961973796829967, 0.0017374714199313583]` | `0.002233668799614355` |
| O | `fixtures/reverse/prefix-random-1048576` | `[1.3874912100119699e-05, 0.0014757889648345252]` | `0.0014619140527344055` | `[-0.000655756913865055, 0.001434770454896466]` | `0.002090527368761521` |

[Runtime calibration seal](runtime/calibration.json)

## Candidate qualification and confirmation

The continuation completed 6 calibration, 0 qualification and 0 confirmation sessions. Candidate nonregression, timing margins, and absolute durations for F are unmeasured in both orders. The fixture and Silesia win counts against libdeflate and the second reference remain unverified.

| Candidate comparison | Order | Runtime nonregression | Fixture wins vs each reference (target 81/81) | Silesia wins vs each reference (target 12/12) |
| --- | --- | --- | --- | --- |
| F / R | Forward | Not run | Unmeasured | Unmeasured |
| F / R | Reverse | Not run | Unmeasured | Unmeasured |
| F / O | Forward | Not run | Unmeasured | Unmeasured |
| F / O | Reverse | Not run | Unmeasured | Unmeasured |

Native x86 and M3 execution remain unverified.

## Evidence

The archive holds all raw runtime observations, fixture stages, warmups, logs and receipts. It includes the exact sealed parent archive and inventory, pinned builds, source bundles, historical benchmark objects, and the Silesia corpus. Bundle prerequisites are listed in the verification log. The records bind original canonical paths. Use T_cont at the manifest’s benchmark checkout path for independent reconstruction. [Verified archive receipt](archive-receipt.json) · [Bundle verification log](preparation/verification-history.log)
