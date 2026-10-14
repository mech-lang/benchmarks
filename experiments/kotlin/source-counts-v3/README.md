# Kotlin PSI line-ending input revision

This revision explicitly converts CRLF and lone CR to LF before calling
`KtPsiFactory.createFile`. It retains the exact original bytes as `source.kt`
and requires PSI text to equal the normalized parser input. Unicode characters
and written escape sequences are preserved. UTF-16 ranges refer to the saved
`psi-source.kt`, as required by the unchanged validator.

The preserved v2 run passed environment initialization and emitted all forty
application source artifacts, then failed at `fixture--unicode-crlf`. Its saved
PSI retained the CRLF text and classified the final carriage return as
`BAD_CHARACTER` at UTF-16 range `[45,46)`. That is reader preprocessing evidence,
with no application-source fault established. [newline-review.json](newline-review.json)
binds the actual partial output and failed-run receipts.

The Java change is limited to the five-line normalization/create-file block.
V2's extension-storage initialization remains in place. `kotlin_loc_v3.py`
differs from the frozen v2 controller only in its packet path; all fourteen
fixture inputs are byte-identical. The original readers, controllers, plans
and failed runs remain unchanged.

The [completed native run](run-v1/report.json) accepted all forty authored
inputs and produced the expected outcomes for all fourteen fixtures. It used
one diagnostic compilation and one parser JVM. The [closure review](run-v1-closure-review.json)
verified all 192 saved artifacts and the retained input/runtime pins. No
application main was invoked. Fifteen pure tests additionally cover the
PSI/artifact checks, parser input wiring, mixed line endings, Unicode, written
escape characters and original-byte retention.

The retained preparation command was run under the common timing mutex:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/kotlin_loc_v3.py prepare \
  --plan experiments/kotlin/source-counts-v3/plan-v1.json \
  --output experiments/kotlin/source-counts-v3/run-v1
```

After reviewing the actual plan, use the same Python invocation with
`tools/qualification/kotlin_loc_v3.py run --plan PATH --plan-sha256 SHA256`.
The runtime closure, forty authored inputs, one diagnostic compilation, one
parser JVM, 30-second deadline, five-second cleanup, 2 GiB RSS and 8 MiB file
bounds are unchanged. Outputs must be fresh; no automatic retry occurs.
The [first source-unit replay](../source-units-v1/replay-v1.json) passed all
fourteen fixture assertions and exposed literal-body ownership gaps in the
counter. The [corrected replay and owner review](../source-units-v1/README.md)
resolved those gaps, and the separate source-count qualification now covers all
twenty forms. This reader's original candidate flags remain unchanged.
Formatted LOC has no formatter evidence. Source-work, timing and chart
qualification remain separate.
