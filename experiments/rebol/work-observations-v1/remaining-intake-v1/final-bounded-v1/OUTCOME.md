# Two completed work observations and one diagnostic failure

The three observations ran serially on October 15, 2026. The
[independent review](failed-stage-review-v1.json) verified both completed
contracts and closed the failed stage. Original producer records retain their
`stopped-unqualified` status.

| Observation | Result |
| --- | --- |
| Binary trees, N=4 | The retained tree had 127 distinct nodes, including 64 leaves, before and after allocation churn. Two fresh leaves were distinct and mutation-isolated. Automatic collection occurred; the tree remained intact. |
| Pi digits, N=27 | All 224 instrumented facade calls matched the independent integer recurrence, including operands beyond 64-bit range. The complete 27-digit output matched. |
| Seven k-mer histograms | The expected 243-byte benchmark output was produced. The subsequent global runtime dump exceeded the 512 MiB RSS limit at an observed 538,181,632 bytes. The process was killed and reaped; no map sidecar was written. |

The map failure retains 2,197,930 stderr bytes and exit status -9. Its correct
stdout does not qualify the incomplete work observation. The
[diagnostic analysis](DIAGNOSTIC.md) identifies the dump's broad traversal and
formatting allocations; it does not establish the precise allocation responsible
for the observed peak. A narrower diagnostic can observe all seven map contents
without claiming measured backing capacity.

There were three actual processes: two completed observations, one failure and
no unstarted cases. All five worker, controller and native process identities
and groups were absent at independent closure, and all sixteen leases were
released. The review verified the input pins and complete artifact inventories.
The successful tree and pi observations remain available for continuation;
neither needs to run again.

These bounded diagnostics are not benchmark timing samples. Per-tree frees,
full-size work, complete runtime equivalence, stage-wide required-work admission,
timing admission and chart admission remain unestablished by this packet.
