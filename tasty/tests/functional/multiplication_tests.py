# -*- coding: utf-8 -*-

from itertools import izip
import unittest
from tasty.tests.functional import generic

from tasty.utils import tasty_path, rand, get_random, nogen
from tasty import test_utils

class MulTest(test_utils.TastyRemoteCTRL, generic.TwoInputMixin):

    MAXBITLEN = 256
    COUNT = 3

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


class SignedMulTest(test_utils.TastyRemoteCTRL):

    MAXBITLEN = 256
    COUNT = 3

    def next_data_in(self):
        self.params = {"la": 32, "lb": 32}
        self.inputs = {"a": 0, "b": rand.randint(1, 2**31 - 1)}
        yield
        self.inputs = {"b": 0, "a": rand.randint(1, 2**31 - 1)}
        yield
        self.inputs = {"a": 0, "b": 0}
        yield
        self.inputs = {"a": 2**31 - 1, "b": 2**31 - 1}
        yield

        for i in xrange(self.COUNT):
            la = rand.randint(2, self.MAXBITLEN)
            lb = rand.randint(2, self.MAXBITLEN)
            self.params = {'la': la, 'lb': lb}
            self.inputs = {
                    'a': rand.randint(1, (2 ** (la - 1)) - 1),
                    'b': rand.randint(1, (2 ** (lb - 1)) - 1)}
            yield

    def next_data_out(self):
        while True:
            lg = self.params['la'] + self.params['lb']
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a']*self.client_inputs['b'], int(self.client_outputs['c']),
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'],
                              self.client_inputs['a'] * self.client_inputs['b']))
            self.assertEqual(self.client_outputs['c'].bit_length(), lg,
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(),
                              lg))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield


class GarbledMulTest(test_utils.TastyRemoteCTRL):
    """garbled bitlengths must be equal for now"""
    MAXBITLEN=1024
    MAXDIM=128
    COUNT = 1

    def next_data_in(self):
        self.params = {"la": 32, "lb": 32}
        self.inputs = {"a": 0, "b": rand.randint(1, 2 ** 32 - 1)}
        yield
        self.inputs = {"b": 0, "a": rand.randint(1, 2 ** 32 - 1)}
        yield
        self.inputs = {"a": 0, "b": 0}
        yield
        self.inputs = {"a": 2 ** 32 - 1, "b": 2 ** 32 - 1}
        yield
        for i in xrange(self.COUNT):
            la = lb = rand.randint(1, self.MAXBITLEN)

            self.params = {'la': la, 'lb': lb}
            self.inputs = {
                'a': rand.randint(1, (2 ** la) - 1),
                'b': rand.randint(1, (2 ** lb) - 1)}
            yield

    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            self.assertEqual(self.client_inputs['a'] * self.client_inputs['b'], int(self.client_outputs['c']),
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

class MulVecTest(test_utils.TastyRemoteCTRL):

    MAXBITLEN = 256
    MAXDIM = 128
    COUNT = 3

    def next_data_in(self):
        for i in xrange(self.COUNT):
            da = rand.randint(1, self.MAXDIM)
            db = rand.randint(1, self.MAXDIM)
            la = rand.randint(1, self.MAXBITLEN)
            lb = rand.randint(1, self.MAXBITLEN)

            self.params = {'la': la, 'lb': lb, 'da': da, 'db': db}
            self.inputs = {'a': tuple(get_random(1, (2 ** la) - 1, da)),
                        'b': rand.randint(1, (2 ** lb) - 1)}
            yield

    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            a = self.client_inputs["a"]
            y = self.client_inputs["b"]
            c = self.client_outputs["c"]
            la = self.params['la']
            lb = self.params['lb']
            lc = la + lb
            self.assertFalse(c.signed())
            self.assertEqual(c.bit_length(), lc)
            for x, z in izip(a, c):
                self.assertEqual(x * y, int(z),
                    msg="a[i] = %d, b[i] = %d. c[i] is %d, should be %d" %
                        (x, y, int(z), int(x * y)))
                self.assertEqual(z.bit_length(), lc,
                    msg = "bitlength = %d, should be %d" %
                        (z.bit_length(), max((la, lb)) + 1))
                self.assertFalse(z.signed())
                try:
                    z.validate()
                except Exception, e:
                    self.fail("Validation failed: %s"%e)
            yield

class SignedMulVecTest(test_utils.TastyRemoteCTRL):

    MAXDIM=128
    MAXBITLEN=256
    COUNT = 5

    def next_data_in(self):
        self.params = {"la": 32, "lb": 32, "da" : 8, "db" : 8}
        self.inputs = {"a": 8 * (0,), "b": rand.randint(1, 2 ** 31 - 1)}
        yield
        self.inputs = {"b": 0, "a":  nogen(get_random(1, 2 ** 31 - 1, 8))}
        yield
        self.inputs = {"a": 8 * (0,), "b": 0}
        yield
        self.inputs = {"a": 8 * (2 ** 31 - 1,), "b": 2 ** 31 - 1}
        yield
        for i in xrange(self.COUNT):
            da = rand.randint(1, self.MAXDIM)
            db = rand.randint(1, self.MAXDIM)
            la = rand.randint(2, self.MAXBITLEN)
            lb = rand.randint(2, self.MAXBITLEN)
            self.params = {'la': la, 'lb': lb, 'da': da, 'db': db}
            self.inputs = {'a': tuple(get_random(1, max(1, (2 ** (la - 1)) - 1), da)),
                        'b': rand.randint(1, max(1, (2 ** (lb - 1)) - 1))}
            yield

    def next_data_out(self):
        while True:
            self.client_inputs.update(self.server_inputs) #merge inputs together
            self.client_outputs.update(self.server_outputs) # merge outputs together
            a = self.client_inputs["a"]
            y = self.client_inputs["b"]
            c = self.client_outputs["c"]
            la = self.params['la']
            lb = self.params['lb']
            lc = la + lb
            self.assertTrue(c.signed())
            self.assertEqual(c.bit_length(), lc)
            for x, z in izip(a, c):
                self.assertEqual(x * y, int(z),
                    msg="a[i] = %d, b[i] = %d. c[i] is %d, should be %d" %
                        (x, y, int(z), int(x * y)))
                self.assertEqual(z.bit_length(), lc,
                    msg = "bitlength = %d, should be %d" %
                        (z.bit_length(), la + lb))
                self.assertTrue(z.signed())
                try:
                    z.validate()
                except Exception, e:
                    self.fail("Validation failed: %s"%e)
            yield


class UnsignedMulTestCase(MulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsigned")

class SignedMulTestCase(SignedMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signed")

class HomomorphicUnsignedMulTestCase(MulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/homomorphic_unsigned")

class UnsignedHomomorphicMulTestCase(MulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsigned_homomorphic")

class HomomorphicMulTestCase(MulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/homomorphic")

class HomomorphicMulClientClientClientTestCase(MulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/homomorphic_client_client_client")

class GarbledMulClientClientClientTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_client_client_client")

class GarbledMulClientServerClientTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_client_server_client")

class GarbledMulServerServerClientTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_server_server_client")

class GarbledMulServerServerServerTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_server_server_server")

class GarbledMulClientServerServerTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_client_server_server")

class GarbledMulClientClientServerTestCase(GarbledMulTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/garbled_client_client_server")

class UnsignedVecMulClientClientClientTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_client_client_client")

class UnsignedVecMulClientClientServerTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_client_client_server")

class UnsignedVecMulClientServerClientTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_client_server_client")

class UnsignedVecMulClientServerServerTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_client_server_server")

class UnsignedVecMulServerClientClientTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_server_client_client")

class UnsignedVecMulServerClientServerTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_server_client_server")

class UnsignedVecMulServerServerClientTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_server_server_client")

class UnsignedVecMulServerServerServerTestCase(MulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/unsignedvec_server_server_server")

class SignedVecMulClientClientClientTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_client_client_client")

class SignedVecMulClientClientServerTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_client_client_server")

class SignedVecMulClientServerClientTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_client_server_client")

class SignedVecMulClientServerServerTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_client_server_server")

class SignedVecMulServerClientClientTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_server_client_client")

class SignedVecMulServerClientServerTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_server_client_server")

class SignedVecMulServerServerClientTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_server_server_client")

class SignedVecMulServerServerServerTestCase(SignedMulVecTest):
    def protocol_dir(self):
        return tasty_path("tests/functional/protocols/mul/signedvec_server_server_server")


def suite():
    """narf"""

    tests = unittest.TestSuite()
    #tests.addTest(UnsignedMulTestCase())
    #tests.addTest(SignedMulTestCase())

    #tests.addTest(UnsignedVecMulClientClientClientTestCase())
    #tests.addTest(UnsignedVecMulClientClientServerTestCase())
    #tests.addTest(UnsignedVecMulClientServerClientTestCase())
    #tests.addTest(UnsignedVecMulClientServerServerTestCase())
    #tests.addTest(UnsignedVecMulServerClientClientTestCase())
    #tests.addTest(UnsignedVecMulServerClientServerTestCase())
    #tests.addTest(UnsignedVecMulServerServerClientTestCase())
    #tests.addTest(UnsignedVecMulServerServerServerTestCase())

    #tests.addTest(SignedVecMulClientClientClientTestCase())
    #tests.addTest(SignedVecMulClientClientServerTestCase())
    #tests.addTest(SignedVecMulClientServerClientTestCase())
    #tests.addTest(SignedVecMulClientServerServerTestCase())
    #tests.addTest(SignedVecMulServerClientClientTestCase())
    #tests.addTest(SignedVecMulServerClientServerTestCase())
    #tests.addTest(SignedVecMulServerServerClientTestCase())
    #tests.addTest(SignedVecMulServerServerServerTestCase())

    #tests.addTest(HomomorphicUnsignedMulTestCase())
    #tests.addTest(UnsignedHomomorphicMulTestCase())

    #tests.addTest(HomomorphicMulTestCase())
    tests.addTest(HomomorphicMulClientClientClientTestCase())

    tests.addTest(GarbledMulClientClientClientTestCase())
    tests.addTest(GarbledMulClientServerClientTestCase())
    tests.addTest(GarbledMulServerServerClientTestCase())
    tests.addTest(GarbledMulClientClientServerTestCase())
    tests.addTest(GarbledMulClientServerServerTestCase())
    tests.addTest(GarbledMulServerServerServerTestCase())

    return tests


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

