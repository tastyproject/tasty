from tasty.types import conversions
from tasty.types import *

def protocol(client, server):
    client.v
    server.w = UnsignedVec(bitlen=32, dim=4, signed=False)
    server.w.input(desc='enter values for w')
    conversions.PaillierVec_PaillierVec_receive(client.hv, server.hv, 32, [4], False)
    server.hx = server.hv * server.w
    conversions.PaillierVec_GarbledVec_send(server.hx, client.gx, 64, [4], False)
