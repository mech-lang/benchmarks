# Closed validation orchestration failure

The initial 74-check Python run completed with 73 passes and one lock error. The
outer validation wrapper held the shared timing mutex while the historical Nim
formatted-source overlay tried to acquire it internally. The verifier was not
changed or bypassed. The corrected wrapper runs pure offline verification
without an outer lock and retains the common lock for native browser jobs.
No benchmark/compiler subject was launched and the failed test process closed
and was reaped. Complete output and the original wrapper are retained here.
