# Exact quoted user-error output

The retained `revcomp:extended-invalid-space` process rejected its input correctly: normal exit 1, no stdout, and exactly 53 bytes of stderr:

```text

** User error: "Unsupported revcomp sequence byte"

```

The frozen output checker expected the message without quotes and therefore stopped the bounded continuation. The new `tools/qualification/rebol_outputs_quoted.py` changes that exact diagnostic literal and its explanation only. All 142 success contracts, seven rejection inputs, exit and stream requirements, oracle metadata and qualification flags remain unchanged. Unquoted messages, extra context, other errors and partial stdout are rejected. The original checker, native receipt and failed producer report remain intact.

The retained source explains the quotes. `src/boot/errors.reb:234–238` defines `User.message` as `[:arg1]`; `src/core/c-error.c:411–415` stores the user string in `arg1`. `Mold_Error` passes the error frame to `Form_Block_Series` (`src/core/s-mold.c:1165–1175`). The latter resolves the get-word in that frame and calls `Mold_Value` with `molded=true` (`s-mold.c:928–933`). `Mold_String_Series` then emits the short message between double quotes (`s-mold.c:448–466`). The earlier source prediction missed this bound-value formatting step. These paths are relative to the retained SDK source tree; they explain this formatting and do not establish runtime-source equivalence.

The retained capture may be accepted separately after the corrected checker is independently reviewed and its existing native ownership, input and artifact closure is verified. That decision must reference the original plan, failed report, terminal, independent failed-stage closure and exact five capture files. It must retain the failed observer and producer statuses rather than rewrite them. No process needs to be repeated for this acceptance.

The source approval schema is `rebol-quoted-rejection-checker-source-review-v1`, with exact checker/test/README and frozen-checker pins, retained formatting-source references and a pure-test result. The separate actual acceptance schema is `rebol-retained-quoted-rejection-review-v1`; its status is `exact-retained-revcomp-rejection-qualified`, and it names only the existing `revcomp:extended-invalid-space` capture. Its `output_validation` is the new pure checker's result. Broader bounded correctness, source work, counts, timing, chart admission and runtime-source equivalence remain false. The eight unstarted cases require their own continuation.

Focused pure tests check the retained quoted bytes, rejection of the old prediction and every extra-output or exit mismatch, unchanged successful binary and signed-nanounit contracts, and the exact implementation difference. Test execution and review are recorded separately; no native execution is part of this packet.
