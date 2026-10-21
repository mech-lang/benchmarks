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
independent review has passed; guarded catalog admission remains pending.

The preselected [full comparison](../../crystal/regex-byte-offsets-v1/full-v1/plan.json)
covers the retained parallel control, both parallel scan forms and the smallest
compact inline form. Its whole canonical N5m input,298-byte reference, binaries,
sources and discovered linked vendor-library bytes are pinned before timing.
The completed full comparison validates all twelve complete298-byte outputs.
Its [raw report](../../crystal/regex-byte-offsets-v1/full-v1/run-v1/report.json)
and [summary](../../crystal/regex-byte-offsets-v1/full-v1/summary.json) retain every
sample, spread, process capture and peak RSS. These full results supersede pilot
extrapolation; canonical admission remains a separate guarded step.

| Full N5m source | Median | × Mech AOT time | Sample SD | Speedup over matched control | Retained count proposal |
| --- | ---: | ---: | ---: | ---: | ---: |
| Retained parallel control |34.991s|71.47×|0.398s|1.00×|56 |
| Standard scan block, parallel |1.651s|3.37×|0.028s|21.20×|54 |
| Inline scan array, parallel |1.686s|3.44×|0.009s|20.76×|47 |
| Inline scan array, compact |2.572s|5.25×|0.058s|13.61×|32 |

The Mech AOT denominator is the retained full-size regex median **0.489612s
(1.00×)**, from a historical cohort, rather than a new member of the Crystal
cohort. [The relative report](../../crystal/regex-byte-offsets-v1/full-v1/mech-aot-relative-v1.json)
binds that exact profile, catalog snapshot, original samples and workload, and
retains a Mech AOT multiple for every Crystal observation. Reduced-input pilot
ratios to Mech AOT are unavailable: no equivalent reduced-input Mech measurement
was taken. Full-size seconds cannot normalize those pilots.

## Other prepared candidates

- [R fannkuch](../../r/fannkuch-masks-v1/proposal.json): ordinary prefix-reversal
  index masks and a bounded gather-index table. Actual permutations and reversals
  remain in R. An initial n=1shape concern was
  [retracted after control-flow review](../../r/fannkuch-masks-v1/static-boundary-review-v2.json):
  the only permutation has no flips, so the matrix lookup is not reached. The
  additive explicit-matrix form remains an optional unexecuted alternative.
  No R speedup or approved count is claimed.
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
