# Core Janet reader/pretty-printer experiment

This is a retained formatting experiment, not an admitted canonical LOC method.
`format.janet` asserts complete native reader-tree equality and idempotence before
printing source. `run.py` retains thirteen formatted sources, clean flychecks,
eight equivalent layout pairs, bracket/parens and malformed-input controls, and
all 149 output/rejection contracts on the formatted active source set.

The raw `reader_formatted_loc` field counts nonblank formatter output rows. The
[reconciled source report](../source-qualification-v1/README.md) identifies its
meaning explicitly and explains why this data pretty-printer was not selected as
canonical source formatting. All native streams and process receipts remain in
`run-v1`. The formatter does not evaluate application forms while reading them;
bounded application execution is a separate verification stage.
