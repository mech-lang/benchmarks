# Janet invalid-IUPAC rejection qualification

The v2 source's seven captures retain only a generic invalid-nucleotide error.
They remain historical captures. The v3 source adds the offending normalized
ASCII byte and zero-based offset in the selected record's sequence. It preserves
the reverse traversal, complement lookup, output buffering and valid output.
No input byte is silently removed or replaced.

`rerun_revcomp.py` validates all 61 reverse-complement cases serially with the
unchanged owned-process controller. The 54 success cases match their complete
independent references. Each of seven invalid cases exits exactly 1, has the
expected partial stdout, and emits the explicit invalid-byte/offset diagnostic
with the Janet write-record/runtime stack. An unrelated nonzero exit cannot pass.

`rejections.py` independently parses records and comments, normalizes line endings,
uppercases ASCII bases and traverses in reverse with the standard IUPAC table.
It checks the frozen corpus's expected invalid byte, its independently computed
record offset, complete partial stdout and the complete language-specific error
shape. The case with multiple invalid bytes verifies reverse traversal order.
`test_rejections.py` replays all seven native captures and rejects zero exit,
empty or truncated diagnostics, unrelated errors, changed partial stdout and
changed offset-label diagnostics (42 deliberate corruptions in total).

All 149 bounded corpus contracts now pass across the seven unchanged v2 programs
and v3 regex-redux, spectral-norm and reverse-complement overlays. This packet
qualifies these explicit rejection contracts; it does not certify arbitrary
invalid input, source normalization, full-suite output or timing admission.
The original plan/manifests and failed regex capture remain unchanged.
