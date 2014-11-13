from tasty.types import Driver
from tasty.utils import rand

class BenchmarkDriver(Driver):
    def next_data_in(self):
        for i in range(1,11) + range(15,81,5):
	    self.params = {"la": i, "lb": i}
	    self.client_inputs = self.server_inputs = {"a": rand.randint(0,2**i - 1), "b": rand.randint(0,2**i - 1)}
	    yield
