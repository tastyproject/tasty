# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand
from tasty.types import Modular
from tasty.types import key
from tasty.types import state
from tasty.debug import *
from tasty import test_utils

class SetIntersectionTestCase(test_utils.TastyRemoteCTRL):

    def __init__(self, method_name="runTest"):
        super(SetIntersectionTestCase, self).__init__(method_name)

        self.protocol_dir = tasty_path(
            "tests/functional/protocols/set_intersection")
        self.iterations = 10

    def generate_test_data_for_iteration(self):
        if self.iterations:
            start = rand.randint(1, 2 ** state.config.asymmetric_security_parameter -1)
            end = (start + 400) % 2 ** state.config.asymmetric_security_parameter -1
            if start > end:
                start, end = end, start

            self.count_C = rand.randint(1, 200)
            self.count_S = rand.randint(1, 200)
            self.params = {"SETSIZE_C" : self.count_C, "SETSIZE_S" : self.count_S}

            self.client_inputs = set([rand.randint(start, end) for count in xrange(self.count_C)])
            self.server_inputs = set([rand.randint(start, end) for count in xrange(self.count_S)])

            self.intersection =  self.client_inputs.intersection(self.server_inputs)
            self.iterations -= 1
        else:
            self.params = None

    def test_results(self):
        self.assertEqual(set(int(i) for i in self.client_outputs), self.intersection)

        #FIXME: calculate nums of costs
        #self.assertEqual(
            #self.client_costs[0]["abstract"]["online"]["accumulated"]["Enc"],
            #4)
        #self.assertEqual(
            #self.client_costs[1]["abstract"]["online"]["accumulated"]["Enc"],
            #5)
        #self.assertEqual(
            #self.client_costs[2]["abstract"]["online"]["accumulated"]["Enc"],
            #6)
        #self.assertEqual(
            #self.server_costs[0]["abstract"]["online"]["accumulated"]["Enc"],
            #3)
        #self.assertEqual(
            #self.server_costs[1]["abstract"]["online"]["accumulated"]["Enc"],
            #4)
        #self.assertEqual(
            #self.server_costs[2]["abstract"]["online"]["accumulated"]["Enc"],
            #5)

def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(SetIntersectionTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
