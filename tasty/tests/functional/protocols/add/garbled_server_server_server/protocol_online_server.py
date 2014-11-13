from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    server.a = Unsigned(bitlen=59, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    server.b = Unsigned(bitlen=86, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    server.ga = Garbled(val=server.a, signed=False, bitlen=59, dim=[1])
    server.gb = Garbled(val=server.b, signed=False, bitlen=86, dim=[1])
    conversions.Garbled_Garbled_send(server.ga, client.ga, 59, [1], False)
    conversions.Garbled_Garbled_send(server.gb, client.gb, 86, [1], False)
    conversions.Garbled_Garbled_receive(client.gc, server.gc, 87, [1], False)
    server.c = Unsigned(val=server.gc, signed=False, bitlen=87, dim=[1])
    server.c.output(dest=driver, desc='c')
