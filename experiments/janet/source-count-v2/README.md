# Published Spork source-formatter experiment

This uses unmodified `spork/fmt` from the pinned dependency snapshot. Native reader
tree equality, independent-process idempotence, clean flychecks and all 149
application output/rejection contracts pass for the active source set.

The formatter preserves input line layout, so equivalent packed and wrapped
programs retain different row totals. The raw `published_formatted_loc` field
counts all nonblank output rows, including preserved comments. It is not qualified
normalized or noncomment application LOC. The
[reconciliation](../source-qualification-v1/README.md) retains these distinctions
and the native evidence rather than silently promoting a row total.
