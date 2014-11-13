# -*- coding: utf-8 -*-

from tasty import state
from tasty import utils
from tasty.exc import InternalError
from tasty.protocols import protocol
from tasty.protocols.otprotocols import BeaverOT
from tasty.types.party import isclient

class TastyOT(object):
    def __init__(self, party, num):
        self.party = party
        if __debug__:
            state.active_party.socket().sendobj(num)
            assert num == state.active_party.socket().recvobj(), "number of ots not equal on server and client"
        if not num:
            self.__precomputed_b = self.__precomputed_m = utils.mdeque()
            return
        OT = state.config.ot_chain.pop(0)
        ot = OT(party)
        state.config.ot_chain.insert(0, OT)

        if party.role == party.CLIENT:
            self.__precomputed_b = b = utils.mdeque(utils.get_random(0,1,num))
            ot(b)
            self.__precomputed_m = utils.mdeque(ot.get_results())
            if len(self.__precomputed_b) != len(self.__precomputed_m):
                raise InternalError("The partys do not agree on the number of ots to precompute")
        else:
            self.__precomputed_m = m = utils.mdeque(tuple(utils.get_random(0,(2**state.config.symmetric_security_parameter)-1,2))
                                              for i in xrange(num))
            ot(m)
            protocol.Protocol.run()


    def next_ots(self, args):
        args = tuple(args)
        num = len(args)
        try:
            if isclient(self.party):
                x = (args, self.__precomputed_b.popleft(num), self.__precomputed_m.popleft(num))
            else:
                x = (args, self.__precomputed_m.popleft(num))
        except IndexError:
            try:
                x
            except NameError:
                x = [None,[]]
            raise OverflowError("More oblivoius transfers requested then generated (%d requested and only %d left)"%(num, len(x[1])))
        ot = BeaverOT(self.party)
        ot(x)
        return tuple(ot.get_results())


    def __del__(self):
        try:
            if len(self.__precomputed_m):
                print("[WARNING:] %d precomputed OTs left when destroying the TastyOT object" % len(self.__precomuted_m))
        except AttributeError:
            pass

        try:
            if len(self.__precomputed_b):
                print("[WARNING:] %d precomputed OTs left when destroying the TastyOT object" % len(self.__precomputed_b))
        except AttributeError:
            pass
