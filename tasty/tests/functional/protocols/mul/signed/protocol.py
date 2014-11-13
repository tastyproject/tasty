# -*- coding: utf-8 -*-
__params__ = {'la': 32, 'lb': 32, 'da': 10} 

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Signed(bitlen=la).input(src=driver,desc="a")
    client.b = Signed(bitlen=lb).input(src=driver,desc="b")
    client.c = client.a * client.b
    client.c.output(dest=driver, desc="c")

