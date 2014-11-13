from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=215, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.ga = Garbled(val=client.a, signed=False, bitlen=215, dim=[1])
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 67, [1], False)
    client.gc = client.ga + client.gb
    conversions.Garbled_Garbled_send(client.gc, server.gc, 216, [1], False)
