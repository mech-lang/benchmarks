# General map operations for source-level counting

This study identifies and repairs general library/compiler gaps needed to keep
window traversal, lookup, arithmetic and insertion in a Mech counting procedure.
It does not add a runtime histogram shortcut. No benchmark sample is collected,
and the canonical dataset and published nucleotide timings remain unchanged.

The baseline is compiler `be81aff98acbaaffb2a41dc2b1dea7c94d6efd2f`.
`source-probes-v1` and `source-probes-v2` compile small public-source programs
with that pinned compiler. Compilation alone does not prove execution support:
entry writes compiled while missing-key writes failed during execution.

The candidate adds ordinary missing-key insertion to the managed assignment
and resident assignment implementations, retaining existing-key replacement,
canonical key equality/order, declared cardinality limits and resource admission.
New keys must fund their retained payload as well as their value. The generic
`map/new()` constructor obtains key/value kinds from its declared result and
creates an empty growable map. It performs no traversal or counting. Contextual
inference now supplies result kinds and output-only dimensions for nullary calls.

`source-v10` passes two execution tests for string→integer and integer→string
maps. `source-v11` passes all four tests in `source_op_assign_contract`, including
invalid constructor rejection and the existing indexed matrix assignment test.
`source-v12` passes all five source tests after adding fixed-cardinality
replacement/growth checks. `solver-v2` passes all 34 type-solver tests.
`map-runtime-v1` passes 25 filtered engine tests, including managed constructor
execution, insertion/replacement, canonical equality and existing admission
checks; the same filter selects zero stdlib unit tests, which is not additional
coverage. `linkage-v1` passes the installer identity test with only `map_ops` and
`native-link`, without source/compiler features. These are focused correctness
checks, not full native standalone qualification. `catalog-v1` passes 26
source type/catalog contract tests. Together these final focused suites contain
91 passing tests. The candidate is committed as
`e4799a38b466c808dc634137992128cf8e17376c`; `seal.py --check` verifies the
committed source hashes, closed attempt receipts and unchanged canonical data.

Earlier failed compilation/execution attempts are retained. In particular,
`source-v8` repeated the prior candidate because its preceding edit used the
wrong working directory; it is not evidence for the later inference change.
Every completed attempt has an owned-process receipt with terminal status,
reaping and process-group closure. Build elapsed times are diagnostic metadata,
not benchmark samples.

## Remaining requirements

- A mutable-local increment helper remains rejected by the pure state-machine
  control gate. A general pure entry operation is needed; the gate must not be
  bypassed to accept hidden mutable state.
- Ordinary maps store canonical ordered entries. A required hash-table
  representation needs a general library contract and corresponding lowering.
  The current constructor does not promise hashing.
- A typed empty literal retains an exact zero cardinality. The constructor does
  not claim to fix literal widening or empty maps with a zero dynamic upper bound.
- Native standalone qualification, resource-denial checks and final complete
  process timings remain required before admitting a new benchmark result.
- The preceding integration branch retains its abstract-map dense/query
  optimizations. This draft work must not globally replace those optimizations.
