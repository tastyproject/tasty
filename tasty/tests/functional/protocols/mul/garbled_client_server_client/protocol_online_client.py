from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=140, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.ga = Garbled(val=client.a, signed=False, bitlen=140, dim=[1])
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 140, [1], False)
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=280, dim=[1])
    client.c.output(dest=driver, desc='c')
