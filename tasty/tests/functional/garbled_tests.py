# -*- coding: utf-8 -*-

import unittest
from tasty.tests.functional import generic

from tasty.utils import tasty_path, rand
from tasty import test_utils


class GarbledAndTestCase(generic.TwoInputMixin, test_utils.TastyRemoteCTRL):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/garbled/and")

    MAXBITLEN=256
    SAMEBITLEN=True
    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a']&self.client_inputs['b'], int(self.client_outputs['c']), 
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'], 
                              self.client_inputs['a'] & self.client_inputs['b']))
            self.assertEqual(self.client_outputs['c'].bit_length(), max((self.params['la'], self.params['lb'])), 
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(), 
                              max((self.params['la'], self.params['lb']))))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield


class GarbledNotTestCase(generic.TwoInputMixin, test_utils.TastyRemoteCTRL):
    MAXBITLEN=256
    

    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/garbled/not")
    
    def next_data_out(self):
        def Not(b, l):
            return b ^ ((1<<l) - 1)

        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(Not(self.client_inputs['a'], self.params['la']), int(self.client_outputs['c']), 
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'], 
                              Not(self.client_inputs['a'], self.params['la'])))
            self.assertEqual(self.client_outputs['c'].bit_length(), self.params['la'],
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(), 
                              self.params['la']))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield
def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(GarbledAndTestCase())
    tests.addTest(GarbledNotTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

