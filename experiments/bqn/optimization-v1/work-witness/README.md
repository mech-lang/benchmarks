# Untimed CBQN hash-work witness

This directory contains a patch for pinned CBQN commit `c893d3e7828899a50150df03ad33c9052fa51d3c` and a trace validator. The original checkout is not modified. Apply the patch only to a separate copy, build that copy only while holding the common compiler/benchmark lock, and exclude its executable from all timing samples.

`instrument-count.patch` adds stderr JSON lines only when `MECH_BQN_COUNT_WITNESS=1` is in the environment. With no flag, tracing is off. This debug patch still changes execution and must never be used for timings.

- Every completed `count_c1` invocation records its PID, per-process invocation serial, input length/rank/element type, whether its keys are boxed, and selected path: trivial, empty cells, boolean, sorted, brute force, indexed lookup, specialized hash, radix, widening, or generic hash.
- The generic path counts actual lookup-loop iterations, value writes, first insertions, increments of existing values, growth operations, initial/final capacity, and distinct keys. Its map begins at 64 slots and doubles.
- Ordinary public HashMap Get/Set calls also emit operation traces, including namespace identity, capacity, and population. This provides evidence for a singleton piece's explicit fallback. Running the original scalar implementation with this flag can generate an enormous trace: use this only on bounded inputs.
- JSON is formatted into a bounded stack buffer and emitted with one write per record to limit cross-process interleaving. Failed operations may terminate before a completion record; the validator then rejects missing evidence.

To separate workload calls from compiler/helper calls, add these markers around only the ordinal/hash-work block of each Frame operation in a separate untimed candidate. The marker format is:

```text
MECH_FRAME_WITNESS begin PID WIDTH FRAME PIECE ROWS
MECH_FRAME_WITNESS end PID WIDTH FRAME PIECE ROWS
```

Each line must go to stderr, include a trailing newline, and use that worker's actual PID. On this macOS host, BQN can obtain it through an ordinary zero-argument FFI binding:

```bqn
pid ← "/usr/lib/libSystem.B.dylib" •FFI "i32"‿"getpid"
Mark ← {𝕊 event‿width‿frame‿piece‿rows:
 •term.ErrRaw "MECH_FRAME_WITNESS "∾event∾" "∾(•Repr Pid ⟨⟩)∾" "∾(•Repr width)∾" "∾(•Repr frame)∾" "∾(•Repr piece)∾" "∾(•Repr rows)∾(@+10)
}
# In Frame, after computing keys and immediately before ord:
Mark "begin"‿width‿frame‿piece‿rows
# Immediately after ord and before grouping/query postprocessing:
Mark "end"‿width‿frame‿piece‿rows
```

The lowercase `pid` assignment is required to store the FFI value; the function reference is `Pid`. The parent runner has executed this binding in its frame witness; this reviewer did not execute BQN. The native counting expression must be eager inside the scope, and both markers must surround the singleton HashMap fallback as well. Keep all original Frame identities and eight pieces while using this validator's default partition calculation. A changed partition requires an explicitly updated expected-job model.

Validate a small trace, where FASTA N=1000 produces THREE length 5000:

```sh
python3 experiments/bqn/optimization-v1/work-witness/validate_witness.py \
  --stderr /absolute/path/to/debug.stderr --dna-length 5000 \
  --output /absolute/path/to/work-report.json
```

Use `--mode hashmap` for a bounded explicit-HashMap control. In occurrence mode, every piece with at least two keys must have exactly one boxed-key generic occurrence call, one lookup and count write per key, and correct doubling from 64 slots. Singleton pieces must use ordinary HashMap Get/Set; the primitive alone would return without hashing. Empty pieces require no updates. The validator requires exact Frame coverage, summing to `Σ max(0,N-k+1)` across widths; full input requires 874,999,961 updates and the canonical small input requires 34,961.

`--allow-unscoped` permits exploratory invocation-size matching and labels the result `heuristic-only`, never `pass`. It does not establish which Frame generated a call, and cannot prove a singleton fallback. A scoped pass records helper calls outside scopes separately. Verify exact stdout independently: a work trace does not establish correct output.

The validator's `--self-test` checks synthetic accepted and rejected traces without executing or compiling BQN.


For the window-start chunk candidate, pass `--chunk-size 100000` (or the exact
source constant). Keep the same marker format but identify each job as
`WIDTH CHUNK_START 0 ROWS`, where chunk starts are `0, chunk_size, ... < N` and
`ROWS=max(0,min(chunk_size,N-CHUNK_START-WIDTH+1))`. Every chunk must emit seven
separate scopes, including empty widths near EOF. Place each begin/end pair only
around that width's ordinal/native-hash block; grouping output afterwards may
invoke unrelated count primitives. Default frame/piece validation is unchanged.
The synthetic suite includes alternate chunk coverage and missing-chunk rejection;
the offline synthetic suite subsequently passed after the parent closed the native
execution window. An empty chunk plan (N=0) has no scope identity and is intentionally
not accepted as a standalone positive work witness by this validator.
