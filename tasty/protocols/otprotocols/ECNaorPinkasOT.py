# -*- coding: utf-8 -*-

from tasty.protocols.otprotocols import OTProtocol
from tasty.protocols import protocol
from tasty import utils, state, cost_results
from gmpy import mpz
import hashlib
import math
import cPickle
from tasty.crypt.homomorph.ecc import getEC, decompressPoint


def NP_EC_OT_P192(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("P-192"), False, *args, **kwargs)

def NP_EC_OT_secp256r1(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp256r1"), False, *args, **kwargs)

def NP_EC_OT_secp224r1(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp224r1"), False, *args, **kwargs)

def NP_EC_OT_secp192r1(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp192r1"), False, *args, **kwargs)

def NP_EC_OT_secp160r1(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp160r1"), False, *args, **kwargs)

def NP_EC_OT_P192_c(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("P-192"), True, *args, **kwargs)

def NP_EC_OT_secp256r1_c(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp256r1"), True, *args, **kwargs)

def NP_EC_OT_secp224r1_c(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp224r1"), True, *args, **kwargs)

def NP_EC_OT_secp192r1_c(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp192r1"), True, *args, **kwargs)

def NP_EC_OT_secp160r1_c(*args, **kwargs):
    return _ECNaorPinkasOT(getEC("secp160r1"), True, *args, **kwargs)

class _ECNaorPinkasOT(OTProtocol):
    """
    [NP01] Protocol 3.1 implemented over EC
    uses sha256 as a random oracle
    """
    def __init__(self, ec, compress, *args, **kwargs):
        super(_ECNaorPinkasOT, self).__init__(*args, **kwargs)
        self.EC = ec
        self.G = ec.G           
        self.compress = compress
        #the communication costs for the transmission of one ECPoint
        self.comCostsECPoint = self.EC.bitlen + 2 if self.compress else 2 * self.EC.bitlen + 2


    def sender_online0(self, args):
        k = utils.rand.randint(1,self.EC.getOrder())
        self.C = self.G * k
        self.C.compress = self.compress
        
        self.r = r = utils.rand.randint(1, self.EC.getOrder())
        self.rG = self.G * r
        self.rG.compress = self.compress
        self.rC = self.C * r
        cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send = utils.bit2byte(2*self.comCostsECPoint))

        yield self.C
        yield self.rG
    
    
    def receiver_online1(self, args):
        """         
        self.args is expected to be a list of one-bit integers 
        """
        # receive C and rG from sender
        args = tuple(args)
        self.C = C = decompressPoint(args[0],self.EC)
        self.rG = decompressPoint(args[1], self.EC)    
        self.idx = utils.nogen(self.args)
        
        G = self.G
        order = self.EC.getOrder()
        compress = self.compress 
        self.s = ss = []
        #Communication costs in this round: one ECPoint per bit in self.args
        cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send = utils.bit2byte(len(self.idx)*self.comCostsECPoint ))
        for i in self.idx:
            s = utils.rand.randint(1, order)
            ss.append(s)
            PK = G * s
            PK.compress = compress
            if i == 0:
                yield PK
            else:
                PK2 = C-PK
                PK2.compress = compress
                yield PK2
    
    def sender_online2(self, args):
        """ 
        self.args is expected to be a list of message-tuples
        """ 
        args = tuple(args)
        self.args = utils.nogen(self.args)

        r = self.r
        rC = self.rC

        #TODO: PLEASE FIX COSTS !!!
        #communication costs:
        # at the moment we sent 256 bit chunks. so the bits needed to transmit a message is 
        # ceil(bitlen(msg)/256) * 256
        costs = 0
        for msg in self.args:
            costs += int(math.ceil(mpz(msg[0]).bit_length() / 256.0)) * 256
            costs += int(math.ceil(mpz(msg[1]).bit_length() / 256.0)) * 256
        cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](Send = utils.bit2byte(costs))

        for i,(m0,m1) in enumerate(self.args):
            PK = decompressPoint(args[i], self.EC)
            PK0r = PK*r
            PK1r = rC - PK0r
#            digest0 = ""
#            digest1 = ""
            chunks = ((utils.bitlength(max(m0, m1)) - 1) // 256) + 1
            cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](SHA256 = 2 * chunks)

            key0 = cPickle.dumps((PK0r, "0"), protocol=2)
            key1 = cPickle.dumps((PK1r, "1"), protocol=2)
            
            digest0 = "".join(hashlib.sha256(key0 + mpz(j).binary()).digest() for j in xrange(chunks))
            digest1 = "".join(hashlib.sha256(key1 + mpz(j).binary()).digest() for j in xrange(chunks))
#            for j in xrange(chunks):
#                sj = mpz(j).binary()
#                digest0 += hashlib.sha256(key0 + sj).digest()
#                digest1 += hashlib.sha256(key1 + sj).digest()
            #TODO: truncate digest0 and digest1 to same length as m0 and m1 !!!
            h0 = abs(mpz(digest0,256)) ^ m0
            h1 = abs(mpz(digest1,256)) ^ m1

            yield (h0.binary(),h1.binary())

    def receiver_online3(self, args):
        """
        args ist expected to be [(h0_1,h1_1),(h0_2,h1_2), ... ,(h0_n, h1_n)]
        """
        args = tuple(args)
        results = []
        idx = self.idx
        s = self.s
        rG = self.rG
        for i,hs in enumerate(args):
            hs = mpz(hs[idx[i]], 256)
            PKr = rG*s[i]
            chunks = ((hs.bit_length() - 1) // 256) + 1
            cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](SHA256 = chunks)
            digest = ""
            key = cPickle.dumps((PKr, str(self.idx[i])), protocol=2)
            for j in xrange(chunks):
                sj = mpz(j).binary()
                digest += hashlib.sha256(key + sj).digest()
            digest = abs(mpz(digest, 256))
            results.append( digest ^ hs )
        self.results = results
        return None
  


    client_online_queue = [protocol.Protocol.dummy_op, receiver_online1, protocol.Protocol.dummy_op, receiver_online3]
    server_online_queue = [sender_online0, protocol.Protocol.dummy_op, sender_online2, protocol.Protocol.finished]
