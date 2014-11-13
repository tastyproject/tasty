# -*- coding: utf-8 -*-
import unittest
from tasty.crypt.garbled_circuit import *
from tasty.circuit.dynamic import *
from tasty.circuit import *
from tasty import utils
from tasty import config, state
from tasty.protocols.otprotocols import PaillierOT
from itertools import product #cartesian product



class GarbledCircuitTestCase(unittest.TestCase):
    """ test  case addition circuit... """

    def setUp(self):
        state.config = config.create_configuration(host="::1", port=8000, symmetric_security_parameter=80, asymmetric_security_parameter=1024, testing=True, protocol_dir=".")
        state.config.ot_chain = [PaillierOT]
        state.R = generate_R()

    def test_R(self):
        self.assertEqual(state.R & 1 , 1)

    def test_garbled_primitives(self):
        for i in xrange(1,32):
            v = tuple(utils.get_random(0,1,i))
            gzv = tuple(generate_garbled_value(i))
            gv = tuple(plain2garbled(v, gzv, state.R))
            nv = tuple(garbled2plain(gv, gzv, state.R))
            self.assertEqual(v, nv)

    def test_garbledcircuit_1bitand(self):
        c = GateCircuit(2,((0,0,0,1),))
        for comb in product((0,1), repeat=2):
            ### Generate Inputs
            gzv = tuple(tuple(generate_garbled_value(1)) for i in (1,1))
            gv = tuple(plain2garbled((comb[0], ), gzv[0], state.R))
            gv2 = tuple(plain2garbled((comb[1], ), gzv[1], state.R))

            ### Generate and evaluate Circuit
            sgc = CreatorGarbledCircuit(c, state.R, gzv)
            egc = EvaluatorGarbledCircuit(c, sgc.next_garbled_gate(), gv, gv2)

            ### evaluate G
            outputs = map(tuple, egc.eval())
            c_outputs = map(tuple, sgc.results())

            ### get outputs
            out = tuple(perm2plain(outputs[0], c_outputs[0]))

            self.assertEqual(out[0],comb[0] & comb[1])

    def test_garbledcircuit_add(self):
        """ Test wether the addition cirucit works """
        for l_x in xrange(1, 6):
            for l_y in xrange(1, l_x + 1):
                c = AddCircuit(l_x, l_y, UNSIGNED, UNSIGNED)
                c.check()
                for val in product(xrange(1<<l_x), xrange(1<<l_y)):
                    null_inputs = [tuple(generate_garbled_value(l)) for l in (l_x, l_y)]
                    bval = (value2bits(mpz(val[0]), l_x), value2bits(mpz(val[1]), l_y),)
                    inputs = [tuple(plain2garbled(y, x, state.R)) for x, y in zip(null_inputs, bval)]
                    sgc = CreatorGarbledCircuit(c, state.R, null_inputs)

                    egc = EvaluatorGarbledCircuit(c, sgc.next_garbled_gate(), inputs)
                    outputs = map(tuple, egc.eval())
                    sgcres = sgc.results()
                    sgcr = tuple(sgcres.next())
                    sgcres = map(lambda x: x & 1, sgcr)
                    out = tuple(perm2plain(outputs[0], sgcres))
                    tuple(garbled2plain(outputs[0], sgcr, state.R)) # make sure that this are correct results
                    self.assertEqual(sum(val),bits2value(out))

    def test_garbledcircuit_bruteforce(self):
        """ IMPLEMENT THIS: Brute-force test GC with d-input gates """
        #TODO: implement brute force test: for d in (0,1,2,3,4): forall possible gate tables: forall possible inputs: assert c.eval == gc.eval
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(GarbledCircuitTestCase("test_R"))
    suite.addTest(GarbledCircuitTestCase("test_garbled_primitives"))
#    suite.addTest(GarbledCircuitTestCase("test_garbledcircuit_1bitand"))
    suite.addTest(GarbledCircuitTestCase("test_garbledcircuit_add"))
    suite.addTest(GarbledCircuitTestCase("test_garbledcircuit_bruteforce"))

    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

