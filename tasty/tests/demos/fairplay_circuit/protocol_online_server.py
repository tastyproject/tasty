from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import IODriver
driver = IODriver()

def protocol(client, server, params):
    server.y = Signed(bitlen=4, empty=True, signed=True, dim=[1]).input(src=driver, desc='b')
    client.gx = Garbled(val=Signed(bitlen=4, dim=[1], signed=True, passive=True, empty=True), passive=True, signed=True, bitlen=4, dim=[1])
    server.gy = Garbled(val=server.y, signed=True, bitlen=4, dim=[1])
    conversions.Garbled_Garbled_send(server.gy, client.gy, 4, [1], True)
