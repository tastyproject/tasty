from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=844, empty=True, signed=False, dim=[1]).input(src=driver, desc='a')
    client.a.output(dest=driver, desc='cc')
    client.a.output(dest=driver, desc='cc2')
    conversions.Paillier_Garbled_receive(server.hb, client.gb, 233, [1], False)
    client.sc = Unsigned(val=client.gb, signed=False, bitlen=233, dim=[1])
    client.sc.output(dest=driver, desc='sc')
