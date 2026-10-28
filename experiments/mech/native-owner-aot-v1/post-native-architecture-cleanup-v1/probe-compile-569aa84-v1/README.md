# Probe compile and selection evidence

This archive preserves three bounded attempts without rewriting their reports or
process receipts. It verifies the external probe overlay can compile and select
all three exact ignored tests at cleanup source `569aa84ed0e80c08e954fe39add6f83ab21e5a3a`.
It contains no native probe execution or primary timing observations.

- `native-compiler-probes-compile-83ee-v1`: interrupted obsolete-source attempt.
  The original failed report, signal/cleanup receipt, and interruption reason remain.
- `native-compiler-probes-compile-adopted-v2`: both targets compiled at the adopted
  source, but the program-only feature excluded the host-gated kernel tests. The
  first exact ignored selection was empty and the runner rejected it.
- `native-compiler-probes-compile-adopted-v3`: the host feature compiled both
  targets and selected each of the three exact ignored tests once. No test body ran.

`manifest.json` maps each retained original path to its archive path, sizes, and
SHA-256 digests. `stdout.bin.gz` and `stderr.bin.gz` decompress losslessly; their
original and decompressed digests match. JSON receipts, reports, patches, and
other logs retain their original bytes. The result reports retain the exact
source/tree, runner, manifest, archived-probe, shared-controller, supervisor,
executable, process, and mutex pins. Checkout/target/tmp directories and compiled
executables are excluded. `v2-before-v3-sha256.json` records the unchanged failed
attempt before the corrected run began.

These records demonstrate compile and selection availability only. K-nucleotide
performance remains subject to the separate complete-process qualification.
