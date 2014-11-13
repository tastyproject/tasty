# -*- coding: utf-8 -*-

from tasty.circuit import Circuit


class FPGA_output(object):
    LOAD_A = 0
    LOAD_B = 1
    XOR_A = 2
    XOR_B = 3
    XOR_C = 4
    XOR_AB = 5
    XOR_BC = 6
    XOR_AC = 7
    STORE_A = 8
    STORE_B = 9
    STORE_C = 10
    EVAL_A = 11
    EVAL_B = 12
    EVAL_C = 13
    EVAL_AB = 14
    EVAL_BC = 15
    EVAL_AC = 16
    OUT = 17

    ASC = 0
    BIN = 1

    o_codes = ["LOAD_A","LOAD_B","XOR_A","XOR_B","XOR_C","XOR_AB","XOR_BC","XOR_AC","STORE_A","STORE_B","STORE_C","EVAL_A","EVAL_B","EVAL_C","EVAL_AB","EVAL_BC","EVAL_AC","OUT"]

    def __init__(self, file, type_):
        assert type_ == self.ASC or type_ == self.BIN
        self.type_ = type_
        if file is not None :
            self.f = open(file, "w")
        else:
            self.f = None
        self.lines_written = 0
        self.n_reads = 0
        self.n_writes = 0

    def w(self, op, addr=None):

        self.lines_written += 1

        if self.f is not None :
            assert op >= 0 and op < len(self.o_codes)

            if self.type_ == self.ASC:
                if op in (self.EVAL_A, self.EVAL_AB, self.EVAL_AC, self.XOR_AB, self.XOR_AC, self.XOR_BC):
                    s = self.o_codes[op] + "\n"
                else:
                    s = self.o_codes[op] + "\t" + ("0x%x"%addr) + "\n"
                self.f.write(s)

            else:
                v = op << 27
                assert addr < (1<<27)
                if op not in (self.EVAL_A, self.EVAL_AB, self.EVAL_AC, self.XOR_AB, self.XOR_AC, self.XOR_BC):
                    v |= addr

                for i in xrange(8):
                    c = (v & (0xf << 4*(7-i))) >> 4*(7-i)
                    self.f.write("%x"%c)

                self.f.write("\n")

        if op in (self.LOAD_A, self.LOAD_B, self.XOR_A, self.XOR_B, self.XOR_C):
            self.n_reads += 1
        elif op in (self.STORE_A, self.STORE_B, self.STORE_C):
            self.n_writes += 1

    def num_lines(self):
        return self.lines_written

    def num_reads(self):
        return self.n_reads

    def num_writes(self):
        return self.n_writes

class FPGA_output_simple(object):
    """ Read inputs, compute, store
        uses: LOAD_A, LOAD_B, XOR_A, STORE_A, STORE_C, EVAL_A, EVAL_AB
    """
    def __init__(self, c, o_file, type_):
        self.c = c
        self.o_file = o_file
        self.type_ = type_

    def do(self):
        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()

        o = FPGA_output(self.o_file, self.type_)

        next_gate = n_inputs
        for g_ins, g_tab in self.c.next_gate():
            d = len(g_ins)

            if d == 1:
                o.w(o.LOAD_A, g_ins[0])
                o.w(o.EVAL_A, g_tab)
                o.w(o.STORE_C, next_gate)

            elif d == 2:
                if g_tab == 0b0110:
                    o.w(o.LOAD_A, g_ins[0])
                    o.w(o.XOR_A, g_ins[1])
                    o.w(o.STORE_A, next_gate)

                else:
                    o.w(o.LOAD_A, g_ins[0])
                    o.w(o.LOAD_B, g_ins[1])
                    o.w(o.EVAL_AB, g_tab)
                    o.w(o.STORE_C, next_gate)

            next_gate += 1
        return o.num_lines(), n_inputs+n_gates

class FPGA_output_avoid_loadstore(object):
    """ Read inputs, compute, store
        Optimizations:
          a) avoid load:
            1) if output of previous gate is in cache
            2) if input of previous gate is in cache
          b) avoid store: store whenever remaining fanout is > 0 and removed from cache
        uses: LOAD_A, LOAD_B, XOR_A, STORE_A, STORE_C, EVAL_A, EVAL_AB, EVAL_AC
    """

    def __init__(self, c, o_file, type_):
        self.c = c
        self.o_file = o_file
        self.type_ = type_

    def opt_load(self, type_):
        if type_[0] == "A" and self.in_A is not None :
            self.fan_out[self.in_A] -= 1
            if self.fan_out[self.in_A] == 0:
                mem = self.memory[self.in_A]
                self.memory[self.in_A] = None
                if mem is not None :
                    self.memory_unused.append(mem)
        elif type_[0] == "B" and self.in_B is not None :
            self.fan_out[self.in_B] -= 1
            if self.fan_out[self.in_B] == 0:
                mem = self.memory[self.in_B]
                self.memory[self.in_B] = None
                if mem is not None :
                    self.memory_unused.append(mem)
        elif type_[0] == "C" and self.in_C is not None :
            self.fan_out[self.in_C] -= 1
            if self.fan_out[self.in_C] == 0:
                mem = self.memory[self.in_C]
                self.memory[self.in_C] = None
                if mem is not None :
                    self.memory_unused.append(mem)

        if len(type_) > 1:
            if type_[1] == "A" and self.in_A is not None :
                self.fan_out[self.in_A] -= 1
                if self.fan_out[self.in_A] == 0:
                    mem = self.memory[self.in_A]
                    self.memory[self.in_A] = None
                    if mem is not None :
                        self.memory_unused.append(mem)
            if type_[1] == "B" and self.in_B is not None :
                self.fan_out[self.in_B] -= 1
                if self.fan_out[self.in_B] == 0:
                    mem = self.memory[self.in_B]
                    self.memory[self.in_B] = None
                    if mem is not None :
                        self.memory_unused.append(mem)
            if type_[1] == "C" and self.in_C is not None :
                self.fan_out[self.in_C] -= 1
                if self.fan_out[self.in_C] == 0:
                    mem = self.memory[self.in_C]
                    self.memory[self.in_C] = None
                    if mem is not None :
                        self.memory_unused.append(mem)

    def load(self, reg, addr):
        m_addr = self.memory[addr]
        if reg == "A":
            self.in_A = addr
            self.o.w(self.o.LOAD_A,m_addr)
        elif reg == "B":
            self.in_B = addr
            self.o.w(self.o.LOAD_B,m_addr)

        self.fan_out[addr] -= 1
        if self.fan_out[addr] == 0:
            self.memory_unused.append(m_addr)
            self.memory[addr] = None

    def write(self, op, addr=None):
        if op in (self.o.XOR_A, self.o.XOR_B, self.o.XOR_C, self.o.OUT):
            replaced_addr = self.memory[addr]
            if replaced_addr is None:
                raise ValueError("Address empty: " + str(addr))
            addr = replaced_addr

        self.o.w(op, addr)
        pass

    def opt_store(self, type_):
        if type_ == "A" and self.in_A is not None  and self.fan_out[self.in_A] > 0 and self.memory[self.in_A] is None:
            if len(self.memory_unused) > 0:
                m_addr = self.memory_unused.pop()
            else:
                m_addr = self.memory_size
                self.memory_size+=1
            self.o.w(self.o.STORE_A, m_addr)
            self.memory[self.in_A] = m_addr
            self.in_A = None
        elif type_ == "B" and self.in_B is not None  and self.fan_out[self.in_B] > 0 and self.memory[self.in_B] is None:
            if len(self.memory_unused) > 0:
                m_addr = self.memory_unused.pop()
            else:
                m_addr = self.memory_size
                self.memory_size+=1
            self.o.w(self.o.STORE_B, m_addr)
            self.memory[self.in_B] = m_addr
            self.in_B = None
        elif type_ == "C" and self.in_C is not None  and self.fan_out[self.in_C] > 0 and self.memory[self.in_C] is None:
            if len(self.memory_unused) > 0:
                m_addr = self.memory_unused.pop()
            else:
                m_addr = self.memory_size
                self.memory_size+=1
            self.o.w(self.o.STORE_C, m_addr)
            self.memory[self.in_C] = m_addr
            self.in_C = None

    def swap_inputs(self,tab):
        a = tab & 1
        b = tab & 2
        c = tab & 4
        d = tab & 8
        new_tab = d | (b << 1) | (c >> 1) | a
        return new_tab

    def fanout(self):
        """ Compute fan-out of gates """
        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()
        fan_out = [0 for i in xrange(n_inputs+n_gates)]
        for g_ins, g_tab in self.c.next_gate():
            for i in g_ins:
                fan_out[i] += 1

        # outputs as well
        for o_list, o_desc, o_type in self.c.outputs():
            for o in o_list:
                fan_out[o] += 1

        return fan_out

    def do(self):
        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()

        self.fan_out = self.fanout()

        self.o = FPGA_output(self.o_file, self.type_)

        self.memory = [None for i in xrange(n_inputs+n_gates)] # mapping table from values to memory
        self.memory_unused = [] # unused memory
        self.memory_size = n_inputs # size of memory

        # inputs are stored already
        for i in xrange(n_inputs):
            self.memory[i] = i

        next_gate = n_inputs
        self.in_A = None
        self.in_B = None
        self.in_C = None
        for g_ins, g_tab in self.c.next_gate():
            d = len(g_ins)

            if d == 1:
                if g_ins[0] == self.in_A:
                    self.opt_load("A")
                    self.opt_store("C")
                    self.write(self.o.EVAL_A,g_tab)
                elif g_ins[0] == self.in_B:
                    self.opt_load("B")
                    self.opt_store("C")
                    self.write(self.o.EVAL_B,g_tab)
                elif g_ins[0] == self.in_C:
                    self.opt_load("C")
                    self.opt_store("C")
                    self.write(self.o.EVAL_C,g_tab)
                else:
                    self.opt_load("*")
                    self.opt_store("A")
                    self.load("A", g_ins[0])
                    self.opt_store("C")
                    self.write(self.o.EVAL_A,g_tab)
                self.in_C = next_gate

            elif d == 2:
                if g_tab == 0b0110:
                    if (g_ins[0] == self.in_A and g_ins[1] == self.in_B) or (g_ins[1] == self.in_A and g_ins[0] == self.in_B):
                        self.opt_load("AB")
                        self.opt_store("A")
                        self.write(self.o.XOR_AB)
                        self.in_A = next_gate
                    elif (g_ins[0] == self.in_B and g_ins[1] == self.in_C) or (g_ins[1] == self.in_B and g_ins[0] == self.in_C):
                        self.opt_load("BC")
                        self.opt_store("B")
                        self.write(self.o.XOR_BC)
                        self.in_B = next_gate
                    elif (g_ins[0] == self.in_A and g_ins[1] == self.in_C) or (g_ins[1] == self.in_A and g_ins[0] == self.in_C):
                        self.opt_load("AC")
                        self.opt_store("A")
                        self.write(self.o.XOR_AC)
                        self.in_A = next_gate
                    elif g_ins[0] == self.in_A:
                        self.opt_load("Ax")
                        self.opt_store("A")
                        self.write(self.o.XOR_A, g_ins[1])
                        self.in_A = next_gate
                    elif g_ins[1] == self.in_A:
                        self.opt_load("xA")
                        self.opt_store("A")
                        self.write(self.o.XOR_A, g_ins[0])
                        self.in_A = next_gate
                    elif g_ins[0] == self.in_B:
                        self.opt_load("Bx")
                        self.opt_store("B")
                        self.write(self.o.XOR_B, g_ins[1])
                        self.in_B = next_gate
                    elif g_ins[1] == self.in_B:
                        self.opt_load("xB")
                        self.opt_store("B")
                        self.write(self.o.XOR_B, g_ins[0])
                        self.in_B = next_gate
                    elif g_ins[0] == self.in_C:
                        self.opt_load("Cx")
                        self.opt_store("C")
                        self.write(self.o.XOR_C, g_ins[1])
                        self.in_C = next_gate
                    elif g_ins[1] == self.in_C:
                        self.opt_load("xC")
                        self.opt_store("C")
                        self.write(self.o.XOR_C, g_ins[0])
                        self.in_C = next_gate
                    else:
                        self.opt_load("xx")
                        self.opt_store("A")
                        self.load("A", g_ins[0])
                        self.write(self.o.XOR_A, g_ins[1])
                        self.in_A = next_gate

                else:
                    if g_ins[0] == self.in_A:
                        if g_ins[1] == self.in_B:    # AB
                            self.opt_load("AB")
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, g_tab)
                        elif g_ins[1] == self.in_C:  # AC
                            self.opt_load("AC")
                            self.opt_store("C")
                            self.write(self.o.EVAL_AC, g_tab)
                        else:                   # A*
                            self.opt_load("A*")
                            self.opt_store("B")
                            self.load("B",g_ins[1])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, g_tab)
                    elif g_ins[0] == self.in_B:
                        if g_ins[1] == self.in_A:    # BA
                            self.opt_load("BA")
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, self.swap_inputs(g_tab))
                        elif g_ins[1] == self.in_C:  # BC
                            self.opt_load("BC")
                            self.opt_store("C")
                            self.write(self.o.EVAL_BC, g_tab)
                        else:                   # B*
                            self.opt_load("B*")
                            self.opt_store("A")
                            self.load("A", g_ins[1])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, self.swap_inputs(g_tab))
                    elif g_ins[0] == self.in_C:
                        if g_ins[1] == self.in_A:    # CA
                            self.opt_load("CA")
                            self.opt_store("C")
                            self.write(self.o.EVAL_AC, self.swap_inputs(g_tab))
                        elif g_ins[1] == self.in_B:  # CB
                            self.opt_load("CB")
                            self.opt_store("C")
                            self.write(self.o.EVAL_BC, self.swap_inputs(g_tab))
                        else:                   # C*
                            self.opt_load("C*")
                            self.opt_store("A")
                            self.load("A", g_ins[1])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AC, self.swap_inputs(g_tab))
                    else:
                        if g_ins[1] == self.in_A:    # *A
                            self.opt_load("*A")
                            self.opt_store("B")
                            self.load("B", g_ins[0])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, self.swap_inputs(g_tab))
                        elif g_ins[1] == self.in_B:  # *B
                            self.opt_load("*B")
                            self.opt_store("A")
                            self.load("A", g_ins[0])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, g_tab)
                        elif g_ins[1] == self.in_C:  # *C
                            self.opt_load("*C")
                            self.opt_store("A")
                            self.load("A", g_ins[0])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AC, g_tab)
                        else:                   # **
                            self.opt_load("**")
                            self.opt_store("A")
                            self.load("A", g_ins[0])
                            self.opt_store("B")
                            self.load("B", g_ins[1])
                            self.opt_store("C")
                            self.write(self.o.EVAL_AB, g_tab)

                    self.in_C = next_gate
            else: # d > 2
                raise ValueError("only gates with <= 2 inputs are supported")

            next_gate += 1

        self.opt_store("A")
        self.opt_store("B")
        self.opt_store("C")

        # write outputs
        for o_list, o_desc, o_type in self.c.outputs():
            for out in o_list:
                self.write(self.o.OUT, out)

        return self.o.num_lines(), self.memory_size, self.o.num_reads(), self.o.num_writes()

from reader import PSSW09Circuit
from transformations import *

import sys


def make_all():
    c = FileCircuitPSSW09("circuits/PSSW09_PracticalSFE/AES_PSSW09.txt")
    d = replace_xnor_with_xor(c)
    e = reorder_DFS(d)
    f = reorder_Priority(d)

    DIR = "circuits/CHES/"

    filename = "A_PSSW09"
    #print filename, FPGA_output_simple(c, DIR+filename+".asc", FPGA_output.ASC).do()
    FPGA_output_simple(c, DIR+filename+".bin", FPGA_output.BIN).do()

    filename = "B_NOXNOR"
    #print filename, FPGA_output_simple(d, DIR+filename+".asc", FPGA_output.ASC).do()
    FPGA_output_simple(d, DIR+filename+".bin", FPGA_output.BIN).do()

    filename = "C_CACHE"
    #print filename, FPGA_output_avoid_loadstore(d, DIR+filename+".asc", FPGA_output.ASC).do()
    FPGA_output_avoid_loadstore(d, DIR+filename+".bin", FPGA_output.BIN).do()

    filename = "D_DFS"
    #print filename, FPGA_output_avoid_loadstore(e, DIR+filename+".asc", FPGA_output.ASC).do()
    FPGA_output_avoid_loadstore(e, DIR+filename+".bin", FPGA_output.BIN).do()

    filename = "E_Prio"
    #print filename, FPGA_output_avoid_loadstore(f, DIR+filename+".asc", FPGA_output.ASC).do()
    FPGA_output_avoid_loadstore(f, DIR+filename+".bin", FPGA_output.BIN).do()


def make_rand(mode, suffix):
    c = PSSW09Circuit("circuits/PSSW09_PracticalSFE/AES_PSSW09.txt")
    d = replace_xnor_with_xor(c)

    DIR = "circuits/CHES/"
    filename = "F_Rand"
    if suffix is not None :
        filename += suffix

    def minimize_size(min, now):
        return min[0] > now[0]

    def minimize_rw(min, now):
        return min[2] + min[3] > now[2] + now[3]

    if mode == "RW":
        #print "Minimizing number of read/write operations..."
        minimize = minimize_rw
    else: # if mode == "SIZE":
        #print "Minimizing size..."
        minimize = minimize_size

    asc_name = DIR+filename+".asc"
    bin_name = DIR+filename+".bin"

    mode=reorder_DFS.MAX_FANOUT
    e = reorder_DFS(d, mode)
    min = FPGA_output_avoid_loadstore(e, asc_name, FPGA_output.ASC).do()
    #print min, min[2]+min[3]
    FPGA_output_avoid_loadstore(e, bin_name, FPGA_output.BIN).do()

    while True:
        v = reorder_DFS(d, reorder_DFS.RAND_ALL_MAX_FANOUT)
        now = FPGA_output_avoid_loadstore(v, None, FPGA_output.ASC).do()
        if minimize(min, now):
            min = now
            FPGA_output_avoid_loadstore(v, asc_name, FPGA_output.ASC).do()
            FPGA_output_avoid_loadstore(v, bin_name, FPGA_output.BIN).do()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        suffix = None
        mode = None
    elif len(sys.argv) == 2:
        mode = sys.argv[1]
        suffix = None
    else:
        mode = sys.argv[1]
        suffix = sys.argv[2]

    #make_all()
    make_rand(mode,suffix)
