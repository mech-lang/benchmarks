# Lean4 k-nucleotide: standard-map source candidates

This is a source-only proposal. Neither candidate has been parsed, compiled,
executed, counted, formatted or timed. No eligibility, existing source, sample,
count or catalog field is changed. All qualification flags and application counts
remain false/null in [plan.json](plan.json).

The [two historical applications](../library-map-review-v1/README.md) produced
the requested output through dense counters and query-only scans, omitting the
required library-map accumulation. These candidates replace that work with full
ordinary `Std.HashMap` histograms at all seven widths. Their historical timings
cannot be transferred to this different algorithm. The proposal is not evidence
that either candidate is fast or the most concise Lean formulation.

## Exact standard API, without a custom map

The inspected distribution is the retained official Lean4.35.0 release at
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`. Selected unchanged source/header files
and the Apache2.0 license are saved in [vendor/lean-4.35.0](vendor/lean-4.35.0/).
[api-source-snapshot.json](api-source-snapshot.json) gives their exact hashes and
ties them to the retained [toolchain evidence](../toolchain-v1.json). This small
API snapshot is not a newly verified complete runtime/transitive dependency
closure. A future build must use the actual pinned distribution and capture its
loaded compiler/module/library inputs; it must not import the review snapshot as
a suite-local map implementation.

The public [HashMap API](vendor/lean-4.35.0/src/lean/Std/Data/HashMap/Basic.lean)
has `emptyWithCapacity` with default capacity8 (lines70–72), `alter` (245–247),
`fold` (219–221), `getD` (157–159) and `toArray` (257–259). The empty collection
instance also uses that same default constructor. These are existing project
APIs, not guessed helpers. The standard implementation uses separate chaining,
a power-of-two bucket array and library-managed growth. Its default capacity8
is rounded by the library to16 initial buckets; no input-sized or width-sized
reservation is requested by either application.

`counts := counts.alter key (fun previous => some (previous.getD 0 + 1))` is one
public read/update operation and handles both absent and present keys. **It is
not a claim of one probe or one chain traversal.** The pinned
[implementation](vendor/lean-4.35.0/src/lean/Std/Data/DHashMap/Internal/Defs.lean)
at288–306 computes a bucket, checks membership, alters the chain and checks
post-update membership on an existing key; insertion can trigger growth and
rehashing. Do not patch those internals or replace them with a custom table to
improve a benchmark. The public `getThenInsertIfNew?` does not itself increment
an existing value, so its name is not a substitute for a real counter update.

The callback captures no old map. The application threads the returned map into
the next iteration and never retains earlier versions while updating. This is
the standard library's recommended linear use. The library clears the selected
bucket before rebuilding its chain, and the runtime's array operations check
exclusive ownership. These facts motivate the source shape; they do not prove
that the generated candidate avoids all copies, RC operations or allocations.
Future compiler IR/generated-C inspection and an independent diagnostic are
required before making such a performance claim.

## Two isolated key representations

- [nat-alter.lean](sources/nat-alter.lean) stores keys as `Nat` while using the same
  UInt64 rolling arithmetic and converting each completed key with `toNat`.
- [uint64-alter.lean](sources/uint64-alter.lean) stores those same keys as `UInt64`.

The sources differ only in `Key`, `mapKey` and `wordKey`. Both store `Nat` counts,
use the standard BEq/Hashable instances, the same parser, default constructor,
`alter` call, seven histogram passes, sorting and output. No custom hash function,
bucket access, reservation, raw-map operation, unsafe access or native counting
kernel appears in either application.

The largest key is below2^36 (width18); the specified full input's counts also fit
the pinned64-bit runtime's immediate-Nat range. The pinned
[Hashable instances](vendor/lean-4.35.0/src/lean/Init/Data/Hashable.lean) convert Nat
to UInt64 and use UInt64 itself respectively, so these encoded keys supply the
same numerical hash before the standard library's own scrambling/indexing.
The [runtime header](vendor/lean-4.35.0/include/lean/lean.h) shows immediate Nat
boxing below `SIZE_MAX >> 1`, while `lean_box_uint64` allocates a constructor for
a UInt64 in object representation. This suggests a possible advantage for Nat
keys in a generic map. It does **not** establish how many boxes the specialized
candidate emits or whether inlining eliminates temporary objects. No generated
code for these new candidates has been captured. Conversely, Nat conversion and
generic arithmetic could have costs. Keep this comparison a static hypothesis
until native C/IR and matched measurements resolve it.

## Input, work and source boundaries

The parser reads binary stdin through the existing `IO.FS.Stream.read` API in
64KiB blocks and processes complete CR/LF-delimited lines. It retains a partial
line across blocks and terminates the final line at EOF, avoiding a new UTF-8
restriction on irrelevant headers/comments. It enforces the exact THREE token,
stops that record at the next header, ignores comment/empty lines, folds valid
DNA letters to0..3 and rejects invalid target-record bytes. These are intended
source semantics, pending boundary fixtures; no parser acceptance is claimed.

For each width1,2,3,4,6,12,18, `histogram` rolls every input byte and invokes
`alter` once for each completed overlapping window. It has no query parameter.
Widths1/2 enumerate the completed map and sort by descending count, then ascending
encoded key (the same lexicographic order for fixed-width A/C/G/T). Each longer
width builds its **complete** map before reading the one requested query with
`getD`; unrelated keys are still accumulated. Maps are produced sequentially so
unused long-width maps may be released before the next pass, rather than keeping
all seven live. That lifetime must be confirmed in generated code. The source
does not combine occurrences, infer counts from a suffix table, sort/reduce,
use dense arrays, or skip updates for keys that will not be printed.

The full histogram can be much larger than the earlier query-only state. Memory
and startup/growth behavior must be measured at bounded/pilot sizes before any
full-size process is authorized. An allocation failure remains a failed
candidate; it is not a reason to restore query-only work or input-sized reserve.
Both current sources are serial and create no extra workers. Parallel width
tasks would be a separately qualified variant with a reviewed memory budget and
the established worker cap.

Every declaration in each Lean application, including binary parsing, encoding,
histogram, decoding, sorting, output and FFI declaration, is application source.
The unchanged [Format.c](sources/Format.c), SHA
`efa69b65452aef20b0b9d60a24f95bcc13a08d03e607d1f4fe411948f3a16000`, remains the
same generic fixed-point leaf. It does not count nucleotides. Submitted and
application scopes must both remain explicit; no application helper is excluded.
The [parent-authorship snapshot](parent-authorship.json) preserves the parent's
existing source citations/license/model record without extending it to this
new write. New application changes were authored in the current Codex GPT-6
family session; exact model version is unknown. Suite changes use the repository
Apache2.0 terms, and the unchanged Lean source snapshots retain their notices.

## Qualification required before any result

1. Verify the exact restored Lean/compiler/runtime/module/SDK/PCRE-independent
   formatting inputs. Compile both sources with the retained native C backend,
   strict floating-point and recorded optimization settings, with all commands,
   environments, diagnostics, failed attempts, generated C and binary hashes.
   No compiler run has occurred for this packet.
2. Compare complete output with the independent bounded corpus/reference,
   including THREE versus THREEX, tab/space header boundaries, absent/empty/short
   records, lengths around every width, ties, upper/lowercase, invalid target
   bytes, comment/header bytes, later records, CR/LF/CRLF, EOF and splits through
   a header/line at a64KiB input boundary. A former parent is an output comparison,
   not an oracle for required map work.
3. In untimed exact-source-bound diagnostics, compare every complete histogram
   with an independent map reference; record every window/key/update, old and new
   count, map entry count and library growth. Require `max(N-k+1,0)` actual updates
   for each of the seven widths and conservation of total counts. Cover repeated
   keys, collisions, default-capacity expansion and non-query long-width keys.
   Output agreement alone is insufficient.
4. Inspect actual native specialization, key boxing, callback closure allocation,
   bucket/chain RC, exclusivity and map destruction. Any instrumentation must
   append observations to the actual library/application operations, retain exact
   deltas and stay outside timed binaries. Do not replace the library algorithm.
5. Obtain an exact-source retained count/owner review for all application units,
   explicit generic support roles and any later formatted measure separately.
   Counts are currently null; neither physical inspection nor a parent's count
   supplies qualification.
6. Only after those gates and a separately authorized quiet window, seal bounded
   memory/time pilots and then an appropriate shuffled fresh-process full-size
   comparison. Preserve all valid observations and all old source/history. No
   current eligibility or performance result transfers to these candidates.
