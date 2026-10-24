# Adjacent source cursor: exact-code profile

Compiler revision
[`c7574fa95`](https://github.com/mech-lang/mech/commit/c7574fa952a9981e1b2b0659a510fc05eff1c2ff),
IR74 / ABI27 / work65, carries a byte cursor for a source-certified adjacent
selection. The proof requires the actual index+1 recurrence and inclusive
range [index+1,index+width] over the admitted immutable one-byte-grapheme source.
The selected byte is therefore source[index+width-1]. The original scalar index
is recovered for source continuations. Stop and fuel-base arguments are
relocated in the caller, and exact fuel is reconstructed at exits.

This is an experimental lowering of the same source graph. It recognizes no
benchmark name, expected output or input sample. It retains every table update,
complete map, source failure origin and finite charge. Changed or unproved
recurrences retain the checked implementation. The Mech source and bytecode are
unchanged; this is not a call to the upstream Rust nucleotide implementation.

## Complete-process timings

Six balanced serial cohorts on 125 million selected bases retain every process,
including startup/shutdown and all outliers. There are no excluded full-input
warmups.

| Executable | Median seconds | × protected Rust time |
| --- | ---: | ---: |
| Protected upstream Rust | 0.5619 | 1.000× |
| IR73 parent | 0.7979 | 1.420× |
| IR74 cursor candidate | 0.7858 | 1.399× |

The median is 1.52% lower, but **only three of six pairs are faster** and ranges
overlap: candidate 0.7784–0.8097 s, parent 0.7767–0.8062 s. This does not establish
a robust speedup. The Rust outlier at 0.8357 s remains. Every Mech process verifies
the complete output, 874,999,961 physical updates, seven packed SSA maps and
peak workers under the unchanged secured policy. See the
[full cohort](../full-affine-cursor-cohort-v1/results.json).

The separate [one-million-base prefix cohort](../affine-cursor-timing-v1/results.json)
has Rust 0.0209 s, parent 0.0891 s / 4.259× and candidate 0.0885 s / 4.229×.
It retains one excluded warmup and three observations per subject. No prefix
gain is established; prefix and full observations are not pooled.

## Fresh profile and machine code

Three [completed exact-code profiles](../affine-cursor-remaining-profile-v1/results.json)
partition 6,844 worker observations. Every profiling executable matches the
entire machine-code section of its timed executable and verifies full output.

| Observed worker location | Observations | Share |
| --- | ---: | ---: |
| Generated counting loops | 5,776 | 84.40% |
| Storage helpers | 468 | 6.84% |
| Active work accounting | 299 | 4.37% |
| Accounting waits | 102 | 1.49% |
| Generated helper bridge | 88 | 1.29% |
| Other activity/waits | 111 | 1.62% |

These are sampled thread observations including waits, not elapsed-time shares
or CPU utilization. Capture distributions vary and do not assign individual
instruction costs.

The [38 explicitly assumed successful paths](../affine-cursor-codegen-audit-v1/steady-paths-v2.json)
across both emitted source functions have **37–39 instructions, five branches
and no stack access**. The parent's range is 37–40; the examined Rust path is
34 instructions/four branches. Static path counts are not dynamic frequencies.

The load now uses the cursor directly. However, source-counter reconstruction
still appears on the successful loop path. One retained path contains:

```asm
ldrb w5, [x13]
...
add  x13, x5, #0x1
add  x5, x11, #0x11
sub  x8, x13, x5
cmp  x13, x4
b.hs ...
```

The change in source representation did not remove the corresponding cold
state's native dataflow. [Separate whole-process counters](../affine-cursor-hardware-v1/results.json)
confirm only **0.27% fewer retired instructions and 0.63% fewer cycles** against
the parent: candidate 39.858 billion instructions / 10.505 billion cycles,
parent 39.967 / 10.572, Rust 33.139 / 7.928. These diagnostic processes are not
additional primary timing observations.

The next hypothesis is explicit cold reconstruction of source scalar/frame
values from proved affine recipes. A recipe must describe the exact original
value at each continuation, distinguish initial and completed edges, and retain
unknown values and original failures. Merely renaming the induction variable
or adding another invariant expression is insufficient. No speedup is assigned
to this unimplemented step.

## Validation, admission and rejected preparation trial

At the exact timed source revision, [365 native checks](../../native-owner-dispatch-v1/affine-cursor-native-v1/summary.json)
and the [catalog integration check](../../native-owner-dispatch-v1/affine-cursor-catalog-v1/summary.json)
pass, with three existing manual exclusions. Six targeted checks also execute
changed inputs, complete maps, all admitted widths, original/decoded source,
arbitrary seeds/headers, source overflow, declined proofs, precise finite limits
and refill frontiers.

Each funded function admits 21,268 code bytes and 112 stack bytes, including all
eighteen width arms and the generic arm. Entry/source/snapshot maxima are
92/79/23 inside the unchanged 512 envelope; caller work is 60 instructions and
fixed work 540 inside the unchanged 1,024 envelope. No allowance, worker count,
power setting, QoS or affinity is changed.

The preceding [source-alphabet scan trial](../proved-graphemes-diagnosis-v1/README.md)
passed 65 focused checks and emitted an identical entire Mech object, but its
full median regressed 1.54%. It is reverted to the exact IR73 tree before the
cursor experiment. Its failed initial profile setup, corrected capture and
all observations remain.

[Verification](results.json) recomputes both separate cohorts (36 full-input
observations), checks four completed exact-code captures, rejects twelve
malformed source-bound qualification fixtures, verifies immutable test revisions
and the restored source tree, and confirms 106 terminal owned-process receipts.
The sole failed process is the retained missing-policy profile setup. Canonical
benchmark data is unchanged. Rust parity remains incomplete; this checkpoint
establishes correctness and the remaining code-generation issue, not parity or
a general language-performance result.
