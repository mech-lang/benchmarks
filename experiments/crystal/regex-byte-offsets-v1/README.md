# Crystal regex counting and standard scan comparison

The retained Crystal regex programs repeatedly use a standard regex match in an
explicit count loop. Inspection and experiments distinguish three hypotheses:

1. Byte offsets alone show no useful measured improvement on ASCII FASTA. The
   pinned String implementation already has a single-byte conversion fast path.
2. Validating the same immutable UTF8subject on every search is unnecessary after
   the first successful validation. The explicit
   [validation-once candidates](utf8-once-v1/proposal.json) use the standard option
   only after the first ordinary match. Bounded outputs and invalid input rejection
   pass; the reduced-input parallel median improves about4×.
3. The standard `String.scan` API already implements that validation policy.
   The [block and inline-array candidates](scan-v1/proposal.json) use that
   existing general API, reducing authored code while retaining the same scans,
   nonoverlap, case modes, complete input/output and five ordered substitutions.
   All authored orchestration and formatting remain application source.

The [full-size comparison](full-v1/summary.json) measures three fresh complete
processes per source, on the canonical N5m input. The retained parallel control's
34.991s (71.47× Mech AOT) median falls to1.651s (3.37×) with parallel block
scan,1.686s (3.44×) with parallel inline scan, or2.572s (5.25×) with compact
inline scan. The [relative report](full-v1/mech-aot-relative-v1.json) identifies
the retained Mech AOT baseline of0.489612s (1.00×), its original samples and
full-size workload. That baseline is historical; the Crystal speedups use the
fresh matched Crystal control. Peak RSS remains around341MB. This is a
matched comparison of exact retained/new source and configuration, not a claim
of global optimality or a new sample for the historical control profile.

Retained-policy count replays propose54/47/32application units and46/41/28physical
lines respectively. The native compiler consumes these exact application files;
every new helper is counted. The replay preserves the original qualified grammar,
counter and parent controls. It does not create uniform logical-owner or formatted
LOC qualification. The [independent source/evidence review](independent-review-v1.json) found no
blocker for these three sources. Guarded catalog admission remains separate.

The [full plan](full-v1/plan.json) predates the twelve observations and binds the
canonical input/reference, exact binaries, sources, raw qualification/pilot
records, compiler distribution and discovered linked vendor-library bytes.
Compilation, preparation and hashing are outside each clock. Startup, runtime
regex preparation, full stdin/work/stdout and shutdown are inside. All quantitative
processes share one inherited exclusive mutex; no benchmarks run concurrently.

Original application citations and authorship/license uncertainty remain in each
source proposal. Current edits are Codex GPT-6-family adaptations; the exact
serving model is unknown. No parent model attribution is inferred. All unsuccessful
hypotheses, failed source-count host attempts and immutable earlier sources remain
available. No canonical chart record has yet changed from this packet.
