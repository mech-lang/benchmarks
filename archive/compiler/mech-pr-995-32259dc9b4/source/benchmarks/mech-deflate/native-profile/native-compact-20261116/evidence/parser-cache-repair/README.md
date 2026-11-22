# Parser integration and cache repair

The incoming parser changes made the unchanged 2,719-line codec exceed its default fuel budget and, after that correctness issue was repaired, compile about 20% more slowly. The compiler now checks for an ordered-list prefix before scanning a whole line as a possible underlined heading. Completed nodes remain reusable during speculative parsing, and sealed lexical execution leaves repeated-node replay and nested scanner phases intact.

**The original source again parses in 3,967,302 steps under the unchanged 4,000,000-step default.** It emits 718,353 events and the same 160,696 final nodes. Both actual standard recipes and both checked source recipes reproduce the entire qualified object, metadata and canonical bytecode exactly. The default linked executable passes output, alias, injected-failure and recovery checks. **586 parser tests pass**, including a new one-shot cached/uncached comparison of identities, Unicode scanner state, logical work and finite resource limits.

Compiler source: [`be392dedfe0e8439bf632882e4bb302b92f4dbcc`](https://github.com/mech-lang/mech/commit/be392dedfe0e8439bf632882e4bb302b92f4dbcc). The earlier list-prefix repair is [`72cec3e52`](https://github.com/mech-lang/mech/commit/72cec3e528464c7b78548116b7d376c4e9f570b8). The original codec source, canonical bytecode and native lowering are unchanged by these parser repairs. The reproduced selected encoder retains **81/81 Roc and 63/81 libdeflate wins** from its two complete qualified runtime orders.

## Fresh-process complete builds

Twelve balanced serial orders use six actors and equally prebuilt compilers and fixed support. Every observation starts a fresh process and includes original source through final executable linking. Bootstrap and strip remain separate. A preceding twelve-order comparison records the intermediate regression as well; both full sets are archived.

| Compiler / recipe | Source through final link, seconds | Separate strip, seconds |
|---|---:|---:|
| Prior qualified compiler, e112b5dcd | 2.205278 | 0.010883 |
| Rebased compiler before cache repair, 72cec3e52 | 2.647433 | 0.010881 |
| Cache-repaired selected compiler, be392dedf | 2.185589 | 0.010938 |
| Cache-repaired smaller alternative | 2.185459 | 0.010903 |
| Roc | 2.990179 | 0.010852 |
| libdeflate | 0.483009 | 0.010934 |

Selected paired build-time ratios are **0.732022× Roc /4.526886× libdeflate**. Relative to the matched regressed compiler, time is **0.825019×**, a 17.50% reduction. Relative to the matched prior qualified compiler it is **0.991579×**, approximately 0.84% less time. These are measured cohort summaries; no confidence interval is asserted.

Parser time is **0.679448 s**, versus 1.151924 s in the regressed compiler and 0.703017 s in the prior qualified compiler. Frontend, native emission and linking take **0.223067 /1.208653 /0.035343 s**. Independently calculated phase medians do not add exactly.

The selected image remains **63,832 B of encoder text, 3,200 B of readonly data and 210,024 B stripped**. The smaller qualified alternative remains 63,784 B of text. This repair changes compilation; the native images and their runtime score remain the same. The goal is still 1× libdeflate across all 81 cases, with 64 wins next.

## Evidence and reproduction

The portable verifier recomputes all 24 complete-build orders, artifact identities, phase medians, paired ratios, 972 actual stripped-executable deployments and their independently inflated streams. Raw data is deduplicated by SHA-256; `files.json` maps each recorded logical file to its exact blob. It includes both successful source generations, checked replays, all eight diagnostic parser variants, the failed parser case, the CPU sample, exact timing-driver source and the historical pair-append decline. The initial combined fast-path test failure is also retained: it exposed scanner-state and work-count differences, which the nested-phase guard repairs. Diagnostic parser-only elapsed values are separate from the complete-build clocks.

From this directory, on the recorded Apple ARM64 configuration:

```sh
python3 verify.py
python3 replay.py /tmp/mech-parser-repair --target-dir /tmp/mech-parser-repair-compiler
```

`replay.py` uses the actual main builder, first with its default recipe, then the retained control. Supplying `--mimalloc-object /path/to/mimalloc.o` also links the normal worker and executes its output and failure/recovery probes. It never runs an archived compiler. The raw historical commands contain their original temporary paths as provenance; the replay command resolves inputs from this checkout.

The full optimized parser checks were:

```sh
cargo test --manifest-path src/syntax/Cargo.toml --release --locked --lib \
  --test document_parser_limits --test document_streaming_equivalence \
  --test document_streaming_resources --test document_streaming_complexity
```

This is parser qualification and exact native-image reproduction; the full GPU suite is not claimed. [Measured build data and source hashes](summary.json) · [Archive identity](archive.json) · [Previously qualified runtime measurements](../arm64-byte-extensions/PARITY.md).
