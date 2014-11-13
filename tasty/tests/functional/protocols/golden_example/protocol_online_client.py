from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'dim': 10, 'lenX': 32, 'lenY': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.v = UnsignedVec(bitlen=32, dim=3, signed=False)
    client.v.input(src=driver, desc='X')
    server.w
    conversions.UnsignedVec_PaillierVec_send(client.v, server.hv, 32, [3], False)
    conversions.PaillierVec_GarbledVec_receive(server.hx, client.gx, 64, [3], False)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin, signed=False, bitlen=64, dim=[1])
    client.min.output(desc='r', dest=driver)
