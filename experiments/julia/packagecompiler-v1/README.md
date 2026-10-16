# Julia AOT executables

This workflow builds standalone benchmark executables with Julia 1.13.1 and
PackageCompiler 2.4.3's documented `create_app` interface. Each of the seventeen
distinct selected Julia source profiles has its own package and executable, so
profile-specific extensions to Base cannot affect another implementation.

The [build recipe](build_app.jl) uses exhaustive compilation (`--compile=all`)
and removes compiled-function IR (`--strip-ir`). It uses the standard application
launcher, without trimming or experimental compiler options. Compilation and
the small [training workloads](training-inputs.json) occur before measurement.
The scored process must construct its runtime state, read actual arguments and
input, perform the complete workload, write output and shut down.

Native validation runs the executable with `JULIA_LOAD_CODEGEN_LIB=0` and
`--julia-args --compile=no`. Complete expected output is required before timing.
Those restrictions disable runtime code generation; stripped benchmark method
bodies cannot supply an interpreted substitute. This does not claim that Julia's
runtime contains no interpreter or performs no launcher setup evaluation.

Validation and scoring explicitly use eight compute threads and no interactive
pool (`JULIA_NUM_THREADS=8,0`). The original fannkuch version 2 indexes per-worker
arrays with thread IDs; the extra interactive thread introduced by newer Julia
defaults would shift worker IDs beyond those arrays. Its build-time training
uses the same explicit pool configuration, preserving the original kernel.

[Source adaptation](source-adaptation.json) records original identities, exact
edits, standard-library dependencies and runtime initialization. All authored
application code, including module, entry and reset logic, contributes to LOC.
Build scripts and training workloads are compilation inputs, not scored runtime
helpers. The existing Julia JIT measurements remain a separate series.

All seventeen profiles are admitted as a separate Julia (AOT) series after 51 full-workload samples and 30 matched Mech controls passed independent reconciliation. Fourteen profiles supply the selected endpoints; all seventeen remain inspectable. The [results](RESULTS.md) include every workload, the FASTA slowdown and the limits of comparisons with retained JIT measurements. Existing measurements and fixed baselines are preserved.

Builds and measurements run serially under the shared benchmark mutex. The
[builder](../../../tools/build_julia_app.py) retains commands, environments,
input hashes, compiler logs and owned-process cleanup. Build receipts under `builds/` describe compilation; bounded validation, full timing and independent reconciliation each retain separate evidence.

References: [PackageCompiler apps](https://julialang.github.io/PackageCompiler.jl/stable/apps.html)
and [Julia compiler options](https://docs.julialang.org/en/v1/manual/command-line-interface/).
