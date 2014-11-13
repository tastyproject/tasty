# -*- coding: utf-8 -*-

import multiprocessing
import tasty.crypt.homomorph.paillier.gmp.generate
from tasty.crypt.homomorph.paillier.gmp.utils import crt_pow
from gmpy import mpz
from tasty.utils import get_random, rand

__all__ = ["compute_r", "precompute_r"]

def compute_r(key):
    """Computes random number

    @rtype: mpz
    @return: a random integer
    """

    if isinstance(key, tasty.crypt.homomorph.paillier.gmp.generate.SecretKeyGMP):
        return crt_pow(rand.randint(0, long(key.n)), key.n, key)
    return pow(
        mpz(rand.randint(1, long(key.n))),
        key.n,
        key.nsq)


def precompute_r(key, count=1, concurrency=1):
    """Precomputes random number

    @type count: int
    @param count: number of random numbers to precompute

    @type concurrency: int
    @param concurrency: count of parallel processes used for computation

    @rtype: NoneType
    """

    #print "precompute_r(key, count=1, concurrency=1)", count, concurrency
    def _p_r(num=1, queue=None):
        """interal method"""
        l = [compute_r(key) for i in xrange(num)]
        if queue:
            queue.put(l)
        else:
            key.r.extend(l)

    if count > 20 and concurrency == 1:
        _p_r(count)
        return

    queue = multiprocessing.Queue()
    procs = tuple(multiprocessing.Process(
        target = lambda: _p_r(count // concurrency + 1, queue))
        for x in xrange(concurrency))

    for process in procs:
        process.start()

    for process in procs:
        key.r.extend(queue.get())
        process.join()

