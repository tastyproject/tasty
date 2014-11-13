# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32, 'da': 10} 
def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    da = params["da"]
    client.a = UnsignedVec(bitlen=la, dim=da).input(src=driver, desc="a")
    client.b = Unsigned(bitlen=lb).input(src=driver, desc="b")

    server.a <<= client.a
    server.b <<= client.b

    server.c = server.a * server.b
    server.c.output(dest=driver, desc="c")


