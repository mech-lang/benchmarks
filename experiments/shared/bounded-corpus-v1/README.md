# Shared bounded workload corpus

This corpus supplies independent inputs and expected outputs for the Scala and
TypeScript implementations. It contains 149 cases: 142 successful outputs and
seven invalid-IUPAC rejections. Preparing the corpus executes no subject program
and establishes no new language's correctness or timing.

The [builder](build.py) retains 78 cases from the closed original conformance
corpus and 15 supplemental cases, with their saved reference and validation
hashes. It also generates the 54 independent reverse-complement fixtures and
adds handwritten zero-size Mandelbrot and fannkuch outputs. Original evidence
is preserved; generated files use repository-relative provenance and local
paths so native checks can consume the same input bytes in both languages.

Coverage includes all ten workloads, complete outputs, non-byte-aligned PBM
rows, pi row boundaries and leading zeroes, FASTA RNG/wrapping boundaries,
exact THREE record selection, frequency ties, regex alternatives/replacements,
and reverse-complement record, byte, line-ending and buffer boundaries.
N-body retains the established two-finite-energy-lines tolerance of 1e-8;
the other successful cases require complete byte equality.

Invalid reverse-complement cases record the offending byte in reverse traversal
order. Their expected nonzero exit is only part of the check: each language's
adapter must also verify its own error diagnostic and partial-output policy.
No Prolog-specific exception text or partial output is imposed on Scala or
TypeScript. These seven adapter checks remain unqualified until native runs.

The [Scala/TypeScript output checker](../../../tools/qualification/scala_typescript_outputs.py)
implements those proposed stream contracts separately from native supervision.
TypeScript's explicit catch must exit 1, write the offending-byte message to
stderr and retain the already-written `>r` header. Scala's direct JVM main must
exit 1 with the matching `IllegalArgumentException` and subject stack, while its
local buffered output remains unflushed for these short rejection inputs.
The pure checker tests include truncation, incorrect PBM padding, altered
expectations, lost energy lines, wrong errors and abnormal exits. Synthetic
checker tests do not establish that either runtime actually behaves this way;
native runs must verify these contracts against the exact compiled sources.

Regenerate into a fresh directory:

```sh
python3 -I -S -B experiments/shared/bounded-corpus-v1/build.py --output /tmp/bounded-corpus-review
```

The retained data is in [cases/manifest.json](cases/manifest.json). Future runs
must bind the corpus hash, exact compiled artifacts, runtime and environment,
then execute cases serially under the existing timing mutex with bounded process
and output limits. Correct output is separate from required-work checks, source
counting and full-input measurements; none of those gates is granted here.
