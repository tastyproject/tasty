from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 33, 'lb': 33, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    server.b = Signed(bitlen=32, empty=True, signed=True, dim=[1]).input(src=driver, desc='b')
    client.ga = Garbled(val=Signed(bitlen=32, dim=[1], signed=True, passive=True, empty=True), passive=True, signed=True, bitlen=32, dim=[1])
    conversions.Signed_Garbled_send(server.b, client.gb, 32, [1], True)
    conversions.Garbled_Garbled_receive(client.ga, server.ga, 32, [1], True)
    conversions.Garbled_Signed_send(server.ga, client.cc2, 32, [1], True)
    server.gb = Garbled(val=server.b, signed=True, bitlen=32, dim=[1])
    conversions.Garbled_Signed_send(server.gb, client.sc2, 32, [1], True)
