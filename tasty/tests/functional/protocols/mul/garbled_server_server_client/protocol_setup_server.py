from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    server.ga = Garbled(val=Unsigned(bitlen=764, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=764, dim=[1])
    server.gb = Garbled(val=Unsigned(bitlen=764, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=764, dim=[1])
    conversions.Garbled_Garbled_send(server.ga, client.ga, 764, [1], False)
    conversions.Garbled_Garbled_send(server.gb, client.gb, 764, [1], False)
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc, passive=True, signed=False, bitlen=1528, dim=[1])
