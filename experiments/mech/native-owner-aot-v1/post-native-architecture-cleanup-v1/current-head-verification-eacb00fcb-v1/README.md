# Current cleanup verification

This records #939 at `eacb00fcb3352fbbf3d4dddb7b983f4c130f4a7b`, directly above
green #935 at `36bcb9292ed40676a4547c91588c96735785b139`.

- All 32 original/decoded objects, descriptors, metadata and bytecode files match
  the actual green #935 head byte for byte. The fresh-source build, exactly one
  selected test, immutable inputs and owned-process closure all validate.
  Baseline bytes remain in the architecture study's
  `contract-repairs-b4e7b151-36bcb929-v1/current-heads/snapshots-935/` archive.
- The repaired full-source distribution check passes all three profile tests
  and all 14 independent catalog cases, with complete owned-process closure.
- All 132 existing CI contract checks pass. The current cleanup head has a
  [clean review](https://github.com/mech-lang/mech/pull/939#issuecomment-6459909376).
- Three earlier CI jobs passed their profile assertions, then exhausted disk
  quota while rebuilding independent full-library fixtures. The new seven-line
  CI-only change retires completed temporary target directories before the next
  build. Compiler-produced bytecode stays outside its retired producer target
  for the independent runtime consumer. All commands, assertions, feature graphs
  and compiler settings remain unchanged.
- Rust cleanup diffs remain byte-identical to the historical cleanup patch. The
  current CI checkpoint is timestamped progress, not a completed green result.

No primary performance observation is collected here. The frozen historical
campaigns and their failed acceptance results are unchanged. Current-head full
correctness/process and runtime-speed qualification remain outstanding; these
representative artifacts are not an equal-speed claim.

`archive-manifest.json` pins every archived byte and lossless log/patch encoding.
Large non-timed test executables and full diagnostic process tables remain local
with hashes in `retained-local.json`. Idle earlier test executables were retained
losslessly before reclaiming roughly 43 GiB of cache space. Frozen measured
controls and source trees were preserved.
