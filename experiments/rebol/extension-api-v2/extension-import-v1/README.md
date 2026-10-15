# Explicit extension suffix continuation

The [retained source diagnosis](source-diagnosis.json) identifies `.rebx` as a
registered extension suffix on every branch of the runtime's file-type setup.
The preceding load reached the original `.dylib` but treated it as Rebol source
and exited 1 for a missing header. Both that failure and the earlier security
failure remain unchanged.

The [additive entrypoint](../../../../tools/qualification/rebol_extension_rebx_load.py)
uses the frozen load-only controller, observer and finalizer. Preparation creates
a regular `.rebx` copy of the original extension image and verifies every byte.
The original image, install name, dependencies, loader and smoke source remain
unchanged. Only `MECH_CLBG_REBOL_PRIMITIVES` changes; the existing process-local
read-prefix exceptions, three input bytes and exact stdout/stderr contract are
retained. No recompilation is scheduled.

The plan pins both image paths, the static dependency closure, both failed runs
and their durable evidence. It holds the common lease, four earlier prerequisite
leases and both completed extension-stage leases. The controller reuses the
three original successful build/layout captures and starts at most one new load
process, with the original 30-second, 2-GiB RSS, 64-MiB stream and 5-second cleanup
bounds. Run never recreates a missing prepared image, and a differing existing
copy is preserved and rejected.

Two focused synthetic methods passed in 0.002 seconds, checking exact image-copy
identity and that only the image environment value changes. No existing test
suite or native command was repeated. Actual extension load and the later
independent combined disposition remain pending; no fixture, work, count,
timing or chart qualification follows from preparation.
