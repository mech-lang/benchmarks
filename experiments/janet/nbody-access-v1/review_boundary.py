"""Additive clarification of telemetry wording; never alter captured elapsed values."""
import json
from pathlib import Path
from common import HERE,ROOT,process

def main():
    cases=[]
    for directory in (HERE/'run-v1',HERE.parent/'revcomp-stream-v1/run-v2',HERE.parent/'revcomp-stream-v1/block-run-v1'):
        report=json.loads((directory/'results.json').read_bytes())
        assert report['status'] in ('twelve-full-size-complete-process-outputs-pass','nine-full-size-complete-process-outputs-pass','three-full-size-complete-process-outputs-pass')
        examples=[]
        for sample in report['samples']:
            path=directory/f"{sample['sample']:02d}-{sample['label']}"/'process.json';r=json.loads(path.read_bytes())
            birth=r['birth_identity'];start=birth['birth_seconds']+birth['birth_microseconds']/1e6
            # One-second margins avoid inferring submillisecond fork/exec boundaries.
            for telemetry in sorted(directory.glob('telemetry-*-battery/process.json')):
                tr=json.loads(telemetry.read_bytes());tb=tr['birth_identity'];when=tb['birth_seconds']+tb['birth_microseconds']/1e6
                if start+1<when<start+r['elapsed_seconds']-1:
                    examples.append(dict(subject=str(path.relative_to(ROOT)),snapshot=str(telemetry.relative_to(ROOT)),subject_elapsed_seconds=r['elapsed_seconds'],subject_sha256=process.sha(path),snapshot_sha256=process.sha(telemetry)))
                    break
        assert len(examples)==len(report['samples'])
        cases.append(dict(report=str((directory/'results.json').relative_to(ROOT)),report_sha256=process.sha(directory/'results.json'),subjects_with_strictly_inside_live_snapshot=len(examples),examples=examples))
    result=dict(schema='janet-telemetry-boundary-clarification.v1',status='verified-additive-wording-clarification',
                source_controller=dict(path='experiments/janet/knucleotide-bytes-v1/process.py',sha256=process.sha(HERE.parent/'knucleotide-bytes-v1/process.py')),
                corrected_boundary='The clock runs from immediately before fork through independently observed subject exit. Read-only process/power snapshots taken while the subject lives are concurrent host activity inside this wall-time window, with possible scheduling/I/O contention. Post-exit callbacks do not extend the independent exit timestamp; validation and group cleanup follow the observed exit.',
                affected_wording='The n-body frozen controller/report says telemetry is excluded, and the historical reverse-complement README describes all telemetry as outside the interval. Those phrases apply only to direct post-exit callback overhead, not to concurrent snapshots during a live subject.',
                elapsed_samples_changed=False,source_controller_changed=False,prior_sealed_artifacts_changed=False,reports=cases)
    target=HERE.parent/'measurement-boundary-review-v1.json';process.save(target,result)
    print('Verified live snapshots inside',sum(r['subjects_with_strictly_inside_live_snapshot'] for r in cases),'subject windows; elapsed values unchanged')

if __name__=='__main__':main()
