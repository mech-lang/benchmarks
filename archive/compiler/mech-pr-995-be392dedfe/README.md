# Mech PR 995 benchmark records

This snapshot preserves the benchmark work from [Mech PR #995](https://github.com/mech-lang/mech/pull/995)
at `be392dedfe0e8439bf632882e4bb302b92f4dbcc`: **11,830 files and 4,081,915,462 bytes**.
Compiler implementation and maintained regression tests remain in Mech.
Original measurements, failed experiments, recipes and qualifications are unchanged.

[manifest.json](manifest.json) records every original path, mode, Git blob,
SHA-256 and byte count. The 11,313 smaller files and qualification
fixtures remain readable under [source/](source/). The 517
larger payloads are stored byte for byte inside deduplicated bundles in the
[pinned release](https://github.com/mech-lang/benchmarks/releases/tag/mech-pr-993-995-evidence-20261121).
Each original blob is an individually verifiable bundle member.

Verify the complete snapshot, including all pinned payloads:

```sh
python3 -B archive/compiler/mech-pr-995-be392dedfe/verify.py \
  --asset-dir /tmp/mech-pr993-pr995-evidence --download
```

Add `--restore-dir /tmp/mech-pr-995-records` to reconstruct every original
repository-relative path outside this checkout. Restored scripts can require
the original compiler revision, platform and toolchains; this migration makes
no new performance or completed-CI claim.

The qualification-policy tests remain with their frozen fixtures here and run
in the benchmarks repository's correctness workflow. The original Mech program
needed by compiler regression tests is retained byte for byte in Mech's native
test fixtures, so those tests do not download benchmark records.
