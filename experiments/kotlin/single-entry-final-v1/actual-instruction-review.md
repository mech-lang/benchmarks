# Optimized-pi execution-path review

The final diagnostic completed one fresh direct-main execution at 10,000 digits.
The [review record](actual-instruction-review.json) binds its actual artifacts.
The saved native receipt and capture validator were independently replayed with
the observed controller PID 62776; the validated artifact inventory matches
exactly. JVM PID 62778 exited zero, was reaped, left no live group members, and
produced the expected 16,893 stdout bytes with empty stderr. Both prior failed
capture reports remain unchanged; none of their three executions was repeated.

The complete HotSpot XML contains 217 queued and completed compiler tasks,
217 installed compiler methods and 32 native wrappers. No normal-entry or OSR
`clbg.pidigits.MainKt.main` compilation appears. A separate whole-log scan also
finds no compiler method reference that could attribute an inlined main to a
different caller. This invocation therefore followed an interpreted main.

The actual loaded main class agrees with the retained optimized class bytes
and its checksum-bearing disassembly. Its bytecode is identical to the reviewed
compact implementation: loop header BCI 48, independent general
`BigInteger.divide` calls at BCIs 122 and 201, then comparison at BCI 216.
Both calls dominate the comparison. The accepted-digit and refinement backedges
return to BCI 48; there is no exception handler that enters the loop after either
division. An interpreted caller preserves both invocations even when the
division library compiles. No observed numeric count of loop iterations or
divisions is claimed.

All seven installed targeted division methods have complete retained machine
bytes and their exact printed method/compiler identities:

| Compile ID | Compiler | Method | Main-code bytes |
| --- | --- | --- | ---: |
| 145 | C1 | MutableBigInteger.divideMagnitude | 7,744 |
| 153 | C1 | BigInteger.divide | 648 |
| 154 | C1 | BigInteger.divideKnuth | 2,000 |
| 160 | C1 | MutableBigInteger.divideKnuth | 4,832 |
| 171 | C2 | MutableBigInteger.divideMagnitude | 6,312 |
| 218 | C2 | BigInteger.divide | 3,344 |
| 221 | C2 | BigInteger.divideKnuth | 3,160 |

This invocation has no installed C2 `MutableBigInteger.divideKnuth`; the earlier
compact invocation's eighth capture is not attributed to it. Actual library
origins, VM properties, G1 observations and diagnostic routing pass the saved
capture checks. These are diagnostic observations, not performance samples.

Together with the [other three execution reviews](../single-entry-remaining-v1/actual-instruction-review.md),
this closes the fresh-main tree/pi evidence collection. Qualification of all
twenty source forms still requires the combined decision record and full-suite
prerequisite adapter. Timing and chart admission remain ungranted.
