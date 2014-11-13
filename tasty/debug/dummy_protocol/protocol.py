# -*- coding: utf-8 -*-

from tasty.types import *

def protocol(client, server):
    N = 4
    L = 32

    # input of client
    client.v = UnsignedVec(bitlen=L, dim=N)
    client.v.input(desc="please provide %d comma-separated values for v" % N)

    # input of server
    server.w = UnsignedVec(bitlen=L, dim=N)
    server.w.input(desc="please provide %d comma-separated values for w" % N)

    # convert unsigned to homomorphic vector
    server.hv <<= HomomorphicVec(val=client.v)

    # multiply homomorphic and unsigned vector (component-wise)
    server.hx = server.hv * server.w

    # convert homomorphic to garbled vector
    client.gx <<= GarbledVec(val=server.hx)

    # compute minimum value
    client.gmin = client.gx.min_value()

    # convert garbled to unsigned value and output this
    client.min = Unsigned(val=client.gmin)
    client.min.output(desc="minimum value")
