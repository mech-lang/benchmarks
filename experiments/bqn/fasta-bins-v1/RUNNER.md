# Prepared serial execution, not yet run

`run_serial.py --prepare` reads/hash-checks sources, references and the existing runtime and writes `execution-plan.json`. It starts no BQN or compiler process. Root owns the later execution window and will close browser/publication work before running any mode below.

```sh
python3 experiments/bqn/fasta-bins-v1/run_serial.py --mode bounded --output experiments/bqn/fasta-bins-v1/bounded-v1
python3 experiments/bqn/fasta-bins-v1/run_serial.py --mode full --bounded-report experiments/bqn/fasta-bins-v1/bounded-v1/report.json --output experiments/bqn/fasta-bins-v1/full-matched-v1
```

The bounded stage first executes the standalone139,968-state lookup equivalence test. This is untimed qualification, and its output, source snapshot and raw process receipt are retained separately. It then runs all three sources on all16 shared FASTA cases in shuffled sequential source order:48 whole-source attempts plus the lookup test. The complete empty-safe source must match all16 complete independent outputs. The unchanged parent and minimal Bins source retain their original empty-state pick. Their n0 attempts must fail normally with diagnostics and the exact two already-written header lines. The report explicitly marks these as known control failures with `output_valid=false`, separately from `qualification_valid`; they are not accepted as candidate output passes. Any unexpected outcome stops the packet without automatic retry. Positive controls must pass exactly.

The full stage requires the exact successful bounded packet and rechecks saved streams/raw receipts. It measures only `parent-faithful` and `bins-empty-safe`, in three deterministic shuffled matched rounds, six fresh `[BQN, source, "25000000"]` processes. Every full process requires zero stderr and the exact complete254,166,745-byte FASTA hash. All sample times are retained. Startup, parsing, every naive LCG update, floating-point probability lookup, formatting, output and process exit are timed. Hashing, power checks, source snapshots and reference validation happen outside those intervals.

Both stages use `/tmp/mech-clbg-timing.lock` nonblockingly, the exact existing release runtime SHA-256 `0d39846db5f4727c59e6cb652328481e5d4c80d1bce28158172bd0c71d7305d5`, the pinned saved process helper, and AC-power/low-power-mode gates before and after every process. New output directories are mandatory. Reports preserve source/runtime/support pins, invocation order, source/controller/test snapshots, source commit, raw stdout/stderr/process receipts and power checks. No new native helper, runtime modification or application import is involved. No execution has been performed by this preparation stage.

`source-ownership-v1/bins-empty-safe-counts.json` proposes24 normalized /24 physical under the exact retained BQN rule; approval is deliberately false and canonical application LOC unset. It is a manual exact-source extension, independent of future timing qualification. The existing24/24 parent and all historical observations remain unchanged.
