from tasty.types import conversions
from tasty.types import *
from tasty.types.driver import IODriver
from tasty.crypt.math import getPolyCoefficients
from tasty.utils import rand
from tasty.types.driver import Driver
__params__ = {'SETSIZE_C': 3, 'SETSIZE_S': 3}


class BenchmarkingDriver(Driver):

    def next_data_in(self):

        def generate_random_set(max_number, num):
            '  generate a random set with num entries in the r ange between 0 and max_number '
            s = set()
            while len(s) < num:
                s.add(rand.randint(0, max_number))
            return s
        max_set_entry = 4294967295

        for i in [10, 100, 1000]:
            self.count_C = i
            self.count_S = i
            self.params = {'SETSIZE_C': self.count_C, 'SETSIZE_S': self.count_S}
            client_inputs = generate_random_set(max_set_entry, self.count_C)
            server_inputs = generate_random_set(max_set_entry, self.count_S)
            self.client_inputs = {'X': client_inputs}
            self.server_inputs = {'Y': server_inputs}
            yield 

driver = IODriver({'SETSIZE_C': 3, 'SETSIZE_S': 3})

def protocol(c, s, params):
    pass
