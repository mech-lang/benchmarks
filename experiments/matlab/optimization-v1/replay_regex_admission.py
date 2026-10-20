#!/usr/bin/env python3
"""Reconcile retained MATLAB regex evidence without launching a runtime."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "archive/comparisons/matlab-comparison/20261012/regex-case-sensitive-v1"
LEGACY = "/matlab-comparison/20261012/regex-case-sensitive-v1/"
EXPECTED_GATES = {
    "sampler_exited_normally", "authoritative_native_group_received",
    "native_inherited_common_mutex", "native_exited_normally", "no_execution_error",
    "no_wrapper_integrity_error", "no_resource_violation", "no_resource_monitor_errors",
    "no_compiler_power_monitor_errors", "no_monitor_finish_error", "no_execute_cleanup_error",
    "no_remaining_execute_group", "no_supervisor_cleanup", "no_supervisor_remaining_group",
    "valid_environment", "actual_full_workload", "exact_command_and_group",
    "complete_output_reference_match", "complete_output_bytes_and_hash", "pins_unchanged",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def relocated(path):
    return BASE / path.split(LEGACY, 1)[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def check_attempt(attempt, missing):
    gates = attempt["qualification_checks"]
    check(set(gates) == EXPECTED_GATES and all(value is True for value in gates.values()),
          f"Incomplete or failed exact gate inventory: {attempt['id']}")
    check(attempt["qualified"] is True and attempt["sampler_wait_status"] == 0,
          f"Unqualified attempt: {attempt['id']}")
    check(attempt["pins_unchanged_at_end"] is True, "Changed historical pins")
    native = attempt["supervised_native_group"]
    check(native["type"] == "native-group-started" and native["pid"] == native["pgid"]
          and native["inherited_common_mutex"] is True and native["command"] == attempt["command"],
          "Wrong native-group ownership")
    check(attempt["supervisor_remaining_members"] == [], "Supervisor left native children")
    check(attempt["exit_status"] == 0 and attempt["valid_environment"] is True,
          "Invalid native exit or environment")
    for key in ("remaining_group_members", "competing_compilers", "power_changes", "monitor_errors",
                "resource_monitor_errors"):
        check(attempt[key] == [], f"Historical anomaly: {key}")
    check(attempt["resource_violation"] is None, "Historical resource violation")
    output = attempt["validation"]
    check(output["reference_match"] is True and output["bytes"] == attempt["stdout_bytes"]
          and output["sha256"] == attempt["stdout_sha256"], "Incomplete output validation")
    supervisor_path = relocated(attempt["supervisor_result_path"])
    if supervisor_path.exists():
        supervisor = read(supervisor_path)
        check(all(key in attempt and attempt[key] == value for key, value in supervisor.items()),
              "Report/supervisor artifact mismatch")
        check(set(attempt) - set(supervisor) <= {"case", "preparation_only", "full_performance_run", "chart_admission"},
              "Unexpected report-only metadata")
    else:
        missing.append(str(supervisor_path.relative_to(ROOT)))
    raw_path = relocated(attempt["result_path"])
    if raw_path.exists():
        raw = read(raw_path)
        check(all(key in attempt and attempt[key] == value for key, value in raw.items()),
              "Raw sampler/report artifact mismatch")
    else:
        missing.append(str(raw_path.relative_to(ROOT)))


def replay():
    proposal_path = BASE / "proposal-sealed-v1.json"
    qualification_path = BASE / "qualification-v1/report.json"
    manifest_path = BASE / "studies/full-v1/regexredux/manifest.json"
    full_path = BASE / "studies/full-v1/regexredux/report.json"
    proposal, qualification, manifest, full = map(read, (proposal_path, qualification_path, manifest_path, full_path))
    check(qualification["proposal_sha256"] == digest(proposal_path), "Proposal digest mismatch")
    check(manifest["qualified_semantics_sha256"] == digest(qualification_path), "Qualification digest mismatch")
    check(full["manifest_sha256"] == digest(manifest_path), "Full manifest digest mismatch")
    check(qualification["pins_unchanged_at_end"] is True and full["pins_unchanged_at_end"] is True,
          "Historical pin closure failed")
    check(full["status"] == "complete" and full["active"] is None
          and full["skipped_failed_profile_slots"] == [], "Incomplete full cohort")
    check(manifest["canonical_full_workload"] is True and manifest["size"] == 5_000_000
          and manifest["samples"] == 3 and manifest["full_processes"] == 9, "Wrong full workload")
    missing = []
    case_files_verified = 0
    embedded_inputs_verified = 0
    for path, expected in qualification["case_pins"].items():
        local = relocated(path)
        if local.exists():
            check(digest(local) == expected, f"Changed archived case artifact: {path}")
            case_files_verified += 1
        else:
            missing.append(str(local.relative_to(ROOT)))
            if local.name == "stdin":
                case = local.parent.name
                payload = b"" if case == "runtime-identity" else bytes.fromhex(proposal["cases"][case])
                check(hashlib.sha256(payload).hexdigest() == expected,
                      "Embedded proposal input differs from missing duplicate stdin pin")
                embedded_inputs_verified += 1
    for attempt in qualification["attempts"] + full["attempts"]:
        check_attempt(attempt, missing)
    qualified_ids = ("matlab-case-compact", "matlab-case-optimized", "mech-aot-control")
    cases = set(proposal["cases"])
    observed = Counter((a["id"], a["case"]) for a in qualification["attempts"] if a["id"] in qualified_ids)
    check(observed == Counter((identity, case) for identity in qualified_ids for case in cases),
          "Wrong bounded semantic coverage")
    for attempt in qualification["attempts"]:
        if attempt["id"] in qualified_ids:
            expected = bytes.fromhex(proposal["expected"][attempt["case"]])
            check(attempt["stdout_bytes"] == len(expected)
                  and attempt["stdout_sha256"] == hashlib.sha256(expected).hexdigest(),
                  "Corrected profile does not match the common independent bounded oracle")
        if attempt["language"] == "matlab":
            witness = attempt["bounded_mutex_fd_evidence"]
            check(witness["descriptor"] == 64 and witness["native_MATLAB_engine_observed"] is True
                  and witness["errors"] == [], "Missing bounded native MATLAB mutex witness")
            check(any("cMATLAB\n" in row["lsof"] and "f64\n" in row["lsof"]
                      and "mech-clbg-timing.lock\n" in row["lsof"] for row in witness["observations"]),
                  "No actual native MATLAB lock-descriptor observation")
    check(len(qualification["attempts"]) == 18, "Wrong qualification attempt count")
    check(len(full["attempts"]) == 9, "Wrong full attempt count")
    check(Counter(a["id"] for a in full["attempts"]) == Counter({identity: 3 for identity in qualified_ids}),
          "Wrong full profile coverage")
    profiles = []
    for identity in qualified_ids:
        profile = full["profiles"][identity]
        attempts = [a for a in full["attempts"] if a["id"] == identity]
        samples = [a["seconds"] for a in attempts]
        check(samples == profile["samples_seconds"] and statistics.median(samples) == profile["median_seconds"],
              "Full sample aggregation mismatch")
        for attempt in attempts:
            check(attempt["full_workload"] is True and attempt["workload_n"] == 5_000_000,
                  "Shortened full attempt")
            check(attempt["validation"] == manifest["full_output_reference"] | {"reference_match": True},
                  "Wrong full output reference")
            check(attempt["command"] == profile["command"]
                  and attempt["source_sha256"] == profile["source_sha256"]
                  and attempt["runtime_environment"] == profile["runtime_environment"],
                  "Changed full profile source/command/environment")
        row = {"id": identity, "source_sha256": profile["source_sha256"],
               "samples_seconds": samples, "median_seconds": statistics.median(samples),
               "historical_loc": profile["loc"], "command": profile["command"],
               "runtime_environment": profile["runtime_environment"]}
        if identity.startswith("matlab-case-"):
            source = relocated(profile["source"])
            check(digest(source) == profile["source_sha256"], "Changed corrected MATLAB source")
            old = ROOT / "archive/comparisons/matlab-comparison/20261010/sources" / source.name
            check(old.read_text().split("function ", 1)[1].replace("regexpi(", "regexp(")
                  == source.read_text().split("function ", 1)[1], "Unexpected corrected application-body change")
            row.update(source=str(source.relative_to(ROOT)), body_change_only="regexpi to regexp",
                       parent_source=str(old.relative_to(ROOT)), parent_source_sha256=digest(old))
        profiles.append(row)
    return {
        "schema": "matlab-regex-historical-admission-replay.v1",
        "status": "historical-execution-evidence-reconciled-awaiting-source-accounting-and-root-admission",
        "runtime_executed": False, "canonical_catalog_changed": False, "retiming_needed_for_this_reconciliation": False,
        "artifacts": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)}
                      for p in (proposal_path, qualification_path, manifest_path, full_path)],
        "semantic_attempts": len(qualification["attempts"]), "full_attempts": len(full["attempts"]),
        "bounded_case_pin_files_verified": case_files_verified,
        "bounded_case_pin_files_recorded": len(qualification["case_pins"]),
        "missing_duplicate_stdin_pins_reconciled_from_embedded_bytes": embedded_inputs_verified,
        "missing_separate_artifacts": sorted(set(missing)),
        "archive_replay_limit": "Reports and embedded proposal case/oracle bytes are retained and hash chained. Missing duplicated stdin files are reconciled from proposal bytes (empty for runtime identity), but are not claimed present. Any other separately missing artifact remains unverified. Absence does not establish historical run failure.",
        "exact_boolean_gate_count_per_attempt": len(EXPECTED_GATES), "profiles": profiles,
        "old_source_counterexample": {
            "case": "first-pattern-case", "stdin": ">CASE\nagggtaaaAGGGTAAA\n",
            "corrected_first_count": 1, "old_first_count": 2,
            "note": "Old witnesses matched their separately adjusted expected stdout. Their qualified=True does not mean agreement with the corrected oracle.",
        },
        "remaining_admission_questions": [
            "Both exact corrected sources still have null canonical LOC in the sealed/full evidence. Replay the qualified source-accounting policy or explicitly approve the unchanged statement inventory before catalog admission.",
            "Root must independently decide source-specific ownership/admission and reconcile distinct historical cohort IDs; no source/sample replacement is performed here.",
            "This replay verifies retained artifacts and historical recorded runtime pins. It does not attest that old absolute runtime paths or binaries still exist today, or rerun native code.",
            "Root must decide whether the retained hash-chained reports, inline ownership observations and embedded input/oracle bytes suffice given missing separate case/sampler artifacts; no missing artifact is treated as verified.",
        ],
        "primary_references": [
            "https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/regexredux.html",
            "https://benchmarksgame-team.pages.debian.net/benchmarksgame/program/regexredux-python3-1.html",
            "https://www.mathworks.com/help/matlab/ref/regexp.html",
            "https://www.mathworks.com/help/matlab/ref/regexpi.html",
        ],
    }


if __name__ == "__main__":
    result = replay()
    output = Path(__file__).with_name("regex-admission-replay.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "semantic_attempts": result["semantic_attempts"],
                      "full_attempts": result["full_attempts"], "output": str(output)}))
