# Bounded continuation with evaluated tree leaves

This additive controller selects the [reviewed tree-leaf correction](../../tree-leaves-v1/README.md) and runs only the final 126 cases of the unchanged shared149 corpus. It starts with `binarytrees:n-0`, followed by the 125 cases that were not started in the [retained failed run](../remaining-intake-v1/failed-stage-review-v1.json). The new schedule has 119 expected successes and seven language-specific rejections. No compiler or matched control runs are added.

The earlier run's 23 successful output contracts are replayed independently from their original captures. Its failed tree attempt, all 122 run artifacts and eight durable job artifacts remain immutable prerequisites. The old failure is never relabeled as a success. If all new cases pass, the combined evidence will contain 149 successful output contracts across 150 actual attempts, including the retained failure; that disposition still requires independent review.

`rebol_bounded_continue.py` loads the exact frozen bounded intake and its primitive adapter. The original observer, output checker, stdin handling, direct runtime invocation and 180-second / 512 MiB / 1 MiB stream limits are retained. Only the remaining schedule, tree selection and continuation report counts/schemas change. The corrected regex and Fannkuch sources remain selected; all original source pins remain present. The prior bounded job becomes a seventh prerequisite job under twelve inherited leases, including the common mutex. Its output inventory is added to the existing prerequisite closures.

The new source approval uses schema `rebol126-continuation-source-review-v1`, status `independent-source-review-complete-native-cases-pending`, and `independent_review: true`. Its `files` map pins this controller, its focused test, this README, the corrected tree main and the tree source review. Its dependency pins the frozen bounded adapter. It names the exact `base_source_review`, `prior_stage_review` and `tree_source_review`. The base review continues to bind the original controller, checker and earlier source choices. Every downstream qualification gate remains false.

Preparation and execution use the retained Python with `-I -S -B`:

```text
tools/qualification/rebol_bounded_continue.py --adapter-sha256 SHA prepare \
  --plan experiments/rebol/bounded-v1/tree-continuation-v1/plan-v1.json \
  --output experiments/rebol/bounded-v1/tree-continuation-v1/run-v1 \
  --primitive-review ABSOLUTE_COMBINED_PRIMITIVE_REVIEW --primitive-review-sha256 SHA \
  --source-review ABSOLUTE_CONTINUATION_SOURCE_REVIEW --source-review-sha256 SHA

tools/qualification/rebol_bounded_continue.py --adapter-sha256 SHA run \
  --plan ABSOLUTE_PREPARED_PLAN --plan-sha256 SHA
```

Actual commands use absolute physical paths. The target command has no `-u`; the durable launcher manages its own buffering separately. Preparation requires source review and a free lease set. It starts no native process. Execution is serial, stops at its first unexpected failure and performs no automatic retry. Fresh output paths are required.

The plan, result and terminal schemas are `rebol126-bounded-plan-v1`, `rebol126-bounded-results-v1` and `rebol126-bounded-terminal-v1`. Result and terminal counts describe only new processes; `preserved_successful_cases: 23` identifies the separate earlier evidence. The success status is `remaining126-output-contracts-retained-awaiting-independent-review`. Complete bounded correctness, source work, updated counts, full timing and chart admission remain separate later decisions. Tests, source approval and preparation are recorded separately; no native success is implied by this source packet.
