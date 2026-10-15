# Rebol extension API revision

This unmeasured revision fixes binary result construction in the nine-command
general extension. It preserves the original extension proposal, all ten Rebol
mains, the loader, the primitive fixtures and every generated SDK file. No
extension build, load or native ABI qualification has occurred for this revision.

The SDK inputs are the 29 retained outputs identified by
[the generated-output reuse review](../sdk-generation-v1/generated-output-reuse-review-v1.json).
The generator's original exit remains a failure: the separate review permits
header inspection and later compilation from its exact retained outputs without
inventing a successful producer terminal or regenerating them.

## Binary result correction

The original `finish_binary` calls `RL_SET_CHAR` once per byte. In the retained
SDK, `reb-lib.h:643` dispatches that operation to `RL_Set_Char` in
`src/core/a-lib.c:893`. Its `SET_ANY_CHAR` macro, at
`src/include/sys-value.h:640`, marks the series as UTF-8 and calls
`UTF8_Replace_Codepoint` for a value above `0x7f`. That function, at
`src/core/s-unicode.c:409`, can expand the series before encoding the code point.
Consequently a raw input byte can become multiple output bytes. The original
capacity argument considered only the first append, so it does not establish
the claimed allocation-free path through the character setter.

[The revised extension](clbg_primitives.c) changes only its introductory comment
and `finish_binary`. It requires an empty width-one result with capacity for the
entire byte sequence and its terminator, then calls
`RL_EXPAND_SERIES(series, 0, length)` once. The generated API declares that entry
at `reb-lib.h:55` and its macro at line 410; `a-lib.c:590` forwards to the retained
`Expand_Series` implementation at `m-series.c:36`.

For these inputs, the implementation's `size + extra` is `1 + length`, and the
checked available space is at least that large. The allocating branch therefore
does not execute. The existing terminator moves to the new tail. The extension
checks the resulting extent, obtains storage through `RL_SERIES(...,
RXI_SER_DATA)`, copies exactly `length` bytes with `memcpy`, and writes the
terminator. It uses no private series-structure layout and no Unicode setter.
An empty result retains tail zero. The existing reserve limits and all arithmetic,
regex, formatting, IO-loop and native-resource ordering remain unchanged.

The fresh `Make_Binary` path (`s-make.c:37` and `m-pools.c:522`) creates width-one
storage with zero tail and bias. Even if the general expander's earlier head-bias
branch were reached, that branch changes the data pointer and extent without
allocating; the post-call extent checks and explicit terminator still apply.
The zero-delta branch returns without changing the empty result. The signed
byte limit keeps the extent arithmetic below the implementation's signed cap.

This is a source argument against the retained implementation, not a native
observation. The existing all-256-byte IO fixtures and chunk-boundary cases are
required to validate the corrected behavior after compilation.

## Header and return-path review

The retained `reb-lib.h` and `reb-lib-lib.h` agree on the function-table entries
used here: `version`, `make_string`, `expand_series` and `series`.
`RL_MAKE_BINARY` is the generated `make_string(size, FALSE)` macro. `REBUPT` is
the pointer-width unsigned type in the retained C99 definitions, so the data
pointer does not pass through a 32-bit integer.

The generated prototypes match `RX_Init(int, RL_LIB *)`, `RX_Quit(int)` and
`RX_Call(int, RXIFRM *, void *)`. The SDK defines a packed 16-byte `RXIARG`, a
16-slot `RXIFRM`, and the binary/integer/decimal access macros used by the
extension. The proposed arm64 layout checks remain compiler observations to
be collected; source declarations and the version guard alone do not prove the
running interpreter's ABI or its source/build equivalence.

The retained `f-extension.c` joins the return paths: `RXR_VALUE` converts the
returned binary series and its zero index; `RXR_BLOCK` constructs the two-integer
match interval after the extension has freed PCRE2 temporaries; `RXR_ERROR`
copies the static NUL-terminated diagnostic string; and `RXR_NONE`/`RXR_UNSET`
have their declared meanings. The nine command declarations retain their exact
original order and argument types. No workload recurrence, scan, replacement or
output assembly is introduced into C.

## Next native stage

After the common timing lane is free, prepare a bounded build/load stage that:

1. Binds this C input, the unchanged Rebol loader/facades, the failed generator
   receipt and its output-reuse disposition, and the complete selected SDK
   include closure. Preserve the original fixture specification as historical
   input; explicitly record this C replacement and the output-reuse prerequisite
   in the new plan instead of editing that specification's original C pin or
   requiring a fabricated successful generator status.
2. Resolves and pins the actual arm64 Clang, macOS SDK, GMP and PCRE2-8 headers,
   source provenance and linked images. Compile as an extension with `REB_EXT`
   and the selected macOS configuration using the complete generated headers.
   Do not substitute a handwritten function table or headers.
3. Records compiler layout checks for the argument/frame and API structures,
   the exact build command/output, exported entry symbols and the resulting
   image's dependency closure. No benchmark source executes during this step.
4. Loads the extension in the retained isolated interpreter and verifies all
   nine commands, then runs the separately reviewed ordinary byte, signed-GMP,
   rounding, PCRE2, error, GC and short-IO fixtures with exact process ownership,
   output and cleanup receipts. A failed case remains failed without an
   automatic retry or changed oracle.

The new source has not been compiled or tested. Canonical counts, full benchmark
correctness, required-work evidence, timing and chart admission remain pending.
