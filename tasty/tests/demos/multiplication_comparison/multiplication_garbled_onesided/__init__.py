# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, get_random, nogen
from tasty import test_utils

class UnsignedAddTestCase(test_utils.TastyRemoteCTRL):

    def __init__(self, method_name="runTest"):
        super(UnsignedAddTestCase, self).__init__(method_name)

        self.protocol_dir = tasty_path(
            "tests/functional/protocols/unsigned_add")
        self.iterations = 10

    def generate_test_data_for_iteration(self):
        if self.iterations:
            self.client_inputs = nogen(get_random(1, 2**32 - 1, 2))
            self.server_inputs = tuple()
            self.params = {}
            self.iterations -= 1
        else:
            self.params = None

    def test_results(self):
        self.assertEqual(sum(self.client_inputs), int(self.client_outputs[0]))

def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(UnsignedAddTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

