from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    conversions.Paillier_Garbled_receive(server.hb, client.gb, 233, [1], False)
    client.sc = Unsigned(val=client.gb, signed=False, bitlen=233, dim=[1])
