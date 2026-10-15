# Bounded extension build, layout and load

This source draft schedules four serial processes and no benchmark. Its 13 pure
test methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). No native command in this
stage has been executed. A concrete toolchain
intake and independent source approval are still required; no plan or successful
qualification receipt is supplied here.

The original SDK generation exited unsuccessfully after producing its headers.
The [closed failure](../sdk-generation-v1/failed-generation-closure-review-v1.json)
and [output-reuse review](../sdk-generation-v1/generated-output-reuse-review-v1.json)
remain separate immutable inputs. All 29 retained generated files and the whole
saved source/output inventory are replayed under the original common mutex and
four prior durable leases. No generator reruns and no producer status changes.
Only the 29 explicitly reviewed generated names use their recorded final bytes
instead of their historical pre-generation copy pins.

## Four commands

1. Compile the [corrected general extension](clbg_primitives.c) into a fresh
   dylib, retaining a complete `-MD` dependency rule and linker map.
2. Compile [layout-probe.c](layout-probe.c) against those same complete generated
   SDK headers, Clang resource headers, macOS SDK, GMP and PCRE2-8.
3. Run the probe. Its static assertions cover the actual generated argument,
   frame, event/request and API-table layout. It loads the new dylib, resolves
   `RX_Init`, `RX_Quit` and `RX_Call` back to that image, and records actual
   loaded image names plus the GMP/PCRE2 runtime versions. It does not call the
   extension without an interpreter API table.
4. Start the retained Rebol interpreter and run [load-smoke.reb](load-smoke.reb).
   The unchanged original loader checks the exact nine commands. The smoke uses
   ordinary signed arithmetic, byte matching, fixed formatting and IO, including
   bytes `00`, `80` and `ff`. Expected stdout is those three raw bytes followed by
   `ok extension-load-v2` and LF. Stderr must be empty.

The nine general commands are `gmp-add`, `gmp-subtract`, `gmp-multiply`,
`gmp-floor-divide`, `gmp-compare`, `pcre-find`, `read-stdin-chunk`,
`write-stdout` and `format-fixed`. They are not nine additional processes.

Compilation has a 300-second deadline per process; the probe and interpreter
each have 30 seconds. Every group has a 2-GiB RSS guard, 64-MiB capture/file
limit and five-second cleanup deadline. The frozen owned observer is privately
reused; a new session, direct-child reaping and an empty owned process group are
required. Failure stops the sequence without a retry. A fast, already-owned
zombie may have no live RSS sample: that derived value is null and memory
qualification remains false. Signals are masked while transferring a returned
capture into the ledger and during final evidence retention.

Static Mach-O dependency checks run before either built image executes and
again when validating the probe. Every non-OS image must already be in the
reviewed intake. The probe's loaded images are observed directly; the
interpreter's complete loaded-image set is **not** observed. OS/dyld-cache images
are recorded by install name, without an invented file hash. Source/build
equivalence of the retained interpreter remains unproved.

## Required intake

The controller accepts an explicit JSON file and SHA256 for each prerequisite.
Missing fields, draft statuses, unbound headers, unknown images and changed
named resolutions fail closed. No receipt is inferred from installed paths.

`rebol-extension-build-source-review-v1` must have status
`source-reviewed-awaiting-native-build-layout-load`, the exact ordered
`commands` above, `sdk_output_reuse` as the absolute reuse-review path and its
retained SHA, and a `files` map from repository-relative paths to SHA256 for
`rebol_extension.py`, `test_rebol_extension.py`, the corrected C source, both new
probes and this document. All seven native/work/count/timing/chart gates named
in the controller remain false. This approval must follow source review and
the recorded pure fault tests; it cannot claim a completed build.

`rebol-extension-concrete-toolchain-intake-v1` must have status
`reviewed-concrete-compiler-sdk-and-library-inputs` and contain:

- `source_review`: the exact absolute reference supplied to the controller;
  `target`: `arm64-apple-macos11.0`; `actual_loaded_images_observed`: false.
- `tools`: exact physical path/SHA pairs for `clang`, `linker` and `runtime`.
  Runtime must be the retained Rebol 3.22.1 binary already bound by generation.
- `include_roots`: physical paths for `rebol` (the retained generated SDK's
  `src/include`), `clang_resource` (the resource `include` directory),
  `macos_sdk` (SDK root), `gmp` and `pcre2`. `input_pins` must bind all selected
  headers and linker inputs, the three frozen loader/common/spec identities and
  any required startup inputs. Actual compiler dependency rules must contain
  only pinned inputs. Header files consumed by the compiler are rechecked.
- `libraries.gmp` and `libraries.pcre2`: physical image path/SHA,
  `runtime_version`, and a `source_provenance` path/SHA. Each provenance record
  must have status `reviewed-exact-library-source-and-installed-image` and an
  `installed_image` pair equal to the selected library. These are general
  primitives; no benchmark algorithm is supplied by a native helper.
- `compiler_version`, `linker_version`, `sdk_identity`: exact saved JSON
  observation references. `declared_image_closure` must equal the retained
  static Mach-O reader's closure for Clang, linker, interpreter and both library
  images in that order. `unavailable_inputs` records absent lookup/startup
  candidates that must stay absent.
- `prior_leases`: the exact four paths declared by the controller, each with
  its observed device/inode. The common mutex is separately fixed to inode
  79859134. Its descriptor is inherited by each native process and remains held
  through cleanup and terminal creation.

The native intake must review actual compiler/linker version receipts, resource
and SDK selection, header/library source provenance, named-path resolutions and
the recorded OS boundary. Arbitrary extra compiler flags, PATH lookup and
ambient DYLD/compiler include variables are not accepted. The fixed compilation
uses C11, `REB_EXT`, `TO_MACOS`, generated `gen-config.h`, `-nostdinc`, explicit
include roots, an explicit linker and absolute GMP/PCRE2 images. The original
fixture specification is retained as history; this plan records its C revision
and the independently reviewed output reuse instead of modifying old pins.

Both compile commands use `--no-default-config` to disable Clang's default
configuration files, as specified in the
[Clang configuration documentation](https://clang.llvm.org/docs/UsersManual.html#configuration-files).
The installed Clang 22 configuration selects `MacOSX26.sdk`; that ambient
selection must not contribute to this explicitly selected toolchain. The
scheduled `-isysroot`, resource directory and linker remain explicit. Before
preparation, retain a bounded `-###` observation of the exact compiler argv to
check those selections and implicit inputs without compiling or linking.

## Execution after prerequisites close

Use the retained Python interpreter with `-I -S -B`. From the original evidence
checkout, replace every uppercase placeholder with an independently reviewed
absolute path or digest; these examples are not prepared plans.

```sh
PYTHON -I -S -B tools/qualification/rebol_extension.py prepare \
  --toolchain-intake INTAKE.json --toolchain-intake-sha256 INTAKE_SHA \
  --source-review REVIEW.json --source-review-sha256 REVIEW_SHA \
  --plan /private/tmp/mech-benchmark-completion/experiments/rebol/extension-api-v2/plan-v1.json \
  --output /private/tmp/mech-benchmark-completion/experiments/rebol/extension-api-v2/run-v1

PYTHON -I -S -B tools/qualification/rebol_extension.py run \
  --plan /private/tmp/mech-benchmark-completion/experiments/rebol/extension-api-v2/plan-v1.json \
  --plan-sha256 REVIEWED_PLAN_SHA
```

Preparation hashes only while holding the original leases and starts no native
process. The prepared plan must receive a separate review before launch. Use a
fresh owned durable job around the exact run argv when launching unattended.
Each capture, dependency rule, linker map and built image is retained, including
failures. Finalization compares exact validated artifacts and serialized report
bytes after input replay and then rechecks named leases before writing terminal.
FIFO/special artifacts are not opened; readable failure evidence is preserved.

Successful capture is not automatic ABI or primitive qualification. Independent
review must disposition actual layout, exports, image/input joins and all smoke
outputs. The separate 18-case primitive suite, all-256-byte/chunk/short-IO cases,
GC observations, benchmark correctness, required work, complete source counts,
timing and chart admission remain pending.
