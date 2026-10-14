# Recorded Prolog runtime metadata

`tools/qualification/prolog_metadata.py` reviews the retained runtime and
application-loading evidence after independent full-workload reconciliation.
It runs no compiler, runtime probe, or benchmark. Its source binds the reviewed
reconciliation implementation, the original full90 plan, and the retained
runtime configuration.

The records identify SWI-Prolog 10.0.2 running ARM64 bytecode/QLF applications.
QLF compilation occurs before measurement; runtime startup and application
loading occur inside the fresh-process timer. Each application declares one
compute worker. Saved probe and preparation records observe `gc=true`,
`bounded=false`, and an 8 GiB stack limit. These observations do not claim that
the timed processes were separately instrumented for loaded images or GC flags.

Regex programs use SWI's `library(pcre)` interface to the private application's
PCRE2 10.40 and `pcre4pl` images. Authored regex calls request `jit(false)`.
The native dependency closure also includes a private GMP image for arbitrary
integers. Its package version is not inferred from the library filename.
The retained seven-image probe closure includes diagnostic JSON support;
it is not presented as a list of images observed in every timed application.
Operating-system install names remain explicitly outside the file-hash closure.

The review binds the exact runtime command/environment, all authored source
files and compiled QLF artifacts, saved successful compilation receipts, and
each preparation's runtime flags and foreign-library observations. It preserves
compact and optimized profile identities and their recorded source aliases.
An alias does not imply a distinct algorithm. Profiles that failed the full
workload are excluded from import candidates without borrowing their alias's
results. A failed matched Mech control retains the reconciliation's null ratio.
Each profile counts and loads `clbg_io`; reverse-complement and k-nucleotide
also count and load `clbg_records`. The 20 forms therefore bind 44 compiled
source copies, derived from 22 distinct authored source files.

The command requires the existing durable-worker lease, Prolog cohort lease,
and common timing mutex without waiting. After the job has ended, it verifies
the supplied reconciliation digest, rechecks its file closure, reruns the pure
ledger reconciliation, validates runtime metadata, and rechecks the files and
closed measurement inventory. It writes a new artifact outside that inventory.

From the repository root, after the independent reconciliation completes:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -I -S -B \
  tools/qualification/prolog_metadata.py \
  --reconciliation experiments/prolog/reconciliation-v1/review.json \
  --reconciliation-sha256 ACTUAL_RECONCILIATION_SHA256 \
  --durable-directory experiments/prolog/full90-v1/owned-jobs/full90 \
  --output experiments/prolog/runtime-metadata-v1/review.json
```

The digest placeholder must be replaced by the completed reconciliation's
actual SHA-256. Synthetic tests exercise metadata changes, rejected failures,
source aliases, foreign dependencies, and exact storage handling. They grant
no runtime qualification. A successful file review qualifies only the recorded
runtime publication metadata; chart admission remains false until explicit
dataset import and website validation.
