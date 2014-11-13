# -*- coding: utf-8 -*-

from tasty.types import *
from tasty.types.driver import TestDriver

driver = TestDriver()

def protocol(client, server, params):
    client.a = Unsigned(bitlen=params["la"]).input(src=driver,desc="a")
    client.b = Unsigned(bitlen=params["lb"]).input(src=driver,desc="b")
    client.c = client.a + client.b
    client.c.output(dest=driver, desc="c")

