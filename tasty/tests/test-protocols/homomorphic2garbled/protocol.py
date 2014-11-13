# -*- coding: utf-8 -*-

from tasty.types import *

def protocol(client, server, params):
    server.value_plain = Unsigned(bitlen=32, val=32)
    client.vp = Unsigned(bitlen = 32, val=31)
    client.hv = Homomorphic(val=client.vp)
    server.value = Homomorphic(val=server.value_plain)
    server.hv <<= client.hv
#    server.value += server.hv
    server.gv = Garbled(bitlen=32, val=server.value)
    client.gv <<= server.gv
    client.v = Unsigned(val=client.gv)
    client.output(client.v)
