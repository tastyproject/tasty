# -*- coding: utf-8 -*-

from tasty.types import *
from tasty.types.driver import TestDriver

driver = TestDriver()

def protocol(client, server, params):
    dim = params['dim']
    client.a = UnsignedVec(bitlen=16, dim=dim).input(src=driver)
    client.b = UnsignedVec(bitlen=16, dim=dim).input(src=driver)
    client.c = client.a.dot(client.b)
    client.c.output(dest=driver)
