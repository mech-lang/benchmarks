# Direct map membership in Mech counting procedures

The candidate adds the general `map/contains-key(map, key)` predicate and maps
existing `∈` / `∉` syntax to it for map receivers. Set membership retains its
existing path. No parser grammar changes or counting primitive are introduced.

The counting procedure can now use the map itself:

```mech
increment(h<{string:u64}>, key<string>) => (out<{string:u64}>) :=
  previous := (key ∈ h)? | true => h{key} | false => 0u64.
  out := map/insert(h, key, previous + 1u64).
```

The Mech state machine still traverses all overlapping windows and performs the
count arithmetic and insertion. Membership performs one ordinary dictionary
lookup and creates no intermediate collection of keys.

## Verified result

The same 26-character diagnostic input,
`ACGTACGTNACGTTACGTACGTACGT`, now passes widths 1, 2, 3, 4, 6, 12 and 18 under
the unchanged default resident work policy. Every key and count matches an
independent BTreeMap reference; the seven totals are 26, 25, 24, 23, 21, 15 and 9.
The [preceding key-set version](../general-map-entry-v1/README.md) failed at
width six with 65,925 requested comparison units against 65,536. This study
removes the key-set construction; it does not increase that limit or modify the
preceding entry-work bound. These are bounded correctness/resource observations,
not full-size benchmark timings.

`source-v3` passes the original-artifact membership and seven-width tests.
`decoded-source-v2` passes three tests after encoding/decoding each artifact and
verifying byte-identical re-encoding. Additional cases cover integer, Boolean,
Unicode string and canonical signed-zero floating-point keys, empty maps/keys,
negative membership, mismatched kinds and invalid arity.

`map-runtime-v1` passes 30 filtered engine tests, including managed membership,
change reporting, no publication on resource denial, retry and unchanged input
storage. `source-suite-v2` passes 60 tests across eight source/catalog/managed
integration targets. `core-types-v1` passes 60 type/catalog tests. `linkage-v1`
passes the six map installers' identity checks without source/compiler features.
Together these final suites cover 151 distinct tests; earlier original/decoded
focused runs repeat a subset of those cases.

The committed candidate is `684e7471151b122c5c8c5bd15a0b0231e28b3be3`, based on
`fdb489566a7fa0a52cdb3086d9db3bfb12909ea0`. `seal.py --check` verifies committed
source hashes, terminal receipts, unchanged resource-policy definitions, retained
historical catalog identities and unchanged canonical benchmark data. Byte-exact
catalog captures are retained once in deterministic gzip form, with references
for duplicate captures.

## Integration and remaining work

The predicate returns a scalar Bool and uses `NoAdditionalScratch`; its managed
implementation resolves read leases and stages the Bool output through the
managed writer. The resident implementation reuses the admitted canonical-key
lookup, checks the actual map/selector schemas, and reserves publication before
lookup. `map_ops` enables Bool support. The installer declares that concrete
feature dependency, and profile checks verify it. Historical factory/source
fixture files remain unchanged; the three explicit new map operations are
checked independently of their retained historical projection.

Failed compile/test attempts remain terminal evidence. In particular,
`decoded-source-v1` used `{true: 1u64}`, which is a record with a named field;
`{(true): 1u64}` expresses the intended Boolean map key. `source-suite-v1` found
a stale expected installer feature list; the Bool output's explicit feature
requirement is now asserted. Neither failure is counted as a passing result.

The underlying ordinary map remains a canonical ordered dictionary. Direct
membership does not promise physical hashing. An explicit general hash-table
representation/entry contract, native ownership-aware lowering, complete-input
work witnesses and standalone AOT qualification remain required. Neither the
new predicate nor the earlier pure insertion operation has a native lowering
witness yet. No benchmark samples, timing comparison, catalog admission or
website publication occurs in this study. Normal abstract-map optimizations
remain on the preceding integration branch; this draft is not merge-ready.
