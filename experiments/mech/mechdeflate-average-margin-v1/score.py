"""Score the fixed 18-case loss cohort and protect all existing named wins."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from statistics import mean
import json
import math

HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(Path(path).read_text())


def metrics(cases):
    ratios = [r['paired_x_C'] for r in cases]
    assert len(ratios) == 18 and all(math.isfinite(r) and r > 0 for r in ratios)
    contributions = [
        dict(r, contribution_pp=100 * max(0, r['paired_x_C'] - 1) / 18)
        for r in cases
    ]
    return {
        'average_positive_slowdown_pct': 100 * mean(max(0, r - 1) for r in ratios),
        'geometric_mean_time_ratio': math.exp(mean(math.log(r) for r in ratios)),
        'worst_order_average_positive_slowdown_pct': 100 * mean(
            max(0, max(r['orders_x_C']) - 1) for r in cases
        ),
        'maximum_positive_slowdown_pct': 100 * max(max(0, r - 1) for r in ratios),
        'cohort_wins_in_both_orders': sum(max(r['orders_x_C']) < 1 for r in cases),
        'cases': sorted(contributions, key=lambda r: -r['contribution_pp']),
    }


def main():
    parser = ArgumentParser(__doc__)
    parser.add_argument('--results', type=Path, help='Combined controller result with two runs.')
    parser.add_argument('--forward', type=Path, help='Forward summary.json array.')
    parser.add_argument('--reverse', type=Path, help='Reverse summary.json array.')
    parser.add_argument('--actor', default='mech-experiment')
    parser.add_argument('--discovery', action='store_true', help='Allow fewer than 81 cases; still require all 18 cohort cases.')
    args = parser.parse_args()
    baseline = load(HERE / 'baseline.json')
    data = HERE / baseline['data_file']
    assert sha256(data.read_bytes()).hexdigest() == baseline['data_sha256']
    assert load(data)['losses'] == baseline['cohort']
    if not (args.results or args.forward or args.reverse):
        result = metrics(baseline['cohort'])
        assert math.isclose(result['average_positive_slowdown_pct'], baseline['average_positive_slowdown_pct'], rel_tol=1e-14)
        print(json.dumps(dict(source='pinned baseline', **result), indent=2))
        return
    if args.results:
        if args.forward or args.reverse:
            parser.error('Use --results or --forward/--reverse.')
        result = load(args.results)
        assert result['complete'], 'Both orders must be complete.'
        runs = result['runs']
    else:
        if not (args.forward and args.reverse):
            parser.error('Provide both --forward and --reverse.')
        runs = [dict(order=order, results=load(path)) for order, path in [('forward', args.forward), ('reverse', args.reverse)]]
    assert len(runs) == 2 and {r['order'] for r in runs} == {'forward', 'reverse'}
    indexed = []
    for run in sorted(runs, key=lambda r: r['order']):
        rows = {r['case']: r for r in run['results']}
        assert len(rows) == len(run['results']), 'Duplicate case names.'
        indexed.append((run['order'], rows))
    observed = set(indexed[0][1])
    assert observed == set(indexed[1][1]), 'Order inventories differ.'
    cohort = [r['case'] for r in baseline['cohort']]
    assert set(cohort) <= observed, 'All 18 fixed cohort cases are required.'
    if args.discovery:
        assert observed <= set(baseline['inventory'])
    else:
        assert observed == set(baseline['inventory']), 'Full qualification needs the original 81 cases.'

    def case_metrics(actor):
        cases = []
        for name in cohort:
            ratios = [rows[name]['paired_x_libdeflate'][actor] for _, rows in indexed]
            assert all(math.isfinite(r) and r > 0 for r in ratios)
            cases.append(dict(case=name, paired_x_C=math.exp(mean(math.log(r) for r in ratios)), orders_x_C=ratios))
        return metrics(cases)

    result = case_metrics(args.actor)
    result.update(actor=args.actor, full_81=not args.discovery, reference_average_positive_slowdown_pct=baseline['average_positive_slowdown_pct'])
    result['scores'] = []
    for order, rows in indexed:
        scores, missing, unassessed = {}, {}, {}
        for peer, protected in baseline['protected_wins'].items():
            wins = {name for name, row in rows.items() if row['paired_x_' + peer][args.actor] < 1}
            scores[peer] = len(wins)
            missing[peer] = sorted(set(protected) & observed - wins)
            unassessed[peer] = sorted(set(protected) - observed)
        result['scores'].append(dict(order=order, wins=scores, protected_missing=missing, protected_unassessed=unassessed))
    result['protected_wins_pass'] = not args.discovery and all(not any(r['protected_missing'].values()) for r in result['scores'])
    if args.actor != 'mech-control' and all('mech-control' in row['paired_x_libdeflate'] for _, rows in indexed for row in rows.values()):
        control = case_metrics('mech-control')
        result['matched_control_average_positive_slowdown_pct'] = control['average_positive_slowdown_pct']
        result['average_improvement_pp_vs_matched_control'] = control['average_positive_slowdown_pct'] - result['average_positive_slowdown_pct']
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
