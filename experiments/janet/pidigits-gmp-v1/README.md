# Janet pi-digits GMP-leaf study

Eight local Janet sources implement the required sequential unbounded spigot.
The complete advance, both candidate extractions, acceptance/removal decisions
and output formatting remain in Janet. Unmodified GMP 6.3.0 supplies only general
arbitrary-precision arithmetic and conversions. No pi generator, digit cache,
approximate quotient, alternative spigot or fixed-width arithmetic replaces the
big-integer state. Every FFI declaration and authored helper is application source.

- `parent`: the unchanged v2 application.
- `fused`: ordinary GMP `addmul_ui` advances the accumulator without a full-size
  product temporary; `submul` removes a digit without a separate multiply/subtract.
- `fused-combine`: additionally copies the accumulator and uses `addmul_ui` to
  construct the first extraction numerator. Both divisions remain independent.
- `unsigned-digit`: changes only the conversion of an accepted digit to the
  unsigned API, with an explicit Janet `int/to-number` conversion.
- `combined`: the fused/combine form with that unsigned digit conversion.
- `positive-division`: fused arithmetic with two ordinary `tdiv_q` calls rather
  than two `fdiv_q` calls. Numerator and denominator stay positive. The guard
  `accumulator > numerator`, with positive numerator/denominator, makes both
  extraction numerators positive; floor and truncation therefore agree. Both
  arbitrary-precision quotients are still actually evaluated. No exact-division,
  remainder shortcut or narrowed quotient comparison is used.
- `compact-positive`: combines the shorter initializer with positive-division arithmetic.
- `compact`: fused arithmetic with a single destructuring/map initializer for
  the six independently initialized GMP values. It preserves all six lifetimes
  and clears; it is not a shared zero object.

The unsigned conversion is only used after accepting an emitted value in 0..9.
No unbounded state or candidate comparison is converted to a machine integer.
Janet returns C unsigned-long values as `core/u64` objects; the explicit numeric
conversion is necessary and is included in scored source. A cheaper-looking C
conversion is not assumed to be a faster Janet operation.

## Correctness and work

`qualify.py` and `qualify_refined.py` cover twelve sizes from zero through 257,
including line boundaries and the official N=30 example. All retained original
corpus outputs match the independent Python arbitrary-integer reference.
Across eight sources there are 96 complete application outputs and 96 diagnostic
state traces. The latter compare every advance state, both actual GMP quotients,
every emitted digit and every removal state, including negative accumulators.
Each trace also verifies six native initializations and six native clears.

The diagnostic GMP string-conversion bindings and trace helpers are not in the
production sources. Their extra allocations/I/O are never timing observations.
`qualification-v1` retains the first diagnostic failure: the size query returned
an unsigned wrapper where `buffer/new-filled` required a numeric size. The
corrected helper explicitly converts this bounded diagnostic buffer length.
The two initial unsigned-output drafts remain under `attempts-v1`; they were not
accepted timing subjects. Final evidence is in `qualification-v2` and
`refined-qualification-v1`.

`check_full_work.py` and its refined follow-up run complete 10,000-digit outputs
with actual per-call counters and no huge state trace. Every source performs:

- 33,209 advance steps;
- 22,454 extract(3) calls and 22,454 extract(4) calls;
- 10,000 digit emissions and 9,999 digit removals;
- six GMP initializations and six GMP clears.

The independent Python reference produces all 16,893 output bytes and matches
the retained historical full-output SHA-256. Full output is compared, not merely
a prefix or final digit. Formulas and expected digits occur only in validation,
never in an application. These checks qualify the explicit input domain and
source identities; they do not certify arbitrary FFI programs.

## Library, lifecycle and timing

Read-only `DYLD_PRINT_LIBRARIES` captures verify that complete parent and candidate
applications load the exact pinned GMP library. Static `otool -L` metadata and OS
build evidence are retained. A known `otool` temporary-directory fallback warning
is accepted only as that exact diagnostic with zero exit; arbitrary stderr is
rejected. The initial stricter metadata attempt remains in `library-v1`; final
captures are in `library-v2`, `refined-library-v1` and `composed-library-v1`. No debugger, root access,
security setting change or runtime modification is needed.

`full.py` records seven shuffled sequential rounds across the initial five
sources (35 observations). `full_refined.py` adds a seven-way cohort after
qualifying two further candidates (49 observations). `full_final.py` then tests
the composed compact/positive form alongside all seven controls in a fresh
eight-way cohort (56 observations). All 140 observations remain separate by
cohort. The result table and paired analysis use only the final 56; earlier
cohorts are not pooled to select a winner. All valid observations remain.
Within-round parent/candidate ratios accompany the final medians because the
cohorts show temporal drift.

The official version-matched GMP release source is retained for inspection, with
its original notices and GNU license texts. `mpz_fdiv_q` allocates a remainder
and calls `mpz_tdiv_qr`; `mpz_tdiv_q` uses the quotient-only `mpn_div_q` path.
This supplies a source-level explanation for the measured positive-division gain.
The installed library is byte-pinned, but release-source inspection alone does
not prove a complete source/build-to-binary chain. Both required extractions
remain actual arbitrary-precision quotient calculations.

Each timed subject is a fresh standard Janet VM process. Source/FFI compilation,
library loading, all arithmetic, formatting, six native clears and shutdown are
inside the interval. The unchanged owner establishes child identity before exec,
observes exit independently, captures `wait4` resources, closes the group and
reaps the process. Validation and cleanup follow exit. Periodic live telemetry
is ordinary host activity inside observed wall time; later callbacks cannot
extend the independent exit timestamp. No other benchmark/native validation or
compiler runs concurrently. No power setting is changed or CPU throttling disabled.
Recorded power/process observations do not prove continuous temperature/frequency
or a pristine idle host.

The requested Mech AOT denominator is the retained same-input median of
`pidigits:mech-pi-final-advance-signed`. Both implementations use general GMP-backed
big-integer arithmetic; this study does not independently establish an identical
historical GMP binary/build for Mech. It is not a freshly paired control. These
exploratory results do not change the public chart or establish global optimality.
Nested output-validation receipts certify output only; native ownership and
source work have separate evidence.

## Source measures and reproduction

Physical rows, UTF-8 bytes, deterministic gzip, pinned BPE and native Janet grammar
lexical tokens are separate measures. Every binding/helper is included. Normalized
logical and canonical formatted LOC remain unqualified. The original parent
manifest preserves consulted implementations, contributors and applicable
Apache-2.0/BSD notices. Local authoring identifies Codex GPT-6 family; exact serving
model is unknown. Reproduce in clean output directories with the pinned runtime
and GMP present, keeping all native commands outside other timing windows:

```sh
python3 experiments/janet/pidigits-gmp-v1/qualify.py
python3 experiments/janet/pidigits-gmp-v1/qualify_refined.py
python3 experiments/janet/pidigits-gmp-v1/qualify_composed.py
python3 experiments/janet/pidigits-gmp-v1/check_libraries.py
python3 experiments/janet/pidigits-gmp-v1/check_libraries_refined.py
python3 experiments/janet/pidigits-gmp-v1/check_libraries_composed.py
python3 experiments/janet/pidigits-gmp-v1/check_full_work.py
python3 experiments/janet/pidigits-gmp-v1/check_full_work_refined.py
python3 experiments/janet/pidigits-gmp-v1/check_full_work_composed.py
python3 experiments/janet/pidigits-gmp-v1/full.py
python3 experiments/janet/pidigits-gmp-v1/full_refined.py
python3 experiments/janet/pidigits-gmp-v1/full_final.py
experiments/source-metrics/.build/venv39/bin/python experiments/janet/pidigits-gmp-v1/measure.py --run
python3 experiments/janet/pidigits-gmp-v1/analyze.py
python3 experiments/janet/pidigits-gmp-v1/verify.py
```

Workload: https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/pidigits.html
GMP arithmetic: https://gmplib.org/manual/Integer-Arithmetic
GMP division: https://gmplib.org/manual/Integer-Division
GMP conversions: https://gmplib.org/manual/Converting-Integers
