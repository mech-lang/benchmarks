# Saved chart normalization

Chart filters do not change saved denominators. A newly admitted qualified source can establish a smaller canonical-LOC minimum. Such an admission changes only that workload's LOC baseline, derived program/publication x coordinates, and affected aggregate x coordinates. Source counts, timings, samples, source bytes, time baselines, formatted axes and historical receipts remain unchanged.

`tools/normalization_history.py` validates those changes before the repository's preservation checks run. It binds the admission to its completed apply receipt and the existing before/after catalog snapshots, checks the complete coordinate change inventory, independently recomputes the ratios and geometric means, and verifies the current minimum. It then produces an in-memory historical-coordinate view. `check_previous` passes that view to the unchanged Mech interpreted publication verifier and its archived-field comparisons. The published catalog continues to use the current denominator; the historical view is never written back.

## Recording a completed admission

The registry is `data/normalization-history.json`. The guarded importer writes or extends it as part of the apply transaction. The entry is valid only after all final evidence, output and lease-closure checks succeed. Previews never install the registry or an applied success receipt. Do not copy either catalog snapshot again. Each entry names the top-level admission audit and the exact existing `SUCCESS.json` bytes:

```json
{
  "schema": "canonical-loc-normalization-history-v1",
  "admissions": [
    {
      "audit_key": "uiua_fann_v5_publication_audit",
      "success": {
        "path": "experiments/uiua/fann-v5-publication-v1/apply-v1/SUCCESS.json",
        "sha256": "<SHA-256 of the actual closed success receipt>"
      }
    }
  ]
}
```

The placeholder above is documentation, not an admissible digest. The validator requires `status=applied`, `catalog_changed=true`, and an audit identical to the catalog audit. Relative to the receipt directory, it reads the existing `before/data/benchmarks.json`, `after/data/benchmarks.json`, and matching language metadata snapshots. Their bytes must match `originals` and `prepared` in that receipt. Entries are chronological: each before snapshot must contain the earlier admissions and no later one. The guarded shared importer journals the registry as a third target alongside the two catalogs. To avoid a circular hash, its actual success receipt binds the prior registry only; the prepared registry then records the digest of that receipt. Preview may calculate a proposed future entry, but must not write an applied success receipt. A failed apply restores all still-owned targets and removes the owned success receipt.

Registered adapters cover the exact Uiua fannkuch v5 admission and the retained R, GNU APL and Uiua n-body/tree admissions. They bind exact candidate bytes, independently qualified source-count receipts, retained reports and source audits, source hashes, native sample ownership and selected endpoints. Uiua fannkuch additionally binds its sealed manifest and prior independent reconciliation. APL aliases and the Uiua tree alias retain their original native observation owners. APL additionally binds its separate exact runtime-scope review and all eleven recorded source/runtime/command/environment joins. That review describes static declared dependencies; it does not claim observed per-process loaded images or promote the original candidate’s false metadata-review flag. A missing registry entry, unregistered admission, changed snapshot, incomplete coordinate list, altered raw field, incorrect current minimum or wrong aggregate is a verification failure. The registry itself grants no source or timing qualification.

## Interface for additional admissions

`historical_view(root, data)` is the repository integration point. It returns the original object when no registered normalization exists, and otherwise returns a validated copy. `validate_registry(history)` checks the registry schema without reading files. `validate_transition(before, after, audit, added_keys, added_reference_languages)` provides the pure coordinate checks and returns validated coordinate boundaries; `reverse_boundary(current, boundary)` restores one boundary. `added_keys` is a mapping with separate `programs` and `program_inventory` sets, since only selected endpoints enter the former. Admission adapters bind concrete candidate/count/report evidence and return those exact additions and any newly created aggregate languages. Only code-reviewed adapters are registered; a JSON flag cannot authorize an admission.

The coordinate rules are independent of workload and support ordered canonical-LOC rebases such as fannkuch31→20, nbody20→19 and binarytrees16→15. Repeated rebases reverse in opposite order. Later additive languages are checked against the current denominator and converted in the preservation view without pretending they existed in an earlier change inventory. Existing aggregate before values are restored exactly after independently validating their arithmetic, preserving historical floating-point bytes as JSON values.

A multiworkload admission uses one successful apply and one existing snapshot pair. Its `normalizations` list contains ordered per-workload change inventories, and `endpoints` maps workloads to newly appended groups. `aggregate_change.before` records the own-language aggregate after those rebases; `aggregate_change.after` records its final expanded coverage. Empty normalization lists are recorded too, so a later expansion of an existing language’s coverage is bound to an actual admission. The historical view retains that expanded coverage and recomputes its historical-axis aggregate, while restoring exact earlier aggregate values where coverage and other metadata are unchanged. A time-baseline rebase is not currently supported.

## Source checks

The focused suite uses tiny synthetic catalog snapshots and the already retained small R, APL and Uiua candidate, source-count and report metadata. It does not open the current catalog, replay a runtime closure, invoke native code or modify publication data:

```sh
/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -I -S -B tools/test_normalization_history.py
```

After a real admission and registry update, the normal repository verifier validates the normalization automatically. Existing producer reports and the earlier Mech interpreter correction receipt remain unchanged.
