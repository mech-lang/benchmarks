# Ruby JIT measurements

The retained Ruby submissions were measured with CRuby 4.0.7 on Apple M3. Both modes use unchanged source, normalized application LOC, full workload sizes, and the same worker policies. Times are medians of three complete-process samples, including startup and JIT warm-up. Output was independently checked in full.

Both engines use their default compilation thresholds. Cold methods can remain interpreted with a JIT enabled. These results measure the complete application under that policy; they do not claim exhaustive runtime tuning.

Sixteen YJIT profiles reuse historical samples whose recorded executable digest matches the current executable. The two regex profiles and the pi-digits profile have fresh YJIT samples because their historical reports lack that digest. Measurement dates and the comparison basis are retained per profile; this is not a claim that all YJIT samples were collected alongside ZJIT.

The ratio is ZJIT time divided by YJIT time; values below 1 favor ZJIT. The fastest retained source is selected separately for each mode.

| Workload | YJIT (s) | ZJIT (s) | ZJIT / YJIT |
| --- | ---: | ---: | ---: |
| binarytrees | 7.221 | 10.124 | 1.40× |
| fannkuchredux | 68.744 | 120.027 | 1.75× |
| fasta | 11.171 | 13.294 | 1.19× |
| knucleotide | 24.768 | 25.428 | 1.03× |
| mandelbrot | 33.545 | 109.033 | 3.25× |
| nbody | 56.653 | 129.157 | 2.28× |
| pidigits | 4.915 | 4.912 | 1.00× |
| regexredux | 4.415 | 4.415 | 1.00× |
| revcomp | 0.694 | 0.685 | 0.99× |
| spectralnorm | 19.606 | 23.489 | 1.20× |

Every retained source:

| Submission | Application LOC | YJIT (s) | ZJIT (s) | ZJIT / YJIT |
| --- | ---: | ---: | ---: | ---: |
| binarytrees-ruby-1 | 27 | 22.222 | 38.510 | 1.73× |
| binarytrees-ruby-5 | 117 | 7.221 | 10.124 | 1.40× |
| fannkuchredux-ruby-2-cpu4 | 174 | 68.744 | 120.027 | 1.75× |
| fannkuchredux-ruby-8 | 46 | 1079.721 | 1029.513 | 0.95× |
| fasta-ruby-2 | 66 | 34.762 | 48.819 | 1.40× |
| fasta-ruby-6 | 95 | 11.171 | 13.294 | 1.19× |
| knucleotide-ruby-1 | 50 | 24.768 | 25.428 | 1.03× |
| knucleotide-ruby-2 | 31 | 88.774 | 91.389 | 1.03× |
| mandelbrot-ruby-5 | 122 | 33.545 | 109.033 | 3.25× |
| mandelbrot-ruby-8 | 38 | 280.739 | 754.684 | 2.69× |
| nbody-ruby-2 | 110 | 59.954 | 142.120 | 2.37× |
| nbody-ruby-3 | 113 | 56.653 | 129.157 | 2.28× |
| pidigits-ruby-1 | 69 | 4.915 | 4.912 | 1.00× |
| regexredux-ruby-3 | 74 | 4.415 | 4.415 | 1.00× |
| regexredux-ruby-9 | 23 | 11.369 | 11.405 | 1.00× |
| revcomp-ruby-4 | 57 | 0.694 | 0.685 | 0.99× |
| revcomp-ruby-5 | 15 | 1.413 | 1.348 | 0.95× |
| spectralnorm-ruby-5 | 95 | 19.606 | 23.489 | 1.20× |
| spectralnorm-ruby-8 | 29 | 47.873 | 61.057 | 1.28× |

The measurements retain the original Benchmarks Game authorship and license records. No source was generated or rewritten for ZJIT. The [cohort record](../experiments/ruby-jit/README.md), [runtime/source plan](../experiments/ruby-jit/plan-v1.json), [full execution report](../experiments/ruby-jit/full-v1/report.json), and [reconciled observations](../experiments/ruby-jit/results-v1.json) retain commands, versions, environment, input/output digests, individual samples, power checks and source identities.

## First-call YJIT

The compact Fannkuch function is called once. Its default-policy compilation logs contain no kernel compilation entry; the first-call logs contain that function. The follow-up uses only `--yjit-call-threshold=1`, with no source changes, warm-up launcher, diagnostic preload or logging in the measured process. Startup and compilation remain inside every sample.

| Same source | Application LOC | Default YJIT (s) | First-call YJIT (s) | Speedup |
| --- | ---: | ---: | ---: | ---: |
| fannkuchredux-ruby-8 | 46 | 1079.7 | 316.7 | 3.41× |

The three full-size first-call observations are retained separately from every historical/default observation. The website selects the fastest qualified measured configuration for each endpoint. The opening comparison table reports default policies; the first-call follow-up is a separate configuration. The N=10 policy diagnostics are not chart observations or full-size estimates. Forced, zero-profile first-call ZJIT was slower in that diagnostic, and no full-size timing for that setting is claimed.
