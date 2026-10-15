# Independent full90 result review

`tools/qualification/rebol_reconcile.py` independently reconstructs the 90-slot
rotation and checks each raw sampler, supervisor and outer observer record. It
does not import the timing producer. The prerequisite consumer replays the
actual extension, primitive, shared-corpus, required-work and source-count
evidence under the original leases.

The 16 synthetic test methods passed on 2026-10-15 UTC in
[the repaired-run record](../../../shared/pure-validation-20261015/post-prolog-pure-validation-repaired-v1/report.json); the earlier failed run
remains in [the initial record](../../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). No prepared
timing plan, completed timing report or successful reconciliation is implied.
Native measurements, source freezing and independent physical review remain
pending.

The consumer API is
`review_context(plan_path, plan_sha256, durable_directory, consumer_sha256, *, on_exit_failure=None, final_consumer_check=None)`.
`review_files` names the same context manager. The caller supplies actual
reviewed plan and consumer digests. It yields one deterministic result while
holding the existing full90 durable lease, suite lease and all qualification
leases. No measurement file or original receipt is rewritten.

Both public forms require three distinct fresh samples. Their one authored
source bundle is disclosed as an alias; their timings are never copied. A
failed form retains its observations without a partial median. A failed Mech
control also excludes both corresponding subject endpoints; successful subject
medians may remain descriptive, with no ratio or endpoint eligibility.

The result records every actual observation and receipt reference, all 15
counted source files through the ten qualified bundles, and the reproduced
qualification. Canonical and physical counts are retained; formatted counts
remain absent. The complete process boundary includes runtime startup, source
and facade evaluation, extension loading, input, work, output and shutdown.
Runtime publication metadata and chart admission require separate review.

Publication consumers must provide restoration and final output checks. Body
errors, late pin or inventory changes, and inherited helper exit failures all
invoke restoration. A late failure after an inherited lease closes must not be
described as occurring under that closed lease. Successful timing reports with
failed integrity terminals are rejected.
