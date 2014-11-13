# -*- coding: utf-8 -*-
import unittest
from tasty.tests.functional import generic

from tasty.utils import tasty_path, rand
from tasty import test_utils


class MulTest(test_utils.TastyRemoteCTRL, generic.TwoInputMixin):

    MAXBITLEN=256

    def next_data_out(self):
        while True:
	    self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a']*self.client_inputs['b'], int(self.client_outputs['c']), 
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'], 
                              self.client_inputs['a'] * self.client_inputs['b']))
            self.assertEqual(self.client_outputs['c'].bit_length(), self.params['la'] + self.params['lb'],
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(), 
                              max((self.params['la'], self.params['lb'])) + 1))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield



class HomomorphicMulTestCase(MulTest):
    def __init__(self, method_name="runTest"):
        test_utils.TastyRemoteCTRL.__init__(self, method_name)

        self.protocol_dir = tasty_path(
            "tests/demos/multiplication_comparision/multiplication_homomorphic")
    

class HomomorphicMulOnesidedTestCase(MulTest):
    def __init__(self, method_name="runTest"):
        test_utils.TastyRemoteCTRL.__init__(self, method_name)

        self.protocol_dir = tasty_path(
            "tests/demos/multiplication_comparison/multiplication_homomorphic_onesided")
    

class GarbledMulTestCase(MulTest):
    def __init__(self, method_name="runTest"):
        test_utils.TastyRemoteCTRL.__init__(self, method_name)

        self.protocol_dir = tasty_path(
            "tests/demos/multiplication_comparision/multiplication_garbled")

class GarbledMulOnesidedTestCase(MulTest):
    def __init__(self, method_name="runTest"):
        test_utils.TastyRemoteCTRL.__init__(self, method_name)

        self.protocol_dir = tasty_path(
            "tests/demos/multiplication_comparision/multiplication_garbled_onesided")




def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(HomomorphicMulTestCase())
    tests.addTest(HomomorphicMulOnesidedTestCase())
    tests.addTest(GarbledMulOnesidedTestCase())
    tests.addTest(GarbledMulTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

