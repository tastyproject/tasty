from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'K': 12, 'N': 10304, 'M': 42}
driver = TestDriver()

def protocol(c, s, p):
    s.homegabar = HomomorphicVec(dim=12, bitlen=31, signed=True, passive=True)
    s.hgamma = HomomorphicVec(dim=10304, bitlen=8, signed=False, passive=True)
    s.hD = HomomorphicVec(dim=42, bitlen=69, signed=True, passive=True)
    c.bot = Unsigned(val=42, bitlen=6, signed=False, dim=[1])
    c.gbot = Garbled(val=c.bot, signed=False, bitlen=6, dim=[1])
    c.gamma = UnsignedVec(bitlen=8, dim=10304, empty=True, signed=False).input(src=driver, desc='gamma')
    conversions.UnsignedVec_PaillierVec_send(c.gamma, s.hgamma, 8, [10304], False)
    s.hs3 = s.homegabar.dot(s.homegabar)
    conversions.PaillierVec_GarbledVec_receive(s.hD, c.gD, 69, [42], True, force_bitlen=50, force_signed=False)
    (c.gDmin_val, c.gDmin_ix) = c.gD.min_value_index()
    conversions.Unsigned_Garbled_receive(s.tau, c.gtau, 50, [1], False)
    c.gcmp = c.gDmin_val < c.gtau
    c.gout = c.gcmp.mux(c.gbot, c.gDmin_ix)
    c.out = Unsigned(val=c.gout, signed=False, bitlen=6, dim=[1])

    if c.out == c.bot:
        c.output(None, dest=driver, desc='out')
    else:
        c.output(c.out, desc='out', dest=driver)
