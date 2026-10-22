# Native Mech logical source owners

Three exact Mech pi-digits source forms are qualified under
`logical-source-owners.mech-v1-definitions-bindings`. The count comes from the
lossless native Mech concrete syntax tree, not rows or a regular-expression lexer.
The input programs are parsed without evaluation, lowering, macro expansion or
execution. Native capture uses compiler source checkpoint
`6de19875e2266f39c93712800c400672a44b98c9`.

| Exact source form | Function definitions | Written bindings | Type definitions | Logical units |
|---|---:|---:|---:|---:|
| Parent | 11 | 26 | 1 | 38 |
| Shared numerator | 11 | 27 | 1 | 39 |
| Compact shared numerator | 10 | 26 | 1 | 37 |

The [runtime study](../../mech/pidigits-performance-v1/RESULTS.md) retains its
original frozen source-measure status. This packet adds the separate logical
qualification afterward; it does not change those raw measurements or claim
canonical formatted LOC. The native-owned count coincides with physical rows for
these three files, but the fixtures establish that row wrapping does not define
the count. The [qualification](qualification.json) retains every owner's byte
range, significant native token count and exact source/capture hashes.

## Policy and limits

A written function, type definition or independent binding owns one logical unit.
A block function also contains its separately written body bindings. A pure
expression function owns one definition. Function parameters, kind annotations,
record fields, matrix rows, nested calls, comprehensions and expression matches
do not invent statements or scalar loops. Grouping punctuation, terminators,
comments and whitespace add no units. Each significant native token belongs to
its nearest written owner; no token may be silently discarded or left unowned.

The exact-source policy accepts only the qualified definition/binding statement
subset. It rejects native parser diagnostics, unowned significant expressions,
unsupported statement kinds and unqualified FSM/loop owners. This is not a
whole-language certificate. Extending it requires additional fixtures and source
review. The independent expected breakdown above is checked separately from the
owner walk.

Eighteen handwritten fixtures cover nested calls, expression/block functions,
multiple bindings, type definitions, comments, strings containing binding-like
text, Unicode byte positions, comprehensions and expression matches. Equivalent
2D matrices with semicolon-separated or physically wrapped rows both count one;
flat and multiline spellings of a block function both count its definition and
its one body binding. Invalid syntax and an unowned top-level expression are
expected rejections. A missing-token corruption is also rejected during replay.

All **21 native helper executions** finished successfully and their process
groups were closed and reaped. They inherit the existing shared benchmark mutex;
no benchmark timing is recorded by this packet. Captures are retained as complete
lossless native trees including token text and original UTF-8 byte positions.

## Reproduction

Prepare the pinned Mech compiler checkout at
`/private/tmp/mech-pidigits-performance`, as recorded by the runtime study. The
helper's Cargo manifest pins that local source boundary; `helper/Cargo.lock`
records dependency versions. Build it with:

```sh
cargo build --release --offline --locked \
  --manifest-path experiments/source-normalization/mech-v1/helper/Cargo.toml \
  --target-dir experiments/source-normalization/mech-v1/.build/target
```

In clean native output directories, run `capture.py` and `capture_fixtures.py`.
For an offline replay of the retained captures, run:

```sh
python3 experiments/source-normalization/mech-v1/qualify.py
```

`owners.py` is the versioned owner policy; `fixtures.json` contains the manual
expectations. The native helper uses the official Mech parser's retained-document
API and checks that its complete syntax text equals the original input bytes.
Local helper/policy authoring used Codex GPT-6 family; the exact serving model is
not independently established. These diagnostic helpers are not application
source or dependencies of a timed executable.
