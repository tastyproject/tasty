# -*- coding: utf-8 -*-
from tasty.protocols.otprotocols import OTProtocol
from tasty.protocols.protocol import Protocol
from tasty import state, utils, cost_results
from hashlib import sha256
from gmpy import mpz
from struct import pack
from numbers import Integral
import gc

def ithrow(mat, i):
    """ returns the i'th row-vector of matrix mat """
    return [x[i] for x in mat]


class IKNP03(OTProtocol):
    """
    Straight forward implementation of
    Ishail et al. 03: Extending Oblivious Transfers Efficiently
    (Protocol for semi-honest receiver)
    """
    k = None
    __MAX = None

    def __init__(self, *args, **kwargs):
        if not self.k or not self.__MAX:
            IKNP03.k = state.config.symmetric_security_parameter
            IKNP03.__MAX = mpz((1 << (self.k + 1)) - 1)
        super(IKNP03, self).__init__(*args, **kwargs)
        OT = state.config.ot_chain.pop(0)
        self.subot = OT(self.party, reverse=True)
        state.config.ot_chain.insert(0, OT)



    @staticmethod
    def H(m, inp):
        # generate digest
        if isinstance(inp, Integral):
            inp = mpz(inp).binary()
        else:
            inp = inp.binary()
        s = pack(">I", m) + inp
        mpzdigest = mpz(sha256(s).digest(),256)
        v = mpzdigest & IKNP03.__MAX
        return v


    def client_1(self, args):

        self.args = utils.nogen(self.args)

        gc.disable()

        def otlist(r, T):
            r = utils.bits2value(r)
            for i in xrange(self.k):
                ti = utils.bits2value(ithrow(T, i))
                yield (ti, ti^r)

        m = len(self.args)

        if m <= state.config.symmetric_security_parameter:
            # IKNP03 does not make sense if m <= symmetric_security_parameter
            # Use the subot directly then.
            self.subot.forward()
            self.subot(self.args)
            self.results = self.subot.get_results()
            return None

        #self.T = T = [list(utils.get_random(0, 1, self.k)) for i in xrange(m)]
        l = (1<<self.k) - 1
        self.T = T = [utils.value2bits(mpz(utils.rand.randint(0, l)), self.k) for i in xrange(m)]

        self.subot(otlist(self.args, T))

        return tuple()

    def client_2(self, args):
        args = tuple(args)
        self.results = (mpz(args[j][i],256) ^ self.H(j, utils.bits2value(self.T[j])) for j, i in enumerate(self.args))
        gc.enable()
        return None


    def server_1(self, args):
        gc.disable()
        s = list(utils.get_random(0,1, self.k))
        m = len(self.args)

        if m <= state.config.symmetric_security_parameter:
            # IKNP03 does not make sense if m <= symmetric_security_parameter
            # Use the subot directly then.
            self.subot.forward()
            self.subot(self.args)
            return None

        self.subot(s)
        tmp = [utils.value2bits(res, m) for res in self.subot.get_results()]
        Q = zip(*tmp) # transpose tmp
        del tmp
        si = utils.bits2value(s)
        q = [utils.bits2value(j) for j in Q]
        cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send=2*utils.bit2byte(state.config.symmetric_security_parameter) * m)
        gc.enable()
        return (((xj0 ^ self.H(j, qj)).binary(), (xj1 ^ self.H(j, qj ^ si)).binary()) for (j, qj), (xj0, xj1) in zip (enumerate(q), self.args))

    client_online_queue = [client_1, client_2]
    server_online_queue = [server_1, Protocol.finished]
