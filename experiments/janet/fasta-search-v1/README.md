# Janet FASTA search and output candidates

Two locally authored candidates retain the v2 parent's ALU text, original
probability vectors, cumulative-addition order, seed and naive floating LCG
expressions. All application logic remains Janet. They use no new library or
native workload helper. Original Ian Osgood lineage and BSD-3-Clause notice are
preserved through the source manifest; local changes use the repository's
Apache-2.0 license, authored by Codex GPT-6 family, exact serving model unknown.

Both candidates batch random-record output at completed rows into roughly 64 KiB
buffers, flatten the small alphabet into a local array, hoist its last index,
and inline the unchanged LCG expressions. The fixed ALU record uses a startup-built
period containing 287 wrapped rows, then ordinary repeated block copying and a
short tail. This reuses only the prescribed fixed input sequence, not a random
sequence. Every randomly selected nucleotide still performs its own LCG update,
floating division and comparison against unscaled cumulative probabilities.

The linear candidate retains the parent's strict upper-bound scan. The binary
candidate uses ordinary upper-bound binary search with the same equality rule.
Neither contains scaled thresholds, an integer-state-to-letter table, cached
random draws, seed skip-ahead or independently seeded parallel streams. The
[FASTA requirements](https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/fasta.html)
are the algorithm boundary, not complete-output equality alone.

`qualification-v1` retains 48 complete bounded outputs, all passing: three sources
over the 16 shared FASTA cases. Another 48 actual-source projections add only a
counter immediately before the LCG update and a final diagnostic. Each performs
exactly 8*N draws and reaches the independently iterated final seed while
retaining its complete expected stdout. The TWO-to-THREE seed continuation,
zero-length input, row tails, fixed-sequence wrap and chunk flush are exercised.

The source-extracted search functions agree on every one of 139,968 normalized
states for each original alphabet, plus fifteen synthetic equality, duplicate
threshold and adjacent floating-point cases: 279,951 checks. This is an untimed
test of ordinary searches, not a production lookup table. All complete native
streams, source projections, process identities and cleanup receipts are retained.

`full.py` runs three sequential full-size samples per source under the common
mutex, with complete-output SHA-256 validation, source/runtime pins and power/
process monitoring. It uses the existing owned quantitative controller and the
retained equivalent-input Mech AOT median. Full stdout is checked completely,
then only the validated owned payload is removed to avoid retaining over 2 GB;
its size, SHA and removal policy remain recorded. Bounded streams remain complete.
Preparation, diagnostic projections and output hashing are excluded from the
whole-process timing interval. Chart admission, qualified source counts and
quiet-host confirmation remain separate gates.
