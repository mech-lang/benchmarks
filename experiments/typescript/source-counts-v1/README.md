# TypeScript AST source-count preparation

This packet prepares an authored-source reader and counting policy for the ten
[TypeScript drafts](../source-v1/INVENTORY.md). The reader has **not run**.
There is no native AST receipt, implemented canonical counter, admitted source
count or timing in this packet.

## Compiler frontend

[reader.mjs](reader.mjs) targets exactly TypeScript 7.0.2. Its intended frontend
is the native compiler exposed through `typescript/unstable/sync`, with node
kinds from `typescript/unstable/ast`. These APIs are unstable and version-pinned;
the implementation does not assume the older `createSourceFile` API exists.
The package version's recorded upstream commit is
`2bd066d87f5bafd315be9f40889d0a60b9e58e0b` in `microsoft/typescript-go`.

The official [API implementation](https://github.com/microsoft/typescript-go/blob/2bd066d87f5bafd315be9f40889d0a60b9e58e0b/_packages/native-preview/src/api/sync/api.ts)
provides snapshots, source retrieval and syntactic diagnostics.
Its [client](https://github.com/microsoft/typescript-go/blob/2bd066d87f5bafd315be9f40889d0a60b9e58e0b/_packages/native-preview/src/api/sync/client.ts)
starts the compiler with `--api`. Node plus the native child therefore require
retained process ownership, limits, complete diagnostics and closure evidence.
Returning from `api.close()` alone is not proof that the process tree was reaped.

The reader uses an explicit source-only virtual project with `noEmit`, `noLib`,
`noResolve` and an empty `types` list. Its closed filesystem returns a definite
missing result outside the supplied text/configuration inventory. It invokes
only snapshot/source/syntactic-diagnostic APIs. It never imports, evaluates,
type-checks, emits or runs benchmark source. This parse configuration is separate
from the benchmark compilation configuration; successful parsing cannot establish
type correctness or compilation-option compatibility.

Every successful input retains its original bytes, exact parser text, full
semantic AST, parent/child links, selected semantic-role links and per-node text
hashes. Ranges are UTF-16 offsets, as exposed by the native API; they are checked
against JavaScript string slices. Unsupported enum identities, malformed ranges,
missing role owners, unexpected sources or unexpected parse outcomes fail the
reader. Expected syntax-error fixtures retain diagnostics and source bytes with
no owner tree. The serialized role inventory is deliberately bounded; it is not
a claim that every TypeScript grammar construct has an admitted counting rule.

The native API is a semantic AST, not a complete concrete token/trivia tree.
The future counter must separately prove comment/literal coverage and punctuation
ownership. In particular, `forEachChild` success does not prove that every source
character has been classified. Source text, unknown semantic nodes and all
unclassified ranges must remain available to review.

## Counting policy to implement

The common rule is
`canonical-source-units-20261012-approved-rule-v2`. Its retained JavaScript
implementation is policy evidence, not a TypeScript parser or an allowed alias:

- [Canonical boundaries](../../../archive/validation/loc-normalization/20261012/canonical.py)
  count a function/control/declaration header once, its opening brace zero times,
  and each explicit executable/declaration closing brace once.
- [Independent units and physical remainder](../../../archive/validation/loc-normalization/20261012/normalizer.py)
  retain separately written declarations and chained assignments, while preserving
  literal/data wrapping. Formals, arguments, for-header separators, object data
  properties and type punctuation do not become independent statements.
- [JavaScript compatibility fixtures](../../../archive/validation/loc-normalization/20261012/test_normalizer.py)
  establish, among other cases, two units for `let a=1,b=2`, one for destructuring,
  one for an expression arrow, and four for a callback containing two statements.

The TypeScript projection must use native ownership, not text substitutions that
erase types before applying JavaScript rules:

| Authored form | Proposed owner treatment |
| --- | --- |
| Import or complete type alias | One source declaration; retain its type syntax and source span |
| Independent `let`/`const`/`var` declarator | One binding, plus additional independently written chained assignments |
| Destructuring declarator | One destructuring operation; binding-pattern punctuation is structural |
| Named function, method or constructor with body | Header 1, opener 0, each body unit, written close 1 |
| Class | Header 1, separately authored members, written close 1 |
| Class field | One declaration, including its type; initializer work remains visible |
| Constructor parameter property | One field unit in addition to the constructor header; modifiers identify the property; ordinary formals add no field units |
| Annotation, generic argument/parameter, union or tuple member | Retain under its declaration/header owner; commas and type operators add no executable statements |
| Expression-bodied arrow | Part of its containing expression; no invented body header or close |
| Block-bodied callback | Retain header, every body unit and written close; only its first containing expression prefix may combine with the header |
| `if`/`else`, loops, `try`/`catch`/`finally` | Explicit control headers and bodies; `else if` is a combined header; no fabricated closes for unbraced bodies |
| Multiline array/object/string data | Preserve noncomment physical rows; data braces are not executable closes |

Constructor parameter properties count as authored fields even when an emitter
creates corresponding JavaScript assignments. Generated assignments and runtime
declaration libraries are not additional application source. Conversely, erased
types and uninitialized class fields cannot disappear from the source inventory.

Only native literal owners may protect strings, regex literals and template
segments before recognizing comments. Protecting an entire template expression
would hide executable interpolation; interpolation with independent work remains
gated until that ownership is qualified. Chained callback continuations, unknown
syntax, decorators, ambient declarations, namespaces, interfaces and complex
mapped/conditional type declarations also remain review gates. Every diagnostic
requires a null admitted count. A parser accepting syntax does not approve its
owner projection.

[fixtures.json](fixtures.json) contains hand-reviewed source cases and proposed
counts or explicit review/rejection expectations. The expected numbers are
fixture contracts, not observed parser/counter results. Packed/expanded pairs,
authored fields, parameter properties, typed aliases, chained writes, data
wrapping, literal/comment ambiguity, non-BMP text, CRLF and a never-evaluate
canary are included. More complex forms deliberately have no proposed count.

## Deferred native sequence

1. Under the common timing mutex, retain exact Node, TypeScript 7.0.2 package,
   native compiler, module dependency closure and source pins. Check the actual
   installed API against the upstream interfaces and reader assumptions.
2. Materialize fixture text as separately pinned files. Prepare a fresh
   `typescript-ast-reader-plan-v1` with explicit reader, package metadata/API
   entry pins, native executable path, Node path/version, output path and each
   input's ID, role, source path/hash and expected parse outcome.
3. Run the reader once with its exact plan SHA under the existing supervised
   native-process protocol. Capture Node and every compiler descendant. Preserve
   failures; use a new reviewed attempt if source changes are needed.
4. Independently reconcile exact bytes, UTF-16/non-BMP offsets, all role links,
   source coverage, parser outcomes, source inventory and process closure. The
   reader intentionally leaves `native_transport_verified` false.
5. Implement and qualify the small owner projection against these actual ASTs
   and fixture contracts. Review all ten source projections before admitting
   canonical LOC. Formatted LOC and runtime/work qualification remain separate.

The eventual supervised command shape is:

```text
<pinned-node> <absolute-reader.mjs> <absolute-plan.json> <plan-sha256>
```

No executable plan, runtime closure hash or native result has been created by
this source-only preparation.
