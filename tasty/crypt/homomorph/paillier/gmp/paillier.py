# -*- coding: utf-8 -*-


from tasty.crypt.homomorph.paillier.gmp.precompute_r import *
from tasty.crypt.homomorph.paillier.gmp.utils import L, crt_pow
from gmpy import mpz
import warnings
from tasty.exc import UserWarningOnce

from tasty import cost_results

__all__ = ["encrypt", "encrypt_fast", "decrypt", "encrypt_add", "encrypt_sub",
    "encrypt_mul", "encrypt_div", "add", "sub"]

def encrypt_fast(m, r, public_key):
    """Faster _encrypt_r implementation"""

    n = public_key.n
    if m > n:
        raise ValueError("Message too large!!!")
    # return (mpz(1) + n * (m % n)) * r % public_key.nsq
    return (mpz(1) + n * m  % public_key.nsq) * r % public_key.nsq
    #return (mpz(1) + n * m) * r % public_key.nsq

def encrypt(m, public_key):
    """Encrypts a message

    @type m: mpz
    @param m: message to encrypt

    @type encryptor: callable
    @param m: message to encrypt

    @rtype: L{PaillierCiphertext}
    @return: the encrypted message as L{PaillierCiphertext} object
    """

    cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Paillier_ENC=1)
    try:
        r = public_key.r.popleft()
    except IndexError:
        warnings.warn("Not enough precomputed r", UserWarningOnce)
        r = compute_r(public_key)

    nsq = public_key.nsq
    return ((1 + (m * public_key.n)) * r) % nsq

def decrypt(ciphertext, secret_key):
    """Decrypts a L{PaillierCiphertext}

    @type ciphertext: L{PaillierCiphertext}
    @param ciphertext: the ciphertext to decrypt

    @rtype: int
    @return: plaintext message
    """

    cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Paillier_DEC=1)

    numer = L(crt_pow(ciphertext, secret_key.lm, secret_key), secret_key.n)
    return numer * secret_key.denominv % secret_key.n


def add(ciphertext_a, ciphertext_b, public_key):
    """Addition in ciphertext space

    @type other: PaillierCiphertext
    @param other: the ciphertext to add

    @rtype: PaillierCiphertext
    @return: the sum of self and other
    """

    return ciphertext_a * ciphertext_b % public_key.nsq

def encrypt_add(message, ciphertext, public_key):
    """Addition in ciphertext space

    @type other: PaillierCiphertext
    @param other: the ciphertext to add

    @rtype: PaillierCiphertext
    @return: the sum of self and other
    """

    nsq = public_key.nsq
    return ciphertext * pow(public_key.g, mpz(message), nsq) % nsq


def sub(ciphertext_a, ciphertext_b, public_key):
    """Subtraction in ciphertext space

    @type other: PaillierCiphertext
    @param other: ciphertext to subtract

    @rtype: PaillierCiphertext
    @return: difference ciphertext
    """

    nsq = public_key.nsq
    return ciphertext_a * ciphertext_b.invert(nsq) % nsq

def encrypt_sub(message, ciphertext, public_key):
    """Subtraction in ciphertext space

    @type other: PaillierCiphertext
    @param other: ciphertext to subtract

    @rtype: PaillierCiphertext
    @return: difference ciphertext
    """

    nsq = public_key.nsq
    return ciphertext * pow(public_key.g, mpz(message), nsq).invert(nsq) % nsq


def encrypt_mul(ciphertext_a, scalar, public_key):
    """Multiplication in ciphertext space

    @type other: integer
    @param other: scalar to multiply

    @rtype: PaillierCiphertext
    @return: product ciphertext
    """

    nsq = public_key.nsq
    if scalar >= 0:
        return pow(ciphertext_a, scalar, nsq)
    else:
        return pow(ciphertext_a.invert(nsq), -scalar, nsq)


def encrypt_div(ciphertext, scalar, public_key):
    """Division in ciphertext space

    @type other: integer
    @param other: scalar to divide self

    @rtype: PaillierCiphertext
    @return: difference ciphertext
    """

    cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](exp=1)

    return encrypt_mul(ciphertext, mpz(scalar).invert(public_key.nsq), public_key)
