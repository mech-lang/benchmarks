# Mech PR 993 benchmark records

This snapshot preserves the benchmark work from [Mech PR #993](https://github.com/mech-lang/mech/pull/993)
at `1c5cc197c988b4e64423735db5da14d9bfb37859`: **8,473 files and 1,282,615,484 bytes**.
Compiler implementation and maintained regression tests remain in Mech.
Original measurements, failed experiments, recipes and qualifications are unchanged.

[manifest.json](manifest.json) records every original path, mode, Git blob,
SHA-256 and byte count. The 8,127 smaller files and qualification
fixtures remain readable under [source/](source/). The 346
larger payloads are stored byte for byte inside deduplicated bundles in the
[pinned release](https://github.com/mech-lang/benchmarks/releases/tag/mech-pr-993-995-evidence-20261121).
Each original blob is an individually verifiable bundle member.

Verify the complete snapshot, including all pinned payloads:

```sh
python3 -B archive/compiler/mech-pr-993-1c5cc197c9/verify.py \
  --asset-dir /tmp/mech-pr993-pr995-evidence --download
```

Add `--restore-dir /tmp/mech-pr-993-records` to reconstruct every original
repository-relative path outside this checkout. Restored scripts can require
the original compiler revision, platform and toolchains; this migration makes
no new performance or completed-CI claim.

The qualification-policy tests remain with their frozen fixtures here and run
in the benchmarks repository's correctness workflow. The original Mech program
needed by compiler regression tests is retained byte for byte in Mech's native
test fixtures, so those tests do not download benchmark records.
