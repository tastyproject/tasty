# -*- coding: utf-8 -*-
from tasty.circuit import Circuit
from tasty.circuit.transformations import circuit_buffer_RAM, replace_xnor_with_xor, replace_3_by_2
from tasty import state, cost_results
from gmpy import mpz
import hashlib
from tasty.utils import bit2byte, str2mpz
from tasty.crypt.garbled_circuit.abstract_garbled_circuit import * 
from tasty.protocols.protocol import get_realcost

__all__ = ["FreeXORReducedRowEvaluatorGarbledCircuit", "FreeXORReducedRowCreatorGarbledCircuit"]

### Implementation with FreeXORgates and reduced row (see [pssw09]), semi-honest model
class FreeXORReducedRowGarbledCircuit(object):
    """
    FreeXOR standard methods for both, evaluator and creator
    """
#    __MAX = (2**(state.config.symmetric_security_parameter + 1) - 1)

    __MAX = None

    def optimize_circuit(self, c):
        """
        Try to minimize number of non-XOR gates
        """
        stopwatch = get_realcost("Circuit")
        stopwatch.start()
        c = circuit_buffer_RAM(replace_xnor_with_xor(replace_3_by_2(c)))
        stopwatch.stop()
        return c
    
    def packforhash(self, tup, gid):
        """ pack into string for sha-hashing 
        tup = inputs
        gid = gate id
        d = num of inputs
        """
        from struct import pack
        
        d = len(tup)

        secparambytes = bit2byte(state.config.symmetric_security_parameter + 1)
        s = pack((str(secparambytes) + "s") * d + "HI", # formatstring: "11s11s11sHI" for d = 3 with t = 80
                 *map(lambda x: x.binary(), tup) + [ # tup[0].binary(), tup[1].binary(), tup[2].binary()
                self.circuit_id, gid])
                                
#        s = pack(str(secparambytes) + "s" + str(secparambytes) + "sHH", # formatstring looks as follows: "10s10sHH"
#                    (tup[0]>>1).binary(), (tup[1]>>1).binary(),
#                    self.circuit_id,
#                    gid) #TODO: check that this works
#        return s + mpz(gid << 2 | (_bit(tup[0], 1) << 1) | _bit(tup[1], 1)).binary()

        return s # "tup[0] || ... || tup[d-1] || circuit_id || gate_id"


    @staticmethod
    def perm_bit(garbled_bit):
        """ Get permutation bit from garbled_bit """
        return mpz(garbled_bit).getbit(0)

    @staticmethod
    def get_permbits(zero_inputs):
        permbits = 0
        for i in zero_inputs: # get permutation bits from zero inputs and
            permbits <<= 1
            permbits |= FreeXORReducedRowGarbledCircuit.perm_bit(i)

        return permbits
    
    @staticmethod
    def get_permuted_truth(zero_inputs, truthtable):
        """
        zero_inputs is a tuple of garbled bits with value 0
        
        @returns permutation bits as integer, permutation (list of indexes), 
        
        document me!
        """
        d = len(zero_inputs)

        permbits = FreeXORReducedRowGarbledCircuit.get_permbits(zero_inputs)
        perm = [i ^ permbits for i in xrange(1 << d)] # generate list of indexes

        _truthtable = mpz(truthtable)
        permtruth = tuple(reversed([_truthtable.getbit(i) for i in perm])) # compute permuted truthtable
        return permtruth


    def pentry(self, inputs, e):
        """ 
        returns garbled input values for row e
        """

        d = len(inputs)

        a = tuple(inp ^ (self.R * (self.perm_bit(inp) ^ ((e >> (d-i-1)) & 1)))
                     for i, inp in enumerate(inputs))
        
        assert d != 2 or (inputs[0] ^ (self.R * (self.perm_bit(inputs[0]) ^ (e >> 1))),
                          (inputs[1] ^ (self.R * (self.perm_bit(inputs[1]) ^ e & 1)))) == a
        return a

        # for d = 2:
        # return (inp[0] ^ (self.R * (self.perm_bit(inp[0]) ^ (e >> 1))),
        #                (inp[1] ^ (self.R * (self.perm_bit(inp[1]) ^ e & 1))))

    @staticmethod
    def mpzsha256trunc (x):
        """ 
        generate sha256-hash of x, convert to mpz and truncate 
        to symmetric_security_parameter + 1 bits
        @itypes: string
        @rtypes: mpz
        """ 
        if not FreeXORReducedRowGarbledCircuit.__MAX:
            FreeXORReducedRowGarbledCircuit.__MAX = mpz((1 << (state.config.symmetric_security_parameter + 1)) - 1)

        # generate digest
        mpzdigest = str2mpz(hashlib.sha256(x).digest())
        # truncate
        v = mpzdigest & FreeXORReducedRowGarbledCircuit.__MAX
        return v

class FreeXORReducedRowCreatorGarbledCircuit(
    FreeXORReducedRowGarbledCircuit, AbstractCreatorGarbledCircuit):


    def create_garbled_gate(self, inputs, truthtable, gateid):
        """crypto related stuff only here
         FIXME: COMMENT
        """

        d = len(inputs)
        if d == 2 and truthtable == 0b0110:
            # XOR gate (free XOR)
            return inputs[0] ^ inputs[1], None # no garbled table
        
        else:
            R = self.R
                                
            ptruth = self.get_permuted_truth(inputs, truthtable) # get permuted truthtable of the gate

            # compute garbled zero output value
            g0 = self.mpzsha256trunc(
                self.packforhash(self.pentry(inputs, 0), # get inputs for first entry in permuted table
                                 gateid)) ^ (R * ptruth[0]) 

            # compute garbled table
            garbledtable = tuple((g0 ^ self.mpzsha256trunc(self.packforhash(
                            self.pentry(inputs, e), gateid)) ^ (R * ptruth[e])).binary() 
                                 for e in xrange (1,1<<d)) # 2^d -1 table entries

            return g0, garbledtable 


    def creation_costs(self):
        """ IMPLEMENT ME"""
        t = self.circuit.gate_types()
        hashes = 0
        bits = 0
        for key in t.keys():
            if key == "2_XOR":
                pass
            elif key == "2_NONXOR":
                hashes += t[key] * 4
                bits += t[key] * 3 * (state.config.symmetric_security_parameter + 1)
            else:
                d = int(key)
                hashes += t[key] * (1<<d)
                bits += t[key] * ((1<<d) - 1) * (state.config.symmetric_security_parameter + 1)
        
        #TODO: we should count theoretical costs in bits
        # instead of rounding each time when converting from bits to bytes.
        # for now to remain compatible:
        bytes = bit2byte(bits)
            
        return {"SHA256": hashes,
                "Send": bytes }
        
        

class FreeXORReducedRowEvaluatorGarbledCircuit(
    FreeXORReducedRowGarbledCircuit, AbstractEvaluatorGarbledCircuit):

    def evaluate_garbled_gate(self, inputs, table, index):
#        print "*"
        d = len(inputs)
        if d == 2 and table == 0b0110: # free XOR gate
                return inputs[0] ^ inputs[1]
        else:
            table = self.next_garbled_gate.next()
            val = self.mpzsha256trunc(self.packforhash(inputs, index))
            index = self.get_permbits(inputs)
            if index == 0:
                return val
            else:
                return val ^ str2mpz(table[index - 1])


    def evaluation_costs(self):
        t = self.circuit.gate_types()
        hashes = 0
        for key in t.keys():
            if key == "2_XOR":
                pass
            else:
                hashes += t[key]
            
        return {"SHA256": hashes}

