# First native Scala parser capture

One supervised JVM processed all 70 source-reader fixtures and ten application
sources. It retained an unmodified parser transport and an observed transport
for each input. **All 80 pairs are exactly equal**, including graph IDs,
diagnostics, spans and final scanner state. The process exited successfully
with empty stdout and stderr; the [report](native-token-capture-v1/report.json) binds all inputs and
generated records.

The candidate reports complete coverage for 27 inputs. It rejects eight
intentional negative fixtures: six parser-error cases, a physical terminal
U+001A that the scanner treats as early EOF, and an XML reader handoff. Another
45 otherwise valid inputs fail the candidate's graph-completeness gate.

The graph failures consist of native `EmptyTree` and `Thicket` containers whose
compiler-internal `NoType` marker makes `hasType` true. There are 71 such records
across 47 inputs, including two already-invalid fixtures. Their native graph
data is retained. This observation calls for a narrowly scoped transport
correction; it does not admit these records by ignoring graph failures.

The eight negative fixtures remain rejected and their expected results remain
unchanged. The original reader, capture candidate and these native artifacts
remain available for comparison with the correction. No canonical count,
formatted count, benchmark compilation or benchmark timing is admitted by this
capture.
