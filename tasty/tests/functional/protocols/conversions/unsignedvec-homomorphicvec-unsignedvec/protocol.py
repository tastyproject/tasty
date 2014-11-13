# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32, 'dima': 10, 'dimb': 10}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    db = params['db']
    da = params['da']

    client.a = UnsignedVec(bitlen=la, dim=da).input(src=driver, desc="a")
    server.b = UnsignedVec(bitlen=lb, dim=db).input(src=driver, desc="b")

    client.ha = HomomorphicVec(val=client.a)
    client.cc = UnsignedVec(val=client.ha)

    server.ha <<= HomomorphicVec(val=client.a)
    client.cc2 <<= UnsignedVec(val=server.ha)

    client.hb <<= HomomorphicVec(val=server.b)
    client.sc = UnsignedVec(val=client.hb)

    server.hb = HomomorphicVec(val=server.b)
    client.sc2 <<= UnsignedVec(val=server.hb)

    client.cc.output(dest=driver, desc="cc")
    client.sc.output(dest=driver, desc="sc")
    client.cc2.output(dest=driver, desc="cc2")
    client.sc2.output(dest=driver, desc="sc2")
