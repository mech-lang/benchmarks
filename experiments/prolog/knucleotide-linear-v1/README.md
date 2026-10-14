# Prolog k-nucleotide: linear text access

This packet prepares a narrow correction to the retained k-nucleotide program.
It has not been compiled, executed, timed or admitted to the catalog. The
original sources and completed observations remain preserved.

The original k-nucleotide attempt was deliberately stopped on 14 October 2026
and remains unqualified; its deadline did not expire. The separate
[closure record](stop-v1/closure.json) confirms 54 preserved observations
(40 retained and 14 completed continuation observations), all 42 receipt files
for the 14 completed observations unchanged, and the owned processes and groups
closed. That record verifies the stopped cohort's evidence; it does not qualify
the corrected program below.

## Retained source finding

The original program constructs the third FASTA record with
`atomics_to_string/3`, then calls `get_string_code/3` for every base in each of
seven scans. The retained SWI-Prolog 10.0.2 source shows that this call copies
the complete string before reading the indexed character:

| Retained source | Relevant behavior |
| --- | --- |
| `src/pl-string.c:342` | `get_string_code/3` calls `PL_get_text` without `BUF_ALLOW_STACK`. |
| `src/pl-fli.c:907` | String text has storage `PL_CHARS_PROLOG_STACK`. |
| `src/os/pl-text.c:129` | `PL_from_stack_text` copies `length + 1` bytes for an ASCII string. |
| `src/os/pl-buffer.h:91` | `addMultipleBuffer` copies every requested byte. |

For sequence length L, the seven scans therefore request approximately
7 × L × (L + 1) copied bytes. The final character lookup itself is constant
time; the preceding full-string copy causes the quadratic work.

The retained [loaded-input record](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-knucleotide-compact/loaded-inputs.json)
identifies `swi(10,0,2,[])` on `arm64-darwin`. Its
[scored WAM](../../../archive/languages/prolog/20261013/qualification/prepare-explicit-goal-rest-v1/builds/prolog-knucleotide-compact/original-scored.wam)
retains the `get_string_code/3` call inside `windows/7`. Exact source-archive
and C-file digests recorded by the retained runtime packet are listed in
[source-review.json](source-review.json). They are recorded provenance, not a
new physical verification of the runtime or its machine instructions.

## Proposed correction

After parsing and measuring the sequence length, convert it once with
`atom_string(SequenceAtom, Sequence)` and pass `SequenceAtom` to the unchanged
`all_maps/4` loop. SWI-Prolog's [text input policy](https://www.swi-prolog.org/pldoc/man?section=string)
accepts atoms. In the retained version, `PL_get_text` obtains their heap-backed
pointer and stored length through `get_atom_ptr_text`, without the string-copy
path. The conversion and atom allocation remain inside whole-process timing.

Both [compact.pl](sources/knucleotide/compact.pl) and
[optimized.pl](sources/knucleotide/optimized.pl) contain identical corrected
bytes. They are source aliases, with no distinct optimization claim. All seven
widths (1, 2, 3, 4, 6, 12 and 18), complete maps, rolling keys, per-window count
updates, query counts, frequency ordering and output formatting are preserved.
The two support files are byte-identical to the original inputs. No runtime
flags, hash-table implementation or garbage-collection settings change.

Native compilation, bounded correctness, required-work inspection, source-count
review and resource behavior remain to be qualified before full-size timing.
This packet makes no measured speedup claim and supplies no replacement timing.
