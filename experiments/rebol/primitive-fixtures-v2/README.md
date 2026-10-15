# Retained primitive fixture adapters

This source draft reuses all eighteen cases in
[`primitive-fixtures-v1/spec.json`](../primitive-fixtures-v1/spec.json), its six
Rebol sources and the unchanged diagnostic interposer. No new fixture case or
benchmark source is introduced. The adapter's 12 synthetic test methods and
fixed-stage controller's 14 methods passed on 2026-10-15 UTC, recorded in
[the initial pure-validation record](../../shared/pure-validation-20261015/post-prolog-pure-validation-run-v1/report.json). Their actual file and native
execution phases have not run.
The extension build, fixture plan and native qualification are still pending.

[`adapter.py`](adapter.py) supplies two hooks for the existing owned observer
and independent byte/sidecar checks. The new
[`rebol_primitive_fixtures.py`](../../../tools/qualification/rebol_primitive_fixtures.py)
provides explicit preparation and a fixed nineteen-process run. The observer remains responsible
for native identity registration, deadlines, RSS, stop signals, direct-child
reaping and empty process groups. The controller retains transport records and
every available sidecar on failures as well as successes, with no automatic retry.

## Existing coverage

| Existing cases | Source and required observation |
| --- | --- |
| Arithmetic | `arithmetic.reb`: signed arbitrary precision, floor division in all sign combinations, rejected operands, indexes, independent results and recovery after errors. |
| Formatting | `formatting.reb`: exact binary64 rounding, both signs, signed zero and precision limits under the declared C locale. |
| Regex | `regex.reb`: case-sensitive bytes, NUL and high bytes, indexes, empty/absent matches, whole-match bounds and compile/bounds/match-time errors. |
| Automatic GC | `gc-ownership.reb`: existing live binary/block results survive the fixed allocation churn; actual recycle count increases without forced collection or changed policy. |
| Nine regular-file inputs | `io-roundtrip.reb`, collect mode, lengths 0, 1, 255, 256, 32767, 32768, 32769, 65537 and 131089. The deterministic cycle contains all 256 values whenever length is at least 256. |
| Four ordinary pipe inputs | Collect, stream and indexed modes at 65537 bytes, plus empty indexed input. Concurrent feeding follows fragment cycle 1, 2, 255, 32767, 3, 4096; parent stdout reads request at most 13 bytes. |
| One injected pipe input | The same unchanged IO source plus `io-faults.c`: 65537 input bytes and the real 17-byte activation prefix. Exact output, two injected EINTRs per direction, positive short-call counters and exact read/write totals are all required. |

The original specification's recorded digest is
`3962c9c0782f4b8fae81555821e5ad5573ea4aa36b55a2d3396e570fa5bb2a79`.
Its [source review](../primitive-fixtures-v1/source-review.json) binds the fixture
files; its [corpus map](../primitive-fixtures-v1/bounded-corpus-map.json) separately
describes the 149 benchmark correctness cases. None of those 149 cases is part
of this eighteen-process primitive stage.

## Corrected extension prerequisites

The original specification remains immutable. Its original C pin and requirement
for successful complete SDK generation cannot be silently reused as descriptions
of the new stage. A future plan must explicitly bind:

1. The original specification and source review, with their original values.
2. The failed SDK producer, its closed failure and the separate
   [generated-output reuse review](../sdk-generation-v1/generated-output-reuse-review-v1.json).
3. The corrected [extension C source](../extension-api-v2/clbg_primitives.c),
   its actual built image, complete selected input/image closure and independent
   disposition of the four [build/layout/load captures](../extension-api-v2/BUILD.md).
4. The exact unchanged loader and facades. `MECH_CLBG_REBOL_PRIMITIVES` selects
   that reviewed image; `MECH_REBOL_FIXTURE_SUPPORT` selects the retained support
   directory. All eighteen fixture argv templates remain the original `-q -s`
   invocations. The retained `src/os/host-args.c` maps `q` to quiet and `s` to
   minimum security; this is an explicit original fixture choice, not the
   different argv used by the earlier smoke program.
5. One separately observed compilation of the unchanged `io-faults.c`, using the
   reviewed Clang/SDK and official dyld interposing header. Reuse the explicit
   toolchain selection and `--no-default-config` policy, dependency capture and
   static image checks; the old compiler template alone is not a concrete intake.

The fixed stage consists of one diagnostic interposer compilation followed by
eighteen serial Rebol processes. There is no eighteen-only or existing-interposer
reuse mode. This count excludes the prior four-command extension stage.
The interposer is absent from all ordinary fixture and benchmark
environments. Its activation must be observed, not assumed from loader variables.

The diagnostic compile uses the same reviewed compiler, explicit linker and
SDK roots, `--no-default-config`, `-D_DARWIN_C_SOURCE`, `-nostdinc`, dependency
file and linker-map policy. It does not link GMP or PCRE2. The selected SDK's
`usr/include/mach-o/dyld-interposing.h` and all consumed headers must already be
included in the concrete reviewed intake. Its declared Mach-O dependencies are
checked before the injected case; this is static dependency evidence, not a new
native image-inspection process.

## Required actual extension disposition

Preparation accepts `--extension-review PATH --extension-review-sha256 SHA`.
That future independent record must use schema
`rebol-extension-actual-build-layout-load-review-v1`, status
`qualified-exact-extension-build-layout-load`, `independent_review: true`, and
`extension_abi_qualified: true`. A missing file, draft, incomplete native stage or
source-only approval is rejected. No successful disposition is supplied here.

The record must contain exact path/SHA references named `plan`, `report`,
`terminal`, `toolchain_intake` and `source_review` under `references`; the original
fixture source review as `fixture_source_review`; `sdk_output_reuse`;
`corrected_source`; the actual `built_image`; `declared_image_closure`; and the
four exact path/SHA entries in `unchanged_facades`. `durable` contains its
physical job directory, complete regular-file artifact inventory excluding
`owner.lock`, and that lease's path/device/inode. The original extension plan,
all four captures, their actual controller parent, zero-exit durable terminal,
exact runtime and build inputs, and closed output inventories are replayed.
The extension target argv is the retained Python with `-I -S -B`, the original
`rebol_extension.py run`, and the exact plan path/SHA; the durable launcher's
own flags are separate. The durable terminal retains
`command-exited-zero-awaiting-report-review`; independent report and capture
checks establish the extension stage's approval.

Only that actual build/layout/load ABI approval is required to be true. Its
`full_primitive_fixtures_qualified`, `benchmark_correctness_qualified`,
`runtime_source_equivalence_proven`, `source_work_qualified`,
`canonical_source_count_qualified`, `full_timing_qualified` and `chart_admission`
remain false. It also records four native processes, zero benchmark samples,
and preservation of the failed SDK producer. This record does not rewrite the
older specification's successful-generator/original-C requirements: their
historical bytes and pins are retained, with the explicit output-reuse and
corrected-image disposition supplied separately.

`--source-review PATH --source-review-sha256 SHA` names an independent review of
this controller packet, using schema
`rebol-primitive-fixture-controller-source-review-v1` and status
`independent-source-review-complete-native-fixtures-pending`. It binds the
controller, its test, this README, adapter and adapter test under `files`, and
the exact unchanged `tools/qualification/rebol_extension.py` under
`dependencies`. `independent_review` is true and all seven admission gates listed
above are false. The helper is loaded from its original path/root and its
transitive frozen observer pins are retained.

## Observer integration boundary

The unchanged `tools/qualification/kotlin_bounded_v2.py` observer exposes
`launch=` and `transfer=` hooks. Use its privately loaded definitions as in
`tools/qualification/rebol_extension.py`; do not modify the frozen module or run
its original CLI. `julia_native_inspection.py` binds this observer to recorded
SHA256 `c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc`.
Configure the private observer for the specification's
180-second deadline, 512-MiB RSS guard and 1-MiB stream limits before a fixture.
Its overflow capture can retain a failing final read; that does not relax the
1-MiB acceptance limit. Keep the existing five-second cleanup deadline, common
mutex inode 79859134, original durable leases and the closed extension-stage
lease through capture, sidecar validation, final pin replay and terminal creation.

For each actual case, construct `Transport(case)`, or pass the handle yielded by
`regular_input(prepared_path, payload)` for a regular-file case. Pass the bound
`launch` and `transfer` methods to the observer. The regular input context must
surround the whole observer call, including cleanup. The handle is unbuffered;
its actual OS offset, size, inode and regular-file type are checked before spawn.
The launch hook substitutes only that stdin descriptor and immediately returns
the observer's `Popen` result. It performs no fallible post-launch work before
the observer records native ownership.

The pipe transfer checks actual parent endpoint types. Both ready events and
stalls call the existing kernel/resource polling hook against the same absolute
deadline. Partial writes advance by their actual return value and finish the
current fragment before advancing its cycle. The record counts successful
transfers, would-block/interrupted calls, EOF and EPIPE separately. Parent read
and write observations do not assert the extension's syscall sizes; only the
independent injected-call sidecar can support that claim. An early EPIPE fails
and lets the observer retain exit/cleanup evidence; EOF does not suppress exit
status or the remaining input checks.

The controller retains actual transport records in `finally`, opens sidecars
with the existing physical regular-file guards, and binds their exact bytes
before decoding. It joins each native capture to those observations and stops
at the first failure. Missing sidecars never become inferred successful
observations. Actual sidecars remain available even if output validation fails
before their values are decoded. No later case is attempted after that failure.

It retains all eighteen input byte files, compiler dependency/map/image outputs,
five observer files per attempted process, fixture transport records, GC/IO
sidecars and the injected-call JSON. A complete stage requires exact expected
file membership and bytes. The finalizer binds the serialized report, replays
all physical inputs and prior SDK/extension/durable inventories, compares the
current output inventory again, then verifies every named lease before writing
the exclusive terminal. The outer helper's lease list remains unchanged; the
extra closed-extension lease is held in a separate combined list until its own
final check.

## Future preparation and execution

After the actual extension and controller reviews exist, use fresh plan/output
paths under this packet. The following variables denote real reviewed files
and their exact digests; they are not successful evidence placeholders:

```sh
PY=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
E=/private/tmp/mech-benchmark-completion
"$PY" -I -S -B "$E/tools/qualification/rebol_primitive_fixtures.py" prepare \
  --extension-review "$EXTENSION_REVIEW" --extension-review-sha256 "$EXTENSION_REVIEW_SHA" \
  --source-review "$FIXTURE_SOURCE_REVIEW" --source-review-sha256 "$FIXTURE_SOURCE_REVIEW_SHA" \
  --plan "$E/experiments/rebol/primitive-fixtures-v2/plan-v1.json" \
  --output "$E/experiments/rebol/primitive-fixtures-v2/run-v1"
"$PY" -I -S -B "$E/tools/qualification/rebol_primitive_fixtures.py" run \
  --plan "$E/experiments/rebol/primitive-fixtures-v2/plan-v1.json" \
  --plan-sha256 "$REVIEWED_FIXTURE_PLAN_SHA"
```

The second argv can be supplied unchanged to the existing durable launcher
with the original repository as cwd. Preparation starts zero native processes;
execution starts at most nineteen, serially. The compile has a 300-second,
2-GiB, 64-MiB capture policy; each fixture has the original 180-second, 512-MiB,
1-MiB policy. Cleanup remains five seconds. A fast process observed only as an
owned zombie can retain a null derived RSS with incomplete/unqualified memory
observation; it cannot claim a measured zero peak.

A successful producer terminal has status
`nineteen-captures-retained-awaiting-independent-primitive-review`, not native
primitive qualification. Independent review must assess the actual saved
captures and closure before granting that separate gate. The 149 benchmark
correctness cases, exact source counts, required work, full timings and chart
admission remain outside this stage.

## Independent sidecar decoding

The retained SDK source at
`experiments/rebol/sdk-generation-v1/work-v1/source/src/mezz/mezz-save.reb`
uses `mold/only` and appends a newline. Thus the two sidecars are flat key/value
sequences without an outer block or header. The same source tree's
`src/core/s-mold.c` emits logical values as `#(true)` and `#(false)`.
The adapter accepts only the saved word keys, simple quoted strings, nonnegative
integers, these logical literals and a single integer chunk block. It does not
evaluate Rebol or accept a general program. Actual parser/native behavior remains
to be observed; a different representation fails instead of being guessed.

The IO sidecar requires the exact mode, byte count, EOF and positive chunks no
larger than 32768 whose sum equals the actual expected input length. The GC
sidecar requires the fixed 65536 allocations of capacity 1024, unchanged policy
and an actual increase in collection count. The separate JSON interposer record
rejects duplicate/unknown keys, noninteger counters, inactive injection, wrong
EINTR counts, missing short operations and incorrect byte totals. Its marker is
included in stdout and the 65554 written-byte total.

The 12 passing synthetic tests in [`test_adapter.py`](test_adapter.py)
cover sidecar grammar, exact bytes/counters, real-file descriptor offset, mocked
partial pipe writes, stalls, EOF and EPIPE without starting an interpreter or
compiler. The new
[`test_rebol_primitive_fixtures.py`](../../../tools/qualification/test_rebol_primitive_fixtures.py)
adds fourteen synthetic tests for fixed scheduling, disposition gates, inherited
lease lifetime, regular-input lifetime, transport/sidecar failure retention,
strict captures, no retries and terminal closure. Both suites passed in the
recorded pure run; source pin freezing, actual preparation and execution remain
pending. No source-work, LOC,
benchmark timing or chart gate is granted by this packet.
