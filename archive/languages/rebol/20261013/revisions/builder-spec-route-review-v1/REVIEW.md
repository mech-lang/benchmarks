# Actual retained Builder route to the Rebol macOS ARM64 spec

This review selects the unchanged official Builder asset captured by the closed
intake, new-repository root receipt SHA
`1f11a2fb754a9329fe524a77e5436c94f39ee9aed186231f634f113e7fc16caa`.
The actual intake preserved2,133 pins,898 exact source copies and four owned
native0 commands, worker23888/target23894. Its banner is Builder0.21.2 with
Rebol3.21.15, from the official0.21.15 asset. The later subject/generator
candidate remains Rebol3.22.1; source/binary build equivalence and independent
Git-tree verification are not claimed.

The source review reads the complete retained core `Siskin/siskin.reb`
(2,727 lines), `source-copy/make/rebol3.nest` (2,076), pre-make.r3 (309),
prebol.reb, and import/startup modules. All digests in the resulting review
come from the actual intake's source pins and are reverified under common.
No source parser manufactures a resolved spec; Builder must produce its own
raw spec through the unchanged frozen controller and explicit launcher.

The exact argv is the official retained `tools/siskin`, absolute unchanged
copy `make/rebol3.nest`, `--test`, `%rebol3-bulk-macos-arm64`. Private HOME,
REBOL_HOME/install/temp, fixed system PATH, C locale and CI are reused from
the actual intake. No debug/update/run/script/force-compiler option is supplied.

The route is source-backed:

- Core30–33 imports prebol/msvc/xcode/mmake; startup `siskin-do.reb` invokes
  only `system/modules/siskin/do-args`, then quits. Imported project generators
  declare functions/data; their project/native actions require unselected
  force-compiler routes. Core's pre-3.17 compatibility branch is not selected
  by the actual embedded3.21.15 runtime. Linux `uname` is not a macOS path.
- Core `do-nest` loads/parses the exact nest, sets its root, and calls
  `clone-gits` before processing options. The nest's complete default/selected
  closure has no git/github/gits entry or linked nest; template gits is empty,
  so clone-gits exits before locating or invoking Git. `--update` is absent.
- Prebol/only preprocesses the nest and then selected blocks. The nest's
  directives are platform/architecture conditions, with no #do, file include,
  include-eval or command side effect. No target body is evaluated as host code.
- Core994–1044 sets `no-eval?` from test before selecting the target. The exact
  macOS target references target-macos, include-rebol-bulk, make-arm64-exe.
  Those expand ordinary source/config/platform/Bulk/ARM64 data plus the sole
  written pre-build file command `do %make/pre-make.r3 "$NEST_SPEC"`.
  The defined probe-spec action and block-do branch are not selected.
- Core1466–1474 stores NEST_SPEC and saves the genuine spec before pre-build.
  Core2007–2014 sends file-do to `eval-cmd/v` with the official boot executable;
  core2361 exits when no-eval and not force. This selected call has no /force.
  Thus the pre-make script, its header/boot generators and its security/file
  declarations are read as evidence but never run in this command.
- Compiler/resource/link/archive/strip calls also use ordinary eval-cmd and
  are suppressed by test; clean/delete/move obey no-eval. The target has no
  bundle/upx/gzip/custom action, and its output did not exist in the fresh copy.
  Tool lookup reads existence/PATH only; no compiler-version probe is selected
  because debug is false. No sign-identity query is reached for absent output.
- The build and store-object functions permit structural directory creation and objects.txt
  collection even in test mode. This is disclosed. Fresh spec.reb plus its
  same-directory objects.txt are allowed; objects, executable, generated header,
  other files, symlinks or install/temp files reject in frozen spec_only.

The concrete review uses the existing controller's exact status/schema fields:
spec-only authorized, generation false, no unresolved fields, empty linked
repositories, no selected force evaluation, every selected action suppressed.
These are bounded source judgments. They are not a claim of independent kernel
post-exec image observation or descendant count. The readonly review binds the
actual intake/report/body/durable digest, original old-host owner, Builder hash,
all actual Builder source files, the unchanged nest and pre-make hashes, and
this source note. The capture step also verifies all actual old/new-repository
closure bytes under common without rerunning any intake command.

The spec command remains exactly the previously frozen three-file packet.
The original-host durable launcher is required because spec_only demands the
retained intake owner's parent equal its original `continuation/owned-jobs`.
Its new output is original-host sdk-qualification/builder-spec-only-v1; the
actual release packet6f9c2f and intake23888/23894 are reused. No intake download,
extraction, copy, image, version, runtime or fixture repeats. All native work
waits on common inode79859134, which stays held through one120-second command,
full original898 preservation, added-file bounds and terminal pin closure.

```text
BUNDLED_PYTHON -I -S -B -u OLD_HOST/benchmarks/clbg/rebol-comparison/20261013/revisions/sdk-builder-spec-v1/controller.py
  --spec-only
  --packet NEW_REPO/benchmarks/clbg/continuation/jobs/rebol-builder-intake-release-v1/frozen-inputs.json
  --packet-sha256 6f9c2fd02f4140cb10de570feb7ddc1d26447e47cbb322db32d273bc8975c1ba
  --intake-review NEW_REPO/benchmarks/clbg/rebol-comparison/20261013/sdk-qualification/builder-spec-route-review-v1/review.json
  --intake-review-sha256 ACTUAL_COMMON_LOCKED_REVIEW_SHA
```

After a real native0/body/durable closure, preserve the complete raw spec and
stdout/stderr/startup/receipts at original paths and copy exact completed
evidence to the new repository. Then inspect all resolved product/version,
platform/architecture/ABI/config/source/mezzanine arrays and containment. A
later header route uses the selected actual pre-make script with the retained
subject3.22.1 runtime and reviewed actual spec in a fresh SDK generation copy;
that stage needs a separate reviewed source/root relocation plan because
pre-make writes generated headers/boot source. No generation, extension,
workload, primitive/work/LOC/timing or chart qualification occurs here.
