from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32, 'da': 10}
driver = TestDriver()

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver, desc='a')
    client.ha = Homomorphic(val=client.a)
    client.b = Unsigned(bitlen=lb).input(src=driver, desc='b')
    client.hb = Homomorphic(val=client.b)
    server.ha <<= client.ha
    server.hb <<= client.hb
    server.hc = server.ha * server.hb
    client.hc <<= server.hc
    client.c = Unsigned(val=client.hc)
    client.c.output(dest=driver, desc='c')
