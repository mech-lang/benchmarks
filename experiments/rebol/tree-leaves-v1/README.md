# Evaluated binary-tree leaf values

The retained binarytrees main initializes each node with `copy [none none]`.
That block contains two literal words; copying it does not evaluate them to
`none` values. The first bounded binarytrees case (`n-0`) exited with a script
error when `check-tree` received a `word!` child. Its original source and failed
capture remain preserved in
`experiments/rebol/bounded-v1/remaining-intake-v1/run-v1/023-binarytrees-n-0`.

The additive [main](main.reb) changes that initializer to `reduce [none none]`
so both leaf fields are evaluated. Recursive construction, child assignments,
tree checking, iteration counts, output and input handling otherwise remain
identical. Its relocated loader still resolves to the original archived
`clbg_io.reb`; no helper is copied or changed.

The additive [N4 diagnostic](binarytrees.reb) points to this new main. Apart
from that path and its title/comment identifying the corrected main, its
identity traversal, independent leaf checks, collection window, output
sidecar and assertions are unchanged. It continues to disclose its additional
root alias and does not claim per-tree freeing or full-size observations.

This is a source correction awaiting native validation. No controller or
prior plan is changed, and no retry is performed by this packet. Required work,
source counts, runtime equivalence, timing and chart admission are not granted.
