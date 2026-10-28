"""Qualify performance only after prerequisite and raw-process evidence checks."""
import json
import sys
from analyze import analyze_sessions
from campaign import validate_reports
from study import HERE, STUDY_ID, process, read, read_plan


def qualify(reports, plan):
    validate_reports(reports, plan)
    result = analyze_sessions(reports, plan)
    result.update(study_id=STUDY_ID, evidence_validated=True,
                  performance_qualified=result['statistically_accepted'],
                  scope='Both complete sessions, committed prerequisites and all 192 raw owned-process observations validated.')
    return result


if __name__ == '__main__':
    assert len(sys.argv) == 3, 'Supply both complete session receipts.'
    result = qualify([read(path) for path in sys.argv[1:]], read_plan())
    process.save(HERE / 'qualification-analysis.json', result)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['performance_qualified'] else 2)
