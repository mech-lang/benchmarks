# Published-source edit protection

Thirty-four profiles were marked locally adapted and editable despite complete
application source identity with cited published programs. The identity matches
were already present in the retained citation metadata, but the old ownership
classifier let a broad `local_adaptation` or `ai-adapted` flag override protection.
Runner/compatibility metadata cannot authorize modifying matching published code.

The corrected classifier keeps the existing origin classification and historical
metadata, while enforcing edit protection whenever **every application file**
matches a cited external implementation. Unmatched local application helpers
prevent complete-identity protection. Generic runtime support is outside that
application boundary. A local Mech repository URL does not establish external
published-source identity. Regression cases cover each of these boundaries.
Neither the guard nor this packet infers who copied a file or which AI wrote it.
The current generator writes a separate v2 inventory; the frozen v1 inventory is
not overwritten. Source license notices are retained in `LICENSE.benchmarksgame`
and `LICENSE.programming-language-benchmarks`; local tooling remains under the
repository license.

`capture-v1` retains original source pages/files, their response hashes, extracted
source bytes and URLs. There are 27 indexed URLs covering 26 distinct normalized
application sources. The only source normalization is CRLF to LF and trimming
surrounding whitespace. Comments, identifiers, strings and all interior layout
remain significant. Captured sources keep upstream trailing blanks; Git whitespace
checks are disabled only for those raw source captures, while their byte hashes
remain exact. `replay.py` re-extracts every indexed response and compares
all application bytes independently with the retained catalog.

The original per-profile acquisition stopped when the current JIT-mode n-body
URL no longer matched the retained file. That partial attempt is preserved,
including its unindexed response and source payload. The corresponding AOT-mode
published URL supplies the exact same application SHA already used by that JIT
profile. The separate replay therefore binds eight JIT source aliases to their
identical captured executable-mode sources. This transfers **source identity and
edit protection only**; it does not transfer builds, outputs or timings between
execution modes. `acquisition-review.json` pins the legacy classifier used by the
one-time acquisition; the later corrected classifier is a separate input to the
replay. Re-running that historical selection after the guard is fixed would no
longer select the same conflicts; replay is the reproducible verification step.

| Family | Newly protected profiles |
|---|---:|
| Dart | 16 |
| Swift | 8 |
| Fortran | 7 |
| V | 2 |
| Crystal | 1 |

The [coverage reconciliation](../coverage-v4/README.md) preserves prior snapshots
and removes these profiles from the editable optimization queue. It does not
claim a new performance review. Source, timing, LOC, licensing and canonical
attribution records are unchanged; the contradictory broad adaptation metadata
remains visible for a separate attribution reconciliation. Published program
bytes must remain protected in the meantime.

No language runtime or benchmark is executed by this audit. The HTTP acquisition
and static source inspection occurred alongside the serial Janet tree study and
were ordinary host activity, not additional timing subjects. No pristine idle
host claim is made for that study.

Verify without network access:

```sh
python3 experiments/implementation-audit/upstream-protection-v1/replay.py --check
python3 experiments/implementation-audit/coverage-v4/build.py --check
python3 -m unittest discover -s tools -p test_owned_implementations.py
```
