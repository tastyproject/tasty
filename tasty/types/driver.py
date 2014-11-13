# -*- coding: utf-8 -*-

"""
Drivers
-------

This modules implements the Driver baseclass and some special purpose
subclasses
"""

import tasty.types.party
from tasty.exc import TastyUsageError
from tasty.fmt_utils import *

from tasty import state
from tasty.fmt_utils import format_output


class Driver(object):
    """Base class for tasty protocol drivers.

    Subclasses of this class are used in protocol batch/analyze/test modes.
    You must implement some mandatory methods."""

    def __init__(self):
        """std constructor for Driver baseclass"""

        self._client_costs = list()
        self._server_costs = list()
        self._outputs = list()
        self.params = None
        self.client_inputs = None
        self.server_inputs = None

    def output(self):
        """returns an iterable of iterables of each protool runs outputs"""

        return self._outputs

    def client_costs(self):
        """returns an 2 item tuple of iterables of client and server cost
        objects for each tasty protocol run"""

        return self._client_costs

    def server_costs(self):
        """returns an 2 item tuple of iterables of client and server cost
        objects for each tasty protocol run"""

        return self._server_costs

    def next_params(self):
        for i in self.next_data_in():
            yield self.params

    def get_input(self, desc, obj):
        if state.config.client:
            return self.client_inputs[desc]
        return self.server_inputs[desc]

    def new_iteration(self):
        """called before beginning a next protocol run"""

        self._outputs.append({})

    def iteration_end(self):
        pass

    def next_output(self, val, desc, fmt=None):
        self._outputs[-1][desc] = val

    def next_costs(self, client_costs, server_costs):
        """ should cololect costs, optimal: For each driver run, a 2 item set of costs will be saved. """
        self._client_costs.append(client_costs)
        self._server_costs.append(server_costs)


    def next_data_in(self):
        raise NotImplementedError("You must implement a next_data() generator")


class IODriver(Driver):
    """This class will be used for interactive sessions when a driver was
    initialized but config.use_driver is False. Tasty now behaves as if there
    would be any driver mentioned in protocol and uses interactive inputs."""

    def __init__(self, default_parameters=None, client_inputs=None, server_inputs=None):
        """
        @type default_parameters: dict
        @param default_parameters: the parameters that will be used when
        one has implemented an instrumentated protocol and only want to execute
        that protocol once
        """

        super(IODriver, self).__init__()
        self.default_parameters = default_parameters
        self.client_inputs = client_inputs
        self.server_inputs = server_inputs
        if state.config.client:
            self.default_inputs = client_inputs
        else:
            self.default_inputs = server_inputs

    def next_params(self):
        yield self.default_parameters

    def get_input(self, desc, obj):
        if self.default_inputs:
            return self.default_inputs[desc]
        else:
            return obj.input(desc=desc)

    def next_output(self, val, desc, fmt=None):
        """should collect value outputs, optional, method body can be set to pass"""
        state.log.critical(format_output(val, desc=desc, fmt=fmt))


class TestDriver(Driver):
    """This class will be used when started by functional test cases. Its data
    will be received from a testcase via a pipe like connection."""

    def next_params(self):
        try:
            state.parent_pipe.recv
        except AttributeError:
            raise TastyUsageError(
                "TestDriver is exclusively used for use in tastys functional tests (see the tasty.test_utils module) "
                "and cannot be used directly")
        while 1:
            params = state.parent_pipe.recv()
            if params is None:
                break
            self.client_inputs = self.server_inputs = state.parent_pipe.recv()
            yield params

    def iteration_end(self):
        state.parent_pipe.send(self._outputs[-1])
        if tasty.types.party.isclient():
            state.parent_pipe.send((self._server_costs[-1], self._client_costs[-1]))

