# Uiua fannkuch v5 source owners

The exact compact source `95f622e306aa23ce3678e6c5aba0dfec8f303bf31b294d78124c7e451ea65489` has 14 independent bindings, four record declarations and two output statements: **20 canonical source units**. The exact fast source `b3a2563f7d6503d03d2c0bbd7edae82f9743f137f7d47b3fa561970cfa0a4a0e` adds the independent `FlipPermutations` binding: **21 units**. Both complete files are retained under `archive/comparisons/r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/sources/`.

Each nonblank line contains one complete source owner. There are no comments, blank lines, detached delimiters, imports, application helpers or authored auxiliary modules in either bundle. The exact-source owner checker enumerates every line and accepts only those two digests. It is not a language-wide parser or a physical-count fallback for changed sources.

| Owners | Compact lines | Fast lines | Treatment |
| --- | --- | --- | --- |
| `N`, `Widths`, `Divisors`, `Total`, `Rotate`, `Permutation`, `FlipIndices` | 1–7 | 1–7 | Seven separate bindings |
| `FlipPermutations` | — | 8 | One additional binding |
| `FlipState` | 8 | 9 | One record declaration |
| `FlipStep`, `Flips` | 9–10 | 10–11 | Two separate bindings |
| `F`, `Ranks`, `Block` | 11–13 | 12–14 | Three separate record declarations |
| `BlockIndices`, `Ranked`, `Candidate`, `Work`, `Result` | 14–18 | 15–19 | Five separate bindings |
| Checksum and maximum output | 19–20 | 20–21 | Two separate output statements |

Record fields inside `{…}` specify one declaration's shape; they are not separately executable assignments. The opening and closing braces occupy that same declaration line. Nested tacit pipelines, branches and function arguments remain expressions within their named binding. For example, `Result` contains the worker spawning, wait and ordered result collection expression; it contains no additional named binding. The formatter string is part of the maximum-output expression, not another statement. No independent application owner is omitted or hidden in a native benchmark helper.

This uses the same source-unit rule as the preserved Uiua array-source review: each independent binding or data declaration is counted, with ordinary tacit pipelines remaining expressions. It extends that reasoning to two explicitly inspected source identities; it does not extend the old seventeen-source whitelist or modify any old count approval.

Existing validation compiled and ran these exact complete sources, and the saved source audit records their full required work. The completed nine-observation study and its independent reconciliation remain the runtime evidence. Source-count admission requires independent review of this owner coverage and a successful pure checker replay against the exact retained bytes; it requires no additional Uiua execution or native parser capture.

Formatted LOC is unavailable. These counts must be published as canonical source units only, with the two authored source hashes and this review bound into the publication candidate.
