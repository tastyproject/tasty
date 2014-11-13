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
    client.a = Unsigned(bitlen=la).input(src=driver,desc="a")
    server.b = Unsigned(bitlen=lb).input(src=driver,desc="b")
    client.ga = Garbled(val=client.a)
    server.gb = Garbled(val=server.b)
    client.gb <<= server.gb
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc)
    client.c.output(dest=driver, desc="c")

