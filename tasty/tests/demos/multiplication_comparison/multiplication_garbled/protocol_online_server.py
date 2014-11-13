from tasty.types import conversions
from tasty.types import *
from tasty.utils import rand


class BenchmarkDriver(Driver):

    def next_data_in(self):

        for i in range(1, 256):
            self.params = {'la': i, 'lb': i}
            self.client_inputs = self.server_inputs = {'a': rand.randint(0, 2 ** i - 1), 'b': rand.randint(0, 2 ** i - 1)}
            yield 

__params__ = {'la': 32, 'lb': 32}
driver = BenchmarkDriver()

def protocol(client, server, params):
    server.b = Unsigned(bitlen=137, empty=True, signed=False, dim=[1]).input(src=driver, desc='b')
    client.ga = Garbled(val=Unsigned(bitlen=137, dim=[1], signed=False, passive=True, empty=True), passive=True, signed=False, bitlen=137, dim=[1])
    server.gb = Garbled(val=server.b, signed=False, bitlen=137, dim=[1])
    conversions.Garbled_Garbled_send(server.gb, client.gb, 137, [1], False)
