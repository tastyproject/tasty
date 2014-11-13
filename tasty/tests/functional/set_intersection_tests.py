# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand, get_random, nogen
from tasty.types import Modular
from tasty.types import key
from tasty.types import state
from tasty.debug import *
from tasty import test_utils
from itertools import imap

class SetIntersectionTestCase(test_utils.TastyRemoteCTRL):

    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/set_intersection")

    def next_data_in(self):
        self.params = {"SETSIZE_C": 3, "SETSIZE_S": 3}
        self.client_inputs = {"X": (1, 2, 3)}
        self.server_inputs = {"Y": (2, 3, 4)}
        self.intersection = set((2,3))
        yield
        for i in xrange(10):
            randset = nogen(get_random(1, 2 ** state.config.asymmetric_security_parameter -1, 100))

            self.count_C = rand.randint(1, 50)
            self.count_S = rand.randint(1, 50)
            self.params = {"SETSIZE_C" : self.count_C, "SETSIZE_S" : self.count_S}

            client_inputs = set(rand.sample(randset, self.count_C))
            server_inputs = set(rand.sample(randset, self.count_S))
            self.client_inputs = {"X": client_inputs}
            self.server_inputs = {"Y": server_inputs}

            self.intersection =  client_inputs.intersection(server_inputs)
            yield

    def next_data_out(self):
        while True:
            self.assertEqual(set(int(self.client_outputs[key]) for key in self.client_outputs.keys()), self.intersection)
            yield
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
    unittest.TextTestRunner(verbosity=0).run(suite())
