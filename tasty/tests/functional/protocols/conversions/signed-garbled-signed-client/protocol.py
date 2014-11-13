
# -*- coding: utf-8 -*-

__params__ = {'la': 33, 'lb': 33, 'dima': 10, 'dimb': 10}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Signed(bitlen=la).input(src=driver, desc="a")
    server.b = Signed(bitlen=lb).input(src=driver, desc="b")

    client.ga = Garbled(val=client.a)
    client.cc = Signed(val=client.ga)

    client.gb <<= Garbled(val=server.b)
    client.sc = Signed(val=client.gb)

    server.ga <<= client.ga
    client.cc2 <<= Signed(val=server.ga)

    server.gb = Garbled(val=server.b)
    client.sc2 <<= Signed(val=server.gb)

    client.sc.output(dest=driver, desc="sc")
    client.cc.output(dest=driver, desc="cc")
    client.sc2.output(dest=driver, desc="sc2")
    client.cc2.output(dest=driver, desc="cc2")

