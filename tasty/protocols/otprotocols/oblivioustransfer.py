#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Implements Oblivious Transfer protocols"""

from tasty.protocols import protocol
from tasty.types import Party
from tasty.exc import InternalError
from warnings import warn as warning
from tasty import cost_results
from tasty import utils, state
from gmpy import mpz

class _OTProtocol(protocol.Protocol):
    """
    An OT Protocol does not fit 100% to the protocol architecture as it
    should run everytime it is called without being defered and might
    be run from within another protocol (for example in the IKNP03
    construction)
    """
    name = "ObliviousTransfer"
    def __init__(self, party, reverse=False):
        """
        @type start: party
        """
        self.party = party
        self.results = []
        self.__protocount = protocol.Protocol._protocount
        protocol.Protocol._protocount += 1

        protocol.Protocol._equalize_queuelengths(self.__class__)

        if reverse:
            self.reverse()
        else:
            self.forward()

        if len(self.server_precomputation_queue) > 0:
            raise InternalError("OT Protocols cannot have a precomputation phase")

    def forward(self):
        self.reversed = False
        if self.party.role == self.party.CLIENT:
            self.online_costs = self.client_online_costs
            self.remaining_online_queue = list(self.client_online_queue)
        else: # server
            self.remaining_online_queue = list(self.server_online_queue)
            self.online_costs = self.server_online_costs



    def reverse(self):
        self.reversed = True
        if self.party.role == self.party.SERVER:
            self.online_costs = self.client_online_costs
            self.remaining_online_queue = list(self.client_online_queue)
        else: # server
            self.remaining_online_queue = list(self.server_online_queue)
            self.online_costs = self.server_online_costs

    @staticmethod
    def clear_queue(queue):
        if queue and iter(queue):
            for i in queue: #empty that recvqueue to avoid inconsistency
                warning("Your protocol did not use all messages it received")

    def __call__(self, args):
        self.args = args
        recvqueue = None
        protocol.get_realcost("%s-duration"%self.name).start()
        for op in self.remaining_online_queue:
            send = op(self, recvqueue)
            if send is None: #last message
                self.clear_queue(recvqueue)
                protocol.get_realcost("%s-duration"%self.name).stop()
                return

            if __debug__:
                self.party.socket().sendobj("%s %d"%(self.__class__.__name__, self._protocount))

            for attr in send:
                #print "sening stuff %s"%attr
                self.toggle_timers()
                self.party.socket().sendobj(attr)
                self.toggle_timers()
            self.toggle_timers()
            self.party.socket().sendobj(None)
            self.toggle_timers()
            #print "send None"
            self.clear_queue(recvqueue)
            recvqueue = self._recv_iterator()
        protocol.get_realcost("%s-duration"%self.name).stop()

    def get_results(self):
        return self.results

class OTProtocol(_OTProtocol):
    """
    Interface for the Oblivious Transfer Protocol
    Inherit your OT-Implementation from this
    """
    def client_online1(self, args):
        """
        args is empty in the first round

        self.args a list of the choices in form of one-bit integers

        returns a iterable of messages that should be send to the server
        or None if no messages should be send
        """
        raise NotImplementedError()

    def server_online1(self, args):
        """
        args is empty in the first round

        self.args is expected to be a list of message-tuples

        returns iterable to send to the client or None if no messages to send
        """
        raise NotImplementedError()


    client_precompute_queue = []
    server_precompute_queue = []

    client_online_queue = [client_online1]
    server_online_queue = [server_online1]



class DummyOT(OTProtocol):
    """
    Implements the DUMMY-OT protocol. This is for debugging purpose only.

    ATTENTION:
    NO SECURITY AT ALL, IT IS _NOT_ OBLIVIOUS AND THUS _MUST NOT_ BE USED IN
    PRODUCTION!
    """
    def client_online1(self, args):
        """
        args is empty (no previous messages)

        self.args is expected to be a list of one-bit integers

        returns list of bits
        """
        return self.args

    def client_online3(self, args):
        """
        args contains the messages of the server
        """
        self.results = tuple(args)
        return None

    def server_online2(self, args):
        """
        args contains the choice-bits from the client (round 1)

        self.args is a list of message-tuples

        returns generator function of chosen messages
        """

        for m, b in zip(self.args, args):
            yield m[b]

    def server_online3(self, args):
        return None

    client_online_queue = [client_online1, protocol.Protocol.dummy_op, client_online3]
    server_online_queue = [protocol.Protocol.dummy_op, server_online2, server_online3]



class BeaverOT(protocol.Protocol):
    """
        Not a OTProtocol because the semantic is different, it needs
        additional precomputed parameters
    """
    name = "BeaverOT"

    def client_online1(self, args):
        """ self.args is a tuple containing:
        (
        list of wanted bits,
        list of random bits, chosen at precomputation time,
        list of values received from the Server at runtime
        )
        args is empty (first round)
        """
        b, prec_b = self.args[:2]
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send = utils.bit2byte(len(b)))
        return (tuple(i == j for i, j in zip(b, prec_b)),)

    def client_online3(self, args):
        args = tuple(args)[0]
        self.results = (mpz(m[prec_b], 256) ^ prec_m
                        for m, prec_b, prec_m in
                        zip(args, self.args[1], self.args[2]))
        return None

    def server_online2(self, args):
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send = utils.bit2byte(len(self.args[0])*2*state.config.symmetric_security_parameter))
        args = tuple(args)

        x = tuple(((prec_m[0] ^ m[1-int(b)]).binary(), (prec_m[1] ^ m[int(b)]).binary()) for b, m, prec_m in zip(args[0], *self.args))
        return (x,)
#        for b, m, prec_m in zip(args[0], *self.args):
#            yield ((prec_m[0] ^ m[1-int(b)]).binary(), (prec_m[1] ^ m[int(b)]).binary())


    client_online_queue = [client_online1, protocol.Protocol.dummy_op, client_online3]
    server_online_queue = [protocol.Protocol.dummy_op, server_online2, protocol.Protocol.finished]

