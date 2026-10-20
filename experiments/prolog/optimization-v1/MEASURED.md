# Prolog spectral norm: matched full-work comparison

The specialized row-loop candidate divides each matrix-vector product into eight
contiguous blocks using SWI-Prolog's standard thread library. It retains all
forty products and 1.21 billion coefficient evaluations at `N = 5500`; it does
not cache the matrix or delegate the numerical kernel to another language.

| Source | Full-process median | Sample SD | Retained source units | Physical code lines |
| --- | ---: | ---: | ---: | ---: |
| Original | 179.48 s | 1.10 s | 96 | 67 |
| Specialized, eight blocks | 34.52 s | 1.49 s | 128 | 87 |

The candidate is **5.20× faster** in this matched comparison. Three complete
processes per source were run sequentially in a preselected shuffled order, with
startup, worker creation, computation, output and exit included. All six outputs
exactly match the reference. The complete observations, process receipts,
runtime/source pins and power checks are in
[the full report](full-selected-v1/full-v1/report.json).

This comparison measures the combined effect of specialized row loops and
parallelism. It does not isolate their individual contributions or establish a
globally fastest Prolog implementation. A serial specialized candidate was
qualified and piloted, but was not selected for the full comparison.

The candidate's 128-unit count is an independently reviewed extension of the
retained source-accounting convention for this exact source. The existing native
logical counter remains unqualified for its imported dynamic thread goals; the
manual review does not turn that unavailable measure into a grammar qualification.
The original source and its historical measurements remain retained.
