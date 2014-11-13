from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=75, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.b = Unsigned(bitlen=54, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.ga = Garbled(val=client.a, signed=False, bitlen=75, dim=[1])
    client.gb = Garbled(val=client.b, signed=False, bitlen=54, dim=[1])
    client.gc = client.ga + client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=76, dim=[1])
    client.c.output(dest=driver, desc='c')
