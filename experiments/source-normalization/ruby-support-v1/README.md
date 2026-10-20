# Ruby embedded support partition candidate

This is a separate, **not applied** accounting review. The 19 protected Game source files, all 42 Ruby runtime profiles, historical samples, admission and retained counts stay unchanged. `review.json` binds the complete catalog and every Ruby profile and source digest, then proposes exact inclusive original line ranges for five reusable worker APIs. There are ten affected profiles: the original Ruby/YJIT profile and its independent ZJIT source alias for each file. The three fresh regex/pi YJIT aliases and first-call compact Fannkuch alias do not use these five files.

| Exact file | Proposed reusable support | Application retained outside the range |
| --- | --- | --- |
| binarytrees-ruby-5.rb | 12–103, `MiniParallel` | tree construction/checks, lifetimes, depth jobs, callback, serial fallback, output; line 10 thread import |
| mandelbrot-ruby-5.rb | 14–105, `MiniParallel` | arguments/header, row kernel, pixel packing, row-job construction and output; line 12 import |
| fannkuchredux-ruby-2.rb | 10–101, `MiniParallel` | `Fannkuch`, actual flips/permutations, weighted chunks, platform-specific dispatch, callbacks, merge, output; line 8 import |
| spectralnorm-ruby-5.rb | 5–74, `Worker` | matrix formula, both dense products and their worker callbacks, all 40 products, final reductions and output |
| knucleotide-ruby-1.rb | 44–62, `Worker` | FASTA input, every window/Hash update, query lengths, seven worker callbacks, order and output |

The three MiniParallel definitions accept arbitrary arrays and blocks, determine generic worker counts, move arbitrary jobs/results over pipes with Marshal, synchronize generic queues and close/join processes. Spectral-norm's Worker accepts an arbitrary enumeration and block and preserves result order; it contains no matrix arithmetic. K-nucleotide's Worker accepts an arbitrary block and returns its byte output; it contains no sequence or map logic. Each row in these complete definition ranges has a source-row digest and review classification, including structural syntax and whitespace. They are source-specific reviewed ranges, not a heuristic that excludes anything called Worker.

Benchmark-specific uses of these APIs remain application even when they only dispatch jobs. In particular Fannkuch's lines 172–221 remain counted: those lines select weighted permutation chunks, execute `Fannkuch.flip`, combine checksum/max and format output. Sharing the same API does not make these operations generic support.

The reverse-complement fork bridge (31–60) and regex count bridge (53–65) remain counted and deferred: each calls a fixed workload method rather than an arbitrary callback. Their application-specific orchestration cannot be removed by excluding a broad top-level wrapper. Revisit narrower ranges only with an explicit API-boundary review.

The proposal reports raw selected-text UTF-8 bytes and hashes, with original comments/whitespace included. Kept complete rows concatenate exactly as the existing raw source metric scope does. It intentionally gives **no replacement LOC count**: Ruby-native statement-owner and formatter qualification are needed before converting a new boundary into those measures. Physical row counts must not be subtracted from heterogeneous retained LOC. Gzip/BPE and canonical source reports remain unchanged until review is approved and the existing generators are deliberately rerun.

Reproduce without a Ruby process or benchmark:

```
python3 tools/test_ruby_support_partitions.py
python3 tools/ruby_support_partitions.py
python3 tools/ruby_support_partitions.py --check
```

The tests reject changed source bytes and unreviewed alias coverage, verify that application entry points remain included, partition every source byte, bind complete historical profile records and confirm that proposal generation does not write the catalog. Source acceptance/output or historical timings are not requalified by this accounting-only candidate.
