from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    conversions.Garbled_Garbled_receive(server.ga, client.ga, 764, [1], False)
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 764, [1], False)
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=1528, dim=[1])
    client.c.output(dest=driver, desc='c')
