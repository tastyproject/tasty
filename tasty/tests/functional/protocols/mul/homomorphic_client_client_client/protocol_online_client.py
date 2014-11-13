from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=51, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.ha = Homomorphic(val=client.a, signed=False, bitlen=51, dim=[1])
    client.b = Unsigned(bitlen=184, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.hb = Homomorphic(val=client.b, signed=False, bitlen=184, dim=[1])
    conversions.Paillier_Paillier_send(client.ha, server.ha, 51, [1], False)
    conversions.Paillier_Paillier_send(client.hb, server.hb, 184, [1], False)
    server.hc = server.ha * server.hb
    conversions.Paillier_Paillier_receive(server.hc, client.hc, 235, [1], False)
    client.c = Unsigned(val=client.hc, signed=False, bitlen=235, dim=[1])
    client.c.output(dest=driver, desc='c')
