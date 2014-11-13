# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']

    server.a = Unsigned(bitlen=la).input(src=driver, desc="a")
    client.b = Unsigned(bitlen=lb).input(src=driver, desc="b")

    server.ga = Garbled(val=server.a)
    server.cc = Unsigned(val=server.ga)

    client.temp = Garbled(val=client.b)
    server.gb <<= client.temp
    server.sc = Unsigned(val=server.gb)

    client.ga <<= Garbled(val=server.a)
    server.cc2 <<= Unsigned(val=client.ga)

    client.gb = Garbled(val=client.b)
    server.sc2 <<= Unsigned(val=client.gb)

    server.sc.output(dest=driver, desc="sc")
    server.cc.output(dest=driver, desc="cc")
    server.sc2.output(dest=driver, desc="sc2")
    server.cc2.output(dest=driver, desc="cc2")

