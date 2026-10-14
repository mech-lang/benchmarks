"""Static contracts for two fixed diagnostic sources; this does not parse APL."""
from pathlib import Path
import re
import unittest


HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "allocation-witness.apl"
FUNCTION = re.compile(r"^∇ ([^\n]+)\n(.*?)^∇$", re.M | re.S)
PROBE = [
    "Initialize", "Record 0", "BuildA", "Record 1", "BuildB", "Record 2",
    "BuildT", "Record 3", "DropT", "Record 4", "DropA", "Record 5",
    "DropB", "Record 6",
]


def functions(text):
    result = {}
    for match in FUNCTION.finditer(text):
        header = match.group(1)
        name = header.split("←")[-1].split(";")[0].split()[0]
        if name in result:
            raise ValueError("Duplicate function")
        result[name] = (header, match.group(2), match.group(0))
    return result


def lines(body):
    return [line.strip() for line in body.splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_source(text, control=False):
    """Reject changes that invalidate the fixed scope/ownership argument."""
    fs = functions(text)
    old = functions(ORIGINAL.read_text())
    require(set(fs) == {
        "Make", "Check", "Initialize", "BuildA", "BuildB", "BuildT",
        "DropT", "DropA", "DropB", "Record", "Probe", "PrintCounts", "Verify",
    }, "Unexpected function set")
    for name in ("Make", "Check"):
        require(fs[name][2] == old[name][2], "Subject definition changed")
    require(lines(fs["Probe"][1]) == PROBE, "Measurement driver changed")
    require(fs["Probe"][0] == "Probe", "Driver must return no value")
    require(fs["Record"][0] == "Record I", "Recorder must return no value")
    require(lines(fs["Record"][1]) == ["Counts[I]←⊃⎕SYL[4;1]"],
            "Recorder must use one unchanged read expression")
    require(fs["Initialize"][0] == "Initialize", "Initializer must return no value")
    require(lines(fs["Initialize"][1]) == ["A←⍬", "B←⍬", "T←⍬", "Counts←7⍴0", "Counts[0]←0"],
            "Initialization must finish before the baseline")
    builds = ["A←⍬", "B←⍬", "T←⍬"] if control else ["A←Make 0", "B←Make 0", "T←Make 2"]
    operations = dict(zip(("BuildA", "BuildB", "BuildT"), builds))
    operations.update({"DropT": "T←⍬", "DropA": "A←⍬", "DropB": "B←⍬"})
    for name, operation in operations.items():
        require(fs[name][0] == name, "Action must return no value")
        require(lines(fs[name][1]) == [operation], "Action ownership changed")
    require(fs["Verify"][0] == "Verify;A;B;T", "Output checks must use separate local trees")
    require(lines(fs["Verify"][1])[:3] == ["A←Make 0", "B←Make 0", "T←Make 2"],
            "Output checks must reconstruct the trees")
    remainder = FUNCTION.sub("", text)
    top = [line.strip() for line in remainder.splitlines()
           if line.strip() and not line.lstrip().startswith("⍝")]
    require(top == ["⎕IO←0", "⎕CT←0", "OUT←'w'⎕FIO[3]'/dev/fd/3'",
                    "Probe", "PrintCounts", "Verify", "⊣⎕FIO[4]OUT", ")OFF"],
            "All formatting/checking must follow the completed count sequence")
    require(text.count("⎕SYL") == 1, "Additional counter read")
    return fs


def owned_nodes(depth):
    return 1 if depth == 0 else 1 + 2 * owned_nodes(depth - 1)


class SourceContract(unittest.TestCase):
    def setUp(self):
        self.source = (HERE / "allocation.apl").read_text()
        self.control = (HERE / "zero-allocation-control.apl").read_text()

    def test_both_sources_preserve_scopes_and_subject(self):
        audit_source(self.source)
        audit_source(self.control, control=True)

    def test_control_changes_only_three_actions_and_output_label(self):
        left, right = functions(self.source), functions(self.control)
        differences = {name for name in left if left[name] != right[name]}
        self.assertEqual(differences, {"BuildA", "BuildB", "BuildT", "PrintCounts"})
        self.assertEqual(left["PrintCounts"][2].replace("live_deltas", "control_deltas"),
                         right["PrintCounts"][2])

    def test_oracle_follows_independent_owned_tree_roots(self):
        leaf, tree = owned_nodes(0), owned_nodes(2)
        self.assertEqual([leaf, 2 * leaf, 2 * leaf + tree, 2 * leaf, leaf, 0],
                         [1, 2, 9, 2, 1, 0])

    def test_returned_tree_would_break_scope_proof(self):
        with self.assertRaisesRegex(ValueError, "Action must return no value"):
            audit_source(self.source.replace("∇ BuildT\n", "∇ Z←BuildT\n"))

    def test_inlined_build_would_break_scope_proof(self):
        with self.assertRaisesRegex(ValueError, "Measurement driver changed"):
            audit_source(self.source.replace(" BuildT\n Record 3", " T←Make 2\n Record 3"))

    def test_check_between_samples_rejected(self):
        with self.assertRaisesRegex(ValueError, "Measurement driver changed"):
            audit_source(self.source.replace(" DropT\n Record 4", " Verify\n DropT\n Record 4"))

    def test_returned_counter_value_rejected(self):
        with self.assertRaisesRegex(ValueError, "Recorder must return no value"):
            audit_source(self.source.replace("∇ Record I\n", "∇ Z←Record I\n"))

    def test_subject_mutation_rejected(self):
        with self.assertRaisesRegex(ValueError, "Subject definition changed"):
            audit_source(self.source.replace(" Right←Make D-1", " Right←Left"))

    def test_control_allocation_rejected(self):
        altered = self.control.replace("∇ BuildA\n A←⍬", "∇ BuildA\n A←Make 0")
        with self.assertRaisesRegex(ValueError, "Action ownership changed"):
            audit_source(altered, control=True)

    def test_literal_result_vector_isolation_required_before_baseline(self):
        with self.assertRaisesRegex(ValueError, "Initialization must finish before the baseline"):
            audit_source(self.source.replace(" Counts[0]←0\n", ""))


if __name__ == "__main__":
    unittest.main()
