# Literal regex bytes in Rebol

Rebol consumes caret escapes while reading quoted strings. The original
primitive fixture's `"(?m)^b"` therefore supplied a control byte, causing its
multiline-boundary assertion to fail. The corrected `regex.reb` uses binary
`#{283F6D295E62}`, the exact bytes of `(?m)^b`, in both boundary cases.

The original regex-redux program also lost the negation caret from two
character classes. `main.reb` escapes those carets as `^^`, retaining the
intended PCRE2 patterns `<[^>]*>` and `\|[^|][^|]*\|`. Its two relative support
paths point to the unchanged archived facades. The fixture similarly points
to the unchanged assertion helper.

The original sources and failed captures remain preserved. These additive
sources require native correctness validation before use in benchmark timings.
The existing source-count admission applies to the original regex main; the
corrected main requires a separate exact source identity/count review.
