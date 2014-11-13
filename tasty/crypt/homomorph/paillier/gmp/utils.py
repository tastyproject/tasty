# -*- coding: utf-8 -*-

__all__ = ["L", "crt_pow"]

def L(u, n):
    """L(u, n) = (u-1)/n"""
    return (u - 1) / n


def crt_pow(b, e, secret_key):
    """Modular exponentiation using crt

    @type b: mpz
    @param b: the base

    @type e: mpz
    @param e: the exponent

    @rtype: mpz
    @return: the result of modular exponentiation
    """

    p = secret_key.psq
    q = secret_key.qsq
    invpmq = secret_key.invpsqmqsq
    invqmp = secret_key.invqsqmpsq
    ordp = secret_key.ordpsq
    ordq = secret_key.ordqsq

    mod = secret_key.nsq

    bp = b % p
    ep = e % ordp

    bq = b % q
    eq = e % ordq

    return ((((p * invpmq) % mod) * pow(bq, eq, q) % mod) + (((q * invqmp) % mod) * pow(bp, ep, p))) % mod
