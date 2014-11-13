from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.ga = Garbled(val=Unsigned(bitlen=215, dim=[1], signed=False, passive=True, empty=True), passive=True, signed=False, bitlen=215, dim=[1])
    server.gb = Garbled(val=Unsigned(bitlen=67, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=67, dim=[1])
    conversions.Garbled_Garbled_send(server.gb, client.gb, 67, [1], False)
    client.gc = client.ga + client.gb
    conversions.Garbled_Garbled_receive(client.gc, server.gc, 216, [1], False)
