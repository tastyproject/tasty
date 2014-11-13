# -*- coding: utf-8 -*-
#TODO: Create Example Protocol --FaUl

from warnings import warn as warning
from itertools import izip_longest
from tasty import state, cost_results
from tasty.exc import InternalError
import time
__all__ = ["Protocol", ]

def get_realcost(name):
    if state.precompute:
        costs = cost_results.CostSystem.costs["real"]["setup"]
    else:
        costs = cost_results.CostSystem.costs["real"]["online"]

    try:
        costs[name]
    except KeyError:
        costs[name] = cost_results.StopWatch()

    return costs[name]



class Protocol(object):
    """
    This is the Protocol base class, every protocol must be derived from here.

    Usage:
    * Generate a protocol object on both sides synchroniously, constructor
      may get additional precomputation arguments (depending on the protocol)
    * Call protocol with object(<online arguments>), this stores the arguments
      in the object and queues the protocol for execution
    * the next protocol run starts either whenever any results of any queued
      protocol is accessed (in particular object.get_results() returns an
      generator, the protocol run is executed when the generator is used)
      or with explicit call of tasty.protocols.protocol.Protocol.run()
    * Make sure both sides start a protocol-run, otherwise one side will wait
      forever for input. Both method to ensure this is to access the results
      on both side, even if one side does not need any results.

    Implementation of own protocols:
    A protocol consists of multiple methods that describe what happenes between
    the rounds on each side (server, client).

    Each of this methods get two arguments, self (the current protocol object)
    and an generator for the data received from the other sides protocol run
    or None if the call is before the first round.
    Each of this methods MUST return a iterable (tuple, list, generator, ...)
    if there are rounds to go and it must return None after the last round.

    Each Protocol-Subclass has command iterables that lists methods in order
    of execution. Their names and purposes are as follows:
    * server_precomputation_queue lists the methods for precomputation phase
      on the server side
    * client_precomputation_queue lists the corresponding methods for
      precomputation phase on the client side
    * server_online_queue lists the methods for the online phase on the server
      side
    * client_online_queue lists the corresponding methods for the online phase
      on the client side
    """

    __precompute_queue = []
    __online_queue = []
    __run_count = 0
    __precomputed_protocols = 0
    __completed_protocols = 0
    _protocount = 0

    online_round_count = 0
    precompute_round_count = 0

    @staticmethod
    def sync(socket):
        if __debug__:
            state.log.debug("sync")
        socket.sendobj((Protocol.__precomputed_protocols, Protocol.__completed_protocols))
        tmp = socket.recvobj()
        try:
            precomp, online = tmp
        except Exception, e:
            raise InternalError("The protocol framework is out of sync: While unpacking the synchronization data, got %r (%s): %r (Expected: tuple(int, int))"%(tmp, type(tmp), e))

        assert precomp == Protocol.__precomputed_protocols, "The protocol framework is out of sync (precompute)"
        assert online == Protocol.__completed_protocols, "The protocol framework is out of sync (online)"
        if __debug__:
            state.log.debug("sync done")


    @staticmethod
    def _register_precompute(proto):
        Protocol.__precompute_queue.append(proto)

    @staticmethod
    def _unregister_precompute(proto):
        Protocol.__precompute_queue.remove(proto)


    @staticmethod
    def _register_online(proto):
        Protocol.__online_queue.append(proto)


    @staticmethod
    def _unregister_online(proto):
        Protocol.__online_queue.remove(proto)


    @staticmethod
    def precompute():
        if __debug__:
            state.log.debug("doing protocol run (precompute)")
        tmp = len(Protocol.__precompute_queue)
        if Protocol.__precompute_queue != []:
            Protocol.precompute_round_count -= 1
        while Protocol.__precompute_queue != []:
            Protocol.precompute_round_count += 1
            for proto in Protocol.__precompute_queue:
                proto.next_precompute_round()
        Protocol.__run_count += 1

        Protocol.__precomputed_protocols += tmp
        if __debug__:
            state.log.debug("protocol ran complete (precompute)")

    @staticmethod
    def run():
        if __debug__:
            state.log.debug("doing protocol run (online)")
            state.log.debug(Protocol.__online_queue)
        tmp = len(Protocol.__online_queue)
        if Protocol.__online_queue != []:
            Protocol.online_round_count -= 1
        while Protocol.__online_queue != []:
            Protocol.online_round_count += 1
            for proto in Protocol.__online_queue:
                proto.next_online_round()
        Protocol.__run_count += 1
        Protocol.__completed_protocols += tmp
        if __debug__:
            state.log.debug("protocol ran complete (online)")


    @staticmethod
    def dummy_op(self, args):
        """ empty round """
        return tuple()

    @staticmethod
    def finished(self, args):
        return None

    @staticmethod
    def _equalize_queuelengths(cls):
        for a, b in ((cls.server_precomputation_queue, cls.client_precomputation_queue),
                     (cls.server_online_queue, cls.client_online_queue),
                     (cls.server_queue, cls.client_queue)):
            la, lb = len(a), len(b)
            if la == lb:
#                print "lengths are equal"
                continue

            lastround_a = lastround_b = Protocol.finished
            if la > 0:
                lastround_a = a.pop()
            if lb > 0:
                lastround_b = b.pop()
            tmp = izip_longest(a, b, fillvalue=Protocol.dummy_op)

            a = [i[0] for i in tmp]
            b = [i[1] for i in tmp]
            a.append(lastround_a)
            b.append(lastround_b)
#            print a, b

    def toggle_timers(self):
        get_realcost("%s-duration"%self.name).toggle()
        get_realcost("socket-duration").toggle()


    def _recv_iterator(self):
#        x = self.party.socket().recvobj()
        assert self.party.socket().recvobj() == "%s %d"%(self.__class__.__name__, self._protocount), "Make sure we are running the same protocol"
#        print "%s == %s %d"%(x,  self.__class__.__name__, self._protocount)
#        assert x == "%s %d"%(self.__class__.__name__, self._protocount), "Make sure we are running the same protocol"
        while True:
#            debug ("receiving data...")
            self.toggle_timers()
            obj = self.party.socket().recvobj()
            self.toggle_timers()
            if obj is not None :
 #               try:
 #                   debug ("received %r"%obj)
 #               except TypeError:
 #                   debug ("received nonprintables")
                yield obj
            else:
#               debug ("received None")
                break

    def __init__(self, party, precomp_args=None):
        """
        @type start: party
        """

        if __debug__:
            state.log.debug("registering protocol for precomputation: %s", self.__class__.__name__)

        self.party = party
        self.precomp_args = precomp_args
        self.precomputation_results = []
        self.results = []
        self.__running = False
        self._protocount = Protocol._protocount
        Protocol._protocount += 1

        Protocol._equalize_queuelengths(self.__class__)

        if party.role == party.CLIENT:
            self.online_costs = self.client_online_costs
            self.precompute_costs = self.client_precompute_costs
            self.remaining_precomputation_queue = list(self.client_precomputation_queue)
            self.remaining_online_queue = list(self.client_online_queue)
        else: # server
            self.remaining_precomputation_queue = list(self.server_precomputation_queue)
            self.remaining_online_queue = list(self.server_online_queue)
            self.online_costs = self.server_online_costs
            self.precompute_costs = self.server_precompute_costs

        if len(self.remaining_precomputation_queue) > 0:
            Protocol._register_precompute(self)

#        print self.remaining_precomputation_queue


    def __call__(self, args):
        """
        """
        if __debug__:
            state.log.debug("registering protocol for online: %s", self.__class__.__name__)
        self.args = args
        self.currentrun = Protocol.run
        Protocol._register_online(self)


    def get_results(self):
        if Protocol.__run_count <= self.run:
            # Protocol run needed, if data is not yet computed but accessed
            Protocol.run()
#        print self.results
        for i in self.results:
            yield i

    def get_precomputation_results(self):
        if Protocol.__run_count <= self.run:
            # precomputation run nedeed, data is not yet computed but accessed
            Protocol.precompute()
        for i in self.precomputation_results:
            yield i


    def __next_round(self, queue, unregister):
        get_realcost("%s-duration"%self.name).start()
        if self.__running == True:
#            debug ("creating recv_iterator()")
            recvqueue = self._recv_iterator()
        else:
            recvqueue = None
            self.__running = True
        if __debug__:
            state.log.debug("round of %s %s", self, queue)
        op = queue.pop(0)
        if __debug__:
            state.log.debug("starting operation %s", str(op))
        try:
            send = op(self, recvqueue)
        except StopIteration, e:
            state.log.exception(e)
            raise InternalError("StopIteration should not happen here: %s", str(e))
        if __debug__:
            state.log.debug("done %r: %r", op, send)
        if send is not None :
            if __debug__:
                self.party.socket().sendobj("%s %d"%(self.__class__.__name__, self._protocount))
            for attr in send:
#                try:
#                    debug ("sending %r"%attr)
#                except TypeError:
#                    debug ("sending nonprintables")
                self.toggle_timers()
                self.party.socket().sendobj(attr)
                self.toggle_timers()
        else: # send is None
#            debug ("done, unregistering")
            self.__running = False
            if __debug__:
                state.log.debug("unregistering %r", self)
            unregister(self)
            if recvqueue:
                for i in recvqueue: #empty that recvqueue to avoid inconsistency
                    warning("Your protocol did not use all messages it received")
            get_realcost("%s-duration" % self.name).stop()
            return
        self.toggle_timers()
        self.party.socket().sendobj(None)
        self.toggle_timers()
        if recvqueue:
            for i in recvqueue: #empty that recvqueue to avoid inconsistency
                warning("Your protocol did not use all messages it received")
        get_realcost("%s-duration" % self.name).stop()


    def next_precompute_round(self):
#        debug ("next precomputation round")
        self.__next_round(self.remaining_precomputation_queue, Protocol._unregister_precompute)

    def next_online_round(self):
        self.__next_round(self.remaining_online_queue, Protocol._unregister_online)

    #methods for theretical costs
    def server_precompute_costs(self):
        pass

    def server_online_costs(self):
        pass

    def client_precompute_costs(self):
        pass

    def client_online_costs(self):
        pass

    @staticmethod
    def protocol_one_side_precompute_only(*args):
        Protocol.__precomputed_protocols -= 1
        return None

    @staticmethod
    def protocol_one_side_online_only(*args):
        Protocol.__completed_protocols -= 1
        return None


    server_precomputation_queue = []
    client_precomputation_queue = []
    server_online_queue = []
    client_online_queue = []
    server_queue = []
    client_queue = []
