# Independently verified final source counts

The [independent count review](count-review-v1.json) admits the exact owner
projections for all fifteen authored files and all ten workload bundles. The
corrected tree and regex mains retain their earlier counts; the remaining
thirteen files and every bundle membership are unchanged.

The tree main has 34 canonical source units and 32 physical source lines. Its
complete bundle has 436 canonical units and 345 physical lines. The regex main
has 59 / 56, with a complete bundle of 469 / 375. All authored helpers, including
the shared C extension, are counted once in each applicable bundle.

Five focused binding tests passed. The separate
[independent validation](independent-validation-v1.json) replayed every owner
projection and bundle total with the pinned canonical counter. This admission
covers source counts only; required work, runtime equivalence, full timings and
chart admission are separate decisions. No native benchmark was run.
