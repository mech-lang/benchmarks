# Kotlin tree allocation and pi division evidence

The [completed compiled-work run](run-v2/report.json) records twenty retained
forms, twenty JVM processes, one diagnostic compilation, and 200,000 checked
main returns. Its [terminal](run-v2/terminal.json) keeps full source-work
qualification false. Constructor/container witnesses, native method compilation,
and observed runtime dependencies passed; those claims do not establish every
allocation or arithmetic operation in the optimized main routines.

## Binary trees

The [counted source](../../../archive/languages/kotlin/20261013/drafts/private-v1/sources/binarytrees/Main.kt)
allocates both leaf and internal nodes at line 5, constructs the stretch tree at
line 10, retains the long-lived root from line 11 through line 21, and constructs
every short-lived tree at line 17. The corresponding
[retained bytecode](../../../archive/languages/kotlin/20261013/revisions/subject20-compile-owners-v1/jobs/subject20-compile-owners-v1/kotlin-binarytrees-optimized/owners/javap.stdout)
has `new Node` at tree BCIs 4 and 16 (lines 812 and 818), recursive constructor
calls at BCIs 23 and 29, and main constructor call sites 36, 52 and 93. Main
stores the long-lived root in local 3 at BCI 55 and reads it at BCI 139 before
the final check at 140 (lines 914–915 and 961–962).

Both actual JVMs recorded complete, disjoint constructor graphs and retained
the same 511 nodes across a normal G1 collection. These are separate reflective
calls in [WorkProbe.java](WorkProbe.java), lines 95–134; the probe itself retains
the root and applies `Reference.reachabilityFence`. They are not observations
of main's local variables or allocations.

The actual compiler records contain positive evidence of allocation elimination:

| Form | Successful normal-entry C2 main | `Node` allocation eliminations |
| --- | --- | --- |
| compact | compile 641 | [hotspot.xml](run-v2/kotlin-binarytrees-compact/hotspot.xml), lines 7786–7849 |
| optimized | compile 654 | [hotspot.xml](run-v2/kotlin-binarytrees-optimized/hotspot.xml), lines 8561–8623 |

Within optimized compile 654, line 4929 maps type 1398 to
`clbg.binarytrees.Node`; line 4930 maps method 1399 to `tree`. Nine elimination
records identify tree BCI 16: the root and its two immediate children at each
of main's call sites 36 (stretch), 52 (long-lived), and 93 (short-lived).
These are nine allocation **sites**, with short-tree sites reached repeatedly.
The task succeeds at line 8877 and its installed C2 nmethod is recorded at line
2243. Compact compile 641 has the same nine site stacks.

This establishes an allocation violation in the recorded repeatedly warmed
normal-entry compilation. It does not establish that compilation's use in a
fresh benchmark process: these tasks begin after roughly 1,900–2,400 main
invocations, whereas the timed entry shape calls main once. The saved OSR main
tasks, compact 615 and optimized 587, contain no `Node` elimination records.
Absence of such records is not a complete allocation or GC-root proof.

## Pi digits

The [counted pi source](../../../archive/languages/kotlin/20261013/drafts/private-v1/sources/pidigits/Main.kt),
lines 16–18, computes `(3*q+r)/t` and `(4*q+r)/t` before comparing candidates.
The [retained compact bytecode](../additive-compile-owners-v1/kotlin-pidigits-compact/owners/javap.stdout)
contains `BigInteger.divide` at BCIs 122 and 201 (lines 920 and 957), with
separate results compared at BCI 216 (line 964).

Both forms completed 10,000 calls at 27 digits with exact complete output checks.
Actual C2 main tasks compact 617 and optimized 607 inline both divide sites.
The [optimized compilation log](run-v2/kotlin-pidigits-optimized/hotspot.xml)
records the first call at lines 16248–16251, the second at 16721–16723, and
comparison at 17074–17076. The respective profile counts are 221,187, 221,186,
and 221,186. Compact records 229,318 at all three sites. These are snapshots
used during compilation, not terminal execution counts. Neither pi log
contains an assembly node, and the probe has no pi-specific division counter.
The retained evidence therefore establishes two authored general divisions and
hot participation of both call sites, but not their complete optimized runtime
execution contract.

## Targeted next observation

The [single-entry diagnostic](../single-entry-work-v1/README.md) covers only
binary trees and pi digits, with each retained alias in a fresh JVM. It invokes
the original main directly once at prescribed input 21 or 10,000. Diagnostic
output requests preserve the original tiered compilation, heap and GC policy.
The capture must retain native instructions, bytecode-location annotations,
compilation identities, and OopMaps for the relevant compiled versions.

The resulting review must trace actual surviving tree allocations and the
long-lived graph's roots across collection safepoints, and both general division
paths before each candidate comparison. A missing capture remains incomplete;
an observed removed required operation is a failure. Sampled allocations,
matching output, or an unchanged repeat of the reflective witness cannot replace
this proof. Any source correction or different VM policy needs its own disclosed
qualification; the existing scored sources and runtime settings remain pinned.
