# PR 995 final benchmark checkpoint

PR 995 received another record-only commit while its archive was being prepared.
This overlay preserves all ten changed or added files at `32259dc9b45d64aabd5e1ee602165e27f168a510`, including the complete-build trials and parser-repair qualification. Its **4,438,580 original bytes** retain their exact Git blobs, SHA-256 and modes.

The [base snapshot](../mech-pr-995-be392dedfe/) plus this overlay reconstruct the latest original benchmark tree. Verify both snapshots; apply their `--restore-dir` operations to the same external directory, base first.

```sh
python3 -B archive/compiler/mech-pr-995-32259dc9b4/verify.py --asset-dir /tmp/mech-pr993-pr995-evidence --download
```

Original qualifications remain unchanged. This migration makes no new measurement or completed-CI claim.
