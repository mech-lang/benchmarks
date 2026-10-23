# Batched native library updates

Compiler revision `be81aff98acbaaffb2a41dc2b1dea7c94d6efd2f` emits up to
128 initialized rolling keys into a fixed 2 KiB stack slot, then invokes one
synchronous library callback for the batch. Every key still performs an actual
hashbrown lookup/count update. The stack descriptor includes the buffer; both
partial batches and failure before complete publication are checked. ABI15 and
work policy40 reject preceding private callback contracts.

Seven focused tests pass. The complete native suite passes 168 tests, with
three ignored. The earlier complete run retained one stale version assertion
failure; it was corrected before the successful `tests-v3` run. No assertion
was removed. Source and decoded standalone builds produce identical executable
bytes. Twelve bounded cases, two permission denials, and both full outputs
pass, with seven completed tables and 874,999,961 actual updates per full
execution. `profile-v1` is an owned CPU-stack diagnostic, not a timing cohort.
No quantitative benchmark samples were collected.

This remains an experimental required-work lowering, not a replacement for
normal abstract-map optimization. The preceding canonical-native integration
branch retains the dense-counter and direct-query fast paths. Integration of
this lowering requires an explicit source-level operation/representation
contract in the map library, using existing grammar, and preserving ordinary
compiler freedom for the existing abstract map operations. No such source API
is claimed by this experiment. The draft PR must remain unmerged while that
work and further performance optimization are incomplete.

The canonical benchmark dataset and website are unchanged. `seal.py --check`
replays execution closure, binary identity, full output and required-work
witnesses and evidence hashes. Final timings remain deferred.
