# Typed Mach-O roots for the Rebol extension stage

The first concrete intake stopped before compilation or native execution because
the retained static dependency reader required executable filesystem mode for
all roots. GMP, PCRE2 and libLTO are regular arm64 Mach-O dylibs with file type 6
and mode `0444`.

The [additive entrypoint](../../../../tools/qualification/rebol_extension_typed_images.py)
uses the unchanged extension controller and the frozen static reader's parser,
path expansion, pinning and OS boundary. Executable roots (type 2) still require
executable mode; library roots (type 6) require a regular physical file. Other
image forms remain rejected. This static walk does not establish actual loaded
images or source/build equivalence.

The intake and plan bind the adapter's exact source digest. The plan retains the
original controller identity and records the actual adapter entrypoint. Prepare
and run rebuild through that same adapter, preserving the original observer,
limits, leases, four commands and pending qualification gates. The completed GMP
and PCRE2 comparison records are reused only with identical pinned inputs; the
[original failed intake](../intake-v2-failure.json) remains intact.

Eight [focused pure tests](../../../../tools/qualification/test_rebol_extension_typed_images.py)
passed in 0.035 seconds. The [validation record](validation.json) binds the exact
source versions and original [stdout](test.stdout) and [stderr](test.stderr).
The tests use temporary synthetic images, cover permission/type distinctions and
unchanged graph output, and check source/plan identity and rejection paths. The
canonical files are exact copies of the tested sources; no test rerun was needed
for copying. Independent source review found no concrete blocker.

The subsequent [native stage](../run-v1/README.md) completed both builds and
the layout/export probe; its first interpreter load failed at an external
fixture read. That failure remains preserved. Before primitive fixtures consume
the combined results, their helper and exact durable-command checks must
recognize this adapter entrypoint and the separate load continuation.
