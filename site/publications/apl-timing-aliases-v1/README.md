# APL coverage and timing-alias validation

This packet records functional checks of explorer build `72094b4bd8833f60`,
built from source commit `7b714451029910cad47a53a7b4987a8c543c570a` and the
catalog containing the admitted APL binary-trees cohort. The
[asset manifest](build.json) binds the 35 emitted assets.

The [validation record](validation.json) retains the exact commands, source
and catalog hashes, output captures and zero exits for the isolated build and
seven Node suites. Projection parity covered all 973 programs and 902 source
files; the layer checks covered 216 combinations and 432 SVG renders. The
unchanged 12-method Python builder suite reuses its earlier passing captures
and exact source identities; it was not rerun for this build.

The [browser results](browser/mech-alias-apl-browser-v1.json) record passed
assertions at widths 390 and 1280, with no JavaScript errors. APL shows 19
programs sharing 48 distinct recorded runs; Uiua shows 17 programs and 48 runs.
The checks also retain 60 independent runs each for Prolog and Kotlin, and
exercise owner links, alias-only sample selection, pointer and keyboard actions,
sample-layer toggles, filters and local reset.

The [execution context](browser/execution-context.json) records an important
capture limitation: the browser assertions passed, but the Node process exit
status was not observed. The outer shell exited 1 afterward because it tried
to assign zsh's read-only `status` variable. The original
[stdout](browser/mech-alias-apl-browser-v1.stdout) and empty
[stderr](browser/mech-alias-apl-browser-v1.stderr) are preserved; no zero exit
or browser rerun is inferred.

The [mobile](browser/mech-alias-apl-browser-v1.apl-390.png) and
[desktop](browser/mech-alias-apl-browser-v1.apl-1280.png) screenshots are exact
captures. JSON and stream files are copied without rewriting their original
execution paths. These checks do not establish live deployment or new
performance measurements, and launched no benchmarks.

## Live deployment

The [publication receipt](publication.json) records website commit
`1024bfbc18c976c33b932af693be509294171c18`.
[Deployment verification](deployment.json) passed all 35 live assets and the
final manifest on October 15, 2026 at 05:29 UTC; both the build and Pages
deployment jobs succeeded.

A [fresh mobile browser](live-browser.json) verified 58 execution variants,
2,835 selected runs, sample visibility, language-page navigation and resource
filters with no JavaScript errors or horizontal overflow. The JSON arrived
compressed: 1,213,325 transferred body bytes decoded to 8,369,808 bytes with
the tested SHA-256. The [execution record](live-check-execution.json) retains
both successful process exits and exact verification-script identities.
These checks establish live behavior without adding performance measurements
or rerunning benchmark timings.
