from tasty.types import conversions
from tasty.types import *

def protocol(client, server):
    client.setup_output('client setup test')
    client.v
    server.w
    conversions.PaillierVec_GarbledVec_receive(server.hx, client.gx, 64, [4], False)
    client.gmin = client.gx.min_value()
    client.min = Unsigned(val=client.gmin, signed=False, bitlen=64, dim=[1])
    client.setup_output('client setup test 2')
    client.min.setup_output(desc='blah')
