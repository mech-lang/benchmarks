# Retained Lua pi-digit admission

The Lua 5.5.1 interpreter study completed on 2026-10-12. It contains twelve
N=10,000 source observations (four applications, three each) and six matched
Mech observations (two controls, three each). All eighteen original attempts
passed; none was retried. This packet prepares their additive admission without
executing another benchmark or changing the nine published Lua workloads.

The original gap was an unavailable `c-gmp` module and an incompatible `bn`
module. The completed study already repaired that dependency boundary with a
general GMP compatibility module. Its later
[family review](../../../archive/comparisons/r-apl-uiua-comparison/20261011/evidence/lua-family-complete-20261012T145204315140Z/receipt.json)
explicitly deferred chart admission until canonical whole-source counts were
reviewed. The current packet does not modify LuaJIT results.

## Retained programs and observations

| Listed form | Application work | Attempt numbers | Median seconds |
| --- | --- | --- | ---: |
| 1 | Immutable `bn` LFT, with impossible-candidate guard | 1, 12, 17 | 0.461363 |
| 5 | Mutable four-coefficient LFT | 2, 7, 18 | 0.569993 |
| 6 | Mutable endpoint-numerator LFT | 3, 8, 13 | 0.343833 |
| 7 | Mutable triangular LFT | 4, 9, 14 | 0.887403 |
| Mech fast control | Retained AOT source | 5, 10, 15 | 0.304468 |
| Mech compact control | Retained AOT source | 6, 11, 16 | 0.404603 |

These are descriptive retained observations, not a new admission. Form 6 is
1.12929 times its matched fast Mech control. All four Lua applications have
different source hashes and independently measured samples; there are no
timing aliases. The controller selected the ordinary Lua interpreter, not
LuaJIT. The C module implements general signed/mutable/immutable GMP operations;
the spigot, candidate selection, both quotient tests and output remain Lua.

[input-index.json](input-index.json) pins the retained report, manifest,
per-attempt receipts, launch receipt, validation, prior family review and all
46 original input pins. The original report SHA-256 is
`833761cabd812ff56d8f685097cbb664e87640e5d8a2f2043db945241315c789`.
The original manifest is `aaf6af5f…`; the public archived manifest is `4faf2cfa…`.
Only its `chart_policy` documentation sentence changed. Both identities are
checked separately; no report is rewritten to claim the archived hash was used
for execution. The archived preparation script has the corresponding
documentation-string change; the original script remains in the 46-pin closure.

## Source counts and required work

Every application bundle contains its exact measured `.lua` file and the
complete shared [support/gmp.c](support/gmp.c) file. The helper is counted once
per bundle, although its binary exposes both `bn` and `c-gmp` module names.
Upstream GMP itself remains a general library dependency. Original producer
counts, which excluded the helper, remain separately recorded.

[lua_pidigits_source_units.py](../../../tools/qualification/lua_pidigits_source_units.py)
maps each significant character of the four exact Lua sources to an authored
owner. Explicit function/control headers, written `end`/`else`, the label and
ordinary source statements retain their approved canonical treatment. The
application proposals are 62, 77, 63 and 57 units. This is an exact-source
review, not a general Lua parser or an inference from an unreviewed line count.
The complete C helper has an independent
[218-unit, 119-physical-line owner review](c-helper-owner-review.json).
The independent [Lua owner review](application-owner-review.json) and
[qualified complete bundle counts](qualified-source-counts-v1.json) retain
280, 295, 281 and 275 canonical units (181, 196, 182 and 176 physical lines).
Formatted counts remain unavailable.

The retained qualification contains 248 original/normalized application output
checks, eighteen Mech output checks and general arithmetic primitive tests.
Untimed N=97 traces verify 444 actual divisions for form 1 and 832 for each of
forms 5, 6 and 7: two actual exact divisions per tested candidate. The timed
commands use the unchanged application directly, with no tracer. Every full
observation retains the 16,893-byte output SHA-256 and successful reference
comparison.

## Reconciliation and publication boundary

[lua_pidigits_reconcile.py](../../../tools/qualification/lua_pidigits_reconcile.py)
reuses the frozen independent full-record validator; it never imports a
measurement producer. It joins all eighteen raw receipts to the completed
report, checks launch identity, ordered observation intervals, sample statistics,
source/runtime/module identity, required-work evidence and the independently
approved complete source bundles.

Its file phase acquires the existing common timing mutex without waiting. It
replays all 46 physical input pins, the retained evidence and count approval,
then holds the mutex through candidate creation and final input/output checks.
It cannot run while another timing owner holds the mutex. This phase has not
been executed for this packet.

[lua_pidigits_export.py](../../../tools/qualification/lua_pidigits_export.py)
prepares four inventory rows and the fastest/fewest-source endpoint proposal.
Its exclusive writer verifies output inode and bytes after the final input
replay. An error removes only still-owned output. It writes no catalog data.
The shared retained publication validator still needs an explicit Lua schema
and two-file-bundle admission before preview/apply; existing one-file language
rules must remain intact.

The narrow source tests use saved small documents and synthetic future
physical-phase flags in memory. They never save a fabricated native approval,
run a native process, replay runtime pins or read the current catalog:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -I -S -B tools/qualification/test_lua_pidigits_retained.py
```

Historical limits remain explicit: temporary stdout files were removed after
validation; their complete byte counts and digests survive. The receipts retain
native PGIDs and clean group closure, but lack modern per-native birth listings
and terminal files. Runtime dependencies are statically pinned rather than
invented loaded-image records. The original harness retained ambient environment
settings and a standard Lua module-search suffix. Short processes may finish
between RSS polls, so a recorded zero peak is not a zero-memory claim.
