# -*- coding: utf-8 -*-

from tasty.types.driver import TestDriver

driver = TestDriver()

def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    da = params["da"]
    server.a = UnsignedVec(bitlen=la, dim=da).input(src=driver, desc="a")
    server.b = Unsigned(bitlen=lb).input(src=driver, desc="b")
    server.c = server.a * server.b
    server.c.output(dest=driver, desc="c")
