55  # -*- coding: utf-8 -*-

"""Tastys public types and api"""

import numbers
import os.path
import types
import warnings
import multiprocessing
from collections import deque, defaultdict
from types import GeneratorType, NoneType

import cPickle
import operator
import sys
import math
from itertools import izip, imap

import gmpy
from gmpy import mpz
from tasty.exc import InternalError, TastySyntaxError, UserWarningOnce, UserWarningRepeated
from tasty import utils, state
from tasty.utils import protocol_file, result_file, tasty_file, protocol_path, tasty_path, result_path, get_random, \
    bit2byte, rand, bitlength, int2comp2, comp22int, nogen, value2bits, bits2value, chunks
from tasty.protocols import transport
from tasty import cost_results


# Homomorphic features
from tasty.crypt.homomorph.paillier.gmp.paillier import *
import tasty.protocols.homomorphic_mult

# GarbledCircuit features
from tasty.circuit import DROP_MSB, SIGNED, UNSIGNED
from tasty.circuit.dynamic import *
from tasty.crypt.garbled_circuit import *
from tasty.protocols.gc_protocols import GCProtocol

# fairplay features
from tasty.circuit.reader import FairplayMP21Circuit as FairplayCircuit, FairplayMP21Circuit, FairplayMP20Circuit, \
    PSSW09Circuit

from tasty.types.metatypes import *
from tasty.types import key
from tasty.types.driver import *
from tasty.types.party import *
from tasty.types.tastyfunction import *
from tasty.types.utils import *

_mpz = type(mpz(0))

__all__ = [
    "Signed",
    "Unsigned",
    "SignedVec",
    "UnsignedVec",
    "Modular",
    "ModularVec",
    "Homomorphic",
    "HomomorphicVec",
    "Paillier",
    "PaillierVec",
    "Garbled",
    "GarbledVec",
    "PlainCircuit",
    "Driver",
    "IODriver",
    "GarbledCircuit",
    "FairplayCircuit",
    "PSSW09Circuit",
    "tasty_file",
    "protocol_file",
    "result_file",
    "tasty_path",
    "protocol_path",
    "FairplayMP20Circuit",
    "FairplayMP21Circuit",
    "result_path"]


class Plain(PlainType):
    costs = {
        "__add__": {"add": 1},
        "__neg__": {"neg": 1},
        "__iadd__": {"add": 1},
        "__sub__": {"sub": 1},
        "__isub__": {"sub": 1},
        "__mul__": {"mul": 1},
        "__eq__": {"equal": 1},
        "__imul__": {"mul": 1},
        "__div__": {"div": 1},
        "__idiv__": {"div": 1}
    }

    def __init__(self, **kwargs):
        """Initializes tasty unencrypted numeric base class.
        Subclasses' validate method will be called.

        @type bit_length: int
        @param bit_length: sets the maximum bit length for this instance,
        if None is provided, the bitlength is calculated automatically so that the value fits in

        @type value: Plain | Paillier | mpz
        @param value: the initial value of this instance
        """

        bit_length = kwargs.get("bitlen", None)
        value = kwargs.get("val", None)
        self._passive = kwargs.get("passive", False)

        if isinstance(value, Plain):
            self._value = value
        elif isinstance(value, Paillier):
            self._value = value._decrypt()
            if value.signed():
                if self._value > state.key._key.n_half:
                    self._value -= state.key._key.n
                if not self.signed():
                    warnings.warn("Warning: value of Unsigned is negative, using absolute value instead",
                                  UserWarningRepeated)
                    self._value = abs(self._value)

        elif isinstance(value, _mpz) or isinstance(value, numbers.Integral):
            self._value = mpz(value)
        elif isinstance(value, Garbled):
            # We don't know to which party we belong at this time, so defer
            # the conversion until we get attached
            super(Plain, self).__init__(**kwargs)
            self.obj = value
            self.on_attach.append(self._defered_init)
        elif value is None or type(value) == PartyAttribute:
            self._value = None
        else:
            raise NotImplementedError("Unsigned cannot be initialized by type %s" %
                                      type(value))
        super(Plain, self).__init__(**kwargs)
        self.on_overwrite.append(self.__preserve_permbits)

    def __preserve_permbits(self, other):
        try:
            # if so, try to keep the permutation_bits if there
            # isn't already one in the to attach Plain
            self.permutation_bits
        except AttributeError:
            try:
                self.permutation_bits = other.permutation_bits
            except AttributeError:
                pass


    def get_value(self):
        return self._value

    def __getstate__(self):
        t = super(Plain, self).__getstate__()
        t['_value'] = self._value
        return t

    def __setstate__(self, state):
        super(Plain, self).__setstate__(state)
        self._value = state["_value"]

    def __abs__(self):
        return Unsigned(bitlen=self._bit_length, val=abs(self._value))

    def __eq__(self, other):
        if not isinstance(other, Plain):
            return False
        if self._value is None:
            return other is None
        return self._value == other._value

    def __ge__(self, other):
        return self._value >= other._value

    def __gt__(self, other):
        return self._value > other._value

    def __int__(self):
        return int(self._value)

    def __le__(self, other):
        return self._value <= other._value

    def __lt__(self, other):
        return self._value < other._value

    def __long__(self):
        return long(self._value)

    def __add__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__add__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        return return_rec["type"](bitlen=return_rec["bitlen"], val=self._value + other._value)

    def __iadd__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__add__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        bitlen = return_rec["bitlen"]
        if isinstance(other, Plain):
            self._value += other._value
            self._bit_length = bitlen
            # FIXME: rtype ???
            if isinstance(self, rtype):
                if __debug__:
                    self.validate()
                return self
            return rtype(bitlen=bitlen, val=self._value)
        raise ValueError("you cannot inplace add %d to %d as it would generate a typechange" % type(self), type(other))

    def __sub__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__sub__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        return rtype(bitlen=return_rec["bitlen"], val=self._value - other._value)

    def __isub__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__sub__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        self._value -= other._value
        self._bit_length = return_rec["bitlen"]
        if isinstance(self, rtype):
            if __debug__:
                self.validate()
            return self
        return rtype(bitlen=return_rec["bitlen"], val=self._value)

    def __mul__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__mul__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        return return_rec["type"](bitlen=return_rec["bitlen"], val=self._value * other._value)

    def __imul__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__mul__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        self._value *= other._value
        self._bit_length = return_rec["bitlen"]
        if isinstance(self, rtype):
            if __debug__:
                self.validate()
            return self
        return return_rec["type"](bitlen=return_rec["bitlen"], val=self._value)

    def __div__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__div__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        return return_rec["type"](bitlen=return_rec["bitlen"], val=self._value / other._value)

    def __idiv__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return_rec = self.returns("__div__", (type(other),), (self._bit_length, other.bit_length(),), ([1], [1]),
                                  (self.signed(), other.signed()))[0]
        self._value /= other._value
        self._bit_length = return_rec["bitlen"]
        if isinstance(self, rtype):
            if __debug__:
                self.validate()
            return self
        return return_rec["type"](bitlen=return_rec["bitlen"], val=self._value)

    def __neg__(self):
        return_rec = self.returns("__neg__", None, (self._bit_length,), ([1],), (self.signed(),))[0]
        return return_rec["type"](bitlen=return_rec["bitlen"], val=-self._value)

    def __str__(self):
        try:
            return str(self._value)
        except AttributeError:
            return str(None)

    def __repr__(self):
        name = self.__class__.__name__
        try:
            return "%s(bitlen = %r, value = %r)" % (name, self._bit_length, self._value)
        except AttributeError:
            try:
                return "%s(bitlen=%r)" % (name, self._bit_length)
            except AttributeError:
                return "<%s at 0x%x>" % (name, id(self))

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Plain.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims,
                            role, passive, precompute)
        if methodname in ("Signed", "Unsigned"):
            # obj = input_type[1]
            if input_types and isinstance(input_types[0], Paillier):
                return Paillier.costs["_decrypt"]
            return {}
        return Plain.costs[methodname]


    @staticmethod
    def affects(methodname, input_types, role):
        """
        @see: L{Value.affects}
        """

        if __debug__:
            state.log.debug("Plain.affects(%r, %r, %r)", methodname, input_types, role)
        if role == Party.CLIENT:
            if methodname in ("Unsigned", "Signed", "Modular"):
                if input_types and issubclass(input_types[0], GarbledType):
                    return Value.S_SETUP | Value.C_SETUP | Value.C_ONLINE
        return Value.affects(methodname, input_types, role)

    def get_bit(self, num):
        self._value.getbit(num)

    def set_value(self, value):
        warnings.warn("do not use anymore 'Plain.set_value()'", DeprecationWarning)
        self._value = value
        if __debug__:
            self.validate()

    def input(self, desc="enter a value", src=None, random=False):
        cost_results.CostSystem.online_stopwatch_group.stop()
        orig_desc = desc
        if isinstance(src, Driver):
            if desc == "enter a value":
                raise TastySyntaxError("You must use desc in input() if using a Driver as source")
            try:
                self._value = mpz(src.get_input(desc, self))
            except TypeError:
                if not self._value:
                    raise

        elif callable(src):
            self._value = src(desc)
            if type(self._value) == GeneratorType:
                self._value = mpz(self._value.next())
            else:
                self._value = mpz(self._value)
        elif src:
            self._value = cPickle.load(open(src, "rb"))
            cost_results.CostSystem.online_stopwatch_group.start()
            self.validate()
            return self
        elif random:
            cost_results.CostSystem.online_stopwatch_group.start()
            return self.rand()
        else:
            while 1:
                try:
                    tmp = raw_input("%s: " % desc)
                    if tmp[:2] in ("0x", "0X"):
                        tmp = int(tmp, 16)
                    elif tmp[:2] == "0b":
                        tmp = int(tmp, 2)
                    self._value = mpz(tmp)
                    self.validate()
                    break
                except ValueError, e:
                    desc = "Invalid input (%s), try again: %s" % (str(e), orig_desc)
                    pass
        cost_results.CostSystem.online_stopwatch_group.start()
        self.validate()
        return self

    def output(self, desc="", dest=None, fmt=None):
        self.parent.output(self, desc=desc, dest=dest, fmt=fmt)

    def __nonzero__(self):
        return self._value != 0

    def rand(self):
        raise NotImplementedError("rand() not implemented for %s" % type(self))


class Signed(Plain):
    """ signed integer type """

    def __init__(self, **kwargs):
        """ optional arguments:
                - val: an [int|mpz|PlainType|HomomorphicType|GarbledType] value. If not provided, it is set to 0
                - bitlen: the bit length of this type. Whereas one bit is reserved for the sign.
                          Therefore the minimum bit length of a type has to be:
                              bitlen( abs(value) )  + sign-bit
        """
        value = kwargs.get("val", None)
        bit_length = kwargs.get("bitlen", None)
        if bit_length <= 1:
            warnings.warn("Signed with bitlength=%r makes no sense" % bit_length)
        super(Signed, self).__init__(**kwargs)


    def _defered_init(self):

        obj = self.obj
        # after that function, self.obj is processed and unnecessary
        del self.obj
        # we are now initialized
        self.on_attach.remove(self._defered_init)
        if not isinstance(obj, GarbledType):
            raise NotImplementedError("Defered conversion is only implemented for garbled")
        role, CLIENT, SERVER = state.active_party.role, Party.CLIENT, Party.SERVER
        if not state.precompute:
            if role == CLIENT:
                # if we are client, we must get the permutation bits to convert
                # to plain. the Transport protocol can provide taht
                # create an unsigned from the result
                if not self._bit_length:
                    self._bit_length = len(self.permutation_bits)
                if obj.signed():
                    self.__init__(bitlen=self._bit_length,
                                  val=comp22int(bits2value(perm2plain(obj.get_value(), self.permutation_bits)),
                                                self._bit_length))
                else:
                    self.__init__(bitlen=self._bit_length,
                                  val=bits2value(perm2plain(obj.get_value(), self.permutation_bits)))
            else:  # SERVER
                if not self._passive:
                    # we do know the zero_value, the R and the garbled value
                    # of the Garbled, so its just simple conversion
                    val = obj.get_value()
                    if obj.signed():
                        val = bits2value(
                            comp22int(garbled2plain(val, Garbled.get_zero_value(obj.gid), state.R), self._bit_length))
                    else:
                        val = bits2value(garbled2plain(val, Garbled.get_zero_value(obj.gid), state.R))
                    # create an unsigned from the result
                    self.__init__(bitlen=self._bit_length, val=val)
        else:
            if role == CLIENT:
                # if we are client, we must get the permutation bits to convert
                # to plain. the Transport protocol can provide taht
                t = transport.Transport(state.active_party)
                t(tuple())
                self.permutation_bits = tuple(t.get_results())
            else:
                if self._passive:
                    # as helper, we just have to send the permutation bits
                    t = transport.Transport(state.active_party)
                    zv = tuple(Garbled.get_zero_value(obj.gid))
                    t(permbits(Garbled.get_zero_value(obj.gid)))
                    cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send=bit2byte(len(zv)))
                    tuple(t.get_results())  # force protocol not being defered


    def signed(self):
        return True

    def validate(self):
        if self._value is None:
            return

        if not isinstance(self._value, _mpz):
            raise TypeError("Value has to be a mpz type. Is: %s" % (type(self._value)))

        valBL = self._value.bit_length()
        if valBL > self._bit_length - 1:
            raise ValueError("Value's(%d) bitlength %d too big for Signed max bit length %d - 1" % (
            self._value, valBL, self._bit_length))

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Signed.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims,
                            role, passive, precompute)
        if methodname in ("__add__", "__sub__", "__mul__"):
            if input_types[0] == Paillier:
                return Paillier.calc_costs(methodname, (Signed), (bit_lengths[1], bit_lengths[0]), dims, role, passive,
                                           precompute)
        return Plain.calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute)

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("Signed.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims, signeds)

        if methodname == "Signed":
            return ({"type": Signed, "bitlen": bit_lengths[0], "dim": [1], "signed": True},)
        elif input_types:
            if input_types[0] == Paillier:
                return Paillier.returns(methodname, (Signed, ), tuple(reversed(bit_lengths)), tuple(reversed(dims)),
                                        tuple(reversed(signeds)))
            elif input_types[0] in (SignedVec, UnsignedVec, PaillierVec, ModularVec):
                return input_types[0].returns(methodname, (Signed, ), tuple(reversed(bit_lengths)),
                                              tuple(reversed(dims)), tuple(reversed(signeds)))
            elif input_types[0] not in (Signed, Unsigned):
                raise NotImplementedError(
                    "unsupported operand type '%s' for arithmetic operations with Signed" % input_types[0])

        if methodname in ("__add__", "__iadd__", "__sub__", "__isub__"):
            if input_types[0] == Signed:
                return ({"type": Signed, "bitlen": max(bit_lengths) + 1, "dim": [1], "signed": True},)
            else:
                return (
                {"type": Signed, "bitlen": max(bit_lengths[0] - 1, bit_lengths[1]) + 2, "dim": [1], "signed": True},)
        elif methodname in ("__mul__", "__imul__"):
            return ({"type": Signed, "bitlen": sum(bit_lengths), "dim": [1], "signed": True},)
        elif methodname in ("__div__", "idiv"):
            return ({"type": Signed, "bitlen": bit_lengths[0], "dim": [1], "signed": True},)
        elif methodname in ("__neg__", "input", "output"):
            return ({"type": Signed, "bitlen": bit_lengths[0], "dim": [1], "signed": True},)
        elif methodname in ("__abs__"):
            return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": [1], "signed": False},)
        elif methodname in ("__le__", "__ge__", "__eq__", "__gt__", "__lt__"):
            return ({"type": bool, "bitlent": 1, "dim": [1], "signed": False},)

        raise NotImplementedError("returns() not implemented for Signed.%s()" % methodname)

    def rand(self):
        self._value = rand.randint(-2 ** (self._bit_length - 1) - 1, 2 ** (self._bit_length - 1) - 1)
        return self


class Unsigned(Plain):
    """ unsigned integer type """

    def __init__(self, **kwargs):
        """ optional arguments:
                - val: a (positive) integer value. If not provided, it is set to 0
                - length: the bit length of this type.
        """
        value = kwargs.get("val", None)
        if isinstance(value, bool):
            kwargs["val"] = int(value)
        if isinstance(value, Value):
            if value.signed():
                warnings.warn("loosing signedness", UserWarningRepeated)

        super(Unsigned, self).__init__(**kwargs)


    def _defered_init(self):

        obj = self.obj
        # after that function, self.obj is processed and unnecessary
        del self.obj
        # we are now initialized
        self.on_attach.remove(self._defered_init)
        if not isinstance(obj, GarbledType):
            raise NotImplementedError("Defered conversion is only implemented for garbled")
        role, CLIENT, SERVER = state.active_party.role, Party.CLIENT, Party.SERVER
        if not state.precompute:
            if role == CLIENT:
                # if we are client, we must get the permutation bits to convert
                # to plain. the Transport protocol can provide taht
                # create an unsigned from the result
                if not self._bit_length:
                    self._bit_length = len(self.permutation_bits)
                if obj.signed():
                    warnings.warn("loosing signedness", UserWarningRepeated)
                    self.__init__(bitlen=self._bit_length, val=abs(
                        comp22int(bits2value(perm2plain(obj.get_value(), self.permutation_bits)), self._bit_length)))
                else:
                    self.__init__(bitlen=self._bit_length,
                                  val=bits2value(perm2plain(obj.get_value(), self.permutation_bits)))
            else:  # SERVER
                if not self._passive:
                    # we do know the zero_value, the R and the garbled value
                    # of the Garbled, so its just simple conversion
                    val = obj.get_value()
                    if not self.signed and obj.signed():
                        warnings.warn("loosing signedness", UserWarningRepeated)
                        val = bits2value(abs(
                            comp22int(garbled2plain(val, Garbled.get_zero_value(obj.gid), state.R), self._bit_length)))
                    else:
                        val = bits2value(garbled2plain(val, Garbled.get_zero_value(obj.gid), state.R))
                    # create an unsigned from the result
                    self.__init__(bitlen=self._bit_length, val=val)
        else:
            if role == CLIENT:
                # if we are client, we must get the permutation bits to convert
                # to plain. the Transport protocol can provide taht
                t = transport.Transport(state.active_party)
                t(tuple())
                self.permutation_bits = tuple(t.get_results())
            else:
                if self._passive:
                    # as helper, we just have to send the permutation bits
                    t = transport.Transport(state.active_party)
                    zv = tuple(Garbled.get_zero_value(obj.gid))
                    t(permbits(Garbled.get_zero_value(obj.gid)))
                    cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send=bit2byte(len(zv)))
                    tuple(t.get_results())  # force protocol not being defered


    def signed(self):
        return False

    def rand(self):
        self._value = rand.randint(0, (2 ** self._bit_length) - 1)
        return self

    def __iadd__(self, other):
        if self._bit_length < other._bit_length and other.signed():
            raise OverflowError("Addition might result in a negative value, not supported for Unsigned")
        else:
            return super(Unsigned, self).__iadd__(other)

    def validate(self):
        if self._value is None:
            return

        if not isinstance(self._value, _mpz):
            raise TypeError("Value has to be a mpz type. Is: %s" % (type(self._value)))

        c = self._value.bit_length()
        bits = self._bit_length
        if c > bits:
            raise ValueError("value bit length '%d' bigger than max bit length '%d'" % (c, bits))

        if self._value < 0:
            raise TypeError("Unsigned instance got negative value. For possibly negative variables use %s" % Signed)


    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("Unsigned.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims, signeds)

        if input_types and input_types[0] not in (Signed, Unsigned, Garbled, Paillier):
            raise NotImplementedError(
                "unsupported operand type '%r' for arithmetic operations with Unsigned" % input_types[0])

        if methodname == "Unsigned":
            return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": dims[0], "signed": False},)
        elif input_types and input_types[0] == Paillier:
            return Paillier.returns(methodname, (Unsigned,), tuple(reversed(bit_lengths)), tuple(reversed(dims)),
                                    tuple(reversed(signeds)))
        elif methodname == "__add__" or methodname == "__iadd__":
            if input_types[0] == Signed:
                return (
                {"type": Signed, "bitlen": max((bit_lengths[0], bit_lengths[1] - 1)) + 2, "dim": [1], "signed": True},)
            else:
                return ({"type": Unsigned, "bitlen": max(bit_lengths) + 1, "dim": [1], "signed": False},)
        elif methodname == "__sub__" or methodname == "__isub__":
            if input_types[0] == Signed:
                return (
                {"type": Signed, "bitlen": max(bit_lengths[0], bit_lengths[1] - 1) + 2, "dim": [1], "signed": True},)
            else:
                return ({"type": Signed, "bitlen": max(bit_lengths) + 1, "dim": [1], "signed": False},)
        elif methodname == "__mul__" or methodname == "__imul__":
            if not signeds[1]:
                return ({"type": Unsigned, "bitlen": sum(bit_lengths), "dim": [1], "signed": False},)
            else:
                return ({"type": Signed, "bitlen": sum(bit_lengths), "dim": [1], "signed": True},)
        elif methodname == "__div__" or methodname == "__idiv__":
            if input_types[0] == Signed:
                return ({"type": Signed, "bitlen": bit_lengths[0] + 1, "dim": [1], "signed": True},)
            else:
                return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": [1], "signed": False},)
        elif methodname == "__neg__":
            return ({"type": Signed, "bitlen": bit_lengths[0] + 1, "dim": [1], "signed": True},)
        elif methodname == "rand":
            return ({"type": Signed, "bitlen": bit_lengths[0], "dim": [1], "signed": True},)
        elif methodname == "__abs__":
            return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": [1], "signed": False},)
        elif methodname in ("__le__", "__ge__", "__eq__", "__gt__", "__lt__"):
            return ({"type": bool, "bitlen": 1, "dim": [1], "signed": False},)
        elif methodname in ("input", "output"):
            return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": [1], "signed": False},)
        raise NotImplementedError("returns not implemented for Unsigned.%s(%s)" % (methodname, input_types))


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Unsigned.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        if methodname in ("__add__", "__sub__", "__mul__"):
            if input_types[0] == Paillier:
                return Paillier.calc_costs(methodname, (Unsigned,), (bit_lengths[1], bit_lengths[0]), dims, role,
                                           passive, precompute)
        elif methodname == "__nonzero__":
            return dict()
        elif methodname == "Unsigned":
            if input_types and input_types[0] == Paillier:
                return {"Dec": 1}
            else:
                return dict()
        return Plain.calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute)


class Modular(Plain):
    """ modular integer type
        the modulus n is set automatically to state.key.n
    """

    def __init__(self, **kwargs):
        """ optional arguments:
                - val: a (positive) integer value. If not provided, it is set to 0
        """
        self.__n = state.key._key.n
        val = kwargs.get("val", None)
        if isinstance(val, Plain):
            val = val._value
        elif isinstance(val, HomomorphicType):
            val = val._decrypt()
        elif isinstance(val, numbers.Integral):
            val = mpz(val)
        elif isinstance(val, _mpz):
            val = val
        elif type(val) == PartyAttribute or val is None:
            val = None
        else:
            raise TypeError("Type %s is not supported as value" % type(val))

        kwargs["bitlen"] = state.config.asymmetric_security_parameter
        kwargs["val"] = val

        super(Modular, self).__init__(**kwargs)

    def validate(self):
        if self._value < 0:
            raise ValueError("value %d has to be greater or equal than 0" % self._value)
        if self._value >= self.__n:
            raise ValueError("value %d has to be smaller than %d" % (self._value, self.__n))
        if self._value.bit_length() > self.bit_length():
            raise ValueError("value bit length '%d' is bigger than maximal bit length '%d'" % (
            self._value.bit_length(), self.bit_length()))

    def signed(self):
        return False

    def __add__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return Modular(val=(self._value + other._value) % self.__n)

    def __iadd__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        self._value += other._value
        self._value %= self.__n
        return self

    def __sub__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return Modular(val=(self._value - other._value) % self.__n)

    def __isub__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        self._value -= other._value
        self._value %= self.__n
        return self

    def __mul__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return Modular(val=(self._value * other._value) % self.__n)

    def __imul__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        self._value *= other._value
        self._value %= self.__n
        return self

    def __div__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        return Modular(val=gmpy.divm(self._value, other._value, self.__n))

    def __idiv__(self, other):
        if not isinstance(other, Plain):
            return NotImplemented
        self._value = gmpy.divm(self._value, other._value, self.__n)
        return self

    def __getstate__(self):
        t = super(Modular, self).__getstate__()
        t['_value'] = self._value.binary()
        t['__n'] = self.__n.binary()
        return t

    def __setstate__(self, state):
        super(Modular, self).__setstate__(state)
        self._value = mpz(state['_value'], 256)
        self.__n = mpz(state['__n'], 256)


    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        # state.log.debug("Modular.returns(%r, %r, %r, %s)", methodname, input_types, bit_lengths, dims)
        return ({"type": Modular, "bitlen": state.config.asymmetric_security_parameter, "dim": [1], "signed": False},)

    def __neg__(self):
        return Modular(val=(self.__n - self._value))

    def __pow__(self, other):
        if isinstance(other, Plain):
            exp = other._value
        else:
            exp = other
        return Modular(val=pow(self._value, exp, self.__n))

    def rand(self):
        self._value = rand.randint(0, self.__n)
        return self

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Modular.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        if methodname in ("__add__", "__sub__", "__mul__"):
            if input_types[0] == Paillier:
                return Paillier.calc_costs(methodname, (Unsigned,), (bit_lengths[1], bit_lengths[0]), dims, role,
                                           passive, precompute)
        elif methodname in ("__nonzero__", "rand"):
            return dict()
        elif methodname == "Modular":
            if input_types and input_types[0] == Paillier:
                return {"Dec": 1}
            else:
                return dict()
        return Plain.calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute)


class PlainVec(Vec):
    _type = Plain

    def rand(self):
        return self.input(random=True)

    def input(self, src=None, desc="", random=False):
        cost_results.CostSystem.online_stopwatch_group.stop()
        if isinstance(src, Driver):
            if desc == "":
                raise TastySyntaxError("You must use desc in input() if using a Driver as source")
            tmp = src.get_input(desc, self)
            self[:] = self._cast(tmp, self._type)
        elif callable(src):
            del self[:]
            newSelf = src(desc)
            tmp = newSelf.next()
            self.extend(tmp)
            self._bit_length = max(i.bit_length() for i in tmp)
            # FIXME: uncomment this
            #if self._bit_length != newSelf._bit_length or self._dim != newSelf._dim:
            #raise TypeError("loaded object parameter (dim=%s, bitlen=%d) don't match to this type (dim=%s,
            # bitlen=%d)" % (str(newSelf._dim), newSelf._bit_length, str(self._dim),self._bit_length))
        elif src:
            newSelf = cPickle.load(open(src, "rb"))
            if self._bit_length != newSelf._bit_length or self._dim != newSelf._dim:
                raise TypeError(
                    "loaded object parameter (dim=%s, bitlen=%d) don't match to this type (dim=%s, bitlen=%d)" % (
                    str(newSelf._dim), newSelf._bit_length, str(self._dim), self._bit_length))
            self = newSelf
        elif random:
            assert self._empty
            bitlen = self.bit_length()
            my_type = type(self)
            item_type = self._type
            if self.signed():
                maxim = 1 << (bitlen - 1) - 1
            else:
                maxim = 1 << bitlen - 1

            def initrandom(next, dim, maxim):
                dim0 = dim[0]
                if len(dim) > 1:
                    # FIXME: random for multidimensional vecs input
                    return [initrandom(i, dim[1:], maxim) for i in xrange(dim0)]
                else:
                    return [item_type(bitlen=bitlen, val=rand.randint(1, maxim))
                            for i in xrange(dim0)]

            self.extend(initrandom(self, self._dim, maxim))
            assert len(self) == self._dim[0]

        else:  # ask the user
            nOfValues = 1
            for d in self._dim:
                nOfValues *= d
            lineLength = self._dim[len(self._dim) - 1]
            lines = nOfValues / lineLength
            values = self._UserInputLines(self._dim, lines, desc=desc)[0]
            self[:] = values

        self._empty = False
        self.validate()

        cost_results.CostSystem.online_stopwatch_group.start()
        return self

    def output(self, desc="", dest=None):
        self.parent.output(self, desc=desc, dest=dest)

    def _UserInputLines(self, dim, nOfLines, linesDone=0, desc=""):
        """ helper function for input() """
        if len(dim) > 1:
            values = []
            for i in xrange(dim[0]):
                vals, linesDone = self._UserInputLines(dim[1:], nOfLines, linesDone, desc=desc)
                values.append(vals)
            return values, linesDone
        else:
            values = [self._type(bitlen=self._bit_length, val=mpz(raw_input("%s[%d/%d]: " % (desc, i + 1, dim[0]))))
                      for i in xrange(dim[0])]
            lv = len(values)
            if lv != dim[0]:
                raise ValueError("Number of values per line has to be %d! (Was %d)" % (dim[0], lv))
            return values, linesDone + 1

    def dot(self, other):
        if isinstance(other, PaillierVec):
            return other.dot(self)  # rdot
        else:
            return super(PlainVec, self).dot(other)

    def __eq__(self, other):
        if type(other) == type(None):
            if len(self) == 0:
                return True
            return False

        if self.dim != other.dim:
            return False
        if self.bit_length != other.bit_length:
            return False
        return all(a == b for a, b in izip(self, other))


    @staticmethod
    def affects(methodname, input_types, role):
        if __debug__:
            state.log.debug("PlainVec.affects(%r, %r, %r)", methodname, input_types, role)
        if role == Party.CLIENT:
            if methodname in ("UnsignedVec", "SignedVec", "ModularVec"):
                if input_types and issubclass(input_types[0], GarbledVec):
                    return Value.S_SETUP | Value.C_SETUP | Value.C_ONLINE
                else:
                    return Value.C_ONLINE

        return Value.affects(methodname, input_types, role)


class SignedVec(PlainVec):
    """n dimensional array of signed values"""
    _type = Signed

    _signed = True

    def __add__(self, other):
        return SignedVec(max(self._bit_length, other.bit_length()) + 1, self._dim,
                         values=[a + b for a, b in izip(self, other.values)])


    def __mul__(self, other):
        if isinstance(other, PaillierVec):
            return other.__mul__(self)
        elif isinstance(other, Plain):
            return_rec = \
            self.returns("__mul__", (type(other),), (self._bit_length, other.bit_length()), (self._dim, [1]),
                         (self.signed(), other.signed()))[0]
            return return_rec["type"](dim=return_rec["dim"], bitlen=return_rec["bitlen"], val=[a * other for a in self])
        elif isinstance(other, Vec):
            tmp = Signed(self.bit_length, 0)
            for a, b in izip(self, other):
                tmp += a * b
            tmp.set_bit_length()
            return tmp
        else:
            raise NotImplementedError("multiplication SignedVec with %s is not yet implemented" % type(other))


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("SignedVec.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        return {}
        raise NotImplementedError("calc_costs() not implemented for SignedVec.%s" % methodname)


    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("SignedVec.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims,
                            signeds)
        dim = dims[0]
        if methodname == "SignedVec":
            return ({"type": SignedVec, "bitlen": bit_lengths[0], "dim": dim, "signed": True},)
        elif methodname == "__mul__":
            return ({"type": SignedVec, "bitlen": sum(bit_lengths), "dim": dim, "signed": True},)
        elif methodname == "dot":
            return ({"type": Signed, "bitlen": 2 * bit_lengths[0] + ceilog(dim[0]), "dim": [1], "signed": True},)
        if methodname == "__getitem__":
            if len(dim) > 1:
                return ({"type": SignedVec, "bitlen": bit_lengths[0], "dim": dim[1:], "signed": True},)
            else:
                return ({"type": Signed, "bitlen": bit_lengths[0], "dim": [1], "signed": True},)
        elif methodname == "input":
            return ({"type": SignedVec, "bitlen": bit_lengths[0], "dim": dim[0], "signed": True},)
        else:
            raise NotImplementedError("returns() not implemented for SignedVec.%s" % methodname)

    def signed(self):
        return True


class UnsignedVec(PlainVec):
    """n dimensional array of unsigned values"""
    _type = Unsigned
    _signed = False

    def signed(self):
        return False

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("UnsignedVec.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        return dict()

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        # state.log.debug("UnsignedVec.returns(%r, %r, %r, %r)", methodname, input_types, bit_lengths, dims)
        dim = dims[0]
        if methodname == "UnsignedVec":
            return ({"type": UnsignedVec, "bitlen": bit_lengths[0], "dim": dim, "signed": False},)
        elif methodname == "__getitem__":
            if len(dim) > 1:
                return ({"type": UnsignedVec, "bitlen": bit_lengths[0], "dim": dim[1:], "signed": False},)
            else:
                return ({"type": Unsigned, "bitlen": bit_lengths[0], "dim": [1], "signed": False},)
        if methodname == "__mul__":
            if input_types[0] == Unsigned:
                return ({"type": UnsignedVec, "bitlen": sum(bit_lengths), "dim": dim, "signed": False},)
            elif input_types[0] == Signed:
                return ({"type": SignedVec, "bitlen": sum(bit_lengths), "dim": dim, "signed": True},)
            else:
                raise NotImplementedError("returns() not implemented for UnsignedVec.__mul__(%r)" % input_types[0])
        if methodname == "dot":
            return ({"type": Unsigned, "bitlen": 2 * bit_lengths[0] + ceilog(dim[0]), "dim": [1], "signed": False},)
        if methodname == "__eq__":
            return ({"type": bool, "bitlen": 1, "dim": [1], "signed": False},)
        elif methodname == "input":
            return ({"type": UnsignedVec, "bitlen": bit_lengths[0], "dim": dims[0], "signed": False},)
        else:
            raise NotImplementedError("returns() not implemented for UnsignedVec.%s()" % methodname)


class ModularVec(PlainVec):
    """ Vector of Modular Values """
    _type = Modular

    def __init__(self, **kwargs):
        kwargs["bitlen"] = state.config.asymmetric_security_parameter
        super(ModularVec, self).__init__(**kwargs)


    def __mul__(self, other):
        if isinstance(other, PaillierVec):
            return other.__mul__(self)
        elif isinstance(other, Vec):
            return ModularVec(val=[a * b for a, b in izip(self, other)])
        else:
            raise NotImplementedError("multiplication Modular with %s is not yet implemented" % type(other))

    def dot(self, other):
        ret = super(ModularVec, self).dot(other)
        if isinstance(other, PlainVec):
            ret.set_bit_length()
        return ret

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("ModularVec.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        return dict()

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        # state.log.debug("ModularVec.returns(%r, %r, %r, %r)", methodname, input_types, bit_lengths, dims)
        dim = dims[0]
        if methodname == "__getitem__":
            if len(dim) > 1:
                return ({"type": ModularVec, "bitlen": state.config.asymmetric_security_parameter, "dim": dim[1:],
                         "signed": False},)
            else:
                return (
                {"type": Modular, "bitlen": state.config.asymmetric_security_parameter, "dim": [1], "signed": False},)
        return (
        {"type": ModularVec, "bitlen": state.config.asymmetric_security_parameter, "dim": dims[0], "signed": False},)


###############################################################################################
###### HOMOMORPHIC STUFF
###############################################################################################

class Paillier(HomomorphicType):
    """Interface for paillier crypto system. The actual implementation could
    provide more operators."""

    costs = {
        "__init__": {"encrypt": 1, "mod": 2, "pow": 1, "mul": 1},
        "__add__": {"pow": 1, "mod": 1},
        "__iadd__": {"pow": 1, "mod": 1},
        "__sub__": {"pow": 1, "invert": 1, "mod": 1},
        "__isub__": {"pow": 1, "invert": 1, "mod": 1},
        "__mul__": {"pow": 1},
        "__imul__": {"pow": 1},
        "__div__": {"invert": 1, "mul": 1},
        "__idiv__": {"invert": 1, "mul": 1},
        "_decrypt": {"add": 1, "sub": 1, "mul": 1, "div": 1, "exp": 1,
                     "mod": 1, "pow": 1}
    }

    def __init__(self, **kwargs):
        """constructor

        @type value: mpz
        @param value: the ciphertext

        @type nsq: mpz
        @param nsq: n*n
        """

        value = kwargs.get("val", None)
        bitlen = kwargs.get("bitlen", None)

        super(Paillier, self).__init__(**kwargs)
        self.overwrite_ok = True
        # if isclient():
        #            self.on_tasty_op.append(self._create_shadow_copy)

        enc = kwargs.get("enc", True)
        hom_key = state.key._key
        self._key = state.key
        self._signed = kwargs['signed']

        if type(value) == PartyAttribute or value is None:
            self._value = None
        else:
            if isinstance(value, Unsigned):
                if value._value >= hom_key.n:
                    raise ValueError("Value too big for homomorphic value")
                _value = value._value
                assert self._signed == False
            elif isinstance(value, Signed):
                _value = value._value
                assert self._signed == True
                if abs(_value) >= hom_key.n_half:
                    raise ValueError(
                        "magnitude of value too big for signed homomorphic value")
                if _value < 0:
                    # _value is negativ, so + (value) is actual -value
                    _value = hom_key.n + _value
            elif isinstance(value, Paillier):
                _value = value._value
                enc = False
                assert self._signed == value._signed
            elif isinstance(value, Modular):
                assert self._signed == False
                _value = value._value
            elif isinstance(value, _mpz):
                #state.log.debug("Warning: creating homomorphic value from mpz")
                _value = value
            else:
                raise TypeError("wrong argument provided for Paillier: %s"
                                % type(value))
            self._value = encrypt(_value, hom_key) if enc else _value

        assert hasattr(self, "_key")
        assert isinstance(self._key, key.PublicKey) or isinstance(self._key, key.SecretKey)

    def validate(self):
        pass  # we cannot validate as we do not have any information about our content

    def get_bitlen(self):
        return self._bit_length

    def __int__(self):
        return int(decrypt(self._value, self._key._key))

    def __long__(self):
        try:
            return long(decrypt(self._value, self._key._key))
        except AttributeError, e:
            return 0L

    def signed(self):
        return self._signed

    def __add__(self, other):
        return_rec = Paillier.returns("__add__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]

        if isinstance(other, Paillier):
            return Paillier(val=add(self._value, other._value, self._key._key), enc=False, bitlen=return_rec["bitlen"],
                            signed=return_rec["signed"])
        elif other.signed():
            return Paillier(val=encrypt_sub(-other._value, self._value, self._key._key), enc=False,
                            bitlen=return_rec["bitlen"], signed=return_rec["signed"])
        else:
            return Paillier(val=encrypt_add(other._value, self._value, self._key._key), enc=False,
                            bitlen=return_rec["bitlen"], signed=return_rec["signed"])

    __radd__ = __add__

    def __iadd__(self, other):
        return_rec = Paillier.returns("__add__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]
        self._bit_length = return_rec["bitlen"]
        if isinstance(other, Paillier):
            self._value = add(self._value, other._value, self._key._key)
        else:
            self._value = encrypt_add(other._value, self._value, self._key._key)
        return self

    def __sub__(self, other):
        return_rec = Paillier.returns("__sub__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]
        if isinstance(other, Paillier):
            return Paillier(val=sub(self._value, other._value, self._key._key), enc=False, bitlen=return_rec["bitlen"],
                            signed=return_rec["signed"])
        else:
            return Paillier(val=encrypt_sub(other._value, self._value, self._key._key), enc=False,
                            bitlen=return_rec["bitlen"], signed=return_rec["signed"])

    def __isub__(self, other):
        return_rec = Paillier.returns("__sub__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]
        self._bit_length = return_rec["bitlen"]
        if isinstance(other, Paillier):
            self._value = sub(self._value, other._value, self._key._key)
        else:
            self._value = encrypt_sub(other._value, self._value, self._key._key)
        return self

    def __lshift__(self, value):
        return Paillier(val=self._value << value, enc=False, bitlen=self._bit_length + 1, signed=return_rec["signed"])

    def __mul__(self, other):
        """Multiplication in ciphertext space

        @type other: integer
        @param other: scalar to multiply

        @rtype: Paillier
        @return: product ciphertext
        """

        other_bits = other.bit_length()
        return_rec = Paillier.returns("__mul__", (type(other),), (self._bit_length, other_bits), ([1], [1]),
                                      (self._signed, other.signed()))[0]

        if isinstance(other, PlainType):
            return Paillier(val=encrypt_mul(self._value, other._value, self._key._key), enc=False,
                            bitlen=return_rec["bitlen"], signed=return_rec["signed"])
        elif isinstance(other, Paillier):
            if self.parent.role == Party.CLIENT:
                warnings.warn("Multiplication of two Homomorphics on side that knows the key")
                if self._signed:
                    x = Signed(val=self)
                else:
                    x = Unsigned(val=self)

                if other.signed():
                    y = Signed(val=other)
                else:
                    y = Unsigned(val=other)
                return Paillier(val=x * y, signed=return_rec["signed"])

            multproto = tasty.protocols.homomorphic_mult.HomomorphicMultiplication(state.active_party, (self, other))

            if isserver():
                multproto((self, other))
                return tuple(multproto.get_results())[0]
            else:  # client
                multproto((self, other))
                tuple(multproto.get_results())
                return self

        else:
            raise ValueError("Multiplication of Homomorphic and %s not supported" % type(other))

    __rmul__ = __mul__

    def __imul__(self, other):
        """Inplace multiplication in ciphertext space

        @type other: integer
        @param other: scalar to multiply

        @rtype: Paillier
        @return: reference to self
        """
        # FIXME multiiplication protocol
        return_rec = Paillier.returns("__mul__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]
        self._bit_length = return_rec["bitlen"]

        raise NotImplementedError("BITLEN MISSING!!!!")

        self._value = encrypt_mul(self._value, other._value, self._key._key)
        return self

    def __div__(self, other):
        """Division in ciphertext space

        @type other: integer
        @param other: scalar to divide self

        @rtype: Paillier
        @return: divided ciphertext
        """
        # FIXME multproto for cipher / cipher

        return_rec = Paillier.returns("__div__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]

        return Paillier(val=encrypt_div(self._value, other._value, self._key._key), enc=False,
                        bitlen=return_rec["bitlen"])

    def __idiv__(self, other):
        """Inplace division in ciphertext space

        @type other: integer
        @param other: scalar to divide self

        @rtype: Paillier
        @return: reference to self
        """
        # FIXME multproto for cipher /= cipher2

        return_rec = Paillier.returns("__div__", (type(other),), (self._bit_length, other.bit_length()), ([1], [1]),
                                      (self.signed(), other.signed()))[0]
        self._bit_length = return_rec["bitlen"]
        self._value = encrypt_div(self._value, other._value, self._key._key)
        return self

    def __getstate__(self):
        r = super(Paillier, self).__getstate__()
        r['_signed'] = self._signed
        r['_value'] = self._value.binary()
        return r

    def __setstate__(self, _state):
        super(Paillier, self).__setstate__(_state)
        self._value = mpz(_state['_value'], 256)
        self._signed = _state['_signed']
        self._key = state.key

    def __eq__(self, other):
        if self._value is None:
            return other is None
        elif other is None:
            return False
        else:
            raise TastySyntaxError("Tasty cannot compare homomorphically encrypted values")

    def __str__(self):
        """String representation

        @rtype: str
        """

        return "<Paillier(%r)>" % self._value

    def __repr__(self):
        """Formal string representation

        @rtype: str
        """

        return "Paillier(val=%r, bitlen=%d, signed=%s)" % (self._value, self._bit_length, self._signed)

    def input(self, src, desc="Paillier input"):
        value = None
        if callable(src):
            value = callable(desc)
        elif src:
            value = cPickle.load(open(src, "b"))
        else:
            value = int(raw_input(desc + ": "))
        self._value = encrypt(value, self._key._key)
        return self

    def serialize(self):
        """Serializes the PaillierPaillier

        @rtype: tuple(str, str)
        @return: a tuple of
        """

        return self._value.binary()


    @staticmethod
    def deserialize(t):
        """Deserializes a PaillierPaillier from a binary representation

        @type t: tuple(str, str)
        @param t: value and nsq as binary strings
        """

        return Paillier(mpz(t[0], 256))


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Paillier.calc_costs(%r, %r, %r, %r, %r, %r, %r)", input_types, bit_lengths, role, passive,
                            methodname, precompute, dims)

        if methodname == "Paillier":
            if issubclass(input_types[0], PlainType):
                return {"Enc": 1}
            else:
                raise NotImplementedError("Constructing garbled from %s" % str(input_types))
        if methodname == "__mul__":
            if issubclass(input_types[0], HomomorphicType):
                if passive:
                    return {"Enc": 1}
                return {"Enc": 2}

        return Paillier.costs[methodname]

    @staticmethod
    def affects(methodname, input_types, role):
        if __debug__:
            state.log.debug("Paillier.affects(%r, %r, %r)", methodname, input_types, role)
            # if methodname == "Paillier" and role == Party.SERVER:
            #return Value.S_ONLINE | Value.C_ONLINE
        if methodname == "__mul__" and role == Party.SERVER and issubclass(input_types[0], Paillier):
            return Value.S_ONLINE | Value.C_ONLINE
        return Value.affects(methodname, input_types, role)

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("Paillier.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims, signeds)
        if input_types and input_types[0] == tasty.types.Modular:
            return ({"type": Homomorphic, "bitlen": bit_lengths[1], "dim": [1, ], "signed": False},)
        if methodname == "Paillier":
            return ({"type": Homomorphic, "bitlen": bit_lengths[0], "dim": [1, ], "signed": signeds[0]},)
        elif methodname in ("__add__", "__iadd__"):
            return ({"type": Homomorphic, "bitlen": max(bit_lengths) + 1, "dim": [1, ], "signed": any(signeds)},)
        elif methodname in ("__sub__", "__isub__"):
            return ({"type": Homomorphic, "bitlen": max(bit_lengths) + 1, "dim": [1, ], "signed": any(signeds)},)
        elif methodname in ("__mul__", "__imul__"):
            return (
            {"type": Homomorphic, "bitlen": bit_lengths[0] + bit_lengths[1], "dim": [1, ], "signed": any(signeds)},)
        elif methodname in ("__div__", "__idiv__"):
            return ({"type": Homomorphic, "bitlen": bit_lengths[0], "dim": [1, ], "signed": any(signeds)},)
        elif methodname == "__neg__":
            return ({"type": Homomorphic, "bitlen": bit_lengths[0], "dim": [1, ], "signed": not any(signeds)},)
        else:
            raise NotImplementedError("Paillier.returns() not implemented for methodname %r" % methodname)

    def _decrypt(self, signed=False):
        key = self._key._key
        value = decrypt(self._value, key)
        if signed and value > key.n_half:
            return value - key.n
        return value

    def blind(self):
        # FIXME: statistic security parameter
        numbits = state.config.symmetric_security_parameter
        blind_value = Unsigned(val=rand.randint(1 << self._bit_length,
                                                # if signed, this ensures that there is no negative value with
                                                # negliable (2^{-l}) bits of security-loss
                                                1 << (numbits + self._bit_length) - 1),
                               bitlen=self._bit_length + numbits)
        self._signed = False
        self += blind_value
        return blind_value


class PaillierVec(Vec):
    """Holds a sequence of Paillier objects

    @group operators: __add__, __sub__, __mul__, componentmult
    @group serialization: deserialize, serialize
    """
    _type = Paillier


    def __init__(self, **kwargs):
        super(PaillierVec, self).__init__(**kwargs)

    def __getstate__(self):
        """Serializes a PaillierVec"""
        d = super(PaillierVec, self).__getstate__()
        d["val"] = [x._value and x._value.binary() or None
                    for x in self]
        return d

    def __setstate__(self, state):
        """Serializes a PaillierVec"""

        super(PaillierVec, self).__setstate__(state)
        self[:] = imap(lambda x: Paillier(val=mpz(x, 256), enc=False, bitlen=self._bit_length, signed=self._signed),
                       state['val'])


    def __sub__(self, other):
        """Subtration"""

        if not isinstance(other, PaillierVec):
            raise TypeError("You can only add two PaillierVecs.")

        if len(other) != len(self):
            raise ValueError("You can only add vectors of equal size.")
        return PaillierVec(self[x] - other[x] for x in xrange(len(self)))

    def __mul__(self, other):
        """Componentwise multiplication"""
        if isinstance(other, PlainVec):
            if len(self) != len(other):
                raise ValueError(
                    "you can only componentmultiply vectors of equal size")
            return PaillierVec(val=nogen(i * j for i, j in zip(self, other)), dim=self._dim,
                               bitlen=self._bit_length + other.bit_length(), signed=self._signed ^ other.signed())
        elif isinstance(other, Plain):
            return PaillierVec(val=nogen(i * other for i in self), dim=self._dim,
                               bitlen=self._bit_length + other.bit_length(), signed=self._signed ^ other.signed())
        elif isinstance(other, PaillierVec):
            cmultproto = tasty.protocols.homomorphic_mult.HomomorphicComponentMultiplication(state.active_party, self,
                                                                                             other)
            if len(other) != len(self):
                raise ValueError(
                    "you can only componentmultiply vectors of equal size")
            if self.parent.party.role != Party.SERVER:
                raise NotImplementedError("Componentmultiplication on client side not implemented")

            if state.active_party.role == Party.SERVER:
                cmultproto((self, other))
                res = nogen(cmultproto.get_results())[0]
                return res
            else:
                cmultproto((self, other))
                nogen(cmultproto.get_results())
                return None
        else:
            raise NotImplementedError()

    def dot(self, other):
        """Multiplies self with another L{PaillierVec}

        @type other: PaillierVec
        @param other: the 2nd PaillierVec
        @rtype: PaillierVec
        @return: the product of self and other

        @note: this is a critical function, therefor it is inlined instead
        of using the multiply function
        """

        if isinstance(other, PaillierVec):

            if other.dim() != self._dim:
                raise ValueError(
                    "you can only scalarmultiply vectors of equal size")
            if self.parent.role != Party.SERVER:
                raise NotImplementedError()

            smultproto = tasty.protocols.homomorphic_mult.HomomorphicScalarMultiplication(state.active_party,
                                                                                          (self, other))

            if state.active_party.role == Party.SERVER:
                smultproto((self, other))
                res = tuple(smultproto.get_results())[0]
                return res
            else:
                smultproto((self, other))
                tuple(smultproto.get_results())
                return Paillier(bitlen=(self._bit_length + other.bit_length() + ceilog(self._dim[0])), val=None,
                                signed=any((self._signed, other.signed())))

        else:
            return super(PaillierVec, self).dot(other)


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("PaillierVec.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)
        dim = dims[0]
        if isinstance(dims, int):
            raise ValueError("type of dim is incorrect %s" % type(dims))
        if methodname == "PaillierVec":
            if input_types and issubclass(input_types[0], Vec):
                return {"Enc": reduce(operator.mul, dim)}
        elif methodname == "dot":
            if issubclass(input_types[0], PlainVec):
                return {"enc_mul": dim[0], "enc_add": dim[0]}
            elif issubclass(input_types[0], PaillierVec):
                assert len(dims[0]) == len(dims[1]) == 1, "dot-multiplication not supported on multi-dimensional " \
                                                          "vectors"
                # FIXME, protocol costs!
                enclen0 = bit_lengths[0] + state.config.symmetric_security_parameter
                enclen1 = bit_lengths[1] + state.config.symmetric_security_parameter
                dpc0 = state.config.asymmetric_security_parameter // enclen0
                dpc1 = state.config.asymmetric_security_parameter // enclen1
                encs = int(math.ceil(dim[0] / float(dpc0)) + math.ceil(dim[0] / float(dpc1)))
                return {"enc_mul": dim[0], "enc_add": dim[0] + 1,
                        "Enc": encs}
        elif methodname == "__mul__":
            # FIXME!!!
            return {"enc_mul": dim[0]}
        elif methodname in ("__add__", "__sub__"):
            return {"enc_add": dim[0]}

        return dict()

    @staticmethod
    def affects(methodname, input_types, role):
        if __debug__:
            state.log.debug("PaillierVec.affects(%r, %r, %r)", methodname, input_types, role)
        if methodname in ("__mul__", "dot"):
            if issubclass(input_types[0], PaillierVec):
                if role == Party.SERVER:
                    return Value.S_ONLINE | Value.C_ONLINE
        if methodname == "PaillierVec":
            if not input_types:
                return Value.S_ONLINE | Value.C_ONLINE
        return Value.affects(methodname, input_types, role)

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("PaillierVec.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims,
                            signeds)
        dim = dims[0]
        if methodname == 'PaillierVec':
            return ({"type": PaillierVec, "bitlen": bit_lengths[0], "dim": dim, "signed": any(signeds)},)
        if methodname == '__getitem__':
            if len(dim) > 1:
                return ({"type": PaillierVec, "bitlen": bit_lengths[0], "dim": dim[1:], "signed": any(signeds)},)
            else:
                return ({"type": Paillier, "bitlen": bit_lengths[0], "dim": [1], "signed": any(signeds)},)
        elif methodname == '__add__':
            return ({"type": PaillierVec, "bitlen": max(bit_lengths) + 1, "dim": dim, "signed": any(signeds)},)
        elif methodname == '__mul__':
            return ({"type": PaillierVec, "bitlen": sum(bit_lengths), "dim": dim, "signed": any(signeds)},)
        if methodname == "dot":
            return ({"type": Paillier, "bitlen": bit_lengths[0] + bit_lengths[1] + ceilog(dim[0]), "dim": [1],
                     "signed": any(signeds)},)

        raise NotImplementedError("returns() not implemented for PaillierVec.%s()" % methodname)

    def input(self, src=None, desc=""):
        if not src:
            raise NotImplementedError()
        self = cPickle.load(file(src, "rb"))
        return self

    def blind(self):
        blind_values = [i.blind() for i in self]
        self._bit_length = self[0].bit_length()
        if __debug__:
            self.validate()
        return blind_values


    def unblind(self, blind_values):
        for i, j in zip(self, blind_values):
            i -= j


    def pack(self, maxlen=0, force_bitlen=None):
        """Packing Paillier Values with Horner's scheme"""
        # FIXME: len of ciphertext-space
        if maxlen <= 0:
            maxlen = state.config.asymmetric_security_parameter + maxlen

        if force_bitlen:
            diff = self._bit_length - force_bitlen
            bitlen = force_bitlen
        else:
            diff = 0
            bitlen = self.bit_length()
        packed = []
        cur = Unsigned(val=0, bitlen=0)

        if len(self._dim) > 1:
            raise NotImplementedError("Packing for multidimensional vectors not implemented yet")
        for i in self:
            tmpsigned = i.signed()
            if i.signed():
                i = i + Unsigned(val=1 << (bitlen - 1), bitlen=bitlen)  # shift into positive range
                i.set_bit_length(i.bit_length() - 1)
                i._signed = False

            if bitlen <= maxlen - cur.bit_length():
                cur = cur * Unsigned(val=1 << bitlen, bitlen=bitlen + 1)
                i._bit_length = bitlen
                cur = cur + i
                i._bit_length += diff
                cur.set_bit_length(cur.bit_length() - 2)  # We generated it so that overflows will never happen
            else:
                packed.append(cur)
                cur = i
            i._signed = tmpsigned

        packed.append(cur)
        return packed, self._bit_length, self._dim[0]

    def encrypt_parallel(self, values, concurrency=2):
        def _p_r(items, queue):
            """interal method"""
            queue.put([Paillier(item) for item in items])

        count = len(values) / concurrency
        data = chunks(values, count)

        data = chunks(values, len(values) / concurrency)

        queue = multiprocessing.Queue()
        procs = tuple(multiprocessing.Process(
            target=lambda: _p_r(p, queue))
                      for p in data)

        res = []
        for ix, process in enumerate(procs):
            process.start()

        for process in procs:
            res.extend(queue.get())
            process.join()
        return res


Homomorphic = None
HomomorphicVec = None


class Garbled(GarbledType):
    comparision_methods = ("__lt__", "__le__", "__gt__", "__ge__", "__eq__", "__ne__", "And", "Or", "Not")

    # Server must store the zero values in order to decrypt stuff
    # later on, this is stored in this class-variable list
    zero_values = []

    class CTuple(tuple):
        pass


    def __init__(self, **kwargs):
        """Initializes tasty Garbled object.

        @type bit_length: int
        @param bit_length: sets the maximum bit length for this instance

        @type value: Plain | Paillier | tuple | mpz
        @param value: the initial value of this instance

        @type gid: int
        @param type: the garbled id, if zero_values are already computed

        @type passive: bool
        @param passive: automatically set by the code analysis, is only helper or active side?
        """
        bitlen = kwargs.get("bitlen", None)
        val = kwargs.get("val", None)
        super(Garbled, self).__init__(**kwargs)

        if isinstance(val, Value):
            # if val.signed():
            #    #FIXME: @Immo
            #    raise ImplementationError("TASTY currently does not support multiplication with signed values within
            #  garbled circuits yet.")
            self._signed = val.signed()
        if isserver():
            self.on_overwrite.append(self.__preserve_gid)
        else:
            self.gid = 0

        self._value = []

        self.obj = val

        gid = kwargs.get("gid", None)
        self.empty = kwargs.get("empty", None)
        self._signed = kwargs['signed']
        if self.empty:
            return
        if type(gid) != type(None):
            self.gid = gid
            if val is not None :
                if not state.precompute and len(val) != self._bit_length:
                    raise ValueError("Specified length does not match with length of value")
        else:
            # if we don't have any gid, we must
            # defer construction until atteched to party
            self.on_attach.append(self._defered_init)

        self._passive = kwargs.get("passive", None)
        if __debug__:
            self.validate()

    def get_value(self):
        return self._value

    def _defered_init(self):
        value = self.obj

        del self.obj
        self.on_attach.remove(self._defered_init)


        # if we have a NoneType or a PartyAttribute or a PlainType
        if type(value) == type(None) or type(value) == PartyAttribute or isinstance(value, PlainType):
            if isserver():
                if state.precompute:
                    self.gid = self.create_zero_values(bitlen=self._bit_length)
                else:
                    # if self.parent == state.active_party:
                    if not self._passive:
                        if type(self._signed) == type(None):
                            self._signed = value.signed()
                        if value is None:
                            raise ValueError("Cannot convert %s to %s" % ("NoneType", Garbled))
                        self._value[:] = plain2garbled(value2bits(value.get_value(), self._bit_length),
                                                       Garbled.get_zero_value(self.gid), state.R)
                    else:
                        state.tasty_ot.next_ots(((i, i ^ state.R) for i in Garbled.get_zero_value(self.gid)))
            else:  # client
                if state.precompute:
                    pass
                    #raise InternalError("client does not have to do precomputation on creation of garbled values")
                else:
                    self._value[:] = nogen(state.tasty_ot.next_ots(value2bits(value.get_value(), value.bit_length())))
        elif isinstance(value, HomomorphicType):
            raise TastySyntaxError("Converting between garbled and Homomorphic on same side does not make sense")
        elif isinstance(value, Garbled.CTuple):
            self._value[:] = value
        else:
            try:
                if not all(map(lambda x: isinstance(x, Garbled), value)):
                    raise TastySyntaxError(
                        "If constructing a Garbled from multiple values, you must give only Garbled Values")
                raise NotImplementedError("Construct garbled from multiple garbled")
            except TypeError:
                raise InternalError("cannot cast '%s' to %s" % (value.__class__, Garbled))
        if __debug__:
            self.validate()


    def __preserve_gid(self, other):
        try:
            if self.gid < 0:
                raise AttributeError()
        except AttributeError:
            # we do not have a gid or its smaller then zero
            try:
                self.gid = other.gid
            except AttributeError:
                pass


    def set_bit_length(self, l):
        if state.precompute:
            if isserver():
                Garbled.zero_values[self.gid] = Garbled.zero_values[self.gid][:l]
        else:
            self._value[:] = self._value[0:l]
        super(Garbled, self).set_bit_length(l)


    def _listgetitem(self, item):
        return self._value[item]

    def _listgetslice(self, start=None, end=None):
        return self._value[start:end]

    def __getitem__(self, item):
        if not isinstance(item, slice):
            item = slice(item, item + 1)
            length = 1
        else:
            try:
                length = len(xrange(item.start, item.stop, item.step))
            except TypeError:
                length = len(xrange(item.start, item.stop))

                if self._signed:
                    warnings.warn("You access slices of a signed Garbled, please note that all values are 2-compliment",
                                  UserWarningOnce)
        try:
            nval = Garbled.CTuple(self._value[item])
        except IndexError:
            if not state.precompute:
                raise
            nval = partyAttribute

        if isserver():
            if state.precompute:
                zv = self.get_zero_value(self.gid)[item]
                newgid = self.create_zero_values(values=zv)
                return Garbled(gid=newgid, bitlen=len(zv), val=nval, signed=False)
            else:
                return Garbled(val=nval, bitlen=len(nval), signed=False)
        return Garbled(bitlen=min((length, self._bit_length)), val=nval, signed=False)


    def __setitem__(self, item, val):
        self._value[item] = val
        if __debug__:
            self.validate()

    def __len__(self):
        return len(self._value)

    def validate(self):
        # if isserver():
        #            try:
        #                if not len(self.get_zero_value(self.gid)) == self._bit_length:
        #                    raise InternalError("bitlength does not equal length of zero bits (%d, %d)"%(len(
        # self.get_zero_value(self.gid)), self._bit_length))
        #            except AttributeError:
        #                pass
        if len(self) > 0:  # do we have any values?
            if not len(self) == self._bit_length:
                raise InternalError(
                    "Internal length does not equal given bitlength (%d, %d)" % (len(self), self._bit_length))

    def __lt__(self, other):
        circuit = CmpCircuit(self._bit_length, other.bit_length(), CmpCircuit.LESS, map_signed(self._signed),
                             map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    def __le__(self, other):
        circuit = CmpCircuit(self._bit_length, other.bit_length(), CmpCircuit.LESSEQUAL, map_signed(self._signed),
                             map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    def __gt__(self, other):
        circuit = CmpCircuit(self._bit_length, other.bit_length(), CmpCircuit.GREATER, map_signed(self._signed),
                             map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    def __ge__(self, other):
        circuit = CmpCircuit(self._bit_length, other.bit_length(), CmpCircuit.GREATEREQUAL, map_signed(self._signed),
                             map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    def __eq__(self, other):
        circuit = CmpCircuit(self._bit_length, other.bit_length(), CmpCircuit.EQUAL, map_signed(self._signed),
                             map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    def __and__(self, other):
        assert other.bit_length() == self._bit_length
        circuit = Bool2Circuit(self._bit_length, Bool2Circuit.AND)
        return self.__do_op2to1(other, circuit)

    def __invert__(self):
        circuit = NotCircuit(self._bit_length)
        return self._n21op(circuit, (self, ))

    def __mul__(self, other):
        if self._bit_length < other.bit_length():
            return other * self
        circuit = FastMultiplicationCircuit(self._bit_length, other.bit_length())
        return self.__do_op2to1(other, circuit)

    def __add__(self, other):
        if self._bit_length < other.bit_length():
            return other + self
        circuit = AddCircuit(self._bit_length, other.bit_length(), map_signed(self._signed), map_signed(other.signed()))
        return self.__do_op2to1(other, circuit)

    __radd__ = __add__


    def __sub__(self, other):
        if self.signed():
            raise NotImplementedError("We cannot sub with first operand possibly negative")
        circuit = SubCircuit(self._bit_length, other.bit_length(), map_signed(other.signed()))

        return self.__do_op2to1(other, circuit)

    def dropmsb_sub(self, other):
        if self.signed():
            raise NotImplementedError("We cannot sub with first operand possibly negative")
        circuit = SubCircuit(self._bit_length, other.bit_length(), map_signed(self._signed), DROP_MSB)
        return self.__do_op2to1(other, circuit)


    def unpack(self, mask, bitlen, chunk_bitlen, sign):
        dim = chunk_bitlen / bitlen
        circuit = UnpackCircuit(bitlen, dim, map_signed(sign))

        return GarbledVec(val=self._n2mop(circuit, (self, mask)), bitlen=bitlen, dim=[dim], signed=(sign == SIGNED))

    def __repr__(self):
        st = "used"
        try:
            bitlen = self._bit_length
        except AttributeError:
            bitlen = -1
        try:
            self.gid
            try:
                self._value[0]
            except IndexError:
                st = "precomputed"
        except AttributeError:
            st = "virgin"

        foo = ""
        if state.config.verbose >= 2:
            foo = "( Content: %s)" % str(self._value)
        return "<%s %d-bit Garbled object at 0x%x%s>" % (st, bitlen, id(self), foo)

    def mux(self, first, second):
        if self._bit_length != 1:
            raise TastySyntaxError("You can only use Mux on 1-bit Garbled Values")
        circuit = MuxCircuit(first.bit_length())
        if state.precompute:
            return self._n21op(circuit, (first, second, self))
        return self._n21op(circuit, (first, second, self))

    def _n2mop(self, circuit, invals):

        if state.precompute:
            out = circuit.outputs()
            if isserver():
                inputs = [Garbled.get_zero_value(x.gid) for x in invals]

                # First we must create the new garbled circuit with the zero values of the
                # garbled inputs on server side, client side will create the
                # counterpart of the protocol
                gc = GCProtocol(state.active_party, (circuit, state.R, inputs))
            else:
                gc = GCProtocol(state.active_party, (circuit,))

            # store the circuit in the gc object
            gc.circuit = circuit

            # precomputation results of the gc are the zero-values of the outputs on the
            # server, empty on the client
            pr = tuple(gc.get_precomputation_results())
            if isserver():
                gc.outputgids = gids = [tasty.types.Garbled.create_zero_values(values=zv) for zv in pr]
                otmp = [tasty.types.Garbled(gid=gid, bitlen=len(out[i][0]), signed=(out[i][2] == SIGNED)) for i, gid in
                        enumerate(gids)]

            else:
                otmp = [tasty.types.Garbled(gid=0, bitlen=len(out[0]), signed=False) for out in circuit.outputs()]

            # store the newly created gc protocol object in the party to be able to access
            # it at online phase again
            state.active_party.push_gc(gc)

            return otmp


        else:  # Online
            if isclient():
                invals = [x.get_value() for x in invals]
            gc = state.active_party.pop_gc()
            out = gc.circuit.outputs()
            if isserver():
                # server has nothing to do, force protocol-run
                gc(None)
                tuple(gc.get_results())
                return tuple(
                    tasty.types.Garbled(bitlen=len(out[i][0]), gid=gid, signed=(out[i][2] == SIGNED)) for i, gid in
                    enumerate(gc.outputgids))
            else:  #Client, the actual results...
                gc((gc.circuit, invals))
                # Generate a list of garbleds
                otmp = tuple(
                    tasty.types.Garbled(bitlen=len(out[i][0]), val=Garbled.CTuple(res), signed=(out[i][2] == SIGNED))
                    for i, res in enumerate(gc.get_results()))
                return otmp

    def _n21op(self, circuit, invals):
        ret = self._n2mop(circuit, invals)
        assert len(ret) == 1, "_n21op on circuit that returns more then one value"
        return ret[0]


    def __do_op2to1(self, other, circuit):
        return self._n21op(circuit, (self, other))


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("Garbled.calc_costs(%r, %r, %r, %r, %r, %r, %r)", input_types, bit_lengths, role, passive,
                            methodname, precompute, dims)
        if (precompute and (role == Party.CLIENT) and methodname == "Garbled" and issubclass(input_types[0],
                                                                                             PlainType)):
            return {"ot": bit_lengths[0]}
        if (precompute and role == Party.CLIENT or not precompute and role == Party.SERVER
        and methodname in ("__add__", "__sub__", "__gt__", "__lt__", "__ge__", "__le__", "__mul__")):
            return {}
        if precompute and methodname == "Garbled" and role == Party.SERVER and issubclass(input_types[0],
                                                                                          HomomorphicType):
            # FIXME: statistic security parameter!
            statistic_secparam = state.config.symmetric_security_parameter
            circuit = AddCircuit(statistic_secparam + bit_lengths[0] + 2, statistic_secparam + bit_lengths + 1,
                                 UNSIGNED, SIGNED)
            tmp = circuit.gate_types()
            tmp["ot"] = bit_lengths[0] + statistic_secparam + 2
            return tmp

        circuit = None
        if methodname == "__lt__":
            circuit = CmpCircuit(bit_lengths[0], bit_lengths[1], CmpCircuit.LESS, False, False)
        if methodname == "__gt__":
            circuit = CmpCircuit(bit_lengths[0], bit_lengths[1], CmpCircuit.GREATER, False, False)
        if methodname == "__mul__":
            circuit = FastMultiplicationCircuit(bit_lengths[0], bit_lengths[1])
        if circuit:
            return circuit.gate_types()
        return dict()


    @staticmethod
    def affects(methodname, input_types, role):
        if __debug__:
            state.log.debug("Garbled.affects(%r, %r, %r)", methodname, input_types, role)
        if methodname == "Garbled":
            if role == Party.CLIENT:
                if not input_types:
                    return 0
                elif issubclass(input_types[0], PlainType) or issubclass(input_types[0], HomomorphicType):
                    return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE | Value.S_ONLINE
            else:
                if not input_types:
                    return 0
                elif issubclass(input_types[0], PlainType):
                    return Value.S_SETUP | Value.S_ONLINE

        if methodname == "__getitem__" and role == Party.SERVER:
            return Value.S_SETUP | Value.S_ONLINE

        return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("Garbled.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims, signeds)
        if methodname == "Garbled":
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": signeds[0]},)
        elif methodname == "__add__":
            return ({"type": Garbled, "bitlen": max(bit_lengths) + 1, "dim": [1], "signed": any(signeds)},)
        elif methodname == "__sub__":
            return ({"type": Garbled, "bitlen": max(bit_lengths) - 1, "dim": [1], "signed": any(signeds)},)
        elif methodname == "__mul__":
            return ({"type": Garbled, "bitlen": bit_lengths[0] + bit_lengths[1], "dim": [1], "signed": any(signeds)},)
        elif methodname == "__div__":
            return ({"type": Garbled, "bitlen": bit_lengths[0] - bit_lengths[1], "dim": [1], "signed": any(signeds)},)
        elif methodname == "__neg__":
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": any(signeds)},)
        elif methodname == "__and__":
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": any(signeds)},)
        elif methodname == "mux":
            assert bit_lengths[0] == 1 and bit_lengths[1] == bit_lengths[
                2], "mux must operate with on bit control and equal-size inputs (%s)" % bit_lengths
            return ({"type": Garbled, "bitlen": bit_lengths[1], "dim": [1], "signed": any(signeds)},)
        elif methodname == "__invert__":
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": not any(signeds)},)
        elif methodname in Garbled.comparision_methods:
            return ({"type": Garbled, "bitlen": 1, "dim": [1], "signed": False},)
        else:
            raise NotImplementedError(methodname)


    def __getstate__(self):
        # we must only send if exists _value and the signed opera
        state = super(Garbled, self).__getstate__()
        state["_signed"] = self._signed
        try:
            self._value[0]
            state['_value'] = tuple(imap(lambda x: x.binary(), self._value))
        except IndexError:
            pass

        return state


    def __setstate__(self, state):
        super(Garbled, self).__setstate__(state)
        self._signed = state["_signed"]
        try:
            self._value = map(lambda x: mpz(x, 256), state["_value"])
        except KeyError:
            self._value = []
        self.gid = 0
        self.on_attach = []

    @staticmethod
    def create_zero_values(values=None, bitlen=None):
        """Create zero values and store them in the Garbled class list

        @param values: if zero value is already chosen (e.g. output of
        a circuit) it is not computed but stored instead
        @type values: tuple

        @param length: length of the garbled value
        @type length: int

        @rtype: int
        @returns: Gate ID"""

        gid = len(Garbled.zero_values)
        if values is None:
            if bitlen is None:
                raise ValueError("you must either specify length or values")
            values = generate_garbled_value(bitlen)
        Garbled.zero_values.append(tuple(values))
        return gid

    @staticmethod
    def get_zero_value(gid):
        """ gets zero value of gate with gate id gid """
        tmp = Garbled.zero_values[gid]
        # check wether we deal with a generator. If so, don't return it, but
        # unpack it first, store it unpacked in the list and return a copy
        if not isinstance(tmp, tuple):
            tmp = tuple(tmp)
            Garbled.zero_values[gid] = tmp
        return tmp

    def signed(self):
        return self._signed


class GarbledVec(Vec):
    _type = Garbled


    @staticmethod
    def affects(methodname, input_types, role):
        if __debug__:
            state.log.debug("GarbledVec.affects(%r, %r, %r)", methodname, input_types, role)
        if methodname in (
        "min_value_index", "max_value_index", "min_value", "max_value", "min_index", "max_index", "__add__", "__sub__",
        "dot", "__mul__"):
            return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE
        elif methodname == "__getitem__":
            return Value.S_ONLINE if role else Value.C_ONLINE
        elif methodname == "GarbledVec":
            if not input_types:
                return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE | Value.S_ONLINE
            if role == Party.CLIENT:
                if issubclass(input_types[0], PlainVec):
                    return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE | Value.S_ONLINE
                elif issubclass(input_types[0], HomomorphicVec) or issubclass(input_types[0], PaillierVec):
                    return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE | Value.S_ONLINE
            else:
                if issubclass(input_types[0], PlainVec):
                    return Value.S_SETUP | Value.S_ONLINE
                elif issubclass(input_types[0], HomomorphicVec) or issubclass(input_types[0], PaillierVec):
                    return Value.C_SETUP | Value.S_SETUP | Value.C_ONLINE | Value.S_ONLINE

        raise NotImplementedError("affects() not implemented for GarbledVec.%s(%r)" % (methodname, list(input_types)))


    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        if __debug__:
            state.log.debug("GarbledVec.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths,
                            dims, role, passive, precompute)

        if methodname == "GarbledVec" and (role == Party.CLIENT or role == Party.SERVER and passive):
            try:
                if isinstance(input_types[0], PlainVec):
                    return {"ot": dims[0] * bit_lengths[0]}
            except IndexError:
                return dict()
        elif methodname in ("min_value", "min_value_index", "max_value_index"):
            return dict()
        raise NotImplementedError(
            "calc_costs() not implemented for GarbledVec.%s(%s)" % (methodname, list(input_types)))

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        if __debug__:
            state.log.debug("GarbledVec.returns(%r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims,
                            signeds)

        if methodname == "GarbledVec":
            return ({"type": GarbledVec, "bitlen": bit_lengths[0], "dim": dims[0], "signed": signeds[0]},)
        elif methodname in ("min_value", "max_value", "min_index", "max_index"):
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": any(signeds)},)
        elif methodname in ("min_value_index", "max_value_index"):
            return ({"type": Garbled, "bitlen": bit_lengths[0], "dim": [1], "signed": any(signeds)},
                    {"type": Garbled, "bitlen": ceilog(dims[0][0]), "dim": [1], "signed": False},)
        elif methodname == "__add__":
            return ({"type": GarbledVec, "bitlen": max(bit_lengths) + 1, "dim": dims[0], "signed": any(signeds)}, )
        elif methodname == "__sub__":
            return ({"type": GarbledVec, "bitlen": max(bit_lengths), "dim": dims[0], "signed": any(signeds)}, )
        elif methodname == "__getitem__":
            if len(dims[0]) > 1:
                newtype = GarbledVec
                newdim = dims[0][1:]
            else:
                newtype = Garbled
                newdim = dims = [1]
            return ({"type": newtype, "bitlen": bit_lengths[0], "dim": newdim, "signed": any(signeds)},)
        else:
            raise NotImplementedError(
                "returns() not implemented for GarbledVec.%s(%s)" % (methodname, list(input_types)))


    def _n2mop(self, circuit, invals):

        if state.precompute:
            out = circuit.outputs()
            if isserver():
                inputs = [Garbled.get_zero_value(x.gid) for x in invals]

                # First we must create the new garbled circuit with the zero values of the
                # garbled inputs on server side, client side will create the
                # counterpart of the protocol
                gc = GCProtocol(state.active_party, (circuit, state.R, inputs))
            else:
                gc = GCProtocol(state.active_party, (circuit,))

            # store the circuit in the gc object
            gc.circuit = circuit

            # precomputation results of the gc are the zero-values of the outputs on the
            # server, empty on the client
            pr = tuple(gc.get_precomputation_results())
            if isserver():
                gc.outputgids = gids = [tasty.types.Garbled.create_zero_values(values=zv) for zv in pr]
                otmp = [tasty.types.Garbled(gid=gid, bitlen=len(out[i][0]), signed=(out[i][2] == SIGNED)) for i, gid in
                        enumerate(gids)]

            else:
                otmp = [tasty.types.Garbled(gid=0, bitlen=len(out[0]), signed=False) for out in circuit.outputs()]

            # store the newly created gc protocol object in the party to be able to access
            # it at online phase again
            state.active_party.push_gc(gc)

            return otmp


        else:  # Online
            if isclient():
                invals = [x.get_value() for x in invals]
            gc = state.active_party.pop_gc()
            out = gc.circuit.outputs()
            if isserver():
                # server has nothing to do, force protocol-run
                gc(None)
                tuple(gc.get_results())
                return tuple(
                    tasty.types.Garbled(bitlen=len(out[i][0]), gid=gid, signed=(out[i][2] == SIGNED)) for i, gid in
                    enumerate(gc.outputgids))
            else:  #Client, the actual results...
                gc((gc.circuit, invals))
                # Generate a list of garbleds
                otmp = tuple(
                    tasty.types.Garbled(bitlen=len(out[i][0]), val=Garbled.CTuple(res), signed=(out[i][2] == SIGNED))
                    for i, res in enumerate(gc.get_results()))
                return otmp

    def _n21op(self, circuit, invals):
        ret = self._n2mop(circuit, invals)
        assert len(ret) == 1, "_n21op on circuit that returns more then one value"
        return ret[0]

    def min_value_index(self):
        c = MinMaxValueIndexCircuit(self._dim[0], self.bit_length(), MinMaxValueIndexCircuit.MIN,
                                    map_signed(self._signed))
        return self._n2mop(c, reversed(self))  # FIXME: Why reversed?

    def min_index(self):
        c = MinMaxIndexCircuit(self._dim[0], self.bit_length(), MinMaxValueIndexCircuit.MIN, map_signed(self._signed))
        return self._n2mop(c, reversed(self))  # FIXME: Why reversed?

    def min_value(self):
        c = MinMaxValueCircuit(self._dim[0], self.bit_length(), MinMaxValueCircuit.MIN, map_signed(self._signed))
        return self._n2mop(c, reversed(self))[0]

    def max_value_index(self):
        c = MinMaxValueIndexCircuit(self._dim[0], self.bit_length(), MinMaxValueIndexCircuit.MAX,
                                    map_signed(self._signed))
        return self._n2mop(c, reversed(self))  # FIXME: Why reversed?

    def max_index(self):
        c = MinMaxIndexCircuit(self._dim[0], self.bit_length(), MinMaxValueIndexCircuit.MAX, map_signed(self._signed))
        return self._n2mop(c, reversed(self))  # FIXME: Why reversed?

    def max_value(self):
        c = MinMaxValueCircuit(self._dim[0], self.bit_length(), MinMaxValueCircuit.MAX, map_signed(self._signed))
        return self._n2mop(c, self)[0]

