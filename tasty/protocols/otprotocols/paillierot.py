# -*- coding: utf-8 -*-
from tasty.protocols.otprotocols import OTProtocol
from tasty.protocols import protocol
from tasty import state
from tasty import utils
from tasty import cost_results
from tasty.crypt.homomorph.paillier.gmp.precompute_r import precompute_r
from tasty.crypt.homomorph.paillier.gmp.paillier import encrypt as Enc, decrypt as Dec, add, encrypt_mul as mul
from tasty.crypt.homomorph.paillier.gmp.generate import generate_keys_gmp as Gen
from gmpy import mpz

class PaillierOT(OTProtocol):
    def client_online1(self, args):
        """
        args is empty (no previous messages)

        self.args is expected to be a list of one-bit integers

        returns generator function for encrypted bits
        """
        pk, sk = Gen(state.config.asymmetric_security_parameter)
        self.sk = sk
        yield pk
        size = 0
        size = utils.bit2byte(2*state.config.asymmetric_security_parameter + len(self.args) * state.config.asymmetric_security_parameter * 2)
        if state.precompute:
            cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send=size)
        else:
            cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=size)
        for i in self.args:
            yield Enc(i, pk).binary()

    def client_online3(self, args):
        """
        args[0] = encrypted message 0
        ...
        args[n] = encrypted message n

        returns generator function for encrypted messages
        """
        sk = self.sk
        self.results = tuple(Dec(mpz(c,256), sk) for c in args)
        return None

    def server_online2(self, args):
        """
        args[0] = key
        args[1] = list of encrypted bit values

        self.args is expected to be a list of message-tuples

        returns generator function for encrypted messages
        """

        args = list(args)
        key = args.pop(0)
        size = utils.bit2byte(len(self.args) * state.config.asymmetric_security_parameter * 2)
        if state.precompute:
            cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send=size)
        else:
            cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=size)

        return (add(mul(mpz(cb, 256), m[1] - m[0], key), Enc(m[0], key), key).binary()
                for m, cb in zip(self.args, args))


    client_online_queue = [client_online1, protocol.Protocol.dummy_op, client_online3]
    server_online_queue = [protocol.Protocol.dummy_op, server_online2, protocol.Protocol.finished]
