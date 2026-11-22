# Mech PR 973 records

These records were relocated from [mech-lang/mech#973](https://github.com/mech-lang/mech/pull/973)
at source revision `9087b1f07727a9bfcb7c09059f48edaca6dc2301`. The compiler
implementation and maintained regression tests stay in Mech. This directory
preserves the study record without changing its results or qualifications.

The snapshot contains **32,786 original files and 2,368,576,303 bytes**:

- Related Post Gen sources, generated projects, raw observations and validation records.
- DEFLATE experiments, comparison/profiling tools, packets and measured source variants.
- 373 design/measurement reports added by the compression work.
- Four standalone measurement probes and the pinned block-oracle generator test.

[manifest.json](manifest.json) maps every original repository path to its exact
Git blob, SHA-256, byte count and destination. The 32,734 smaller records are
retained under [source/](source/), preserving their original repository paths.
The 52 large compressed payloads are retained byte for byte in the
[pinned evidence release](https://github.com/mech-lang/benchmarks/releases/tag/mech-pr-973-evidence-9087b1f077).
Their asset names and download URLs are in the same manifest.

Run the complete byte verification from a benchmarks checkout:

```sh
python3 archive/compiler/mech-pr-973-9087b1f077/verify.py \
  --asset-dir /tmp/mech-pr973-evidence --download
```

Omit `--download` to verify an existing asset directory without network access.
Verification checks all original Git blob identities as well as SHA-256 and sizes;
it does not compile a candidate or run a benchmark.

Historical source pins, measurements, failures, timing boundaries and adverse
results remain attached to their original revisions. This migration makes no
new performance or completed-CI claim. Recorded relative paths and host paths
remain historical context; replay can require the source revision above,
external SDKs and the original toolchains.

Mech retains byte-identical copies of the five small DEFLATE source-variant
helpers/inputs and the Related Post Gen program used by its regression tests,
under `hosts/gpu/tests/fixtures/native/`. Normal correctness tests need no
download from this archive.
