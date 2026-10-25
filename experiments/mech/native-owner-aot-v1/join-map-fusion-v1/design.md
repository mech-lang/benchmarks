# Selected join and emitted String-map composition

This is the implementation contract for the candidate, not a claim that the runtime transformation or timings are complete. The parent is `630921324a65c385cf63e871d3241dbb0847b8d6`.

## Representation and execution

The static proof requires the existing String-map region's complete last-use inventory to include the selected join's result. The path from that join to the map header may contain only an exact linear copy chain, no-op jumps, the selected collection begin and its initializer. It cannot cross an activation boundary or retain another observer of the joined String. Serialized associations are rederived from the canonical plan.

Runtime eligibility further requires successful EOF, an empty join separator, unique contiguous captured ASCII lines, and an already available immutable `Map<String,String>` whose relevant ASCII entries map one byte to one ASCII byte. Initial support bounds the source map at 128 entries. Other representations and maps retain the original selected join and normalization paths.

The original join performs all existing local/global admissions and prepays its complete library computation before choosing composition. Its private state then owns the selected view, exact output allocation, finite table and original map identity. A generated loop at that same join visit requests one initialized physical output chunk, calls the **existing generated SIMD String-map function** on that newly copied span in place, and reports the processed prefix. The source chunk retires before normalization runs; no raw source loan survives a callback. Copying and mapping remain two local passes over a cache-local chunk, replacing the separate whole-string normalization pass.

Two auxiliary operations pair chunk preparation and completion at the exact original join visit. The runtime rejects duplicate prepare, completion without a loan, wrong sites, foreign collections, excessive processed counts and advancement while a loan remains. Generated code, rather than a Rust program dispatcher, runs the chunk loop and invokes the compiled map. The ordinary helper interface never accepts a function pointer.

At the first missing map key, the current span contains its mapped valid prefix and its unchanged missing-key byte. Later chunks are copied without further mapping. The missing-key index is retained without raising a map error. The complete original join still finishes before the original map header is reached.

The completed private output becomes a genuine same-account owned byte buffer. Original join-result and copy-result semantic slots stay absent. The proved collection initializer obtains the original one-byte source count from private geometry and retains the existing initialization charge; captured ASCII line payloads contain no LF, so an empty-separator join has one original grapheme per byte even if a lone CR remains. The map's replacements may contain CR or LF without changing that original source count.

At the original String-map header, the runtime verifies the saved immutable map generation and storage identity, executes the original map admissions and full scan/loop charges, and installs the owned buffer through the existing compiled-map buffer/finish path. It delegates a saved missing key to the existing selected owned-String lookup at the original selection origin. Successful preparation returns a distinct completed marker so generated code jumps to the original generator exit without applying the map a second time. The normal ready marker continues to invoke the existing compiled mapper; unsupported cases retain ordinary execution.

## Fuel, memory and ordering

No call or root allowance is renewed. A conservative composition bound must fit the already charged original join bound. The proposed bound includes fixed descriptor work, at most 128 table entries, 56 work units per payload byte, 128 per selected row and 2,048 per retained physical chunk. If the bound does not fit, composition declines before consuming the selected view. Empty physical spans may be folded inside preparation; they cannot cause unpriced native calls. Actual emitted/helper work must be audited against these conservative factors before promotion.

The original join's output envelope covers output backing and optional fixed table/state metadata. Managed node claims for temporary metadata replace, rather than coexist with, final canonical-output node claims; metadata retires before output publication. Optional metadata admission/allocation failure retains the ordinary join path. The completed owned buffer retains its real capacity claim and schema provenance. Current generation/ownership checks remain mandatory at every handoff.

Input/UTF-8 errors retain precedence. Original selection and join capacity failures occur before map inspection or deferred map failure. Collection begin and original map admissions retain their later positions. No fabricated canonical intermediate String, partial Matrix, query-only histogram, dense-counter replacement, input-specific preallocation or early counting is introduced.

## Qualification still required

The complete candidate needs original/decoded output equivalence for fragment boundaries, CRLF, empty rows, unterminated lines, lone CR, Unicode fallback, partial selections, nonempty separators, shared/reordered source fallback and byte-map replacements containing line endings. Tests must check missing-key origin, join-versus-map error precedence, tight local/global byte/node/work limits, replay/foreign-site denials, cleanup, and successful reuse after failure. Runtime reporting should record composed byte count so primary runs prove selection of the new path.

Only after qualification should the unchanged benchmark source be compiled and timed in two balanced complete-process sessions against the fixed parent and exact upstream Rust. All original 874,999,961 histogram updates, seven complete maps, startup, secured shutdown and the seven-worker cap remain. Exact-code profiles and stage diagnostics remain separate from primary timings.
