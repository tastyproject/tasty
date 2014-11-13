# -*- coding: utf-8 -*-

from tasty import state, config
class blah(object):
	pass

state.config = config.create_configuration(
    host="::1",
    port=8000,
    security_level = "short",
    asymmetric_security_parameter = 1024,
    symmetric_security_parameter = 80,
    protocol_dir = "",
)

import unittest
import cPickle
import random
from copy import copy
from gmpy import mpz

from tasty.types import *
from tasty.types.key import generate_keys
from tasty.types import ModularVec
from tasty.types import PaillierVec
from tasty.types import key
from tasty import cost_results
cost_results.CostSystem.create_costs()

class PlainTestCase(unittest.TestCase):

    def test_int(self):
        '''testing Plain.__int__'''

        self.assertEqual(2, int(Signed(bitlen=8, val=2)))

    def test_long(self):
        '''testing Plain.__long__'''

        self.assertEqual(2, long(Signed(bitlen=8, val=2)))

    def test_abs(self):
        '''testing Plain.__abs__'''

        self.assertEqual(Signed(bitlen=8, val=2), abs(Signed(bitlen=8, val=-2)))

    def test_eq(self):
        '''testing Plain.__eq__'''

        a = Signed(bitlen=8, val=2)
        b = Signed(bitlen=8, val=3)
        self.assertEqual(True, a == a)
        self.assertEqual(False, a == b)

    def test_lt(self):
        '''testing Plain.__lt__'''

        a = Signed(bitlen=8, val=2)
        b = Signed(bitlen=8, val=3)
        self.assertEqual(True, a < b)
        self.assertEqual(False, b < a)

    def test_gt(self):
        '''testing Plain.__gt__'''

        a = Signed(bitlen=8, val=2)
        b = Signed(bitlen=8, val=3)
        self.assertEqual(False, a > b)
        self.assertEqual(True, b > a)

    def test_le(self):
        '''testing Plain.__le__'''

        a = Signed(bitlen=8, val=2)
        b = Signed(bitlen=8, val=3)
        self.assertEqual(True, a <= b)
        self.assertEqual(True, a <= a)
        self.assertEqual(True, b <= b)
        self.assertEqual(False, b <= a)

    def test_ge(self):
        '''testing Plain.__ge__'''

        a = Signed(bitlen=8, val=2)
        b = Signed(bitlen=8, val=3)
        self.assertEqual(True, b >= a)
        self.assertEqual(True, b >= b)

        self.assertEqual(True, a >= a)
        self.assertEqual(False, a >= b)



class SignedTestCase(unittest.TestCase):

    def setUp(self):
        self.max = Signed(bitlen=8, val=2**7-1)
        self.min = Signed(bitlen=8, val=-(2**7-1))
        self.zero = Signed(bitlen=8, val=0)

    def test_validation(self):
        '''testing Signed.validate'''
        try:
            self.max.validate()
            self.min.validate()
            self.zero.validate()
        except Exception, e:
            self.fail(e.message)
        tooBig = copy(self.max)
        tooSmall = copy(self.min)
        tooBig._value += 1
        tooSmall._value -= 1
        self.assertRaises(ValueError,tooBig.validate)
        self.assertRaises(ValueError,tooSmall.validate)
        tooBig._value = 42 #no mpz
        self.assertRaises(TypeError,tooBig.validate)


    def test_add(self):
        '''testing Signed.__add__'''

        self.assertEqual(Signed(bitlen=8, val=2) + Signed(bitlen=8, val=3), Signed(bitlen=8, val=5))
        self.assertEqual(Signed(bitlen=8, val=mpz(2)) + Signed(bitlen=8, val=mpz(3)), Signed(bitlen=8, val=mpz(5)))
        x = self.max + Signed(bitlen=8,val=1)
        x.validate() #test if bitlength is still correct
        self.assertEqual(x, Signed(bitlen=9, val=2**7))
        (self.max + self.max).validate()
        (self.max + Unsigned(bitlen=8,val=2**8-1)).validate()

    def test_iadd(self):
        '''testing Signed.__iadd__'''

        tmp = Signed(bitlen=8, val=2)
        tmp += Signed(bitlen=8, val=3)
        self.assertEqual(tmp, Signed(bitlen=8, val=5))


        tmp = Signed(bitlen=8, val=mpz(2))
        tmp += Signed(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Signed(bitlen=8, val=mpz(5)))


    def test_sub(self):
        '''testing Signed.__sub__'''

        self.assertEqual(Signed(bitlen=8, val=2) - Signed(bitlen=8, val=3), Signed(bitlen=8, val=-1))
        self.assertEqual(Signed(bitlen=8, val=mpz(2)) - Signed(bitlen=8, val=mpz(3)), Signed(bitlen=8, val=mpz(-1)))
        s = self.max - (-self.max)
        self.assertEqual(s, self.max+self.max)
        s.validate()
        (self.zero - Unsigned(bitlen=8, val=2**8-1)).validate()

    def test_isub(self):
        '''testing Signed.__isub__'''

        tmp = Signed(bitlen=8, val=5)
        tmp -= Signed(bitlen=8, val=3)
        self.assertEqual(tmp, Signed(bitlen=8, val=2))

        tmp = Signed(bitlen=8, val=mpz(5))
        tmp -= Signed(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Signed(bitlen=8, val=mpz(2)))

    def test_mul(self):
        '''testing Signed.__mul__'''

        self.assertEqual(Signed(bitlen=8, val=2) * Signed(bitlen=8, val=3), Signed(bitlen=8, val=6))
        self.assertEqual(self.zero * self.min, self.zero)
        #does the bitlength grows accordingly
        (self.max * self.max).validate()

    def test_imul(self):
        '''testing Signed.__imul__'''

        tmp = Signed(bitlen=8, val=2)
        tmp *= Signed(bitlen=8, val=3)
        self.assertEqual(tmp, Signed(bitlen=8, val=6))

        tmp = Signed(bitlen=8, val=mpz(2))
        tmp *= Signed(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Signed(bitlen=8, val=mpz(6)))
        tmp = copy(self.max)
        tmp *= self.zero
        self.assertEqual(tmp, self.zero)

    def test_div(self):
        '''testing Signed.__div__'''

        self.assertEqual(Signed(bitlen=8, val=6) / Signed(bitlen=8, val=3), Signed(bitlen=8, val=2))
        self.assertEqual(Signed(bitlen=8, val=mpz(6)) / Signed(bitlen=8, val=mpz(3)), Signed(bitlen=8, val=mpz(2)))


    def test_idiv(self):
        '''testing Signed.__idiv__'''

        tmp = Signed(bitlen=8, val=6)
        tmp /= Signed(bitlen=8, val=3)
        self.assertEqual(tmp, Signed(bitlen=8, val=2))

        tmp = Signed(bitlen=8, val=mpz(6))
        tmp /= Signed(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Signed(bitlen=8, val=mpz(2)))

    def test_serialization(self):
        '''testing Signed serialization'''

        p = Signed(bitlen=8, val=6)
        pstr = cPickle.dumps(p, protocol=2)
        pnew = cPickle.loads(pstr)

        self.assertEqual(p, pnew)

    def test_negation(self):
        '''testing Signed.__neg__'''
        s= Signed(bitlen=8, val=42)
        self.assertEqual(-s, Signed(bitlen=8,val=-42))
        self.assertEqual(-(-s), s)
        self.assertEqual(-self.zero,self.zero)
        s = -self.max
        s.validate()

    def test_rand(self):
        '''testing Signed.rand'''
        s = Signed(bitlen=8).rand()
        try:
            s.validate()
        except ValueError, e:
            self.fail(e.message)


class UnsignedTestCase(unittest.TestCase):

    def setUp(self):
        self.max = Unsigned(bitlen=8, val=2**8-1)
        self.zero = Unsigned(bitlen=8, val=0)
        self.one = Unsigned(bitlen=8, val=1)

    def test_constructor(self):
        '''testing Unsigned.__init__'''
        #go's
        Unsigned(bitlen=8, val=42)
        s = Signed(bitlen=8, val=127)
        Unsigned(bitlen=8, val=s)
        Unsigned(bitlen=8, val=42)
        Unsigned()
        #no go's
        self.assertRaises(TypeError, Unsigned, bitlen=8, val=-1)
        self.assertRaises(ValueError, Unsigned, bitlen=8, val=2**8)
        s = Signed(bitlen=8,val=-1)
        self.assertRaises(TypeError, Unsigned, bitlen=8, val=s)
        s = Signed(bitlen=8, val=127)
        self.assertRaises(ValueError, Unsigned, bitlen=6, val=s)


    def test_validation(self):
        '''testing Unsigned.validate'''

        self.failUnlessRaises(ValueError, Unsigned, bitlen=8, val=1024)
        self.failUnlessRaises(TypeError, Unsigned, bitlen=8, val=-1)
        #no mpz
        x = Unsigned(bitlen=8, val=42)
        x._value = 42
        self.assertRaises(TypeError, x.validate)


    def test_add(self):
        '''testing Unsigned.__add__'''

        self.assertEqual(Unsigned(bitlen=8, val=5) + Unsigned(bitlen=8, val=3), Unsigned(bitlen=8, val=8))
        self.assertEqual(Unsigned(bitlen=8, val=mpz(5)) + Unsigned(bitlen=8, val=mpz(3)), Unsigned(bitlen=8, val=mpz(8)))
        (self.max + Unsigned(bitlen=1,val=1)).validate()
        (self.zero + Signed(val=-42)).validate()


    def test_iadd(self):
        '''testing Unsigned.__iadd__'''

        tmp = Unsigned(bitlen=8, val=2)
        tmp += Unsigned(bitlen=8, val=3)
        self.assertEqual(tmp, Unsigned(bitlen=8, val=5))

        tmp = Unsigned(bitlen=8, val=mpz(2))
        tmp += Unsigned(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Unsigned(bitlen=8, val=mpz(5)))


    def test_sub(self):
        '''testing Unsigned.__sub__'''

        self.assertEqual(Unsigned(bitlen=8, val=2) * Unsigned(bitlen=8, val=3), Unsigned(bitlen=8, val=6))
        self.assertEqual(Unsigned(bitlen=8, val=mpz(2)) * Unsigned(bitlen=8, val=mpz(3)), Unsigned(bitlen=8, val=mpz(6)))
        (Unsigned(val=0)-Unsigned(val=7)).validate()
        (Unsigned(val=0)-Signed(val=7)).validate()


    def test_isub(self):
        '''testing Unsigned.__isub__'''

        tmp = Unsigned(bitlen=8, val=5)
        tmp -= Unsigned(bitlen=8, val=3)
        self.assertEqual(tmp, Unsigned(bitlen=8, val=2))

        tmp = Unsigned(bitlen=8, val=mpz(5))
        tmp -= Unsigned(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Unsigned(bitlen=8, val=mpz(2)))

    def test_mul(self):
        '''testing Unsigned.__mul__'''

        self.assertEqual(Unsigned(bitlen=8, val=2) * Unsigned(bitlen=8, val=3), Unsigned(bitlen=8, val=6))
        x = self.max * Signed(bitlen=2, val=-1)
        x.validate()
        # m * -1 = -m
        self.assertEqual(x, -Signed(bitlen=11, val=self.max))
        r = Unsigned(bitlen=8).rand()
        # r*1 = r
        self.assertEqual(r*self.one, r)
        # r*0 = 0
        self.assertEqual(r*self.zero, self.zero)
        s = Unsigned(bitlen=6).rand()
        # r*s = s*r
        self.assertEqual(r*s, s*r)


    def test_imul(self):
        '''testing Unsigned.__imul__'''

        tmp = Unsigned(bitlen=8, val=2)
        tmp *= Unsigned(bitlen=8, val=3)
        self.assertEqual(tmp, Unsigned(bitlen=8, val=6))
        tmp = Unsigned(bitlen=8, val=mpz(2))
        tmp *= Unsigned(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Unsigned(bitlen=8, val=mpz(6)))
        tmp = copy(self.max)
        tmp *= Signed(bitlen=3, val=-3)
        tmp.validate()
        self.assertEqual(tmp, Signed(bitlen=9, val=self.max)*Signed(bitlen=3, val=-3))


    def test_div(self):
        '''testing Unsigned.__div__'''

        self.assertEqual(Unsigned(bitlen=8, val=6) / Unsigned(bitlen=8, val=3), Unsigned(bitlen=8, val=2))
        self.assertEqual(Unsigned(bitlen=8, val=mpz(6)) / Unsigned(bitlen=8, val=mpz(3)), Unsigned(bitlen=8, val=mpz(2)))
        u = self.max / self.one
        self.assertEqual(u, self.max)
        u.validate() #check bitlen
        u = self.max / Signed(val=-1)
        self.assertEqual(u, -self.max)
        u.validate()

    def test_idiv(self):
        '''testing Unsigned.__idiv__'''

        tmp = Unsigned(bitlen=8, val=6)
        tmp /= Unsigned(bitlen=8, val=3)
        self.assertEqual(tmp, Unsigned(bitlen=8, val=2))

        tmp = Unsigned(bitlen=8, val=mpz(6))
        tmp /= Unsigned(bitlen=8, val=mpz(3))
        self.assertEqual(tmp, Unsigned(bitlen=8, val=mpz(2)))

    def test_negation(self):
        '''testing Unsigned.__neg__'''
        u = Unsigned(bitlen=8).rand()
        self.assertEqual(-u, self.zero-u)
        u = -self.max
        u.validate()

    def test_serialization(self):
        '''testing Unsigned serialization'''

        p = Unsigned(bitlen=8, val=6)
        pstr = cPickle.dumps(p, protocol=2)
        pnew = cPickle.loads(pstr)

        self.assertEqual(p, pnew)

    def test_rand(self):
        '''testing Unsigned.rand'''
        s = Unsigned(bitlen=8).rand()
        try:
            s.validate()
        except ValueError, e:
            self.fail(e.message)

class ModularTestCase(unittest.TestCase):

    def setUp(self):
        '''prepare the test fixture and init needed data'''
        self.p, self.s = generate_keys(1024)
        self.n = state.key._key.n

    def test_validation(self):
        '''testing Modular.validate'''
        p = Modular(val=1)
        p._value = self.n*16
        self.assertRaises(ValueError, p.validate)
        p._value = mpz(-1)
        self.assertRaises(ValueError, p.validate)
        p._value = self.n
        self.assertRaises(ValueError, p.validate)
        p._bit_length = 4
        self.assertRaises(ValueError, p.validate)

    def test_constructor(self):
        ''' testing Modular.__init__'''
        Modular(val=0)
        Modular(val=self.n-1)
        Modular(val=Unsigned(val=42) )
        Modular(val=Signed(val=55))
        Modular(val=mpz(127))
        self.assertRaises(ValueError, Modular, val=Signed(val=-4) )
        self.assertRaises(ValueError, Modular, val=-1)

    def test_add(self):
        '''testing Modular.__add__'''
        self.assertEqual(Modular(val=5) + Modular(val=3), Modular(val=8))
        self.assertEqual(Modular(val=mpz(5)) + Modular(val=mpz(3)), Modular(val=mpz(8)))
        self.assertEqual(Modular(val=self.n-2)+Modular(val=2), Modular(val=0))
        r = Modular().rand()
        # r + n = r mod n
        self.assertEqual(r+Unsigned(bitlen=self.n.bit_length(),val=self.n),r)
        # r + (-n) = r mod n
        self.assertEqual(r+Signed(bitlen=self.n.bit_length()+1, val=-self.n),r)


    def test_iadd(self):
        '''testing Modular.__iadd__'''

        tmp = Modular(val=2)
        tmp += Modular(val=3)
        self.assertEqual(tmp, Modular(val=5))


        tmp = Modular(val=mpz(2))
        tmp += Modular(val=mpz(3))
        self.assertEqual(tmp, Modular(val=mpz(5)))


    def test_sub(self):
        '''testing Modular.__sub__'''

        self.assertEqual(Modular(val=2) * Modular(val=3), Modular(val=6))
        self.assertEqual(Modular(val=mpz(2)) * Modular(val=mpz(3)), Modular(val=mpz(6)))
        self.assertEqual(Modular(val=0)-Unsigned(bitlen=2,val=1), Modular(val=self.n-1) )

    def test_isub(self):
        '''testing Modular.__isub__'''

        tmp = Modular(val=5)
        tmp -= Modular(val=3)
        self.assertEqual(tmp, Modular(val=2))

        tmp = Modular(val=mpz(5))
        tmp -= Modular(val=mpz(3))
        self.assertEqual(tmp, Modular(val=mpz(2)))

    def test_mul(self):
        '''testing Modular.__mul__'''

        self.assertEqual(Modular(val=2) * Modular(val=3), Modular(val=6))

    def test_imul(self):
        '''testing Modular.__imul__'''

        tmp = Modular(val=2)
        tmp *= Modular(val=3)
        self.assertEqual(tmp, Modular(val=6))

        tmp = Modular(val=mpz(2))
        tmp *= Modular(val=mpz(3))
        self.assertEqual(tmp, Modular(val=mpz(6)))

    def test_div(self):
        '''testing Modular.__div__'''
        r = Modular().rand()
        # r/1 = r
        self.assertEqual(r/Modular(val=1), r)
        s = Modular().rand()
        t = r*s
        # t/s = r <> r*s = t mod n
        self.assertEqual(t/s,r)


    def test_idiv(self):
        '''testing Unsigned.__idiv__'''
        r = Modular().rand()
        s = copy(r)
        r /= Modular(val=1)
        self.assertEqual(r,s)


    def test_rand(self):
        '''testing Modular.rand'''
        s = Modular().rand()
        try:
            s.validate()
        except ValueError, e:
            self.fail(e.message)

    def test_serialization(self):
        '''testing Modular serialization'''
        p = Modular(bitlen=8).rand()
        pstr = cPickle.dumps(p, protocol=2)
        pnew = cPickle.loads(pstr)

        self.assertEqual(p, pnew)

class PaillierTestCase(unittest.TestCase):

    def setUp(self):
        '''prepare the test fixture and init needed data'''

        self.msg = Signed(bitlen=8, val=42)
        self.factor = Signed(bitlen=8, val=2)
        self.p, self.s = generate_keys(1024)
        self.c = Homomorphic(val=self.msg)
        self.msg2 = Signed(bitlen=8).rand()
        self.c2 = Homomorphic(val=self.msg2)


    def test_decryption(self):
        '''testing Homomorphic enc/decryption'''
        #Unsigned
        msg = Unsigned(bitlen=32).rand()
        c = Homomorphic(val=msg)
        self.assertEqual(Unsigned(val=c), msg)
        #Signed
        msg = Signed(bitlen=32).rand()
        c = Homomorphic(val=msg)
        self.assertEqual(Signed(val=c), msg)
        msg = Signed(bitlen=8, val=-12)
        c = Homomorphic(val=msg)
        d = Signed(val=c)
        self.assertEqual(Signed(val=c), msg)
        #mpz
        n = state.key._key.n
        msg = mpz(random.randint(0,n-1))
        c = Homomorphic(val=msg)
        self.assertEqual(long(c), msg)
        #Modular
        msg = Modular().rand()
        c = Homomorphic(val=msg)
        self.assertEqual(Modular(val=c),msg)

    def test_addition(self):
        '''testing Homomorphic.__add__'''

        self.assertEqual(Signed(bitlen=None, val=self.c + self.msg), self.msg + self.msg)

    def test_paddition(self):
        '''testing Homomorphic.__add__(Homomorphic other)'''

        self.assertEqual(Signed(bitlen=None, val=self.c + self.c2), self.msg + self.msg2)

    def test_iaddition(self):
        '''testing Homomorphic.__iadd__'''

        self.c += self.msg
        self.assertEqual(Signed(bitlen=None, val=self.c), self.msg + self.msg)

    def test_subtraction(self):
        '''testing Homomorphic.__sub__'''

        self.assertEqual(Signed(bitlen=None, val=self.c - self.msg), self.msg - self.msg)

    def test_psubtraction(self):
        '''testing Homomorphic.__sub__(Homomorphic other)'''

        self.assertEqual(Signed(bitlen=None, val=self.c - self.c2), self.msg - self.msg2)

    def test_isubtraction(self):
        '''testing Homomorphic.__isub__'''

        self.c -= self.msg
        self.assertEqual(Signed(bitlen=None, val=self.c), self.msg - self.msg)

    def test_multiplication(self):
        '''testing Homomorphic.__mul__'''

        self.assertEqual(Signed(bitlen=None, val=self.c * self.factor), self.msg * self.factor)

    def test_imultiplication(self):
        '''testing Homomorphic.__imul__'''

        self.c *= self.factor
        self.assertEqual(Signed(bitlen=None, val=self.c), self.msg * self.factor)

    def test_division(self):
        '''testing Homomorphic.__div__'''

        self.assertEqual(Signed(bitlen=None, val=self.c / self.factor), self.msg / self.factor)

    def test_idivision(self):
        '''testing Homomorphic.__idiv__'''

        self.c /= self.factor
        self.assertEqual(Signed(bitlen=None, val=self.c), self.msg / self.factor)

    def test_negative_values(self):
        '''testing negative values in Homomorphic'''

        a = Signed(bitlen=8, val=-2)
        h = Homomorphic(val=a)
        h_plain = Signed(bitlen=None, val=h)
        self.assertEqual(a, h_plain)

    def test_serialization(self):
        '''testing Homomorphic serialization'''

        pstr = cPickle.dumps(self.p, protocol=2)
        pnew = cPickle.loads(pstr)

        sstr = cPickle.dumps(self.s, protocol=2)
        snew = cPickle.loads(sstr)

        state.key = snew
        c = Homomorphic(val=self.msg)
        cnew = cPickle.loads(cPickle.dumps(c, protocol=2))
        self.assertEqual(Signed(bitlen=None, val=cnew), self.msg)

    def tearDown(self):
        del self.msg
        del self.factor
        del self.p
        del self.s
        del self.c


class PlainVecTestCase(unittest.TestCase):
    def test_constructor(self):
        ''' testing constructor of Vec classes'''
        #go's
        UnsignedVec(bitlen=8, dim=3)
        UnsignedVec(bitlen=8, dim=[3])
        UnsignedVec(bitlen=8, dim=[3,5,3])
        UnsignedVec(bitlen=8, dim=(3,4,5))
        UnsignedVec(val=[mpz(42),mpz(46),mpz(127)])
        v = UnsignedVec(val = [[Unsigned(bitlen=8, val=255),Unsigned(val=127)],[Unsigned(bitlen=7, val=125),Unsigned(val=0)]])
        self.assertEqual(v.bit_length(),8)
        self.assertEqual(v.dim, [2,2])
        s = SignedVec(val=v)
        self.assertEqual(s.bit_length(), v.bit_length()+1)
        self.assertEqual(s.dim, v.dim)
        self.p, self.s = generate_keys(1024)
        ModularVec(val=s)
        #PaillierVec(val=s) Should work, but currently doesn't :-(

        #no go's
        self.assertRaises(ValueError, UnsignedVec)
        self.assertRaises(ValueError, UnsignedVec, bitlen=16)
        #self.assertRaises(ValueError, UnsignedVec, dim=[2,3])
        self.assertRaises(TypeError, UnsignedVec, bitlen=8, dim=2, val=[mpz(255),mpz(256)]) #value too big
        self.assertRaises(ValueError, UnsignedVec, bitlen=8, dim=2, val=[mpz(255),mpz(250),mpz(123)]) #dim of val != dim
        self.assertRaises(TypeError, SignedVec, bitlen=8, dim=2, val=[Unsigned(lenght=8),Unsigned(bitlen=8)]) #bitlen don't match
        self.assertRaises(ValueError, ModularVec, dim=[3,2], val=s)

    def test_serialization(self):
        ''' testing PlainVec serialization'''
        v = SignedVec(bitlen=16, dim=[4,2,5]).rand()
        dv = cPickle.dumps(v,2)
        v2 = cPickle.loads(dv)
        self.assertEqual(v,v2)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(PlainTestCase("test_int"))
    suite.addTest(PlainTestCase("test_long"))
    suite.addTest(PlainTestCase("test_abs"))
    suite.addTest(PlainTestCase("test_eq"))
    suite.addTest(PlainTestCase("test_lt"))
    suite.addTest(PlainTestCase("test_gt"))
    suite.addTest(PlainTestCase("test_le"))
    suite.addTest(PlainTestCase("test_ge"))


    suite.addTest(SignedTestCase("test_validation"))
    suite.addTest(SignedTestCase("test_add"))
    suite.addTest(SignedTestCase("test_iadd"))
    suite.addTest(SignedTestCase("test_sub"))
    suite.addTest(SignedTestCase("test_isub"))
    suite.addTest(SignedTestCase("test_mul"))
    suite.addTest(SignedTestCase("test_imul"))
    suite.addTest(SignedTestCase("test_div"))
    suite.addTest(SignedTestCase("test_idiv"))
    suite.addTest(SignedTestCase("test_serialization"))
    suite.addTest(SignedTestCase("test_negation"))
    suite.addTest(SignedTestCase("test_rand"))

    suite.addTest(UnsignedTestCase("test_validation"))
    suite.addTest(UnsignedTestCase("test_constructor"))
    suite.addTest(UnsignedTestCase("test_add"))
    suite.addTest(UnsignedTestCase("test_iadd"))
    suite.addTest(UnsignedTestCase("test_sub"))
    suite.addTest(UnsignedTestCase("test_isub"))
    suite.addTest(UnsignedTestCase("test_mul"))
    suite.addTest(UnsignedTestCase("test_imul"))
    suite.addTest(UnsignedTestCase("test_div"))
    suite.addTest(UnsignedTestCase("test_idiv"))
    suite.addTest(UnsignedTestCase("test_negation"))
    suite.addTest(UnsignedTestCase("test_serialization"))
    suite.addTest(UnsignedTestCase("test_rand"))

    suite.addTest(ModularTestCase("test_validation"))
    suite.addTest(ModularTestCase("test_constructor"))
    suite.addTest(ModularTestCase("test_add"))
    suite.addTest(ModularTestCase("test_iadd"))
    suite.addTest(ModularTestCase("test_sub"))
    suite.addTest(ModularTestCase("test_isub"))
    suite.addTest(ModularTestCase("test_mul"))
    suite.addTest(ModularTestCase("test_imul"))
    suite.addTest(ModularTestCase("test_div"))
    suite.addTest(ModularTestCase("test_idiv"))
    suite.addTest(ModularTestCase("test_rand"))
    suite.addTest(ModularTestCase("test_serialization"))

    suite.addTest(PaillierTestCase("test_decryption"))
    suite.addTest(PaillierTestCase("test_addition"))
    suite.addTest(PaillierTestCase("test_paddition"))
    suite.addTest(PaillierTestCase("test_iaddition"))
    suite.addTest(PaillierTestCase("test_subtraction"))
    suite.addTest(PaillierTestCase("test_psubtraction"))
    suite.addTest(PaillierTestCase("test_isubtraction"))
    suite.addTest(PaillierTestCase("test_multiplication"))
    suite.addTest(PaillierTestCase("test_imultiplication"))
    suite.addTest(PaillierTestCase("test_division"))
    suite.addTest(PaillierTestCase("test_idivision"))
    suite.addTest(PaillierTestCase("test_serialization"))
    suite.addTest(PaillierTestCase("test_negative_values"))

    suite.addTest(PlainVecTestCase("test_constructor"))
    suite.addTest(PlainVecTestCase("test_serialization"))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

