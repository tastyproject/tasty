# -*- coding: utf-8 -*-

import unittest
import sys

from tasty.scripts import main

from tasty.types import key
from tasty import config
from tasty.utils import clean_tmpfiles
from tasty import state
#from tasty.utils import result_path
from time import sleep
from multiprocessing import Pipe, Process

"""

HOWTO::

Create a new Subclass of the TastyRemoteCTRL class, that
contains the following methods:
__init__ must have a method_name parameter that is given
to the superclass
__init__ must set the protocol dir (best using the tasty_path() methods from
the tasty.utils package)

next_test_ins is a generator that is called when the
next_params() generator of the TestDriver class is
called. It must set the self.params, self.server_inputs
and self.server_outputs dictionarys apropriatly. When
finished setting up the values for your test run, just yield

next_test_outs is a generator that is called when
the test run is of the protocol is done. it can access
self.client_outputs and self.server_outputs with the
output values of the test run as well as self.server_costs
and self.client_costs. It should implement the usual
python unittest TestCase methods to verify the results.

An Example Test Case (Addition here) follows:

class ExampleTestCase(test_utils.TastyRemoteCTRL):

    def __init__(self, method_name="runTest"):
        test_utils.TastyRemoteCTRL.__init__(self, method_name)

        self.protocol_dir = tasty_path(
            "tests/functional/protocols/unsigned_add")



    def next_data_in(self):
        self.server_inputs = {}
        self.params = {"la": 32, "lb": 32}
        self.client_inputs = {"a": 0, "b": rand.randint(1, 2**32 - 1)}
        yield
        self.client_inputs = {"b": 0, "a": rand.randint(1, 2**32 - 1)}
        yield
        self.client_inputs = {"a": 0, "b": 0}
        yield
        self.client_inputs = {"a": 2**32 - 1, "b": 2**32 - 1}
        yield
        self.client_inputs
	for i in xrange(10):
            la = rand.randint(1, 1024)
            lb = rand.randint(1, 1024)
            self.params = {'la': la, 'lb': lb}
            self.client_inputs = {'a': rand.randint(1, (2**la) - 1), 'b': rand.randint(1, (2**lb) - 1)}
	    yield

    def next_data_out(self):
        while True:
            self.assertEqual(self.client_inputs['a']+self.client_inputs['b'], int(self.client_outputs['c']),
                             msg = "a = %d, b = %d, protocol result is %d, should be %d"%
                             (self.client_inputs['a'], self.client_inputs['b'], self.client_outputs['c'],
                              self.client_inputs['a'] + self.client_inputs['b']))
            self.assertEqual(self.client_outputs['c'].bit_length(), max((self.params['la'], self.params['lb'])) + 1,
                             msg = "bitlength = %d, should be %d"%
                             (self.client_outputs['c'].bit_length(),
                              max((self.params['la'], self.params['lb'])) + 1))
            try:
                self.client_outputs['c'].validate()
            except Exception, e:
                self.fail("Validation failed: %s"%e)
            yield

"""



class TastyRemoteCTRL(unittest.TestCase):

    """Inherit high level testcases aka tasty protocols from this class and
    call in SetUp start_parties().

    You will get access output data via 'self.client_outputs' and
    'self.server_outputs' and the cost objs via 'self.client_costs' and
    'self.server_costs'

    Anyways you must instrumentate your tasty protocol with a 'TestDriver'.
    """

    def __init__(self, methodName='runTest'):
        """narf"""

        super(TastyRemoteCTRL, self).__init__(methodName)

        self._protocol_dir = self.protocol_dir()
        self.client_outputs = None
        self.server_outputs = None
        self.client_costs = None
        self.server_costs = None
        self.params = None
        self.verbose = False

    def setUp(self):
        """Sets tasty config t o something meaningfull"""

        state.config = config.create_configuration(
            protocol_dir=self._protocol_dir,
            host="::1",
            port=9000,
            asymmetric_security_parameter=1024,
            symmetric_security_parameter=80,
            client = True
        )
        public_key, secret_key = key.generate_keys(1024)
        clean_tmpfiles()


    def tearDown(self):
        try:
            self.server_tasty.terminate()
        except Exception:
            pass
        try:
            self.client_tasty.terminate()
        except Exception:
            pass


    def runTest(self):

        self.run_parties()
        sleep(.5)

    def next_params(self):
        self.__delcinputs = self.__delsinputs = False
        for i in self.next_data_in():
            try:
                self.client_inputs
            except AttributeError:
                try:
                    self.client_inputs = self.inputs
                    self.__delcinputs = True
                except AttributeError:
                    raise ValueError("You must either specify self.inputs or self.client_inputs and self.server_inputs in next_data_in")
            try:
                self.server_inputs
            except AttributeError:
                try:
                    self.server_inputs = self.inputs
                    self.__delsinputs = True
                except AttributeError:
                    raise ValueError("You must either specify self.inputs or self.client_inputs and self.server_inputs in next_data_in")
            yield self.params
            if self.__delcinputs:
                del self.client_inputs
                self.__delcinputs = False
            if self.__delsinputs:
                del self.server_inputs
                self.__delsinputs = False


    def run_parties(self):
        """This method adds self.client_pipe and self.server_pipe to this class to be able to communicate with the parties
        for now there are only the outputs awailable"""

        if self.verbose:
            sys.argv = ["tasty", "-sdvv", "--test_mode", self._protocol_dir]
        else:
            sys.argv = ["tasty", "-sd", "--test_mode", self._protocol_dir]

        server_parent_pipe, server_child_pipe = Pipe()
        client_parent_pipe, client_child_pipe = Pipe()
        self.server_tasty = server_tasty = Process(target=main.start, args=(server_child_pipe,), name="Process_tasty_server")
        server_tasty.start()
        sleep(.3)

        if self.verbose:
            sys.argv = ["tasty", "-cdvv", "--test_mode", self._protocol_dir]
        else:
            sys.argv = ["tasty", "-cd", "--test_mode", self._protocol_dir]

        self.client_tasty = client_tasty = Process(target=main.start, args=(client_child_pipe,), name="Process_tasty_client")
        client_tasty.start()
        tester = self.next_data_out()
        for param in self.next_params():
            server_parent_pipe.send(param)
            server_parent_pipe.send(self.server_inputs)
            client_parent_pipe.send(param)
            client_parent_pipe.send(self.client_inputs)
            self.client_outputs = client_parent_pipe.recv()
            self.server_costs, self.client_costs = client_parent_pipe.recv()
            self.server_outputs = server_parent_pipe.recv()
            tester.next()

        server_parent_pipe.send(None)
        client_parent_pipe.send(None)

        server_tasty.join()
        client_tasty.join()
        oldsys = sys.argv
