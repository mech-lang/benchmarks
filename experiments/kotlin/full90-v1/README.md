# Retained Kotlin full-workload controller

[kotlin_full.py](../../../tools/qualification/kotlin_full.py) prepares and runs
three fresh-process measurements of twenty retained Kotlin forms and ten matched
Mech AOT controls. This is source preparation only. The required independent
compiled-work qualification receipt and remaining-three native capture do not
exist yet. No draft, prepared execution plan or timing is supplied here.

The sequence contains ninety serial slots: compact, optimized and Mech rotate
through each of three positions for every workload. The two Kotlin forms remain
separate retained artifacts and observations; identical source aliases do not
imply an optimization distinction. Full sizes are regex-redux 5,000,000,
reverse-complement/FASTA/k-nucleotide 25,000,000, pi digits 10,000, spectral norm
5,500, Mandelbrot 16,000, binary trees 21, n-body 50,000,000, and fannkuch-redux 12.

Each Kotlin invocation is the original direct Java launcher, fixed
`-XX:ActiveProcessorCount=8 -Xms64m -Xmx8g -XX:+UseG1GC`, retained home/temp paths,
complete retained class directory, original Kotlin stdlib and one main call.
Runtime startup, class loading, ordinary tiered JIT, complete input, required
work, output and shutdown are timed. Subject compilation, pin verification and
output validation are outside the timer. There is no warmup wrapper, diagnostic
logging, subject recompilation or automatic retry.

The controller reuses the frozen full-workload sampler, complete-output
references and independent process supervisor used by the retained Elixir and
Prolog runs. Each process group has a six-hour native deadline, a 22,200-second
outer deadline and a 10 GiB process-group RSS bound. The original mutex inode
79859134 remains continuously held through environment waits, all samples,
cleanup, final pin verification and artifact retention. A separate suite lease
and fresh output directory exclude implicit resume or concurrent cohorts.
Process ownership, inherited mutex, native exit, reaping, resource/monitor
failures, exact command/environment fingerprint and complete output proof must
all pass. Native stderr must be empty. The established two-finite-energy-lines
1e-8 policy is retained for n-body; other full outputs require their pinned byte
count and SHA-256. An isolated workload failure consumes its slot and skips its
remaining slots; an integrity, ownership or environment failure stops the run.

Canonical LOC is already qualified for all twenty forms. Formatted LOC remains
null and unqualified. Full timing reconciliation and chart admission remain
false even in the raw full-run terminal; they require a separate review.

## Required independent work receipt

The `draft` command requires an explicitly supplied path and digest for a future
`kotlin-retained-compiled-work-qualified-v1` JSON document. This controller never
creates or upgrades that receipt. Its exact contract is enforced by
`prerequisites`, `validate_remaining` and `validate_decisions`:

- `status` is `all20-retained-required-work-qualified`,
  `source_work_qualified` is true and `compiled_work_profiles` is 20.
  Subject recompilations and benchmark samples are zero; full timing and chart
  admission are false.
- `compiled_work` contains `plan`, `report` and `terminal` references. Every
  reference is exactly `{path, sha256}`. These must match the hard-pinned clean
  run-v2 producer, with twenty work JVMs, one diagnostic compiler, 200,000
  observed calls/returns and its original false source-work flag.
- `single_entry_remaining` contains `plan`, `report`, `terminal` and
  `first_capture_reconciliation` references. The exact remaining controller must
  have closed all three additional captures with no errors, no active process,
  three distinct registered native groups and complete outputs. Its plan and
  report must reuse the saved first compact tree capture without reexecution.
  The original failed capture and its exact hsdis warning remain unchanged.
- `decisions` references a separate
  `kotlin-independent-required-work-decisions-v1` document whose status is
  `all20-retained-required-work-reviewed`. It repeats the same compiled-work and
  remaining-capture reference groups and has exactly twenty `profiles`.
- Receipt `profiles` each contain exactly `id`, identical `decision_id`, and
  `source_work_qualified: true`. Each decision profile repeats the exact retained
  `physical_inputs`, `class_artifacts`, `retained_runtime_command`,
  `runtime_environment`, and a `runtime_binding` containing `java`, `stdlib`
  and `runtime_expected` from the original work plan. It includes nonempty
  technical `rationale` and `evidence_pins` referencing the actual closed native
  artifacts, including that form's process, validated result and compilation log.
- Decision `checks` contain exactly `required_work_preserved`,
  `retained_bytecode_and_source_binding` and `runtime_dependency_closure`, all
  true. Binary trees additionally require `single_entry_compiled_versions`,
  `surviving_leaf_and_internal_allocations`, `fresh_disjoint_tree_construction`
  and `long_lived_graph_gc_roots`. Pi additionally requires
  `single_entry_compiled_versions` and
  `both_general_divisions_before_every_comparison`. Those four forms must cite
  their single-entry process/native capture and capture index or saved first
  reconciliation. Missing evidence or an observed removed required operation
  cannot be converted into a passing decision.

The native producer's status “awaiting instruction review” is a necessary
capture result, not an independent work decision. Reflection witnesses,
matching stdout, sampled allocations or method-compilation presence alone do
not satisfy the additional tree/pi requirements. The future decision document
must explain the surviving required work in the relevant single-entry code.

All inherited source/class/runtime pins and closed artifact inventories from
compiled work, both capture stages and the canonical reader are retained.
Preparation verifies them under the common mutex. Each sample rechecks the
closure, exact application class inventory and working directories; final
verification preserves failures and never overwrites an earlier attempt.

## Deferred invocation

After real capture completion and independent native-work review, invoke the
controller with the retained Python and `-I -S -B`:

1. `draft --qualified-work PATH --qualified-work-sha256 SHA256 --plan NEW_DRAFT
   --output NEW_OUTPUT` reads and validates qualified metadata without runtime
   closure hashing or native execution.
2. `prepare --draft NEW_DRAFT --draft-sha256 SHA256 --plan NEW_PREPARED_PLAN`
   verifies the reviewed draft and full dependency/artifact closure under the
   mutex, without launching a subject.
3. `run --plan NEW_PREPARED_PLAN --plan-sha256 SHA256` executes under a durable
   external owner after review of the prepared plan.

The [pure tests](../../../tools/qualification/test_kotlin_full.py) use synthetic
in-memory qualification records and small temporary artifacts. They do not
create a successful prerequisite receipt, parse native compilation logs, hash
runtime closures or launch Kotlin, Java or another benchmark.
