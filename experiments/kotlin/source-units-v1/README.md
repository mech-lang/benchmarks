# Kotlin canonical source-unit candidates

The [counter](../../../tools/qualification/kotlin_source_units.py) consumes the frozen Kotlin reader's saved PSI and produces inspectable canonical LOC candidates. Native parsing and actual source replay have **not run**. Every qualification and chart-admission flag remains false.

The input is the original `source.kt`, the explicitly normalized `psi-source.kt`, and `psi.json`. The counter verifies complete native parent/child partitions, leaf text, UTF-16 boundaries and permitted newline normalization. It loads only the reviewed `kotlin_loc.py` definitions after checking SHA-256 `0f64cbd36435d578de238248a890b581e2389de240534a6a2c4d439147c73710`; it invokes only that module's pure PSI validator.

Ownership follows the [approved source-unit rule](../../../docs/methodology.md): physical nonblank/noncomment source, expanded independent statements/declarations, real executable headers and written closers, and preserved literal/data wrapping. Native PSI distinguishes scalar expression functions and `if` expressions from statement controls, `when` branches, lambda bodies and promoted constructor fields. Chained callbacks have separate headers and bodies. Scalar continuation on an owned closer row adds no independent unit; a separately wrapped continuation row retains its physical unit.

| Constructor source | Candidate units |
| --- | ---: |
| `class Node(val left: Node?, val right: Node?)` | 2 |
| `class Plain(left: Int, right: Int)` | 1 |
| `class Node(val left: Node?, val right: Node?) {}` | 4 |

Unsupported owners, unowned or overlapping executable spans, annotations lacking explicit ownership, and interpolation with independent block work produce diagnostics and a null `normalized_loc`. The [stage record](stage.json) documents the grammar, input inventory and provenance. The [fixture contract](fixture-contract.json) gives the fourteen existing native reader fixtures' expected outcomes; those expectations are not observed parser results.

Run the small synthetic tests with:

```sh
python3 -I -S -B tools/qualification/test_kotlin_source_units.py
```

After the native reader finishes, replay its saved artifacts with:

```sh
python3 -I -S -B tools/qualification/kotlin_source_units.py replay \
  --plan SOURCE-READER-PLAN.json \
  --reader-directory SOURCE-READER-OUTPUT/native-reader/sources \
  --output NEW-source-units.json
```

Replay binds the plan and native report hashes to the completed controller report, including its actual `reader_path` values. It checks saved source/PSI artifacts, applies fixture assertions, and sums both authored inputs for each profile only when both candidates are unambiguous. `--controller-report PATH` supports a relocated controller report; otherwise the plan's output directory supplies it. Output paths must be new.

Native reader execution, actual PSI replay and source-owner review remain pending. Process completion and runtime provenance require the existing reader controller's independently reviewed terminal evidence; this counter always reports `native_reader_terminal_verified: false`. This reader supplies no formatter evidence, so formatted LOC remains null. Synthetic tests exercise ownership and report handling without executing Kotlin, Java, compilers, workloads or runtime preflights.
