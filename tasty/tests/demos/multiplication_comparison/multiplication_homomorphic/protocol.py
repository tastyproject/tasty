# -*- coding: utf-8 -*-

from tasty.types import *
from tasty.utils import rand

class BenchmarkDriver(Driver):
    def next_data_in(self):
        for i in range(1,2**8):
            self.params = {"la": i, "lb": i}
            self.client_inputs = self.server_inputs = {"a": rand.randint(0,2**i - 1), "b": rand.randint(0,2**i - 1)}
            yield

__params__ = {"la" : 32, "lb" : 32}


def protocol(client, server, params):
    la = params['la']
    lb = params['lb']
    client.a = Unsigned(bitlen=la).input(src=driver, desc='a')
    client.ha = Homomorphic(val=client.a)
    server.b = Unsigned(bitlen=lb).input(src=driver, desc='b')
    server.ha <<= client.ha
    server.hc = server.ha * server.b
    client.hc <<= server.hc
    client.c = Unsigned(val=client.hc)
    client.c.output(dest=driver, desc='c')
