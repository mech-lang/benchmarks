"""Unrun source regressions: fake children, real small local capture files only."""
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('julia_entry_controller', HERE/'controller.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ControllerClosure(unittest.TestCase):
    def fake_run(self, mutation=None, cleanup_failure=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output, plan_path = root/'run', root/'plan.json'
            plan = dict(output=str(output), intake=dict(path=str(root/'intake.json'), sha256='a'*64),
                pins={str(HERE/name): 'b'*64 for name in ('owned_processes.py', 'client.py', 'trace.py')},
                modules=dict(main=dict(path='/unexecuted-subject', uuid='main'),
                             runtime=dict(path='/unexecuted-runtime', uuid='runtime')),
                subject_environment={'JULIA_LOAD_CODEGEN_LIB': '0'}, debugger_environment={'PATH': '/usr/bin'},
                runtime_dwarf='/unopened-dwarf', tools=dict(lldb='/unexecuted-lldb',
                debugserver='/unexecuted-debugserver'), cwd=str(root))
            plan_raw = c.encoded(plan)
            plan_path.write_bytes(plan_raw)
            cleanup_calls = []
            private_dirs = []
            endpoint_paths = set()
            original_lstat = Path.lstat
            def fake_endpoint_stat(path, *args, **kwargs):
                observed = original_lstat(path, *args, **kwargs)
                if path in endpoint_paths:
                    # Only the fake server endpoint has a simulated socket
                    # type. Its real file still supplies the owner and inode.
                    return SimpleNamespace(st_mode=stat.S_IFSOCK|stat.S_IMODE(observed.st_mode),
                        st_uid=observed.st_uid, st_dev=observed.st_dev, st_ino=observed.st_ino)
                return observed
            class FakeOwner:
                def __init__(self, kernel, atomic, lock, verify, verify_lock, emit, deadline):
                    self.children = []
                    self.peak_rss = None
                    self.monitor_samples = 0
                def child(self, role):
                    pid = 100+len(self.children)
                    child = SimpleNamespace(role=role, pid=pid, identity={'pid': pid},
                        parent_observations=[], spawned=True, reaped=False, exit_status=None)
                    self.children.append(child)
                    return child
                def spawn_target(self, *args):
                    return self.child('subject')
                def spawn_tool(self, role, argv, *args):
                    child = self.child(role)
                    if role == 'debugserver':
                        private_dirs.append(Path(argv[1]).parent)
                        endpoint = Path(argv[1])
                        endpoint.write_bytes(b'fake owned endpoint')
                        endpoint_paths.add(endpoint)
                    else:
                        config = json.loads((output/'client-config.json').read_bytes())
                        events = [dict(kind='initial-owned-stop', pid=config['subject_pid']),
                                  dict(kind='client-complete', target_exit_status=0)]
                        # Open the existing owner-created inode, as the real
                        # client does. No script, child or debugger is executed.
                        (output/'trace.jsonl').write_bytes(b''.join(c.encoded(e).replace(b'\n', b'')+b'\n'
                            for e in events))
                    return child
                def identity(self, child):
                    return {'status': 5}
                def monitor(self, *args):
                    self.monitor_samples += 1
                def cleanup(self, terminate):
                    cleanup_calls.append(terminate)
                    if cleanup_failure:
                        # Represents cleanup(False)'s already attempted normal
                        # and forced phases, with an unreaped owned remainder.
                        raise ValueError('normal and forced cleanup failed')
                    for child in self.children:
                        child.reaped, child.exit_status = True, 0
            kb = SimpleNamespace(Kernel=lambda: object(), atomic=nullcontext)
            owner_module = SimpleNamespace(OwnedProcesses=FakeOwner)
            real_inventory = c.artifact_inventory
            injected = False
            def inventory(path, excluded=()):
                nonlocal injected
                if mutation and not injected and not excluded:
                    injected = True
                    with (path/mutation).open('ab') as stream:
                        stream.write(b' ')
                return real_inventory(path, excluded)
            try:
                with patch.object(c, 'prepare_document', return_value=plan), \
                        patch.object(c, 'verify_pins', return_value={}), \
                        patch.object(c, 'lock_identity'), \
                        patch.object(c, 'load_source', side_effect=[kb, owner_module]), \
                        patch.object(Path, 'lstat', fake_endpoint_stat), \
                        patch.object(c, 'artifact_inventory', side_effect=inventory):
                    if mutation or cleanup_failure:
                        with self.assertRaisesRegex(ValueError, 'did not close successfully'):
                            c.run(plan_path, c.digest(plan_raw), object())
                    else:
                        try:
                            c.run(plan_path, c.digest(plan_raw), object())
                        except ValueError as error:
                            failed = json.loads((output/'report.json').read_bytes())
                            self.fail(str(error)+': '+json.dumps(failed['errors']))
                report = json.loads((output/'report.json').read_bytes())
                terminal = json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['report']['sha256'], c.digest((output/'report.json').read_bytes()))
                if mutation:
                    self.assertEqual(report['status'], 'entry-capture-failed-unqualified')
                    self.assertTrue(any('prevalidated' in error['message'] for error in report['errors']),
                                    report['errors'])
                    self.assertTrue(terminal['errors'])
                elif cleanup_failure:
                    self.assertEqual(cleanup_calls, [False], report['errors'])
                    self.assertFalse(terminal['all_owned_children_reaped'])
                else:
                    self.assertEqual(report['status'], 'raw-entry-capture-complete-awaiting-semantic-review')
                    self.assertTrue(terminal['all_owned_children_reaped'])
                    self.assertEqual(cleanup_calls, [False])
                self.assertTrue(all(terminal[key] is False for key in c.FALSE_FLAGS))
            finally:
                for private in private_dirs:
                    (private/'debug.sock').unlink(missing_ok=True)
                    private.rmdir()

    def test_complete_fake_capture_retains_false_semantic_flags(self):
        self.fake_run()

    def test_initial_inventory_cannot_adopt_modified_validated_trace(self):
        self.fake_run(mutation='trace.jsonl')

    def test_initial_inventory_cannot_adopt_modified_client_configuration(self):
        self.fake_run(mutation='client-config.json')

    def test_failed_normal_and_forced_cleanup_is_not_repeated_a_third_time(self):
        self.fake_run(cleanup_failure=True)


if __name__ == '__main__':
    unittest.main()
