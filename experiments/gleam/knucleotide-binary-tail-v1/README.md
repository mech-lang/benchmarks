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

These are uncompiled source hypotheses. The preencoding append must be inspected
in emitted Erlang/BEAM before claiming linear construction or efficient binary
reuse. Complete work, exact syntax, application ownership/counts and timings
remain separate qualification gates. New helper source counts in full; existing
inventory support-role flags do not prove that authored helpers may be excluded.

[The proposal](proposal.json) preserves original source identity, exported byte
identity, citations and unresolved lineage. Current edits are Codex GPT-6-family
adaptations; the exact serving model and original authoring model are unknown.
