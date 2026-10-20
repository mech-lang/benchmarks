"""Protect the JIT and workload boundary used by the Ruby comparison."""
import unittest
from unittest.mock import patch

import ruby_jit_run as run


class RubyJitBoundary(unittest.TestCase):
    def test_only_jit_and_workload_placeholders_change(self):
        profile = dict(argv=['{jit}', '-W0', '-r', '/support.rb', '/program.rb', '{n}'])
        self.assertEqual(run.command(profile, 'zjit', 50000000)[1:],
                         ['--zjit', '-W0', '-r', '/support.rb', '/program.rb', '50000000'])
        self.assertEqual(run.command(profile, 'yjit', 12)[1:],
                         ['--yjit', '-W0', '-r', '/support.rb', '/program.rb', '12'])

    def test_stdin_program_keeps_no_positional_argument(self):
        self.assertEqual(run.command(dict(argv=['{jit}', '/regex.rb']), 'zjit', 5000000)[1:],
                         ['--zjit', '/regex.rb'])

    def test_runtime_or_source_mutation_rejects_resume(self):
        plan = dict(runtime=dict(sha256='same'), controller_sha256='same',
                    profiles=[dict(source_path='program.rb', source_sha256='same', support={'support.rb':'same'})])
        with patch.object(run, 'sha', return_value='same'):
            run.check_pins(plan)
        for changed in (run.RUBY, run.ROOT/'program.rb', run.ROOT/'support.rb'):
            with self.subTest(path=changed), patch.object(run, 'sha', side_effect=lambda p: 'changed' if p == changed else 'same'):
                with self.assertRaises(AssertionError):
                    run.check_pins(plan)


if __name__ == '__main__':
    unittest.main()
