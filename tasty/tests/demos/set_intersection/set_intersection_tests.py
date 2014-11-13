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

    def __init__(self, method_name="runTest"):
        super(SetIntersectionTestCase, self).__init__(method_name)

        self.protocol_dir = tasty_path(
            "tests/demos/set_intersection")

    def next_data_in(self):
        self.params = {"SETSIZE_C": 3, "SETSIZE_S": 3}
        self.client_inputs = {"X": (1, 2, 3)}
        self.server_inputs = {"Y": (2, 3, 4)}
        self.intersection = set((2,3))
        yield
        for i in xrange(3):
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

def suite():
    tests = unittest.TestSuite()
    tests.addTest(SetIntersectionTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
