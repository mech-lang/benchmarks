# TypeScript workload source drafts

This packet contains one typed source for each of the ten workloads. The
[manifest](source-manifest.json) records exact reference and draft hashes,
source adaptations, required work and pending qualification. Nine sources adapt
retained JavaScript submissions; reverse complement has a new record parser and
output traversal. Contributor attribution remains in each adapted source and the
[upstream license](LICENSE.benchmarksgame) accompanies the packet.

| Workload | Reference submission | Authored TypeScript structure | Required work |
| --- | --- | --- | --- |
| Binary trees | `binarytrees-node-7` | Nullable recursive node class | Distinct leaf/internal nodes, stretch tree, repeated temporary trees, retained long-lived root |
| Fannkuch-redux | `fannkuchredux-node-8` | Numeric arrays and scoped integer state | Every permutation, prefix reversals, alternating checksum |
| FASTA | `fasta-node-1` | Probability dictionaries and string buffers | Sequential RNG and complete 2n/3n/5n records |
| K-nucleotide | `knucleotide-node-8` | `Map<string, number>`, string sequences and frequency tuples | Overlapping substrings at all seven required lengths |
| Mandelbrot | `mandelbrot-node-1` | Numeric recurrence and byte output | All pixels, escape iterations and padded PBM rows |
| N-body | `nbody-node-8` | Typed `Body` class and body arrays | Fresh state, momentum adjustment, pair forces, integration, two energy evaluations |
| Pi digits | `pidigits-node-2-two-extracts` | Explicit `bigint` spigot state | Unbounded sequential recurrence with both independent division extractions |
| Regex-redux | `regexredux-node-4` | `RegExp[]` and strings | Nine counts and five ordered replacements |
| Reverse complement | `revcomp-node-2` as historical reference | New typed byte parser, complement table and output buffer | Complete records, reverse traversal, IUPAC mapping and 60-column wrapping |
| Spectral norm | `spectralnorm-node-8` | Numeric arrays and explicit local loop variables | Forty implicit coefficient products; no stored matrix |

All ten drafts use one computation thread. They preserve the algorithms of the
selected sequential references, except for the disclosed source changes. Binary
trees uses a typed class instead of a constructor returning a separate object
literal. Accidental global variables in several JavaScript references become
explicit locals. Mandelbrot and pi accept an explicit zero instead of treating
it as a missing argument, and zero-size fannkuch emits both summary lines.
K-nucleotide selects only the exact THREE identifier before space, tab or line
end, ignores comment lines, validates selected bases and breaks frequency ties
by ASCII key. Pi output accumulates digit characters so leading zeroes in a
final partial group survive. Mandelbrot writes through a fixed 64 KiB buffer
using synchronous writes with partial-write handling. Regex counts are
case-sensitive and Latin-1 input decoding preserves byte values; header cleanup
uses the retained byte oracle's unanchored non-LF pattern. These corrections
require bounded comparison against the independent oracles before admission.

The new reverse-complement parser accepts CR, LF and
CRLF, preserves arbitrary header bytes, ignores preamble/comment lines, handles
empty records and rejects invalid sequence bytes in reverse traversal order.
It reads the complete input and uses one input-sized sequence buffer; memory
cost and full-input behavior require measurement. Its output writes handle
partial writes. The existing independent
[reverse-complement fixtures](../../prolog/revcomp-linear-v1/fixtures.py)
provide 54 future conformance cases; no TypeScript case has run.

The planned execution mode is TypeScript compiled to JavaScript, then executed
by Node.js/V8. The [configuration](tsconfig.json) enables
[strict checking](https://www.typescriptlang.org/tsconfig/strict.html), requires
successful checking before emission, targets ES2022 and selects
[NodeNext module resolution](https://www.typescriptlang.org/docs/handbook/modules/reference.html).
The local package explicitly selects CommonJS. Source maps and original source
text will be retained with emitted JavaScript. The configuration targets
TypeScript 7.0.2 and enables `esModuleInterop`: TypeScript 7 rejects the previous
`false` setting, as documented in its
[release notes](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).
The intended class-field behavior is constructor assignment semantics via
`useDefineForClassFields: false`; acceptance and emitted behavior still require
verification with the pinned compiler. Constructor parameter properties must
remain attributable to their authored declarations in the emitted-code review.
No `any`, suppression comments, JavaScript inputs or transpile-only runner is used.

Dependencies are the TypeScript compiler, `@types/node` and its declared type
dependencies for building, plus Node.js standard libraries and V8 at execution.
The programs use `node:fs`, `node:readline`, `node:process`, buffers, ordinary
collections, BigInt and built-in regular expressions. No external benchmark
kernel or npm arithmetic/regex package is required. The retained Node candidate
exists and a historical version receipt says `v24.19.0`; its current executable
and dependency closure have not been verified for this packet. TypeScript and
Node declaration packages were not found in the specific local/global package
locations checked. The exact `@types/node` version and integrity, compiler platform-package
integrity, dependency lock and local package verification remain pending. The
[toolchain selection](../toolchain-v1/selection.json) records the compiler's
official 7.0.2 registry integrity and platform package, with installation and
dependency verification explicitly pending.

Canonical LOC is also pending. The retained qualified lexical/canonical pipeline
has JavaScript support but no TypeScript language entry. Adding an alias or
counting emitted JavaScript would omit authored types and misclassify typed
syntax. A TypeScript compiler-AST reader must preserve source spans and account
for type aliases, class fields, constructor parameter properties, annotations,
nullable unions, tuples and generics alongside ordinary executable statements.
It needs packed/expanded equivalence and ambiguity fixtures before counting
these sources. General library declarations are dependencies, while all authored
application declarations belong to their source bundle. No formatter has been
selected or qualified.

The [shared conformance corpus](../../shared/bounded-corpus-v1/) now provides
149 cases across all ten workloads. Its 142 success cases and seven rejection
cases have expected inputs/results prepared; no TypeScript subject has run.
The [AST reader draft and fixtures](../source-counts-v1/) prepare compiler-based
source ownership; the native reader and canonical counter remain unqualified.

Compilation, emitted-code review, bounded conformance, runtime allocation/work
checks, canonical source counts and fresh full measurements remain unperformed.
All counts are null and all timing/admission fields remain empty or false. The
existing JavaScript measurements are not TypeScript samples.
