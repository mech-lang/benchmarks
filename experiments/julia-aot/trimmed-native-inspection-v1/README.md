# Trimmed Julia native ownership inspection

The next inspection decodes the retained optimized LLVM modules and disassembles
the existing object archive and final executable. This uses ordinary offline
LLVM tools; it does not attach a debugger, rebuild Julia, or execute a benchmark.
The [command draft](command-draft.json) contains eleven exact argument vectors,
artifact hashes copied from the existing receipts, and the remaining execution
gates. No command in this draft has run. Tool hashes and dependency closure must
be captured under the shared timing mutex before execution.

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
the existing bounded process observer, a fresh output directory, exact raw
stdout/stderr and start/active/final receipts. All eleven run sequentially under
mutex inode `79859134`; nonzero status, nonempty stderr, unsupported bitcode,
missing definitions or an output limit stops the stage without automatic retry.
The tools only read the retained input artifacts. Their documented operations
are [LLVM bitcode decoding](https://llvm.org/docs/CommandGuide/llvm-dis.html)
and [object/image disassembly](https://llvm.org/docs/CommandGuide/llvm-objdump.html).

The owner review must connect the exported entry to fresh state construction,
the two energy evaluations and the argument-dependent integration loop. Follow
calls across all eight shards, including generic wrappers, runtime initialization,
error paths and indirect targets. Compare LLVM function/debug ownership with
object relocations and final linked instructions. Record unresolved dispatch
targets individually; a name match or a missing textual `interpret` reference
cannot close them.

Fallback proof remains a separate, precise gap. The final serialized image has
not been inspected for `Method.source`, `CodeInstance.inferred`, native invoke
pointers or opaque-closure bodies. `sysimg_opt.bc` contains serialized image
data; converting its byte array to LLVM text would not decode those Julia
objects. The tagged [serializer](https://github.com/JuliaLang/julia/blob/v1.13.1/src/staticdata.c#L2461-L2564)
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
