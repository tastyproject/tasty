from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    server.a = Unsigned(bitlen=764, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    server.b = Unsigned(bitlen=764, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    server.ga = Garbled(val=server.a, signed=False, bitlen=764, dim=[1])
    server.gb = Garbled(val=server.b, signed=False, bitlen=764, dim=[1])
    conversions.Garbled_Garbled_send(server.ga, client.ga, 764, [1], False)
    conversions.Garbled_Garbled_send(server.gb, client.gb, 764, [1], False)
