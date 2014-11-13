# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand
from tasty import test_utils
from itertools import product

class GarbledFairplayTestCase(test_utils.TastyRemoteCTRL):
    """ 
    """
    def next_data_in(self):
        for i, j in product(xrange(-7, 8), xrange(-7, 8)):
            self.params = {}
            self.client_inputs = {"a": i}
            self.server_inputs = {"b": j}
            yield

    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/filecircuits/fairplaycircuit")

    def next_data_out(self):
        while True:
            self.assertEqual(int(self.client_outputs['zc']), self.client_inputs['a'] + self.server_inputs['b'])
            yield


class GarbledAESTestCase(test_utils.TastyRemoteCTRL):
    """ 
    """

    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/filecircuits/aescircuit")

    def next_data_in(self):
        self.server_inputs = {"key": 0xfffffffffffffffffffffffffffffff0}
        self.params = {}
        self.client_inputs = {"m": 0xffffffffffffffffffffffffffffffff}
        yield

    def next_data_out(self):
        self.assertEqual(int(self.client_outputs['e']), 0x3e67846d19ffcc6d56641b9a7b7b7c5f) 
        yield


def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(GarbledAESTestCase())
    tests.addTest(GarbledFairplayTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

