# Formatted source-size measurement

Formatted LOC is a second X-axis measure. Run the exact scored authored source through its language's native formatter when one exists
and retain the resulting line count. A language without a native formatter
has a blank formatted-LOC entry. Existing canonical LOC remains available.

Formatting must operate on separate copies of
the exact scored application/helper bundle; it must never rewrite scored source
or change its measured executable/timings. Retain actual formatter command,
version, configuration, original and formatted source identities and output.
Use the existing source-line counting definition after formatting, and document
the definition in the UI. Do not silently fall back to another LOC measure or
replace a missing native formatter with an unrelated formatter. If any counted
helper cannot be natively formatted, the complete bundle total remains blank.

Unavailable, pending and failed formatter evidence may all have a blank numeric
entry, but their reason must remain distinct in evidence and source details.
Formatting, version probes, output hashes and checks share the timing mutex;
they cannot contend with an active benchmark. Formatter outputs are a second
source-size measure, not new performance measurements or language optimizations.

This proposal includes no measured formatted-LOC values.
