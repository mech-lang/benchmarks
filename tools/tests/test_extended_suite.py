import copy
import json
from pathlib import Path
import sys
import unittest
import zlib

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from application_tasks import validate_deflate,nbody_output,validate_nbody,snapshot_u8,NBODY_STEPS,FASTA_N
from benchmark_suite import ROOT,load_catalog,measurement_response,equal
from extended_oracles import table_join,graph,ekf
from suite_oracle import outputs


class ExtendedContracts(unittest.TestCase):
    def test_boolean_and_large_exact_integer_answers_cannot_alias_other_values(self):
        task={'absolute_tolerance':0,'relative_tolerance':0}
        self.assertFalse(equal(1,True,task))
        self.assertFalse(equal(True,1,task))
        self.assertFalse(equal(2**60+1,2**60,task))
        self.assertTrue(equal(2**60,2**60,task))

    def test_join_oracle_preserves_duplicates_outer_nulls_and_anti_cardinality(self):
        inner=table_join('join',1.0)
        self.assertEqual(inner['rows'],[[1.0,10.0,20.0],[1.0,10.0,21.0],[1.0,11.0,20.0],[1.0,11.0,21.0],[2.0,12.0,22.0]])
        self.assertEqual(table_join('left-semi-join',1.0)['rows'],[[1.0,10.0],[1.0,11.0],[2.0,12.0]])
        self.assertEqual(table_join('left-anti-join',1.0)['rows'],[[3.0,13.0]])
        self.assertEqual(table_join('full-outer-join',1.0)['rows'][-2:],[[3.0,13.0,None],[4.0,None,23.0]])
        self.assertEqual(table_join('left-semi-join',7.0)['rows'],[[2.0,12.0]])

    def test_graph_bridge_changes_reachability_and_parallel_edge_multiplicity(self):
        disconnected=graph(0.0)['values'];connected=graph(1.0)['values'];parallel=graph(2.0)['values']
        self.assertEqual(disconnected[4:],[0.0]*4)
        self.assertTrue(all(x>0 for x in connected))
        self.assertEqual(parallel[4:],[2*x for x in connected[4:]])
        self.assertEqual(connected[:4],disconnected[:4])

    def test_unicode_raw_equality_and_frozen_fsm_capture_are_distinct(self):
        cases={c['id']:c for c in load_catalog()['cases']}
        observations=outputs(cases['strings'],len(cases['strings']['measurement']['schedule']))
        self.assertNotEqual(observations[1],observations[2])
        self.assertEqual(outputs(cases['state-machines'],2),[{'kind':'unpublished'},{'kind':'scalar','value':True}])

    def test_full_ekf_trace_and_covariance_are_required(self):
        case=next(c for c in load_catalog()['cases'] if c['id']=='ekf')
        frames=case['measurement']['schedule'];self.assertEqual(len(frames),4096)
        trajectory=outputs(case,4096)
        self.assertEqual(len(trajectory),4096)
        for observed in trajectory:
            values=observed['values'];self.assertEqual(len(values),12)
            self.assertGreater(min(values[3],values[7],values[11]),0)
            self.assertAlmostEqual(values[4],values[6],places=12)
            self.assertAlmostEqual(values[5],values[9],places=12)
        self.assertAlmostEqual(trajectory[-1]['values'][0],18.16982725892544,places=9)

    def test_full_application_sizes_and_control_backends_cannot_be_smoke_substitutes(self):
        cases={c['id']:c for c in load_catalog()['cases']}
        self.assertEqual(FASTA_N,25_000_000);self.assertEqual(NBODY_STEPS,50_000_000)
        self.assertEqual(cases['knucleotide']['task']['logical_input_elements'],125_000_000)
        self.assertEqual(cases['knucleotide']['task']['input_bytes'],254_166_745)
        self.assertEqual(cases['nbody']['task']['logical_input_elements'],NBODY_STEPS)
        self.assertNotIn('jvm',cases)
        self.assertEqual(cases['related-post-gen']['task']['logical_input_elements'],5000)
        self.assertEqual(cases['deflate']['task']['logical_input_elements'],6_627_202)
        self.assertTrue({'program-jit','program-jit-bytecode','roc','libdeflate'}<=set(cases['deflate']['backends']))

    def test_primary_metric_does_not_require_resident_timings_for_jit(self):
        case=next(c for c in load_catalog()['cases'] if c['id']=='jit')
        expected=outputs(case,1)[0]
        response={'outcome':'ok','iterations':1,'output_name':'result','final_output':expected,
            'metrics':{'jit_invocation_seconds':1e-6,'source_to_artifact_seconds':.1,'artifact_bytes':100,'managed_after_drop_bytes':0}}
        self.assertEqual(measurement_response(response,expected,case,1),('ok',None))
        response['metrics']['jit_invocation_seconds']=0
        self.assertEqual(measurement_response(response,expected,case,1)[0],'incorrect')


class CompleteApplicationValidation(unittest.TestCase):
    def setUp(self):
        self.plain=b'complete input with overlapping repetitions '*16
        encoder=zlib.compressobj(6,zlib.DEFLATED,-15)
        self.stream=encoder.compress(self.plain)+encoder.flush()

    def test_inflation_requires_eof_complete_input_and_no_trailing_bytes(self):
        self.assertTrue(validate_deflate(self.stream,self.plain,b'')['complete_stream'])
        for bad in [self.stream[:-1],self.stream+b'trailing',b'']:
            with self.assertRaises((ValueError,zlib.error)):validate_deflate(bad,self.plain,b'')
        with self.assertRaises(ValueError):validate_deflate(self.stream,self.plain[:-1],b'')

    def test_prefix_and_exact_reference_are_separate_from_stream_validity(self):
        validate_deflate(b'prefix'+self.stream,self.plain,b'prefix',b'prefix'+self.stream)
        with self.assertRaises(ValueError):validate_deflate(b'wrong'+self.stream,self.plain,b'prefix')
        with self.assertRaises(ValueError):validate_deflate(self.stream,self.plain,b'',self.stream+b'x')

    def test_all_preserved_small_and_boundary_streams_independently_inflate(self):
        root=ROOT/'suite/applications'
        for case in json.loads((root/'deflate-compress-reference.json').read_text())['cases']:
            validate_deflate(bytes(case['expected']),bytes(case['input']),bytes(case['prefix']),bytes(case['expected']))
        for name in ('16384-distribution-change','33027-periodic-window'):
            base=root/('deflate-boundary-'+name)
            validate_deflate(base.with_suffix('.deflate').read_bytes(),base.with_suffix('.input').read_bytes(),b'')

    def test_nbody_rejects_missing_extra_nonfinite_and_incorrect_outputs(self):
        expected=[-.169075164,-.169059907]
        validate_nbody(b'-0.169075164\n-0.169059907\n',expected)
        for raw in (b'-0.169075164\n',b'nan\n0\n',b'0\n0\n',b'0\n0\n0\n'):
            with self.assertRaises(ValueError):validate_nbody(raw,expected)

    def test_snapshot_cannot_hide_extra_or_truncated_payload_bytes(self):
        import struct
        blob=b'mech-snapshot-v1\0'+b'x'*32+struct.pack('<Q',0)+struct.pack('<Q',3)+b'abc'
        self.assertEqual(snapshot_u8(blob),b'abc')
        for raw in (blob[:-1],blob+b'x',b'bad'):
            with self.assertRaises(ValueError):snapshot_u8(raw)


if __name__=='__main__':unittest.main()
