# Follow-up pure validation

All 28 methods in these three source-version-specific suites passed on
2026-10-15 UTC. The APL suite includes previously existing methods, so this
result is not added to earlier runs as a unique test total.

| Suite | Methods | Scope |
| --- | ---: | --- |
| APL publication | 17 | Source/setup counts, timing alias, catalog preservation, history binding and transaction faults |
| Rebol library relocation | 5 | Synthetic install-name and CodeDirectory checks, with unrelated changes rejected |
| Julia intake transport | 6 | Complete descriptor writes, interrupted/partial writes and failure preservation using fake probes |

[validation.json](validation.json) preserves the exact commands, recorded working
directory, source identities, exit statuses and links to the complete captured
stdout and stderr in [checks](checks). All three commands ran sequentially with
the retained Python interpreter and `-I -S -B`; every exit status was zero and
source bytes were unchanged afterward. Source pins include the documentation
versions present during execution. The packet READMEs subsequently received only
test-status updates, separately identified in the receipt.

The tests launched no native benchmark or debugger, compared no installed library
images and performed no result reconciliation, catalog import or publication.
They do not grant runtime, timing or chart admission. Earlier native failures and
their original evidence remain unchanged.
