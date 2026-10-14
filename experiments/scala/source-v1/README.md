# Scala JVM source drafts

This packet contains one separate Scala source bundle for each of
the ten workloads. All ten are **source drafts**: no Scala compiler, subject JVM,
source reader or benchmark has run for this packet. No timing or source count is
admitted. The [manifest](source-manifest.json) identifies the source bytes and
the retained Java references used during adaptation. Reference timings are not
reused.

Each directory contains a self-contained `object Main` with
`def main(args: Array[String]): Unit`, the conventional JVM entry documented in
the [Scala main-method reference](https://docs.scala-lang.org/scala3/book/methods-main-methods.html).
Compile each directory separately; the ten `Main` objects are separate programs.
The target is Scala 3.10.0 on the retained ARM64 JVM, following the official
[current stable release](https://www.scala-lang.org/download/3.10.0.html).
The [toolchain selection](../toolchain-v1/selection.json) records this version
without claiming installation. Compiler dependencies, Scala runtime jars, JDK
and emitted classes remain to be retained and verified before execution.
Compilation must occur outside the timed fresh JVM invocation.

| Workload | Application work and general libraries |
| --- | --- |
| Binary trees | Separate `Node` per constructor call, recursive checks, stretch tree, repeated temporary trees and a long-lived root checked last; JDK executor for depth tasks |
| Fannkuch-redux | Factoradic chunk starts, complete permutation traversal, copied flip workspace, signed checksum and maximum; at most eight executor workers |
| FASTA | Authored repeat stream, weighted selection and continuous linear-congruential RNG across both random records; buffered JDK output |
| K-nucleotide | Exact THREE identifier, comments and case handling, seven newly constructed complete rolling-key maps at lengths 1, 2, 3, 4, 6, 12 and 18; Scala `mutable.LongMap` |
| Mandelbrot | Authored binary64 recurrence, fifty-step limit, PBM bit packing and zero unused bits; at most eight row workers |
| N-body | Fresh five-body state, momentum offset, both energy evaluations and argument-controlled pairwise integration loop |
| Pi digits | Unbounded Scala `BigInt` spigot; two independently evaluated general divisions before every candidate comparison |
| Regex-redux | All nine count patterns and five ordered replacements expressed in Scala, using JDK `Pattern`; at most eight executor workers |
| Reverse complement | New Scala record parser, preserved byte-valued headers, comments, CR/LF/CRLF, both-case IUPAC mapping, reverse traversal and sixty-column output |
| Spectral norm | Both matrix orientations, ten power-iteration pairs and final reduction; at most eight executor workers |

The parallel programs use `min(8, availableProcessors)` application workers.
Other workloads are sequential. This is not a claim about total VM, JIT or GC
thread counts. Worker failures are observed through futures; pools shut down in
`finally`. Input and complete output remain inside the future timing interval.
The new reverse-complement parser replaces the reference's chunk/header
assumptions; the Mandelbrot implementation handles non-byte-aligned widths;
K-nucleotide excludes THREE-like identifiers and sorts frequency ties by key.
Regex header cleanup explicitly excludes only LF from its character class,
matching the byte oracle even when a header contains CR or high bytes.
These are source-level properties awaiting native conformance.

Independent review covered all ten drafts and their stated workload structure.
The source/reference hash and manifest audit passed; compilation and native
conformance were not run. Reverse-complement invalid input currently raises a
Scala `require` failure. Its future rejection checks must retain and validate
the actual diagnostic and buffered-output behavior, rather than assume another
language's error bytes.

## Qualification still required

1. Retain the exact Scala compiler and dependencies, JVM, runtime jars, commands,
   diagnostics, class files and source-to-class ownership for every program.
2. Run the [149 shared independent cases](../../shared/bounded-corpus-v1/),
   including non-aligned PBM widths, all IUPAC symbols and record boundaries,
   exact THREE selection, full frequency maps and final pi padding.
3. Check required work in the actual compiled program. In particular, verify
   tree allocation and long-lived-root reachability after optimization, both pi
   divisions, seven distinct complete maps, and relevant JVM compilation/runtime
   evidence. Correct stdout alone does not prove those obligations.
4. Qualify a Scala-aware source owner reader. The
   [reader draft and 41 fixtures](../source-counts-v1/) are prepared, with parser
   APIs reviewed in the exact compiler source. Compilation, native transport and
   complete token coverage remain unverified. No existing canonical counter is
   assumed to understand Scala's methods, blocks, lambdas, patterns, interpolated
   strings, compound assignments or type syntax. Formatting LOC remains null
   until a separate formatter/AST-preservation check exists.
5. Measure all full-size workloads sequentially, with matched Mech controls,
   fresh JVMs, retained resource/exit/output records and independent result
   reconciliation before catalog or site publication.

Native preparation, compilation, inspection and measurement require exclusive
ownership of the common timing lane.

The adapted sources retain their upstream contributors. The
[Benchmarks Game license](LICENSE.benchmarksgame) accompanies this packet;
the [upstream notice](https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html)
identifies its terms. New application work remains within the Scala source
bundles and must count toward source size.
