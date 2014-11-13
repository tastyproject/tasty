from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'K': 12, 'N': 10304, 'M': 42}
driver = TestDriver()

def protocol(c, s, p):
    s.homegabar = HomomorphicVec(dim=12, bitlen=31, signed=True)
    s.hgamma = HomomorphicVec(dim=10304, bitlen=8, signed=False)
    s.hD = HomomorphicVec(dim=42, bitlen=69, signed=True)
    c.gbot = Garbled(val=Unsigned(bitlen=6, dim=[1], signed=False, passive=True, empty=True), passive=True, signed=False, bitlen=6, dim=[1])
    s.omega = UnsignedVec(bitlen=32, dim=(42, 12), empty=True, signed=False).input(src=driver, desc='omega')
    s.psi = UnsignedVec(bitlen=8, dim=10304, empty=True, signed=False).input(src=driver, desc='psi')
    s.u = SignedVec(bitlen=8, dim=(12, 10304), empty=True, signed=True).input(src=driver, desc='u')
    s.tau = Unsigned(bitlen=50, empty=True, signed=False, dim=[1]).input(src=driver, desc='tau')
    conversions.UnsignedVec_PaillierVec_receive(c.gamma, s.hgamma, 8, [10304], False)

    for i in xrange(12):
        s.homegabar[i] = Homomorphic(val=-s.u[i].dot(s.psi), signed=True, bitlen=30, dim=[1]) + s.hgamma.dot(s.u[i])

    s.hs3 = s.homegabar.dot(s.homegabar)

    for i in xrange(42):
        s.hD[i] = s.hs3 + s.omega[i].dot(s.omega[i])
        s.hD[i] += s.homegabar.dot(s.omega[i] * Signed(bitlen=3, val=-2, signed=True, dim=[1]))

    conversions.PaillierVec_GarbledVec_send(s.hD, c.gD, 69, [42], True, force_bitlen=50, force_signed=False)
    conversions.Unsigned_Garbled_send(s.tau, c.gtau, 50, [1], False)
