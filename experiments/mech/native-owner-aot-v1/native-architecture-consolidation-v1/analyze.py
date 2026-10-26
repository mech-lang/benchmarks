"""Statistical acceptance only; this module cannot qualify campaign evidence."""
import json, math, random, statistics, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent

def analyze(report, plan):
    rows = report['samples']
    assert len(rows) == 96 and report['session'] in (1, 2)
    orders = plan[f"session_{report['session']}"]
    pairs = {}
    for order, expected in enumerate(orders):
        actual = [row for row in rows if row['order'] == order]
        assert len(actual) == 4
        assert sorted(r['position'] for r in actual) == [0, 1, 2, 3]
        assert [r['subject'] for r in sorted(actual, key=lambda r: r['position'])] == expected
        assert all(math.isfinite(r['seconds']) and r['seconds'] > 0 and r['verified'] for r in actual)
        pairs[order] = {r['subject']: r['seconds'] for r in actual}
    comparisons = {}
    for numerator, denominator in [('F','I'), ('F','W'), ('F','R'), ('I','W')]:
        logs = [math.log(pair[numerator] / pair[denominator]) for pair in pairs.values()]
        rng = random.Random(plan['bootstrap_seed'])
        boot = sorted(statistics.median(rng.choices(logs, k=len(logs))) for _ in range(plan['bootstrap_resamples']))
        result = dict(change_percent=100 * math.expm1(statistics.median(logs)), interval_95=[100 * math.expm1(boot[i]) for i in (499,19499)], pairs=len(logs), bootstrap_seed=plan['bootstrap_seed'])
        key = f'{numerator}/{denominator}'
        if key in plan['acceptance_upper_95_percent']:
            result['accepted'] = result['interval_95'][1] < plan['acceptance_upper_95_percent'][key]
        comparisons[key] = result
    return dict(session=report['session'], comparisons=comparisons, statistically_accepted=all(r.get('accepted', True) for r in comparisons.values()))

def analyze_sessions(reports, plan):
    sessions = [analyze(report, plan) for report in reports]
    assert [s['session'] for s in sessions] == [1, 2]
    return dict(sessions=sessions,
                statistically_accepted=all(s['statistically_accepted'] for s in sessions),
                performance_qualified=False,
                scope='Statistics only. Source, prerequisite gates and owned-process evidence require separate validation before any performance claim.')

if __name__ == '__main__':
    plan = json.loads((HERE/'plan.json').read_text())
    assert len(sys.argv) == 3, 'Supply both complete session receipts.'
    result = analyze_sessions([json.loads(Path(p).read_text()) for p in sys.argv[1:]], plan)
    (HERE/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['statistically_accepted'] else 2)
