"""Estimate paired factor effects and their interaction without pooling batches."""
import hashlib
import json
import math
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STUDY = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(sorted_values, q):
    location = (len(sorted_values) - 1) * q
    low = math.floor(location)
    high = math.ceil(location)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (location - low)


def analyze(folder, plan):
    raw = json.loads((folder / 'results.json').read_text())
    assert raw['status'] == 'all-factorial-outputs-updates-and-source-pins-verified'
    values = raw['samples_seconds']
    assert all(len(v) == 20 and all(t > 0 for t in v) for v in values.values())
    contrasts = {
        'scan_over_baseline': [math.log(a / b) for a, b in zip(values['scan'], values['baseline'])],
        'alias_over_baseline': [math.log(a / b) for a, b in zip(values['alias'], values['baseline'])],
        'combined_over_baseline': [math.log(a / b) for a, b in zip(values['combined'], values['baseline'])],
        'combined_over_scan': [math.log(a / b) for a, b in zip(values['combined'], values['scan'])],
        'combined_over_alias': [math.log(a / b) for a, b in zip(values['combined'], values['alias'])],
        'interaction': [math.log(c * b / (s * a)) for c, b, s, a in
                        zip(values['combined'], values['baseline'], values['scan'], values['alias'])],
    }
    # Resample whole matched orders jointly; no subject or fast observation
    # is selected independently. Intervals are descriptive within this fixed
    # run design and do not establish performance on other machines/programs.
    rng = random.Random(plan['bootstrap_seed'] + raw['batch'])
    draws = {key: [] for key in contrasts}
    for _ in range(plan['bootstrap_resamples']):
        indices = [rng.randrange(20) for _ in range(20)]
        for key, samples in contrasts.items():
            draws[key].append(statistics.median(samples[i] for i in indices))
    effects = {}
    for key, samples in contrasts.items():
        distribution = sorted(draws[key])
        lo, hi = [percentile(distribution, p) for p in (.025, .975)]
        value = statistics.median(samples)
        effects[key] = dict(median_paired_ratio=math.exp(value),
                            paired_change_percent=100 * math.expm1(value),
                            ratio_interval_95=[math.exp(lo), math.exp(hi)],
                            change_percent_interval_95=[100 * math.expm1(lo), 100 * math.expm1(hi)],
                            negative_orders=sum(s < 0 for s in samples), orders=len(samples))
    return dict(receipt=folder.name, results_sha256=sha(folder / 'results.json'),
                median_seconds=raw['median_seconds'], x_rust=raw['x_rust'],
                standard_deviation_seconds=raw['standard_deviation_seconds'], effects=effects,
                combined_median_change_percent=100 * (raw['median_seconds']['combined'] /
                                                      raw['median_seconds']['baseline'] - 1))


def main():
    plan = json.loads((STUDY / 'plan.json').read_text())
    batches = [analyze(HERE / f'full-preparation-interactions-v{i}', plan) for i in (1, 2)]
    result = dict(status='two-independent-factorial-batches-analyzed', plan_sha256=sha(STUDY / 'plan.json'),
                  analysis_driver_sha256=sha(Path(__file__)), batches=batches, pooled=False,
                  complete_process_observations=200,
                  interpretation='Negative interaction means the combined ratio is below the product of the two individual ratios in the same matched order. Individual effect sizes need not exceed a threshold for an interaction to exist. Intervals resample matched orders, preserve the five-subject grouping and include all observations. Each twenty-order batch remains separate; no result is selected from an extreme observation.')
    (STUDY / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
