# Exact archived evidence intake

The first preparation stopped before creating a plan or run directory. The
retained link receipt refers to 31 historical JSON, stdout and stderr files
whose original absolute names are absent. Each file is preserved byte-for-byte
at the corresponding path in the repository migration index.

[metadata-relocation-evidence-v1.json](metadata-relocation-evidence-v1.json)
records the exact old name, archived name, historical SHA-256, byte count and
migration row for each file. The 31 files total 5,808,846 bytes. This mapping
does not change historical receipts or restore files into the old checkout.

[julia_native_inspection_metadata.py](../../../tools/qualification/julia_native_inspection_metadata.py)
loads the exact frozen `julia_native_inspection.py` implementation and changes
only metadata intake, plan identity and final adapter identification. Its
original main function continues to own the common mutex, eleven sequential
commands, resource limits, process supervision and final artifact closure.
The adapter permits no relocation beyond the 31 manifest entries. Every old
name must remain absent; every archived target must be a physical regular file
with the exact historical digest. The original link receipt and migration row
must agree with each mapping. These conditions are rechecked around input
verification, including between captures and at finalization.

The prepared plan binds the original controller, adapter, manifest, migration
index and all resolved metadata files, and explicitly lists the historical
evidence mappings. Its controller field identifies the adapter. The final
report keeps the frozen implementation's controller digest and separately
identifies the entry adapter and mapping manifest. LLVM executables, libraries,
bitcode, object archive and final executable retain their original physical
paths and exact hashes. There is no general missing-file fallback.

After source review, preparation uses the same fresh destinations:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  /private/tmp/mech-benchmark-completion/tools/qualification/julia_native_inspection_metadata.py prepare \
  --plan /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/plan-v1.json \
  --output /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/run-v1
```

Execution requires independent review of the actual plan and uses the same
adapter with `run --plan <absolute-plan-path> --plan-sha256 <reviewed-digest>`.
No retry preparation or native capture has been performed with this adapter.
All native ownership, fallback, IR-removal, AOT and chart gates remain false.
The focused tests use temporary metadata and fake inspector functions only;
they start no LLVM, Julia or benchmark process.
