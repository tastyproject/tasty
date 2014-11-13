from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.ga = Garbled(val=Unsigned(bitlen=15, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=15, dim=[1])
    client.gb = Garbled(val=Unsigned(bitlen=15, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=15, dim=[1])
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=30, dim=[1])
