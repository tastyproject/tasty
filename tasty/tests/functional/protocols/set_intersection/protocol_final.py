from tasty.types.driver import TestDriver
from tasty.crypt.math import getPolyCoefficients, evalPoly
__params__ = {'SETSIZE_C': 10, 'SETSIZE_S': 10}
driver = TestDriver()

def protocol(c, s, params):
    M = params['SETSIZE_C']
    N = params['SETSIZE_S']
    c.X = ModularVec(dim=M).input(src=driver, desc='X')
    s.Y = ModularVec(dim=N).input(src=driver, desc='Y')
    c.a = getPolyCoefficients()(c.X)
    c.ha = HomomorphicVec(val=c.a)
    s.ha <<= c.ha
    s.hbarY = HomomorphicVec(bitlen=1776, dim=N)

    for i in xrange(N):
        s.p = s.ha[M]

        for j in xrange(M - 1, -1, -1):
            s.p = s.p * s.Y[i] + s.ha[j]

        s.hbarY[i] = s.p * Modular().rand() + Homomorphic(val=s.Y[i])

    c.hbarY <<= s.hbarY
    c.barY = ModularVec(val=c.hbarY)

    for e in xrange(M):

        if c.X[e] in c.barY:
            c.output(c.X[e], dest=driver, desc='X%d' % e)
