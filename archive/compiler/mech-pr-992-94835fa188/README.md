# Mech PR 992 compact Object checkpoint

This directory preserves the remaining benchmark-only commit from
[mech-lang/mech#992](https://github.com/mech-lang/mech/pull/992),
[`94835fa1882d77d9897be88b3fedf2b1988cd464`](https://github.com/mech-lang/mech/commit/94835fa1882d77d9897be88b3fedf2b1988cd464).
Its compiler ancestors are already incorporated in Mech PR 973. The remaining
commit changes five recipe, reconstruction and metadata files; it adds no
compiler implementation change.

The complete compact-size directory is retained under [source/](source/):
**14 files, 2,901,812 bytes**, each with its original Git blob identity.
[manifest.json](manifest.json) records every original path, blob, SHA-256 and
size, and identifies the five files changed since `b2729eb666`.
The earlier [PR 973 snapshot](../mech-pr-973-9087b1f077/) remains unchanged.

Verify the archive and every fixture digest used by the recipe:

```sh
python3 archive/compiler/mech-pr-992-94835fa188/verify.py
```

The preserved recipe targets Apple ARM64 and requires LLVM **22.1.8**. Its
pinned prepared inputs allow reconstruction without building the compiler:

```sh
python3 -B archive/compiler/mech-pr-992-94835fa188/source/benchmarks/mech-deflate/native-profile/compact-size/rebuild.py \
  /tmp/mech-pr992-object --llvm-bin /path/to/llvm-22.1.8/bin
```

The original README and metadata retain their historical measurements and
source references. This archive makes no new performance claim and does not
claim a fresh Object rebuild or timing run.
