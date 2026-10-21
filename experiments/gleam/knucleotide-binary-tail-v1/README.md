# Gleam nucleotide binary traversal candidates

The retained optimized source already uses rolling integer keys and seven
ordinary process workers. Its recorded full median is 120.653s (234.81× the
retained Mech AOT median of 0.513828s) on the canonical nucleotide workload.
Those historical observations remain unchanged.

The raw-tail candidate replaces repeated foreign byte/size access in each
histogram with native binary pattern matching. The preencoded-tail candidate
also converts case-insensitive bases to 0–3 once before starting the seven scans.
All seven dictionaries still start empty and count every overlapping occurrence;
query lookup happens after complete histograms exist. Parsing, sorting and full
output are retained. No workload kernel is moved into another language.

The original source proposals failed the native compiler's exhaustiveness check:
BitArray can also contain a partial-byte tail. Their errors remain in
[native-v1](native-v1/report.json). The additive
[version2 sources](proposal-v2.json) explicitly reject that unreachable-for-FASTA
shape. The retained program and both repaired candidates compile with the exact
historical compiler version and pass81complete independent output checks across
empty/short inputs, token decoys, comments, record boundaries, mixed case, CRLF
and wide numeric keys. [The native report](native-v2/report.json) binds every build
input, generated artifact and process capture.

[Actual BEAM lowering](native-lowering-review-v1.json) shows binary match-context
traversal in both histogram loops and private-append construction in the encoding
loop. Per-byte foreign byte/size calls are absent from the changed histogram
loops. This establishes the emitted mechanism; it does not establish a speedup.
Complete work traces, source counts, independent review and measurements remain.

The [ownership boundary](ownership-boundary-v1.json) preserves the qualified
retained policy: main application code counts, and the same93units of generic
I/O/formatting/dispatch/concurrency support remain separately reported. All new
workload helpers are in the main source. No additional foreign workload helper or
new exclusion is introduced. New candidate counts remain unapproved.

[The proposal](proposal.json) preserves original source identity, exported byte
identity, citations and unresolved lineage. Current edits are Codex GPT-6-family
adaptations; the exact serving model and original authoring model are unknown.
