# -*- coding: utf-8 -*-

__params__ = {'dim': 10, 'lenX': 32, 'lenY': 32}

def protocol(client, server, params):
    N = params["dim"]
    Lx = params["lenX"]
    Ly = params["lenY"]

    # input of client
    client.v = UnsignedVec(bitlen=Lx, dim=N)
    client.v.input(src=driver, desc="X")

    # input of server
    server.w = UnsignedVec(bitlen=Ly, dim=N)
    server.w.input(src=driver, desc="Y")

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
    client.min.output(desc="r", dest=driver)
