from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 33, 'lb': 33, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Signed(bitlen=32, empty=True, signed=True, dim=[1]).input(src=driver, desc='a')
    client.ga = Garbled(val=client.a, signed=True, bitlen=32, dim=[1])
    client.cc = Signed(val=client.ga, signed=True, bitlen=32, dim=[1])
    conversions.Signed_Garbled_receive(server.b, client.gb, 32, [1], True)
    client.sc = Signed(val=client.gb, signed=True, bitlen=32, dim=[1])
    conversions.Garbled_Garbled_send(client.ga, server.ga, 32, [1], True)
    conversions.Garbled_Signed_receive(server.ga, client.cc2, 32, [1], True)
    conversions.Garbled_Signed_receive(server.gb, client.sc2, 32, [1], True)
    client.sc.output(dest=driver, desc='sc')
    client.cc.output(dest=driver, desc='cc')
    client.sc2.output(dest=driver, desc='sc2')
    client.cc2.output(dest=driver, desc='cc2')
