# -*- coding: utf-8 -*-
from tasty.types.party import PartyAttribute
from tasty.crypt.homomorph.paillier.gmp import generate
from tasty.crypt.homomorph.paillier.gmp.precompute_r import *

__all__ = ["PublicKey", "SecretKey", "generate_keys"]


class Key(object):
    pass


class PublicKey(Key, PartyAttribute):
    def __init__(self, public_key):
        super(PublicKey, self).__init__()
        self._key = public_key

    def __getstate__(self):
        return self._key

    def __repr__(self):
        """String representation"""

        return "PublicKey(%d, %d, %d, %d)" % (
            self._key.bit_length, self._key.n, self._key.nsq, self._key.g)

    def __setstate__(self, _state):
        self._key = _state

    def bit_length(self):
        return self._key.bit_length

    def precompute(self, n, c):
        precompute_r(self._key, n, c)


class SecretKey(Key, PartyAttribute):
    """Interface for paillier crypto system"""

    def __init__(self, secret_key):
        """Returns a pair of public and secret paillier keys

        @type bit_length: int
        @param bit_length: the bit_length of the keys
        """

        super(SecretKey, self).__init__()
        self._key = secret_key

    def __getstate__(self):
        return self._key.bit_length, self._key.p, self._key.q, self._key.g

    def __repr__(self):
        """String representation"""

        return "SecretKey(%d, %d, %d, %d)" % (
            self._key.bit_length, self._key.p, self._key.q, self._key.g)

    def __setstate__(self, state):
        _, self._key = generate.set_secret(*state)

    def bit_length(self):
        return self._key.bit_length

    def precompute(self, n, c):
        precompute_r(self._key, n, c)


def generate_keys(bit_length):
    pub, sec = generate.generate_keys_gmp(bit_length)
    return PublicKey(pub), SecretKey(sec)
