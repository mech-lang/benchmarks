# Prolog: fifty remaining full-workload processes

This continuation completes the original three-sample, ten-workload study by
retaining forty validated samples and executing only its fifty unfinished
slots. The retained measurements comprise nine regex-redux samples from the
[original study](../full90-v1/README.md) and all 31 successful attempts from the
[linear reverse-complement continuation](../full81-linear-v1/README.md).

The latter producer stopped between attempts after its fourth Mandelbrot
sample. Its report remains `stopped-unqualified`; the exact SIGTERM request,
`KeyboardInterrupt`, durable exit −2, and clean terminal are preserved. The
[stop closure](../full81-linear-v1/priority-interpreter-stop-v1/closure.json)
records zero interrupted native attempts. No failed process is reused as a
measurement. The original interrupted quadratic reverse-complement attempt
remains excluded.

The [concrete plan](plan-v1.json) binds 20,750 file hashes, including all source,
compiled artifacts, runtimes, workload inputs, prior qualification evidence,
original controller plans, and saved process receipts. Its SHA-256 is
`fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195`.
Preparation completed without launching a benchmark, compiler, or runtime
probe. The destination `run-v1/` does not yet exist.

## Exact remaining schedule

| Workload | New processes | Retained samples |
| --- | ---: | ---: |
| Regex-redux | 0 | 9 |
| Reverse-complement | 0 | 9 |
| Pi digits | 0 | 9 |
| Spectral norm | 0 | 9 |
| Mandelbrot | 5 | 4 |
| FASTA | 9 | 0 |
| K-nucleotide | 9 | 0 |
| Binary trees | 9 | 0 |
| N-body | 9 | 0 |
| Fannkuch-redux | 9 | 0 |
| **Total** | **50** | **40** |

The fifty new slots contain 33 Prolog processes and 17 matched Mech AOT
controls. They retain the original round rotations and full input sizes. The
first slot is Mandelbrot round 2's Mech control; the last is Fannkuch-redux
round 3's optimized Prolog form. The two reverse-complement profile names
still represent explicitly equivalent source aliases, with no distinct
optimization claim.

Each retained sample carries its original report path and hash, cohort,
attempt number, raw receipt, supervisor receipt, outer ownership receipt,
seconds and validation. New attempt numbers start at one in the new output
directory. Per-profile `retained_attempts` use cohort-qualified identities, so
identical attempt numbers from different producers cannot collide.

## Measurement and closure

The [controller](../../../tools/qualification/prolog_remaining_full.py) reuses
the frozen native sampler and process-ownership supervisor. It preserves fresh
process wall timing, including runtime startup, QLF loading, full input,
complete computation, output and shutdown. Compilation, file hashing and
output validation remain outside the native timer. Each native process keeps
the existing six-hour deadline, 10,240 MiB sampled process-group RSS limit and
22,200-second ownership-supervisor deadline.

The controller continuously holds the common timing mutex, original durable
lease, original suite lease and stopped continuation's durable lease while
checking prerequisites, running subjects, cleaning up and closing receipts.
It verifies all retained file hashes before execution and at finalization.
Every new attempt retains raw, supervisor and outer ownership receipts; their
validated hashes are checked again against the final inventory. Signals are
masked while committing lifecycle transitions and closing the terminal.

An isolated full-workload failure preserves earlier successful observations
and skips only later slots for that failed profile. It never retries a slot or
promotes a partial failed profile's median. Integrity, environment and
ownership failures stop the continuation. Fresh plan, output and durable job
paths prevent accidental repeat launches.

This is a study spanning three measurement periods. Workload ratios use the
three matched Mech control samples belonging to that workload, including the
preserved Mandelbrot control. The sampler retains complete-output byte
counts, hashes and validation receipts; it discards successful stdout bytes.
Producer reports keep `full_timings_qualified=false` and
`chart_admission=false`. Independent reconciliation and runtime/publication
review are required after actual closure.

## Launch

The prepared controller and plan require the exact physical paths below. The
existing durable launcher creates a fresh job and passes the target command
without adding options to its argv:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/experiments/prolog/full90-v1/launch_durable.py --job linear-remaining50-v1 --cwd /private/tmp/mech-benchmark-completion --command-json '["/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12","-I","-S","-B","/private/tmp/mech-benchmark-completion/tools/qualification/prolog_remaining_full.py","run","--plan","/private/tmp/mech-benchmark-completion/experiments/prolog/full50-remaining-v1/plan-v1.json","--plan-sha256","fef4341ebee2d6cf8ef2d0fab618abe6be90d24ec180b8d7036f9e8f37fd4195"]'
```

The launcher stores lifecycle records under
`experiments/prolog/full90-v1/owned-jobs/linear-remaining50-v1/`. The target
command owns the common timing mutex. No native process was launched while
preparing this packet.

## Independent review

1. Verify the controller, test and plan hashes. Replay the pure test suite:

   ```sh
   /Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B /private/tmp/mech-benchmark-completion/tools/qualification/test_prolog_remaining_full.py
   ```

2. Check the exact stopped durable argv, parent and birth identities, signal,
   exit code, complete 31-attempt ledger, zero interrupted native attempts,
   terminal pin closure and released owner lease. Replay all 31 raw,
   supervised and outer ownership receipts plus the nine original regex
   samples; do not reinterpret either stopped producer as successful.
3. Verify that `retained_slots` are exactly original schedule positions 1–40,
   `remaining_slots` are exactly positions 41–90, and each of the thirty
   profiles has exactly three combined slots. Compare manifest/runtime/input
   policy to the frozen full81 plan; no source or workload changes are made.
4. Review fresh-output requirements, continuous common-lock ownership,
   unchanged native sampling, signal-safe cleanup, snapshot closure, and
   failure skipping. The sixteen tests cover saved receipt replay, changed
   identities, missing/unowned receipts, repeated or reordered slots,
   nonfinite observations, altered snapshots and preservation of retained
   samples when a future matched control fails.
5. After actual closure, independently reconstruct all per-profile sample
   arrays, medians and standard deviations from three cohorts. Validate new
   durable/terminal linkage, process births, sequential timing intervals,
   exact stdout validation records, source/runtime metadata and every final
   artifact hash before producing any publication candidate.

Controller SHA-256:
`d5921e9807413dbd720bd38fd42b3f0ff2984553216e8ab6ca2b558092e09147`.
Test SHA-256:
`8c059d2e0120dbfc2d228bedf4752120f0e293ba7a814c8d80a35878e87a2a5f`.
The saved-data test suite passed all sixteen tests in 1.42 seconds.

## Runtime estimate

The saved full-size Mandelbrot samples were 816.01 seconds for compact,
827.59 and 819.82 seconds for optimized, and 0.47 seconds for the matched Mech
control. Applying each profile's observed median to its remaining slots gives
about 2,457 seconds, or 41 minutes, for the five unfinished Mandelbrot slots.
This excludes file validation and environment waits. No full-size observations
exist yet for the remaining five Prolog workloads, so a dependable total
runtime estimate is unavailable.
