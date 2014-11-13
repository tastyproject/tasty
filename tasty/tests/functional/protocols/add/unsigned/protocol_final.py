from tasty.types.driver import TestDriver
__params__ = {'la': 32, 'lb': 32}
driver = TestDriver()

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver, desc='a')
    client.b = Unsigned(bitlen=lb).input(src=driver, desc='b')
    client.c = client.a + client.b
    client.c.output(dest=driver, desc='c')
