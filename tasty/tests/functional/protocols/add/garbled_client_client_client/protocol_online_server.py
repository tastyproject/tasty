from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.ga = Garbled(val=Unsigned(bitlen=75, dim=[1], signed=False, passive=True, empty=True), passive=True, signed=False, bitlen=75, dim=[1])
    client.gb = Garbled(val=Unsigned(bitlen=54, dim=[1], signed=False, passive=True, empty=True), passive=True, signed=False, bitlen=54, dim=[1])
