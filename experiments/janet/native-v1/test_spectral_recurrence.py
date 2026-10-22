"""Check recurrence boundaries and integer-exact binary64 domain at full size."""
import unittest

class RecurrenceTests(unittest.TestCase):
    def test_full_dimension_rows_and_edges(self):
        n = 5500
        for i in range(n):
            for j in (0, 1, n//2, n-2, n-1):
                for transpose in (False, True):
                    a, b = (j, i) if transpose else (i, j)
                    direct = (a+b)*(a+b+1)//2+a+1
                    start = i*(i+1)//2+(1 if transpose else i+1)
                    delta = i+(2 if transpose else 1)
                    recurrence = start+j*delta+j*(j-1)//2
                    self.assertEqual(direct, recurrence)
                    self.assertLess(direct, 2**53)
                    self.assertEqual(float(direct), direct)
                    next_a, next_b = (j+1,i) if transpose else (i,j+1)
                    next_direct = (next_a+next_b)*(next_a+next_b+1)//2+next_a+1
                    self.assertEqual(next_direct-direct, delta+j)

if __name__ == '__main__': unittest.main()
