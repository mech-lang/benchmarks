# Current counting-loop inspection

`results.json` binds this disassembly to the complete machine-code section of
the timed frozen-map executable. `hot-offset-groups.json` maps the retained
collapsed profile groups to listed instruction addresses. A group may contain
several or undisplayed program counters; its observation count is not an
individual instruction's frequency or elapsed-time share.

The current generated entry retains SIMD table probing and full-key comparison.
Listed PCs include an entry-presence comparison at offset 33864, SIMD mask
extraction at 33612 and an entry-pointer stack reload at 35180. The last reload
duplicates the immediately preceding reload on both incoming count-store paths.
The entry also checks its existing cached-entry flag around later source map
calls. A known cache already avoids hashing/probing again; this inspection does
not establish three hash probes per source update.

The pinned upstream Rust source performs one `entry` operation per update,
initializes the first rolling window outside the loop, uses width-specific
integer keys and 32-bit counts, and shares a single preencoded input among its
seven workers. The retained Rust u64 existing-key path has 34 instructions,
including rolling-key construction, hashing, probing, comparison and update.
That is one inspected path, not a dynamic instruction count for all inputs.

Next general targets are cache-state facts across the proved source graph and
smaller loop-carried state. Later possibilities include peeling the first
window, hoisting invariant call checks without moving errors, and narrowing
storage only when source bounds preserve logical u64 behavior. No speedup is
assigned to these proposals before execution measurement.
