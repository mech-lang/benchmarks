# Retained compact tree capture

The first single-entry observer stopped after one native process because a VM
diagnostic preceded the exact prescribed subject output. The
[report](../single-entry-work-v1/run-v1/report.json) and
[terminal](../single-entry-work-v1/run-v1/terminal.json) remain failed. This
additive review does not change those artifacts or rerun the compact tree.

The [process receipt](../single-entry-work-v1/run-v1/kotlin-binarytrees-compact/process.json)
records PID/PGID 23661, parent 23659, start 2026-10-14 08:07:43.931736 UTC,
finish 08:07:45.722181 UTC, native exit zero, direct-child reaping and an empty
remaining group. No stop signal or cleanup error is recorded. Its observed peak
group RSS was 1,324,515,328 bytes, within the 10 GiB observer policy. The
[durable terminal](../dispatch-v1/owned-jobs/single-entry-four-v1/terminal.json)
records controller exit one at 08:07:46.785784 UTC, no automatic retry and no
qualification grant. These diagnostic elapsed values are not benchmark samples.

The retained [stdout](../single-entry-work-v1/run-v1/kotlin-binarytrees-compact/stdout.bin)
is exactly 506 bytes: this 51-byte diagnostic followed by the complete 455-byte
[expected output](../single-entry-work-v1/run-v1/kotlin-binarytrees-compact/expected.stdout):

```text
[0.023s][warning][os] Loading hsdis library failed
```

The complete raw SHA is
`0f9613f0fe74e0c926c46ff1951ba907639333c5a07401d7d5cd3ea23b7b4533`;
the complete subject-output SHA is
`341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1`.
The additive controller accepts only that exact concatenation. It does not
remove arbitrary warning lines or alter the original raw stream. Stderr is empty.

## Native capture reconstruction

The [saved HotSpot XML](../single-entry-work-v1/run-v1/kotlin-binarytrees-compact/hotspot.xml)
contains complete machine bytes despite the missing optional disassembler.
The original byte-row regular expression allowed newline whitespace between
hex groups and consumed the next row's indentation. The additive parser reads
one physical row at a time, preserves address/overlap checks and reconstructs
every byte in each nmethod's advertised main-code range.

| Compile ID | Method | Entry | Complete main-code bytes |
| --- | --- | --- | --- |
| 79 | tree | C1 normal | 1096 |
| 81 | tree | C2 normal | 2280 |
| 84 | check | C1 normal | 2392 |
| 88 | check | C2 normal | 448 |
| 126 | main | C1 OSR at BCI 81 | 13264 |
| 127 | main | C1 normal | 12992 |
| 128 | main | C2 OSR at BCI 81 | 3480 |
| 157 | main | C1 OSR at BCI 81 | 18832 |
| 158 | main | C2 OSR at BCI 81 | 3848 |

Each capture has OopMaps. There is no C2 normal-entry main in this invocation,
and no `Node` elimination record in any compilation task. This alone would not
prove allocation or lifetime; the following instruction evidence is additional.

## Allocation and root evidence

Source and bytecode locations are enumerated in the
[earlier tree/pi review](../compiled-work-v1/single-entry-review.md). Relevant
addresses below refer to the saved XML, whose physical lines are stable.

* C2 tree 81, lines 534–540: at `0x1180442ec` the fast path loads the thread's
  allocation top, compares top plus 24 with the allocation end, advances the
  top and initializes a `Node` object. The zero-depth branch reaches the
  separate leaf allocation at `0x11804462c` (lines 609–616). The internal paths
  allocate the root and the two inlined children; the deeper descendants use
  recursive calls. Capacity failures branch to the annotated `C2 Runtime
  new_instance` paths, rather than omitting allocation.
* Tree 81 calls at `0x11804437c` and `0x118044394` (lines 545–565) branch to
  the same tree entry with decremented depth. Their OopMaps retain the root,
  in-progress child and first completed subtree in stack slots `[0]`, `[16]`
  and then `[24]`. Child-pointer stores and G1 barriers follow; the analogous
  right-child calls at `0x118044470`/`0x118044488` retain the same objects plus
  `rfp`. The leaf path initializes the child fields to zero.
* Main C1 126 stores the long-lived tree result in stack slot `[456]` before
  the short-tree loop (`0x1105896a4`, lines 2166–2170). That slot is an Oop
  at the short-tree constructor, checker and loop poll (lines 2174–2205).
  The final-check path reloads it and passes it to `check@140` (lines 2270–2287).
* Main C2 128 imports the existing long-lived Node in `x24` at OSR entry
  (lines 6994–7001), checks its class and retains it as `rlocals` in loop-poll
  maps (lines 7006–7039). Its call spills carry the root in stack slot `[16]`.
  Its short-tree fast paths contain explicit Node allocation and child stores;
  fallback calls at `0x118047f20`, `0x118047f68`, `0x118047fb4`,
  `0x1180483d4`, `0x118048420` and `0x118048444` retain the root as an Oop.
* Main C2 158 imports the existing Node in `x25`, checks its class and moves
  it to `x13` (`0x118049ef4` through `0x118049f6c`, lines 11239–11250).
  Inner-loop polls map `r13` (lines 11303–11310); call spills preserve it in
  `[16]` or `[32]`, with matching OopMaps. Across outer-loop output, it is
  retained in `[8]` (lines 11648–11669). The terminal path reloads `[8]` into
  the checker argument at `0x11804a804` before `check@140` at `0x11804a808`
  (lines 11672–11678). The root can cease to be live after that final use.

Both C2 OSR versions were actually entered: the XML records a runtime
`unstable_if` trap from compile 128 at 0.412 seconds (lines 7406–7409) and an
`uninitialized` trap from compile 158 at 1.752 seconds, after the final check
(lines 11982–11985). Main's invocation count is one in the installed records
at lines 6964 and 11212. Thus the repeatedly warmed normal-entry C2 allocation
eliminations in the earlier witness are not attributed to this fresh invocation.

These retained paths provide concrete allocation and long-lived-root evidence
for the compact single-entry tree. They do not transfer a runtime compilation
claim to the unobserved alias or establish pi's two-division execution contract.
The additive machine-readable capture keeps work/timing/admission flags false;
the remaining three captures and their semantic review must supply those facts.
No elapsed diagnostic value is admitted to the timing dataset.

The new plan binds the original plan SHA
`363f5a7af8a10e0dc93b88e3da3d371872ae0737e91d8f2a4591889d8885e88d`,
report SHA `5918aed5d40abb86e1c647dcad9e3664062be762f47a63d1e4d59d0730c52aea`,
terminal SHA `e69e7f55f8ae63dfd6f516b82256625fd13cd8c53e9e359d5cef943266260097`
and durable SHA `e550b132232a4fdb5cf87c46516a2444f267ff8faeb40dc8f7f8e52cf39a6814`.
Preparation must revalidate their complete closure under the common mutex;
the source-only preparation of this note does not repeat that verification.
