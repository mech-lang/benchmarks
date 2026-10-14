# Retained GNU APL source owners

Nine exact complete source files cover the five completed workloads still
missing from the chart. Their source counts include every independent statement,
function header and explicitly written function closer. Comments and blank lines
are excluded. The original producer counts and their historical approvals are
unchanged.

| Source | Canonical units | Function headers | Written closers |
| --- | ---: | ---: | ---: |
| N-body canonical v2 | 32 | 2 | 2 |
| Mandelbrot original | 34 | 1 | 1 |
| Mandelbrot compact v2 | 36 | 1 | 1 |
| Mandelbrot optimized v2 | 38 | 1 | 1 |
| K-nucleotide compact v2 | 185 | 12 | 12 |
| K-nucleotide optimized v2 | 205 | 12 | 12 |
| Fannkuch-redux | 38 | 1 | 1 |
| FASTA compact | 41 | 3 | 3 |
| FASTA optimized v3 | 60 | 5 | 5 |

Every noncomment source line in these files has one complete owner. Function
headers include their result, arguments and local-name declaration syntax;
those names do not add executable assignments. A label belongs to the following
statement on its line. Branch expressions count once, including conditional
branches. Array updates have one assignment owner. Function arguments, vector
literals, indexed dimensions, arithmetic pipelines, formatting strings and regex
patterns remain expressions inside their statement.

All nine files were read in full. None contains a packed diamond-separated
statement sequence or chained independent assignments. Quoted text and doubled
APL quotes are protected when checking those properties. Each opening function
header pairs with a separately counted closing `∇`. Source hashes restrict the
checker to these nine reviewed identities; it is not an APL grammar certificate
or a fallback line counter for other files.

The old APL policy excluded standalone closing `∇` lines. The existing canonical
closer approval covers six different source identities. This packet applies the
same written-closer rule to these nine independently inspected complete files,
without modifying that older whitelist or treating its approval as evidence
for unreviewed bytes. Fannkuch therefore has 38 units; its older 37-unit producer
metric is preserved in the original report.

The two n-body labels share one source, as do the fannkuch labels. Each pair
receives one source-count identity and retains its explicit timing alias. All
three measured Mandelbrot implementations remain separate source identities.
APL binary trees is outside this packet: its failed full-size execution cannot
become a timing by approving a source count.

Formatted LOC is unavailable. This packet does not execute APL, remeasure a
workload or admit observations to the chart. Publication must separately bind
these exact authored files to the retained runtime and sample evidence,
including the FASTA argument correction and fannkuch sample-84 recovery.

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -I -S -B tools/qualification/test_apl_retained_source_units.py
```
