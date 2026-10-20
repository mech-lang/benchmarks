# Exact Nim preencoded formatter capture

The [terminal record](terminal.json) reports a successful native evidence capture
for `knucleotide:nim-knucleotide-preencoded-v1`, **pending independent review and
a separate additive formatter overlay**. No application source was evaluated,
semantically compiled, benchmarked or changed. No catalog/publication or sealed
importer was changed. The shared timing lock was released after the processes
exited.

Observed formatted application physical LOC: **66** under
`nonblank-noncomment-physical-lines-v1`. This result is measured from this exact
source, not inferred from its parent count:

- Input SHA-256: `b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b`.
- Both output SHA-256 values: `f89f1d009db71981a321cb7d5c2137569eb53e3edcc8b164bd4e061c300ec0c2`.
- `nimpretty` SHA-256: `cdf07fca977cfcfbeceb0189317657280ea89b11bed7220524bfef66db862cd5`.
- Native verifier source SHA-256: `941cdbc64879ab62b41314ac31efce433f61474c980d99da3036e03d429e8a01`.
- Native verifier binary SHA-256: `2c866a513395f7ddf4116098dee4fe81de5a0d372384f2363c1b88102e910890`.

The [capture worker](../capture_window.py) held the common native-work lock
nonblocking throughout distribution verification, version probe, formatting,
trusted verifier build and input parsing. It rehashed all **6,770** files in the
existing exact distribution restoration map. Native processes inherited the
lock descriptor, had distinct owned process groups and bounded timeouts; each
command, environment, cwd, time, exit code and raw stdout/stderr hash is saved.
No timeout or native failure occurred in this run. Failed stages would retain
their raw streams and a failed terminal record.

`version.stdout` contains the formatter's exact `0.2` result. `format.json` and
`format-again.json` use the previously reviewed `--indent:0 --maxLineLen:80`
arguments with separate outputs; [the initial plan](../nim-plan.json) pins the
identical historical configuration and native tool sources. The original copy
remained unchanged. Both formatted files are retained and byte-identical.

[The trusted verifier](parse_proof.nim) imports the pinned raw compiler parser
and lexer. Its build compiles **tooling**, not the application source. The helper
never calls the semantic compiler pipeline, resolves application imports,
expands application macros, evaluates `static` code or runs source filters.
It parses and tokenizes the original, first output and second output. The full
saved `native-proof.stdout` shows identical AST node kinds/ordered children,
identifier/literal payloads, **614 significant token payloads**, and comment
streams, with zero native errors. Source positions and indentation are omitted
from the comparison; token kinds and literal/identifier values are preserved.
No singleton statement-list normalization is used. This is an exact-source
preservation result, not a whole-Nim parser or formatter certificate.

The physical adapter calls the exact previously reviewed Nim mask in
`foreign_future_mask.py` (SHA-256
`3b9a5c498459e5ae3ed04695faef938bbd15080c2c47ac1010ef87fb964cabd5`)
directly, rather than importing unused owner modules and their historical
dependency graph. For this non-BOM source it is the same lexical operation as
the retained `mask_nim` wrapper; mask diagnostics are empty and mask/source
lengths agree. It counts nonblank masked rows only and invokes no normalized
owner counter. The direct adapter and missing broader new adversarial fixture
batch need explicit review before admission. The native source-specific equality
and idempotence evidence is complete; generic helper/whole-language claims are
not made.

The worker releases the common lock before returning. A later overlay must bind
these bytes, the exact catalog source/role and producer/runtime/config/count
evidence, retain all earlier formatter totals, and prove all source/timing and
retained/logical LOC fields unchanged. Until that review, this packet adds no
published formatter coordinate.
