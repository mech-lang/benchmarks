# Closed standalone projection lock conflict

The corrected wrapper completed all 74 Python checks and the repository,
authorship, reproduction, source-metric and Python/Julia projection checks.
Its standalone Clojure projection check also acquires the common mutex itself,
so that command needs the same outer-lock exclusion as historical replay.
The verifier is unchanged. The failed closed process and wrapper remain here.
Passed checks are retained and resumed without re-execution; no data, timings
or source changed between those checks and the resumed validation.
