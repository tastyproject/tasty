# -*- coding: utf-8 -*-

import unittest
from gmpy import mpz

from tasty.circuit import Circuit, SIGNED, UNSIGNED, DROP_MSB, NODROP_MSB
from tasty.utils import int2comp2, comp22int, rand

from tasty.circuit.dynamic import *
from itertools import product

from tasty import state

class CircuitTestCase(unittest.TestCase):

    def test_Bool2Circuit(self):
        """testing Bool2Circuit"""
        self.failUnlessRaises(ValueError, Bool2Circuit, 0, 0)

        # test AND
        for bitlen in (1,2,3,4):
            c = Bool2Circuit(bitlen, Bool2Circuit.AND)
            c.check()
            for x, y in product(xrange(1 << bitlen), xrange(1 << bitlen)):
                self.assertEqual(c.eval((x, y))[0], x&y)

        # test OR
        for bitlen in (1,2,3,4):
            c = Bool2Circuit(bitlen, Bool2Circuit.OR)
            c.check()
            for x, y in product(xrange(1 << bitlen), xrange(1 << bitlen)):
                self.assertEqual(c.eval((x, y))[0], x | y)

        # test XOR
        for bitlen in (1,2,3,4):
            c = Bool2Circuit(bitlen, Bool2Circuit.XOR)
            c.check()
            for x, y in product(xrange(1 << bitlen), xrange(1 << bitlen)):
                self.assertEqual(c.eval((x, y))[0], x ^ y)


    def test_SubCircuit(self):
        """testing SubCircuit"""
        self.failUnlessRaises(NotImplementedError, SubCircuit, 2, 3, UNSIGNED, NODROP_MSB)
        self.failUnlessRaises(ValueError, SubCircuit, 0, 0, UNSIGNED)
        self.failUnlessRaises(ValueError, SubCircuit, 2, 2, "foo", NODROP_MSB)
        self.failUnlessRaises(ValueError, SubCircuit, 2, 2, UNSIGNED, "foo")

        # test unsigned y
        for l_x in (1,2,3,4):
            for l_y in xrange(1, l_x + 1):
                #print "l_x:", l_x, " l_y:", l_y
                c = SubCircuit(l_x, l_y, UNSIGNED)
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    z = c.eval((x, y))[0]
                    #print x,y,comp22int(z,l_x+1),bin(z)
                    self.assertEqual(z, int2comp2(x-y,l_x+1))

        # test signed y
        for l_x in (1,2,3,4):
            for l_y in xrange(1, l_x + 1):
                c = SubCircuit(l_x, l_y, SIGNED)
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    res = c.eval((x, y))[0]
                    vy = comp22int(mpz(y),l_y)
                    self.assertEqual(res, int2comp2(mpz(x - vy),l_x+1))

        # test unsigned y + DROP_MSB
        for l_x in (1,2,3,4,5,6):
            for l_y in xrange(1, l_x+1):
                c = SubCircuit(l_x, l_y, UNSIGNED, DROP_MSB)
                o_len = c.num_output_bits()
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    if x >= y:
                        c_res= c.eval((x, y))[0]
                        res = int2comp2(mpz(x-y),o_len)
                        self.assertEqual(c_res, res)

    def test_AddCircuit(self):
        """testing AddCircuit"""
        self.failUnlessRaises(NotImplementedError, AddCircuit, 2, 3, UNSIGNED, UNSIGNED)
        self.failUnlessRaises(ValueError, AddCircuit, 0, 0, UNSIGNED, UNSIGNED)
        self.failUnlessRaises(ValueError, AddCircuit, 2, 2, "foo", UNSIGNED)

        # test unsigned y
        for l_x in (1,2,3,4):
            for l_y in xrange(1, l_x + 1):
                c = AddCircuit(l_x, l_y, UNSIGNED, UNSIGNED)
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    self.assertEqual(c.eval((x, y))[0], x+y)

        # test unsigned y
        for l_x in (1,2,3,4):
            for l_y in xrange(1, l_x + 1):
                c = AddCircuit(l_x, l_y, UNSIGNED, SIGNED)
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    res = c.eval((x, y))[0]
                    vy = comp22int(mpz(y),l_y)
                    self.assertEqual(res, int2comp2(mpz(x + vy),l_x+1))

        # test unsigned y + DROP_MSB
        for l_x in (1,2,3,4,5,6):
            for l_y in xrange(1, l_x+1):
                c = AddCircuit(l_x, l_y, UNSIGNED, UNSIGNED, DROP_MSB)
                o_len = c.num_output_bits()
                c.check()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    if x + y < (1<<o_len):
                        c_res= c.eval((x, y))[0]
                        res = int2comp2(x+y,o_len)
                        self.assertEqual(c_res, res)

    def test_CmpCircuit(self):
        '''testing CmpCircuit'''

        types = (CmpCircuit.LESS, CmpCircuit.LESSEQUAL, CmpCircuit.GREATER, CmpCircuit.GREATEREQUAL, CmpCircuit.EQUAL, CmpCircuit.NOTEQUAL)

        self.failUnlessRaises(ValueError, CmpCircuit, 2, 2, "foo")

        for type_ in types:
            self.failUnlessRaises(NotImplementedError, CmpCircuit, 2, 3, type_)
            self.failUnlessRaises(ValueError, CmpCircuit, 0, 0, type_)


            for lx in xrange(1,6):
                for ly in xrange(1, lx + 1):
                    c = CmpCircuit(lx, ly, type_)
                    c.check()
                    for x, y in product(xrange(1 << lx), xrange(1 << ly)):
                        v = c.eval((x, y))[0]

                        if type_ == CmpCircuit.LESS:
                            ref = int(x<y)
                        elif type_ == CmpCircuit.LESSEQUAL:
                            ref = int(x<=y)
                        elif type_ == CmpCircuit.GREATER:
                            ref = int(x>y)
                        elif type_ == CmpCircuit.GREATEREQUAL:
                            ref = int(x>=y)
                        elif type_ == CmpCircuit.EQUAL:
                            ref = int(x==y)
                        elif type_ == CmpCircuit.NOTEQUAL:
                            ref = int(x!=y)

                        self.assertEqual(v, ref)


    def test_MultiplicationCircuit(self):
        '''testing MultiplicationCircuit'''
        self.failUnlessRaises(NotImplementedError, MultiplicationCircuit, 2, 3)
        self.failUnlessRaises(ValueError, MultiplicationCircuit, 0, 0)

        for l_x,l_y in ((1, 1), (2, 1), (3, 1), (2, 2), (3, 2), (4, 2), (3, 3), (4, 3), (5, 3), (5,4), (5, 5)):
            c = MultiplicationCircuit(l_x, l_y)
            c.check()
            for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                self.assertEqual(c.eval((x, y))[0], x*y)

    def test_FastMultiplicationCircuit(self):
        '''testing FastMultiplicationCircuit'''
        self.failUnlessRaises(NotImplementedError, FastMultiplicationCircuit, 2, 3)
        self.failUnlessRaises(ValueError, FastMultiplicationCircuit, 0, 0)

        for l_x,l_y in ((5,4), (5,5)):
            c = FastMultiplicationCircuit(l_x, l_y)
            c.check()
            for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                self.assertEqual(c.eval((x, y))[0], x*y)

        for l_x, l_y in ((10,10), (50,50), (100,100)):
            c = FastMultiplicationCircuit(l_x, l_y)
            c.check()
            for x, y in ((1<<l_x-1, 1<<l_y-1), (0,0), (1,1), (0,1)):
                c_res = c.eval((x,y))[0]
                res = x*y
                self.assertEqual(c_res, res)

    def test_MuxCircuit(self):
        '''testing MuxCircuit'''
        self.failUnlessRaises(ValueError, MuxCircuit, -1)
        self.failUnlessRaises(ValueError, MuxCircuit, 0)

        for l in (1, 2, 3):
            c = MuxCircuit(l)
            c.check()
            for x, y in product(xrange(1 << l), repeat=2):
                self.assertEqual(c.eval((x, y, 0))[0], x)
                self.assertEqual(c.eval((x, y, 1))[0], y)

    def test_AddSubCircuit(self):
        '''testing AddSubCircuit'''
        self.failUnlessRaises(ValueError, AddSubCircuit, -1, -1)
        self.failUnlessRaises(ValueError, AddSubCircuit, 0, 0)
        for l_x in (1, 2, 3, 4, 5):
            for l_y in xrange(1,l_x+1):
                # SIGNED / UNSIGNED
                c = AddSubCircuit(l_x,l_y,SIGNED,UNSIGNED)
                c.check()
                o_len = c.num_output_bits()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    c_res = c.eval((x, y, 0))[0]
                    #print "%d,%d: %d + %d = %d (%d)" % (l_x,l_y,x,y,comp22int(c_res,o_len),x+y)
                    self.assertEqual(c_res, int2comp2(comp22int(mpz(x),l_x) + y, o_len))
                    c_res = c.eval((x, y, 1))[0]
                    #print "%d,%d: %d - %d = %d (%d)" % (l_x,l_y,x,y,comp22int(c_res,o_len),x-y)
                    self.assertEqual(c_res, int2comp2(comp22int(mpz(x),l_x) - y, o_len))

                # UNSIGNED / UNSIGNED
                c = AddSubCircuit(l_x,l_y,UNSIGNED,UNSIGNED)
                c.check()
                o_len = c.num_output_bits()
                for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                    c_res = c.eval((x, y, 0))[0]
                    #print "%d,%d: %d + %d = %d (%d)" % (l_x,l_y,x,y,comp22int(c_res,o_len),x+y)
                    self.assertEqual(c_res, int2comp2(mpz(x + y), o_len))
                    c_res = c.eval((x, y, 1))[0]
                    #print "%d,%d: %d - %d = %d (%d)" % (l_x,l_y,x,y,comp22int(c_res,o_len),x-y)
                    self.assertEqual(c_res, int2comp2(mpz(x - y), o_len))


    def test_AddSub0Circuit(self):
        '''testing AddSub0Circuit'''
        self.failUnlessRaises(ValueError, AddSub0Circuit, -1,)
        self.failUnlessRaises(ValueError, AddSub0Circuit, 0)
        for l in (1, 2, 3, 4):
            c = AddSub0Circuit(l)
            c.check()
            o_len = c.num_output_bits()
            for x in xrange(1 << l):
                self.assertEqual(c.eval((x, 0))[0], 0 + x)
                self.assertEqual(c.eval((x, 1))[0], int2comp2(0 - x, o_len))

    def test_MinMaxCircuits(self):
        '''testing MinMaxCircuits'''
        circuits = (MinMaxValueCircuit, MinMaxIndexCircuit, MinMaxValueIndexCircuit)

        for circ in circuits:
            self.failUnlessRaises(ValueError, circ, -1, 1, circ.MIN)
            self.failUnlessRaises(ValueError, circ, 0, 1, circ.MIN)
            self.failUnlessRaises(ValueError, circ, 1, 1, circ.MIN)
            self.failUnlessRaises(ValueError, circ, 2, -1, circ.MIN)
            self.failUnlessRaises(ValueError, circ, 2, 0, circ.MIN)
            self.failUnlessRaises(ValueError, circ, 2, 1, "foo")
            for n in (2,3,4):
                for l in (1,2):
                    c_max = circ(n,l,circ.MAX)
                    c_max.check()
                    c_min = circ(n,l,circ.MIN)
                    c_min.check()
                    possibilities = 1<<(l * n)
                    l_mask = (1<<l) - 1
                    for p in xrange(possibilities):
                        vals = []
                        for i in xrange(n):
                            vi = (p & (l_mask << (i * l))) >> (i*l)
                            vals.append(vi)

                        # MAX
                        max_v = vals[0]
                        max_ix = 0
                        for i in xrange(1,n):
                            if vals[i] > max_v:
                                max_v = vals[i]
                                max_ix = i

                        # MIN
                        min_v = vals[0]
                        min_ix = 0
                        for i in xrange(1,n):
                            if vals[i] < min_v:
                                min_v = vals[i]
                                min_ix = i

                        if circ == MinMaxValueCircuit:
                            v_max, = c_max.eval(vals)
                            self.assertEqual(v_max, max_v)
                            v_min, = c_min.eval(vals)
                            self.assertEqual(v_min, min_v)
                        elif circ == MinMaxIndexCircuit:
                            ix_max, = c_max.eval(vals)
                            self.assertEqual(ix_max, max_ix)
                            ix_min, = c_min.eval(vals)
                            self.assertEqual(ix_min, min_ix)
                        elif circ == MinMaxValueIndexCircuit:
                            v_max, ix_max = c_max.eval(vals)
                            self.assertEqual(v_max, max_v)
                            self.assertEqual(ix_max, max_ix)
                            v_min, ix_min = c_min.eval(vals)
                            self.assertEqual(v_min, min_v)
                            self.assertEqual(ix_min, min_ix)

    def test_VectorMultiplicationCircuit(self):
        '''testing VectorMultiplicationCircuit'''
        self.failUnlessRaises(ValueError, VectorMultiplicationCircuit, -1, 1)
        self.failUnlessRaises(ValueError, VectorMultiplicationCircuit, 0, 1)
        self.failUnlessRaises(ValueError, VectorMultiplicationCircuit, 1, -1)
        self.failUnlessRaises(ValueError, VectorMultiplicationCircuit, 1, 0)

        # Exhaustive tests
        for n,l in ((1,1), (1,2), (1,3), (2,1), (2,2), (3,1)):
            c = VectorMultiplicationCircuit(n,l)
            c.check()
            o_len = c.num_output_bits()
            possibilities = 1<<(2 * (l+1) * n)
            l_mask = ((1<<l) - 1)<<1
            s_mask = 1
            for p in xrange(possibilities):
                vals = []
                for i in xrange(n):
                    for j in xrange(2):
                        vi = (p & (l_mask << ((2*i+j) * (l+1)))) >> ((2*i+j)*(l+1)+1)
                        si = (p & (s_mask << ((2*i+j) * (l+1)))) >> ((2*i+j)*(l+1))
                        vals.append(si)
                        vals.append(vi)
                res = 0
                for i in xrange(n):
                    s_x_i, m_x_i, s_y_i, m_y_i = vals[4*i:4*(i+1)]
                    if (s_x_i == 0 and s_y_i == 0) or (s_x_i == 1 and s_y_i == 1):
                        res += m_x_i * m_y_i
                    else:
                        res -= m_x_i * m_y_i
                c_res = c.eval(vals)[0]
                self.assertEqual(c_res, int2comp2(res,o_len))

        # Test with maximum values only
        for n in xrange(1,30):
            for l in xrange(1,3):
                c = VectorMultiplicationCircuit(n,l)
                c.check()
                o_len = c.num_output_bits()
                max_v = (1<<l) - 1

                # max positive value
                vals=[]
                for i in xrange(n):
                    vals.append(0)
                    vals.append(max_v)
                    vals.append(0)
                    vals.append(max_v)
                c_res = c.eval(vals)[0]
                res = n*(max_v * max_v)
                self.assertEqual(c_res, int2comp2(res,o_len))

                # max negative value
                vals=[]
                for i in xrange(n):
                    vals.append(1)
                    vals.append(max_v)
                    vals.append(0)
                    vals.append(max_v)
                c_res = c.eval(vals)[0]
                res = -n*(max_v * max_v)
                self.assertEqual(c_res, int2comp2(res,o_len))


    def test_HornerMergeCircuit(self):
        '''testing HornerMergeCircuit'''
        self.failUnlessRaises(ValueError, HornerMergeCircuit, -1, -1, -1)
        self.failUnlessRaises(ValueError, HornerMergeCircuit, 0, 0, 0)
        for l_x, l_y, m in ((3,2,0), (3,2,1), (3,3,1)):
            c = HornerMergeCircuit(l_x,l_y,m)
            c.check()
            for x, y in product(xrange(1 << l_x), xrange(1 << l_y)):
                c_res = c.eval((x, y))[0]
                res = x * 2**m + y
                if res < (1 << c.num_output_bits()):
                    self.assertEqual(c_res, res)

    def test_GateCircuit(self):
        '''testing GateCircuit'''
        self.failUnlessRaises(ValueError, GateCircuit, -1, [[0, 1]])
        self.failUnlessRaises(ValueError, GateCircuit, 1, [[0, 1, 0]])
        self.failUnlessRaises(ValueError, GateCircuit, 0, [[0, 1]])

        # 0-input one-gate
        c = GateCircuit(0,[[1]])
        c.check()
        c_val = c.eval([])
        self.assertEqual(c_val[0], 1)

        # 0-input zero-gate
        c = GateCircuit(0,[[0]])
        c.check()
        c_val = c.eval([])
        self.assertEqual(c_val[0], 0)

        # 0 < d < 10 -input gates
        for d in range(1,10):
            d_p = 1<<d
            tab_and = [0 for i in xrange(d_p)]
            tab_and[-1] = 1
            tab_or = [1 for i in xrange(d_p)]
            tab_or[0] = 0
            c = GateCircuit(d,(tab_and,tab_or))
            c.check()
            for vals in product((True, False), repeat=d):
                c_val = c.eval(vals)
                v_and = reduce(lambda a,b: a and b, vals)
                v_or  = reduce(lambda a,b: a or b, vals)
                self.assertEqual(c_val[0], v_and)
                self.assertEqual(c_val[1], v_or)

    def test_UnpackCircuit(self):
        """ testing UnpackCircuit """


        def pack(values, bitlen, signed):
            """ pack values """
            assert signed == SIGNED or not filter(lambda x: x < 0, values)

            ret = 0
            for val in values:
                if signed == SIGNED:
                    val += (1<<(bitlen - 1))
                ret <<= bitlen
                ret += val
            return ret

        def random(bitlen, signed):
            if signed == SIGNED:
                end = 1<<(bitlen - 1)
                start = -end
            else:
                end = 1 << bitlen
                start = 0
            return rand.randint(start, end)

        def mask(length):
            return random(length + 80, False)

        def test(self, values, bitlen, signed, m = None):
            values = list(values)
            num = len(values)
            totallength = num * bitlen
            tmask = (1<<totallength) - 1

            c = UnpackCircuit(bitlen, num, signed)
            c.check()
            packed = pack(values, bitlen, signed)
            if m is None:
                m = mask(num * bitlen)
            packed += m
            ret = c.eval((packed & tmask, m & tmask))
            if signed == SIGNED:
                f = lambda x: int(comp22int(x, bitlen))
            else:
                f = lambda x: int(x)
            x = [f(i) for i in reversed(ret)]
            self.assertEqual(x, values)

        # TODO: Add tests for impossbile conditions

        # brute force for 1 to 3 bit values and 2 to 4bit signed values
        tests = 10
        for bitlen in xrange(1,4):
            for num in xrange(1,4):
                for values in product(xrange(1<<bitlen), repeat=num):
                    for r in xrange(1<<(bitlen * num)):
                        test(self, values, bitlen, UNSIGNED, r)
                        val = map(lambda x: x - 2**(bitlen - 1), values)
                        test(self, val, bitlen, SIGNED, r)

        # random tests
        for i in xrange(tests):
            num = rand.randint(1, 50)
            bitlen = rand.randint(1,1024)
            signed = rand.sample((SIGNED, UNSIGNED), 1)[0]
            values = [random(bitlen, signed) for i in xrange(num)]
            test(self, values, bitlen, signed)



def suite():
    suite = unittest.TestSuite()
    suite.addTest(CircuitTestCase("test_GateCircuit"))
    suite.addTest(CircuitTestCase("test_AddCircuit"))
    suite.addTest(CircuitTestCase("test_SubCircuit"))
    suite.addTest(CircuitTestCase("test_AddSubCircuit"))
    suite.addTest(CircuitTestCase("test_AddSub0Circuit"))
    suite.addTest(CircuitTestCase("test_CmpCircuit"))
    suite.addTest(CircuitTestCase("test_MultiplicationCircuit"))
    suite.addTest(CircuitTestCase("test_FastMultiplicationCircuit"))
    suite.addTest(CircuitTestCase("test_MuxCircuit"))
    suite.addTest(CircuitTestCase("test_MinMaxCircuits"))
    suite.addTest(CircuitTestCase("test_Bool2Circuit"))
#    suite.addTest(CircuitTestCase("test_VectorMultiplicationCircuit"))
    suite.addTest(CircuitTestCase("test_HornerMergeCircuit"))
    suite.addTest(CircuitTestCase("test_UnpackCircuit"))

    return suite

if __name__ == '__main__':
    import tasty.utils
    import logging

    state.log.setLevel(logging.ERROR)
    unittest.TextTestRunner(verbosity=2).run(suite())
