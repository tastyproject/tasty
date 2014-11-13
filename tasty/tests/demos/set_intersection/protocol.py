# -*- coding: utf-8 -*-

from tasty.crypt.math import getPolyCoefficients
from tasty.utils import rand
from tasty.types.driver import Driver


# that are the default parameters for the IODriver
# when tasty is startet in interactive mode (without the driver_mode flag)
__params__ = {"SETSIZE_C" : 3, "SETSIZE_S" : 3}


class BenchmarkingDriver(Driver):

    def next_data_in(self):

        def generate_random_set(max_number, num):
            """  generate a random set with num entries in the r ange between 0 and max_number """
            s = set()
            while len(s) < num:
                s.add(rand.randint(0, max_number))
            return s



        max_set_entry = 2**32-1
        for i in [10, 100, 1000]:
            self.count_C = i
            self.count_S = i
            self.params = {"SETSIZE_C" : self.count_C, "SETSIZE_S" : self.count_S}

            client_inputs = generate_random_set(max_set_entry, self.count_C)
            server_inputs = generate_random_set(max_set_entry, self.count_S)
            self.client_inputs = {"X": client_inputs}
            self.server_inputs = {"Y": server_inputs}

            yield


def protocol(c, s, params):
    M = params["SETSIZE_C"]
    N = params["SETSIZE_S"]

    c.X = ModularVec(dim=M).input(src=driver, desc="X")
    s.Y = ModularVec(dim=N).input(src=driver, desc="Y")

    # interpolate coefficients of poly with roots c.X
    c.a = getPolyCoefficients()(c.X)

    # encrypt and send coefficients to server
    c.ha   = HomomorphicVec(val=c.a)
    s.ha <<= c.ha

    # evaluate and rerandomize p(y_i) under enc
    s.hbarY = HomomorphicVec(bitlen=1776, dim=N)
    for i in xrange(N):   # 0, ..., N-1
        # evaluate poly p under enc using Horner scheme
        s.p = s.ha[M]
        for j in xrange(M-1,-1,-1):
            s.p = (s.p * s.Y[i]) + s.ha[j]
        s.hbarY[i] = s.p * Modular().rand() \
                   + Homomorphic(val=s.Y[i])

    # send hbarY to client and decrypt
    c.hbarY <<= s.hbarY
    c.barY    = ModularVec(val=c.hbarY)

    # compute intersection of c.X and c.barY
    for e in xrange(M):
        if c.X[e] in c.barY:
            c.output(c.X[e], dest=driver, desc="in intersection is X[%d]" % e)
