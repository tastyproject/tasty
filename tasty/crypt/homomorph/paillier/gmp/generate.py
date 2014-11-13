#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module implements the key generation of a paillier cryptosystem.
"""

from collections import deque

import warnings
import gmpy
from gmpy import mpz

from tasty import state
from tasty.crypt.homomorph.paillier.gmp.paillier import *
from tasty.crypt.homomorph.paillier.gmp.utils import L, crt_pow
from tasty.utils import rand


__all__ = ["SecretKeyGMP", "PublicKeyGMP", "generate_keys_gmp", "set_secret"]


class PublicKeyGMP(object):
    """Base class for paillier publickey"""

    def __init__(self, bit_length, n=0, g=0):
        """Std constructor

        @type n: int
        @param n:

        @type g: int
        @param g:

        @type bit_length: int
        @param bit_length: bit length of the public key

        @rtype: NoneType
        """

        self.bit_length = bit_length
        self.n = n
        self.n_half = None
        if n:
            self.n_half = n / 2
        self.nsq = n * n
        self.g = g
        self.r = deque()

    def __del__(self):
        if len(self.r):
            print "WARNING!!! %d precomputed r's left when destroying PublicKeyGMP object " % len(self.r)


    def __str__(self):
        """Informal representation

        @rtype: str
        """

        return "Paillier Public Key: g = %d, n^2 = %d" % (
            int(self.g), int(self.nsq))

    def __repr__(self):
        """Formal representation

        @rtype: str
        """

        return "PublicKeyGMP(%d, %d, %d)" % (self.bit_length, int(self.n),
            int(self.g))


class SecretKeyGMP(object):
    """Class for paillier secret keys"""

    def __init__(self, bit_length, p=None, q=None, g=None, r=deque()):

        """Std constructor, If not :param: 'p', generates a key

        @type bit_length: int
        @param bit_length: the length of the secret key to create
        """

        self.bit_length = bit_length
        self.r = r
        self.p = p
        self.q = q
        self.g = g
        self.ordqsq = None
        self.lm = None
        self.denominv = None
        self.psq = None
        self.ordpsq = None
        self.invpmq = None
        self.invpsqmqsq = None
        self.n = None
        self.n_half = None
        self.qsq = None
        self.invqsqmpsq = None
        self.nsq = None
        self.invqmp = None

    def __str__(self):
        """String representation"""

        return "Paillier Secret Key: g = %d, p = %d, q = %d, n^2 = %d" % (
            int(self.g), int(self.p), int(self.q), int(self.nsq))

    def __repr__(self):
        """String representation"""

        return "SecretKeyGMP(%d, %d, %d, %d)" % (
            self.bit_length, self.p, self.q, self.g)


    def __del__(self):
        if len(self.r):
            print "WARNING!!! %d precomputed r's left when destroying SecretKeyGMP object " % len(self.r)


def generate_g_fast(secret_key):
    """Generates a random number"""

    return secret_key.n + 1

def find_random_prime(k):
    """Find a random *k* bit prime number.

    The prime has exactly *k* significant bits:

    @type k: int
    @param k: number of significant bits

    @rtype: mpz
    @return: prime number

    >>> 2 <= _find_random_prime(10) < 2**10
    True
    """

    while True:
        prime = gmpy.next_prime(rand.randint(2**(k-1), 2**k-1))
        if prime < 2**k:
            return prime


def generate_keys_gmp(bit_length, generate=generate_g_fast):
    """Generating paillier public and secret keys

    @type bit_length: int

    @type generate: callable
    @param generate: a callable which returns a generator g in B

    @rtype: tuple(PublicKey, SecretKey)
    """

    secret_key = SecretKeyGMP(bit_length)
    public_key = PublicKeyGMP(bit_length)

    secret_key.p = p = find_random_prime(bit_length / 2)
    while 1:
        secret_key.q = q = find_random_prime(bit_length / 2)
        if p != q:
            break

    secret_key.n = public_key.n = n = p * q
    secret_key.n_half = public_key.n_half = n / 2
    t, secret_key.invpmq, secret_key.invqmp = gmpy.gcdext(p, q)

    secret_key.nsq = public_key.nsq = nsq = n * n

    secret_key.qsq = qsq = q * q
    secret_key.psq = psq = p * p

    t, secret_key.invpsqmqsq, secret_key.invqsqmpsq = gmpy.gcdext(psq, qsq)

    secret_key.ordpsq = p * p - p
    secret_key.ordqsq = q * q - q

    # Calculate Carmichael's function.
    secret_key.lm = lm = gmpy.lcm(p - 1, q - 1)

    # Generate a generator g in B.
    public_key.g = secret_key.g = g = generate(secret_key)

    secret_key.denominv = gmpy.invert(L(crt_pow(g, lm, secret_key), n), n)
    return public_key, secret_key

def _after_pq(public_key, secret_key):
    p = secret_key.p
    q = secret_key.q
    secret_key.n = public_key.n = n = p * q
    secret_key.n_half = public_key.n_half = n / 2
    t, secret_key.invpmq, secret_key.invqmp = gmpy.gcdext(p, q)

    secret_key.nsq = public_key.nsq = nsq = n * n

    secret_key.qsq = qsq = q * q
    secret_key.psq = psq = p * p

    t, secret_key.invpsqmqsq, secret_key.invqsqmpsq = gmpy.gcdext(psq, qsq)

    secret_key.ordpsq = p * p - p
    secret_key.ordqsq = q * q - q

    # Calculate Carmichael's function.
    secret_key.lm = lm = gmpy.lcm(p - 1, q - 1)

def _after_g(public_key, secret_key):
    secret_key.denominv = gmpy.invert(L(crt_pow(secret_key.g, secret_key.lm, secret_key), secret_key.n), secret_key.n)

def set_secret(bit_length, p, q, g):
    public_key = PublicKeyGMP(bit_length)
    secret_key = SecretKeyGMP(bit_length)
    secret_key.p = p
    secret_key.q = q
    secret_key.g = public_key.g = g
    _after_pq(public_key, secret_key)
    _after_g(public_key, secret_key)
    return public_key, secret_key
