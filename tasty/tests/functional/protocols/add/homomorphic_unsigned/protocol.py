# -*- coding: utf-8 -*-

__params__ = {'la': 32, 'lb': 32}

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver, desc='a')
    client.ha = Homomorphic(val=client.a)
    client.b = Unsigned(bitlen=lb).input(src=driver, desc='b')
    client.hc = client.ha + client.b
    client.c = Unsigned(val=client.hc)
    client.c.output(dest=driver, desc='c')
