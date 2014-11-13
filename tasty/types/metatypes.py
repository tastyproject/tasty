# -*- coding: utf-8 -*-
import copy

from itertools import izip

from tasty.types.party import *


class Value(PartyAttribute):
    """ Baseclass for numeric party attributes"""

    """constants for masking the corresponding bits to 1 for L{Value.affects}"""
    C_SETUP = 1
    S_SETUP = 2
    C_ONLINE = 4
    S_ONLINE = 8
    NO_C_SETUP = 1
    NO_S_SETUP = 2
    NO_C_ONLINE = 4
    NO_S_ONLINE = 8

    """Constants for masking the corresponding on bits to 0 for L{Value.affects}"""
    NO_C_SETUP = 14
    NO_S_SETUP = 13
    NO_C_ONLINE = 11
    NO_S_ONLINE = 7

    def __init__(self, **kwargs):
        bitlen2 = kwargs.get("bitlen", None)
        bitlen = kwargs.get("force_bitlen", bitlen2)
        val = kwargs.get("val", None)
        super(Value, self).__init__(**kwargs)
        if bitlen is not None  and (not isinstance(bitlen, int) or bitlen < 0):
            raise TypeError("bitlength has to be an int > 0")

        if bitlen is not None :
            self._bit_length = bitlen
            if isinstance(val, Value):
                if bitlen2 == bitlen and self._bit_length < val.bit_length():
                    raise ValueError(
                        "value of %r to big for type (is %d, should be %d)" % (val, val.bit_length(), self._bit_length))
        elif isinstance(val, PartyAttribute):
            self._bit_length = val.bit_length()
        else:
            raise TastySyntaxError("You must either specify a bitlen, or a tasty-type as value")


    def bit_length(self):
        return self._bit_length

    def set_bit_length(self, l):
        self._bit_length = l
        if __debug__:
            self.validate()

    def __getstate__(self):
        if state.protocol_run:
            return {}
        else:
            d = {"_bit_length": self._bit_length}
            return d

    def __setstate__(self, st):
        if not state.protocol_run:
            self._bit_length = st["_bit_length"]
        self.on_attach = []
        try:
            self._dim
        except AttributeError:
            self._dim = [1]

    def validate(self):
        raise NotImplementedError()

    def get_value(self):
        return self._value


class VecIterator(object):
    def __init__(self, vec_type, bitlen, dim, iterator):
        self._type = vec_type
        self._bitlen = bitlen
        self._dim = dim
        self._iterator = iterator

    def next(self):
        tmp = self._iterator.next()
        if isinstance(tmp, list):
            return self._type(bitlen=self._bitlen, val=tmp)
        return tmp

    def __iter__(self):
        return VecIterator(self._type, self._bitlen, self._dim[1:], iter(self._iterator))


class Vec(PartyAttribute, list):
    """ Baseclass for container/array party attributes"""
    _type = Value

    def __init__(self, **kwargs):
        """

        @type dim: int | list<int>
        @keyword dim: dimension(s) of this array/container. A (m x n) Vector has the dimensions [m,n]
        If not provided, it will be determined by the then mandatory values

        @type val: iterable
        @keyword val: optional data. Has to be of the same dimension(s) as 'dim'. If the items are not
        of type self._type, they will be casted.

        @type bitlen: int
        @keyword bitlen: The bit length of each of the elements. If not provided, it will be
        determined by the then mandatory values

        @type passive: bool
        @keyword passive: bool

        @type signed: bool
        @keyword signed: The flag indicates that all elements are signed when true or unsigned

        @type empty: bool
        @keyword empty: This flag when False makes the Vec initialize the internal
        storage with the right dimensional layout of type '_type'
        """

        def set_dim(dim):
            if dim is None:
                dim = self._determineDimension()

            try:
                iter(dim)
            except TypeError:
                dim = [dim]

            self._dim = dim

        def cast_val(self, val, empty):
            if val:
                try:
                    iter(val)
                except TypeError, e:
                    raise TypeError("values must be iterable, are %r" % val)

                try:
                    self._checkListForType(val, self._type)
                    val = copy.copy(val)
                except TypeError:
                    val = self._cast(val, self._type)
                list.__init__(self, val)
            else:
                list.__init__(self)

            if not val and not empty:
                self[:] = self.init_dims(self._dim)


        # if values==None and (dim is None or bitlen is None):
        #    raise ValueError("Vec has to be initialized with either ('dim' and 'bitlen') or 'val'!")
        dim = kwargs.get("dim", None)
        bitlen = kwargs.get("bitlen", None)
        val = kwargs.get("val", None)
        self.passive = passive = kwargs.get("passive", False)
        signed = kwargs.get("signed", None)
        empty = self._empty = kwargs.get("empty", False)

        if val is None and dim is None:
            raise ValueError("Vec has to be initialized with either 'dim' or 'val'!")
        list.__init__(self)

        PartyAttribute.__init__(self, **kwargs)

        if type(bitlen) == type(None):
            if not val:
                raise TastySyntaxError(
                    "You must specify bitlen explicitly when creating %s without a value" % type(self))
            try:
                self._bit_length = val.bit_length()
            except AttributeError:
                raise TastySyntaxError(
                    "You must specify bitlen explicitly when creating %s from type without bit_length() method" % str(
                        type(val)))
        else:
            self._bit_length = bitlen

        try:
            self._signed
        except AttributeError, e:
            try:
                if type(signed) == bool:
                    self._signed = signed
                    if val:
                        assert signed == val.signed(), "sign does not match, did you mean force_signed?"
                else:
                    self._signed = val.signed()
            except AttributeError, e:
                self._signed = False
        try:
            set_dim(dim)
        except IndexError:
            pass

        if passive:
            self._passive = True
            try:
                cast_val(self, val, empty)
            except:
                pass
        else:
            self._passive = False
            cast_val(self, val, empty)

        try:
            self._dim
        except AttributeError:
            set_dim(dim)

        self.on_attach.append(self.emulate_attach)
        self.on_overwrite.append(self.emulate_overwrite)

        assert hasattr(self, "_empty")
        assert hasattr(self, "_dim")
        if __debug__:
            self.validate()


    def __iter__(self):
        return VecIterator(type(self), self._bit_length, self._dim, super(Vec, self).__iter__())

    def emulate_attach(self):
        l = len(self)
        for i in xrange(l):
            item = self[i]
            item.parent = self.parent
            for afunc in item.on_attach:
                afunc()

    def emulate_overwrite(self, other):
        for s, o in zip(self, other):
            for ofunc in s.on_overwrite:
                ofunc(o)

    def init_dims(self, dim):
        tmp = list()
        item_type = self._type
        my_type = type(self)
        dim0 = dim[0]
        bits = self.bit_length()
        if len(dim) > 1:
            newdim = dim[1:]
            res = [self.init_dims(newdim) for i in xrange(dim0)]
            return type(self)(val=res, dim=dim0, bitlen=self._bit_length, overwrite_ok=True, signed=self._signed)
        if len(dim) == 1:
            res = [item_type(bitlen=bits, overwrite_ok=True, signed=self._signed, gid=-1)
                   for i in xrange(dim0)]
            return res
        else:
            raise NotImplementedError(len(dim))

    def _determineDimension(self):
        """ determines the dimensions of the values. returns the dimension"""
        dim = []
        tmp = self
        while isinstance(tmp, list):
            dim.append(len(tmp))
            tmp = super(Vec, self).__getitem__(0)
        return dim

    def _cast(self, values, t):
        ret = []
        bitlen = self._bit_length
        my_type = type(self)
        _cast = self._cast
        for element in values:
            if isinstance(element, list):
                ret.append(my_type(val=_cast(element, t), bitlen=bitlen, signed=self.signed(), passive=self._passive))
            else:
                ret.append(t(val=element, bitlen=bitlen, signed=self.signed(), passive=self._passive))
        return ret


    def validate(self, deep=False):
        self_len = len(self)
        if self_len > 0:
            self._checkListForType(self, self._type)

            # check if values fits to dimensions
            if not self._empty and not self._checkDimension(self, self._dim):
                raise ValueError(
                    "Given values doesn't match the given dimensions! (got %d, expected %d)" % (self_len, self._dim[0]))

            #check if the bitlength of the values fits in this type's bitlength
            self._checkBitlength(self, self._bit_length)

            if deep:
                for i in self:
                    i.validate()

    @staticmethod
    def _checkBitlength(l, length):
        lenl = len(l)
        for i in xrange(lenl):
            element = l[i]
            if isinstance(element, list):
                Vec._checkBitlength(element, length)
            elif element.bit_length() != length:
                raise TypeError("Bitlength of %s is set to %d " \
                                "and differs from vector bitlength %d." % (
                                    str(element), element.bit_length(), length))

    @staticmethod
    def _checkDimension(l, d):
        if not isinstance(l, list):  # then the dimensions of the values are too small
            return False

        if len(l) != d[0]:
            return False
        else:
            if len(d) == 1:
                ret = True
                lenl = len(l)
                for i in xrange(lenl):
                    el = l[i]
                    if isinstance(el, Vec):
                        ret = False
                return ret
            else:
                ret = True
                for el in l:
                    res = Vec._checkDimension(el, d[1:len(d)])
                    ret &= res
                return ret

    @staticmethod
    def _checkListForType(l, t):
        """ checks if all elements of the list 'l' are of type 't'. Otherwise raises a TypeError """
        lenl = len(l)
        for i in xrange(lenl):
            element = l[i]
            if isinstance(element, Vec) or type(element) == list:
                Vec._checkListForType(element, t)
            else:
                if type(element) != t:
                    raise TypeError(
                        "Elements of type %r should be %r, got %r" % (l.__class__.__name__, t, type(element).__name__))


    def bit_length(self):
        return self._bit_length

    def set_bit_length(self, l):
        for i in self:
            i.set_bit_length(l)
        self._bit_length = l
        if __debug__:
            self.validate()

    def append(self, item):
        if isinstance(item, list) and not type(item) == list:
            list.append(self, [el for el in item])
        else:
            list.append(self, item)


    def dim(self):
        return self._dim

    def __setitem__(self, key, value):
        if not isinstance(value, self._type):
            raise TypeError("Only %r objects are allowed. Got %r" % (self._type, type(value)))
        try:
            cur = list.__getitem__(self, key)
        except IndexError:
            if key >= self._dim or self._empty:
                raise
            # initialize now
            self[:] = self.init_dims(self._dim)
            cur = list.__getitem__(self, key)

        for ofunc in cur.on_overwrite:
            ofunc(value)
        list.__setitem__(self, key, value)
        value.parent = self.parent
        for afunc in value.on_attach:
            afunc()

    def __getitem__(self, index):
        if self._empty:
            if len(self._dim) > 1:
                return type(self)(dim=self._dim[1:], passive=True, bitlen=self._bit_length)
            else:
                return self._type(passive=True, bitlen=self._bit_length)
                # raise InternalError("Trying to access content of passive vector")
        else:
            if len(self._dim) > 1:
                return type(self)(dim=self._dim[1:], bitlen=self._bit_length, val=super(Vec, self).__getitem__(index))
            else:
                return list.__getitem__(self, index)

    def __getstate__(self):
        d = {"_bit_length": self._bit_length,
             "_dim": self._dim,
             "_passive": self._passive,
             "_signed": self._signed}
        return d

    def __setstate__(self, state):
        self._bit_length = state["_bit_length"]
        self.on_attach = []
        self._dim = state["_dim"]
        self._passive = state["_passive"]
        self._signed = state["_signed"]
        self._empty = False

    def __repr__(self):
        return "%s(bitlen=%d, dim=%s, signed=%s, val=%s)" % (
        self.__class__.__name__, self._bit_length, self._dim, self._signed, list.__repr__(self))

    def __mul__(self, other):
        if len(self._dim) > 1:
            raise TastySyntaxError("You cannot multiply multidimensional Vectors")
        if isinstance(other, Vec):
            # COMPONENT MULTIPLICATION
            raise NotImplementedError("implement component multiplication for vectors!")
        elif isinstance(other, Value):
            return_rec = \
            self.returns("__mul__", (type(other),), (self._bit_length, other.bit_length()), (self._dim, [1]),
                         (self.signed(), other.signed()))[0]
            tmp = return_rec["type"](bitlen=return_rec["bitlen"], dim=self._dim)
            for i in xrange(self._dim[0]):
                tmp[i] = self[i] * other
            return tmp
        else:
            raise TastySyntaxError(
                "You cannot multiply %s with %s (which is not a tasty-type)" % (type(self), type(other)))

    def dot(self, other):
        assert tuple(self.dim()) == tuple(other.dim()), "you cannot dot-multiply vectors of different size (%r, %r)" % (
        self._dim, other._dim)
        return_rec = \
        self.returns("dot", (type(other),), (self._bit_length, other.bit_length()), (self._dim, other._dim),
                     (self.signed(), other.signed()))[0]
        tmp = reduce(operator.add, (a * b for a, b in izip(self, other)))
        tmp.set_bit_length(return_rec["bitlen"])
        return tmp

    def __add__(self, other):
        """Componenentwise addition"""
        return_rec = \
        self.returns("__add__", (type(other),), (self._bit_length, other.bit_length()), (self._dim, other._dim),
                     (self.signed(), other.signed()))[0]
        tmp = return_rec["type"](dim=self._dim, bitlen=return_rec["bitlen"])
        for i, (j, k) in enumerate(zip(self, other)):
            tmp[i] = j + k
        return tmp


    def __sub__(self, other):
        """Componenentwise substraction"""
        return_rec = \
        self.returns("__sub__", (type(other),), (self._bit_length, other.bit_length()), (self._dim, other._dim))[0]
        tmp = return_rec["type"](dim=self._dim, bitlen=return_rec["bitlen"])
        for i, (j, k) in enumerate(zip(self, other)):
            tmp[i] = j - k
        return tmp


class PartyAttributeVec(Vec):
    _type = PartyAttribute


class PlainType(Value):
    pass


class HomomorphicType(Value):
    pass


class GarbledType(Value):
    pass


class CompareTrue(object):
    def __eq__(self, other):
        return True

    def __req__(self, other):
        return True

    def __int__(self):
        return -1
