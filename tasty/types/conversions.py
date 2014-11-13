# -*- coding: utf-8 -*-

import warnings
import operator

from gmpy import mpz

from tasty.exc import UserWarningRepeated, UserWarningOnce

import tasty.types
from tasty.types import *
from tasty.types import PaillierVec, Paillier
from tasty.types.metatypes import Value
from tasty.types.party import Party
from tasty import state
from tasty import cost_results
from tasty.exc import TastySyntaxError, InternalError
from tasty.utils import bit2byte, rand, get_randomm, nogen, value2bits, bits2value, comp22int
from tasty.types.party import isserver, isclient, PartyAttribute, partyAttribute
from tasty.circuit.dynamic import AddCircuit
from tasty.circuit import SIGNED, UNSIGNED
from tasty.crypt.garbled_circuit import *
from tasty.protocols import transport, gc_protocols, protocol

## Helper functions (generic stuff)

def _set_dst(src, dst, new):
    dst.overwrite_ok = True
    setattr(dst.parent, dst.name_at_parent, new)

def _send(src, dst = None, bitlen=0, dim=0):
    t = transport.Transport(state.active_party)
    t((src,))
    tuple(t.get_results())

def _receive(src = None, dst = None):
    t = transport.Transport(state.active_party)
    t(tuple())
    t = tuple(t.get_results())[0]
    if type(t) == PartyAttribute:
        raise InternalError("received a PartyAttribute object should never happen")
    return t

def _cast_send(src, dst, dsttype, signed):
    tmp = dsttype(val=src, signed=signed)
    tmp._signed = signed
    _send(tmp)

def _receive_cast(src, dst, dsttype, bitlen, dim, signed):
    new = _receive(src, dst)
    new._bit_length = bitlen
    new._signed = signed
    new._dim = dim
    _set_dst(src, dst, dsttype(val=new))

def _sender_copy(src, dst):
    _set_dst(src, dst, src)

def _signed_receive(src, dst, bitlen, dim, signed):
    new = _receive()
    new._bit_length = bitlen
    new._dim = dim
    new._signed = True
    _set_dst(src, dst, new)


def _unsigned_receive(src, dst, bitlen, dim, signed):
    new = _receive()
    new._bit_length = bitlen
    new._dim = dim
    new._signed = False
    _set_dst(src, dst, new)


def _just_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_bitlen is not None:
        bitlen = force_bitlen
    new = _receive()
    new._bit_length = bitlen
    new._dim = dim
    if force_signed is not None:
        new._signed = force_signed
    _set_dst(src, dst, new)


def _just_receive_vec(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    new = _receive()
    if force_bitlen is not None:
        bitlen = force_bitlen

    new._bit_length = bitlen
    for i in new:
        if force_signed is not None:
            i._signed = force_signed
        i._bit_length = bitlen
    new._dim = dim
    _set_dst(src, dst, new)


def _dimtimes(dim):
    return reduce(operator.mul, dim, 1)

def _sendcost(bits):
    cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](Send=bit2byte(bits))


#########################################################
### Conversions with same type (just send the object) ###
#########################################################

### Scalar types
def Plain_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_signed is not None:
        raise TastySyntaxError("use Signed/Unsigned for determination of sign in Plain types")
    _sendcost(bitlen)
    _send(src)

Unsigned_Unsigned_send = Plain_send
Unsigned_Unsigned_receive = _just_receive
Signed_Signed_send = Plain_send
Signed_Signed_receive = _just_receive

def Modular_Modular_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_bitlen is not None or force_signed is not None:
        raise TastySyntaxError("Modular is always unsigned with bitlength of the asymmetric security parameter")
    _sendcost(state.config.asymmetric_security_parameter)
    _send(src, dst)

Modular_Modular_receive = _just_receive

def Paillier_Paillier_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):

    _sendcost(state.config.asymmetric_security_parameter * 2)
    _send(src, dst)
    _sender_copy(src, dst)

Paillier_Paillier_receive = _just_receive

def Garbled_Garbled_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    state.log.debug("Garbled_Garbled_send: %r, %r, %r, %r, %r, %r, %r)", src, dst, bitlen, dim, signed, force_bitlen, force_signed)
    if force_bitlen is not None:
        src = src[:force_bitlen]
    _sendcost(bitlen * (state.config.symmetric_security_parameter + 1))
    _send(src, dst)
    if isserver(): # server needs a shadow copy
        _sender_copy(src, dst)


def Garbled_Garbled_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    new = _receive(src, dst)
    if force_bitlen is not None:
        bitlen = force_bitlen
    #copy gid from servers shadow copy
    if isserver():
        if force_bitlen is not None:
            src = src[:force_bitlen]
        new.gid = src.gid

    new._bit_length = bitlen

    _set_dst(src, dst, new)

### Vector types
def PlainVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(bitlen * _dimtimes(dim))
    _send(src, dst)

UnsignedVec_UnsignedVec_send = PlainVec_send
UnsignedVec_UnsignedVec_receive = _just_receive_vec
SignedVec_SignedVec_send = PlainVec_send
SignedVec_SignedVec_receive = _just_receive_vec

def ModularVec_ModularVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_bitlen is not None or force_signed is not None:
        raise TastySyntaxError("Modular is always unsigned with bitlength of the asymmetric security parameter")
    _sendcost(state.config.asymmetric_security_parameter * _dimtimes(dim))
    _send(src, dst)

ModularVec_ModularVec_receive = _just_receive_vec
def PaillierVec_PaillierVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(state.config.asymmetric_security_parameter * 2 * _dimtimes(dim))
    _send(src, dst)
    _sender_copy(src, dst)

PaillierVec_PaillierVec_receive = _just_receive_vec

def GarbledVec_GarbledVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(_dimtimes(dim) * bitlen * (state.config.symmetric_security_parameter + 1))
    _send (src, dst)

GarbledVec_GarbledVec_receive = _just_receive_vec



##############################################################
### Conversions with different types (convert and/or send) ###
##############################################################

### Scalar Types
# encryptions

Unsigned_Signed_send = Plain_send

def Unsigned_Signed_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _receive_cast(src, dst, Signed, bitlen, dim)

Signed_Unsigned_send = Plain_send

def Signed_Unsigned_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _receive_cast(src, dst, Unsigned, bitlen, dim)

def Unsigned_Paillier_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(state.config.asymmetric_security_parameter * 2)
    if force_signed is not None:
        signed = force_signed
    _cast_send(src, dst, Paillier, signed)

Unsigned_Paillier_receive = _just_receive
Signed_Paillier_send = Unsigned_Paillier_send
Signed_Paillier_receive = _just_receive

def Plain_Garbled_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(bitlen * (state.config.symmetric_security_parameter + 1))
    if isclient():
        raise TastySyntaxError("Encrypting to Garbled and Sending to Server does not make sense")
    if state.precompute:
        tmp = Garbled(val=src, bitlen=bitlen, signed=signed)
        state.active_party.push_tmpattr(tmp)
    else:
        tmp = state.active_party.pop_tmpattr()
        tmp = Garbled(val=src, bitlen=bitlen, signed=signed)

    _sender_copy(tmp, dst) # attaches implicitly here
    _send(tmp)

Plain_Garbled_receive = _just_receive
Unsigned_Garbled_send = Plain_Garbled_send
Unsigned_Garbled_receive = Plain_Garbled_receive
Signed_Garbled_send = Plain_Garbled_send
Signed_Garbled_receive = Plain_Garbled_receive

# decryptions
def Paillier_Unsigned_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isclient():
        _sendcost(bitlen)
        _cast_send(src, dst, Unsigned)
    else:
        _sendcost(state.config.asymmetric_security_parameter)
        _send(src, dst)


def Paillier_Unsigned_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isserver():
        _just_receive(src, dst, bitlen, dim, signed)
    else:
        _receive_cast(src, dst, Unsigned, bitlen, dim, signed)


def Paillier_Signed_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isclient():
        _sendcost(bitlen)
        _cast_send(src, dst, Signed)
    else:
        _sendcost(state.config.asymmetric_security_parameter)
        _send(src, dst)


def Paillier_Signed_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isserver():
        _just_receive(src, dst, bitlen, dim, signed)
    else:
        _receive_cast(src, dst, Signed, bitlen, dim, signed)


def Garbled_Unsigned_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(bitlen)
    if isclient():
        if src.signed():
            warnings.warn("Loosing Signedness", UserWarningRepeated)
        _send((bits2value(permbits(src._value)), src.signed()))
    else:
        new = Unsigned(val=src)
        _sender_copy(new, dst) # atteches here
        _send(new)

def Garbled_Unsigned_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isserver():
        val, signed = _receive(src, dst)
        val = value2bits(val, bitlen)
        zv = permbits(Garbled.get_zero_value(src.gid))
        if signed:
            warnings.warn("Loosing Signedness", UserWarningRepeated)
            val = abs(bits2value(perm2plain(val, zv)))
        else:
            val = bits2value(perm2plain(val, zv))
        new = Unsigned(val=val, bitlen=bitlen)
        _set_dst(src, dst, new)
    else:
        _just_receive(src, dst, bitlen, dim, signed)

def Garbled_Signed_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(bitlen)
    if isclient():
        _send(bits2value(permbits(src._value)), src.signed())
    else:
        new = Signed(val=src)
        _sender_copy(new, dst) # atteches here
        _send(new)

def Garbled_Signed_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if isserver():
        val, signed = _receive(src, dst)
        val = value2bits(val, bitlen)
        zv = Garbled.get_zero_value(src.gid)
        val = bits2value(perm2plain(val, zv))
        new = Unsigned(val=val, bitlen=bitlen)
        _set_dst(src, dst, new)
    else:
        _just_receive(src, dst, bitlen, dim, signed)



# conversions
def Paillier_Garbled_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_bitlen is not None:
        diff = bitlen - force_bitlen
        bitlen = force_bitlen
    else:
        diff = 0

    masklen = bitlen + state.config.symmetric_security_parameter #
    p = partyAttribute
    if not isserver():
        raise TastySyntaxError("Conversion from Homomorphic to Garbled from Client to Server does not make sense")
    if state.precompute:
        if force_signed is not None:
            signed = force_signed

        if signed:
            mask = Unsigned(val=rand.randint(2**bitlen - 1, 2**masklen - 1), bitlen=masklen)
        # generate the Homomorphic blinding mask and store
        else:
            mask = Unsigned(val=rand.randint(0, 2**masklen - 1), bitlen=masklen)

        hmask = tasty.types.Homomorphic(val=mask, signed=False)
        state.active_party.push_tmpattr(hmask)
        # Generate the Garbled Blinding Mask
        mgm = Garbled(bitlen=bitlen, signed=False, val=p)
        mgm.plainmask = mask # save the mask to be able to access it in online phase
        state.passive_party.push_tmpattr(mgm) # save the new Garbled
        zv = Garbled.get_zero_value(mgm.gid)
        mgm[:] = plain2garbled(value2bits(mask.get_value() & ((1<<bitlen) - 1), bitlen), zv, state.R)
        _sendcost(state.config.symmetric_security_parameter * bitlen)
        _send(mgm)
        # Precompute the garbled for the masked plain value
        mgv = Garbled(bitlen=bitlen, passive=True, val=p, signed=False)
        state.passive_party.push_tmpattr(mgv)
        # prepare the addition circuit to remove the mask
        ret = mgv.dropmsb_sub(mgm)
        # save shadow copy of resulting Garbled
        _set_dst(src, dst, ret)
        ret.set_bit_length(bitlen)
        ret._signed = False # avoid warning here
    else:
        assert signed == src.signed(), "the analyzer disagrees with the typesystems signedness"
        if force_signed is not None:
            signed = force_signed

        hmask = state.active_party.pop_tmpattr()
        mgm = state.passive_party.pop_tmpattr()
        state.passive_party._tmp_ = state.passive_party.pop_tmpattr()
        # blind the homomorphic and send to other party
        hval = src + hmask
        hval._bit_length -= diff # force_bitlen
        _sendcost(state.config.asymmetric_security_parameter * 2)
        _send(hval)
        # help to encrypt the masked value into Garbled
        state.passive_party._tmp_ = Garbled(bitlen=masklen + 1, passive=True, val=p, signed=signed)
        # help removing the mask
        ret = state.passive_party._tmp_.dropmsb_sub(mgm)
        # tasty calculates theoretical worst case bitlengths. Since we know better,
        # we can safely overwrite that
        _set_dst(src, dst, ret)
        ret.set_bit_length(bitlen)
        ret._signed = hval.signed()


def Paillier_Garbled_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if force_bitlen is not None:
        bitlen = force_bitlen

    if force_signed is not None:
        signed = force_signed

    p = partyAttribute
    if not isclient():
        raise TastySyntaxError("Conversion from Homomorphic to Garbled from Client to Server does not make sense")
    masklen = bitlen + state.config.symmetric_security_parameter
    if state.precompute:
        # receive garbled Mask
        mgm = _receive(src, dst)
        mgm._bit_length = bitlen
        state.active_party.push_tmpattr(mgm)
        # prepare for creation of garbled masked plain value
        mgv = Garbled(bitlen = bitlen, val=p, signed=False)
        state.active_party.push_tmpattr(mgv)
        # prepare addition circuit to remove the mask
        ret = mgv.dropmsb_sub(mgm)
        # save shadow copy of resulting Garbled
        _set_dst(src, dst, ret)
        ret.set_bit_length(bitlen)
        # avoid warnings here, in online phase this is correct
        ret._signed = False
    else:
        mgm = state.active_party.pop_tmpattr()
        state.active_party._tmp_ = state.active_party.pop_tmpattr()
        # get the masked Homomorphic
        hval = _receive()
        hval._bit_length = masklen
        # decrypt the masked Homomorphic
        mpv = Unsigned(val=hval)
        mpv._value &= ((1<<bitlen)-1)
        if mpv.signed():
            raise NotImplementedError()
        mpv.set_bit_length(bitlen)
        # convert plain masked value into Garbled
        state.active_party._tmp_ = Garbled(val=mpv, bitlen=bitlen, signed=signed)
        # deblind the garbled value
        ret = state.active_party._tmp_.dropmsb_sub(mgm)
        # tasty calculates theoretical worst case bitlengths. Since we know better,
        # we can safely overwrite that
        _set_dst(src, dst, ret)
        ret.set_bit_length(bitlen)
        ret._signed = hval.signed()

def Garbled_Paillier_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if state.precompute:
        raise NotImplementedError()
    else:
        raise NotImplementedError()

def Garbled_Homomorphic_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    if state.precompute:
        raise NotImplementedError()
    else:
        raise NotImplementedError()


### Vector types
# encryptions
UnsignedVec_SignedVec_send = PlainVec_send

def UnsignedVec_SignedVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _receive_cast(src, dst, SignedVec, bitlen, dim)

SignedVec_UnsignedVec_send = PlainVec_send

def SignedVec_UnsignedVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _receive_cast(src, dst, UnsignedVec, bitlen, dim)

def UnsignedVec_PaillierVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    _sendcost(_dimtimes(dim) * state.config.asymmetric_security_parameter * 2)
    _cast_send(src, dst, PaillierVec, signed)

UnsignedVec_PaillierVec_receive = _unsigned_receive
SignedVec_PaillierVec_send = UnsignedVec_PaillierVec_send
SignedVec_PaillierVec_receive = _signed_receive

ModularVec_PaillierVec_send = UnsignedVec_PaillierVec_send
ModularVec_PaillierVec_receive = _signed_receive

def PlainVec_GarbledVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    raise NotImplementedError()

def PlainVec_GarbledVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    raise NotImplementedError()

UnsignedVec_GarbledVec_send = PlainVec_GarbledVec_send
UnsignedVec_GarbledVec_receive = PlainVec_GarbledVec_receive
SignedVec_GarbledVec_send = PlainVec_GarbledVec_send
SignedVec_GarbledVec_receive = PlainVec_GarbledVec_receive


# decryptions
def PaillierVec_PlainVec_send(typ, src, dst, bitlen, dim, signed, force_bitlen, force_signed):
    if isclient():
        src = typ(val=src)
    _send(src)

def PaillierVec_PlainVec_receive(typ, src, dst, bitlen, dim, signed, force_bitlen, force_signed):
    tmp = _receive()
    tmp._bit_length = force_bitlen or bitlen
    if isclient():
        bla = typ(val=tmp)
    else:
        bla = tmp
    _set_dst(src, dst, bla)

def PaillierVec_SignedVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    PaillierVec_PlainVec_send(SignedVec, src, dst, bitlen, dim, signed, force_bitlen, force_signed)

def PaillierVec_UnsignedVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    PaillierVec_PlainVec_send(UnsignedVec, src, dst, bitlen, dim, signed, force_bitlen, force_bitlen)

def PaillierVec_SignedVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    PaillierVec_PlainVec_receive(SignedVec, src, dst, bitlen, dim, signed, force_bitlen, force_signed)

def PaillierVec_UnsignedVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    PaillierVec_PlainVec_receive(UnsignedVec, src, dst, bitlen, dim, signed, force_bitlen, force_bitlen)



def GarbledVec_PlainVec_send(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    raise NotImplementedError()

def GarbledVec_PlainVec_receive(src, dst, bitlen, dim, signed, force_bitlen=None, force_signed=None):
    raise NotImplementedError()

GarbledVec_UnsignedVec_send = GarbledVec_PlainVec_send
GarbledVec_UnsignedVec_receive = GarbledVec_PlainVec_receive
GarbledVec_SignedVec_send = GarbledVec_PlainVec_send
GarbledVec_SignedVec_receive = GarbledVec_PlainVec_receive



# conversions
def PaillierVec_GarbledVec_send(src, dst, source_bitlen, source_dim, signed, force_bitlen=None, force_signed=None):

    if force_bitlen and (force_signed or (signed and not force_signed == False)):
        raise NotImplementedError("forcing bitlen on signeds is not supported now")

    if force_bitlen is not None:
        diff = source_bitlen - force_bitlen
        source_bitlen = force_bitlen
    else:
        diff = 0

    p = partyAttribute
    if not isserver():
        raise TastySyntaxError("Conversion from Homomorphic to Garbled from Client to Server does not make sense")
    # number of maximal bits in content
    overallbitlen = _dimtimes(source_dim) * source_bitlen
    # we have asymmetric_security_parameter bits to pack into, but need symmetric_security_parameter bits to blind
    cpc = state.config.asymmetric_security_parameter - state.config.symmetric_security_parameter - 1

    chunksize = cpc / source_bitlen
    chunkpayloadbits = chunksize * source_bitlen
    chunks = (overallbitlen - 1) / chunkpayloadbits  + 1
    lastchunksize = overallbitlen % chunkpayloadbits
    Homomorphic = tasty.types.Homomorphic
    HomomorphicVec = tasty.types.HomomorphicVec


    if lastchunksize:
        chunksizes = (chunks - 1) * (chunkpayloadbits, ) + (lastchunksize, )
    else:
        chunksizes = chunks * (chunkpayloadbits, )

    if state.precompute:

        if lastchunksize:
            masks = nogen(get_randomm(0, 2**(chunkpayloadbits + state.config.symmetric_security_parameter) - 1, chunks - 1)) + (mpz(rand.randint(0, 2**(lastchunksize + state.config.symmetric_security_parameter) - 1)),)
        else:
            masks = nogen(get_randomm(0, 2**(chunkpayloadbits + state.config.symmetric_security_parameter)- 1, chunks))


        if force_signed is not None:
            signed = force_signed

        # generate Mask values
        umasks = nogen(Unsigned(val=v, bitlen=l + state.config.symmetric_security_parameter) for v, l in zip(masks, chunksizes))

        # homomorphically encrypt masks
        hmasks = tuple(tasty.types.Homomorphic(val=mask, signed=False) for mask in umasks)
        state.active_party.push_tmpval(hmasks)

        # garble first chunkpayloadbits of the masks (manual construction of garbled! Voodoo!)
        mgms = []
        for mask, chunksize in zip(masks, chunksizes):
            state.passive_party._tmp_ = Garbled(bitlen=chunksize, signed=False, val=p)
            zv = Garbled.get_zero_value(state.passive_party._tmp_.gid)
            state.passive_party._tmp_[:] = plain2garbled(value2bits(mask & (1<<chunksize) - 1, chunksize), zv, state.R)
            mgms.append(state.passive_party._tmp_)

        state.passive_party.push_tmpval(mgms)


        #raise NotImplementedError("COSTS")
#        _sendcost(chunks * chunksize[0]

        # send garbled masks to client
        _send(mgms)

        # precompute the first chunkpayloadbits for the garbled masked value
        mgvs = []
        for chunksize in chunksizes:
            mgv = Garbled(bitlen=chunksize, passive=True, val=p, signed=False)
            state.passive_party.push_tmpattr(mgv)
            mgvs.append(mgv)


        # precompute the unmasking and unpacking
        rets = []
        for mgv, mgm, chunksize in zip(mgvs, mgms, chunksizes):
            ret = mgv.unpack(mgm, source_bitlen, chunksize, signed)
            state.passive_party.push_tmpattr(ret)
            rets.extend(ret)

        rets.reverse() # packing works exactly in the oposite direction then unpacking, so reverse here to get original result back

        vec = GarbledVec(bitlen=source_bitlen, dim=source_dim, val=rets)

        # save shadow copy of resulting GarbledVec
        _set_dst(src, dst, vec)

    else: # online phase
        assert signed == src.signed(), "the analyzer disagrees with the typesystems signedness"

        if force_signed is not None:
            signed = force_signed

        if not isserver():
            raise TastySyntaxError("Conversion from Homomorphic to Garbled from Client to Server does not make sense")

        # Pack the values with respecting the force_signed and force_bitlen
        hmasks = state.active_party.pop_tmpval()
        if force_signed is not None: # we must change it to the forced sign
            origsigned = src.signed()
            src._signed = force_signed
            for i in src:
                i._signed = force_signed

        packed, _, _ = src.pack(-(state.config.symmetric_security_parameter + 1), force_bitlen=force_bitlen)

        if force_signed is not None: # no change in the source, so revert changes done before pack()
            src._signed = origsigned
            for i in src:
                i._signed = origsigned

        assert len(packed) == len(hmasks), "packing error (%d packed chunks, but %d expected (%r, %r))"%(len(packed), len(hmasks), hmasks, packed)

        # mask the packed values
        for i, j in zip(packed, hmasks):
            i += j

        # send packed values to client
        _send(packed)

        # retrive garbled masks from tmpval-stack
        mgms = state.passive_party.pop_tmpval()

        # passive part for generation of garbled masked values
        mgvs = []
        for chunksize in chunksizes:
            state.passive_party._tmp_ = state.passive_party.pop_tmpattr()
            state.passive_party._tmp_ = Garbled(val=p, bitlen=chunksize, passive=True, signed=False)
            mgvs.append(state.passive_party._tmp_)


        # passive part of unblinding and unpacking
#        rets = []
        for mgm, mgv, chunksize in zip(mgms, mgvs, chunksizes):
            state.passive_party._tmp_ = state.passive_party.pop_tmpattr()
#            state.passive_party._tmp_ = mgv.unpack(mgm, source_bitlen, chunksize, signed)
#            rets.extend(state.passive_party._tmp_)

#        rets.reverse()



def PaillierVec_GarbledVec_receive(src, dst, source_bitlen, source_dim, signed, force_bitlen=None, force_signed=None):
    p = partyAttribute
    if force_bitlen and (force_signed or (signed and not force_signed == False)):
        raise NotImplementedError("forcing bitlen on signeds is not supported now")

    if force_bitlen:
        source_bitlen = force_bitlen

    overallbitlen = reduce(operator.mul, source_dim, 1) * source_bitlen
    cpc = state.config.asymmetric_security_parameter - state.config.symmetric_security_parameter - 1
    chunksize = (cpc - 1) / source_bitlen
    chunkpayloadbits = chunksize * source_bitlen
    chunks = (overallbitlen - 1) / chunkpayloadbits  + 1

    lastchunksize = overallbitlen % (chunksize * source_bitlen)


    if lastchunksize:
        chunksizes = (chunks - 1) * (chunkpayloadbits, ) + (lastchunksize, )
        masks = nogen(get_randomm(0, 2**(chunkpayloadbits + state.config.symmetric_security_parameter) - 1, chunks - 1)) + (mpz(rand.randint(0, 2**(lastchunksize + state.config.symmetric_security_parameter) - 1)),)
    else:
        chunksizes = chunks * (chunkpayloadbits, )
        masks = nogen(get_randomm(0, 2**(chunkpayloadbits + state.config.symmetric_security_parameter)- 1, chunks))


    if state.precompute:
        if force_signed is not None:
            signed = force_signed

         # receive garbled Mask
        mgms = _receive(src, dst)
        for mgm, size in zip(mgms, chunksizes):
            mgm._bit_length = size

        # prepare for creation of garbled masked plain value
        state.active_party.push_tmpval(mgms)

        # precompute first chunkpayloadbits for the garbled masked value
        mgvs = []
        for i in chunksizes:
            mgv = Garbled(bitlen=i, val=p, signed=False)
            state.passive_party.push_tmpattr(mgv)
            mgvs.append(mgv)

        # precompute the unmasking and unpacking
        rets = []
        for mgv, mgm, chunksize in zip (mgvs, mgms, chunksizes):
            ret = mgv.unpack(mgm, source_bitlen, chunksize, signed)
            state.active_party.push_tmpattr(ret)
            rets.extend(ret)

        rets.reverse()

        vec = GarbledVec(bitlen=source_bitlen, dim=source_dim, val=rets, signed=signed)

        # save shadow copy of resulting GarbledVec
        _set_dst(src, dst, vec)

    else: # online phase
        if force_signed is not None:
            signed = force_signed

        if not isclient():
            raise TastySyntaxError("Conversion from Homomorphic to Garbled from Client to Server does not make sense")

        # receive masked homomorphic values
        mhvs = _receive()
        for i, chunksize in zip(mhvs, chunksizes):
            i._bit_length = chunksize


        # decrypt masked garbled values
        mvs = nogen(Unsigned(val=i) for i in mhvs)

        # get the masked garbled values from tmpval-stack
        mgms = state.active_party.pop_tmpval()

        # compute first chunksize bits of garbled masked values
        mgvs = []
        for mv, chunksize in zip(mvs, chunksizes):
            state.passive_party._tmp_ = mgv = state.passive_party.pop_tmpattr()
            mv._value &= (1<<chunksize) - 1
            mv.set_bit_length(chunksize)
            state.passive_party._tmp_ = Garbled(val=mv, bitlen=chunksize, signed=signed)
            mgvs.append(state.passive_party._tmp_)


        # unpacking and unblinding
        rets = []
        for mgm, mgv, chunksize in zip(mgms, mgvs, chunksizes):
            state.active_party._tmp_ = state.active_party.pop_tmpattr()
            state.active_party._tmp_ = mgv.unpack(mgm, source_bitlen, chunksize, signed)
            rets.extend(state.active_party._tmp_)

        rets.reverse()

        vec = GarbledVec(bitlen=source_bitlen, dim=source_dim, val=rets, signed = rets[0].signed())
        _set_dst(src, dst, vec)


def GarbledVec_PaillierVec_send(src, dst, bitlen, dim):
    raise NotImplementedError()

def GarbledVec_PaillierVec_receive(src, dst, bitlen, dim):
    raise NotImplementedError()


def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
    if __debug__:
        state.log.debug("conversions.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims, role, passive, precompute)

    if methodname in ("Unsigned_Unsigned_send", "Unsigned_Unsigned_receive",
                      "Signed_Signed_send", "Signed_Signed_receive",
                      "Modular_Modular_send", "Modular_Modular_receive",
                      "Paillier_Paillier_send", "Paillier_Paillier_receive",
                      "Garbled_Garbled_send", "Garbled_Garbled_receive",

                      "Unsigned_Signed_send", "Unsigned_Signed_receive",
                      "Signed_Unsigned_send", "Signed_Unsigned_receive",
                      "Garbled_Unsigned_send", "Garbled_Unsigned_receive",
                      "Garbled_Signed_send", "Garbled_Signed_receive",
                      "Unsigned_Paillier_receive",
                      "Signed_Paillier_receive",
                      "Modular_Paillier_receive",
                      "Paillier_Unsigned_send",
                      "Paillier_Signed_send",
                      "Paillier_Modular_send",


                      "UnsignedVec_UnsignedVec_send", "UnsignedVec_UnsignedVec_receive",
                      "SignedVec_SignedVec_send", "SignedVec_SignedVec_receive",
                      "ModularVec_ModularVec_send", "ModularVec_ModularVec_receive",
                      "PaillierVec_PaillierVec_send", "PaillierVec_PaillierVec_receive",
                      "GarbledVec_GarbledVec_send", "GarbledVec_GarbledVec_receive"

                      "UnsignedVec_SignedVec_send", "UnsignedVec_SignedVec_receive",
                      "SignedVec_UnsignedVec_send", "SignedVec_UnsignedVec_receive",
                      "GarbledVec_UnsignedVec_send", "GarbledVec_UnsignedVec_receive",
                      "GarbledVec_SignedVec_send", "GarbledVec_SignedVec_receive",
                      "UnsignedVec_PaillierVec_receive",
                      "SignedVec_PaillierVec_receive",
                      "ModularVec_PaillierVec_receive",
                      "PaillierVec_UnsignedVec_send",
                      "PaillierVec_SignedVec_send",
                      "PaillierVec_ModularVec_send"):
        return {}

    elif methodname in ("Unsigned_Garbled_send", "Unsigned_Garbled_receive",
                        "Signed_Garbled_send", "Signed_Garbled_receive"):
        if role == Party.CLIENT:
            return {"ot": bit_lengths[0]}
        else:
            return {}

    elif methodname in ("UnsignedVec_GarbledVec_send", "UnsignedVec_GarbledVec_receive",
                        "SignedVec_GarbledVec_send", "SignedVec_GarbledVec_receive"):
        return {"ot": _dimtimes(dims[0]) * bit_lengths[0]}
    elif methodname in ("Unsigned_Paillier_send",
                        "Signed_Paillier_send",
                        "Modular_Paillier_send"):
        return {"Enc": 1}
    elif methodname in ("Paillier_Unsigned_receive",
                        "Paillier_Signed_receive",
                        "Paillier_Modular_receive"):
        return {"Dec": 1}
    elif methodname in ("UnsignedVec_PaillierVec_send",
                        "SignedVec_PaillierVec_send",
                        "ModularVec_PaillierVec_send"):
        return {"Enc": _dimtimes(dims[0])}
    elif methodname in ("PaillierVec_UnsignedVec_receive",
                        "PaillierVec_SignedVec_receive"):
        return {"Dec": _dimtimes(dims[0])}

    elif methodname == "Paillier_Garbled_send":
        return {"ot": bit_lengths[0],
                "Enc": 1}
    elif methodname == "Paillier_Garbled_receive":
        return {"ot": bit_lengths[0]}

    elif methodname == "PaillierVec_GarbledVec_send":
        overallbitlen = _dimtimes(dims[0]) * bit_lengths[0]
        cpc = state.config.asymmetric_security_parameter - state.config.symmetric_security_parameter - 1

        chunksize = cpc / bit_lengths[0]
        chunkpayloadbits = chunksize * bit_lengths[0]
        chunks = (overallbitlen - 1) / chunkpayloadbits  + 1


        return {"ot": _dimtimes(dims[0]) * bit_lengths[0],
                "Enc": chunks}
    elif methodname == "PaillierVec_GarbledVec_receive":
        return {"ot": _dimtimes(dims[0]) * bit_lengths[0]}
    raise NotImplementedError("calc_costs not implemented for %s"%methodname)


def affects(methodname, input_types, role):
    if __debug__:
        state.log.debug("conversions.affects(%r, %r, %r)", methodname, input_types, role)
    if methodname in ("GarbledVec_GarbledVec_send", "GarbledVec_GarbledVec_receive",
                      "Garbled_Garbled_receive", "Garbled_Garbled_send",
                      "Paillier_Garbled_send", "Paillier_Garbled_receive",
                      "PaillierVec_GarbledVec_send", "PaillierVec_GarbledVec_receive"):
        return isserver() and (Value.S_SETUP | Value.S_ONLINE) or (Value.C_SETUP | Value.C_ONLINE)
    elif methodname in (
        "PlainVec_GarbledVec_receive", "PlainVec_GarbledVec_send",
        "UnsignedVec_GarbledVec_receive", "UnsignedVec_GarbledVec_send",
        "SignedVec_GarbledVec_receive", "SignedVec_GarbledVec_send",
        "Plain_Garbled_receive", "Plain_Garbled_send",
        "Unsigned_Garbled_receive", "Unsigned_Garbled_send",
        "Signed_Garbled_receive", "Signed_Garbled_send",
        "PaillierVec_GarbledVec_receive", "PaillierVec_GarbledVec_send",
        "Paillier_Garbled_receive", "Paillier_Garbled_send"):
        return Value.S_SETUP | Value.C_SETUP | Value.C_ONLINE | Value.S_ONLINE
    else:
        return isserver() and Value.S_ONLINE or Value.C_ONLINE

def returns(methodname, input_types, bit_lengths, dims, signeds):
    if methodname in ("UnsignedVec_PaillierVec_receive", "UnsignedVec_PaillierVec_send"):
        return ({"type" : PaillierVec, "bitlen" : bit_lengths[1], "dim" : dims[1], "signed" : signeds[1]},)
    elif methodname in ("PaillierVec_GarbledVec_send", "PaillierVec_GarbledVec_receive"):
        return ({"type" : GarbledVec, "bitlen" : bit_lengths[1], "dim" : dims[1], "signed" : signeds[1]},)

    return ({"type" : input_types[0], "bitlen" : bit_lengths[1], "dim" : dims[1], "signed" : signeds[1]},)
