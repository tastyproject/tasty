# -*- coding: utf-8 -*-

import unittest
from tasty.tests.functional import generic

from tasty.utils import tasty_path, rand
from tasty import test_utils


class AddTestMixin(generic.TwoInputMixin):
    MAXBITLEN=256
    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a']+self.client_inputs['b'], int(self.client_outputs['c']), 
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'], 
                              self.client_inputs['a'] + self.client_inputs['b']))
            self.assertEqual(self.client_outputs['c'].bit_length(), max((self.params['la'], self.params['lb'])) + 1, 
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(), 
                              max((self.params['la'], self.params['lb'])) + 1))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield



class UnsignedAddTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/add/unsigned")

class HomomorphicUnsignedAddTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/add/homomorphic_unsigned")    

class UnsignedHomomorphicAddTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/unsigned_homomorphic")

class HomomorphicAddTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/homomorphic")

class GarbledAddClientClientClientTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_client_client_client")

class GarbledAddClientServerClientTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_client_server_client")

class GarbledAddServerServerClientTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_server_server_client")

class GarbledAddServerServerServerTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_server_server_server")

class GarbledAddClientServerServerTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_client_server_server")

class GarbledAddClientClientServerTestCase(test_utils.TastyRemoteCTRL, AddTestMixin):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/add/garbled_client_client_server")




def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(UnsignedAddTestCase())
    tests.addTest(HomomorphicUnsignedAddTestCase())
    tests.addTest(UnsignedHomomorphicAddTestCase())
    tests.addTest(HomomorphicAddTestCase())
    tests.addTest(GarbledAddClientClientClientTestCase())
    tests.addTest(GarbledAddClientServerClientTestCase())
    tests.addTest(GarbledAddServerServerClientTestCase())
    tests.addTest(GarbledAddClientClientServerTestCase())
    tests.addTest(GarbledAddClientServerServerTestCase())
    tests.addTest(GarbledAddServerServerServerTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

