# Ruby YJIT and ZJIT comparison

This cohort runs the 19 retained Benchmarks Game Ruby submissions across all ten full workloads. The source programs, normalized application LOC, attribution, input sizes, and worker policies are unchanged. Only the selected CRuby JIT changes.

Both engines use the same Homebrew CRuby 4.0.7 executable. `plan-v1.json` records its digest, build options, operating system, source and portability-helper digests, complete commands, environment, and explicit probes showing that `--yjit` and `--zjit` activate the intended engine exclusively. Ruby documents these engines in its [YJIT](https://docs.ruby-lang.org/en/4.0/jit/yjit_md.html) and [ZJIT](https://docs.ruby-lang.org/en/4.0/jit/zjit_md.html) manuals.

Sixteen retained YJIT profiles have the exact executable digest in their historical measurement reports. Their three samples remain historical observations with their original dates. The other three profiles have saved version strings but lack the executable digest; this cohort collects fresh YJIT samples for those profiles. All 19 ZJIT profiles receive three fresh, complete-process samples. No other language is remeasured.

`bounded-v2/report.json` records 38 checks: each source runs once under each engine with a smaller workload, and each ZJIT output must equal its paired YJIT output. This checks engine agreement and does not replace the independent full-size output check. The earlier `bounded-v1/input-preparation` directory retains a setup attempt that stopped on a recorder path error before any comparison sample; it is not timing evidence.

All native work is serial under `/tmp/mech-clbg-timing.lock`. Full samples require AC power, disabled low-power mode, and no competing benchmark or compiler process. Timing starts before process creation and ends after process exit, including startup, source loading, JIT compilation and warm-up, workers, input, all required work, complete output, and shutdown. Output hashing and validation occur afterward. Every full output must match the suite's complete reference output (N-body uses the existing energy tolerance of 1e-8). The source and executable digests are rechecked before each process.

The four-worker policy of the retained parallel Fannkuch submission and the eight-CPU portability fixture used by other parallel submissions remain unchanged. Published sources are neither rewritten nor tuned for ZJIT.

Reproduction:

```sh
python3 tools/qualification/ruby_jit_run.py --mode bounded --output experiments/ruby-jit/bounded-replay
python3 tools/qualification/ruby_jit_run.py --mode full --bounded-report experiments/ruby-jit/bounded-replay/report.json --output experiments/ruby-jit/full-replay
```

The plan is tied to the recorded executable, sources and controller. A different runtime requires a newly reviewed plan. A stopped measurement can resume with the same arguments plus `--resume`; completed samples are retained.
