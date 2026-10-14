# Retained R observations

This packet reconciles the completed N-body, binary-trees and fannkuch workloads
that are absent from the chart. It uses **18 saved R observations and nine
matched Mech AOT controls**, with three measurements per exact source. No
replacement performance run is needed.

The [verifier](../../../tools/qualification/r_retained_reconcile.py) checks the
original [complete R report](../../../archive/comparisons/r-apl-uiua-comparison/20261011/results/timings-r.json),
its frozen source audit, and the
[six independent source counts](../retained-source-counts-v1/qualified-source-counts-v1.json).
All six complete application sources have been read. N-body retains every
integration step and pair interaction; fannkuch visits the full permutation
range in bounded matrices and performs the prefix reversals; binary trees
allocates each node and keeps the long-lived root until its final check.
Retained small and adversarial output checks and the tree allocation fixture
remain bound to the original source/runtime records.

| Original observations | Evidence retained |
| --- | --- |
| 67–75: binary trees | Repaired runner's original report records |
| 76–84: N-body | Repaired runner's original report records |
| 85–87: first fannkuch round | Repaired runner's original report records |
| 88–93: remaining fannkuch rounds | Original sampler receipts, supervisor receipts and report records |

The continuation preserves all 87 earlier report records exactly. Its six
later observations are compared across the three actual representations;
only the documented supervisor and report metadata may differ. Earlier
observations retain their original schema: no independent sampler receipt,
supervisor receipt or per-attempt pin flag is invented. None of these 27
observations comes from the older pre-repair runner or requires its migration
exception. Existing unrelated exclusions and historical cohorts remain intact.

The saved-document phase checks the full workload sizes, complete output
references, balanced sample order, source/runtime fingerprints, native exit
status, process-group completion, power/compiler observations, resource limits,
sample arrays and statistics. Fresh-process elapsed time includes startup,
runtime/source preparation inside the process, workers, work, output and
shutdown. External builds, output validation and file hashing are outside it.
The full inherited ambient environment was not captured. A stored zero peak
RSS on a subsecond control means that the periodic monitor did not observe its
peak; it is not evidence of zero memory use.

`review_files` adds a deferred physical-file phase under the existing common
timing mutex and original owner leases. It checks the 104 source-audit pins and
1,429 continuation pins, exact retained/original document equality, source-count
dependencies and receipt bytes. It keeps an immutable input-pin inventory and
rechecks named lease identities after the final file replay, before the
caller's output check. A busy timing mutex fails immediately. It neither starts
a benchmark nor waits while interfering with an active timing owner.

The [eight focused tests](../../../tools/qualification/test_r_retained_reconcile.py)
exercise saved-record and source/count mutations, invented lifecycle fields,
native completion, output references, sample order and replacement of held
lease paths. They use saved documents and temporary test locks only. The actual
physical-file phase and chart publication have not run; passing these tests
does not admit timings to the catalog.
