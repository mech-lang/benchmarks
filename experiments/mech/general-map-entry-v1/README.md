# Pure map entries for source-level counting

The candidate adds `map/insert(map, key, value)`, a general functional entry
operation. It inserts or replaces one entry and preserves the input map. The
Mech procedure retains traversal, window selection, presence handling, count
arithmetic and state transitions. No runtime histogram/counting helper is added.

The baseline is compiler `e4799a38b466c808dc634137992128cf8e17376c`.
The source execution tests include this procedure inside an ordinary state
machine:

```mech
increment(h<{string:u64}>, key<string>) => (out<{string:u64}>) :=
  keys := {k | k <- h_keys}
  previous := (key ∈ keys)? | true => h{key} | false => 0u64.
  out := map/insert(h, key, previous + 1u64).
```

The state machine advances one position at a time and counts every overlapping
window. The seven-character fixture `GGTAGGT`, width three, produces `AGG:1`,
`GGT:2`, `GTA:1`, `TAG:1`; no queried-key subset replaces those entries. Guard
cases cover empty input, zero width and width greater than input length.

## Implementation and evidence

Managed and resident insertion share ordinary map semantics and canonical key
ordering. The resident path shares the admitted single-entry builder with
assignment, checks the borrowed base's declared schema identity, and publishes a
new value after successful construction. Tests cover preservation of the input,
replacement, insertion, integer/string kinds, matrix values and invalid calls.

A resource refusal encountered during footprint measurement is preserved as a
resource refusal rather than reported as invalid output. The resident regression
also checks no publication on refusal and successful retry.

String-entry finalization previously prepaid a quadratic upper bound for an
already ordered prefix plus one appended entry. The tighter bound funds the
actual extra last-key comparison, at most one old-prefix scan, and at most N
shifts. Old key bytes are visited at most twice and the new key at most N+1
times. It does not alter the actual finalizer or relax the work limit. Forty
independent cases run the real canonicalizer under the computed allowance,
including empty keys/maps, insertion positions, NUL, Unicode and long shared
prefixes; a budget below actual consumption is rejected. Other key kinds retain
their preceding conservative allowance.

`source-v6` passes the initial five source-entry tests. `map-runtime-v4` passes
28 filtered engine tests, including managed insertion, resident denial/retry,
existing map regressions and the independent work-bound cases.
`source-suite-v3` passes 57 tests across seven integration files. `core-types-v1`
passes all 60 solver/catalog tests. `linkage-v1` passes the compiler-free map
installer identity check. These final suites cover 146 distinct tests.
`map-schema-regression-v1` additionally reruns the two insertion tests after
adding a wrong-base-schema rejection assertion; it adds no distinct test count.

The committed candidate is `fdb489566a7fa0a52cdb3086d9db3bfb12909ea0`.
`seal.py --check` verifies source hashes, exact terminal receipts, passing counts,
retained catalog identities and the unchanged benchmark dataset.

The profile checks account explicitly for both `map/new` and `map/insert`.
Historical source/runtime fixture files remain unchanged. New-operation
contracts, arities, memory classes and exports are checked separately from the
retained historical identities. The catalog capture retains both actual runtime
and source inventories; it is an API identity diagnostic, not benchmark data.
Byte-identical duplicate captures are stored once in deterministic gzip form,
with per-attempt references retaining the uncompressed byte count and SHA-256.

## Retained failures and remaining work

- Earlier compile failures and stale profile-count expectations are retained as
  terminal attempts, not passing results.
- `source-v5` used the catalog-free helper with receiver shorthand. That test
  setup was corrected to compile against the same library catalog used during
  activation. The key set now uses an explicit comprehension over the projection.
- The larger all-width diagnostic uses `ACGTACGTNACGTTACGTACGTACGT` (26 characters).
  `width-two-diagnostic-v2` establishes a real default resident work refusal:
  66,457 comparison units requested against 65,536. Temporary logging was removed.
  After the tighter entry bound, `source-v9` reaches width six before refusal.
  `all-widths-diagnostic-v1` verifies the remaining cause at the committed
  candidate: 65,925 comparison units requested against the same 65,536 limit.
  The temporary instrumentation is retained as `activation-diagnostic.patch`
  and removed from the compiler checkout. This does not establish a wrong count
  or stale-state bug. The diagnostic source
  is retained in `all-widths-resident-probe.rs`; it can be copied into the stdlib
  tests directory to reproduce that default-policy probe. It is not a passing
  full-width qualification.
- Presence handling still constructs a key set. A direct ordinary lookup/default
  operation and ownership-aware lowering remain optimization work.
- The map constructor and insertion operation do not promise a hash-table
  representation. An explicit general hash-entry contract and native lowering
  remain required. The new entry operation has no native lowering witness yet;
  resident source execution is not standalone AOT qualification.
- Broader execution must be qualified with the native host's explicit finite
  policy. Final whole-process timings remain deferred. No new benchmark samples,
  catalog admission or website publication occurs in this study.
