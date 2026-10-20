"""Ownership protection and retained-cohort arithmetic; no workloads executed."""
import copy
import unittest

from audit_owned_implementations import ADMISSION_EXTENSIONS, classify, exact_source_reviews, make_inventory, performance


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
            language = ("matlab" if "matlab" in field else "nim" if "nim" in field
                        else "clojure" if "clojure" in field else "prolog" if "prolog" in field else "bqn")
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
        self.assertEqual(result["summary"]["admitted_candidates"], 8)
        self.assertEqual(result["summary"]["admission_purposes"], {
            "source-speed-candidate": 6, "source-expressiveness-candidate": 1,
            "archived-correctness-correction": 1})
        for i, field in enumerate(ADMISSION_EXTENSIONS):
            child = result["programs"]["task:candidate-"+str(i)]["audit"]
            parent = result["programs"]["task:parent-"+str(i)]["audit"]
            self.assertIn("further-search-open", child["status"])
            self.assertIn("predecessor", parent["qualification_note"].lower())
            self.assertNotIn("admission", parent)
            if field == "matlab_regex_case_audit":
                self.assertIn("archived-measurements", child["status"])
                self.assertIn("no-new-timing", child["runtime_configuration_status"])
            elif field == "clojure_compact_audit":
                self.assertIn("new-expressiveness-candidate", child["status"])
            else:
                self.assertIn("new-speed-candidate", child["status"])
        mech = result["programs"]["task:mech"]
        self.assertTrue(mech["separately_requested_compiler_review"])
        self.assertFalse(mech["user_requested_priority_language"])
        self.assertIn("compiler-idioms-reviewed", mech["audit"]["status"])

    def test_confirmed_policy_exclusion_overrides_measured_candidate_status(self):
        data = self.admission_catalog()
        row = data['programs']['task:candidate-0']
        for reason in ('suite-local-custom-hash-table', 'dense-and-query-only-counting-omits-library-map-work'):
            row.update(eligible_for_chart=False, eligibility_correction=dict(
                reason=reason, evidence=dict(review=dict(path='policy/review.json'))))
            original = copy.deepcopy(row)
            report = make_inventory(data, 'catalog-sha')['programs'][row['key']]['audit']
            self.assertIn('confirmed-required-work-policy-exclusion', report['status'])
            self.assertIn('historical-measurements-retained', report['status'])
            self.assertIn('policy/review.json', report['evidence'])
            self.assertEqual(data['programs'][row['key']], original)

    def test_unbound_or_incomplete_admission_metadata_never_gets_measured_status(self):
        data = self.admission_catalog()
        data["programs"]["task:candidate-0"]["source_provenance_record"]["admission"] = dict(path="other", sha256="0"*64)
        with self.assertRaisesRegex(ValueError, "Unbound"):
            make_inventory(data, "catalog-sha")
        data = self.admission_catalog(); data["bqn_spectral_audit"]["appended_programs"] = ["task:missing"]
        with self.assertRaisesRegex(ValueError, "Missing"):
            make_inventory(data, "catalog-sha")

    def lean_source_catalog(self):
        proposal, _ = exact_source_reviews(['lean4'])['lean4']
        key = 'nbody:lean4-nbody-compact-v1'
        reviewed = proposal['profiles'][key]
        row = dict(key=key, benchmark='nbody', language='lean4',
            files=[p['source_sha256'] for p in reviewed['sources']],
            file_roles={p['source_sha256']: dict(role=p['role'], included_in_application_loc=p['included_in_application'])
                        for p in reviewed['sources']},
            loc=reviewed['application_loc'], seconds=10, samples=[9, 10, 11],
            authorship=dict(origin_status='suite-authored'))
        mech = dict(key='nbody:mech', benchmark='nbody', language='mech', files=['mech-source'],
                    loc=4, seconds=2, samples=[1, 2, 3])
        files = {p['source_sha256']: dict(path=p['source_path']) for p in reviewed['sources']}
        files['mech-source'] = dict(path='retained/mech')
        return dict(programs={key: row, mech['key']: mech}, program_inventory={}, files=files, archive_paths={},
            benchmarks=[dict(key='nbody', groups=[dict(language='mech', fast=mech['key'], small=mech['key']),
                                                  dict(language='lean4', fast=key, small=key)])]), key

    def test_lean_static_review_binds_exact_profile_source_and_proposal(self):
        data, key = self.lean_source_catalog()
        row = make_inventory(data, 'catalog-sha')['programs'][key]['audit']
        self.assertTrue(row['status'].startswith('static-source-and-idiom-reviewed'))
        binding = row['source_review_binding']
        self.assertEqual(binding['path'], 'experiments/implementation-audit/v1/lean4-source-review-proposal.json')
        self.assertEqual(len(binding['sha256']), 64)
        self.assertEqual(len(binding['review_sha256']), 64)
        self.assertIs(binding['source_count_approval'], False)
        self.assertEqual(binding['source_sha256_reviewed'], [data['programs'][key]['files'][0]])

    def test_changed_lean_source_or_support_boundary_does_not_inherit_review(self):
        for changed_scope in ('application', 'support'):
            data, key = self.lean_source_catalog()
            if changed_scope == 'application':
                old = data['programs'][key]['files'][0]
                data['programs'][key]['files'][0] = 'new-application-source'
                data['files']['new-application-source'] = dict(path='new/source.lean')
                data['programs'][key]['file_roles']['new-application-source'] = data['programs'][key]['file_roles'].pop(old)
            else:
                support = data['programs'][key]['files'][1]
                data['programs'][key]['file_roles'][support]['included_in_application_loc'] = True
            row = make_inventory(data, 'catalog-sha')['programs'][key]['audit']
            self.assertEqual(row['status'], 'not-yet-source-performance-reviewed')
            self.assertNotIn('source_review_binding', row)
            self.assertNotIn('source_sha256_reviewed', row)

    def test_new_lean_profile_with_matching_source_has_no_automatic_review(self):
        data, key = self.lean_source_catalog()
        new_key = 'nbody:new-lean4-candidate'
        data['programs'][new_key] = dict(data['programs'].pop(key), key=new_key)
        group = data['benchmarks'][0]['groups'][1]
        group['fast'] = group['small'] = new_key
        row = make_inventory(data, 'catalog-sha')['programs'][new_key]['audit']
        self.assertEqual(row['status'], 'not-yet-source-performance-reviewed')
        self.assertNotIn('source_review_binding', row)


if __name__ == "__main__":
    unittest.main()
