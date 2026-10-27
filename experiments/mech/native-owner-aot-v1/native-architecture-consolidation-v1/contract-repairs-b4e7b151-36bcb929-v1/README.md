# Current-head contract and artifact validation

This evidence covers the repaired #934 head
`b4e7b15168c9caced1dc10f5a487bd151a2ba976` and architecture #935 head
`36bcb9292ed40676a4547c91588c96735785b139`. It collects no timing samples and
does not modify or qualify either historical frozen timing campaign.

- #934 CI run 40533852218 passed. #935 run 40533994980 attempt 2 resumed only
  incomplete work after the earlier cancellation. The timestamped CI checkpoint
  here records progress, not a completed green result.
- The current #935 head has a [clean review with no findings](https://github.com/mech-lang/mech/pull/935#issuecomment-6451363674).
- All 32 original/decoded object, descriptor, metadata and bytecode files are
  byte-identical between these two actual source heads. Both exact-one-test
  executions and complete process closure receipts passed. Baseline uses the
  byte-identical pinned harness overlay, removed after execution. A fresh Cargo
  target was used for #934; every workspace package artifact was removed before
  switching that target to #935. The two test executables were hash-pinned and
  retained locally before any later cache use.
- The architecture patch remains byte-for-byte identical to the historical
  `a093aea` to `7543c56` patch. The repairs restore indexed missing-key rejection,
  existing-key map footprint accounting, unused-Bool-schema admission and exact
  bounded-snapshot resource errors. No limit or failing expectation is relaxed.
- At repaired #934, all 77 selected native tests pass: four structural-map tests
  and 73 closed-map tests. Base-repair validation retains 52 minimal-source,
  422 full-source and 76 core-snapshot passes. The engine run has 810 passes and
  one independently reproduced integration-baseline option-footprint failure;
  the raw failure is retained and is not relabelled as a passing scope.

The compatibility audit is partial. Historical 51-scope and 16-process results
belong to `7543c56`, not this newer source. Current-head full correctness and
performance qualification remain separate requirements. The historical timing
studies still fail their original acceptance policy. This comparison is not an
adoption of these heads into those immutable timing plans.

`archive-manifest.json` pins every archived byte and lossless log compression.
Large non-timed test executables and diagnostic tables containing unrelated
processes remain retained locally with hashes in `retained-local.json`.
