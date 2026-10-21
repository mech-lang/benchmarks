#!/usr/bin/env python3
"""Inventory every family without changing sources, eligibility, LOC or timings."""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def pin(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256(path.read_bytes()).hexdigest()}


def main():
    inventory_path = ROOT / "experiments/implementation-audit/v1/inventory.json"
    inventory = json.loads(inventory_path.read_bytes())
    catalog = ROOT / inventory["canonical_input"]["path"]
    assert pin(catalog)["sha256"] == inventory["canonical_input"]["sha256"]
    language_path = ROOT / "data/languages.json"
    languages = json.loads(language_path.read_bytes())["languages"]
    grouped = defaultdict(list)
    for key, record in inventory["programs"].items():
        language = record["language"]
        grouped[languages[language].get("family", language)].append((key, record))

    families = []
    seen = set()
    for family, records in sorted(grouped.items()):
        rows = []
        for key, record in sorted(records):
            assert key not in seen
            seen.add(key)
            ownership = record["ownership"]
            protected = ownership["preserve_upstream_source"]
            editable = not protected and ownership["classification"] in ("derived-adapted", "suite-authored")
            rows.append({
                "program": key,
                "language": record["language"],
                "benchmark": record["benchmark"],
                "ownership": ownership["classification"],
                "preserve_upstream_source": protected,
                "source_change_scope": "new-derived-candidate-allowed" if editable else
                    "byte-preserving-runtime-review-only" if protected else "resolve-lineage-before-source-change",
                "source_review_status": record["audit"]["status"],
                "source_bundle": record["source_bundle"],
                "endpoint_roles": record["endpoint_roles"],
                "saved_seconds": record["performance"].get("seconds"),
                "saved_time_x_mech": record["performance"].get("time_x_mech"),
                "timing_alias_of": record["performance"].get("timing_alias_of"),
            })
        editable = [r for r in rows if r["source_change_scope"] == "new-derived-candidate-allowed"]
        bundles = {tuple((s["sha256"], s["role"]) for s in r["source_bundle"]
                         if s["included_in_application_loc"]) for r in editable}
        targets = sorted((r for r in editable if "fast" in r["endpoint_roles"]),
                         key=lambda r: (-(r["saved_time_x_mech"] or 0), r["program"]))
        families.append({
            "family": family,
            "execution_variants": sorted({r["language"] for r in rows}),
            "profiles": len(rows),
            "protected_profiles": sum(r["preserve_upstream_source"] for r in rows),
            "locally_derived_or_authored_profiles": len(editable),
            "distinct_included_source_bundles": len(bundles),
            "source_review_statuses": dict(sorted(Counter(r["source_review_status"] for r in rows).items())),
            "local_workloads": sorted({r["benchmark"] for r in editable}),
            "initial_largest_saved_gaps": [r["program"] for r in targets[:3]],
            "programs": rows,
        })
    assert seen == set(inventory["programs"])
    protected = sum(r["protected_profiles"] for r in families)
    assert protected == inventory["summary"]["source_protected_profiles"] == 351
    result = {
        "schema": "all-family-implementation-audit-queue.v1",
        "inputs": [pin(inventory_path), pin(catalog), pin(language_path)],
        "scope": "Every retained family; source-sharing modes remain separate observation profiles.",
        "queue_only": True,
        "new_source_reviews_claimed": 0,
        "native_processes_started": 0,
        "canonical_changes": False,
        "ranking_limit": "Saved cohort ratios prioritize inspection; they do not predict optimization gains.",
        "summary": {"families": len(families), "profiles": len(seen), "protected_profiles": protected,
                    "families_with_local_sources": sum(bool(f["locally_derived_or_authored_profiles"]) for f in families)},
        "families": families,
    }
    output = HERE / "queue.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
