# C# nucleotide record and block handling

This uncompiled candidate extends the local rolling-key C# #1 adaptation. It
selects the exact THREE header token with space/tab boundaries, skips line-start
comments, retains StreamReader's CR/LF line handling and stops at the next header.
Direct character iteration removes the temporary ASCII byte array per line.
The final stored block has its actual length, and prefix priming spans whatever
blocks exist; absent, empty and shorter-than-k records need no padding scan.

Every required width still builds a complete ordinary growable dictionary,
starting at capacity 16, with the existing by-reference increment, rolling mask
and frequency/query summaries. Seven tasks and all overlapping updates remain.
The ASCII reader and default mapping outside the expected A/C/G/T alphabet
remain inherited behavior, not a strict invalid-input adapter. Final writes
use ordinary synchronous console calls.

The original is [k-nucleotide C# #1](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/knucleotide-csharpcore-1.html),
submitted by Josh Goldfoot and modified by Anthony Lloyd. Notices and
[BSD terms](LICENSE.benchmarksgame) remain; local changes also carry Apache-2.0.
Current edits identify Codex GPT-6 with the exact serving model unknown; earlier
model evidence is not inferred. All 22 shared/chunk-boundary output cases, full
native histogram/update witnesses and JIT/AOT measurements remain pending.
Changes to parsing, map initialization and representation may have different
costs; no combined speed or normalized-source-size win is claimed.
