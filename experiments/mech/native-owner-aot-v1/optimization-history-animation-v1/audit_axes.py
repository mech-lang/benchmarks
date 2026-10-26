"""Check serialized SVG geometry against its visible axis labels and raw data."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
NUMBER = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("svg", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    tree = ET.parse(args.svg, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    root = tree.getroot()
    groups = {n.attrib["id"]: n for n in root.iter() if "id" in n.attrib}

    def paths(node):
        return [n for n in node.iter() if isinstance(n.tag, str) and n.tag.endswith("}path")]

    def xy(path):
        numbers = [float(n) for n in re.findall(NUMBER, path.attrib["d"])]
        assert len(numbers) % 2 == 0
        return list(zip(numbers[::2], numbers[1::2]))

    def ticks(prefix, component):
        found, minor = [], []
        for key, group in groups.items():
            if not key.startswith(prefix):
                continue
            grid = xy(paths(group)[0])
            labels = [n.text.strip().removesuffix("×") for n in group.iter() if n.tag == ET.Comment]
            labels = [float(label) for label in labels if re.fullmatch(NUMBER, label)]
            if labels:
                assert len(labels) == 1
                found.append({"value": labels[0], "position": grid[0][component]})
            else:
                minor.append(grid[0][component])
        return sorted(found, key=lambda n: n["value"]), minor

    xticks, _ = ticks("xtick_", 0)
    yticks, yminor = ticks("ytick_", 1)
    assert [t["value"] for t in xticks] == list(range(0, 55, 6))
    assert [t["value"] for t in yticks] == [1, 10, 100]
    bx = (xticks[-1]["position"] - xticks[0]["position"]) / (xticks[-1]["value"] - xticks[0]["value"])
    ax = xticks[0]["position"] - bx * xticks[0]["value"]
    by = (yticks[-1]["position"] - yticks[0]["position"]) / math.log10(yticks[-1]["value"] / yticks[0]["value"])
    ay = yticks[0]["position"] - by * math.log10(yticks[0]["value"])
    xgap = [b["position"] - a["position"] for a, b in zip(xticks, xticks[1:])]
    ygap = [a["position"] - b["position"] for a, b in zip(yticks, yticks[1:])]
    assert max(xgap) - min(xgap) < 2e-6
    assert max(ygap) - min(ygap) < 2e-6
    minor_values = sorted(10 ** ((position - ay) / by) for position in yminor)
    assert len(minor_values) == 6
    assert all(math.isclose(a, b, abs_tol=1e-5) for a, b in zip(minor_values, [.5, 2, 5, 20, 50, 200]))
    timeline = json.loads((HERE / "timeline.json").read_text())
    rows = timeline["records"]
    errors = []
    for i, row in enumerate(rows):
        group = groups[f"median-{i:03d}"]
        assert "transform" not in group.attrib
        vertices = xy(paths(group)[0])
        actual = ((min(x for x, y in vertices) + max(x for x, y in vertices)) / 2,
                  (min(y for x, y in vertices) + max(y for x, y in vertices)) / 2)
        expected = (ax + bx * row["hours"], ay + by * math.log10(row["seconds"] / row["rust_seconds"]))
        error = max(abs(a - b) for a, b in zip(actual, expected))
        assert error < 2e-5, (i, error)
        errors.append(error)
    current = xy(paths(groups["current-median-ring"])[0])
    current_center = ((min(x for x, y in current) + max(x for x, y in current)) / 2,
                      (min(y for x, y in current) + max(y for x, y in current)) / 2)
    last = rows[-1]
    assert max(abs(a - b) for a, b in zip(current_center,
        (ax + bx * last["hours"], ay + by * math.log10(last["seconds"] / last["rust_seconds"])))) < 2e-5
    parents = {child: parent for parent in root.iter() for child in parent}
    leaders_checked = 0
    for annotation in timeline["discontinuities"]:
        label = f'{annotation["number"]} {annotation["label"]}'
        targets = [g for key, g in groups.items() if key.startswith("text_")
                   and any(n.tag == ET.Comment and n.text.strip() == label for n in g.iter())]
        assert len(targets) == 1, label
        siblings = list(parents[targets[0]])
        leader = siblings[siblings.index(targets[0]) - 1]
        point = xy(paths(leader)[0])[0]
        target_rows = [r for r in rows if r["key"] == annotation["key"]
                       and math.isclose(r["hours"], annotation["hours"], abs_tol=1e-10)]
        assert len(target_rows) == 1
        target = target_rows[0]
        expected = (ax + bx * target["hours"], ay + by * math.log10(target["seconds"] / target["rust_seconds"]))
        assert max(abs(a - b) for a, b in zip(point, expected)) < 2e-5, label
        leaders_checked += 1
    report = {"status": "passed", "svg_sha256": hashlib.sha256(args.svg.read_bytes()).hexdigest(),
              "x_major_ticks": xticks, "y_major_ticks": yticks,
              "x_major_gap_svg_units": xgap, "y_major_gap_svg_units": ygap,
              "y_minor_values_recovered_from_geometry": minor_values,
              "markers_checked": len(errors), "maximum_marker_error_svg_units": max(errors),
              "annotation_leaders_checked": leaders_checked,
              "x_scale": "linear elapsed hours", "y_scale": "base-10 logarithmic runtime ratio",
              "method": "Recover scale from actual SVG tick-label text and grid coordinates, then compare every serialized marker with receipt-derived values.",
              "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["x_major_ticks", "y_major_ticks"]}, indent=2))


if __name__ == "__main__":
    main()
