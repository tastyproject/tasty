from tasty.types import conversions
from tasty.types import *

def protocol(client, server):
    server.setup_output('server setup test')
    client.v
    server.w
    conversions.PaillierVec_GarbledVec_send(server.hx, client.gx, 64, [4], False)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin, passive=True, signed=False, bitlen=64, dim=[1])
    server.setup_output('server setup test 2')
