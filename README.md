# Mech benchmarks

A benchmark suite comparing execution time and source size across programming languages, with an interactive explorer for results and source code.

**[Explore the benchmarks](https://mech-lang.org/benchmarks/)**

The catalog contains 60 execution variants across 53 language families. The suite covers ten workloads: binary trees, fannkuch-redux, FASTA, k-nucleotide, Mandelbrot, N-body, pi digits, regex-redux, reverse complement, and spectral norm. Implementations span interpreted, JIT-compiled, and ahead-of-time compiled execution. Results include individual timing samples, source hashes, output validation, and measurement provenance.

## Explore the results

Compare runtime and lines of code, inspect programs and their recorded samples, and filter by workload, language, release year, or language characteristics. Chart layers show individual samples, language summaries, density, and global statistics. Ratios use each workload's fixed best recorded baseline.

The **[Data view](https://mech-lang.org/benchmarks/#v=1&view=data)** lists every recorded run across the full retained implementation inventory. Sort columns, search, apply the sidebar filters, or select individual rows. Implementation links open source and timing details. Download the entire dataset, filtered rows, or selected rows as CSV or JSON; JSON includes matching source files and program metadata. Exports cover all pages and retain full numeric precision. Shared timing aliases identify the same recorded observations once. Copy link preserves the filters, sort, page, row selection and open source.

The [methodology](docs/methodology.md) describes timing boundaries, source counting, library use, and comparison rules. [Mech's optimization history](docs/optimizations.md) connects compiler and runtime changes to their measured effects.

[Reproduction records](docs/reproduction.md) expose recorded versions, build commands, runtime settings, inputs and gaps. [Implementation authorship](docs/authorship.md) distinguishes published sources,
local AI adaptations and generated programs. The data view and exports include
verified model IDs, original attribution, license terms and explicit evidence gaps.

## Repository

| Directory | Contents |
| --- | --- |
| [benchmarks/](benchmarks/) | Workload definitions and chart baselines |
| [programs/](programs/) | Measured source bundles organized by language and workload |
| [results/current/](results/current/) | Program results and individual timing samples |
| [data/](data/) | Explorer dataset and language metadata |
| [site/](site/) | Interactive explorer source and tests |
| [docs/](docs/) | Methodology, language classifications, and optimization studies |
| [experiments/](experiments/) | Qualification protocols, active studies, and publication evidence organized by implementation |
| [archive/](archive/) | Detailed measurement reports and experimental evidence |

## Run locally

Python 3 is sufficient to build and serve the explorer:

```sh
python3 tools/serve.py --port 8766
```

Open <http://127.0.0.1:8766/benchmarks/>. To generate the static site without starting a server:

```sh
python3 tools/build_site.py
```

Generated files are written to `site/public/`.

## Validate the dataset and explorer

```sh
python3 tools/export_catalog.py
python3 tools/test_export_catalog.py
python3 tools/verify_repository.py
python3 tools/test_build_site.py
python3 tools/test_authorship.py
python3 tools/audit_authorship.py --check
python3 tools/build_site.py
node site/tests/data_projection.mjs data/benchmarks.json site/public/data.json
node site/tests/layers.mjs
node site/tests/rankings.mjs
node site/tests/languages.mjs data/benchmarks.json
node site/tests/publication.mjs
node site/tests/benchmark_traits.mjs
node site/tests/density.mjs
node site/tests/view_state.mjs
node site/tests/sample_data.mjs
```

With Playwright and Chrome installed, `node site/tests/sample-table.mjs site/public`
checks the table, source links, desktop/mobile layouts, shared selections and
downloaded CSV/JSON contents in isolated browser contexts.

These commands export and check recorded results. Running the benchmarks requires the toolchains and dependencies specified in the measurement reports. Measurements run sequentially, without competing benchmark or compilation jobs.

The [explorer performance audit](docs/explorer-performance.md) describes browser
payload projection, rendering changes and their validation. Complete measurement
evidence remains in the canonical catalog.

See [coverage status](docs/status.md) for published results and remaining
qualification work.

## License

Repository code is licensed under [Apache-2.0](LICENSE). Third-party benchmark submissions retain their respective licenses and attribution.
