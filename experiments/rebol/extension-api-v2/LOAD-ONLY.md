# Scoped load continuation

The original four-stage run compiled the extension and layout probe and captured
the layout/export/library observations. Its final Rebol load exited 1 when the
runtime denied reading the common fixture. That failed run, its durable command
and all six build artifacts remain unchanged.

The [load-only controller](../../../tools/qualification/rebol_extension_load_only.py)
replays those three successful captures and their source, compiler-input, image,
artifact and durable-ownership joins. It retains the original common and four
prerequisite leases and the closed four-stage job lease. It uses the original
extension image without compiling again.

The only command change is a `--do` block before the unchanged smoke script:
`secure` adds read exceptions spelled with the exact pinned `common.reb` and
`clbg_primitives.reb` paths. Rebol implements these as case-sensitive path-prefix
rules. Other process policies remain unchanged; this is not an OS sandbox or a
machine-policy change. The native-extension category already permits loading.

The new run has one process, fresh HOME/REBOL_HOME/TMPDIR, the original three input
bytes, exact expected binary stdout and empty stderr. It retains the original
30-second, 2-GiB RSS, 64-MiB stream and 5-second cleanup bounds. There are no
benchmark samples, recompilations or automatic retries.

Three focused synthetic methods passed in 0.001 seconds. They check the exact
permission argv, original image selection and preservation of the failed-stage
and successful-prefix identities. The [validation record](load-only-validation-v1/validation.json)
retains exact test and metadata-preparation captures. The
[prepared plan](load-only-plan-v1.json) binds 5,011 inputs and schedules one load
process without recompilation. Actual load execution remains pending.

A later independent combined disposition must reference both stages: the
original first three successful captures plus the separate successful load
capture, if obtained. It must preserve the original failed producer and durable
statuses. The primitive-fixture reader must consume this combined disposition
and both closed job leases explicitly; a synthetic four-success report must not
replace the original evidence. Layout/load approval alone does not qualify the
eighteen primitive fixtures, required work, source counts, timings or charts.
