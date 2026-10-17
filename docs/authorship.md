# Implementation authorship and licenses

Each retained implementation has source-bound `authorship` metadata. The sample
table shows Authorship, AI model and License columns; all three support sorting
and text search. CSV and JSON exports include the labels and structured evidence.
The source inspector retains original contributor notices and links to upstream
implementations, reference collections and license texts.

## Origins

- **Published** identifies an upstream submission compiled and measured locally.
  Compiler flags alone do not make the application AI authored.
- **AI adapted** identifies a documented local adaptation or translation of
  upstream application source. Original attribution remains attached.
- **AI generated** identifies an application written locally for this suite.
  Workload descriptions and algorithm references remain visible; these entries
  are not presented as published community submissions.

A workload-description URL is not evidence that a program was downloaded from
that site. Retained source audits, provenance manifests and source notices supply
the distinction. Reference implementations are identified separately from the
measured implementation. Authorship describes implementation provenance and
AI assistance under human direction; it does not assert exclusive copyright
ownership by a person or model.

## Model evidence

The exact recorded IDs include `gpt-6.1-sol` and `gpt-6-astra`. A model is listed
only when the complete retained source bytes were found in a source-writing
assistant tool call with an identified active model. The public
[evidence index](../data/source-model-evidence.json) binds that observation to
the source SHA-256 and a digest of the tool call. Raw conversations, user messages,
session identifiers and local account paths are excluded.

These observations establish source-write contributors, including authored
helpers. They do not establish a sole original author or a complete edit history.
Partial coverage shows how many source files have matching evidence. Unverified
means no exact model attribution was established for that revision. A neighboring
program, Git author, timestamp, requested model or model used to measure the
program never substitutes for a source match. Upstream submissions do not receive
an AI authorship claim merely because an assistant downloaded or built them.

## License evidence

License entries describe the retained source bundle and identify their scope.
Suite-authored code and local changes use the repository's Apache-2.0 license.
Upstream source retains its applicable terms, including the Benchmarks Game's
[revised BSD license](https://benchmarksgame-team.pages.debian.net/benchmarksgame/license.html)
and the retained Programming Language Benchmarks
[MIT notice](../site/reports/programming-language-benchmarks-license.txt).
Original notices and bundled source with separate terms remain inspectable.

**Identified** means the recorded source terms are identified. **Partial** means
some terms are identified while upstream evidence remains incomplete. **Unverified**
means a source license has not been established. These states do not mean
unconditional permission or that no license exists. Runtime, compiler and external
library licenses are separate from this source inventory. A repository-wide
license does not replace an upstream source license.

## Maintaining the records

`python3 tools/audit_authorship.py` regenerates the additive catalog metadata from
retained provenance and model evidence. `--check` detects stale records. Source
identities, measurements, LOC, baseline values and original qualification records
are preserved. `python3 tools/export_catalog.py` includes the same metadata in each
readable program manifest. `python3 tools/test_authorship.py` checks provenance
classification, license gaps, exact model bindings and inventory coverage.
