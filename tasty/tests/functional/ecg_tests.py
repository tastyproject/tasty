# -*- coding: utf-8 -*-

import unittest

from tasty.utils import tasty_path, rand, get_random, nogen
from tasty import test_utils
from operator import mul


class done(Exception):
    pass

def dot(a, b):
    return sum(map(mul, a, b))
    

class ECGTestCase(test_utils.TastyRemoteCTRL):    
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/ecg_classification")


    def next_data_in(self):
        self.params = {}
        self.client_inputs = {"x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]}
        self.server_inputs = {"A": [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 
                                    [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
                                    [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17], 
                                    [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                                    [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 
                                    [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]]}
        self.result = "NSR"
        yield
        for i in xrange(10):
            self.client_inputs = {"x": list(get_random(-2**23,2**23, 15))}
            self.server_inputs = {"A": [list(get_random(-2**23, 2**23, 15)) for i in xrange(6)]}
            x = map(lambda a: dot(self.client_inputs['x'], a), self.server_inputs['A'])
            class Done(Exception):
                pass
            try:
                done = Done()
                if x[0] <= 0:
                    if x[2] <= 0:
                        self.result = "VF"
                    else:
                        self.result = "VT"
                    raise done
                else:
                    if x[2] <= 0: 
                        self.result = "SVT"
                        raise done
                    if x[1] > 0:
                        if x[3] <= 0 and x[4] <= 0:
                            self.result = "PVC"
                            raise done
                        if x[3] > 0 and x[5] <= 0:
                            self.result = "APC"
                            raise done
                self.result = "NSR"
            except Done:
                pass              
            yield

    def next_data_out(self):
        while True:
            self.assertEqual(self.client_outputs["out"], self.result)
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
    tests.addTest(ECGTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=0).run(suite())
