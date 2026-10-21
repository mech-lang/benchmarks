# C# reverse-complement short-read repair

This uncompiled adaptation advances the destination span after each positive
read and clears the unused tail once. It retains the rest of the SIMD/page and
threaded application. The source comparison does not prove general FASTA
conformance: page/header boundaries, comments, irregular rows, EOF, invalid-byte
behavior and thread publication still require native checks.

The original is [reverse complement C# #9](https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/revcomp-csharpcore-9.html),
contributed by Peperud, modified by Anthony Lloyd and rewritten with SIMD by
Thom Kiesewetter. Source notices and [BSD terms](LICENSE.benchmarksgame) remain;
local changes also carry Apache-2.0 terms. Current edits identify Codex GPT-6
with the exact serving model unknown; predecessor attribution stays recorded.

The [helper diagnostic](ReadBlockDiagnostic.cs) supplies variable short reads
at eighteen length/chunk-size combinations and checks the complete retained
prefix, consumed byte count and cleared tail. It does not call benchmark main.
Its [preparation](prepare_probe.py) changes only `Program` to a partial class in
separate parent/fixed copies, allowing the same diagnostic to call the private
helper. The separate startup object selects diagnostic main. No probe was run;
the expected parent failure must be captured rather than claimed from a model.

```sh
python3 experiments/csharp/revcomp-short-read-v1/prepare_probe.py --check
```

The diagnostic and source projections are untimed verification artifacts, not
linked benchmark helpers or LOC exclusions. The complete candidate application
is counted independently. All 61 shared reverse-complement cases remain in the
qualification schedule; seven malformed-IUPAC cases need a C#-specific reviewed
rejection contract and cannot pass on an arbitrary nonzero exit. No source,
timing or chart admission is granted by this packet.
