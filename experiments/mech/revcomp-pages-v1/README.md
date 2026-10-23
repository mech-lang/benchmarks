# Mech streamed-record runtime Pages deployment

The [Benchmark Explorer](https://mech-lang.org/benchmarks/) serves build
`5da585f5c98f3a15`, containing four separately measured Mech runtime configurations
and all **28 fresh observations** from the verified seven-round cohort. All
**41 published assets** match the tested local manifest, including the complete
dataset and reproduction index. Verification completed October 23, 2026 at
00:02 UTC; the GitLab Pages build and deployment jobs both succeeded.

Benchmark source checkpoint: `44f48ac24cb833b2d090b560ef994cd35f2fc672`.
Website commit: `dc049182447a4abd86f6b91029fbc9c31ad871f2`, based on
`b9829651c8056f5e254d52d7b13efd542268c5a9`. Only benchmark assets change.
Frontend source bytes match the preceding website after cache-version
substitution; other website content is preserved.

[Pipeline 2978862828](https://gitlab.com/mech-lang/web/website/-/pipelines/2978862828)
completed successfully. `publication.json` records the verified remote commit;
`live-verification.json` verifies all versioned assets and rechecks the live
manifest after fetching them.

The selected Mech reverse-complement endpoint is **0.1229 s (1.00× new Mech AOT)**,
versus **0.1433 s (1.17×)** for the freshly measured original parent. Combined
compaction and completed-buffer reuse reduce elapsed time 14.3% and observed
peak RSS 49.6% in that cohort. Unchanged published Rust remains in the retained
comparison study at **0.1107 s (0.90×)**; its control observations are not added
by this Mech-only admission.

The Data view distinguishes emitter and runtime commits and retains the full
emitter/application build recipes, environment, worker settings, generator/input
and output identities, all seven samples per configuration, and source/binary
pins. Original source authorship and license gaps are preserved. The application's
seven-unit retained count is unchanged; no new logical-owner or formatted LOC
qualification is claimed. All older sources, observations and fixed global
normalization baselines remain intact.

Local validation includes 74 Python checks, twelve JavaScript core suites,
canonical/browser parity, source-axis browser checks, and desktop/mobile Data
interactions and exports. Receipts and closed validation-orchestration attempts
are retained in the [admission packet](../revcomp-publication-v1/README.md).
No benchmark was run during catalog admission or website publication. Compiler
changes remain separately reviewable in [PR #910](https://github.com/mech-lang/mech/pull/910).
