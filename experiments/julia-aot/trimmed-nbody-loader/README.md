# Trimmed Julia N-body loader check

The retained Julia 1.13.1 safe-trim executable produces the expected two energy
values for 1,000 integration steps and exits successfully. Its executable hash
is unchanged from the recorded link result. `report.json` identifies the input,
reference, binary, command, environment, process group, output hashes, and loaded
images; the raw output and loader diagnostics are retained alongside it.

The process loads `libjulia-codegen` and LLVM. Loading these libraries does not
establish that compilation occurred, and correct output does not establish AOT
closure. Native entry ownership, interpreter/JIT fallback observation, negative
controls, full-workload validation, and fresh measurements remain separate gates.
This check contributes no plotted timing sample.
