from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.ga = Garbled(val=Unsigned(bitlen=90, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=90, dim=[1])
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 158, [1], False)
    client.gc = client.ga + client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=159, dim=[1])
