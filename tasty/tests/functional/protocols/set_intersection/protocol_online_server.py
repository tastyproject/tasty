from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
from tasty.crypt.math import getPolyCoefficients, evalPoly
__params__ = {'SETSIZE_C': 10, 'SETSIZE_S': 10}
driver = TestDriver()

def protocol(c, s, params):
    s.Y = ModularVec(dim=20, empty=True, signed=False, bitlen=1776).input(src=driver, desc='Y')
    conversions.PaillierVec_PaillierVec_receive(c.ha, s.ha, 1776, [35], False)
    s.hbarY = HomomorphicVec(bitlen=1776, dim=20, signed=False)

    for i in xrange(20):
        s.p = s.ha[34]

        for j in xrange(33, -1, -1):
            s.p = s.p * s.Y[i] + s.ha[j]

        s.hbarY[i] = s.p * Modular(signed=False, bitlen=1776, dim=[1]).rand() + Homomorphic(val=s.Y[i], signed=False, bitlen=1776, dim=[1])

    conversions.PaillierVec_PaillierVec_send(s.hbarY, c.hbarY, 1776, [20], False)
