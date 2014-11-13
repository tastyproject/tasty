# -*- coding: utf-8 -*-

from tasty.crypt.garbled_circuit import *
from tasty.protocols import protocol
from tasty import state
from tasty import cost_results


class GCProtocol(protocol.Protocol):
    """
    server side, precomputation phase
    self.args[0] = circuit
    self.args[2] = R
    self.args[1] = inputs of 0

    client side, online phase
    self.args[0] = circuit
    self.args[1] = inputs
    """

    name = "GarbledCircuit"

    def __garbledgate_generator(self, gc):
        for g in gc.next_garbled_gate():
            yield g
        self.precomputation_results = gc.outputs


    def server_precomputate1(self, args):
        """
        self.precomp_args[0] = circuit
        self.precomp_args[1] = R
        self.precomp_args[2] = inputs
        """
        c = CreatorGarbledCircuit(*self.precomp_args)
        self.precomputation_results = c.results()

        cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"] += c.creation_costs()

        return self.__garbledgate_generator(c)

    def next_gtable_entry(self):
        for i in self.garbled_table:
            yield i

    def client_precompute1(self, args):
  #      self.garbled_table = tuple()
        self.e = EvaluatorGarbledCircuit(self.precomp_args[0], self.next_gtable_entry(), None)
        self.garbled_table = tuple(args)
        return None

    def client_online1(self, args):
        """
        self.args[0] = circuit
        self.args[1] = tuple of inputs
        """
        self.protocol_one_side_online_only()
        self.e.set_inputs(self.args[1])
        self.e.eval()
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"] += self.e.evaluation_costs()

        self.results = map(tuple, self.e.results())
        return None



    client_precomputation_queue = [protocol.Protocol.dummy_op,
                                   client_precompute1]
    server_precomputation_queue = [server_precomputate1,
                                   protocol.Protocol.finished]

    client_online_queue = [client_online1]
    server_online_queue = [protocol.Protocol.protocol_one_side_online_only]

