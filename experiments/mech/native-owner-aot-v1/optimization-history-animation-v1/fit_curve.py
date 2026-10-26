#!/usr/bin/env python3
"""Fit an offset and two exponential components to all measured medians."""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    source = HERE / "timeline.json"
    rows = json.loads(source.read_text())["records"]
    xs = [r["hours"] for r in rows]
    ys = [r["x_rust"] for r in rows]
    zs = [math.log(y) for y in ys]
    assert len(rows) == 120

    def parameters(v):
        c, a, b, slow, delta = [math.exp(x) for x in v]
        return dict(C=c, A_fast=a, A_slow=b, k_fast=slow + delta, k_slow=slow)

    def predictions(p):
        return [p["C"] + p["A_fast"] * math.exp(-p["k_fast"] * x)
                + p["A_slow"] * math.exp(-p["k_slow"] * x) for x in xs]

    def loss(v):
        if max(v) > 30 or min(v) < -40:
            return 1e100
        return sum((a - b) ** 2 for a, b in zip(ys, predictions(parameters(v))))

    def minimize(start):
        points = [list(start)] + [[v + (.2 if j == i else 0) for j, v in enumerate(start)] for i in range(5)]
        values = [loss(p) for p in points]
        for iteration in range(3500):
            order = sorted(range(6), key=lambda i: values[i])
            points = [points[i] for i in order]
            values = [values[i] for i in order]
            if max(abs(v - values[0]) for v in values) < 1e-12 and max(abs(points[i][j] - points[0][j]) for i in range(6) for j in range(5)) < 1e-6:
                break
            center = [sum(p[j] for p in points[:-1]) / 5 for j in range(5)]
            reflected = [2 * c - w for c, w in zip(center, points[-1])]
            fr = loss(reflected)
            if fr < values[0]:
                expanded = [c + 2 * (r - c) for c, r in zip(center, reflected)]
                fe = loss(expanded)
                points[-1], values[-1] = (expanded, fe) if fe < fr else (reflected, fr)
            elif fr < values[-2]:
                points[-1], values[-1] = reflected, fr
            else:
                outside = fr < values[-1]
                contracted = [c + .5 * ((r if outside else w) - c) for c, r, w in zip(center, reflected, points[-1])]
                fc = loss(contracted)
                if fc < (fr if outside else values[-1]):
                    points[-1], values[-1] = contracted, fc
                else:
                    for i in range(1, 6):
                        points[i] = [(a + b) / 2 for a, b in zip(points[0], points[i])]
                        values[i] = loss(points[i])
        assert iteration < 3499
        p = parameters(points[min(range(6), key=lambda i: values[i])])
        pred = predictions(p)
        raw_sse = sum((a - b) ** 2 for a, b in zip(ys, pred))
        log_sse = sum((a - math.log(b)) ** 2 for a, b in zip(zs, pred))
        p.update(iterations=iteration, raw_sse=raw_sse, log_sse=log_sse,
                 r_squared_original=1 - raw_sse / sum((y - sum(ys) / len(ys)) ** 2 for y in ys),
                 r_squared_log=1 - log_sse / sum((z - sum(zs) / len(zs)) ** 2 for z in zs),
                 multiplicative_rmse=math.exp(math.sqrt(log_sse / len(xs))))
        return p

    starts = [(.7, 213, 2.5, .04, 1.2), (.2, 210, 6, .08, 1.0),
              (1, 215, 3, .02, 1.5), (1, 210, 6, .2, .8), (.1, 215, 2, .01, 2)]
    runs = [minimize([math.log(v) for v in start]) for start in starts]
    fit = min(runs, key=lambda p: p["raw_sse"])
    assert max(p["raw_sse"] for p in runs) - fit["raw_sse"] < 1e-8
    residual = [y - predicted for y, predicted in zip(ys, predictions(fit))]
    fast = [math.exp(-fit["k_fast"] * x) for x in xs]
    slow = [math.exp(-fit["k_slow"] * x) for x in xs]
    gradient = dict(C=-2 * sum(residual),
        A_fast=-2 * sum(e * g for e, g in zip(residual, fast)),
        A_slow=-2 * sum(e * g for e, g in zip(residual, slow)),
        k_fast=2 * fit["A_fast"] * sum(e * x * g for e, x, g in zip(residual, xs, fast)),
        k_slow=2 * fit["A_slow"] * sum(e * x * g for e, x, g in zip(residual, xs, slow)))
    assert max(abs(v) for v in gradient.values()) < .01
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = dict(schema="mech.optimization-history-fit.v1", fitted_cohorts=len(rows),
        model="r(h) = C + A_fast exp(-k_fast h) + A_slow exp(-k_slow h)",
        objective="Unweighted least squares in measured runtime ratios, using all 120 medians.",
        drawn_fit=fit, starts=starts, optimization_runs=runs,
        first_derivatives_sse=gradient, source_sha256=digest(source),
        fitter_sha256=digest(Path(__file__)))
    (HERE / "best-fit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"medians": len(rows), "fit": fit, "gradient": gradient}, indent=2))


if __name__ == "__main__":
    main()
