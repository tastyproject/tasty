from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    server.b = Unsigned(bitlen=233, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    server.b.output(dest=driver, desc='sc2')
    server.hb = Homomorphic(val=server.b, signed=False, bitlen=233, dim=[1])
    conversions.Paillier_Garbled_send(server.hb, client.gb, 233, [1], False)
