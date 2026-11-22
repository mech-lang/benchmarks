# Mechdeflate at level 12 on the full Silesia corpus

On the Apple M1, Mech won **11/12 against Roc** and **9/12 against libdeflate** in each order. The median paired elapsed-time ratio was **0.924417× Roc** and **0.878235× libdeflate**. All 12 files produced byte-identical raw DEFLATE across all three encoders. Each stream independently inflated to the original input.

The local Roc build won 6/12 against libdeflate. Its median elapsed-time lead was 0.32%. Feldman's M1 chart gives Roc 7/12 wins and a 2.48% median level-12 lead from the plotted per-file throughput pairs. [Feldman's chart](https://rtfeldman.com/fp-vs-c#chart) · [Feldman's benchmark script](https://gist.github.com/rtfeldman/7b6830809149867b79761ffb8e0456c3).

Each pair is the geometric mean of forward and reverse ratios. Each order uses all six permutations of the three actors, with one original-source-matched encoder invocation per actor per permutation. A common harness loads each file before timing and measures the encoder call with `CLOCK_MONOTONIC_RAW`. File I/O, output verification and release of the returned buffer occur outside the call clock. The codec and support artifacts match the published phase-route build. Roc uses the `671077457` codec source pin and the C peer is libdeflate 1.26. [Published phase-route build](../mechdeflate-phase-routes-v1/README.md) · [Build bindings](binding.json) · [Input hashes](corpus.json) · [Correctness record](complete.json).

| Full Silesia file | Mech / Roc time | Mech / libdeflate time | Roc / libdeflate time |
|---|---:|---:|---:|
| dickens | 0.927700× | 0.814930× | 0.878442× |
| mozilla | 0.906936× | 0.900814× | 0.993250× |
| mr | 0.957340× | 1.080888× | 1.129053× |
| nci | 0.837543× | 0.861073× | 1.028095× |
| ooffice | 0.921134× | 0.903426× | 0.980776× |
| osdb | 0.930159× | 0.895397× | 0.962628× |
| reymont | 0.894637× | 0.732698× | 0.818989× |
| samba | 0.837224× | 0.837553× | 1.000393× |
| sao | 0.959490× | 1.000379× | 1.042615× |
| webster | 0.940384× | 0.775892× | 0.825080× |
| x-ray | 1.084162× | 1.153258× | 1.063731× |
| xml | 0.806846× | 0.821296× | 1.017909× |

A ratio below one means the first encoder took less time. The exact medians and raw samples are available for both orders. [Scores](scores.json) · [Forward](timings-forward.json) · [Reverse](timings-reverse.json).

## Reproduce on arm64 macOS

The replay checks all actor binaries by SHA-256. The input downloader uses Feldman's twelve exact compressed input pins.

```sh
curl -fsSL https://raw.githubusercontent.com/rtfeldman/roc-deflate/671077457ff7ef3a3d44caf715a3fc595addf379/benchmark/Silesia.roc -o /tmp/silesia-pins.roc
python3 fetch_silesia.py /tmp/silesia-pins.roc /tmp/silesia-inputs
python3 replay_silesia.py --corpus /tmp/silesia-inputs --output /tmp/silesia-run
python3 score_silesia.py /tmp/silesia-run /tmp/silesia-inputs/corpus.json
```
