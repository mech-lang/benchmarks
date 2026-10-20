# Preselected full-size Clojure comparison

Prepared before full-size execution. No subject, compiler, test or timing was
started while preparing this separate runner/plan. All earlier sources,
controllers, plans, bounded records, state proof and pilot records are unchanged.

The sealed 1,000,000-step pilot contains one complete-process observation per
source, including JVM startup, class loading/JIT, all work, both energies and exit:

| Source | Pilot seconds | Full-size selection |
| --- | ---: | --- |
| Original compact parent | 3.328331791 | Matched control |
| Scalar-updates intermediate | 2.775786959 | Retained pilot/qualified bounded evidence; omitted from full rounds |
| Primitive-updates | 0.274928458 | Selected candidate |

The candidate with the lowest observed pilot time and the original compact
control proceed to three shuffled sequential full rounds at **50,000,000 steps**.
The pilot supports this resource-saving preselection; it does not prove that the
intermediate is slower at full size, estimate a precise effect or supply chart
data. Its complete source, classes, state check, 30-case bounded cohort and all
three pilot observations remain available. No observation is discarded.

[plan.json](plan.json) binds 659 files, including the exact frozen execution
helper, runtime, classes, source/support, state proof, bounded/pilot reports,
raw process receipts, streams, independent reference and archived build helper.
It declares the selection and the three pilot times before any full process is
started. The separate [runner](run_selected_full.py) verifies those bindings and
the original three-source prerequisites, then uses the unchanged helper's owned
process, power and competition checks. It never mutates the helper's `NAMES` or
other constants. Full sources, workload and round count are fixed rather than
accepted as command-line substitutions.

The plan SHA-256 is
`aeb77e8c01e21e3136c09240ca2657a3d71bb61a460117eeab994bb71696e736`;
runner SHA-256 is
`e8aef3f962d206151191a54dd62be4e5dda90f4624c333ac9936afaa7ac11c4d`.
The original three-source execution-plan SHA remains
`cb43a5a01cfafa8c441e0c9ee8a13d1abcfe84cc1b14f3ff247bc74f96c92195`.

Root can first verify metadata and prerequisites without starting a subject:

```
python3 experiments/clojure/optimization-v1/primitive-v1/selected-full-v1/run_selected_full.py --check-only
```

Root owns the full invocation:

```
python3 experiments/clojure/optimization-v1/primitive-v1/selected-full-v1/run_selected_full.py --output experiments/clojure/optimization-v1/primitive-v1/selected-full-v1/run-v1 --timeout 600
```

The controller holds the shared mutex throughout verification and execution.
Every process inherits that lock and has a new owned process group, timeout,
complete raw stdout/stderr, native resource receipt and leftover-group check.
Six full observations include startup, HotSpot compilation, GC, every sequential
step, both energy evaluations, output/flush and process exit. Power and compiler
competition are checked outside each process timer. Source/runtime/class and
prerequisite pins are checked before and after each observation.

Full output must retain both complete finite energy lines under the established
1e-8 tolerance and the complete 26-byte stream; exact byte equality is also
recorded. Failures remain in their exclusive output directory and stop the run.
The report retains all samples, medians and sample standard deviations. The
plan also binds root's separate exact-source approval of **111 application LOC /
52 physical LOC** under the retained owner convention. This establishes neither a
uniform logical grammar nor formatted LOC. Full-work source review and any
append/publication remain separate gates; `chart_admission` remains false here.
