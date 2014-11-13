# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    dima = params['dima']
    dimb = params['dimb']
    client.a = SignedVec(bitlen=la, dim=dima).input(src=driver, desc="a")
    client.a.output(dest=driver, desc="cc")

    server.b = SignedVec(bitlen=lb, dim=dimb).input(src=driver, desc="b")
    server.hb = HomomorphicVec(val=server.b)
    client.gb <<= GarbledVec(val=server.hb)
    client.sc = SignedVec(val=client.gb)
    client.sc.output(dest=driver, desc="sc")

