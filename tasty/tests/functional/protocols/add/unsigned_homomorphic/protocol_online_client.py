from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=30, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.b = Unsigned(bitlen=238, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.hb = Homomorphic(val=client.b, signed=False, bitlen=238, dim=[1])
    client.hc = client.a + client.hb
    client.c = Unsigned(val=client.hc, signed=False, bitlen=239, dim=[1])
    client.c.output(dest=driver, desc='c')
