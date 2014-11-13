# -*- coding: utf-8 -*-
__params__ = {'la': 32, 'lb': 32}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver,desc="a")
    client.b = Unsigned(bitlen=lb).input(src=driver,desc="b")
    client.ga = Garbled(val=client.a)
    client.gb = Garbled(val=client.b)
    client.gc = client.ga + client.gb
    server.gc <<= client.gc
    server.c = Unsigned(val=server.gc)
    server.c.output(dest=driver, desc="c")

