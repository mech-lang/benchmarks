# Mech worker scaling

Fixed total work: 196,608 accepted pure numerical turns, split evenly across 1, 2 and 4 independent Mech processes. Each application worker uses one execution thread. The group timer includes supervisor startup, source compilation, activation, warmup, accepted turns, output observation and complete child-process teardown. It is a process-scaling result; it makes no shared-state or parallel-kernel claim.

| Workers | Median complete group seconds | Accepted turns/s |
| ---: | ---: | ---: |
| 1 | 0.101986 | 1927795.6 |
| 2 | 0.071804 | 2738123.6 |
| 4 | 0.061221 | 3211431.8 |
