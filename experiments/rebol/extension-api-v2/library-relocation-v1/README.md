# Selected library install-name comparison

This additive source packet compares the selected GMP 6.3.0 and PCRE2-8 10.49
Homebrew bottle images with their installed counterparts. Source review is
complete. Its five synthetic tests passed on 2026-10-15 UTC, recorded in
[the follow-up validation receipt](../../../shared/follow-up-pure-validation-20261015/validation.json).
Comparison of the actual images remains pending; no library provenance approval
is granted by the synthetic tests.

The first intake attempt correctly stopped at whole-file equality: the GMP
header matched its bottle member, but the installed dylib differed. A subsequent
read-only byte comparison found 79 changed bytes in GMP and 261 in PCRE2. Their
`LC_ID_DYLIB` names replace `@@HOMEBREW_PREFIX@@` with `/opt/homebrew`. PCRE2's
identity command also shrinks by eight bytes; signature bytes differ as well.
The original failure and byte-range observations remain preserved.

Homebrew records these images in `linkage_files`. That is separate from
`binary_relocation_files`: its retained macOS relocation implementation changes
dylib identities and signs saved images again. The validator checks the bytes
directly rather than accepting any change described as relocation.

[compare.py](compare.py) accepts only the two selected thin arm64 dylib forms.
It requires the same load-command order, unchanged header fields other than
command-byte count, the exact identity-prefix substitution, unchanged remaining
commands, and zero padding after a resized command. All subsequent image bytes
must match. It independently verifies every primary CodeDirectory SHA256 code
page in both files; only the first code-page digest may differ in the signature.
The retained LLVM 22 `MachO.h` CodeDirectory declarations define that layout.
This proves neither signing authority nor equivalence to an upstream source
rebuild.

[test_compare.py](test_compare.py) covers both allowed identity forms, a changed
image body even with a valid replacement page hash, a stale hash, a changed
non-identity command, and unrelated signature/prefix edits. It passed with the
retained Python interpreter and `-I -S -B` at the recorded source identities.

The next extension intake must pin this comparator and its retained format and
Homebrew source references. Each new library provenance record must retain the
exact selected bottle digest/member, installed image digest, header equality,
`linkage_files`, and complete comparison result. The library image comparison
replaces only the unsuccessful blanket image-byte-equality check; header
equality remains exact. The existing `source_provenance` references and
`input_pins` fields carry these records into the unchanged extension controller.

The frozen controller, six-file build source review, original SDK failure,
generated-output reuse, runtime and native observers remain unchanged. The
four-command extension plan still requires complete tool/header/image intake
and separate review before any compilation or load observation.
