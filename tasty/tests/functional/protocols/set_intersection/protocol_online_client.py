from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
from tasty.crypt.math import getPolyCoefficients, evalPoly
__params__ = {'SETSIZE_C': 10, 'SETSIZE_S': 10}
driver = TestDriver()

def protocol(c, s, params):
    c.X = ModularVec(dim=34, empty=True, signed=False, bitlen=1776).input(src=driver, desc='X')
    c.a = getPolyCoefficients()(c.X)
    c.ha = HomomorphicVec(val=c.a, signed=False, bitlen=1776, dim=[35])
    conversions.PaillierVec_PaillierVec_send(c.ha, s.ha, 1776, [35], False)
    s.hbarY = HomomorphicVec(bitlen=1776, dim=20, signed=False, passive=True)
    conversions.PaillierVec_PaillierVec_receive(s.hbarY, c.hbarY, 1776, [20], False)
    c.barY = ModularVec(val=c.hbarY, signed=False, bitlen=1776, dim=[20])

    for e in xrange(34):

        if c.X[e] in c.barY:
            c.output(c.X[e], dest=driver, desc='X%d' % e)
