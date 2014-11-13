# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    server.a = Unsigned(bitlen=la).input(src=driver,desc="a")
    server.b = Unsigned(bitlen=lb).input(src=driver,desc="b")
    server.ga = Garbled(val=server.a)
    server.gb = Garbled(val=server.b)
    client.ga <<= server.ga
    client.gb <<= server.gb
    client.gc = client.ga + client.gb
    server.gc <<= client.gc
    server.c = Unsigned(val=server.gc)
    server.c.output(dest=driver, desc="c")

