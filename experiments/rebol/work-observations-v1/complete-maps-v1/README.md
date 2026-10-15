# Complete seven-map observation

This additive diagnostic retains the original knucleotide main and the existing
10,299-byte `arbitrary-widths` input. It records every key/count pair from each
of the seven actual maps after the main has written its complete 243-byte
benchmark output. The original map wrapper and failed capture remain unchanged.

The earlier global `stats/dump-series -1` diagnostic exceeded its 512 MiB RSS
limit after the main output completed. It traversed unrelated runtime series
and emitted a partial dump; no map sidecar was produced. This packet removes
that call, updates the relative path to the same main and changes only the
descriptive title/comments. It neither raises the memory limit nor changes any
benchmark source, runtime, extension, map loop or sidecar serialization.

The [pure consumer](map_contract.py) retains the exact original record-selection,
sliced-window histogram and complete-sidecar checks. It requires normal exit
zero, complete empty stderr and the caller-pinned full stdout. All seven maps,
their key domains, positive counts and complete window totals must match the
independent oracle. Missing, duplicate, changed, truncated or extra rows reject.

This observation establishes bounded map contents only. It does **not** observe
backing-series capacities, addresses or identities, hash-bucket capacities, or
a capacity growth trajectory. Those fields remain explicitly false. Retained
runtime source describes storage allocation/growth separately; it is not a
native capacity measurement. Full-size work, source/runtime equivalence, timing
and chart admission remain separate gates.

Six focused tests cover the new normal-exit/empty-stderr policy, exact known
maps, meaningful sidecar faults, unchanged helper functions, unchanged bounds
and the exact wrapper delta. All six passed in the
[final focused run](validation-v2/result.json); the earlier passing revision is
retained separately. A future single-process continuation observing all
seven maps must preserve the successful tree/Pi captures and the failed
global-dump capture, bind this source review, and use the existing owned observer
and resource limits. No native result is claimed by this packet.
