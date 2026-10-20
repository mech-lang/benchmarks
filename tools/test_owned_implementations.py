"""Ownership protection and retained-cohort arithmetic; no workloads executed."""
import copy
import unittest

from audit_owned_implementations import ADMISSION_EXTENSIONS, classify, make_inventory, performance


class OwnedImplementationAuditTest(unittest.TestCase):
    def program(self):
        return {"key": "task:local", "files": ["app", "library"],
                "file_roles": {"library": {"included_in_application_loc": False}},
                "seconds": 12, "samples": [11, 12, 13], "loc": 6}

    def test_missing_citation_never_establishes_generated_origin(self):
        p = self.program()
        p["algorithm"] = None
        result = classify(p)
        self.assertEqual(result["classification"], "unknown")
        self.assertFalse(result["ai_authorship_inferred"])

    def test_source_identity_excludes_generic_support_but_does_not_erase_changes(self):
        p = self.program()
        p["authorship"] = {"kind": "upstream", "sources": [{
            "relationship": "implementation", "citation_check": {
                "matching_retained_source_sha256": ["app"]}}]}
        before = copy.deepcopy(p)
        result = classify(p)
        self.assertEqual(result["classification"], "unchanged-upstream")
        self.assertTrue(result["preserve_upstream_source"])
        self.assertEqual(p, before)
        p["local_adaptation"] = True
        self.assertEqual(classify(p)["classification"], "derived-adapted")

    def test_cited_upstream_is_protected_when_identity_is_incomplete(self):
        p = self.program()
        p["authorship"] = {"kind": "upstream"}
        result = classify(p)
        self.assertEqual(result["classification"], "unknown")
        self.assertTrue(result["preserve_upstream_source"])

    def test_explicit_local_origin_is_separate_from_known_translation(self):
        p = self.program()
        p["source_provenance"] = "Local MATLAB implementation of the official required algorithm."
        self.assertEqual(classify(p)["classification"], "suite-authored")
        p["authorship"] = {"parent_programs": ["task:reference"]}
        self.assertEqual(classify(p)["classification"], "derived-adapted")

    def test_comparison_uses_current_mech_seconds_and_all_saved_samples(self):
        p = self.program()
        p["y"] = 900  # Fixed best-baseline coordinates are not direct Mech ratios.
        mech = {"key": "task:mech", "seconds": 2, "loc": 3, "samples": [1, 2, 4]}
        result = performance(p, mech)
        self.assertEqual(result["time_x_mech"], 6)
        self.assertEqual(result["loc_x_mech_fast"], 2)
        self.assertEqual(result["observed_sample_ratio_envelope"], [2.75, 13])

    def admission_catalog(self):
        programs, files = {}, {}
        def add(key, language, seconds=12):
            source = key+"-sha"
            programs[key] = dict(key=key, benchmark="task", language=language, files=[source],
                loc=6, seconds=seconds, samples=[seconds-1, seconds, seconds+1])
            files[source] = dict(path="retained/"+source)
            return programs[key]
        add("task:mech", "mech", 2)
        data = dict(programs=programs, program_inventory={}, files=files, archive_paths={},
            benchmarks=[dict(key="task", groups=[dict(language="mech", fast="task:mech", small="task:mech")])])
        for i, (field, (schema, _, _)) in enumerate(ADMISSION_EXTENSIONS.items()):
            language = "matlab" if "matlab" in field else "nim" if "nim" in field else "bqn"
            parent = add("task:parent-"+str(i), language)
            candidate = add("task:candidate-"+str(i), language, 8)
            result = dict(path="evidence/"+field+"/results.json", sha256=str(i)*64)
            candidate.update(report=result["path"], source_provenance_record=dict(original_program_key=parent["key"],
                source_sha256=candidate["files"][0], admission=result),
                source_accounting=dict(application_loc=6, evidence="evidence/count-"+str(i)+".json"))
            data[field] = dict(schema=schema, appended_programs=[candidate["key"]], evidence=dict(results=result))
        return data

    def test_admissions_separate_fresh_speed_archived_correction_and_parent_review(self):
        data = self.admission_catalog(); before = copy.deepcopy(data)
        result = make_inventory(data, "catalog-sha")
        self.assertEqual(data, before)
        self.assertEqual(result["summary"]["admitted_candidates"], 4)
        self.assertEqual(result["summary"]["admission_purposes"], {"source-speed-candidate": 3, "archived-correctness-correction": 1})
        for i in range(4):
            child = result["programs"]["task:candidate-"+str(i)]["audit"]
            parent = result["programs"]["task:parent-"+str(i)]["audit"]
            self.assertIn("further-search-open", child["status"])
            self.assertIn("predecessor", parent["qualification_note"].lower())
            self.assertNotIn("admission", parent)
            if i == 3:
                self.assertIn("archived-measurements", child["status"])
                self.assertIn("no-new-timing", child["runtime_configuration_status"])
            else:
                self.assertIn("new-speed-candidate", child["status"])
        mech = result["programs"]["task:mech"]
        self.assertTrue(mech["separately_requested_compiler_review"])
        self.assertFalse(mech["user_requested_priority_language"])
        self.assertIn("compiler-idioms-reviewed", mech["audit"]["status"])

    def test_unbound_or_incomplete_admission_metadata_never_gets_measured_status(self):
        data = self.admission_catalog()
        data["programs"]["task:candidate-0"]["source_provenance_record"]["admission"] = dict(path="other", sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "Unbound"):
            make_inventory(data, "catalog-sha")
        data = self.admission_catalog(); data["bqn_spectral_audit"]["appended_programs"] = ["task:missing"]
        with self.assertRaisesRegex(ValueError, "Missing"):
            make_inventory(data, "catalog-sha")


if __name__ == "__main__":
    unittest.main()
