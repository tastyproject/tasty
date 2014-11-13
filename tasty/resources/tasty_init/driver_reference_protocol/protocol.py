# -*- coding: utf-8 -*-

from tasty.types import Driver

class BenchmarkingDriver(Driver):

    def next_params(self):
        for i in xrange(1, 81):
            yield {"L" : i, "N" : 4}


driver = BenchmarkingDriver()


def protocol(client, server, params):
    N = params["N"]
    L = params["L"]

    # input of client
    client.v = UnsignedVec(bitlen=L, dim=N).input(random=True)

    # input of server
    server.w = UnsignedVec(bitlen=L, dim=N).input(random=True)

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

