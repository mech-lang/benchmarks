#!/usr/bin/env python3
"""Inventory retained implementation ownership and audit work without executing workloads.

Only the experiment JSON is written. Canonical programs, measurements, source
counts, attribution, and language programs are never changed or executed.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("experiments/implementation-audit/v1/inventory.json")
PRIORITY = ["bqn", "matlab", "nim", "prolog", "apl", "smalltalk", "ruby",
            "clojure", "ada", "futhark", "r", "uiua", "k", "d", "elixir"]
DEEP_REVIEWS = {language: f"experiments/implementation-audit/v1/{language}-review.md"
                for language in PRIORITY}
DEEP_REVIEWS["ruby-zjit"] = DEEP_REVIEWS["ruby"]
DEEP_REVIEWS["lean4"] = "experiments/implementation-audit/v1/lean4-review.md"
EXACT_SOURCE_REVIEWS = {
    "lean4": {
        "path": "experiments/implementation-audit/v1/lean4-source-review-proposal.json",
        "sha256": "ffb28792cf304ed40661d642ad6e2b14263b25d5bb42f8a557e2fc0328fbdd5a",
        "review_sha256": "53a89d767a3c531d6b354b8e9af2f1375a3674ca37e4469f0c103131d9abca39",
    },
}
COMPILER_REVIEWS = {language: "experiments/implementation-audit/v1/mech-review.md"
                    for language in ("mech", "mech-jit", "mech-resident")}
ADMISSION_EXTENSIONS = {
    "bqn_knucleotide_audit": ("bqn-knucleotide-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "nim_knucleotide_audit": ("nim-knucleotide-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "bqn_spectral_audit": ("bqn-spectral-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "bqn_fasta_audit": ("bqn-fasta-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "clojure_nbody_audit": ("clojure-nbody-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "clojure_compact_audit": ("clojure-compact-catalog-extension.v1", "source-expressiveness-candidate", "fresh-complete-process-observations"),
    "prolog_spectral_audit": ("prolog-spectral-catalog-extension.v1", "source-speed-candidate", "fresh-complete-process-observations"),
    "crystal_scan_audit": ("crystal-scan-catalog-extension.v1", "source-speed-and-expressiveness-candidates", "fresh-complete-process-observations"),
    "matlab_regex_case_audit": ("matlab-regex-catalog-extension.v1", "archived-correctness-correction", "archived-complete-process-observations; no-new-native-run-by-intake"),
}

# These are retained written assertions, not newly inferred original authorship.
# A task-description port is locally implemented, but does not establish an AI
# author. A translation with known predecessor remains derived.
LOCAL_IMPLEMENTATION_MARKERS = (
    "local matlab implementation", "newly authored", "new counted",
    "locally authored smalltalk (pharo) application",
)
CHANGE_MARKERS = (
    "language port", "local faithful cpu port", "locally simplified",
    "locally optimized", "locally corrected", "darwin import port",
    "all changed application output",
)
STATIC_REVIEWS = {
    "knucleotide:array-bqn-faithful": {
        "status": "static-source-reviewed; candidate-alternatives-not-measured",
        "evidence": [
            "archive/comparisons/array-comparison/all-20261009/sources/knucleotide-faithful.bqn",
            "archive/comparisons/array-comparison/all-20261009/README.md",
        ],
        "findings": [
            "The current source constructs rows-by-width arrays and packed keys separately for each frame/piece before explicit HashMap updates. Allocation and callback cost are hypotheses requiring profiling, not measured bottleneck attributions.",
            "The six-character header test does not visibly enforce a token boundary after THREE. Missing/empty records and >THREEX require adversarial correctness review.",
            "The initial audit snapshot had one required-work-admitted BQN nucleotide profile; query-only historical sources are disqualified alternatives. Later exact-source admissions are linked separately.",
        ],
        "candidate_work": [
            "Compare an exact-token bounded record parser and fewer full-sequence copies, preserving complete input and output.",
            "Compare rolling packed keys or bounded chunks with existing vector packing; every required overlapping window must still update a growing map in BQN.",
            "Review callback and job granularity, process transport, independent map ownership, boundary coverage and at-most-eight-worker policy.",
            "Retain seven widths, every required lookup/update, and full output. Ordinary native library primitives need work qualification; benchmark-specific native helpers, query-only counts and precomputed results are excluded.",
        ],
    },
    "binarytrees:matlab-compact": {
        "status": "static-source-reviewed; candidate-alternatives-not-measured",
        "evidence": [
            "archive/comparisons/matlab-comparison/20261010/sources/binarytrees_compact.m",
            "archive/comparisons/matlab-comparison/20261010/README.md",
        ],
        "findings": [
            "The recursive constructor creates a two-slot cell at every interior node and leaf; traversal follows construction and the long-lived root is retained.",
            "The retained cohort compared compact and constructor-unrolled forms. Their saved medians do not establish the best possible MATLAB design.",
        ],
        "candidate_work": [
            "Separate fresh-process startup from diagnostic allocation, recursive-call and traversal costs without replacing the admitted whole-process metric.",
            "Review ordinary MATLAB object/cell representations, constructor unrolling and bounded worker scheduling while preserving distinct equal-size nodes and lifetimes.",
            "Recheck unique node headers and backing storage for arbitrary odd/even depths before admitting any candidate; no flat tree, shared leaf or custom pool.",
        ],
    },
    "knucleotide:nim-knucleotide-optimized": {
        "status": "static-source-reviewed; candidate-alternatives-not-measured",
        "evidence": [
            "archive/languages/nim/20261012/PROVENANCE.md",
            "programs/nim/knucleotide/nim-knucleotide-optimized/optimized.nim",
        ],
        "findings": [
            "The source assigns one complete sequence scan to each of seven native threads, with rolling packed keys and a private growing Table per width.",
            "This retained predecessor uses getOrDefault followed by indexed assignment. Later mutable-slot/preencoding alternatives have separate admission evidence; any isolated duplicate-lookup cost remains a source hypothesis.",
        ],
        "candidate_work": [
            "Compare an idiomatic mutable-slot counter API and integer/character conversion in the hot loop, preserving default-capacity map growth and every update. Growth can re-probe; do not assert exactly one probe per occurrence.",
            "Compare bounded input parsing, shared encoding and scheduling only in isolated candidates; preserve the complete original community-derived source and citations.",
        ],
    },
}

# Static observations below were made from the retained SHA-addressed source in
# data/benchmarks.json. They identify candidates, not measured causal diagnoses.
MORE_STATIC_REVIEWS = {
    "spectralnorm:prolog-spectralnorm-compact": (
        "The inner recursive row predicate tests transpose and calls coefficient for every matrix element; vectors use ordinary compound terms and arg/3.",
        "Compare specialized transpose/non-transpose row loops, arithmetic compilation and bounded independent-row workers. Preserve separate required coefficient/product functions and all forty dense products; do not cache the matrix.",
        "Review whether conventional tail-recursive numeric predicates can express the same work with fewer intermediate bindings; source aliases are not independent optimization strategies.",
    ),
    "fannkuchredux:fannkuchredux-apl-compact": (
        "The source executes the canonical permutation and flip loops through labels/branches, copying and gathering the prefix on each actual reversal.",
        "Compare bounded permutation batches and source-level independent rank ranges with ordinary array operations. Preserve every permutation, actual flips, rank parity and at-most-eight-worker policy; no closed-form flip count.",
        "Compare native APL iteration/composition and bounded array expressions with the current scalar control flow; count the full application rather than assuming compressed notation is the minimum.",
    ),
    "knucleotide:knucleotide-smalltalk-packed": (
        "The source uses packed SmallInteger keys and mutable Association values, but scans each of seven widths serially; readThree accepts a >THREE prefix without an explicit token boundary.",
        "Review exact-token parsing, generic byte access and bounded independent-width workers. Single-lookup association updates are already present; do not propose that as an unimplemented optimization.",
        "Review whether the ordinary collection/stream APIs can remove repeated orchestration while preserving explicit full maps and source-counted bindings.",
    ),
    "nbody:clojure-nbody-compact": (
        "Although body arrays are primitive, every pair update constructs [[0 dx] [1 dy] [2 dz]] and iterates through doseq destructuring in the fifty-million-step loop.",
        "Compare explicit primitive scalar coordinate updates or a primitive indexed loop, checking boxing/reflection/allocation evidence and exact pair order. This is a source-level allocation hypothesis; no speedup is measured here.",
        "Review compact idiomatic primitive loops and shared helpers against the existing alternative; preserve exact sqrt/division and every sequential step.",
    ),
    "regexredux:regexredux-ada-pcre2-heap": (
        "The source compiles/JITs PCRE2 patterns and owns count/substitution orchestration, borrowed heap-string views and native bindings in Ada.",
        "Review bounded independent pattern counts, buffer ownership and the two-call substitution sizing/fill path. Preserve all nine nonoverlapping counts and five ordered replacements; general PCRE2 work is already disclosed.",
        "Compare standard package abstractions and shared pattern loops while keeping workload orchestration and application-specific FFI counted. Preserve all nine unchanged Ada upstream profiles.",
    ),
    "knucleotide:futhark-knucleotide-optimized": (
        "The source maps thirty-two pieces, reserves table space by bounded batches, and performs rolling-key increments in Futhark. Its >THREE search is a raw substring search rather than a record-token parser.",
        "Review exact record parsing, generated CPU allocation/copy evidence, reserve granularity and ordinary parallel-piece sizing. Preserve explicit seven growing maps and every update; native table execution is not an admissible replacement.",
        "Compare uniqueness-friendly loop state and general helper composition using the existing hashmap library; verify source accounting for workload helpers rather than hiding them as support.",
    ),
    "fannkuchredux:fannkuchredux-r-array-batched": (
        "The source already uses eight ordinary workers and 8192-rank permutation batches; each active-flip pass constructs rep/ifelse gather vectors and updates a matrix subset.",
        "Compare bounded batch sizes, gather-index reuse and ordinary array allocation behavior. Preserve rank initialization, all actual prefix flips and checksum parity; no native benchmark kernel.",
        "Review vectorized base-R expressions and ordinary reusable helpers against the existing scalar/compact form; the retained small count alone does not prove the most idiomatic or fastest program.",
    ),
    "binarytrees:binarytrees-uiua-compact": (
        "The source recursively constructs Tree records and checks real child fields; the retained compact and optimized profile bundles are identical for this task.",
        "Review ordinary record/box allocation, recursion and bounded independent temporary-tree work, preserving equal-size distinct nodes, complete traversal and long-lived retention. Do not replace the tree by a flat representation.",
        "Seek idiomatic recursive composition and general scheduling helpers without moving construction/checking to native support; aliases do not demonstrate alternative designs.",
    ),
    "fannkuchredux:array-k-faithful": (
        "The source already divides factorial rank intervals among eight language callbacks, with mutable global permutation/count state inside each process and list prefix reversal/concatenation.",
        "Review callback/global-state overhead, scratch reuse and ordinary vector operations. Preserve canonical enumeration, all flips, parity and process isolation; the existing process map is general support.",
        "Compare ordinary fold/iteration structure and reusable permutation helpers while keeping all workload source visible and counted.",
    ),
    "revcomp:revcomp-d-optimized": (
        "The source joins the full input, builds a second full output appender, then writes once; complement lookup and reverse indexing remain in D.",
        "Compare ordinary byte-buffer/in-place or record-streaming designs with bounded full output writes. Review CRLF, comments, empty records, EOF and all IUPAC symbols before admission.",
        "Compare standard ranges/formatting and shared record helpers with full application accounting; existing compact D advantages are already documented separately in site/reports/d-loc-audit.md.",
    ),
    "knucleotide:elixir-knucleotide-optimized": (
        "The source takes binary_part for each window and Map.update on seven serial passes; compact and optimized retained bundles are identical.",
        "Compare rolling integer keys, bounded binary parsing, ordinary map/table APIs and independent width tasks within the worker cap. Preserve seven full growing maps and every lookup/update; no query-only counting or foreign workload executor.",
        "Review tail-recursive binary matching and native Enum/Map/iodata idioms; avoid treating identical source labels as evidence that separate strategies were optimized.",
    ),
}
for _key, (_finding, _candidate, _idiom) in MORE_STATIC_REVIEWS.items():
    STATIC_REVIEWS[_key] = {
        "status": "static-source-reviewed; candidate-alternatives-not-measured",
        "findings": [_finding], "candidate_work": [_candidate],
        "expressiveness_findings": [_idiom], "evidence": [],
    }


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def application_shas(program):
    return [sha for sha in program["files"]
            if program.get("file_roles", {}).get(sha, {}).get("included_in_application_loc") is not False]


def exact_source_reviews(languages, root=ROOT):
    """Load reviewed source inventories, without extending a review to new sources."""
    result = {}
    for language in set(languages).intersection(EXACT_SOURCE_REVIEWS):
        reference = EXACT_SOURCE_REVIEWS[language]
        raw = (root / reference["path"]).read_bytes()
        if digest(raw) != reference["sha256"]:
            raise ValueError("Exact source-review proposal identity differs: " + language)
        proposal = json.loads(raw)
        review = proposal["review"]
        if (proposal.get("schema") != "owned-language-source-review-proposal.v1"
                or proposal.get("language") != language
                or proposal.get("status") != "proposed-source-review-binding-only"
                or review.get("path") != DEEP_REVIEWS[language]
                or review.get("sha256") != reference["review_sha256"]
                or digest((root / review["path"]).read_bytes()) != review["sha256"]
                or proposal.get("qualification", {}).get("source_count_approval") is not False
                or proposal.get("qualification", {}).get("native_execution") is not False):
            raise ValueError("Exact static source-review scope differs: " + language)
        result[language] = (proposal, reference)
    return result


def bound_static_review(program, source_reviews):
    """Return a compact reference only for the exact listed key and source boundary."""
    if program["language"] not in source_reviews:
        return None
    proposal, reference = source_reviews[program["language"]]
    reviewed = proposal["profiles"].get(program["key"])
    if reviewed is None or reviewed["benchmark"] != program["benchmark"]:
        return None
    parts = reviewed["sources"]
    expected_application = [p["source_sha256"] for p in parts if p["included_in_application"]]
    if (program["files"] != [p["source_sha256"] for p in parts]
            or application_shas(program) != expected_application):
        return None
    for part in parts:
        role = program.get("file_roles", {}).get(part["source_sha256"], {}).get("role", "application")
        if role != part["role"]:
            return None
    return dict(path=reference["path"], sha256=reference["sha256"],
                review_path=proposal["review"]["path"], review_sha256=proposal["review"]["sha256"],
                scope="exact-listed-profile-and-application-support-sources; static-review-only",
                source_sha256_reviewed=expected_application, source_count_approval=False,
                candidate_execution=False)


def classify(program):
    """Separate ownership from AI attribution and unchanged-source protection."""
    authored = program.get("authorship", {})
    prose = (program.get("source_provenance") or "").lower()
    refs = [r for r in authored.get("sources", [])
            if r.get("relationship") in ("implementation", "reference implementation")]
    parents = authored.get("parent_programs", [])
    matches = set()
    for ref in refs:
        check = ref.get("citation_check", {})
        matches.update(check.get("matching_retained_source_sha256", []))
        if check.get("body_sha256"):
            matches.add(check["body_sha256"])
        if ref.get("upstream_sha256"):
            matches.add(ref["upstream_sha256"])
    app = set(application_shas(program))
    confirmed = bool(app) and app.issubset(matches)
    changed = (program.get("local_adaptation") is True
               or authored.get("kind") == "ai-adapted"
               or any(marker in prose for marker in CHANGE_MARKERS))
    unmodified = "unmodified listed source" in (program.get("algorithm") or {}).get("reason", "").lower()
    if not changed and (confirmed or (authored.get("kind") == "upstream" and unmodified)):
        category = "unchanged-upstream"
        reason = ("All application files match retained upstream citation checks; CLBG checks normalize CRLF and surrounding whitespace."
                  if confirmed else "Retained source/work record explicitly declares an unmodified listed submission; byte identity is not independently established here.")
    elif parents or (refs and changed):
        category = "derived-adapted"
        reason = "Documented local changes or translation with retained upstream/reference implementation or predecessor lineage."
    elif authored.get("origin_status") == "suite-authored" or any(marker in prose for marker in LOCAL_IMPLEMENTATION_MARKERS):
        category = "suite-authored"
        reason = "A retained source-origin assertion explicitly identifies local implementation; this does not establish an AI author or exclude earlier influences."
    elif changed:
        category = "derived-adapted"
        reason = "Retained metadata explicitly records local adaptation/porting, but original implementation lineage is unresolved."
    else:
        category = "unknown"
        reason = "Retained evidence does not establish unchanged upstream identity, a specific adaptation, or explicit local origin."
    # Cited upstream submissions remain protected even when identity evidence is
    # incomplete. Missing citations never authorize rewriting a published file.
    protect = category == "unchanged-upstream" or (authored.get("kind") == "upstream" and not changed)
    return {
        "classification": category,
        "reason": reason,
        "preserve_upstream_source": protect,
        "upstream_identity": "normalized-source-match" if confirmed else "declared-unmodified" if unmodified else "not-established",
        "original_lineage_status": authored.get("origin_status", "unresolved"),
        "origin_gaps": authored.get("origin_gaps", []),
        "existing_authorship_kind": authored.get("kind"),
        "existing_ai_evidence_status": authored.get("ai", {}).get("status", "unverified"),
        "existing_ai_models": authored.get("ai", {}).get("models", []),
        "ai_authorship_inferred": False,
        "parent_programs": parents,
        "sources": refs,
        "evidence": authored.get("evidence", []),
        "retained_source_assertion": program.get("source_provenance"),
    }


def performance(program, mech):
    """Use saved whole-process medians; the range envelope is not a CI."""
    samples = program.get("samples", [])
    controls = mech.get("samples", [])
    out = {
        "seconds": program["seconds"], "samples": samples,
        "sample_count": len(samples), "loc": program["loc"],
        "mech_fast_program": mech["key"], "mech_seconds": mech["seconds"],
        "mech_loc": mech["loc"],
        "time_x_mech": program["seconds"] / mech["seconds"],
        "loc_x_mech_fast": program["loc"] / mech["loc"],
        "report": program.get("report"), "mech_report": mech.get("report"),
        "timing_alias_of": program.get("timing_alias_of"),
        "comparison_scope": "descriptive medians of retained cohorts; not a new paired experiment",
    }
    if samples and controls and min(samples) > 0 and min(controls) > 0:
        low, high = min(samples) / max(controls), max(samples) / min(controls)
        out["observed_sample_ratio_envelope"] = [low, high]
        out["observed_samples_all_slower_than_mech"] = low > 1
    return out


def admission_reviews(data, catalog):
    """Link admitted exact candidates without transferring qualification to parents.

    The admission importers validate execution/source receipts. Inventory merely
    checks their catalog binding; it neither reruns importers nor starts workloads.
    """
    candidates, predecessors = {}, defaultdict(list)
    for field, (schema, purpose, observation_origin) in ADMISSION_EXTENSIONS.items():
        extension = data.get(field)
        if extension is None:
            continue
        if extension.get("schema") != schema:
            raise ValueError("Unrecognized implementation admission: " + field)
        keys = extension.get("appended_programs", [])
        if not keys or len(set(keys)) != len(keys):
            raise ValueError("Missing/duplicate admission candidates: " + field)
        refs = extension.get("evidence", {})
        results = refs.get("results")
        if not isinstance(results, dict) or not results.get("path") or not results.get("sha256"):
            raise ValueError("Admission result pin missing: " + field)
        for key in keys:
            if key not in catalog or key in candidates:
                raise ValueError("Missing/duplicate admitted profile: " + key)
            program = catalog[key]
            detail = program.get("source_provenance_record") or {}
            parent = detail.get("original_program_key") or program.get("original_program_key")
            accounting = program.get("source_accounting") or {}
            if (detail.get("admission") != results or parent not in catalog
                    or detail.get("source_sha256") not in application_shas(program)
                    or accounting.get("application_loc") != program["loc"]
                    or not accounting.get("evidence") or program.get("report") != results["path"]):
                raise ValueError("Unbound implementation admission: " + key)
            record = {
                "catalog_extension": field, "purpose": purpose,
                "observation_origin": observation_origin,
                "predecessor_program": parent,
                "admitted_application_sha256": application_shas(program),
                "source_count_review": accounting["evidence"],
                "evidence": refs,
                "qualification_scope": "Exact admitted source/configuration only; predecessor observations and source remain unchanged.",
                "global_optimality_proven": False,
            }
            candidates[key] = record
            predecessors[parent].append({"admitted_program": key, **record})
    return candidates, dict(predecessors)


def make_inventory(data, canonical_sha256):
    catalog = {**data.get("program_inventory", {}), **data["programs"]}
    source_reviews = exact_source_reviews(p["language"] for p in catalog.values())
    pools = defaultdict(list)
    for program in catalog.values():
        pools[program["benchmark"], program["language"]].append(program)
    endpoints, mech_fast, mech_small = {}, {}, {}
    for benchmark in data["benchmarks"]:
        for group in benchmark["groups"]:
            endpoints[benchmark["key"], group["language"]] = group
            if group["language"] == "mech":
                mech_fast[benchmark["key"]] = catalog[group["fast"]]
                mech_small[benchmark["key"]] = catalog[group["small"]]
    admissions, predecessor_reviews = admission_reviews(data, catalog)
    records = {}
    for key, program in sorted(catalog.items()):
        ownership = classify(program)
        pool = pools[program["benchmark"], program["language"]]
        best = min(pool, key=lambda p: (p["seconds"], p["loc"], p["key"]))
        shortest = min(pool, key=lambda p: (p["loc"], p["seconds"], p["key"]))
        group = endpoints.get((program["benchmark"], program["language"]), {})
        roles = [role for role in ("fast", "small", "formatted_fast", "formatted_small") if group.get(role) == key]
        requested = program["language"] in PRIORITY
        review = STATIC_REVIEWS.get(key, {
            "status": "not-yet-source-performance-reviewed",
            "findings": [], "candidate_work": [], "evidence": [],
        }).copy()
        review["expressiveness_status"] = (
            "static-idiom-opportunities-identified; no-new-count-or-source-admitted"
            if key in MORE_STATIC_REVIEWS else
            "not-yet-idiom-reviewed; retained source counts only")
        review["runtime_configuration_status"] = (
            "existing-YJIT-ZJIT-study-recorded; no-new-configurations-executed"
            if program["language"] in ("ruby", "ruby-zjit") else
            "recorded-runtime-fields-inventoried; independent-configuration-review-pending")
        if key in STATIC_REVIEWS:
            review["source_sha256_reviewed"] = application_shas(program)
        bound_review = bound_static_review(program, source_reviews)
        if (program["language"] in DEEP_REVIEWS
                and (program["language"] not in EXACT_SOURCE_REVIEWS or bound_review is not None)):
            review["status"] = ("static-source-and-idiom-reviewed; candidate-alternatives-not-measured"
                                if bound_review else "source-and-idiom-reviewed; candidate-alternatives-not-measured")
            review["expressiveness_status"] = "static-idiom-alternatives-reviewed; no-new-count-or-source-admitted"
            review["source_sha256_reviewed"] = application_shas(program)
            review["evidence"] = [*review.get("evidence", []), DEEP_REVIEWS[program["language"]]]
            if bound_review:
                review["source_review_binding"] = bound_review
                review["evidence"].append(bound_review["path"])
        if program["language"] in COMPILER_REVIEWS:
            review["status"] = "source-and-compiler-idioms-reviewed; compiler-alternatives-not-newly-measured"
            review["expressiveness_status"] = "application-host-boundaries-and-source-alternatives-reviewed; no-new-count-assigned"
            review["runtime_configuration_status"] = "fresh-process-mode-boundaries-and-admission-evidence-reviewed; no-new-mode-measurements"
            review["source_sha256_reviewed"] = application_shas(program)
            review["evidence"] = [*review.get("evidence", []), COMPILER_REVIEWS[program["language"]]]
        if key in predecessor_reviews:
            review["status"] = "source-reviewed-against-qualified-measured-alternative; further-search-open"
            review["related_admissions"] = predecessor_reviews[key]
            review["qualification_note"] = "Predecessor source/timings retained; corrected or optimized child qualification does not transfer to this profile."
            review["evidence"] = [*review.get("evidence", []), *[r["evidence"]["results"]["path"] for r in predecessor_reviews[key]]]
        if key in admissions:
            admission = admissions[key]
            review["status"] = (
                "corrected-source-work-qualified-with-archived-measurements; further-search-open"
                if admission["purpose"] == "archived-correctness-correction" else
                "new-expressiveness-candidate-work-qualified-and-measured; further-search-open"
                if admission["purpose"] == "source-expressiveness-candidate" else
                "new-speed-candidate-work-qualified-and-measured; further-search-open")
            review["expressiveness_status"] = "new-exact-source-count-reviewed; uniform-logical-normalization-pending"
            review["runtime_configuration_status"] = (
                "archived-runtime-and-complete-process-evidence-replayed; no-new-timing"
                if admission["purpose"] == "archived-correctness-correction" else
                "matched-runtime-source-comparison-retained")
            review["admission"] = admission
            review["evidence"] = [*review.get("evidence", []), program["report"], program["source_accounting"]["evidence"]]
        if (program.get("eligible_for_chart") is False
                and program.get("eligibility_correction", {}).get("reason") in {
                    "suite-local-custom-hash-table",
                    "dense-and-query-only-counting-omits-library-map-work"}):
            review["status"] = "confirmed-required-work-policy-exclusion; historical-measurements-retained"
            review["eligibility_correction"] = program["eligibility_correction"]
            review["evidence"] = [*review.get("evidence", []), program["eligibility_correction"]["evidence"]["review"]["path"]]
        if ownership["preserve_upstream_source"]:
            scope = "runtime-configuration-review-only; preserve-original-submission"
        elif requested:
            scope = "user-requested-priority; source-and-runtime-review"
        elif program["language"] in COMPILER_REVIEWS:
            scope = "separately-requested-Mech-source-and-compiler-review; no-native-workload-bridge"
        else:
            scope = "database-wide-authored-derived-or-unknown-review-queue"
        review["scope"] = scope
        counts = {
            "retained_catalog_candidate_profiles": len(pool),
            "distinct_source_bundles": len({tuple(sorted(p["files"])) for p in pool}),
            "lowest_retained_median_program": best["key"],
            "lowest_retained_median_seconds": best["seconds"],
            "fewest_retained_loc_program": shortest["key"],
            "fewest_retained_loc": shortest["loc"],
            "published_fast_matches_lowest_retained_median": not group or catalog[group["fast"]]["seconds"] == best["seconds"],
            "status": "saved-candidate-medians-and-source-counts-compared; no-workloads-executed-by-inventory",
            "admitted_candidate_programs": [p["key"] for p in pool if p["key"] in admissions],
            "global_optimality_proven": False,
        }
        comparison = performance(program, mech_fast[program["benchmark"]])
        comparison["loc_x_mech_small"] = program["loc"] / mech_small[program["benchmark"]]["loc"]
        comparison["mech_small_program"] = mech_small[program["benchmark"]]["key"]
        comparison["median_matches_saved_samples"] = statistics.median(program["samples"]) == program["seconds"]
        records[key] = {
            "language": program["language"], "benchmark": program["benchmark"],
            "published_program": key in data["programs"], "endpoint_roles": roles,
            "user_requested_priority_language": requested,
            "separately_requested_compiler_review": program["language"] in COMPILER_REVIEWS,
            "priority_language_order": PRIORITY.index(program["language"]) + 1 if requested else None,
            "ownership": ownership, "audit": review, "candidate_comparison": counts,
            "performance": comparison,
            "runtime_configuration": {
                field: value for field, value in program.items()
                if field.startswith("runtime_") or field in (
                    "execution_mode", "compiler", "compiler_flags", "build_command", "command", "toolchain")
            },
            "source_bundle": [{
                "sha256": sha,
                "path": data.get("archive_paths", {}).get(data["files"][sha]["path"], data["files"][sha]["path"]),
                "role": program.get("file_roles", {}).get(sha, {}).get("role", "application"),
                "included_in_application_loc": sha in application_shas(program),
            } for sha in program["files"]],
        }
    queue = []
    summaries = []
    for language in PRIORITY:
        selected = [(k, r) for k, r in records.items() if r["language"] == language]
        fast = [(k, r) for k, r in selected if "fast" in r["endpoint_roles"]]
        eligible = [(k, r) for k, r in fast if not r["ownership"]["preserve_upstream_source"]]
        top = sorted(eligible, key=lambda x: -x[1]["performance"]["time_x_mech"])[:3]
        summaries.append({
            "language": language, "profiles": len(selected),
            "classifications": dict(Counter(r["ownership"]["classification"] for _, r in selected)),
            "protected_upstream_profiles": sum(r["ownership"]["preserve_upstream_source"] for _, r in selected),
            "largest_owned_or_unknown_fast_endpoint_gaps": [{
                "program": k, "time_x_mech": r["performance"]["time_x_mech"],
                "loc_x_mech_fast": r["performance"]["loc_x_mech_fast"],
                "observed_sample_ratio_envelope": r["performance"].get("observed_sample_ratio_envelope"),
            } for k, r in top],
        })
        priority_keys = [k for k, _ in top]
        if language == "bqn" and "knucleotide:array-bqn-faithful" in records:
            priority_keys.insert(0, "knucleotide:array-bqn-faithful")
        queue.extend(k for k in priority_keys if k not in queue)
    return {
        "schema": "owned-implementation-audit.v1",
        "canonical_input": {"path": "data/benchmarks.json", "sha256": canonical_sha256},
        "policy": {
            "scope": "All retained database profiles; original upstream submissions protected; priority languages affect review order, not ownership classification.",
            "fast_means": "Lowest saved median among retained catalog candidates under the recorded configuration; never proven globally optimal. Archived candidates outside the catalog require separate review.",
            "small_means": "Fewest retained application LOC under the existing accounting policy; never proof of a minimum idiomatic program.",
            "no_workload_executed": True, "canonical_data_changed": False,
            "uncited_does_not_mean_ai_generated": True,
            "admission_status_limit": "Candidate qualification is exact-source/configuration scoped; predecessor records remain unchanged, and archived correctness corrections are not new timing experiments.",
            "Mech_review_scope": "Separately requested application/compiler/mode review; not part of the fifteen-language priority ordering and not a proposal for native workload executors.",
            "sample_envelope_is_confidence_interval": False,
            "sample_envelope_limit": "A descriptive min/max ratio across saved observations from possibly different cohorts; no confidence or causal speedup claim.",
            "unchanged_identity_limit": "CLBG citation matching permits CRLF normalization and trimming only; declared-unmodified assertions are labeled separately.",
        },
        "summary": {
            "profiles": len(records),
            "classifications": dict(Counter(r["ownership"]["classification"] for r in records.values())),
            "source_protected_profiles": sum(r["ownership"]["preserve_upstream_source"] for r in records.values()),
            "source_review_statuses": dict(Counter(r["audit"]["status"] for r in records.values())),
            "admitted_candidates": len(admissions),
            "admission_purposes": dict(Counter(r["purpose"] for r in admissions.values())),
            "separately_scoped_compiler_review_profiles": sum(r["separately_requested_compiler_review"] for r in records.values()),
            "all_published_fast_endpoints_match_retained_minimum_median": all(r["candidate_comparison"]["published_fast_matches_lowest_retained_median"] for r in records.values()),
        },
        "priority_languages": PRIORITY,
        "optimization_checklist": [
            {"step": "lineage-and-scope", "requirement": "Bind exact application/support hashes, source notices, original citations and known predecessors. Preserve unchanged upstream submissions; unknown lineage remains explicit."},
            {"step": "required-work", "requirement": "Review semantic work and adversarial record/boundary cases, not only canonical output. Keep full inputs, all required updates/allocations, numeric order and complete output."},
            {"step": "runtime-and-idioms", "requirement": "Review documented release/flags, JIT policy, standard APIs, scalar/array representation, boxing, copying, allocation, map lookup and bounded worker scheduling."},
            {"step": "independent-candidates", "requirement": "Retain isolated complete alternatives with distinct hashes and a stated source/runtime hypothesis; source aliases are not independent optimization strategies."},
            {"step": "expressiveness", "requirement": "Review a native-language idiomatic form and the existing compact form; count all workload helpers under the same application boundary and retain formatter evidence separately."},
            {"step": "qualification", "requirement": "Before future admission, require source/work review, arbitrary small/adversarial cases, independent reference output and full-output validation; never a native workload executor or precomputed answer."},
            {"step": "future-measurement", "requirement": "Future measurements require separately authorized execution and the established guarded fresh-process full-size protocol, shuffled sequential rounds, bounded workers and matched Mech controls. This audit executes none."},
            {"step": "selection-and-reporting", "requirement": "Retain every valid sample, report medians/spread/source cost, compare fastest and smallest independently, and describe winners only within the qualified retained candidate pool."},
        ],
        "priority_language_summary": summaries,
        "initial_review_queue": queue,
        "programs": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check the retained inventory without writing any file")
    args = parser.parse_args()
    path = ROOT / "data/benchmarks.json"
    raw = path.read_bytes()
    result = make_inventory(json.loads(raw), digest(raw))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    out = ROOT / OUTPUT
    if args.check:
        if not out.is_file() or out.read_text() != text:
            raise SystemExit("Stale implementation audit inventory; regenerate it with tools/audit_owned_implementations.py")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    if path.read_bytes() != raw:
        raise SystemExit("Canonical input changed during audit")
    print(json.dumps({"status": "passed", "inventory": OUTPUT.as_posix(), **result["summary"]}))


if __name__ == "__main__":
    main()
