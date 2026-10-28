# Exact timed binary differences

The full executables include the generated guest Object plus the Rust launcher,
runtime, standard-library monomorphizations, constants, exception data and linker
metadata. The rearchitecture changes that Rust implementation. Its generated
launcher shrinks from 580 lines to a 44-line image/symbol binding that invokes the
compiled shared launcher. The cleanup then shares more private Rust helpers and
changes module/source locations.

| Comparison | Executable file change | Rust/host code-section change | Function-start table change |
| --- | ---: | ---: | ---: |
| #934 → #935 | +33,104 bytes | +25,316 bytes | +52 |
| #935 → #939 | +16 bytes | +1,428 bytes | +16 |

The cleanup consumes existing segment padding, so total file-size growth does
not track code-section growth. Code-section sizes include alignment padding.
Constants, source-path strings, exception/unwind records, UUIDs, code signatures
and function addresses also change. Source deletion does not imply smaller
machine code: Rust optimization and linking act on the resulting runtime program.

The exact executable checks establish:

- The same release settings: optimization level 3, ThinLTO, stripped symbols.
- Identical versions/checksums for all 156 dependency packages. Resolved dependency
  features are identical; only the I/F generated application package name differs.
- Identical linked system libraries and the same generated ordinary guest files.
- All 129,296 bytes of guest text match across the linked executables after
  accounting for the same 76 address-fixup sites. Opcode/register bits at every
  fixup remain unchanged; only address-immediate fields differ.
- All four funded packed-loop bodies are fully byte-identical even after linking;
  these bodies contain no direct or indirect call instructions.

The guest block itself moves: its file offsets are 4,125,312 (I), 4,139,904 (A)
and 4,138,368 (C). The changed compiled Rust host code and layout explain why
complete-executable hashes differ despite identical guest instructions.

This audit does **not** establish which host or layout difference caused timing
variation. The four timing sessions did not meet complete performance acceptance.
Public executables intentionally omit Rust symbols, so section counts cannot
attribute growth to individual named Rust functions. No timed executable was
rebuilt, changed or retimed during this audit.

`I.json`, `A.json` and `C.json` pin the exact timed bytes, section sizes and all
14 guest functions. `supplemental-validation.json` records every fixup mask,
resolved-feature comparison and signature hash. The three Cargo metadata files
record the actual offline, locked dependency resolution. `executed-driver.py`
records the section/guest comparison. These are static diagnostic results, not
new timing observations or a performance qualification.
