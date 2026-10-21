# C# retained implementation review

The [bound review](review.json) inspects ten complete local/derived source
bundles across nine workloads, shared by twenty JIT/AOT profiles. Nineteen
unchanged upstream profiles are protected. No protected program is rewritten,
and no runtime or performance claim transfers between JIT and NativeAOT.

| Workload | Retained design and next checks |
| --- | --- |
| Fannkuch #5 | Four workers claim factorial-rank blocks and perform byte-vector shuffles for actual prefix flips. ARM compatibility helpers retain the x86 shuffle/mask conventions. Inspect native shuffle lowering and every small-n/tail rank; compare scheduling only after preserving the complete permutation/checksum work. This is already a vectorized design. |
| FASTA #9 | Bounded output buffers and periodic ALU copying already exist. The local random-base path uses scalar cumulative lookup and one binary64 division per RNG value. Compare ordinary vector threshold selection or general distribution lookup while retaining every draw, seed transition and threshold rule; no cached generated period. |
| K-nucleotide #1/#8 | #1 already uses rolling integer keys, by-reference dictionary increments and seven independent tasks; #8 uses substring keys and repeated map lookup. Both local readers use prefix-only THREE selection and need comments/token/empty-record checks. The new general form retains full maps, removes line-to-byte temporary arrays, uses exact-length blocks and safely primes across short blocks. |
| Mandelbrot #2 | Scalar recurrence and `WriteByte` output are present, with corrected final-byte masking. Compare buffered rows, reused coordinates and bounded independent row work, retaining every requested pixel and all fifty permitted recurrence tests. No analytic-interior or periodicity shortcuts. |
| N-body #6 | Stack-allocated bodies and portable Vector256 operations retain the earlier AVX-oriented representation and grouped lane sum. API names or historical comments do not prove the actual ARM lowering. Capture hardware flags and emitted JIT/NativeAOT instructions, then compare smaller vectors or scalar storage without silently changing pair/update/reduction order. |
| Pi digits #6 | General GMP arithmetic through counted C# bindings; both digit extractions and spigot control remain C#. All digits are buffered on the stack. Review large-n stack size, complete GMP lifecycle and the exact ABI; no native pi executor is introduced. |
| Regex-redux #2 | PCRE2 JIT, byte buffers and parallel counts already exist. Native objects lack explicit disposal and return/error handling needs review. Ordinary .NET Count/source generation are distinct library/idiom alternatives, with all scans, substitutions and lengths retained. The protected managed #5 program remains unchanged. |
| Reverse complement #9 | SIMD byte mapping, pooled pages and reader/transform/writer threads are already present. The short-read loop reuses an unadvanced destination span, so multiple positive reads can overwrite the prefix. This is a source-derived path, not a newly observed native failure. Header/page/EOF parsing, 60-column assumptions and publication between threads need separate boundary/lifecycle review. |
| Spectral norm #5 | Two-lane division and independent parallel rows already exist; the temporary vector is allocated/pinned for each A-transpose-A call. Reusing one scratch vector preserves the source's forty dense products and numeric expressions. Allocation reduction may be insignificant beside the quadratic arithmetic. |

All authored compatibility methods, FFI declarations, parsers and orchestration
remain application source. `GeneratedRegex` declarations and attributes are
authored source; emitted framework-generator code is a separate compilation
artifact whose boundary must be reviewed, not a manually authored helper
silently excluded from LOC. Modules, collection expressions, expression-bodied
methods and literal wrapping need native Roslyn ownership/formatter evidence.
Raw physical rows, bytes, gzip and BPE remain separately labelled measures.

The regex alternatives expose different library boundaries without dropping any
authored bridge from the count. These are raw complete-file measures, including
comments and notices; native normalized/formatted counts are not approved.

| Regex source | Physical rows | UTF-8 bytes | Gzip bytes | BPE tokens |
| --- | ---: | ---: | ---: | ---: |
| Retained local PCRE2 adaptation | 167 | 6,837 | 2,014 | 1,717 |
| Ordinary managed draft | 33 | 1,695 | 814 | 483 |
| Source-generated parallel draft | 67 | 3,347 | 1,059 | 843 |

The [source/case preparation](preparation-v1.json) binds 208 pending native
candidate executions across JIT and NativeAOT. Of these, 194 are success-output
cases and fourteen are malformed-input captures awaiting the C# rejection
adapter. Four separate helper-diagnostic processes each contain eighteen
short-read checks. None has run. The prepared source comparisons verify numeric
body, map-update/summary, mask, regex-literal and reverse-complement-remainder
identity; they do not parse or execute C#.

Preparation uses the pinned source-measurement Python environment for its XML
reader. It changes no system packages:

```sh
experiments/source-metrics/.build/venv39/bin/python experiments/csharp/source-review-v1/prepare.py --check
experiments/source-metrics/.build/venv39/bin/python experiments/csharp/source-review-v1/source_measures.py --check
```

The project target is the retained `net10.0` cohort. The old manifest pins SDK
10.0.401 and its verified distribution; a fresh SDK/runtime/library preflight
and dependency closure are still required. Preparation does not install or
invoke .NET. Fresh JIT measurements must include process/CLR startup, assembly
loading, JIT, full work/I/O and shutdown; NativeAOT measurements must include the
same complete executable lifetime with compilation outside the interval.

Primary API references used for candidate preparation:

- [Regex.Count](https://learn.microsoft.com/en-us/dotnet/api/system.text.regularexpressions.regex.count?view=net-10.0)
- [.NET regex source generation](https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-source-generators)
- [Dictionary entry references](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.collectionsmarshal.getvaluereforadddefault?view=net-10.0)
- [MemoryStream.GetBuffer](https://learn.microsoft.com/en-us/dotnet/api/system.io.memorystream.getbuffer?view=net-10.0)
- [Vector256 hardware-acceleration indicator](https://learn.microsoft.com/en-us/dotnet/api/system.runtime.intrinsics.vector256.ishardwareaccelerated?view=net-10.0)

Retained medians below are historical complete-workload observations, not results
from this source inspection. Every ratio uses the cited Mech AOT profile on the
same workload/input. `review.json` retains source, samples, denominator and report
identities; JIT and AOT remain separate observations.

| Retained C# implementation | Mode | Seconds | × Mech AOT |
| --- | --- | ---: | ---: |
| fannkuchredux-csharpcore-5-arm64-faithful-aot | aot | 2.413904 | 1.42× |
| fannkuchredux-csharpcore-5-arm64-faithful-jit | jit | 2.421079 | 1.42× |
| fasta-csharpcore-9-arm64-faithful-aot | aot | 2.562407 | 4.73× |
| fasta-csharpcore-9-arm64-faithful-jit | jit | 2.257991 | 4.17× |
| knucleotide-csharpcore-1-arm64-faithful-aot | aot | 1.676538 | 3.26× |
| knucleotide-csharpcore-1-arm64-faithful-jit | jit | 1.486446 | 2.89× |
| knucleotide-csharpcore-8-arm64-faithful-aot | aot | 24.864513 | 48.39× |
| knucleotide-csharpcore-8-arm64-faithful-jit | jit | 23.890815 | 46.50× |
| mandelbrot-csharpcore-2-arm64-faithful-aot | aot | 49.847046 | 112.72× |
| mandelbrot-csharpcore-2-arm64-faithful-jit | jit | 50.022617 | 113.12× |
| nbody-csharpcore-6-arm64-faithful-aot | aot | 1.709337 | 1.64× |
| nbody-csharpcore-6-arm64-faithful-jit | jit | 1.736036 | 1.67× |
| pidigits-csharpcore-6-arm64-faithful-aot | aot | 0.305775 | 1.02× |
| pidigits-csharpcore-6-arm64-faithful-jit | jit | 0.323749 | 1.08× |
| regexredux-csharpcore-2-arm64-faithful-aot | aot | 0.685856 | 1.40× |
| regexredux-csharpcore-2-arm64-faithful-jit | jit | 0.697474 | 1.42× |
| revcomp-csharpcore-9-arm64-faithful-aot | aot | 0.077569 | 0.52× |
| revcomp-csharpcore-9-arm64-faithful-jit | jit | 0.098118 | 0.66× |
| spectralnorm-csharpcore-5-arm64-faithful-aot | aot | 0.121809 | 1.42× |
| spectralnorm-csharpcore-5-arm64-faithful-jit | jit | 0.321852 | 3.74× |
