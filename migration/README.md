# Repository provenance

The benchmark corpus was extracted from the `benchmarks/` directory of [mech-lang/mech](https://github.com/mech-lang/mech) at `c80c2ed57b939593fa5ca549e4651729028e9a9d`. The source branch was `codex/clbg-native-benchmarks`.

[commit-map.tsv](commit-map.tsv), [request.json](request.json), and [result.json](result.json) describe the extraction and its tree checks. Compiler commit references refer to the Mech repository. The compiler integration is reviewed in [Mech PR #897](https://github.com/mech-lang/mech/pull/897); [compiler-validation.json](compiler-validation.json) records its validation results.

The active corpus is organized into source bundles (`programs/`), workload definitions (`benchmarks/`), result tables (`results/current/`), datasets and language metadata (`data/`), explorer code (`site/src/`), and documentation (`docs/`). Historical studies are grouped in `archive/` by language, workload, compiler topic, and validation purpose.

[reorganization-paths.tsv](reorganization-paths.tsv) maps historical paths to their current locations. Resolve an old report reference with:

```sh
python3 tools/resolve_archive.py <historical-path>
```

Historical build commands may depend on local SDKs, compiler builds, libraries, or untracked binaries that are not included here. Reproduction requires checking those dependencies and applying the documented validation and measurement protocol. See [methodology](../docs/methodology.md).

Repository code uses the [Apache-2.0 license](../LICENSE). Third-party sources retain their own attribution and license notices.
