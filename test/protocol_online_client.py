from tasty.types import conversions
from tasty.types import *

def protocol(client, server):
    client.v = UnsignedVec(bitlen=32, dim=4, signed=False)
    client.v.input(desc='enter values for v')
    server.w
    client.hv = HomomorphicVec(val=client.v, signed=False, bitlen=32, dim=[4])
    conversions.PaillierVec_PaillierVec_send(client.hv, server.hv, 32, [4], False)
    conversions.PaillierVec_GarbledVec_receive(server.hx, client.gx, 64, [4], False)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin, signed=False, bitlen=64, dim=[1])
    client.min.output(desc='minimum value')
