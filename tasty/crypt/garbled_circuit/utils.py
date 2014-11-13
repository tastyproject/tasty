# -*- coding: utf-8 -*-

from tasty import state
from gmpy import mpz
from itertools import imap
from tasty import utils

__all__ = ["generate_garbled_value", "plain2garbled", "garbled2plain", "generate_R", "perm2plain", "permbits"]


### Helper functions
def generate_garbled_value(length):
    return imap(mpz, utils.get_random(0, 2**(state.config.symmetric_security_parameter + 1) - 1, length))

def plain2garbled(value, garbled_null, R):
    return (inp ^ (bit * R) for inp, bit in zip(garbled_null, value))

def garbled2plain(garbled, garbled_null, R):
    for x, y in zip(garbled_null, garbled):
        if x == y:
            yield 0
        elif x == (y ^ R):
            yield 1
        else:
            raise ValueError("Unexpected garbled value (does not match to garbled_null)")

def generate_R():
    return (utils.rand.randint(0,2**(state.config.symmetric_security_parameter)-1) << 1) | 1

def perm2plain(results, zerobits):
    return imap(lambda x: (x[0] & 1) ^ x[1], zip(results, zerobits))

def permbits(values):
    return (int(i & 1) for i in values)

# get n'th bit of val
bit = lambda val, n: (val & (1 << (n - 1))) >> (n - 1)
