from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}
driver = TestDriver()

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver, desc='a')
    client.a.output(dest=driver, desc='cc')
    client.a.output(dest=driver, desc='cc2')
    server.b = Unsigned(bitlen=lb).input(src=driver, desc='b')
    server.b.output(dest=driver, desc='sc2')
    server.hb = Homomorphic(val=server.b)
    client.gb <<= Garbled(val=server.hb)
    client.sc = Unsigned(val=client.gb)
    client.sc.output(dest=driver, desc='sc')
