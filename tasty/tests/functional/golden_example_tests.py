# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand, get_random, nogen
from tasty import test_utils

class GoldenExampleTestCase(test_utils.TastyRemoteCTRL):    
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/golden_example")

    def next_data_in(self):
        self.params = {"dim": 3, "lenX": 32, "lenY": 32 }
        self.client_inputs = {"X": (1, 2, 3)}
        self.server_inputs = {"Y": (2, 3, 4)}
        self.result = 2
        yield
        for i in xrange(10):
            self.params = {"dim": rand.randint(0,100), "lenX": rand.randint(0,512), "lenY": rand.randint(0,512)}
            self.client_inputs = {"X": nogen(get_random(0,2**self.params['lenX']-1,self.params["dim"]))}
            self.server_inputs = {"Y": nogen(get_random(0,2**self.params['lenY']-1,self.params["dim"]))}
            self.result = min(map(lambda x: x[0] * x[1], zip(self.client_inputs["X"], self.server_inputs["Y"])))
            yield

    def next_data_out(self):
        while True:
            self.assertEqual(int(self.client_outputs["r"]), self.result)
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
    tests.addTest(GoldenExampleTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=0).run(suite())
