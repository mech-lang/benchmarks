"""Verify the final unapproved source-count receipt, entirely offline."""
import json
from pathlib import Path

import replay

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def check():
    receipt=replay.load(HERE/'source-count-receipt-v1.json')
    replay.require(receipt['schema']=='elixir-rolling-source-count-receipt.v1'
        and receipt['status']=='REPLAYED-AWAITING-INDEPENDENT-OWNER-REVIEW','Wrong source receipt')
    for item in receipt['evidence'].values():
        path=Path(item['path']);replay.require(not path.is_absolute() and '..' not in path.parts
            and replay.sha(ROOT/path)==item['sha256'],'Changed source receipt evidence')
    native=replay.load(HERE/'run-v1/report.json');_,owners=replay.make()
    replay.require(owners==replay.load(HERE/'source-ownership-proposed-v1.json'),'Stale native owner ledger')
    for name,units,physical,formatted in [('serial',81,67,74),('parallel',None,71,81)]:
        observed=next(r for r in owners['profiles'] if r['id']==name);saved=receipt[name]
        replay.require(observed['retained_rule_proposed_loc']==saved['retained_rule_proposed_loc']==units
            and observed['candidate_physical_loc']==saved['candidate_physical_loc']==physical
            and observed['candidate_formatted_application_loc']==saved['candidate_formatted_physical_loc']==formatted
            and saved['source_sha256']==observed['source_sha256'],'Candidate count/identity differs')
        replay.require(saved['original_owner_diagnostics']==observed['diagnostics']
            and saved['formatted_owner_diagnostics']==observed['formatted_diagnostics'],'Suppressed native owner diagnostic')
        replay.require(all(saved[k] is None for k in ['application_loc','physical_loc','formatted_loc','independent_review_approved']),
            'Unreviewed candidate count was approved')
    replay.require(receipt['parallel']['unqualified_arithmetic_candidate']==83
        and len(receipt['parallel']['original_owner_diagnostics'])==3,'Parallel diagnostic-only status differs')
    replay.require(all(receipt[k] is None for k in ['independent_review_approved','application_loc','formatted_loc','uniform_logical_loc'])
        and receipt['chart_admission'] is False and receipt['policy']['uniform_logical_axis_qualified'] is False,
        'Unreviewed global count/format/logical admission')
    replay.require(receipt['native_capture']['artifact_files']==len(native['artifacts'])==91
        and receipt['exact_controls']['native_artifact_byte_comparisons']==15
        and len(owners['controls'])==3 and len(owners['profiles'])==2,'Source control inventory differs')
    replay.require(receipt['current_application_boundary']==dict(parent=[47,39],historical_parent_whole_bundle=[109,93],
        excluded_support=[62,54],helper=[61,53],runner=[1,1]),'Changed current/historical application boundary')
    replay.require(receipt['frozen_native_qualification_or_pilot_changed'] is False and receipt['new_timing_observations']==0,
        'Unexpected native/timing scope')
    print(json.dumps(dict(status='PASSED-OFFLINE-SOURCE-RECEIPT',receipt=replay.ref(HERE/'source-count-receipt-v1.json'),
        serial_proposal=[81,67],parallel_retained_count=None,parallel_physical_lines=71,independent_review_approved=None)))


if __name__=='__main__':check()
