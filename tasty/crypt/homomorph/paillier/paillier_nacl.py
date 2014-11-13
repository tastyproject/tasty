# -*- coding: utf-8 -*-

from gmpy import mpz
import pypaillier, paillier_gmp
from tasty._internal import AbstractKey, NodeAttribute
from tasty.crypt import homomorph

__all__ = ["Ciphertext", "PublicKey", "SecretKey", "generate_keys"]

class NaclFactory(type):
    """internal pairing of PublicKey and Ciphertext"""

    _key = None

    def __init__(cls, name, bases, dct):
        super(NaclFactory, cls).__init__(name, bases, dct)
    def __call__(cls,*args,**kw):
        if cls == Ciphertext:
            if not NaclFactory._key:
                raise RuntimeError("Please create a public key first")
            instance = super(NaclFactory, cls).__call__(*args, **kw)
            return instance
        else:
            instance = super(NaclFactory, cls).__call__(*args, **kw)
            if not NaclFactory._key:
                NaclFactory._key = instance
            return instance


class Ciphertext(NodeAttribute):
    """Interface for paillier crypto system. The actual implementation could
    provide more operators."""

    __metaclass__ = NaclFactory

    def __init__(self, value, enc=True):
        """constructor

        @type value: long
        @param value: the ciphertext

        @type public_key: L{PublicKey}
        @param public_key: important reference to the public key
        """

        self._key = NaclFactory._key
        self._value = enc and pypaillier.encrypt(value, self._key._key) or value

    def __int__(self):
        try:
            return int(pypaillier.decrypt(self._value, self._key._key))
        except AttributeError,e :
            return 0


    def __add__(self, other):
        return Ciphertext(pypaillier.encrypt_add(other, self._value, self._key._key), False)

    def __iadd__(self, other):
        self._value = pypaillier.encrypt_add(other, self._value, self._key._key)
        return self

    def __sub__(self, other):
        nsq = mpz(self._key._key["n_square"])
        return Ciphertext(mpz(self._value) * pow(mpz(self._key._key["g"]), mpz(other), nsq).invert(nsq) % nsq, False)

    def __isub__(self, other):
        nsq = mpz(self._key._key["n_square"])
        self._value = mpz(self._value) * pow(mpz(self._key._key["g"]), mpz(other), nsq).invert(nsq) % nsq
        return self

    def __mul__(self, other):
        """Multiplication in ciphertext space

        @type other: integer
        @param other: scalar to multiply

        @rtype: Ciphertext
        @return: product ciphertext
        """

        return Ciphertext(pypaillier.encrypt_mul(self._value, other, self._key._key), False)

    def __imul__(self, other):
        """Inplace multiplication in ciphertext space

        @type other: integer
        @param other: scalar to multiply

        @rtype: Ciphertext
        @return: reference to self
        """

        self._value = pypaillier.encrypt_mul(self._value, other, self._key._key)
        return self

    def __div__(self, other):
        # FIXME: waiting for upstream implementing this,
        return Ciphertext(pypaillier.encrypt_mul(mpz(self._value),
                mpz(other).invert(mpz(self._key._key["n_square"])), self._key),
                self._key)

    def __idiv__(self, other):
        # FIXME: waiting for upstream implementing this,
        self._value = pypaillier.encrypt_mul(
            mpz(self._value),
            mpz(other).invert(mpz(self._key._key["n_square"])),
            self._key)
        return self

    def __getstate__(self):
        return self._value

    def __setstate__(self, state):
        self._value = state
        self._key = NaclFactory._key

    def __eq__(self, other):
        return self._value == other.value

    def __str__(self):
        """String representation

        @rtype: str
        """

        return "<Ciphertext(%r)>" % self._value

    def __repr__(self):
        """Formal string representation

        @rtype: str
        """

        return "Ciphertext(%r)" % self._value

class PublicKey(NodeAttribute, AbstractKey):
    __metaclass__ = NaclFactory

    def __init__(self, bit_length, public_key):
        self._bit_length = bit_length
        self._key = public_key

    def bit_length(self):
        return self._bit_length

    def encrypt(self, value):
        return Ciphertext(pypaillier.encrypt(value, self._key), False)

    def __getstate__(self):
        return self._key

    def __setstate__(self, state):
        self._key = state
        NaclFactory._key = self


    def __del__(self):
        NaclFactory._key = None


    def __repr__(self):
        """String representation"""

        return "PublicKey(%d, %s)" % (
            self.bit_length(), self._key)

class SecretKey(NodeAttribute, AbstractKey):
    """Interface for paillier crypto system"""

    def __init__(self, bit_length, secret_key):
        """Returns a pair of public and secret paillier keys

        @type bit_length: int
        @param bit_length: the bit_length of the keys
        """

        self._bit_length = bit_length
        self._key = secret_key

    def bit_length(self):
        return self._bit_length

    def decrypt(self, ciphertext):
        return mpz(pypaillier.decrypt(ciphertext._value, self._key))

    # floating point exceptions?
    #def encrypt(self, value):
        #return Ciphertext(pypaillier.encrypt(value, self._key), self._key)

    def __getstate__(self):
        return self._bit_length, pypaillier.get_secret(self._key)

    def __setstate__(self, state):
        self._bit_length, state = state
        _, self._key = pypaillier.set_secret(*state)

    def __del__(self):
        NaclFactory._key = None

    def __repr__(self):
        """String representation"""

        return "SecretKey(%d, %d, %d, %d)" % (
            self._bit_length, self._key.p, self._key.q, self._key.g)

def generate_keys(bit_length):
    pub, sec = pypaillier.generate_keys(bit_length)
    return PublicKey(bit_length, pub), SecretKey(bit_length, sec)
