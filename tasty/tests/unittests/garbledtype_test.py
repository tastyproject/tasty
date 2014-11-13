# -*- coding: utf-8 -*-
from tasty.types import *
from tasty.types import Party
import unittest
from tasty import state,config
from tasty.crypt.garbled_circuit import generate_R

class GarbledTestCase(unittest.TestCase):
    def test_garbledconversions(self):
        """ simple server plain -> garbled -> plain test """
        state.config = config.create_configuration(host="::1", port=8000, symmetric_security_parameter=80, asymetric_security_parameter=1024, protocol_dir="docs/millionaires_problem/")
        state.role = Party.SERVER
        state.R = generate_R()
        state.precompute = True
        p = state.active_party = Party(role=Party.SERVER, sock=None)
        p.gx = Garbled(bitlen=32, val=0)
        state.precompute = False
        val = 132421
        p.x = Unsigned(length=32, val=val)
        p.gx = Garbled(length=32, val=p.x)
        p.rx = Unsigned(length=32, val=p.gx)

        self.assertEqual(p.x, p.rx)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(GarbledTestCase("test_garbledconversions"))
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())


