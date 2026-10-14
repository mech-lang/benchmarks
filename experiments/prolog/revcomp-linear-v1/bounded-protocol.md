# Bounded conformance protocol

The [controller](../../../tools/qualification/prolog_revcomp_bounded.py) compiles
the separate linear reverse-complement candidate once and inspects its resulting
QLF in a fresh SWI-Prolog process. It then executes all 54 independent fixtures
through the production entry and through each of nine diagnostic capacities:
1, 2, 3, 7, 59, 60, 61, 64 and 127 bytes. The planned cohort contains 542 native
processes: one compiler, one compiled-code reader, and 540 candidate invocations.
Of the candidate invocations, 470 must produce the complete expected output and
70 must reject the exact invalid IUPAC code. The latter also require the exact
already-written header, `>r` followed by LF, with no sequence output. This adds
a source-backed partial-output check to the fixture generator's error-code
expectation. These are bounded checks, not timing
samples. No native execution has been performed for this protocol.

The candidate, independent fixture generator, existing compiler/VM reader,
retained SWI runtime and its previously prepared physical dependency closure
are pinned. Preparation materializes the fixture bytes without running a
language runtime. The compiler receives a byte-identical candidate source copy
inside the new output directory. Compilation and inspection preserve their
actual loaded-source and foreign-library inventories, runtime policy and VM
listings. Each case loads the same QLF without recompiling it.

The production entry uses its fixed 65,536-byte capacity. Diagnostic invocations
select only the capacity; they execute the same parser, reversal, complement
mapping and output predicates. Both entries terminate through the candidate's
existing wrapper. The explicit startup goal therefore cannot fall through to a
second initialization entry. All these authored predicates remain counted
candidate source; no diagnostic helper performs the benchmark transformation.

Each native process inherits the unchanged common timing mutex, has an owned
process group, and is checked against its kernel process identity. The existing
bounded supervisor permits 30 seconds, 2 GiB of live process-group RSS and an
8 MiB native file, with a five-second cleanup deadline. These conformance limits
are separate from full measurement limits. Native commands never overlap and
there are no automatic retries. A timeout, unknown diagnostic, unexpected exit,
output mismatch, unowned process or changed input stops the cohort and retains
the actual failure.

The [startup and error-path review](startup-protocol-review.md) records the
retained runtime source locations and earlier compiler receipts behind the
once-only entry and exact diagnostic expectations. Its digest is bound by the
prepared plan.

The generic supervisor normally rejects nonzero exits and stderr. The new
controller preserves those raw supervisor outcomes and independently reconciles
only the planned exceptions: exit 1 with the exact invalid-IUPAC error, and exit
0 with the exact compiler/reader weak-import warning. It does not strip text,
silence diagnostics, modify the candidate, or rewrite a failed observer receipt.
Every accepted exception still needs a reaped child, empty process group, intact
artifacts, unchanged supervision limits and no cleanup intervention.

Preparation and execution both require the existing mutex inode 79859134 to be
free. They must wait for the active full measurement cohort to close. Commands
for the first fresh plan are:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B tools/qualification/prolog_revcomp_bounded.py prepare --plan experiments/prolog/revcomp-linear-v1/bounded-plan-v1.json --fixtures experiments/prolog/revcomp-linear-v1/fixtures-v1 --output experiments/prolog/revcomp-linear-v1/bounded-run-v1
```

After reviewing the prepared plan, use its printed digest with the durable job
owner and the controller's `run --plan … --plan-sha256 …` command. The output
directory must be new. A failed run is retained and never reused as a fresh run.

Successful bounded output alone does not establish the required work, linear
runtime scaling, source counts, runtime dependency closure of the measured
application, full-workload behavior or chart eligibility. Compiled instruction
review, complete source-unit accounting and full measurements remain separate
requirements before publishing this implementation.

The [focused test suite](../../../tools/qualification/test_prolog_revcomp_bounded.py)
passes all 30 pure tests. It checks exact output and diagnostic bytes, required
source/runtime/fixture pins, process ownership and reaping, changed limits,
missing receipts, late plan/artifact changes, and failure retention. Its
synthetic process records are confined to temporary test directories; it never
launches Prolog or creates benchmark results. Independent controller review found
no remaining source-level blocker. Actual compilation, runtime diagnostics and
the full 540-case native cohort remain unverified until execution.
