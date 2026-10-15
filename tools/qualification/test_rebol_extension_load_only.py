"""Pure regression checks; no observer, runtime or compilation is invoked."""
import copy
import json
from pathlib import Path
import types
import unittest

SOURCE=Path(__file__).with_name('rebol_extension_load_only.py')
m=types.ModuleType('load_only');m.__file__=str(SOURCE)
exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),m.__dict__)


def helper():
    e=types.SimpleNamespace(ROOT=m.ROOT,PACKET=m.PACKET,RUNTIME=Path('/retained/rebol'),
        FIXTURES=m.ROOT/'experiments/rebol/primitive-fixtures-v1',
        SUPPORT=m.ROOT/'archive/languages/rebol/20261013/drafts/private-v1/support',
        PYTHON=Path('/retained/python'),IDS=['build-extension','build-layout-probe','layout-and-exports','load-nine-commands'],
        GATES=['extension_abi_qualified','full_primitive_fixtures_qualified','chart_admission'])
    e.environment=lambda out,load=False:dict(HOME=str(out/'home'),TMPDIR=str(out/'tmp'),
        REBOL_HOME=str(out/'home'),MECH_CLBG_REBOL_PRIMITIVES=str(out/'build/clbg_primitives.dylib'))
    return e


class LoadOnly(unittest.TestCase):
    def test_only_two_read_exceptions_and_original_image_are_selected(self):
        e=helper();old=dict(output=str(m.PACKET/'run-v1'),schedule=[{}, {}, {},dict(
            command=[str(e.RUNTIME),'--quiet','--no-color',str(e.PACKET/'load-smoke.reb')],
            stdin_hex='0080ff',timeout_seconds=30)])
        before=copy.deepcopy(old);out=m.PACKET/'load-only-run-v1';slot=m.corrected_slot(e,old,out)
        self.assertEqual(old,before)
        self.assertEqual(slot['command'],[str(e.RUNTIME),'--quiet','--no-color','--do',
            'secure [%'+str(e.FIXTURES/'common.reb')+' [allow read] %'+str(e.SUPPORT/'clbg_primitives.reb')+' [allow read]]',
            str(e.PACKET/'load-smoke.reb')])
        self.assertEqual(slot['environment']['MECH_CLBG_REBOL_PRIMITIVES'],str(m.PACKET/'run-v1/build/clbg_primitives.dylib'))
        self.assertEqual(slot['environment']['HOME'],str(out/'home'))
        self.assertEqual((slot['stdin_hex'],slot['timeout_seconds']),('0080ff',30))
        old['schedule'][3]['command'].insert(1,'-s')
        with self.assertRaisesRegex(AssertionError,'invocation'):
            m.corrected_slot(e,old,out)

    def records(self):
        e=helper();old=dict(controller=str(e.ROOT/'tools/qualification/rebol_extension.py'),
            controller_sha256='8bfd7b7def7562ca810ce633dc5b92455fb29df66fc3a727641ffcc62b516493',
            typed_image_adapter=dict(path=str(m.TYPED),sha256=m.TYPED_SHA),entrypoint=str(m.TYPED))
        report=dict(schema='rebol-extension-build-layout-load-results-v1',status='stopped-unqualified',
            plan=str(m.OLD_PLAN),plan_sha256=m.OLD_PLAN_SHA,attempts=e.IDS,
            registered=[dict(id=x,pid=i+10) for i,x in enumerate(e.IDS)],
            captures=[dict(id=x) for x in e.IDS[:3]],active=None,error='Native command exited unsuccessfully',
            error_type='AssertionError',integrity_errors=[],artifact_errors=[],**{k:False for k in e.GATES})
        terminal=dict(schema='rebol-extension-build-layout-load-terminal-v1',status='stopped-unqualified',
            report_sha256=m.OLD_REPORT_SHA,expected_report_sha256=m.OLD_REPORT_SHA,
            native_processes_started=4,validated_captures=3,common_mutex_held=True,
            integrity_errors=[],artifact_errors=[],**{k:False for k in e.GATES})
        argv=[str(e.PYTHON),'-I','-S','-B',str(m.TYPED),'--adapter-sha256',m.TYPED_SHA,
            'run','--plan',str(m.OLD_PLAN),'--plan-sha256',m.OLD_PLAN_SHA]
        launch=dict(command=argv,cwd=str(m.ROOT));started=dict(launch,command_pid=9,
            command_identity=dict(pid=9,listing='exact observed birth'),command_identity_observation_missing=False)
        ended=dict(status='command-failed',exit_code=1,actual_command_started=True,automatic_retry=False,
            stop_signals=[],command_identity_observation_missing=False,command_pid=9,command_identity=started['command_identity'])
        return e,old,report,terminal,launch,started,ended

    def test_exact_three_successes_do_not_promote_failed_stage(self):
        values=self.records();before=copy.deepcopy(values[1:])
        self.assertEqual(m.check_prior_metadata(*values),9)
        self.assertEqual(values[1:],before)
        for field,value in [('status','complete'),('captures',values[2]['captures'][:2])]:
            changed=list(self.records());changed[2][field]=value
            with self.assertRaisesRegex(AssertionError,'stopped four-stage'):
                m.check_prior_metadata(*changed)
        changed=list(self.records());changed[3]['validated_captures']=4
        with self.assertRaisesRegex(AssertionError,'stopped four-stage'):m.check_prior_metadata(*changed)

    def test_original_durable_failure_and_explicit_adapter_are_mandatory(self):
        for change in ('success','old_argv','identity','gate'):
            values=list(self.records())
            if change=='success':values[6].update(status='command-exited-zero-awaiting-report-review',exit_code=0)
            elif change=='old_argv':values[4]['command']=[str(values[0].PYTHON),'-I','-S','-B','old-controller.py']
            elif change=='identity':values[6]['command_identity']=dict(pid=9,listing='different birth')
            else:values[2]['extension_abi_qualified']=True
            with self.assertRaises(AssertionError):m.check_prior_metadata(*values)


if __name__=='__main__':unittest.main()
