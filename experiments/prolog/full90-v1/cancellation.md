# Prolog full90: deliberate cancellation

The full90 study was deliberately cancelled on **14 October 2026 at 06:43 UTC**
during attempt 10, `prolog-revcomp-compact`. Source, retained compiled-code, and
SWI-Prolog runtime review established a whole-record string copy for every
sequence character. This creates quadratic copying work at the canonical input
size. The [technical analysis](../revcomp-linear-v1/README.md) explains the call
chain and its approximately 23.75 PB analytical copied-byte count; that count is
not measured memory traffic or a completion estimate.

The [cancellation record](cancellation-v1.json) identifies the verified main
controller and the requested SIGTERM. The
[attempt supervisor receipt](results/outer-supervisor/010-prolog-revcomp-compact.json)
records `KeyboardInterrupt`, `deadline_expired: false`, the owned sampler reaped,
and no cleanup errors. The [closure review](cancellation-review-v1.json) records
no remaining owned processes or groups and successful acquisition of the existing
ownership and timing locks. The [durable terminal](owned-jobs/full90/terminal.json)
records the controller's nonzero exit. **This was not a timeout.**

The [final report](results/report.json) and [terminal evidence](results/terminal.json)
retain 10 saved, registered attempts and nine qualified samples, with no active
attempt or unconfirmed native launch. The nine completed regex-redux samples
comprise three compact Prolog, three equivalent-source optimized Prolog, and
three matched Mech AOT control samples. All **27 original receipts**—raw sample,
sample supervisor, and outer supervisor for each—match the hashes saved before
cancellation. Their sample values, successful output validation, and qualified
environment records are unchanged. The full90 study remains
`stopped-unqualified`, with chart admission disabled.

[Attempt 10](results/attempts/010-prolog-revcomp-compact.wrapper.json) has no
admitted reverse-complement timing. Its interrupted elapsed duration is
diagnostic evidence only. Its environment was also unqualified: 18 monitor
observations between **05:02:00.385363 and 05:04:51.756990 UTC** recorded 42 unique
`rustc` PIDs and one `cargo` PID. These records contain executable basenames,
PIDs, and CPU percentages, but no command arguments or executable paths; they
do not establish who launched those processes. The earlier nine regex-redux
samples contain no competing-compiler observations.

The separate [bounded-chunk candidate](../revcomp-linear-v1/candidate.pl) and
[design and fixture notes](../revcomp-linear-v1/README.md) provide a follow-up
implementation for qualification. The candidate has not been executed or
measured. The cancelled study's original source, compiled subjects, and retained
receipts remain unchanged; no replacement timing or successful optimization is
claimed.
