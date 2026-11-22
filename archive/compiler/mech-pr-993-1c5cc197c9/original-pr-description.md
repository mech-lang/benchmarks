# Original Mech PR #993 description

Preserved before benchmark relocation. Measurements and source references below are historical and retain their original qualifications.

Stacked on #994 (`codex/v04-option-set-table-fixes`). Stack order: #973 → #975 → #994 → #993 → #995.

## Source catalog overlap

The matched M1 build takes **2.427 s** through final link with the
same encoder and executable. Overlap saves **60.88 ms**
in the same compiler. The direct frame-copy build uses the measured recipe. [Build and evidence](https://github.com/mech-lang/mech/blob/c2e1b803d82401d28c2aa15dad875bfbfd3e492b/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/inline-syntax-child-traversal/catalog/README.md)

---

## Scorer cost length

The experimental 71,128 B encoder removes 43,020 scorer stack loads
on natural 8 KiB. It keeps both overlap wins. Natural 8 KiB is
**0.99426× libdeflate forward and 1.00101× reverse**, so the candidate
remains experimental. [Patch and paired measurements](https://github.com/mech-lang/mech/blob/cbcc3a803e59d506bb3d582f885e332e71ee1f53/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scorer-admitted-cost-length/README.md)

---

## Scalar entry literals

A paired **40.63 ms** saving brings the matched M1 build to **2.495 s** from source through final link.
The 90% interval is **33.08 to 47.17 ms**.
The frame-copy recipe uses this path. Linked checks cover 162 successes and six failure probes.
The recorded full benchmark holds 81/81 Roc and 61/81 libdeflate in both orders.

[Current scorecard](https://github.com/mech-lang/mech/blob/8c7cec1199fa1348e364c2052d9ec82b0934754e/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md) · [Compiler evidence](https://github.com/mech-lang/mech/blob/8c7cec1199fa1348e364c2052d9ec82b0934754e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/immutable-root-literals/README.md)

---

## Short scorer visits

The scalar pair and earlier vector entry probes preserve strict winner order
and the current checked root. The 71,192 B frame-copy encoder remains the maintained build. The next runtime mechanism is the repeated bound reload.
[Matched runtime results and source patch](https://github.com/mech-lang/mech/blob/ed99ade92836761bebd2f7357bf46817204433d4/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ordered-scorer-short-visits/README.md)

The pinned workspace formatter passes. The compiler probe reproduces
the emitted artifacts and times source semantics and catalog construction,
with a separate SSA occupancy and root-lane census.
[Compiler attribution](https://github.com/mech-lang/mech/blob/ed99ade92836761bebd2f7357bf46817204433d4/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/source-and-ssa-attribution/README.md) ·
[Formatting and contract checks](https://github.com/mech-lang/mech/blob/ed99ade92836761bebd2f7357bf46817204433d4/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/pinned-formatter-repair/README.md)

---

## Overlap and compiler follow-up

Raising the four-byte mapping threshold keeps the 320-byte overlap
win in both screens with less margin. Natural 8 KiB finishes above
parity in reverse. The v3 runtime floor remains 62/81 in both full orders.

The exact bottom-tested scorer repeated at **62/81 and 60/81**
against libdeflate in the complete orders. [Full repeat](https://github.com/mech-lang/mech/blob/3cde720cdf8b24d6bc4f1818988479d8eb5ae960/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/runtime-overlap-backing/root-confirmation/README.md)

Keeping single SSA definitions inline saves a paired
**5.88 ms** through final link, with a 90% interval of
**0.86 to 17.41 ms**.
It reproduces the bytecode, encoder object, metadata, and linked worker.

[Current status](https://github.com/mech-lang/mech/blob/3cde720cdf8b24d6bc4f1818988479d8eb5ae960/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md) · [Runtime backing](https://github.com/mech-lang/mech/blob/3cde720cdf8b24d6bc4f1818988479d8eb5ae960/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/runtime-overlap-backing/README.md) ·
[Compiler timings](https://github.com/mech-lang/mech/blob/3cde720cdf8b24d6bc4f1818988479d8eb5ae960/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ssa-local-definitions/README.md)

---

## Runtime qualification and scorer follow-up

New qualification campaigns use v3, with **81/81 Roc** and
**62/81 libdeflate** required in each complete order. The historical
62-win worker used LLVM. The maintained LLVM-free worker has 61 wins.
Natural 8 KiB accounts for that difference on the same frozen cases
and peer binaries. The next target is **63/81**.

The bottom-tested scorer with the original checked root emits
**71,096 B**.
The candidate wins 81/81 against Roc in both full orders.
It wins **62/81 and 61/81 against libdeflate**, with natural 8 KiB at
**0.99286× and 0.99866×**.

Both workers miss `320-overlap` in reverse. This candidate remains below
the required floor across both full orders.
[Current status](https://github.com/mech-lang/mech/blob/8fb7fa9683a3034866104db196ca5a72d7d312da/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md) · [Policy v3](https://github.com/mech-lang/mech/blob/8fb7fa9683a3034866104db196ca5a72d7d312da/benchmarks/mech-deflate/native-profile/native-compact-20261116/QUALIFICATION.md) ·
[Historical 62-win comparison](https://github.com/mech-lang/mech/blob/8fb7fa9683a3034866104db196ca5a72d7d312da/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/runtime-62-high-water/README.md) ·
[Scorer observations](https://github.com/mech-lang/mech/blob/8fb7fa9683a3034866104db196ca5a72d7d312da/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ordered-vector-latch/README.md)

---

## Current compiler and matched final link

Sealed ASCII literal mismatches preserve the original syntax work, cache
entries and exact emitted artifacts. All 537 syntax tests passed.
The standalone saving is **28.5 ms**. The
matched source-through-final-link saving is **29.3 ms**.
The source change is selected. The measured shortcut compiler builds in
**0.850× Roc** and **5.290× libdeflate** time.

| Apple M1 | Through final link | Through strip |
| --- | ---: | ---: |
| Immediate reference | 2.57145 s | 2.58230 s |
| Mech | 2.54104 s | 2.55172 s |
| Roc | 2.98847 s | 2.99894 s |
| libdeflate | 0.48068 s | 0.49114 s |

Direct scorer address arguments emit **71,000 B** with 5,296 B measured peak
stack. Both scalar branch variants lost peer wins in the focused screens.
The qualified runtime worker uses 71,192 B of encoder text. The next runtime
floor remains 81/81 Roc and 62/81 against libdeflate in both full orders.

[Current status](https://github.com/mech-lang/mech/blob/b05241855264df7df861994ef125e5dfb678bc81/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md) · [Fresh matched builds](https://github.com/mech-lang/mech/blob/b05241855264df7df861994ef125e5dfb678bc81/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/sealed-ascii-literal-miss/README.md) ·
[Scorer results and replay](https://github.com/mech-lang/mech/blob/b05241855264df7df861994ef125e5dfb678bc81/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ordered-scorer-visit-costs/README.md)

---

## Checked scorer runtime and encoder size

A caller-address and layout experiment emits **71,048 B** of encoder text,
**144 B smaller** than the selected frame-copy worker. Its full runtime
wins are **81/62** forward and
**81/61** reverse against Roc and libdeflate
respectively. It passes 162 exact output checks and all six checked failures.
The candidate's measured stack reaches **5,296 B**, 16 B above the
predeclared stack nonregression limit. Deployment continues to use the
qualified 71,192 B frame-copy worker. A second 71,048 B experiment
stays at 5,280 B stack and lands just above parity on the 8 KiB case.

The next release floor is **81/81 Roc and 62/81 libdeflate** in both full
orders. Natural 4 KiB is the next loss after the 8 KiB case, and its
phase profile marks the path toward 63/81.

[Complete evidence and reproducible patch](https://github.com/mech-lang/mech/blob/d03f097b06c8386822a8063de9826715a9c1e897/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/caller-address-scorer/README.md)

---

## Earlier native verification-reuse measurements

The adjacent cleanup uses already-verified control flow across constant-phi
edits and freshly computed graphs after a prune that removes no blocks.
The confirmation saves **33.8 ms** through final linking.

| Apple M1 | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.57808 s | 2.99395 s | 0.48620 s |
| Source through strip | 2.58878 s | 3.00439 s | 0.49685 s |
| Encoder text | 71,192 B | 57,696 B | 37,080 B |
| Stripped executable | 292,568 B | 191,912 B | 155,752 B |

Mech builds in **0.861× Roc** and **5.297×
libdeflate** time. The same worker retains **81/81 Roc** and **61/81
libdeflate** runtime wins in both full orders. The 62-win threshold remains
open.

[Compiler source](https://github.com/mech-lang/mech/commit/204656da92013ce24dabb115685a75fc930c7c46)
· [Current scorecard](https://github.com/mech-lang/mech/blob/176a80bde45bdc0c137ddd797e5961c42f23d56c/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Both timing series, graph census and next measured targets](https://github.com/mech-lang/mech/blob/176a80bde45bdc0c137ddd797e5961c42f23d56c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/verified-flowgraphs/README.md)

---

## Earlier build with ASCII grapheme scanning

Sealed ASCII grapheme scanning saves a paired **98.5 ms**
through the final link in eight balanced orders. Bytecode, native object,
metadata and the qualified worker reproduce exactly. Both full runtime
orders for that worker record **81/81 Roc** and **61/81 libdeflate**.

| Measurement | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.59466 s | 2.97795 s | 0.48074 s |
| Source through strip | 2.60531 s | 2.98852 s | 0.49123 s |
| Encoder text | 71,192 B | 57,696 B | 37,080 B |
| Stripped executable used in timing | 292,568 B | 191,912 B | 155,752 B |

Mech builds in **0.870× Roc** and **5.405× libdeflate**
time. The working budget is **0.45 s** through the final link.

[Compiler source](https://github.com/mech-lang/mech/commit/c93ed0e1a726ff7f64164533593349f04fdfa12c)
· [Current scorecard and whole-build budget](https://github.com/mech-lang/mech/blob/f96c1d4fdbc2db1f98c84b561a37132d0a7b5961/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Matched timings and scanner ablation](https://github.com/mech-lang/mech/blob/f96c1d4fdbc2db1f98c84b561a37132d0a7b5961/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/sealed-ascii-graphemes/README.md)
· [Native trace and selected experiment](https://github.com/mech-lang/mech/blob/f96c1d4fdbc2db1f98c84b561a37132d0a7b5961/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-pass-attribution/README.md)

---

## Earlier build omitting unused failure returns

The compiler omits 5,236 unused failure returns during checked-root SSA
construction. The paired ablation reduces native time from **1.426 s
to 1.418 s** while reproducing all reference artifacts.

| Apple M1 | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.70063 s | 2.98958 s | 0.48058 s |
| Source through strip | 2.71108 s | 3.00001 s | 0.49107 s |
| Encoder text | 71,192 B | 57,696 B | 37,080 B |
| Stripped executable used in timing | 292,568 B | 191,912 B | 155,752 B |

Mech takes **0.903× Roc** and **5.621× libdeflate**
through the common deployment link. Encoder text is **1.920×
libdeflate**. The 71,192 B worker records forward 81/61, reverse 81/61 in the two full orders against Roc/libdeflate. Policy v2 records **Retain**
for the frame-copy candidate.

[Compiler source](https://github.com/mech-lang/mech/commit/033d17ce9cfd66b185e8fc45655575a971a86af9)
· [Current scorecard](https://github.com/mech-lang/mech/blob/7a0b3127ce2ec163d3989f706b7ab819901ec0c2/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Matched builds and ablation](https://github.com/mech-lang/mech/blob/7a0b3127ce2ec163d3989f706b7ab819901ec0c2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/unused-failure-returns/README.md)
· [Runtime proofs](https://github.com/mech-lang/mech/blob/7a0b3127ce2ec163d3989f706b7ab819901ec0c2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/frame-copy-v2/README.md)
· [Parser phase responsibilities](https://github.com/mech-lang/mech/blob/7a0b3127ce2ec163d3989f706b7ab819901ec0c2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/post-statement-parser-profile/README.md)

---

## Earlier build with statement replay

Statement replay reduces matched Apple M1 source-through-link time by
**3.67%**. The compiler takes
**0.906× Roc** and **5.644× libdeflate** from source
through the same deployment link, with prebuilt compilers and host support.

| Apple M1 | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.70927 s | 2.98501 s | 0.47997 s |
| Source through strip | 2.71974 s | 2.99558 s | 0.49037 s |
| Encoder text | 71,768 B | 57,696 B | 37,080 B |
| Stripped deployment file | 292,576 B | 191,920 B | 155,760 B |

Four separate phase captures give **0.918 s for
Mech** and **3 ms for Roc**, about
**306×** across the reported intervals. Mech
builds the lossless syntax tree and indexes. Roc sums tokenization and
parsing with one compilation job and its cache disabled.

The compiler reproduces the bytecode, encoder object, complete metadata and
benchmark worker byte for byte. All 535 existing syntax tests, three
focused checks and 162 exact linked calls pass.
[Compiler source](https://github.com/mech-lang/mech/commit/ac485d5a93e632eeff8d5e32bdee3233189e12bb)
· [Current scorecard](https://github.com/mech-lang/mech/blob/e8b2bb4f2d8c44390e9a67dfe054c6ff40341249/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Matched builds and parser captures](https://github.com/mech-lang/mech/blob/e8b2bb4f2d8c44390e9a67dfe054c6ff40341249/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scoped-statement-replay/README.md)

On the fixed reference encoder, the lower halfword mapping threshold
raises the 1 KiB periodic call from **44 µs to 63 µs** and loses four
libdeflate wins in both focused orders. The variant was rejected.
[Runtime backing profile and replay](https://github.com/mech-lang/mech/blob/e8b2bb4f2d8c44390e9a67dfe054c6ff40341249/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/halfword-zero-page-screen/README.md)

---

## Previous build with adjacent verifier reuse

Mech compiles the encoder through the deployment link in **2.80251 s** on
Apple M1. Adjacent cleanup now reuses verification when constant-phi removal
makes no edits. Native time falls from **1.46444 s to 1.42450 s**, and paired
complete build time falls **1.40%**. Mech is **0.941× Roc** and **5.842×
libdeflate** for the same build boundary with prebuilt compilers and support.

| Apple M1 | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.80251 s | 2.98347 s | 0.47961 s |
| Source through strip | 2.81307 s | 2.99371 s | 0.49005 s |
| Encoder text | 71,768 B | 57,696 B | 37,080 B |
| Stripped deployment file | 292,576 B | 191,920 B | 155,760 B |

Four separate phase captures give **1.020 s for Mech** and **3 ms for Roc**,
about **340×** across the reported intervals. Mech's timer covers its
lossless syntax tree and indexes. Roc sums tokenization and parsing with one
compilation job. Each profiler run reproduced the expected artifacts.
[Parser phase observations](https://github.com/mech-lang/mech/blob/61f012dd1233e746ec199f1d43ea4584ed172737/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/phi-verifier-reuse/parser-phases/README.md)

The new compiler reproduces the exact bytecode, encoder, metadata and runtime
worker. Both focused verifier checks and 162 exact linked calls pass.
[Compiler source](https://github.com/mech-lang/mech/commit/fcb818e6420828a19cf019023f0f765a938c351e)
· [Current scorecard](https://github.com/mech-lang/mech/blob/9abacf0cc5e380cc66c931538f5eacc2f7a46156/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Complete matched builds](https://github.com/mech-lang/mech/blob/61f012dd1233e746ec199f1d43ea4584ed172737/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/phi-verifier-reuse/README.md)

The checked byte-read outline emits **71,420 B**, 332 B below its
unpadded control. The prior comparative runtime counts are withdrawn.
Both earlier workers linked the reference encoder. Corrected worker
bindings match 162 exact output and resource observations and six
checked allocation failures. Peak stack is **5,328 B** for the outline
and **5,280 B** for the reference. The outline exceeds the original
campaign's stack limit by 48 B. Runtime qualification is pending.
[Corrected worker bindings and measurements](https://github.com/mech-lang/mech/blob/9abacf0cc5e380cc66c931538f5eacc2f7a46156/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/checked-byte-read-regions/README.md)

---

## Earlier matched build with function-definition replay

Mech now takes **2.84147 s from source through final link** on Apple M1,
down from **3.13523 s** in this matched set. The paired improvement is
**9.39%**, with **0.951× Roc** and **5.912× libdeflate** build time.
The compilers and fixed host support are prebuilt.

| Measurement | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 2.84147 s | 2.98471 s | 0.48041 s |
| Source through strip | 2.85210 s | 2.99527 s | 0.49103 s |
| Encoder text | 71,768 B | 57,696 B | 37,080 B |
| Stripped deployment file | 292,576 B | 191,920 B | 155,760 B |

The existing structural recipe now covers the winning function definition.
Nested definitions keep their fast path once the enclosing trial has observed
its first raw access. The standalone parser takes **1.009 s**, down from
**1.305 s**. Function replay applies on all 369 measured functions, and
535 existing syntax tests plus three exact differential tests pass.

The bytecode, encoder object, metadata, and benchmark worker reproduce
exactly. The worker earns its **81/81 Roc and 61/81 libdeflate** counts from
the archived full orders. The rebuild passed 162 exact linked calls.
[Compiler source](https://github.com/mech-lang/mech/commit/e9538f71514225abf5ca57a9fc0acab358407167)
· [Current scorecard](https://github.com/mech-lang/mech/blob/d1a9ae0c3f4f8945ddd11fd3903edd6aaab089e2/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)
· [Matched measurements and replay](https://github.com/mech-lang/mech/blob/d1a9ae0c3f4f8945ddd11fd3903edd6aaab089e2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scoped-function-replay/README.md)

The checked root occupies **51,264 B** of the encoder text. A separate
native census identifies approximately **38.7 ms** of verification after
no-op constant-phi removal as an upper bound to test.
[Root symbol extents](https://github.com/mech-lang/mech/blob/d1a9ae0c3f4f8945ddd11fd3903edd6aaab089e2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scoped-function-replay/root-census.json)
· [Native verification census](https://github.com/mech-lang/mech/blob/d1a9ae0c3f4f8945ddd11fd3903edd6aaab089e2/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scoped-function-replay/native-verify/README.md)

---

## Earlier matched build with variable-definition replay

The guarded variable-definition replay brings Mech source through final
deployment link from **3.70961 s to 3.13566 s**.
Eight matched Apple M1 runs give **15.39% less paired build time**, **1.052×
Roc** and **6.530× libdeflate**. The compilers and fixed host support are
prebuilt. Parsing in those runs takes **1.315 s** and native preparation
through object generation takes **1.464 s**.

| Apple M1 | Mech | Roc | libdeflate |
| --- | ---: | ---: | ---: |
| Source through final link | 3.13566 s | 2.98380 s | 0.48054 s |
| Source through strip | 3.14623 s | 2.99426 s | 0.49110 s |
| Encoder text | 71,768 B | 57,696 B | 37,080 B |
| Stripped deployment file | 292,576 B | 191,920 B | 155,760 B |

The bytecode, encoder object, complete metadata and fixed timed worker
reproduce exactly. The fixed worker passed 162 exact calls and retains its
archived v2 runtime evidence of **81/81 Roc and 61/81 libdeflate** in each
order. The parser passes all 535 existing syntax tests and the focused
identity, finite-grant, segmented-input and nested-witness checks.
[Parser source](https://github.com/mech-lang/mech/commit/3819f8850ee17e12ed09659d22c48d9181ef4451)
· [Matched builds, phase timings and prototype checks](https://github.com/mech-lang/mech/blob/f68f93c66e14b8f227bf4a9d1df16d99a59f9b1d/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/scoped-definition-replay/README.md)
· [Current scorecard](https://github.com/mech-lang/mech/blob/ff7c1dbc9c5059ed84d730b008847c02179fa2cf/benchmarks/mech-deflate/native-profile/native-compact-20261116/CURRENT.md)

The native work breakdown shows about 692 ms in cleanup, 297 ms in semantic
preparation, and 280 ms in SSA construction. A shared immutable facts owner
reduces inventory materializations and preserves the exact emitted artifacts.
The checked scalar transport and CFG probes bound the immediate savings to a
small number of sites. The next native experiment will test omitting one more
unused phase body while preserving the existing selection and declarations.
The control-drift sentinel results are also published.
The Related Posts after-4 checked-binding prototype has static receipts and
is pending compiled validation.
[Native trace](https://github.com/mech-lang/mech/blob/f68f93c66e14b8f227bf4a9d1df16d99a59f9b1d/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-exclusive-work/README.md)
· [Scalar transport and CFG probes](https://github.com/mech-lang/mech/blob/f68f93c66e14b8f227bf4a9d1df16d99a59f9b1d/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/checked-root-work/README.md)
· [Related Posts prototype](https://github.com/mech-lang/mech/blob/f68f93c66e14b8f227bf4a9d1df16d99a59f9b1d/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/related-post-linked-binding/checked-after-4/README.md)

## Peer-win policy and earlier native comparisons

New campaigns use **policy v2**. Both full 81-case orders must meet
**81/81 Roc** and **61/81 libdeflate** and keep each individual peer win.
Candidate/control slowdowns and duplicate-control uncertainty are still
reported. The exact output, checked-error, stack and provenance checks
apply. Twenty-five validator tests pass. Archived v1 campaigns keep their
recorded evidence and decisions.
[Policy source](https://github.com/mech-lang/mech/commit/a6cb46aa8720478b947e39e90e70524dba1142c1) · [Qualification rules](https://github.com/mech-lang/mech/blob/c3761207e721ebe46113c2078eb3da9b9f2fdb6c/benchmarks/mech-deflate/native-profile/native-compact-20261116/QUALIFICATION.md#acceptance-policy-v2)

The compiler derives entry bounds for eligible private checked phases
while skipping discarded general SSA. Its maintained rebuild reproduces
the exact **71,768-byte** reference encoder and complete metadata. The
matched comparison reduces paired native time **2.25%**
and source-through-executable-link time **0.87%**.

| Apple M1 with prebuilt compilers and support | Build time | Encoder text |
| --- | ---: | ---: |
| Mech control | 3.77362 s | 71,768 B |
| Mech skipping discarded general SSA | 3.73777 s | 71,768 B |
| Roc | 2.98844 s | 57,696 B |
| libdeflate | 0.48067 s | 37,080 B |

Mech takes **1.251× Roc** and **7.776× libdeflate** build time.
The fixed link reproduces the exact worker that scored 81/81 Roc and
61/81 libdeflate in its earlier complete orders.
[Compiler source](https://github.com/mech-lang/mech/commit/7c77a620cad6854b5e69938021df2f83db2b62f7) · [Source rebuild and raw trials](https://github.com/mech-lang/mech/blob/c3761207e721ebe46113c2078eb3da9b9f2fdb6c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/refused-general-ssa/README.md)

The 71,288-byte owner-exchange worker preserves 81/81 against Roc in both
complete policy v2 orders. Both Mech workers score 61/81 against libdeflate
in forward order and 60/81 in reverse. In reverse the candidate loses the
control's 1 KiB random-data win and gains the 320-byte overlap win. The
individual loss rejects the candidate. The 71,768-byte encoder remains the
reference. [Both complete v2 orders](https://github.com/mech-lang/mech/blob/dae46c686703560230150a93f36c44c4978ffdc7/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/owner-exchange-71288-v2/README.md)

---

## Indexed event pages and earlier matched builds

Direct indexing of completed event-page groups cuts standalone parse
time by **4.08%** in six balanced pairs. All **535 syntax tests** and **60
differential snapshots** pass with identical trees, parser steps, event
counts, diagnostics and finite-limit behavior. The source keeps the
existing streaming journal and logical accounting.
[Parser source](https://github.com/mech-lang/mech/commit/df885d4b43180b5647816f03f42774e118013a41) · [Proof and raw parser trials](https://github.com/mech-lang/mech/blob/78b064c5bb70937db72db21ebd3ab2fd556816c3/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/batch-page-index/README.md)

| Matched Apple M1 | Complete source through final link | Encoder text | Executable file |
| --- | ---: | ---: | ---: |
| Mech before indexing | 3.87335 s | 71,768 B | 956,056 B |
| Mech with page index | 3.81385 s | 71,768 B | 956,056 B |
| Roc | 3.01609 s | 57,696 B | 230,600 B |
| libdeflate | 0.48388 s | 37,080 B | 210,168 B |

The change reduces paired complete build time by **1.23%**,
with **7/8** pairs faster. The new build is **1.265× Roc**
and **7.882× libdeflate**. Encoder text is **1.244× Roc** and
**1.935× libdeflate**. Every measured Mech build reproduces the same
bytecode, object, metadata and comparable executable. The fixed link
reproduces the exact 71,768-byte benchmark worker with 162 exact checks.
That worker's earlier full timing orders scored **81/81 Roc and 61/81
libdeflate** in both directions.
[Complete matched timings and compiler phases](https://github.com/mech-lang/mech/blob/78b064c5bb70937db72db21ebd3ab2fd556816c3/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/batch-page-index/matched/summary.json)

The two ordinary Mech matcher experiments have separate source diffs and
focused replayable runs. The single read of each literal saves 384 bytes
in the shared generic configuration and stays unresolved. The larger
stale-root run grows by 13,648 bytes and is rejected on runtime. The
stack-slot affinity experiment is rejected at the size screen.
[Matcher tests](https://github.com/mech-lang/mech/blob/78b064c5bb70937db72db21ebd3ab2fd556816c3/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/mech-source-matcher/README.md)
· [Allocator size screen](https://github.com/mech-lang/mech/blob/78b064c5bb70937db72db21ebd3ab2fd556816c3/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/spill-slot-affinity-screen/README.md)

---

## Full runtime results for the 71,192-byte encoder

Both complete 81-case orders replay under v1. The smaller encoder keeps
every individual control win. The result is **Reject**, with the paired
`prefix-periodic-16384` estimate **+10.468%** and 90% bounds
**[+1.723%, +19.681%]**. The exact 71,768-byte control previously scored
61/81 against libdeflate in both orders and remains the reference.

| Runtime order | Roc wins control / candidate | libdeflate wins control / candidate |
| --- | ---: | ---: |
| Forward | 81 / 81 | 57 / 57 |
| Reverse | 81 / 81 | 60 / 61 |

Both orders preserve exact compressed output, capacities and aliases.
The reverse candidate gains `reymont-prefix-16384`. The same-worker
diagnostic locates the common forward losses in four consecutive periodic
cases. The source of the elapsed-time shifts is unresolved and all blocks
remain in the validator replay.
[Full raw orders and replay](https://github.com/mech-lang/mech/blob/faf192e6cdb0fb8087f06dbc10d98c3be15ece3c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/frame-copies-71192-runtime/README.md)

The inherited architecture check stops on the related-post comparison
host's same-Object restore. The source-level binding audit is included.
[Blocking check and migration scope](https://github.com/mech-lang/mech/blob/faf192e6cdb0fb8087f06dbc10d98c3be15ece3c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/related-post-linked-binding/README.md)

---

## Source-emitted frame copies and matched build results

The opt-in frame-copies recipe shares identical AArch64 stack moves into
a common continuation. It emits **71,192 B**, 576 B smaller than the
71,768-byte control and **1.234× Roc** and **1.920× libdeflate**.
The fixed link reproduces the focused benchmark worker byte for byte.
The separate metadata hashes describe identical JSON values. All 13
selected backend tests passed.
[Compiler source](https://github.com/mech-lang/mech/commit/fa27c2c4c7595db6337497a2a00c6fd3869063d3) · [Recipe, identity and raw results](https://github.com/mech-lang/mech/blob/b72b7419b39b22765fe1eed6b5c636e63964b905/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/shared-copy-tails/README.md)

| Matched Apple M1 | Source through final link | Encoder text |
| --- | ---: | ---: |
| Mech full-suite control | 3.82900 s | 71,768 B |
| Mech frame copies | 3.82835 s | 71,192 B |
| Roc | 2.98408 s | 57,696 B |
| libdeflate | 0.47948 s | 37,080 B |

The two Mech layouts are effectively level in build time. The smaller
layout takes **1.283× Roc** and **7.984× libdeflate** time.
A separate matched compiler campaign removed repeated CFG construction
and stopped-path searches, cutting native emission **1.71%** and
source through final link **0.50%**. That campaign reproduced the exact
71,768-byte worker and its two full **81/81 Roc and 61/81 libdeflate** orders.
[Compiler change](https://github.com/mech-lang/mech/commit/51b21b2d4fb3591845e65cbf95880d4c2f848aea) · [Independent and combined compiler trials](https://github.com/mech-lang/mech/blob/b72b7419b39b22765fe1eed6b5c636e63964b905/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-graph-work/README.md)

The frame-copy variant preserves every individual win in both focused
orders at **17/17 Roc and 13/17 libdeflate**. It passes exact output,
checked failure and stack comparisons. The 4 KiB random duplicate-control
follow-up bounds the candidate at +0.093%, while the adverse reverse
order keeps the v1 result **Unresolved**. Full-suite floors refer to the
71,768-byte control.
[Focused and duplicate-control replay](https://github.com/mech-lang/mech/blob/b72b7419b39b22765fe1eed6b5c636e63964b905/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/shared-copy-tails/repeatability/combined-replay.json)

The clock calibration and the smaller rejected scorer experiment have
their own raw receipts and exact artifact identities.
[Clock calibration](https://github.com/mech-lang/mech/blob/b72b7419b39b22765fe1eed6b5c636e63964b905/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/batched-clock-calibration/README.md) · [Scorer experiment](https://github.com/mech-lang/mech/blob/b72b7419b39b22765fe1eed6b5c636e63964b905/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ordered-scorer-addresses/README.md)

---

## Latest compiler source and matched Apple M1 results

Single-piece source access reduced the Mech build from **4.03290 s to
3.93889 s** through the final executable link, a **2.23%**
paired median improvement across eight orders. Each compiler, fixed
runtime, and adapter was prebuilt. The new compiler reproduces exact Mech
bytecode, encoder object, complete metadata, executable, and timing worker.
All 534 syntax tests and 60 differential snapshots passed.
[Compiler source](https://github.com/mech-lang/mech/commit/480b24d24acf5af2f63215b2fccfa8c4c5282e91) · [Matched builds and reproduction](https://github.com/mech-lang/mech/blob/197ad8ff1272a9f411bd56f14f08efabba2553cd/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/contiguous-syntax-source/README.md)

| Apple M1 | Build through final link | Encoder text |
| --- | ---: | ---: |
| Mech diagnostic recipe | 3.93889 s | 71,768 B |
| Roc | 3.04136 s | 57,696 B |
| libdeflate | 0.48541 s | 37,080 B |

Time is **1.295× Roc** and **8.115× libdeflate**.
Encoder text is **1.244× Roc** and **1.935× libdeflate**. Both fresh full
runtime orders preserved every individual win at **81/81 Roc and 61/81
libdeflate**. Eighty cases meet the 0.5% regression bound. Duplicate
controls still exceed that resolution on seven-stored-prefix.
[Full runtime replay](https://github.com/mech-lang/mech/blob/197ad8ff1272a9f411bd56f14f08efabba2553cd/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/bound-71768-runtime/README.md)

The 71,256-byte prototype with packed cold origins and one fewer owner-count
write preserved all focused wins. It slowed empty input by 2.375% and
the focused replay rejected it.
[Size experiment](https://github.com/mech-lang/mech/blob/197ad8ff1272a9f411bd56f14f08efabba2553cd/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/terminal-owner-publication/README.md)

The allocator probe now uses owned aligned blocks. Both original receipt
hashes still verify. The local full-tree architecture gate reaches the
inherited linked-module restore after this repair.
[Integration repair](https://github.com/mech-lang/mech/blob/197ad8ff1272a9f411bd56f14f08efabba2553cd/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/allocator-probe-audit/README.md)

---

## Reusable parser cache frames

The matched Apple M1 source-through-link build improved from 4.01608 s to
3.95160 s, a 1.60% paired median reduction. It measured 1.323× Roc and
8.223× libdeflate. The compiler reproduces the same 71,768-byte encoder,
metadata and exact benchmark worker. Both recorded full runtime orders
were 81/81 Roc and 61/81 libdeflate. All 533 syntax unit tests passed.
[Compiler change](https://github.com/mech-lang/mech/commit/e722b71013d6511ff124ee18eeec190157f7910b)
· [Matched builds, tests and reproduction](https://github.com/mech-lang/mech/blob/d5bd13ddd3f5dfd97ee6118171c8674a511c04d0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-cache-frames/README.md)

The 71,256-byte cold-origin table prototype preserves every measured win
in both 16-case orders. Standard placement failed the empty-input resolution
and equal stub/constant section placement remains unresolved. Both screens
and the exact object reproduction are available for review.
[Size experiment](https://github.com/mech-lang/mech/blob/d5bd13ddd3f5dfd97ee6118171c8674a511c04d0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/cold-origin-tables/README.md)
· [Current integration CI](https://github.com/mech-lang/mech/actions/runs/44066015097)

## Ordered scoring vector address screen

The cursor variant emits 71,832 bytes and preserved all focused peer wins.
On 8 KiB natural text, the scorer executed 164,742 fewer instructions and
43,020 additional stack reloads. Runtime remained about 1.04× libdeflate.
The empty-input case regressed by 2.01%, and the validator rejected the variant.
[Compiler patch, replay, and reproducible artifacts](https://github.com/mech-lang/mech/blob/dfdcdb3c1afcbeeb768efa1c8978ce85bb82d894/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/ordered-vector-cursors/README.md)

The 71,768-byte opt-in build has the published full 81/81 Roc and 61/81
libdeflate scores and builds from source through final link in 4.00611 s on
Apple M1. Earlier receipt bindings keep its qualification unresolved.
[Matched full evidence](https://github.com/mech-lang/mech/blob/dfdcdb3c1afcbeeb768efa1c8978ce85bb82d894/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/branch-on-zero/README.md)
· [Current integration CI](https://github.com/mech-lang/mech/actions/runs/44059712343)

## Historical runtime reproduction

The optional worker rebuild now verifies the three original runtime source hashes
from PR #993's pinned ancestor. Relinking with the fixed support and the historical
source locations reproduced the exact aligned benchmark worker. Its previously
published performance measurements apply to that worker identity.
[Reproduction receipt](https://github.com/mech-lang/mech/blob/ea519762d503a7a3d95e33dd36838f04dae297e0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/recorded-runtime-provenance/identity.json)

The static audit checker remains intact. After removing the redundant archive
from the live tree, the local audit reports an inherited allocator test in
`benchmarks/related-post-gen/check-measurement.rs`.
[Audit evidence](https://github.com/mech-lang/mech/blob/ea519762d503a7a3d95e33dd36838f04dae297e0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/recorded-runtime-provenance/README.md)
· [Current integration CI](https://github.com/mech-lang/mech/actions/runs/44056453638)

## AArch64 zero-comparison branches

The compact checked root uses one AArch64 instruction for the supported native-width zero comparisons followed by a branch. The measured layout saves **192 encoder text bytes**, reaching **71,768 B**, **1.244× Roc** and **1.935× libdeflate**. Measured peak native stack drops from **5,296 to 5,280 B**. The maintained rebuild reproduces the exact timed worker. [Source change](https://github.com/mech-lang/mech/commit/c6f7425eb27284c58a77bc40bc26200e66b414c1) · [Rebuild and artifact identities](https://github.com/mech-lang/mech/blob/83e93aefb52bf4bbe1dd90ce8387dd5d77bd731c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/branch-on-zero/README.md)

Both complete timing orders preserve every individual win at **81/81 Roc and 61/81 libdeflate**. All 81 cases meet the per-case 0.5% resolution after the duplicate-control follow-up. The variant stays opt-in. The replay preserves the provenance findings on earlier diagnostic runs. **209 Cranelift tests** and the checked-failure and alias probes pass. [Both full orders and repeatability results](https://github.com/mech-lang/mech/blob/83e93aefb52bf4bbe1dd90ce8387dd5d77bd731c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/branch-on-zero/aligned-full-replay.json)

Eight balanced Apple M1 orders measure **4.013 s → 4.006 s** through final link with compilers, fixed runtimes and adapters prebuilt. The smaller build takes **1.345× Roc** and **8.357× libdeflate** time. [Sizes and raw build comparison](https://github.com/mech-lang/mech/blob/83e93aefb52bf4bbe1dd90ce8387dd5d77bd731c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/branch-on-zero/report.json) · [Integration revision](https://github.com/mech-lang/mech/commit/40ebc4fe128abc5f82deffbc24b24cd3cfc73e25) · [CI](https://github.com/mech-lang/mech/actions/runs/44052638183)

## Single-process source compilation

The maintained rebuild now accepts `--direct-source`. It passes the canonical Program artifact and function catalog to Cranelift in memory and writes the same bytecode receipt. This removes the separate emitter's bytecode reload, decode, canonical re-encode and second catalog construction. [Source change](https://github.com/mech-lang/mech/commit/1f3b7c6826956b81fcb0ac1524a489b263a476df) · [Rebuild and raw trials](https://github.com/mech-lang/mech/blob/7179ed52634902817ca9d1c954fd488322b91f2e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/direct-source/README.md)

In six matched Apple M1 source-through-link orders, the smaller build falls from **4.08628 s to 3.99930 s** (**2.13%**), taking **1.339× Roc** and **8.292× libdeflate** time. Encoder text is **71,960 B**, or **1.247× Roc** and **1.941× libdeflate**. Median peak compiler RSS rises from **382.4 MB to 401.4 MB**. Compilers, fixed runtimes and adapters are prebuilt for each actor. [Complete sizes, timings and profiles](https://github.com/mech-lang/mech/blob/7179ed52634902817ca9d1c954fd488322b91f2e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/direct-source/report.json)

Both paths reproduce the pinned workers byte for byte, preserving their recorded **81/81 Roc and 61/81 libdeflate** wins in both full orders. All seven maintained recipes reproduce their pinned object and metadata. Separate linked-worker checks cover **1,134 exact calls**. The smaller variants keep their existing runtime qualification decisions. [Worker identities and exact checks](https://github.com/mech-lang/mech/blob/7179ed52634902817ca9d1c954fd488322b91f2e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/direct-source/workers/) · [Integration revision](https://github.com/mech-lang/mech/commit/c44a82e7d7572740ba19ba9ff549b5e0c2228302) · [CI run](https://github.com/mech-lang/mech/actions/runs/44045198406)

## Native verification and ownership search

The native emitter compares ordered CFG edges and reuses storage across guarded ownership searches. For the **71,960-byte** recipe on Apple M1, native emission fell from **1.704 s to 1.597 s** (**6.32%**) and the complete build fell from **4.186 s to 4.074 s** (**2.67%**). The smaller recipe takes **1.366× Roc** and **8.478× libdeflate** time through final link, with **1.247× Roc** and **1.941× libdeflate** encoder text. [Matched timings and rebuild](https://github.com/mech-lang/mech/blob/72b46f303398c2cd70583d38dc2c69316f879d4e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-pass-work-reuse/README.md) · [Compiler source](https://github.com/mech-lang/mech/commit/ddd9ba3364fe1efda7a9c92a858afd026eed45da)

The rebuilt emitter reproduces all three original benchmark workers byte for byte. The retained and smaller workers carry their recorded **81/81 Roc** and **61/81 libdeflate** wins in both full orders. The original and new verifiers match on the four CFG and instruction probes, and **43 release tests** passed. [Raw report](https://github.com/mech-lang/mech/blob/72b46f303398c2cd70583d38dc2c69316f879d4e/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-pass-work-reuse/report.json) · [Current integration](https://github.com/mech-lang/mech/actions/runs/44042253143)

## Canonical parser storage

The parser now pools literal scanner storage and copies short one-shot cache requests without retaining their journal pages. Six balanced source-through-link orders on Apple M1 cut the 71,960-byte build from **4.539 s to 4.187 s** (**7.76% faster**). Parsing takes **2.110 s** instead of 2.459 s. The retained 72,520-byte recipe builds in **4.178 s**, down from 4.533 s. The smaller build takes **1.402× Roc** and **8.718× libdeflate** time, with **1.247× Roc** and **1.941× libdeflate** encoder text. [Complete comparison](https://github.com/mech-lang/mech/blob/b6d684604b07ab777330362e8dbafce6f4779d45/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/compact-parser-storage/README.md) · [Compiler source](https://github.com/mech-lang/mech/commit/eefbc059aca81b5aa68ed75b9a9e3b3c8ff8e900)

The newly built compiler reproduces the retained, smaller and aligned-spill workers byte for byte. The retained and smaller workers carry their recorded **81/81 Roc and 61/81 libdeflate** wins in both complete orders. **533 syntax tests** and **60 exact syntax snapshot comparisons** pass. [Exact identities](https://github.com/mech-lang/mech/blob/b6d684604b07ab777330362e8dbafce6f4779d45/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/compact-parser-storage/identity/receipt.json) · [Integration run](https://github.com/mech-lang/mech/actions/runs/44039129263)

## Compiler-emitted aligned spill pairs

The Cranelift compiler at `0f0ace2c9c29fd619014f0e12a0bd9fd0f7ee63b` reproduces the exact native object, metadata and linked benchmark worker. Its **71,896 bytes of encoder text** are **1.246× Roc** and **1.939× libdeflate**, down 64 bytes from the matched Mech control. The complete Apple M1 build is **4.534 s**, or **1.518× Roc** and **9.430× libdeflate**, measured through final link with the compilers and adapters prebuilt. [Source change](https://github.com/mech-lang/mech/commit/0f0ace2c9c29fd619014f0e12a0bd9fd0f7ee63b) · [Rebuild and measurements](https://github.com/mech-lang/mech/blob/e7e54b488641a4665bdb5221f124ff028ddca5ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/aligned-register-spills/README.md)

Each fresh full order preserves every **81/81 Roc** and **61/81 libdeflate** win. The large natural-text cases meet the 0.5% resolution. The paired replay finds slowdowns of **1.704%** on `empty` and **1.085%** on `seven-stored-prefix`. The maintained variant stays opt-in as `fresh-owner-counts-cold-tails-paired-spills`. [Runtime and proof receipts](https://github.com/mech-lang/mech/blob/e7e54b488641a4665bdb5221f124ff028ddca5ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/aligned-register-spills/runtime-policy.json) · [Integration run](https://github.com/mech-lang/mech/actions/runs/44035150703)

## Register spill pairs and function placement

The paired-spill encoder emits **71,864 bytes** (**1.246× Roc**, **1.938× libdeflate**), 96 bytes less than the pinned smaller encoder. The 1 MiB random matcher executes **8.41 million fewer instructions**. Both full timing orders preserve every control win at **81/81 Roc and 61/81 libdeflate**. The per-case replay rejects the paired image because `prefix-natural-65535` and `prefix-natural-262144` slow by **0.576%** and **0.599%**. Complete build time is effectively flat at **4.52776 → 4.52721 s** on matched M1 runs with final linking. [Both complete runs, compiler patch, and replay](https://github.com/mech-lang/mech/blob/0da34baad584c3365642cbd18441e200ab7cf2ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/register-spill-pairs/README.md)

The **71,896-byte** placement diagnostic preserves the control's alignment modulo 64 for all 40 native functions. The two natural cases are within the 0.5% resolution in its nine-case, two-order screen. The short `random-64` case remains unresolved. The recorded paired compiler and both placement controls are reproducible. See the compiler-emitted follow-up above. [Placement results and artifact identities](https://github.com/mech-lang/mech/blob/0da34baad584c3365642cbd18441e200ab7cf2ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/register-spill-pairs/report.json)

## Preselected root inlining

The opt-in AArch64 Cranelift compiler now selects private once-called helpers from optimized IR, verifies the resulting root, and performs one machine compilation for the chosen plan. The pinned 71,960-byte encoder builds from source through final linking in **4.58958 → 4.52728 s** on Apple M1. Native emission takes **1.76414 → 1.69787 s**. All eight matched orders show a shorter complete build.

Roc takes **2.98172 s** and libdeflate **0.48024 s** through the same boundary with compilers, fixed runtimes and adapters prebuilt. Mech builds in **1.518× Roc** and **9.427× libdeflate** time. Encoder text is **1.247× Roc** and **1.941× libdeflate**. Both pinned workers, objects and metadata reproduce byte for byte, preserving **81/81 Roc** and **61/81 libdeflate** historical wins in both full orders. The maintained rebuild exposes `--preselect-root-inlining`. [Raw trials and artifact identities](https://github.com/mech-lang/mech/blob/cf0984ac50e7a1d7e4da47380f42e582d15f1fb0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-root-inline-plan/report.json) · [Rebuild guide](https://github.com/mech-lang/mech/blob/cf0984ac50e7a1d7e4da47380f42e582d15f1fb0/benchmarks/mech-deflate/native-profile/native-compact-20261116/README.md)

The browser standard canary passed after the fullscreen exit fix. The active static audit reached the frozen benchmark runtime after accepting the 11 new exact file contracts. The remaining static gate and per-case repeatability work keep the PR draft. [Hosted browser canary](https://github.com/mech-lang/mech/actions/runs/44022578666/job/133835834951) · [Static architecture job](https://github.com/mech-lang/mech/actions/runs/44022578666/job/133835835167) · [Current review handoff](https://github.com/mech-lang/mech/blob/cf0984ac50e7a1d7e4da47380f42e582d15f1fb0/benchmarks/mech-deflate/native-profile/native-compact-20261116/REVIEW.md)

The spill-store and cached-join screens are archived. The spill-store candidate saved 16 bytes and passed 162 exact linked calls. The cached-join candidate removed 17,270 temporary SSA values with flat native emission time. [Spill-store evidence](https://github.com/mech-lang/mech/blob/cf0984ac50e7a1d7e4da47380f42e582d15f1fb0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/dead-spill-stores/report.json) · [Cached-join evidence](https://github.com/mech-lang/mech/blob/cf0984ac50e7a1d7e4da47380f42e582d15f1fb0/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/native-ssa-timing/report.json)

## One-shot parser improvement

The parser census found **708,002** cache requests whose markers could no longer receive a tree. The one-shot compiler accounts for the same event and token work and reserves the same IDs without building those stale trees when the current grant covers the full scan. The source grammar and runtime artifacts preserve their existing identities.

On Apple M1 the 71,960-byte encoder builds from source through final linking in **4.60240 s**, down from **4.76323 s** (**3.38%**). Roc takes **2.99970 s** and libdeflate **0.48119 s** through the same boundary. Mech is **1.534× Roc** and **9.565× libdeflate** in build time and **1.247× Roc** and **1.941× libdeflate** in encoder text.

All **533 syntax tests** pass. Both persistent benchmark workers reproduce byte for byte and keep their **81/81 Roc and 61/81 libdeflate** results in both full orders. [Raw build trials and correctness proofs](https://github.com/mech-lang/mech/blob/ddc26e24222f14229f4787f55d1d659a4482cddd/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/stale-cache-accounting/report.json) · [Review handoff](https://github.com/mech-lang/mech/blob/ddc26e24222f14229f4787f55d1d659a4482cddd/benchmarks/mech-deflate/native-profile/native-compact-20261116/REVIEW.md)

## Equivalent vector compilation and parser attribution

The opt-in `--reuse-equivalent-vector-ir` path compares the full prepared Cranelift functions. It skips seven of nine unused vector alternatives, moving pool submissions from **23 to 16** with the same cleanup job count. Both pinned benchmark workers reproduce byte for byte and carry their existing **81/81 Roc and 61/81 libdeflate** receipts in both full orders.

On the M1, the 71,960-byte encoder takes **4.76513 s** with reuse disabled and **4.76469 s** with reuse enabled in six balanced source-to-executable orders. Native-only medians move from **1.76341 to 1.76057 s**. The option remains experimental. [Build trials and controls](https://github.com/mech-lang/mech/blob/bef604b4ea4facb27263c034d68f4341277600ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/equivalent-vector-ir/report.json)

The new parser profile attributes **2.565 s** to canonical grammar processing and **2.22 ms** to restart indexing. The separate nested profile counts **499,404** cache advances taking **0.507 s** inside grammar processing. The tree, parser steps, and event counts match in all diagnostic runs. [Parser stages and raw trials](https://github.com/mech-lang/mech/blob/bef604b4ea4facb27263c034d68f4341277600ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-stage-profile/report.json) · [Handoff](https://github.com/mech-lang/mech/blob/bef604b4ea4facb27263c034d68f4341277600ca/benchmarks/mech-deflate/native-profile/native-compact-20261116/REVIEW.md)

## Current compiler profile measurements

On this Apple M1, the 71,960-byte encoder builds from the pinned Mech source through final linking in **4.76479 s**, down from **5.64395 s** at Rust opt-level 1 (**15.58% faster**). Roc takes **2.98555 s** and libdeflate **0.48162 s** through the same boundary. The smaller Mech encoder is **1.24723× Roc** and **1.94067× libdeflate** in text bytes, and **1.59595× Roc** and **9.89315× libdeflate** in build time.

`rebuild.py --compiler-opt-level 3 --target-dir PATH` builds the same Cranelift-based compiler at level 3 with the same C allocator archive. Both pinned benchmark workers reproduce byte for byte and carry their existing 81/81 Roc and 61/81 libdeflate results in both full orders. Level 1 is the pinned reproduction default. The fresh-owner repeatability study and no-inline ablation remain diagnostics.

[Review and continuation handoff](https://github.com/mech-lang/mech/blob/f2eb85ae053a28ee88efeae87a55dc164c83f71c/benchmarks/mech-deflate/native-profile/native-compact-20261116/REVIEW.md) · [Raw build and identity evidence](https://github.com/mech-lang/mech/blob/f2eb85ae053a28ee88efeae87a55dc164c83f71c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/host-opt-levels/report.json) · [Linked-size census](https://github.com/mech-lang/mech/blob/f2eb85ae053a28ee88efeae87a55dc164c83f71c/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/linked-size-census/report.json)

The native compact compiler and parser changes build from this branch on #973. This branch contains the Mech source, compiler changes, exact rebuild recipes, and benchmark evidence another agent can continue from. The recipe uses Cranelift and requires no external LLVM tools.

- Base branch `codex/level12-compression-consolidated` at `9087b1f07727a9bfcb7c09059f48edaca6dc2301`
- Review branch `codex/native-compact-source-handoff` at `9cf94256315362201a897e9a4e0365b6442dac62`
- [Agent handoff](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/REVIEW.md) · [Build and test commands](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/README.md) · [Fresh owner compiler change](https://github.com/mech-lang/mech/commit/9f956f48e57ee504a19ec823aa618f05f60aae96)

## Qualification and integration

Qualification v1 verifies the frozen 81 named cases and both complete orders from raw observations. It keeps individual wins, exact worker and output identities, checked failures and origins, resource observations, and repeatability in the promotion decision. All 20 behavioral tests pass. Archived replay evaluates 41 configurations, with five rejected and 36 unresolved. This includes both 81/61 orders for the fresh-owner and 71,960-byte configurations. [Validator and reproduction commands](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/QUALIFICATION.md) · [Archived decisions](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/qualification-v1/archived-decisions.json).

The distribution snapshots now record the two intended compiler allocator dependencies and their selected graph digests. The exact public CLI selection includes all six units. The warning audit passes locally, and both generated Linux launcher feature sets pass with warnings denied. The browser producer preserves the canonical Cargo lock with identical package records and verifies it against the selected checkout before upload. [Repair evidence and remaining architecture gates](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/integration-repairs/report.json).

The workflow contract now checks the derived CLI counts. All 90 workflow contract tests pass locally. The repaired compiler source at `a16e974f26fd812d0bd906ef9d82477230dc9c7d` rebuilds the default, fresh-owner, and 71,960-byte benchmark workers, encoder objects, and complete metadata byte for byte. Each linked worker passes 162 exact-output, alias, and inflation checks. [Rebuild commands, hashes, and tests](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/integration-repairs/followup/report.json).

The standard distribution snapshot, packaging, and native host catalog passed in CI. The module layout follow-up resolves all 48 conflicts found by that job. The original module-layout and warning checkers and workspace formatting pass locally. The renamed compact layout type removes its retired-value finding. Byte-identical rebuilds preserve the three pinned benchmark workers, encoder objects, and complete metadata. The five fresh-owner code-generation tests pass with warnings denied. [Distribution job](https://github.com/mech-lang/mech/actions/runs/44000997552/job/133765303765) · [Module moves and rebuild receipts](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/integration-repairs/module-layout/report.json).

This PR remains a draft. The full unsafe-boundary audit still reports 182 unlisted paths and three prohibited manual Send or Sync implementations. The retired-value-system checker still reports generated and archived include paths. Browser compute awaits a completed CI build after the Rust component download failure. A separate standard browser canary has an intermittent console-drag failure. [Current integration run](https://github.com/mech-lang/mech/actions/runs/44004955952).

The benchmark cohort below was measured at `5acf709fd8a2904c99a1530e4e29f373c8e09c7a`.

The native cleanup now removes redundant block parameters in one ordered pass. The matched Apple M1 native-emission median moves from **2.22625 to 2.21648 s** and the complete build moves from **5.65167 to 5.64176 s**. All 207 Cranelift tests pass. The pinned 72,520-byte worker, encoder object, and complete metadata reproduce byte for byte. [Compiler change](https://github.com/mech-lang/mech/commit/f5786a14369d23ff764808d72213f8cd82d19308) · [Matched timings and identity checks](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/batched-block-params/report.json).

The new opt-in **71,960-byte** encoder is **1.24723× Roc and 1.94067× libdeflate**, 560 bytes below the default. Both full runtime orders record **81/81 Roc and 61/81 libdeflate**. Peak stack is 5,296 bytes. Its matched build through final linking is **5.65399 s**, **1.88967× Roc and 11.76562× libdeflate**. Duplicate-control repeatability remains open for three cases. The 71,720-byte configuration lost `320-overlap` and `prefix-periodic-1024` in both focused orders. Rebuild the 71,960-byte version with `rebuild.py --variant fresh-owner-counts-cold-tails`. [Full paired evidence and nine size screens](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/continuation-widths/report.json).

The earlier parser change cuts the complete Apple M1 source-to-executable build from **6.30298 s to 5.65845 s (10.23% less time)**. Roc took 2.98664 s and libdeflate 0.48728 s in the same runs. Mech is now **1.89458× Roc and 11.61221× libdeflate** on this build. Final linking is included, with compilers, runtimes, and adapters prebuilt.

The parser reads a retained page at a time, hashes contiguous token bytes within the existing work grants, and skips an unused event map while caching subtrees. The separate parser-only comparison takes **3.51713 → 2.92567 s** with identical syntax trees, IDs, parser steps, and events. All **531 syntax unit tests** pass. [Parser source change](https://github.com/mech-lang/mech/commit/d24ceb9b04729a385a97997c6222bb94c2c9cb3b) · [Full trials, phase profiles, and rebuild receipts](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/parser-journal-pages/report.json).

Both frontends produce byte-identical bytecode, native objects, metadata, and linked executables in all twelve builds, including warmups and separate profiles. The pinned 72,520-byte benchmark worker also rebuilds byte for byte. Its earlier **81/81 Roc and 61/81 libdeflate** results apply to that same binary. The updated compiler reproduces the optional 72,344-byte object and metadata as well. The workflow timeout now covers the extra fresh owner test. The scheduling contract passes locally.

In the earlier fresh owner study, the optional pass folds 20 reference-count loads for successful nonempty allocations. It stops at possible aliases, unknown calls, and control-flow joins without a common count. The smaller build retains all checked failure paths and its 5,296-byte measured peak stack. Five native test groups exercise 2,592 calls across the proof boundaries.

| Earlier owner proof study on Apple M1 | Encoder text | Encoder text relative to libdeflate | Source to final executable | Runtime wins |
| --- | ---: | ---: | ---: | --- |
| Retained Mech control | 72,520 B | 1.95577× | 6.25214 s | 81/81 Roc and 61/81 libdeflate in both orders |
| Mech with fresh owner counts | 72,344 B | 1.95102× | 6.24649 s | 81/81 Roc and 61/81 libdeflate in both orders |
| Roc | 57,696 B | 1.55599× | 2.98377 s | — |
| libdeflate | 37,080 B | 1.00000× | 0.48196 s | — |

The 176-byte reduction gives 1.25388× Roc encoder text. Complete build time is effectively flat at 0.99910× the control, 2.09349× Roc, and 12.96053× libdeflate. The compiler, runtime, and adapters are prebuilt and every measurement includes final linking. Four balanced orders follow one excluded warmup per actor. Parsing accounts for 3.523 s of the candidate build. [Raw build trials and Mech, Roc, and Clang phase profiles](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/fresh-owner-counts/builds/timing.json).

The two full runtime orders verified 1,965,312 calls. Initial paired intervals bound 77 cases at 0.5% resolution. Longer duplicate-control runs resolved `heldout-window-32767`; the control differences exceeded the resolution on three cases. The pass remains opt-in. The baseline reproduces its object, metadata, and original benchmark worker byte for byte. All three new rebuild configurations reproduce their respective object and metadata hashes and pass 162 correctness calls each. [Raw runtime results, checked errors, stack and shape controls, and rebuild receipts](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/fresh-owner-counts/report.json).

The earlier 72,136-byte owner and cleanup configuration reached 81/61 in both full orders but regressed five cases above 0.5% and raised peak stack to 5,344 bytes. The 72,024-byte combination with the new pass also regressed two focused cases. Both remain outside the retained recipe. [Full cleanup experiment](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/evidence/owner-cleanup-full/report.json).

Earlier build validation and experiments remain available in the [rebuild guide](https://github.com/mech-lang/mech/blob/9cf94256315362201a897e9a4e0365b6442dac62/benchmarks/mech-deflate/native-profile/native-compact-20261116/README.md). This PR remains a draft while CI and the remaining runtime and ordinary resource-accounting qualification are open. The target is 1× libdeflate for emitted text and complete build time with at least 81 Roc and 61 libdeflate wins.
