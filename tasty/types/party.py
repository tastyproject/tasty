# -*- coding: utf-8 -*-

import operator
import warnings
from collections import deque

import tasty.types
import tasty.types.driver
import tasty.types.metatypes

from tasty.protocols import transport
from tasty.exc import *
from tasty import cost_results, state, exc
from tasty.utils import get_random, bit2byte
from tasty.fmt_utils import *

def party_name(party):
    p = ("CLIENT", "SERVER")
    return p[party.role]

def isserver(party=None):
    if party is None:
        return state.active_party.role == Party.SERVER
    else:
        return party.role == Party.SERVER

def isclient(party=None):
    return not isserver(party)


class PartyAttribute(object):
    def __init__(self, **kwargs):
        parent = kwargs.get("parent", None)
        name = kwargs.get("name", None)
        indirect = kwargs.get("indirect", False)
        self.nonexistant = kwargs.get("nonexistant", False)

        self.name_at_parent = None

        try:
            iter(self.on_attach)
        except (AttributeError, TypeError):
            self.on_attach = []
        try:
            iter(self.on_overwrite)
        except (AttributeError, TypeError):
            self.on_overwrite = []
        try:
            self.overwrite_ok = kwargs['overwrite_ok']
        except KeyError:
            try:
                self.overwrite_ok
            except AttributeError:
                self.overwrite_ok = False

        if parent:
            self.parent = parent
        else:
            try:
                self.parent
            except AttributeError:
                self.parent = None

        if indirect and name and parent:
            # we got indirectly created by getattr, save the
            # result to the parent object

            setattr(parent, name, self)

    def __getstate__(self):
        return None

    def __setstate__(self, param):
        pass

    def __repr__(self):
        try:
            return "<PartyAttribute object (at %s) %s>"%(self.parent, self.name_at_parent)
        except AttributeError:
            return super(PartyAttribute, self).__repr__()

    def __call__(self, *args, **kwargs):
        pass

    def bit_length(self):
        return tasty.types.metatypes.CompareTrue()

    def signed(self):
        return self._signed

    def validate(self):
        raise NotImplementedError()

    @staticmethod
    def affects(methodname, input_types, role):
        """returns a bitmask of all phases methodname with given inputs and role takes part.

        Use the class constants in :class:`tasty.types.Value':
        - :attr:`tasty.types.Value.C_SETUP
        - :attr:`tasty.types.Value.S_SETUP
        - :attr:`tasty.types.Value.C_ONLINE
        - :attr:`tasty.types.Value.S_ONLINE

        @type methodname: str
        @param methodname: the name of the method to report involved protocol phases.
        """

        if __debug__:
            state.log.debug("PartyAttribute.affects(%r, %r, %r)", methodname, input_types, role)
        return tasty.types.Value.S_ONLINE if role else tasty.types.Value.C_ONLINE

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        """Returns for named method for each returned object a tuple of (return type, bit length, dimension, signed)
        with types (type, int, list[int,...], bool)

        MUST be implemented for every :class:`tasty.types.party.PartyAttribute` subclass, otherwise
        the analyze-phase will generate wrong results

        @type methodname: str
        @param methodname: the name of the method to inform about returned objects metadata

        @rtype: tuple(dict, ...)
        @return:
        """
        raise NotImplementedError()

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        """Must be implemented for each type. This should return an empty dict
        as simplest incarnation of a custom tasty value type.

        @type methodname: str
        @param methodname: the name of the method to report the costs

        @type input_types: list
        @param input_types: the type of all relevant acutal parameters

        @type bit_lengths: list
        @param bit_lengths: the bitlength of the called type and all relevant actual parameters

        @type dims: list
        @param dims: the dminension of the called type and all relevant actual parameters

        @type role: int
        @param role: if its bound to client or server party. use :attr:`Party.CLIENT` or :attr:`Party.SERVER` constants

        @type passive: bool
        @param passive: if the method is been called on the active/this or passive/other party

        @type precompute: bool
        @param precompute: if the method is been called in setup or online phase
        """
        raise NotImplementedError()

class PartyBase(object):
    """Base class for Party objects"""

    CLIENT = 0
    SERVER = 1

    def __init__(self, role):
        self.__gc = deque()
        self.__tmpattr = deque()
        self.__tmpval = deque()
        self.role = role


    def push_tmpattr(self, value):
        state.log.debug("pushing temporary attribute: %r", value)

        value.parent = self
        value.precomp_value = state.precompute
        value.name_at_parent = None
        for afunc in value.on_attach:
            afunc()

        self.__tmpattr.append(value)

    def pop_tmpattr(self):
        ret = self.__tmpattr.popleft()
        state.log.debug("popping temporary attribute: %r", ret)
        return ret


    def push_tmpval(self, value):
        self.__tmpval.append(value)

    def pop_tmpval(self):
        return self.__tmpval.popleft()

    def push_gc(self, gc):
        self.__gc.append(gc)

    def pop_gc(self):
        return self.__gc.popleft()


    def __setattr__(self, name, obj):
        """
        when a value is either attached to server or client,
        there may be additional action necessary
        """

        try:
            # do we overwrite something?
            tmp = super(PartyBase, self).__getattribute__(name)
            if ((not state.precompute) and tmp.precomp_value) or tmp.overwrite_ok or name == "_tmp_":
                if type(tmp) == type(obj):
                    for ofunc in obj.on_overwrite:
                        ofunc(tmp)
            else:
                raise TastySyntaxError("Overwriting %r that forbids overwriting", name)
        except AttributeError, e:
            # nothing to be overwritten, \o/
            pass



        if isinstance(obj, tasty.types.PartyAttribute):
            # each PartyAttribute should have a parent to access its parent
            # party.
            #setattr(obj, "parent", self)
            obj.parent = self
            try:
                obj.precomp_value
            except AttributeError:
                if state.precompute:
                    obj.precomp_value = True
                else:
                    obj.precomp_value = False
            obj.name_at_parent = name

            # maybe there is an defered constructor that requires knowledge
            # of its parent, call it
            if __debug__:
                state.log.debug("attaching %r as %s, running on_attach (%r)", obj, name, obj.on_attach)
            for afunc in obj.on_attach:
                afunc()

        super(PartyBase, self).__setattr__(name, obj)

    def __getattr__(self, name):
        """If there is no such attribute in this object, give a plain
        L{PartyAttribute} instead of raising AttributeError"""

        return PartyAttribute(parent=self, indirect=True, name=name, nonexistant=True)



class Party(PartyBase):
    """ Represents client and server"""
    _format_types = "#bcdeEfFgGnosxX%"

    def __init__(self,
        role,
        socket=None,
        server_socket=None):
        super(Party, self).__init__(role)
        self._sock = socket
        self._server_sock = server_socket

    def server_socket(self):
        return self._server_sock


    def set_socket(self, socket):
        self._sock = socket

    def socket(self):
        return self._sock

    def output(self, attribute, dest=None, desc=None, fmt=None):
        #if fmt and fmt not in self._format_types:
        #raise ValueError("fmt specifier must be one of {0}".format(self._format_types))
        if dest:
            if isinstance(dest, tasty.types.driver.Driver):
                if not desc:
                    raise TastySyntaxError("You must specify description when outputting into a driver")
                dest.next_output(attribute, desc=desc, fmt=fmt)
                return
            elif callable(dest):
                dest(attribute, desc, fmt)
                return
            elif isinstance(dest, basestring):
                f = open(dest, "w").write(format_output(attribute, desc, fmt) + "\n")
                return
        else:
            state.log.critical(format_output(attribute, desc=desc, fmt=fmt))

    def __repr__(self):
        return "<%s party>"%party_name(self)

    setup_output = output

class PassiveParty(PartyBase):
    """dummy class"""

partyAttribute = PartyAttribute()

#from tasty.types import *
#import tasty.types.party
#p = tasty.types.party.Party(None, None, None)
#s = "hällo"
#u = Unsigned(bitlen=8, val=8)
#p.output(u, desc="narf", fmt="#X")
#p.output(u, fmt="#X")
#p.output(u, desc="narf")

#p.output(s, fmt="r")
#p.output(s, desc="narf")
