"""Check the exact binary64 domain of the standard positive mod opcode."""
import math
import random
import unittest

class DomainTests(unittest.TestCase):
    def test_all_widths_boundaries_and_reachable_values(self):
        rng=random.Random(20261022)
        for width in range(1,19):
            modulus=4**width
            keys=[0,1,modulus//2,modulus-2,modulus-1]+[rng.randrange(modulus) for _ in range(1000)]
            for key in keys:
                for base in range(4):
                    value=4*key+base
                    self.assertLess(value,2**38)
                    self.assertEqual(float(value),value)
                    result=float(value)-float(modulus)*math.floor(float(value)/float(modulus))
                    self.assertEqual(result,value%modulus)

if __name__=='__main__':unittest.main()
