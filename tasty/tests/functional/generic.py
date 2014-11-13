# -*- coding: utf-8 -*-
from tasty.utils import rand, nogen, get_random

class InputMixin(object):
    MAXBITLEN = 1024
    COUNT = 10
    SAMEBITLEN = False
    SIGNED=(False, False)

    def random(self, maxbit, innum=0):
        if self.SIGNED[innum]:
            return rand.randint(-2** (maxbit - 1) - 1, 2**(maxbit - 1) - 1)
        else:
            return rand.randint(0, 2**maxbit - 1)


    def get_random(self, maxbits, num, innum=0):
        if self.SIGNED[innum]:
            return nogen(get_random(-2** (maxbit - 1) - 1, 2**(maxbit - 1) - 1, num))
        else:
            return nogen(get_random(0, 2**(maxbit) - 1, num))


class TwoVecInputMixin(InputMixin):

    MAXDIM=128

    def next_data_in(self):
        self.params = {"la": 32, "lb": 32, "da": 8, "db": 8}
        self.inputs = {"a": 8 * (0,), "b": self.get_random(32, 8, 0)}
        yield
        self.inputs = {"b": 8 * (0,), "a": self.get_random(32, 8, 1)}
        yield
        self.inputs = {"a": 8 * (0,), "b": 8 * (0,)}
        yield
        self.inputs = {"a": 8 * (2 ** 32 - 1,), "b": 8 * (2 ** 32 - 1,)}
        yield
        for i in xrange(self.COUNT):
            da = rand.randint(1, self.MAXDIM)
            db = rand.randint(1, self.MAXDIM)
            la = rand.randint(1, self.MAXBITLEN)
            lb = rand.randint(1, self.MAXBITLEN)

            self.params = {'la': la, 'lb': lb, 'da': da, 'db': db}
            self.inputs = {'a': self.get_random(la, da, 0),
                           'b': self.get_random(lb, db, 1)}
            yield


class TwoInputMixin(InputMixin):
    """
    """

    SIGNED = (True, True)


    def next_data_in(self):
        self.params = {"la": 32, "lb": 32}
        self.inputs = {"a": 0, "b": self.random(32, 0)}
        yield
        self.inputs = {"b": 0, "a": self.random(32, 1)}
        yield
        self.inputs = {"a": 0, "b": 0}
        yield
        self.inputs = {"a": 2**32 - 1, "b": 2**32 - 1}
        yield
        for i in xrange(self.COUNT):
            la = rand.randint(1, self.MAXBITLEN)
            if self.SAMEBITLEN:
                lb = la
            else:
                lb = rand.randint(1, self.MAXBITLEN)
            self.params = {'la': la, 'lb': lb}
            self.inputs = {'a': self.random(la, 0), 'b': self.random(lb, 1)}
            yield


