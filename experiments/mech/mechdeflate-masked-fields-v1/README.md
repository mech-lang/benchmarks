The masked-field compiler rule is source-integrated at [`09d4ea14c`](https://github.com/mech-lang/mech/commit/09d4ea14c9a560d91d5e6ff9404dcde4655408f6) in [Mech #995](https://github.com/mech-lang/mech/pull/995). Another compiler agent can rebase on this commit. The original 2,719-line codec and canonical bytecode are unchanged; Mech gains no LLVM dependency.

**All 81 Roc and 63 libdeflate wins hold in both full 81-case, 96-block orders for both new variants. There is no 64th win.** The previous recipe remains primary (`control`): the new standard is effectively flat on random 1 MiB and **4.9–5.2% slower on distribution-change 16 KiB**. The new variants remain qualified alternatives for repair and combination.

| Metric | Previous primary | New standard | New compact |
|---|---:|---:|---:|
| Encoder text |63,720 B|63,704 B|63,672 B|
| Text saved from its corresponding previous recipe |—|16 B|16 B|
| Random 1 MiB |20.915–20.917 ms|20.906–20.908 ms|20.929–20.938 ms|
| Random 1 MiB / C paired time |See raw control rows|1.029–1.031×|1.032–1.032×|
| Peak stack |4,832 B|4,848 B|4,848 B|
| Stripped executable |210,024 B|210,024 B|210,024 B|

The new standard's matched random-1-MiB change is **0.999277× /1.000502× control**: one order slightly faster and the other slightly slower. Its whole-suite geometric point estimates are **1.003176× /1.005571× control**. Overall runtime is slightly slower. Small slowdowns without lost named wins are allowed; all earlier partials remain available.

The actual matcher executes **164,668,189 →162,579,415 instructions**, a reduction of **2,088,774**. All **1,044,626 LDPs and 2,097,082 prefetches** remain. SP load instructions remain 10,151,519. An initial three-instruction fold was flat and its compact screen narrowly lost natural 4 KiB; it is retained. Widening then exposed an emitted self-copy. Tying the destination directly to the virtual input removes that copy; allocation inserts a copy for a shared input, and fixed physical inputs receive a virtual copy.

For the actual unsigned-byte projection `(x &1) |((x >>5) &6)`, the backend can emit:

```asm
lsr x3, x1, #6
bfi x1, x3, #1, #63
```

This requires a proved full-word unsigned bound and a low-bit base mask. Arbitrary dirty narrow registers are not assumed clean. The general disjoint-mask rule uses three instructions. Unsupported signed/variable shifts, overlaps, noncontiguous fields and out-of-range combined shifts retain their existing lowering. The rules preserve guards, memory order, shared values and finite admission.

`MECH_ARM64_INSERT_MASKED_FIELDS=1` retains the initial masked insert; `wide-copy` retains the earlier widened insert; `wide` enables the tied variant. Compiler defaults stay unchanged. Complete recipes also apply their declared allocation and layout profiles; use the scripts below.

| Fresh original source through final executable link | Median |
|---|---:|
| Mech control |2.195255 s|
| Mech new standard |2.192253 s|
| Mech new compact |2.193318 s|
| Roc |2.986928 s|
| libdeflate C |0.482822 s|

Ten balanced serial orders on **Apple M1 / macOS 15.6.1 / arm64** use equally prebuilt compilers and fixed support; final executable linking is included. Construction and stripping are separate. Standard paired build time is **0.998433× control, 0.733954× Roc, 4.541348× C**; compilation time is effectively unchanged. Parse/frontend/native/link medians are **0.676026 /0.222267 /1.221471 /0.035004 s**. Independent phase medians do not add exactly. No heavy job overlaps primary runtime or complete-build clocks.

Encoder text is **1.104× Roc /1.718× C**. The reference encoder text sizes are **57,696 B Roc /37,080 B C**, counting all text sections in the actual generated encoder artifacts. Stripped executables are **191,912 B Roc /155,752 B C**; Mech is **1.094× /1.348×** these sizes. Lookup data stays **3,200 B**, while the whole object const section is separately **17,728 B**. Stack remains below the 5,280 B cap.

Private and public native tests each execute **6,709,248 actual calls** across four modes, I32/I64, none/speed optimization, dirty bits, shared/fixed/zero inputs, joins, signed narrow values, ordered aliased loads/stores, modulo counts, invalid combined shifts and rejected null pointers. The public function records match the private records exactly. **13,056 earlier native function records** are compared exactly, including the retained copy implementation. Formatting, warning-policy and unsafe-boundary checks pass. Every new codec image passes 162 success observations, six named errors and 12 recovery pairs; normal/checked/inspection artifacts agree.

The build matrix contains **50 timed builds**, plus warmups. Every actor produces one identical stripped-executable hash across all trials; **405 actual executable outputs** independently inflate and satisfy their expected-byte rules. There are **18 public exact-artifact replays**. The independent verifier recomputes raw timing observations, scores, instruction totals, source bindings, public native records, build medians and saved streams. Full GPU/CI and formal confidence are not claimed.

```sh
python3 reproduce.py --mech-root /path/to/mech --output /tmp/field-compare
python3 reproduce.py --mech-root /path/to/mech --output /tmp/field-compact --role tied-linear65536
python3 reproduce.py --mech-root /path/to/mech --output /tmp/field-sqrt --role tied-sqrt65536
python3 probe.py --mech-root /path/to/mech --output /tmp/field-native
python3 verify.py
```

[All 18 primary loss margins](primary-losses.json), [all candidate case times and parity gaps](parity.json), [hot blocks](hot-block-census.json), [all recipes](recipes.json), [raw manifest](raw-manifest.json) and [next experiments](next-experiments.json) are retained. The square-root allocation trial also preserves the screened wins but is slower on the target and distribution case; it is not fully qualified. The next experiment will isolate shifted logical merging versus BFI latency and allocation/frame effects. **64 C wins is next; parity across all 81 cases remains the goal.**

The raw archive is stored in three parts below the repository file-size limit. `verify.py` checks each part and reconstructs the original archive in memory. The complete archive SHA-256 is in `archive.json`.
