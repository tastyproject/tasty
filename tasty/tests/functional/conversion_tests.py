# -*- coding: utf-8 -*-

import unittest
from tasty.tests.functional import generic

from tasty.utils import tasty_path, rand
from tasty import test_utils


class ConversionTestMixin(generic.TwoInputMixin, test_utils.TastyRemoteCTRL):
    MAXBITLEN=1024
    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a'], int(self.client_outputs['cc']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['cc'], self.client_inputs['a']))
            self.assertEqual(self.client_inputs['b'], int(self.client_outputs['sc']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['sc'], self.client_inputs['b']))
            self.assertEqual(self.client_outputs['cc'].bit_length(),self.params['la'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['cc'].bit_length(), self.params['la']))
            self.assertEqual(self.client_outputs['sc'].bit_length(),self.params['lb'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['sc'].bit_length(), self.params['lb']))
            self.assertEqual(self.client_inputs['a'], int(self.client_outputs['cc2']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['cc2'], self.client_inputs['a']))
            self.assertEqual(self.client_inputs['b'], int(self.client_outputs['sc2']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['sc2'], self.client_inputs['b']))
            self.assertEqual(self.client_outputs['cc2'].bit_length(),self.params['la'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['cc2'].bit_length(), self.params['la']))
            self.assertEqual(self.client_outputs['sc2'].bit_length(),self.params['lb'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['sc2'].bit_length(), self.params['lb']))
            try:
                self.client_outputs['cc'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['sc'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['cc2'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['sc2'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield


class VecConversionTestMixin(generic.TwoVecInputMixin, test_utils.TastyRemoteCTRL):
    MAXBITLEN=1024
    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a'], int(self.client_outputs['cc']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['cc'], self.client_inputs['a']))
            self.assertEqual(self.client_inputs['b'], int(self.client_outputs['sc']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['sc'], self.client_inputs['b']))
            self.assertEqual(self.client_outputs['cc'].bit_length(),self.params['la'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['cc'].bit_length(), self.params['la']))
            self.assertEqual(self.client_outputs['sc'].bit_length(),self.params['lb'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['sc'].bit_length(), self.params['lb']))
            self.assertEqual(self.client_inputs['a'], int(self.client_outputs['cc2']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['cc2'], self.client_inputs['a']))
            self.assertEqual(self.client_inputs['b'], int(self.client_outputs['sc2']),
                             msg = "protocol result is %d, should be %d"%
                             (self.client_outputs['sc2'], self.client_inputs['b']))
            self.assertEqual(self.client_outputs['cc2'].bit_length(),self.params['la'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['cc2'].bit_length(), self.params['la']))
            self.assertEqual(self.client_outputs['sc2'].bit_length(),self.params['lb'],
                             msg = "bitlength = %d, should be %d" %
                             (self.client_outputs['sc2'].bit_length(), self.params['lb']))
            try:
                self.client_outputs['cc'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['sc'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['cc2'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            try:
                self.client_outputs['sc2'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield



class UnsignedHomomorphicUnsignedConversionTestCase(ConversionTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/conversions/unsigned-homomorphic-unsigned")

class UnsignedGarbledUnsignedServerConversionTestCase(ConversionTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/conversions/unsigned-garbled-unsigned-server")

class UnsignedGarbledUnsignedClientConversionTestCase(ConversionTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/conversions/unsigned-garbled-unsigned-client")

class SignedGarbledSignedClientConversionTestCase(ConversionTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/conversions/signed-garbled-signed-client")

class UnsignedHomomorphicGarbledUnsignedConversionTestCase(ConversionTestMixin):
    def protocol_dir (self):
        return tasty_path("tests/functional/protocols/conversions/unsigned-homomorphic-garbled-unsigned")

class SignedVecHomomorphicVecGarbledVecSignedVecConverisonTestCase(VecConversionTestMixin):
    SIGNED=(True, True)
    def protocol_dir(self):
        return tasty_path("tests/functional/portocols/conversions/signedvec-homomorphicvec-garbledvec-unsignedvec")

def suite():
    """narf"""

    tests = unittest.TestSuite()
    tests.addTest(SignedGarbledSignedClientConversionTestCase())
    #tests.addTest(UnsignedGarbledUnsignedClientConversionTestCase())
    #tests.addTest(UnsignedGarbledUnsignedServerConversionTestCase())
    #tests.addTest(UnsignedHomomorphicUnsignedConversionTestCase())
    #tests.addTest(UnsignedHomomorphicGarbledUnsignedConversionTestCase())
    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

