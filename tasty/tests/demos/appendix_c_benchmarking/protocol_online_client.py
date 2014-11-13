from tasty.types import conversions
from tasty.types.driver import IODriver
from tasty import state
from tasty import utils
from tasty.types import *


class BenchmarkingDriver(Driver):

    def next_data_in(self):
        ' yield bitlength for each protocol run: 5, 10, ..., 80'

        for bitlen in xrange(5, 81, 5):
            self.params = {'l': bitlen}
            self.client_inputs = {'x': utils.rand.randint(0, 2 ** bitlen - 1)}
            self.server_inputs = {'y': utils.rand.randint(0, 2 ** bitlen - 1)}
            yield 

__params__ = {'l': 32}
driver = IODriver({'l': 32})

def protocol(client, server, params):
    ' TASTYL program to multiply two unsigned values held by C and S using HE '
    conversions.Garbled_Garbled_receive(server.hx, client.hx, 32, [1], False)
    conversions.Garbled_Garbled_receive(server.hy, client.hy, 32, [1], False)
    client.hr = client.hx * client.hy
    client.r = Unsigned(val=client.hr, signed=False, bitlen=64, dim=[1])
    client.r.output(dest=driver, desc='r')
