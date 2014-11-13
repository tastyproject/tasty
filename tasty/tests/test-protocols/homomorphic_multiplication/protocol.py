# -*- coding: utf-8 -*-

from tasty.types import *

def protocol(client, server, params):
    client.x = Unsigned(bitlen=32).input(desc="client.x")
    client.y = Unsigned(bitlen=32).input(desc="client.y")

    server.x <<= Homomorphic(val=client.x)
    server.y <<= Homomorphic(val=client.y)

    server.z = server.x * server.y
    client.z <<= server.z

    client.output(Signed(client.z))
