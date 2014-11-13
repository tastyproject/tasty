# -*- coding: utf-8 -*-

import operator

from tasty.protocols import protocol
import tasty.types
from tasty.utils import rand, nogen
from tasty.types.utils import ceilog
from tasty import state, cost_results, utils
from gmpy import mpz

__all__ = ["HomomorphicMultiplication", "HomomorphicScalarMultiplication", "HomomorphicComponentMultiplication"]

def _unpack(packed, vallen, dim):
    ctextspace = state.config.asymmetric_security_parameter


    t = 0
    p = packed.pop(0).get_value()
    u = []


    for i in xrange(dim):
        t += vallen
        if t >= ctextspace:
#            print "next chunk"
            p = packed.pop(0).get_value()
            t = vallen
        mask = (1 << vallen) - 1
        u.append(tasty.types.Unsigned(val=p & mask, bitlen=vallen))
        p >>= vallen

    if p != 0:
        raise InternalException("unpacking unsuccessfull (atoms around after complete unpacking)")

    return tasty.types.UnsignedVec(val=u, bitlen=vallen, dim=dim)


class HomomorphicMultiplication(protocol.Protocol):

    name = "HomomorphicMultiplication"
    t = None

    def __init__(self, *args):
        super(HomomorphicMultiplication, self).__init__(*args)
        #FIXME: statistic security parameter?
        if not self.t:
            HomomorphicMultiplication.t = t = state.config.symmetric_security_parameter
        else:
            t = self.t
        (c1, c2) = self.precomp_args[:2]
        if state.active_party.role == state.active_party.SERVER:
            self.r1 = tasty.types.Unsigned(val=rand.randint(0, (1 << c1.get_bitlen() + t + 1)-1), bitlen=c1.get_bitlen() + t + 1)
            self.r2 = tasty.types.Unsigned(val=rand.randint(0, (1 << c2.get_bitlen() + t + 1)-1), bitlen=c2.get_bitlen() + t + 1)
            self.hr1r2 = tasty.types.Homomorphic(val=-(self.r1 * self.r2), signed=True)

    def server_round1(self, args):
        """Additively blinds the homomorphic values and sends them to client.
        """

        # we send at least one ciphertext
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(2*state.config.asymmetric_security_parameter))

        c1, c2 = self.args
        self.rbitlen = c1.bit_length() + c2.bit_length()
        if ((c1.get_bitlen() + c2.get_bitlen() + 2*self.t) < state.config.asymmetric_security_parameter):
            if not (c1.signed() or c2.signed()):
                c = ((c1 + self.r1) * tasty.types.Unsigned(val=1<<(c2.get_bitlen() + self.t + 1), bitlen=c2.get_bitlen() + self.t + 1, signed=False) + (c2 + self.r2)) + tasty.types.Homomorphic(val=mpz(0),  bitlen=0, signed=False)
                return (c, c1.get_bitlen(), c2.get_bitlen())
            else:
                raise NotImplementedError("We do not pack signeds yet")
        # we send two ciphertexts now
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(2*state.config.asymmetric_security_parameter))
        return (c1 + self.r1, c2 + self.r2)

    def server_round2(self, args):
        """compute unblinding helpvalue while waiting for the client"""
        c1, c2 = self.args
        r1, r2 = self.r1, self.r2
        # (c1+r1)(c2+r2) = c1c2 + f(c1, c1, r1, r2) where c(c1, c2, r1, r2) = c1r2 + c2r1 + r1r2)
        # calculate __unblind = -f(c1, c2, r1, r2)
        #                     = c1(-r2) + c2(-r1) + (-r1)r2
        self.__unblind = (c1 * (-r2)) + (c2 * (-r1)) + self.hr1r2
        return tuple()

    def server_round3(self, args):
        """ """
        z = tuple(args)[0]
        z._bit_length = 0 # we overwrite it two lines below anyways
        self.results = (z + self.__unblind,)
        self.results[0].set_bit_length(self.rbitlen)
        return None

    def client_round1(self, args):
        """ """
        args = tuple(args)
        if isinstance(args[1], tasty.types.HomomorphicType):
            for new, precomp in zip(args, self.precomp_args):
                new._bit_length = precomp._bit_length + self.t + 1
            x = tasty.types.Signed(val=args[0])
            y = tasty.types.Signed(val=args[1])
        else: #packed
            c, l1, l2 = args
            c._bit_length = l1 + l2 + 2 * self.t + 2
            p = tasty.types.Unsigned(val=c).get_value()

            y = tasty.types.Unsigned(val=(p & ((1<<(self.t + l2 + 1)) - 1)), bitlen=l2 + self.t + 1)
            x = tasty.types.Unsigned(val=(p >> (self.t + l2 + 1)), bitlen=l1 + self.t + 1)

        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(2*state.config.asymmetric_security_parameter))
        return (tasty.types.Homomorphic(val=(x * y), signed=False),)




    client_online_queue = [protocol.Protocol.dummy_op, client_round1, protocol.Protocol.finished]
    server_online_queue = [server_round1, server_round2, server_round3]



class _HomomorhicVecMultiplication(protocol.Protocol):
    def compute_deblinding(self):
        b1b2 = (i * (-j) for i, j in zip(self.blindings, self.blindings2))
        b1b2 = nogen(b1b2)
#        print "deblinding", b1b2
        m1b2 = (i * (-j) for i, j in zip(self.args[0], self.blindings2))
        m2b1 = (i * (-j) for i, j in zip(self.args[1], self.blindings))

        return b1b2, m1b2, m2b1


    def unpack_homovec(self, args):
        (p1, l1, dim1), (p2, l2, dim2) = tuple(args)[:2]

        for p1i, p2i in zip(p1, p2):
            p1i._bit_length = p2i._bit_length = state.config.asymmetric_security_parameter # we don't need bitlen here

        p1plain = [tasty.types.Unsigned(val=i) for i in p1]
        p2plain = [tasty.types.Unsigned(val=i) for i in p2]

        u1 = _unpack(p1plain, l1, dim1)
        u2 = _unpack(p2plain, l2, dim2)

        return u1, u2

    def server_round1(self, args):
        m1, m2 = self.args[:2]
#        print m1, m2
        t1 = tasty.types.HomomorphicVec(val=m1)
        t2 = tasty.types.HomomorphicVec(val=m2) #generate copys to not operate on original data

        self.t1bitlen = t1.bit_length()
        self.t2bitlen = t2.bit_length()
        self.t1dim = t1.dim()


        self.blindings = t1.blind()
        p1 = t1.pack()
        self.blindings2 = t2.blind()
        p2 = t2.pack()
        chunks = len(p1[0]) + len(p2[0])
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(4*state.config.asymmetric_security_parameter * chunks))
        return (p1, p2)


class HomomorphicScalarMultiplication(_HomomorhicVecMultiplication):
    name = "HomomorphicScalarMultiplication"


    def client_round1(self, args):
        u1, u2 = self.unpack_homovec(args)
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(2*state.config.asymmetric_security_parameter))
        return (tasty.types.Homomorphic(val=u1.dot(u2), signed=False),)

    def server_round2(self, args):
        r = tuple(args)[0]
        r._bit_length = 0 # incorrect, but we overwrite it afterwards

        deblinding = reduce(operator.add, map(lambda x: reduce(operator.add, x), self.compute_deblinding()))
        r.on_overwrite = []
        r += deblinding
        r.set_bit_length(self.t1bitlen + self.t1bitlen + ceilog(self.t1dim[0])) # set correct bitlen
        self.results = (r,)

        return None

    client_online_queue = [protocol.Protocol.dummy_op, client_round1, protocol.Protocol.finished]
    server_online_queue = [_HomomorhicVecMultiplication.server_round1, protocol.Protocol.dummy_op, server_round2]


class HomomorphicComponentMultiplication(_HomomorhicVecMultiplication):
    name = "HomomorphicComponentMultiplication"

    def client_round1(self, args):
        u1, u2 = self.unpack_homovec(args)
        cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=utils.bit2byte(2*state.config.asymmetric_security_parameter * len(u1)))

        return tasty.types.HomomorphicVec(val=u1.componentmult(u2), signed=False)


    def server_round2(self, args):
        b1b2, m1b2, m2b1 = self.compute_deblinding()
        b1b2 = SignedVec(val = b1b2)
        m1b2 = tasty.types.HomomorphicVec(val=m1b2)
        m2b1 = tasty.types.HomomorphicVec(val=m2b1)

        deblinding = b1b2 + m1b2 + m2b1

        r = tasty.types.HomomorphicVec(val=args)

        r += deblinding

        self.results = (r,)
        return None



    client_online_queue = [protocol.Protocol.dummy_op, client_round1, protocol.Protocol.finished]
    server_online_queue = [server_round2, protocol.Protocol.dummy_op, server_round2]
