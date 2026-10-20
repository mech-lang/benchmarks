"""Scope, Unicode, tokenizer and normalization-gap regression checks."""
import copy
import gzip
import json
import unittest

import source_metrics as metrics


def catalog_fixture():
    files = {}
    def source(name, text, role='application'):
        digest = metrics.sha(text.encode('utf-8'))
        files[digest] = dict(name=name, code=text, sha256=digest, role=role)
        return digest
    main = source('main.txt', '# attribution\r\nx := ⍳3\r\nhelper();\r\ny := 2\r\n')
    host = source('host.txt', 'generic_host();\n', 'runtime-support')
    app_helper = source('workload.txt', 'workload_specific();\n', 'application-helper')
    row = dict(language='fixture', benchmark='fixture', loc=3, files=[main, host, app_helper],
               file_roles={main: dict(role='application', support_line_ranges=[dict(start=3, end=3)])},
               formatted_loc=999, formatted_loc_complete=False, formatted_loc_status='pending')
    return dict(programs={'fixture:main': row}, files=files), (main, host, app_helper)


class SourceMetricsTests(unittest.TestCase):
    def test_exact_application_and_submitted_scopes(self):
        data, (main, host, helper) = catalog_fixture()
        row = metrics.metric_profile('fixture:main', data['programs']['fixture:main'], data['files'], True)
        unit = row['files'][0]
        application = '# attribution\r\nx := ⍳3\r\ny := 2\r\n'
        self.assertEqual(unit['application']['sha256'], metrics.sha(application.encode('utf-8')))
        self.assertEqual(unit['application']['utf8_bytes'], len(application.encode('utf-8')))
        self.assertEqual(unit['application_line_ranges'], [dict(start=1, end=2), dict(start=4, end=4)])
        self.assertEqual(row['files'][1]['application']['utf8_bytes'], 0)
        self.assertGreater(row['files'][2]['application']['utf8_bytes'], 0)
        for name in ('utf8_bytes', 'unicode_codepoints'):
            self.assertEqual(row['submitted'][name], row['application'][name] + row['excluded_support'][name])
        self.assertEqual(row['application']['gzip_bytes'],
            unit['application']['gzip_bytes'] + row['files'][2]['application']['gzip_bytes'])
        self.assertIsNone(row['application']['cl100k_base_tokens'])

    def test_comments_whitespace_unicode_and_newlines_are_never_rewritten(self):
        text = '\ufeff# comment\r\nx = "a;b"; λ ← ⍳3\r\n\r\n'
        measured = metrics.measure(text)
        self.assertEqual(measured['unicode_codepoints'], len(text))
        self.assertGreater(measured['utf8_bytes'], measured['unicode_codepoints'])
        app, excluded, _ = metrics.partition_text(text, [])
        self.assertEqual((app, excluded), (text, ''))

    def test_gzip_round_trip_fixed_header_and_repeatability(self):
        raw = '⍳3\r\n'.encode('utf-8')
        compressed = metrics.gzip_bytes(raw)
        self.assertEqual(gzip.decompress(compressed), raw)
        self.assertEqual(compressed, metrics.gzip_bytes(raw))
        self.assertEqual(compressed[4:8], b'\x00' * 4)
        self.assertEqual(compressed[3], 0)  # no filename or comment fields
        self.assertEqual(compressed[9], 255)

    def test_missing_formatter_stays_unavailable(self):
        data, _ = catalog_fixture()
        row = metrics.metric_profile('fixture:main', data['programs']['fixture:main'], data['files'], True)
        self.assertIsNone(row['canonical_formatted_loc']['value'])
        data['programs']['fixture:main']['formatted_loc_complete'] = True
        with self.assertRaisesRegex(ValueError, 'lacks evidence'):
            metrics.metric_profile('fixture:main', data['programs']['fixture:main'], data['files'], True)

    def test_source_tampering_ranges_and_roles_fail_closed(self):
        data, (main, _, _) = catalog_fixture()
        row = data['programs']['fixture:main']
        for ranges in ([dict(start=0, end=1)], [dict(start=1, end=99)],
                       [dict(start=1, end=2), dict(start=2, end=3)]):
            with self.assertRaises(ValueError):
                metrics.partition_text(data['files'][main]['code'], ranges)
        row['file_roles'][main]['included_in_application_loc'] = False
        with self.assertRaisesRegex(ValueError, 'contradicts'):
            metrics.metric_profile('fixture:main', row, data['files'], True)
        del row['file_roles'][main]['included_in_application_loc']
        data['files'][main]['code'] += 'tampering'
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            metrics.metric_profile('fixture:main', row, data['files'], True)

    def test_measurement_does_not_mutate_catalog_or_invent_logical_loc(self):
        data, _ = catalog_fixture()
        before = copy.deepcopy(data)
        report = metrics.build_report(data, json.dumps(data).encode(), include_audit=False)
        self.assertEqual(data, before)
        self.assertIsNone(report['uniform_logical_loc']['value'])
        self.assertIsNone(report['language_lexical_tokens']['value'])
        self.assertEqual(report['profiles']['fixture:main']['retained_application_loc']['value'], 3)

    def test_counter_probes_expose_gaps_and_do_not_certify_language_grammars(self):
        report = metrics.normalization_audit()
        probes = {row['id']: row for row in report['probes']}
        for name in ('python', 'julia'):
            self.assertFalse(probes[name + '-independent-semicolon-statements']['aligned'])
        self.assertIsNone(probes['mech-independent-semicolon-statements']['aligned'])
        self.assertEqual(probes['mech-independent-semicolon-statements']['native_acceptance']['status'], 'not-run')
        self.assertEqual(probes['python-independent-semicolon-statements']['native_acceptance']['status'], 'accepted')
        for name in ('csharp', 'fsharp', 'zig'):
            self.assertTrue(probes[name + '-independent-semicolon-statements']['aligned'])
        self.assertFalse(probes['mech-matrix-literal-wrapping']['aligned'])
        self.assertFalse(probes['fsharp-array-literal-wrapping']['aligned'])
        self.assertEqual(report['benchmark_executions'], 0)

    def test_proposed_logical_policy_preserves_array_notation_without_changing_counts(self):
        policy = metrics.proposed_logical_policy()
        self.assertEqual(policy['status'], 'proposed-not-qualified')
        self.assertEqual(policy['units']['written_close'], 0)
        cases = {row['id']: row for row in policy['acceptance_cases']}
        self.assertEqual(cases['mech-matrix-literal']['expected_units'], 1)
        self.assertEqual(cases['matlab-matrix-literal']['expected_units'], 1)
        self.assertEqual(cases['python-independent-statements']['expected_units'], 2)

    def test_pinned_tokenizer_or_explicit_unavailable_status(self):
        encoder, spec = metrics.tokenizer()
        if encoder is None:
            self.assertEqual(spec['status'], 'unavailable')
            self.assertIn('reason', spec)
            return
        self.assertEqual(spec['status'], 'available')
        text = '⍳3 λ <|endoftext|>\r\n'
        self.assertEqual(metrics.measure(text, encoder)['cl100k_base_tokens'], len(encoder.encode_ordinary(text)))
        self.assertEqual(encoder.decode(encoder.encode_ordinary(text)), text)


if __name__ == '__main__':
    unittest.main()
