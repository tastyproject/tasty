# -*- coding: utf-8 -*-

import unittest
#from tasty.tests.functional.protocols import generic_tests

from tasty.utils import tasty_path, rand
from tasty import test_utils
from itertools import product

class GarbledFairplayTestCase(test_utils.TastyRemoteCTRL):
    """
    """

    def protocol_dir(self):
        return tasty_path("tests/demos/fairplay_circuit")

    def next_data_in(self):
        for i, j in product(xrange(-7, 8, 3), xrange(-7, 8, 3)):
            self.params = {}
            self.client_inputs = {"a": i}
            self.server_inputs = {"b": j}
            yield

    def next_data_out(self):
        while True:
            self.assertEqual(int(self.client_outputs['zc']), self.client_inputs['a'] + self.server_inputs['b'])
            yield


def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(GarbledFairplayTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())


