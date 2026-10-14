# Retained Elixir full90 measurement stage

The controller and metadata draft are prepared for review. No full workload,
native probe, compiler, runtime invocation, or full closure verification was
performed while preparing this packet. The draft is explicitly not executable:
`pins_verified` is false. A separate locked `prepare` step must verify all
6,559 prerequisite pins and produce a fresh reviewed executable plan.

The cohort is 20 qualified retained Elixir forms, each measured three times,
plus three fresh samples of the matched Mech AOT control for each benchmark.
Each benchmark rotates compact, optimized and control through all three
positions. Identical compact/optimized sources remain separate retained forms
and separate samples; no distinct optimization is claimed.

The work prerequisite is `compiled-work-v1/qualified-work-v1.json`, SHA
`a96ed85f0f0d1da05cca428d18dfeb9d0d702158b7aa0f7a5c87ae827b4588bf`.
The LOC prerequisite is `source-units-v1/qualified-source-counts.json`, SHA
`1fd0401a8dc46a70268beb6dd2a287b7725e74b9a4a0d33d4c6e92d8ff1df755`.
The complete saved work and reader artifact inventories are included in the
flat closure. Retained source, helper, launcher, BEAM and compiler-owner records
are linked by their existing qualified pins. Historical owner paths are
provenance only; each maps to one already-pinned archived record with the exact
same content digest and filename. No historical-language resolver is used.

The exact retained Elixir launcher, absolute ebin and runner arguments, runtime
environment, scheduler settings and default garbage collection remain intact.
The working directory is the retained source-form directory. The first nbody
compact form preserves its separately retained first-compile ebin. No tracing,
diagnostic flags, recompilation of main/helper modules, warmed process, or
in-process repetition is added. Runtime startup, BEAM loading, launcher
evaluation, stdin consumption, required work, all output and shutdown are inside
the measured process lifetime.

| Benchmark | Full size |
| --- | ---: |
| regexredux | 5,000,000 |
| revcomp | 25,000,000 |
| pidigits | 10,000 |
| spectralnorm | 5,500 |
| mandelbrot | 16,000 |
| fasta | 25,000,000 |
| knucleotide | 25,000,000 |
| binarytrees | 21 |
| nbody | 50,000,000 |
| fannkuchredux | 12 |

The controller reuses the frozen serial sampler and output validators, the
unchanged independent `prolog_supervisor.py` process supervisor, and only the
language-neutral receipt validation/accounting helpers in frozen
`prolog_full.py`. It does not call that module's Prolog evidence resolver,
preparation or execution routines. The sampler import closure is six exact
Python files. Main/helper compilation is already complete and excluded;
reference hashing and output validation occur outside the measured interval.

The common timing lock inode 79859134 remains held continuously by one
descriptor through all environment waits, native lifetimes, cleanup and final
terminal writing. Each native/sampler lifetime inherits the same descriptor.
A separate Elixir suite lease excludes a second cohort. Native timeout is
21,600 seconds, outer supervisor deadline 22,200 seconds, and process-group RSS
ceiling 10,240 MiB. Output validation uses complete byte length and SHA-256,
except the unchanged nbody two-energy validator with tolerance 1e-8.

There is no automatic retry or implicit resume. A cleanly isolated benchmark
resource/output failure excludes that form and skips its remaining planned
slots; integrity, environment, monitor or ownership failure stops the cohort.
Reports distinguish planned slots, registered native attempts, qualified
samples and skipped slots. Complete output receives no automatic chart
admission or final timing qualification; those remain a separate evidence
review.

The 18 pure tests cover the saved cohort, balanced rotation, unchanged first
compile ebin, diagnostic/runtime mutation, missing source roles, count linkage,
BEAM and launcher pins, owner evidence ambiguity, distinct control argument
shapes, source aliases, draft rejection, plan/reference/closure tampering,
artifact path escape, conflicting pins and replaced common lock identity. They
passed in 0.108 seconds. No native process is launched by these tests.

The draft SHA is
`fab709a1e51c4d3079590a498b8bdaa5c916f2baadef368944119a0a58e4a7d4`.
After review, the root owner may prepare it with the retained Python:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/elixir_full.py prepare --draft /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/plan-draft-v1.json --draft-sha256 fab709a1e51c4d3079590a498b8bdaa5c916f2baadef368944119a0a58e4a7d4 --plan /private/tmp/mech-benchmark-completion/experiments/elixir/full90-v1/plan-v1.json
```

Execution requires that new plan's exact reviewed digest and a durable external
job owner. The controller refuses an existing output directory or changed
draft, prepared plan, execution identity, prerequisite closure or schedule.
