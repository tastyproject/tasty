# -*- coding: utf-8 -*

from tasty.types import *

def protocol(client, server, params):
    LENGTH = 32

    client.a_plain = Unsigned(bitlen=LENGTH, val=2)
    server.b_plain = Unsigned(bitlen=LENGTH, val=3)
    server.c_plain = Signed(bitlen=LENGTH, val=10)

    client.a = Homomorphic(bitlen=LENGTH, val=client.a_plain)
    server.b = Homomorphic(bitlen=LENGTH, val=server.b_plain)
    server.c = Homomorphic(bitlen=LENGTH, val=server.c_plain)

    server.a <<= client.a

    server.r = server.a + server.b
    #server.r = server.a + server.b - server.c # working on this, folded binop
    server.rr =  server.r - server.c
    client.r <<= server.r
    client.rr <<= server.rr
    client.r_plain = Unsigned(val=client.r)
    client.rr_plain = Unsigned(val=client.rr)
    client.output(client.r_plain, desc="2 + 3") # ok
    client.output(client.rr_plain, desc="2 + 3 - 10") # dam, wrong result
