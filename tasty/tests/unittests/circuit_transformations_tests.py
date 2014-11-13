# -*- coding: utf-8 -*-

import unittest
import os.path
from tasty.circuit import Circuit, int2comp2, comp22int

import time

from tasty.circuit.dynamic import *
from tasty.circuit.transformations import *
from tasty.circuit.reader import PSSW09Circuit

from tasty import state

from itertools import product

class CircuitTestCase(unittest.TestCase):

    def test_replace_3_by_2(self):
        '''testing replace_3_by_2'''
        
        # Test replacement of single gate
        for len in (0,1,2,3):
            for tab in product(range(2), repeat=1<<len):
                c = GateCircuit(len, (tab,))
                c.check()
                d = replace_3_by_2(c)
                d.check()
                for vals in product(range(2), repeat=len):
                    c_val = c.eval(vals)
                    d_val = d.eval(vals)
                    self.assertEqual(c_val[0],d_val[0])

        # Brute-force replacement of small circuit
        x_l = 4
        y_l = 4
        c = FastMultiplicationCircuit(x_l, y_l)
        c.check()
        d = replace_3_by_2(c)
        d.check()
        for vals in product(xrange(1 << x_l), xrange(1 << y_l)):
            self.assertEqual(d.eval(vals)[0], c.eval(vals)[0])

        # Test large circuit
        x_l = 20
        y_l = 20
        c = FastMultiplicationCircuit(x_l, y_l)
        c.check()
        d = replace_3_by_2(c)
        d.check()
        for vals in ((0xAB, 0xCD), (1,0xEF)):
            self.assertEqual(d.eval(vals)[0], c.eval(vals)[0])

    def test_replace_xnor_with_xor(self):
        '''testing replace_xnor_with_xor'''

        # Single XNOR gate
        c = GateCircuit(2,[[1,0,0,1]])
        d = replace_xnor_with_xor(c)
        for vals in product(range(2), repeat=2):
            c_val = c.eval(vals)
            d_val = d.eval(vals)
            self.assertEqual(c_val[0],d_val[0])
        
        # AES circuit contains several XNOR gates
        c = PSSW09Circuit(os.path.join(state.tasty_root, "circuit/circuits/PSSW09_PracticalSFE/AES_PSSW09.txt"))
        d = replace_xnor_with_xor(c)
        k = 0xfffffffffffffffffffffffffffffff0
        m = 0xffffffffffffffffffffffffffffffff
        c_res = c.eval((k,m))[0]
        d_res = d.eval((k,m))[0]
        self.assertEqual(c_res, d_res)

    def test_circuit_buffer_RAM(self):
        '''testing circuit_buffer_RAM'''
        c = PSSW09Circuit(os.path.join(state.tasty_root, "circuit/circuits/PSSW09_PracticalSFE/AES_PSSW09.txt"))
        d = circuit_buffer_RAM(c)
        d.check()
        k = 0xfffffffffffffffffffffffffffffff0
        m = 0xffffffffffffffffffffffffffffffff
        c_res = c.eval((k,m))[0]
        d_res = d.eval((k,m))[0]
        self.assertEqual(c_res, d_res)
        
        print 

        # compare performance for AES file circuit
        repetitions = 2
        start_time = time.clock()
        for i in xrange(repetitions):
            c_res = c.eval((k,m))[0]
        mid_time = time.clock()
        for i in xrange(repetitions):
            d_res = d.eval((k,m))[0]
        stop_time = time.clock()        
        c_time = mid_time - start_time
        d_time = stop_time - mid_time
        improvement = c_time / d_time
        print "Improvement for AES File-Circuit: %f x" % improvement

        # compare performance for Multiplication circuit
        bitlen = 256
        repetitions = 2
        c = FastMultiplicationCircuit(bitlen,bitlen)
        d = circuit_buffer_RAM(c)
        start_time = time.clock()
        for i in xrange(repetitions):
            c_res = c.eval((0,0))[0]
        mid_time = time.clock()
        for i in xrange(repetitions):
            d_res = d.eval((0,0))[0]
        stop_time = time.clock()        
        c_time = mid_time - start_time
        d_time = stop_time - mid_time
        improvement = c_time / d_time
        print "Improvement for FastMultiplication(%d,%d) Circuit: %f x" % (bitlen,bitlen,improvement)

        
        
def suite():
    suite = unittest.TestSuite()
    suite.addTest(CircuitTestCase("test_replace_3_by_2"))
    suite.addTest(CircuitTestCase("test_replace_xnor_with_xor"))
    suite.addTest(CircuitTestCase("test_circuit_buffer_RAM"))

    return suite

if __name__ == '__main__':
    import tasty.utils
    import logging

    state.log.setLevel(logging.ERROR)
    unittest.TextTestRunner(verbosity=2).run(suite())
