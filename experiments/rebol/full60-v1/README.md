# Ten-program Rebol timing cohort

This cohort implements the [distinct-program policy](POLICY.md): one canonical
Rebol implementation for each of ten workloads, with three fresh subject samples
and three matched Mech AOT controls per workload. The earlier ninety-process
proposal remains unchanged. No second program record or measurement alias is
created for identical source.

`tools/qualification/rebol_full60.py` retains the original sampler, independent
supervisor, receipt validation, failure isolation and process-ownership checks.
The measured interval still covers a fresh complete process. The new source
review pins the original producer, frozen timing helpers, final qualification
entrypoint and this cohort's policy. Preparation must reproduce an actual final
qualification context; a source review or prepared plan cannot admit timings.

The schedule contains sixty distinct slots: thirty Rebol processes and thirty
controls. Subject/control order alternates across three rounds. A failed profile
retains its observed failure and skips only its remaining slots; incomplete
profiles receive no median or comparative endpoint. Integrity failures stop the
cohort. There are no automatic retries, preparatory native probes or compilations.

The independent reconciler, exporter and catalog importer must use the same
ten-program policy before publication. They must preserve each actual observation,
matched control, source count and failure; selecting the same program for both
fastest and fewest-lines endpoints does not create another observation.

Focused tests exercise the complete sixty-slot schedule, mutations and omissions,
failure accounting, one-program source policy, all ten counted bundles, unchanged
measurement and cleanup functions, and the reviewed qualification entrypoint.
Their execution records are retained separately. No full-size native result is
claimed by this source packet.
