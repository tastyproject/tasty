from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=192, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.ha = Homomorphic(val=client.a, signed=False, bitlen=192, dim=[1])
    client.b = Unsigned(bitlen=246, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.hc = client.ha + client.b
    client.c = Unsigned(val=client.hc, signed=False, bitlen=247, dim=[1])
    client.c.output(dest=driver, desc='c')
