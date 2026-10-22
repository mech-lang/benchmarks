# Janet array-access candidates

This packet contains three local candidates for two remaining Janet workloads.
The historical v2 implementations remain unchanged. Every authored helper stays
in the source boundary; the standard runtime is unchanged. These candidates
have no full-size timing samples and are not chart entries or fastest claims.

For binary-trees, `binarytrees-cached` uses direct indexed access and retains the
left child across the branch and recursive check. Tree construction is unchanged:
every internal node and every leaf is a new mutable array. No node-count formula,
shared leaf, shared subtree, object pool or omitted traversal enters the program.

For fannkuch-redux, `fannkuch-get` changes callable-array reads to `get`.
`fannkuch-bulk` also copies each permutation into a reusable array using standard
`array/clear` plus `array/concat`, and rotates the prefix using `array/remove`
plus `array/insert`. Removing the first element shifts the complete suffix left;
inserting that element at the rank shifts the suffix right, restoring all
positions beyond that prefix. It is the same permutation ordering. The standard
runtime implements these generic array operations; no native permutation or
flipping kernel is added. All prefix flips, checksums and maxima remain Janet.
The checksum parity uses `mod` rather than `%`: its operands are nonnegative
integral ordinals and divisor 2. For the full N=12 workload all ordinals are below
2^29 and exactly representable, so the two ordinary numeric operators agree.
There is no 32-bit mask or changed full-work permutation count.

`qualify.py` runs all retained cases for both workloads, including N=0 and N=1.
Complete stdout is compared with the independent corpus. Additional projected
executions verify:

- Binary-trees: allocation count, check visits and number of distinct mutable
  node identities. A retained diagnostic table prevents collection/reuse during
  these bounded checks and rejects shared nodes. Formulas appear only in the
  independent checker; they are absent from every application source. This
  diagnostic necessarily has a different lifetime/memory policy from the timed
  application, and is never a performance observation.
- Fannkuch: every permutation's complete sequence, ordinal and exact flip count.
  A Python factoradic unranker supplies an independent order reference, then
  computes each prefix reversal. This checks every permutation through N=8,
  rather than trusting only the final checksum and maximum.

All native executions inherit the common timing mutex and the unchanged owned
process controller. They must run after active timing cohorts have closed.
`verify.py` replays the exact captures, source/projection hashes, complete output,
full work witnesses and process closure. Bounded correctness is not a full-size
output or performance claim.

`measure.py` keeps physical rows, UTF-8 bytes, deterministic gzip, pinned BPE and
native Janet lexical tokens distinct. Normalized logical and canonical formatted
LOC remain unqualified. The source manifest preserves original consulted sources,
contributors and Apache-2.0/BSD notices. Local authoring identifies Codex GPT-6
family; exact serving model is unknown.

Reproduce in a clean output directory with the pinned runtime available:

```sh
python3 experiments/janet/array-access-v1/qualify.py
experiments/source-metrics/.build/venv39/bin/python experiments/janet/array-access-v1/measure.py --run
python3 experiments/janet/array-access-v1/verify.py
```

Full-size controls, optimization alternatives, resource study and timing cohorts
remain pending. Standard array operations reduce written scalar loops; they do
not establish minimal source size or globally optimal performance.
