from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    server.ga = Garbled(val=Unsigned(bitlen=59, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=59, dim=[1])
    server.gb = Garbled(val=Unsigned(bitlen=86, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=86, dim=[1])
    conversions.Garbled_Garbled_send(server.ga, client.ga, 59, [1], False)
    conversions.Garbled_Garbled_send(server.gb, client.gb, 86, [1], False)
    client.gc = client.ga + client.gb
    conversions.Garbled_Garbled_receive(client.gc, server.gc, 87, [1], False)
