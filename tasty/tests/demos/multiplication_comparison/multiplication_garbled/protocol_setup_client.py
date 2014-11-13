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
    client.ga = Garbled(val=Unsigned(bitlen=137, dim=[1], signed=False, passive=True, empty=True), signed=False, bitlen=137, dim=[1])
    conversions.Garbled_Garbled_receive(server.gb, client.gb, 137, [1], False)
    client.gc = client.ga * client.gb
    client.c = Unsigned(val=client.gc, signed=False, bitlen=274, dim=[1])
