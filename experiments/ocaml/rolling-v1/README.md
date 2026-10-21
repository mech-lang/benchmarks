# OCaml nucleotide alternatives

These three uncompiled application drafts explore different source and runtime
costs. None is an original Benchmarks Game submission, a qualified source-count
improvement or a measured performance improvement.

| Draft | Design | Main qualification limits |
| --- | --- | --- |
| `parser_repaired.ml` | Retained numeric-key/fork design with a chunked exact-record parser | Counting kernels and process orchestration retain the predecessor's design; parser changes need native boundary/output tests. |
| `parser_rolling.ml` | The same parser and orchestration, with rolling keys in the native-integer map | All seven full growing histograms remain. The existing pair-key fallback for a 32-bit host remains; the suite's 64-bit host uses native-integer keys at every required width. |
| `compact_rolling.ml` | One generic integer-key `Hashtbl.Make`, mutable count cells, rolling keys and ordinary whole-input line operations | Explicitly requires a 64-bit host. Whole-input copies and a complete list of lines may consume substantially more memory than the chunked parser. It runs serially, so source brevity does not establish speed parity with the forked form. |

The original implementation lineage is
[k-nucleotide OCaml #3](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/knucleotide-ocaml-3.html),
with [OCaml #1](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/knucleotide-ocaml-1.html)
also informing mutable count cells in the compact form. Original notices identify
Troestler Christophe, Mauricio Fernandez, Fabrice Le Fessant and Roman Kashitsyn;
the retained #1 source also names glacialthinker. Original notices in the copied
predecessor remain intact. [LICENSE.benchmarksgame](LICENSE.benchmarksgame)
retains the upstream BSD terms; local changes also carry Apache-2.0 terms.
Current adaptations identify Codex GPT-6 with the exact serving model unknown;
this does not identify the predecessor's serving model.

The parser proposals select the first exact THREE header token with space/tab
boundaries, skip line-start comments, handle CR/LF/CRLF and EOF, and stop at the
next line-start header. Empty or absent selected records yield empty data. They
retain the predecessor's byte encoding, including its default mapping outside
the expected A/C/G/T input alphabet; strict alphabet rejection is not claimed.
Both parser styles need all fourteen shared nucleotide cases and chunk-boundary
cases before qualification. The source-only parser fragment is a review aid,
not an extra linked helper or an exclusion from application source size.

Rolling keys remove repeated packing of each complete window while retaining
every overlapping occurrence and ordinary growable maps starting at capacity
16. Widths 1, 2, 3, 4, 6, 12 and 18 all receive full histograms. Query-only
counters and dense fixed tables are absent. Counts, lexicographic ties, missing
keys, complete final entries and ordered updates still need native witnesses.

Source size includes every application helper, module, parser, type, binding and
process-control function. Raw physical rows, bytes, deterministic gzip and BPE
counts are available separately; native normalized and formatted counts are
unqualified. The compact form must be compared with both retained sources,
including the shorter string-key form, rather than only the long numeric form.
