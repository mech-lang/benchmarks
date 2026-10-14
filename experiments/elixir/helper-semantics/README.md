# Compiled Elixir helper semantics

This unscored probe exercises the retained `Clbg.Support` BEAM module without
loading `Clbg.Main`. It checks size parsing, iteration boundaries, CR/LF splitting,
and 1,536 binary64 formatting cases against Python's independent float formatter.
Cases include negative zero, rounding ties and their adjacent values, subnormal
numbers, large exponents, and seeded finite bit patterns at six precisions.

A nonempty byte stream longer than two 65,536-byte input chunks passes through
the application helper's input and nested iodata output paths. The host must
compare every output byte with its input and require empty stderr, successful
exit, no remaining process group, and unchanged source, BEAM, and runtime hashes.
The repeated EOF read and unloaded benchmark module are checked in the process.
The supervisor regenerates the vector bytes with the pinned independent Python
generator before execution. It writes stdout and stderr directly to artifacts,
retains timeout and cleanup errors, and seals every available output in a terminal
receipt even when a check fails.

`generate_vectors.py` writes a new vector file and never runs Elixir. Running
`probe.exs` requires a reviewed, serialized supervisor, the original compiled
module directory, the vector file, and a fresh summary path.

`results-v1/report.json` records successful checks for all twenty retained
helpers, including complete binary I/O and all 1,536 formatting cases per
profile. Its terminal receipt retains the native results and unchanged input
hashes. `preflight-v1.json` records an earlier path check failure before any
native dispatch. These cases do not qualify algorithmic work, source counts,
regex behavior, or full benchmark timings.
