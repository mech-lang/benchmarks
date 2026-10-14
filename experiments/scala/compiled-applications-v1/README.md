# Scala application compilation and bytecode capture

The [controller](../../../tools/qualification/scala_compile.py) prepares the ten
retained Scala source bundles for subsequent native conformance. It compiles
each `Main.scala` separately with the verified Scala 3.10.0 compiler, then uses
the same retained JDK's `javap` to inspect every emitted class. The maximum is
twenty serial native commands: ten compilers and ten bytecode readers. No
application main runs in this stage.

Each compiler input is a fresh exact copy of the source-manifest bytes. The
complete emitted class and TASTy inventory, compiler command, diagnostics,
bytecode listing and source mapping remain available for independent review.
Application classpaths contain the application classes and the two retained
Scala library jars. Compiler dependencies are confined to the compiler command.
No package manager, dependency resolver, build script or network fetch runs.

The existing bounded observer owns each native process group and inherits the
common timing mutex. Its limits remain 30 seconds, 2 GiB process-group RSS and a
five-second cleanup deadline. Compiler JVMs use eight active processors, a
64 MiB initial heap, 1 GiB maximum heap and G1. These are preparation settings;
this stage establishes no future benchmark heap policy or full-input capacity.
Native failures retain their actual streams and stop the stage without retries.

Run only after source/controller review and when the common timing lane is free:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/scala_compile.py --output /private/tmp/mech-benchmark-completion/experiments/scala/compiled-applications-v1/run-v1
```

The output must be new. The controller checks the pinned compiler/JDK/source
inputs under the existing lock and checks inputs and validated artifacts again
after execution. All bounded-output, required-work, source-count, full-timing
and chart-admission flags remain unqualified. The next native stage is the
[149-case shared corpus](../../shared/bounded-corpus-v1/), followed by required
work/runtime review and serial full measurements.

The [pure tests](../../../tools/qualification/test_scala_compile.py) exercise
source substitution, duplicate workload, runtime dependency ambiguity, missing
or linked classes and failures in the saved process-closure contract. They do
not compile or execute any program.
