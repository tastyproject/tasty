# -*- coding: utf-8 -*-

from tasty.types import *

def protocol(client, server):
    client.foo = UnsignedVec(dim=[5], bitlen=32).input()
    client.gfoo = GarbledVec(val=client.foo)
    client.min_value = client.gfoo.min_value()
    client.pmin_value = Unsigned(val=client.min_value)
    client.output(client.pmin_value, desc="pim_value")
