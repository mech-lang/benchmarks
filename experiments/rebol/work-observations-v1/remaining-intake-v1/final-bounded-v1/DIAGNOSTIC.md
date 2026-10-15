# Complete-map diagnostic resource failure

The original knucleotide main completed its exact 243-byte benchmark output. The following diagnostic, `stats/dump-series -1`, exceeded the 512 MiB process-group RSS limit before writing its map sidecar. This remains a failed diagnostic; correct benchmark stdout alone does not qualify the requested complete-map observation.

The retained [process receipt](run-v1/02-knucleotide-arbitrary-widths/process.json) records PID/PGID 18005, birth `1792046783.723100`, observed RSS 538,181,632 bytes against a 536,870,912-byte limit, signal 9, exit -9 and successful direct-child reap. Its SHA-256 is `9b632fb607d865dde96322ff107885a22b67cefb7f29b52b7d8d2233f95212ed`. The [243-byte stdout](run-v1/02-knucleotide-arbitrary-widths/stdout.bin) has SHA-256 `78e220a584e4ea619d9ca9b6feff7354cd4950c018b840ffd5f74287117dd930`; the [2,197,930-byte stderr](run-v1/02-knucleotide-arbitrary-widths/stderr.bin) has SHA-256 `04725cb7194ba31eec83775c4f3a46273af644ecac91737e045be8cf4b4368af`. No `observation.tsv` was produced. The stderr ends while formatting unrelated line-editor and console functions.

The source supports a concrete explanation for why this diagnostic is too broad. `core/n-system.c:195–198` calls `Dump_Series_In_Pool`; `core/m-pools.c:937–978` walks every live series, with no seven-map filter or aggregate work limit. For value series, `core/d-print.c:373–398` molds every value in the entire tail. `core/s-mold.c:1698–1707` invokes molding before its final per-value output truncation; some individual mold routines also check their limit, but this is not a total allocation bound. Molding can allocate temporary series through `Mold_Binary` → `Encode_Base16` → `Prep_String` (`s-mold.c:681–707,154–174`; `f-enbase.c:915–942`) and expand the shared mold buffer. The allocator queues collection (`m-pools.c:543,601`), while evaluator signal handling performs it (`c-do.c:862–864`); the dump loop contains no such evaluator checkpoint.

These paths explain resource growth during a global formatting operation. They do **not** identify the precise allocation responsible for the observed RSS, prove a leak or establish a recursive allocation defect. The closed capture has no allocation trace. Neither the seven actual maps nor the benchmark's normal execution is shown to require this much memory.

The minimal replacement is a separate diagnostic that runs the same unchanged main, omits the global dump and directly iterates all seven actual maps into the existing complete key/count sidecar. Retained `core/n-loop.c:391–395,462–478` reads the map's existing backing values during `foreach`; it does not first copy the whole map. A new consumer must independently check every key/count and window total, exact original stdout, normal exit zero and empty stderr. Final capacities, pointer identities, hash-bucket sizes and a growth trajectory must remain explicitly unobserved. Allocation/growth behavior can remain a separate static source finding. The original failed capture and successful tree/pi observations are preserved; no repetition of those successful observations is needed.

All runtime paths above are relative to `experiments/rebol/sdk-generation-v1/work-v1/source/src/`. Exact source identities used for this analysis:

| File | SHA-256 |
| --- | --- |
| `core/n-system.c` | `76d5c3a46bbf95ed84f2e4858437ed5221e83c12be49596f714bf2e440e1d8cc` |
| `core/m-pools.c` | `ed531d8c0a4a25982f9bcaf14857bbdfeb9fd9c1788ab2ff25ce1b3c53581a64` |
| `core/d-print.c` | `8518426832e32da49f21dc4af19c8c43f6bdb9e55033aa29dc2c1408aaffb6a7` |
| `core/s-mold.c` | `4f08f9f088b4af9096195b050107095bf0ffe04c12c0bac307aef97d2deebf43` |
| `core/f-enbase.c` | `2440af0836dfdc492f348f104553955967f92ffa1b5d751b9611efa0f3e19c07` |
| `core/c-do.c` | `5aa1e3c9f768086382759232ed974bd052a04861fe20956426749c814b57e446` |
| `core/n-loop.c` | `139d241bdf57a514f3a3b4348e649b3d182afb5e9c865e86136c708c06ee6294` |

The preserved wrapper is `experiments/rebol/work-observations-v1/knucleotide.reb`, SHA-256 `63e5425df08da872e7154d40932980321784cefe2dd7c5ac2832cb3d073e858a`. This note records a source-only diagnosis and a proposed narrower observation, not a successful replacement run or broader qualification.
