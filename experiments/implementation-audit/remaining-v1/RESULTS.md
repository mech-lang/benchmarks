# First database-wide candidate tranche

The [starting queue](queue.json) binds1,067profiles across54families;44families
contain local or derived sources. Its351protected upstream profiles are unchanged.
The additional [TypeScript review](typescript-review.md) inspects all ten workloads
and binds their exact sources in [typescript-review.json](typescript-review.json).
These records distinguish source review from native qualification and timing.

## Bounded native checks

[native-v1/report.json](native-v1/report.json) records six successful builds and
100 complete-output comparisons across TypeScript nucleotide, Crystal regex and
D reverse complement. Every one of the50new-candidate outputs matches its
independent reference. Four known retained D parser differences are preserved:
comments, preheader text, CRLF empty records and bare carriage-return separators.
No old source or historical observation was repaired in place.

Crystal's later validation-once variants pass16additional complete outputs and
two invalid-UTF8rejections. Its standard scan variants pass32outputs and four
invalid-UTF8rejections. See the language-specific receipts. These checks do not
constitute a general whole-language correctness proof or full work certificate.

## Reduced-input pilots

All samples use fresh processes, include startup/input/work/complete output/exit,
and run sequentially under the common lock. Three shuffled rounds are retained.

| Exact comparison | Input scope | Control median | Candidate median | Interpretation |
| --- | --- | ---: | ---: | --- |
| TypeScript string keys → rolling numeric keys | First1m THREE bases only |0.394139s|0.275464s|1.43×pilot speedup; preceding records omitted; full-size result pending |
| D full output appender → in-input compaction/bounded output | Fixed4MiB TWO +4MiB THREE subset |0.038133s|0.033716s|1.13×pilot speedup; short samples/startup remain relevant |
| Crystal character → byte offsets only | Same TWO/THREE subset |1.690604s|1.695933s|No useful observed gain; standard String conversion already has an ASCII fast path |
| Crystal repeated → once-per-subject UTF8validation | Same subset, separate three-way cohort |1.691966s|0.422470s|4.00×pilot speedup; first validation remains enabled |

The [first pilot](pilot-v1/run-v1/report.json) used an8MiB prefix consisting of
uppercase ALU data. It remains valid as an I/O/no-match diagnostic but does not
exercise the hypothesized repeated-match cost. It was retained and superseded
for Crystal selection by [the mixed-record pilot](pilot-v2/run-v1/report.json),
which requires a nonzero count for every one of the nine patterns.

The later [scan comparison](scan-pilot-v1/run-v1/report.json) compares six source
forms on the same mixed-record input. The parallel block and inline-array forms
have0.424212/0.424409s medians; their small difference is within observed spread.
The shortest compact inline form has a0.517698s median. Retained-policy count
proposals are54/47units for the two parallel forms and32for compact inline,
versus56for the retained parallel and41for retained compact. These are exact
retained Crystal policy replays, not new uniform logical-LOC qualifications;
independent approvals remain pending.

The preselected [full comparison](../../crystal/regex-byte-offsets-v1/full-v1/plan.json)
covers the retained parallel control, both parallel scan forms and the smallest
compact inline form. Its whole canonical N5m input,298-byte reference, binaries,
sources and discovered linked vendor-library bytes are pinned before timing.
Full results must be read from its completed report, not extrapolated from this
pilot table. Canonical admission is a separate guarded step.

## Other prepared candidates

- [R fannkuch](../../r/fannkuch-masks-v1/proposal.json): ordinary prefix-reversal
  index masks and a bounded gather-index table. Actual permutations and reversals
  remain in R. Static review caught the n=1vector/matrix boundary in the small-mask
  source; its [additive replacement](../../r/fannkuch-masks-v1/static-boundary-review-v1.json)
  remains unexecuted. No R speedup or approved count is claimed.
- [Pony tree batching](../../pony/tree-batches-v1/proposal.json): bounded work per
  actor behavior, with smaller batches at deeper levels and yields between
  batches. Native allocation, GC/lifetime, fairness, source counts and timings
  remain pending.
- TypeScript rolling-map and D compaction candidates need further required-work,
  owner-count/runtime qualification and independently preselected full-size runs.

No candidate in this tranche has been added to the canonical catalog or chart.
Exact failures, unsuccessful hypotheses, sources, citations and process captures
are retained. A lowest observed candidate median never establishes global
optimality or minimum idiomatic source.
