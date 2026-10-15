# Mech benchmarks

A benchmark suite comparing execution time and source size across programming languages, with an interactive explorer for results and source code.

**[Explore the benchmarks](https://mech-lang.org/benchmarks/)**

The suite covers ten workloads: binary trees, fannkuch-redux, FASTA, k-nucleotide, Mandelbrot, N-body, pi digits, regex-redux, reverse complement, and spectral norm. Implementations span interpreted, JIT-compiled, and ahead-of-time compiled execution. Results include individual timing samples, source hashes, output validation, and measurement provenance.

## Explore the results

Compare runtime and lines of code, inspect programs and their recorded samples, and filter by workload, language, release year, or language characteristics. Chart layers show individual samples, language summaries, density, and global statistics. Ratios use each workload's fixed best recorded baseline.

The [methodology](docs/methodology.md) describes timing boundaries, source counting, library use, and comparison rules. [Mech's optimization history](docs/optimizations.md) connects compiler and runtime changes to their measured effects.

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
python3 tools/verify_repository.py
node site/tests/layers.mjs
node site/tests/rankings.mjs
node site/tests/languages.mjs data/benchmarks.json
node site/tests/publication.mjs
```

These commands export and check recorded results. Running the benchmarks requires the toolchains and dependencies specified in the measurement reports. Measurements run sequentially, without competing benchmark or compilation jobs.

Pending APL, Julia AOT and Rebol tooling has
[250 passing pure test methods across 21 scripts](experiments/shared/pure-validation-20261015/README.md),
with the initial failures and repaired results preserved. These checks do not
perform native intake or admit new benchmark results; remaining qualification
work is recorded in [coverage status](docs/status.md).

## License

Repository code is licensed under [Apache-2.0](LICENSE). Third-party benchmark submissions retain their respective licenses and attribution.
