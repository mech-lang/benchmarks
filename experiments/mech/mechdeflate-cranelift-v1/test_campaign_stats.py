import unittest
from itertools import permutations

from campaign_stats import balanced_cycles, calibration, nonregression, simultaneous


class CampaignStatsTests(unittest.TestCase):
    def fit(self, sessions):
        return simultaneous({"forward": [[{"fixture": value} for value in row]
                                         for row in sessions]}, replicates=400)

    def test_seed_reproduces_hierarchical_resampling(self):
        fixture = [[-0.02, 0.01], [0, 0.03], [-0.01, 0.02]]
        self.assertEqual(self.fit(fixture), self.fit(fixture))
        self.assertEqual(self.fit(fixture)["cycles_per_session"], {"forward": 2})

    def test_identical_controls_and_point_decisions(self):
        seal = calibration(self.fit([[0, 0]] * 3))
        self.assertEqual(seal["decision"], "pass")
        self.assertEqual(seal["epsilon"], {"fixture": 0})
        self.assertEqual(nonregression(self.fit([[0.1, 0.1]] * 3), seal)["decision"], "fail")
        self.assertEqual(nonregression(self.fit([[-0.1, -0.1]] * 3), seal)["decision"], "pass")
        self.assertEqual(nonregression(self.fit([[-0.1, 0.1]] * 3), seal)["decision"], "unresolved")

    def test_biased_calibration_is_unresolved(self):
        seal = calibration(self.fit([[0.1, 0.1]] * 3))
        self.assertEqual(seal["decision"], "unresolved")
        self.assertEqual(seal["excludes_zero"], ["fixture"])

    def test_each_cycle_has_its_own_complete_permutation_inventory(self):
        actors = ("candidate", "control", "peer")
        cycle = [{"order": list(order)} for order in permutations(actors)]
        self.assertEqual(len(balanced_cycles(cycle + cycle, actors, 2)), 2)
        unbalanced = [cycle[1], *cycle[1:], cycle[0], cycle[0], *cycle[2:]]
        with self.assertRaises(ValueError):
            balanced_cycles(unbalanced, actors, 2)
