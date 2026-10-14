# Trimmed Julia native ownership inspection

The next inspection decodes the retained optimized LLVM modules and disassembles
the existing object archive and final executable. This uses ordinary offline
LLVM tools; it does not attach a debugger, rebuild Julia, or execute a benchmark.
The [command draft](command-draft.json) contains eleven exact argument vectors
and artifact hashes copied from the existing receipts. The executable
controller is [julia_native_inspection.py](../../../tools/qualification/julia_native_inspection.py).
Its preparation and execution stages have not run. Tool hashes and dependency
closure are captured under the shared timing mutex during preparation.

The retained archive symbol record contains these actual `__text` definitions:

| Native owner | Object member | Section value |
| --- | --- | --- |
| `_clbg_entry` / `_jlcapi_clbg_entry_5207` | `text#0.o` | `0x0` |
| `_julia_clbg_entry_5209` | `text#2.o` | `0x7174` |
| `_julia_initialize_runtime_state_5297` | `text#4.o` | `0x6C6C` |
| `_julia_run_original_driver_5219` | `text#3.o` | `0x78A0` |
| `_julia_energy_5278` | `text#7.o` | `0x6D70` |
| `_julia_nbodyNOT._5294` | `text#4.o` | `0x656C` |

These are object-section values, not loaded process addresses. The draft retains
five additional generic-wrapper definitions. Defined symbols establish available
native bodies; they do not establish that the entry executes those bodies or
that their instructions implement the required work.

Run the nine `llvm-dis <member> -o -` commands for `text_opt#0.bc` through
`text_opt#7.bc` and `metadata_opt.bc`, then the two
`llvm-objdump --disassemble --reloc --syms <artifact>` commands. Each command uses
the frozen `kotlin_bounded_v2.py` owned-process observer, a fresh output directory, exact raw
stdout/stderr and start/active/final receipts. All eleven run sequentially under
mutex inode `79859134`; nonzero status, nonempty stderr, unsupported bitcode,
or an output limit stops the stage without automatic retry. Each command has a
30-second deadline, five-second cleanup deadline and 2 GiB process-group RSS
limit. This controller allows 64 MiB per captured stream, instead of the draft's
8 MiB, because offline IR, symbols and relocation text expand beyond their binary
inputs. The stdout pipe retains at most one additional 64 KiB chunk on failure.
An exceeded bound remains a failed retained attempt; it does not trigger a retry.
The tools only read the retained input artifacts. Their documented operations
are [LLVM bitcode decoding](https://llvm.org/docs/CommandGuide/llvm-dis.html)
and [object/image disassembly](https://llvm.org/docs/CommandGuide/llvm-objdump.html).

Preparation verifies the existing build/archive/link receipts and their inherited
file pins, all eleven input artifacts and the exact two LLVM 22.1.8 executables.
A bounded reader of the Apple Mach-O load-command format follows their declared
non-OS dependencies, retaining exact image bytes, named-path resolutions and
unavailable search candidates. Preparation, each command and finalization check
that those missing candidates have not appeared and changed the declared lookup.
It supports an arm64 image or one arm64 slice in a universal image, absolute
install names, `@loader_path`, `@executable_path` and unambiguous `@rpath` lookup.
Missing or ambiguous dependencies, non-OS aliases crossing into OS-managed
images, embedded dyld environment commands and unsupported image forms fail
preparation. OS install names are recorded as the
dyld/shared-cache boundary; this is a static declared dependency closure, not an
observation of all loaded images or arbitrary future `dlopen` calls.

Both stages require the unchanged, free common mutex. Preparation starts zero
native processes. The reviewed plan is external to the fresh run directory and
binds exact commands, environments, resource limits, input resolutions and pins.
Execution reconstructs that plan, verifies all inputs, invokes each command once
with empty stdin and a fresh local `HOME`/`TMPDIR`, and checks the complete closure
again before its terminal receipt. No ambient dyld or Julia settings are passed.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  /private/tmp/mech-benchmark-completion/tools/qualification/julia_native_inspection.py prepare \
  --plan /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/plan-v1.json \
  --output /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/run-v1

/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  /private/tmp/mech-benchmark-completion/tools/qualification/julia_native_inspection.py run \
  --plan /private/tmp/mech-benchmark-completion/experiments/julia-aot/trimmed-native-inspection-v1/plan-v1.json \
  --plan-sha256 <independently-reviewed-prepared-plan-sha256>
```

Each successful command retains `start.json`, `active.json`, `process.json`,
`stdout.bin` and empty `stderr.bin`: 55 command artifacts, followed by the stage
report and terminal receipt. Process identities, exit/reaping, empty groups,
serial intervals, stream hashes and saved artifact snapshots are checked.
Partial/failed evidence is retained and never promoted to a completed capture.
The small Python regression suite exercises saved metadata joins, synthetic
Mach-O dependency resolution, ownership failures and late artifact mutation;
it does not run LLVM, Julia or a real preparation.

The owner review must connect the exported entry to fresh state construction,
the two energy evaluations and the argument-dependent integration loop. Follow
calls across all eight shards, including generic wrappers, runtime initialization,
error paths and indirect targets. Compare LLVM function/debug ownership with
object relocations and final linked instructions. Record unresolved dispatch
targets individually; a name match or a missing textual `interpret` reference
cannot close them. The capture controller grants no semantic owner approval;
missing required definitions or unresolved calls must fail the subsequent review.

Fallback proof remains a separate, precise gap. The final serialized image has
not been inspected for `Method.source`, `CodeInstance.inferred`, native invoke
pointers or opaque-closure bodies. `sysimg_opt.bc` contains serialized image
data; converting its byte array to LLVM text would not decode those Julia
objects. The tagged [serializer](https://github.com/JuliaLang/julia/blob/v1.13.1/src/staticdata.c#L2585-L2690)
describes the relevant stripping and method-table traversal, but the recorded
`trim=1` and `strip_ir=1` options do not inspect the actual output fields.

Disabling the codegen library also leaves an interpreter dispatch route in the
tagged [fallback implementation](https://github.com/JuliaLang/julia/blob/v1.13.1/src/codegen-stubs.c#L36-L58).
The retained runtime symbol inventory marks all four interpreter entries as
local `t` symbols in `libjulia-internal`; an exported-symbol interposer therefore
has no demonstrated coverage of those paths. No such interposer is proposed.
After native ownership is established, actual serialized-field inspection and
a negative missing-native or verifier-rejected-dispatch case still have to close
the reachable fallback paths. Native ownership, IR removal, fallback closure,
AOT and chart admission remain false throughout this inspection stage.
