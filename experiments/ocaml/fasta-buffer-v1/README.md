# OCaml FASTA bounded output buffer

This uncompiled adaptation replaces the random-record-sized output allocation
with a 62,464-byte buffer holding at most 1,024 sixty-base rows and their
newlines. It writes only the filled portion before reusing the buffer. The
source's RNG/cumulative-selection function, distribution construction, ALU
repetition, headers, TWO-to-THREE seed handoff and per-base binary64 division
remain unchanged. Zero random bases skip row writes.

The original is
[FASTA OCaml #6](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/fasta-ocaml-6.html),
contributed by Troestler Christophe and modified by Mauricio Fernandez, Fabrice
Le Fessant and Roman Kashitsyn. Original source notices remain in the draft.
[LICENSE.benchmarksgame](LICENSE.benchmarksgame) retains the BSD terms; local
changes also carry Apache-2.0 terms. The current adaptation identifies Codex
GPT-6 with the exact serving model unknown; predecessor model evidence remains
unknown.

The hypothesis is lower peak allocation and less large-object collection work.
More output calls or loop overhead could offset any benefit. No speed, memory,
native output, work or source-count result is claimed. All sixteen shared FASTA
cases, buffer-edge cases, complete RNG/output witnesses and full-size output
remain required before isolated complete-process measurement. Existing
observations and chart selections are unchanged.
