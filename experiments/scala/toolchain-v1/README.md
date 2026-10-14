# Scala 3.10.0 toolchain

The official Apple arm64 distribution was downloaded and verified against its
published SHA-256. The [retention receipt](retained-distribution-v1.json) records
the 101,870,221-byte archive and all 159 extracted files. Its pathing JARs refer
only to retained dependencies inside the distribution; no dependency resolver
or Scala CLI bootstrap was used.

The [native diagnostic report](native-v1/report.json) records four serial
processes: the retained JDK's version, the compiler's version, compilation of the
original parser transport, and compilation of the token-capture candidate.
All four exited successfully with empty stderr. The observed versions are
Temurin OpenJDK 25.0.4.1+1-LTS and Scala 3.10.0. All 400 inherited JDK file pins
and distribution inputs were verified before and after these diagnostics.

The direct compiler entry point is `dotty.tools.dotc.Main`. Its executable
classpath comprises the distribution's `lib/scala.jar` and
`lib/with_compiler.jar`; the complete resolved dependency list is retained in
the report. The diagnostics use eight active processors, G1, a 1 GiB maximum
Java heap, a 30-second process deadline, a 2 GiB observed process-group RSS
limit, and the existing common benchmark mutex. These are compiler/reader
diagnostics, not benchmark timing settings or measurements.

The generated reader classes and complete native receipts are retained under
`native-v1`. The first actual parser run is recorded under
[`source-counts-v1/native-token-capture-v1`](../source-counts-v1/native-token-capture-v1/).
Benchmark compilation, required-work qualification and full measurements remain
separate stages. The original release-selection record preserves its historical
pre-installation state.
