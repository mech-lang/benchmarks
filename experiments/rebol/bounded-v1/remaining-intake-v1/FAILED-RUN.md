# Bounded Rebol run stopped at binary trees

The [149-case plan](plan-v1.json) attempted 24 cases: the first 23 passed their output contracts, and `binarytrees:n-0` failed. The remaining 125 cases were not started. There was no retry, and this run does not qualify the complete bounded corpus.

The failed process exited normally with status 1, produced no stdout and retained 345 bytes of [stderr](run-v1/023-binarytrees-n-0/stderr.bin). Its diagnostic was `check-tree does not allow #(word!) for its node argument`. The [original main](../../../../archive/languages/rebol/20261013/drafts/private-v1/sources/binarytrees/main.reb) creates leaves with `copy [none none]`: those block elements remain words rather than evaluated `none` values. The leaf test therefore takes the recursive branch and passes a word to the block-typed `check-tree` argument. This source diagnosis explains the observed failure; the original source and all captures remain unchanged.

The [independent closure review](failed-stage-review-v1.json) replayed 6,008 input pins, all 122 run artifacts and eight [durable job artifacts](../../../shared/owned-jobs-v1/owned-jobs/rebol-bounded149-remaining-v1/terminal.json). It independently checked the 23 successful output contracts, the failed capture, serial execution and the unstarted suffix. All 26 recorded process IDs and their groups were absent, and all 12 leases were acquired, checked and released.

The [report](run-v1/report.json) and [terminal receipt](run-v1/terminal.json) retain `stopped-unqualified`. This evidence admits no benchmark correctness, source work, source count, runtime-source equivalence, full timing or chart result. The earlier primitive-contract qualification remains a separate prerequisite.
