# Mech pi-digits Pages deployment

The [Benchmark Explorer](https://mech-lang.org/benchmarks/) serves build
`66e4796d6f7171fd`, containing the verified Mech pi-digits catalog admission and
native logical-source projection. All **41 published assets** match the tested
local manifest, including the dataset and full reproduction records. Verification
completed on October 22, 2026 at 23:01 UTC.

The benchmark source checkpoint is `7e7033fb4656b8b5088f4e73666c44016ee2dff5`.
Website commit `b9829651c8056f5e254d52d7b13efd542268c5a9` updates only the
benchmark assets, based on website commit `1754e93bdde2471d4963f01083d339f4b86ffacd`.
Its frontend sources match the prior website after cache-version substitution;
this is a data/source-proof update. Other website content is preserved.

GitLab [pipeline 2978722595](https://gitlab.com/mech-lang/web/website/-/pipelines/2978722595),
the Pages build and its deployment job all succeeded. `publication.json` records
the verified pushed commit; `live-verification.json` records the completed live
checks, including a manifest recheck after all versioned assets were read.

The site retains all 21 fresh Mech samples alongside older cohorts. Its fastest
Mech pi-digits endpoint is 0.2901 seconds (1.00× optimized Mech AOT), versus the
fresh parent's 0.3128 seconds (1.08×). The new source has 37 qualified logical
units. The original 35-unit form remains the smallest retained Mech endpoint.
No benchmark was run during admission or publication.

Local validation covers 71 Python checks, twelve JavaScript core suites, complete
canonical/browser projection parity, source-axis browser checks, desktop/mobile
Data interactions and exports. Those receipts are retained in the separate
[catalog admission](../pidigits-publication-v1/README.md).
