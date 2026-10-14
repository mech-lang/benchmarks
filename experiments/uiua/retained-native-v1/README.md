# Retained Uiua n-body and binary trees

This packet reconciles two completed workloads from the original Uiua suite and prepares their sources and measurements for publication. It reuses **nine subject observations and six matched Mech controls**, retains the excluded compiler-contention observation, and preserves the binary-trees optimized source as an alias with no additional native measurements.

| Source | Canonical units | Accepted report attempts | Median seconds |
| --- | ---: | --- | ---: |
| Binary trees compact | 15 | 59, 61, 63 | 2627.883 |
| Binary trees optimized alias | 15 | Same compact observations | 2627.883 |
| N-body compact v3 | 21 | 66, 71, 74 | 772.874 |
| N-body optimized v3 | 21 | 67, 68, 72 | 472.772 |
| Mech tree control | Original recorded count | 60, 62, 64 | 0.404 |
| Mech n-body control | Original recorded count | 65, 69, 73 | 1.045 |

N-body attempt 70 completed with valid output but overlapped compiler activity. It remains excluded. Attempts 71 and 74 are the completed second and third accepted compact observations; the original attempted order and exclusion are retained. There are three distinct Uiua source byte identities across the four named forms. The tree alias has identical source bytes and exact shared timing ownership.

The canonical counts are independently qualified in [the retained source-count packet](../retained-counts-v1/qualified-source-counts.json). They cover these exact sources only. Formatted LOC remains unavailable. The publication candidate preserves every original sample, source identity, output validation, runtime command and matched control.

## Original evidence

The [retained report](../../../../archive/comparisons/r-apl-uiua-comparison/20261011/results/timings-uiua.json) remains a partial suite report; both selected workloads are complete. Its SHA-256 is `da5ccf102e90dc2755388414390f6401402b2f67edb177ba74a377f2c5cae709`. Its frozen source audit is `82b15648d0c49c6393a0eec1efb441f1ee11237ceae4a8f41ca854c0b7ee0860`.

All 16 selected attempts were written by the repaired report-only runner, SHA-256 `5b2a038cfae4112e9e2eee79c3cd57ccc6a1521812828c47bf28986d6a8e139b`. Every attempt records its execution fingerprint, runtime overrides, full workload, output, environment checks and empty remaining process group. None has a prior-guard migration index. The surrounding report's older guard revisions remain preserved but supply no selected measurements. This schema did not write separate sampler or supervisor receipts; the original report attempts are the authoritative observations.

The timer begins immediately before process launch and stops after process exit. Uiua source compilation inside `uiua run` is included, along with startup, computation and complete output. External preparation/builds, validation and hashing are excluded. Complete inherited ambient environment values were not recorded. The three subsecond tree controls finished before their first periodic RSS poll; the stored zero denotes an unobserved peak.

Tree allocation and retention use the existing pinned-runtime source proof at [results/uiua/source-audit.json](../../../../archive/comparisons/r-apl-uiua-comparison/20261011/results/uiua/source-audit.json). It establishes fresh node and leaf buffers, separate recursive child construction and the retained long-lived root, with its original limitation that no runtime address trace was collected. N-body uses the exact [v3 work proof](../../../../archive/comparisons/r-apl-uiua-comparison/20261011/uiua-nbody-v3/results/source-audit.json): all 50,000,000 updates over five bodies, unchanged binary64 operations and reduction order, no benchmark kernel, host helper or input-specific shortcut. No new native diagnostic is needed to reuse these already recorded proofs.

## Source review and reproduction

The reconciler and its nine small saved-record/fault tests were independently reviewed. [Review v1](independent-source-review-v1.json) records the initial full source review; [review v2](independent-source-review-v2.json) records the additional opened-descriptor and post-pin mutex identity checks. No actual file phase or catalog admission is implied by these source reviews.

The [exporter peer review](exporter-source-peer-review-v1.json) independently confirms its four pure tests, exact measurement/source joins, alias accounting, preserved exclusion and owned-output finalization.

| File | SHA-256 |
| --- | --- |
| `tools/qualification/uiua_retained_reconcile.py` | `6ffbc98941b3e4e60ac63a899f0e8e4e0cb10def2d3d66ba60c61d25ad3a5523` |
| `tools/qualification/test_uiua_retained_reconcile.py` | `1260e6f6d323ec21f74b8f5f4535805341ecf55b43981743cc0d14d2feef859f` |
| `tools/qualification/export_uiua_retained.py` | `dd2298c2ce98613f3e6aa2b9cfa942647d5af9fb976eaf0a600693eac0a7cfa6` |
| `tools/qualification/test_export_uiua_retained.py` | `0890f4ac1997dfd5d655d0d6224c580bde8ef4b51b0b2844034f97ae882db7c9` |

The exporter writes both the reproduced reconciliation and a private publication candidate in one file phase. Run from the repository root on the retained measurement host after the serial timing lane is free:

```sh
uiua_python=/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12
"$uiua_python" -I -S -B tools/qualification/export_uiua_retained.py \
  --tool-sha256 dd2298c2ce98613f3e6aa2b9cfa942647d5af9fb976eaf0a600693eac0a7cfa6 \
  --output experiments/uiua/retained-native-v1/export-v1
```

The command requires a fresh output directory. It acquires the original nonblocking common timing mutex, verifies original and retained documents, all 1,008 frozen audit pins, the independent count receipt and exact source files, then joins the selected records through the frozen archived evidence consumer. It writes `reconciliation.json`, `candidate.json` and `SUCCESS.json`. Final verification preserves an immutable original pin set, rechecks the named mutex on both sides of pin replay, and verifies every owned output's inode and exact bytes while the lease remains held. Failure removes unchanged owned artifacts and preserves external modifications. No native benchmark, compiler, sampler or producer is imported or executed.

The independent reconciler can also produce a standalone receipt with `tools/qualification/uiua_retained_reconcile.py --tool-sha256 6ffbc98941b3e4e60ac63a899f0e8e4e0cb10def2d3d66ba60c61d25ad3a5523 --output experiments/uiua/retained-native-v1/reconciliation-v1.json`, using the same Python flags and lease protocol.

The pure tests use small saved documents and synthetic faults. They never hash the full runtime closure or open the full catalog:

```sh
"$uiua_python" -I -S -B tools/qualification/test_uiua_retained_reconcile.py
"$uiua_python" -I -S -B tools/qualification/test_export_uiua_retained.py
```

## Publication boundary

This packet prepares a candidate; it changes no catalog, chart coordinate or baseline. Admission follows the separate completed fannkuch v5 packet and the shared coordinate-normalization validator. The new tree source minimum is 15 units, so a concrete catalog still using 16 needs an audited × best rebase. A catalog already rebased to 15 can retain that baseline. The 21-unit n-body sources do not justify lowering an already smaller qualified minimum. All baseline decisions must preserve raw measurements and update only explicitly audited derived coordinates.
