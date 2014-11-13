from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=231, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.b = Unsigned(bitlen=38, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.c = client.a + client.b
    client.c.output(dest=driver, desc='c')
