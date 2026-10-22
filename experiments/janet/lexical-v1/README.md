# Native Janet lexical source measure

`count.janet` validates the complete source with the Janet reader and then walks
the pinned, unmodified Spork source grammar. It never evaluates application forms.
`run.py` counts all thirteen source files plus both formatting projections,
checks eight hand-counted packed/wrapped probes, and rejects malformed input
without returning a count. The initial owned diagnostic remains in `probe-v1`.

The [source qualification report](../source-qualification-v1/README.md) defines
tokens, dependencies, exact scope and limits. This metric is complementary to
BPE, bytes and gzip; it is not normalized statement LOC or a language-neutral
complexity or expressiveness score. Process streams and complete owned cleanup
receipts are retained in `run-v1`; no timing sample or chart admission is added.
