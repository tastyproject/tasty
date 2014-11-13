from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'dim': 10, 'lenX': 32, 'lenY': 32}
driver = TestDriver()

def protocol(client, server, params):
    client.v
    server.w = UnsignedVec(bitlen=32, dim=3, signed=False)
    server.w.input(src=driver, desc='Y')
    conversions.UnsignedVec_PaillierVec_receive(client.v, server.hv, 32, [3], False)
    server.hx = server.hv * server.w
    conversions.PaillierVec_GarbledVec_send(server.hx, client.gx, 64, [3], False)
