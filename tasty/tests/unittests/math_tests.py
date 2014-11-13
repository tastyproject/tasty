# -*- coding: utf-8 -*-

import unittest
from tasty.types import generate_keys
from tasty.types import Modular
from tasty.utils import get_random
from tasty.crypt.math import getPolyCoefficients
from tasty.crypt.math import evalPoly
from gmpy import mpz


class MathTestCase(unittest.TestCase):
    def setUp(self):
        '''prepare the test fixture and init needed data'''
        self.p, self.s = generate_keys(1024)

    def test_polynomialInterpolation(self):
        numberOfRoots = 20
        roots = get_random(0, 2**1022 - 1, numberOfRoots)
        rootsM = [Modular(val=root) for root in roots]
        coeff = getPolyCoefficients(rootsM)
        # make sure, that we get the right number of coefficients
        self.assertEqual(len(coeff), numberOfRoots+1)
        # if we evaluate the polynomial at the roots the results have to be 0
        for rootM in rootsM:
            self.assertEqual(evalPoly(coeff, rootM), Modular(val=0))
        # and if we chose other points than the roots, the evaluations mustn't be 0
        notRoots = get_random(0, 2**1022 - 1, numberOfRoots)
        notRoots = [notRoot for notRoot in notRoots if notRoot not in roots]
        for notRoot in notRoots:
            self.assertNotEqual(evalPoly(coeff,Modular(val=notRoot)), Modular(val=0))


def suite():
    suite = unittest.TestSuite()

    suite.addTest(MathTestCase("test_polynomialInterpolation"))

    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())