# Pony suite recovery after archive relocation

The retained suite contains 54 qualified fresh-process samples across the first
six workloads. Its supervisor stopped between samples when the repository moved
historical orchestration and evidence paths into `archive/`. The original stopped
report and failed-integrity terminal remain unchanged. The recovery controller
validates those samples, maps their evidence paths, and schedules the remaining
36 slots from the same 90-slot rotation.

`tools/qualification/pony_resume.py` has separate preparation and execution
commands. Preparation runs no benchmark, compiler, count replay or native probe.
It verifies all historical pins, permitting the three explicitly recorded
orchestration text replacements in `orchestration-supersessions.json` and the
eleven exact `chart_policy` narrative edits in `manifest-editorial-parity.json`.
For those manifests, in-memory reconstruction reproduced every historical hash;
all JSON other than that one narrative field is identical. Sources,
scored binaries, runtime libraries, compiler-bound source inventories, work
proofs, LOC evidence, inputs, output receipts and measurement modules retain their
original hashes. The historical orchestration documents are never executed.

The controller imports the original pinned process supervisor and sampler from
the retained execution host. It retains their timing boundary, complete-output
validation, eight-worker ceiling, four-hour timeout, 10 GiB RSS ceiling, power and
compiler monitoring, inherited common mutex and process-group cleanup. Programs
keep the exact original executable paths, arguments, working directories and
environment fingerprints. An integrity or environment failure stops the study;
there is no automatic retry. An isolated source failure is retained and follows
the original policy for independent profiles.

Preparation verifies every saved raw/supervisor pair and their qualification
gates, the first 22-sample report, the source-work closure, unchanged production
tree-allocation evidence and complete compiler-bound LOC bundles. It writes a new
plan containing the original and mapped pin inventories. Execution checks that
plan's hash and all its inputs again before dispatching slot 55. Previously
completed samples remain byte-for-byte equal as report entries and their original
files are never rewritten. New attempts and a new terminal go into a new output
directory.

Run preparation only when the shared timing host is idle. The pinned Python and
all original native artifacts must still exist; this is a continuation on the
original machine, not a portable rerun with substituted toolchains. Finish edits
to the migration path table before preparing the plan, since its bytes become a
pinned input. Use a new plan and output path for each preparation revision.

```sh
PONY_PYTHON=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
"$PONY_PYTHON" -I -S -B tools/qualification/pony_resume.py prepare \
  --retained-study archive/languages/pony/20261012/full-studies/pony-retained20-resumed-v1 \
  --retained-terminal-sha256 ec1b22744664932c287693ff0bf030d158adeb0423e83374631356b63fc26842 \
  --plan experiments/pony/migration-resume-v1/plan.json \
  --output experiments/pony/migration-resume-v1/results

"$PONY_PYTHON" -I -S -B tools/qualification/pony_resume.py run \
  --plan experiments/pony/migration-resume-v1/plan.json \
  --plan-sha256 SHA256_PRINTED_BY_PREPARATION
```

The controller does not admit results to the chart. Completion still requires
independent full-suite and runtime-publication review. A stopped or failed suite
remains evidence rather than a plotted score.
