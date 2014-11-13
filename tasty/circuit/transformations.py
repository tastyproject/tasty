# -*- coding: utf-8 -*-

"""This module provides circuit transformations"""

from tasty.circuit import Circuit
from collections import deque
from random import randint, shuffle, random, seed
from tasty.circuit import threeinputreplace

class Circuit_Transformation(Circuit):
    def __init__(self, c):
        assert isinstance(c, Circuit), "c must be a circuit"
        self.c = c

    def num_output_bits(self):
        return self.c.num_output_bits()

    def num_input_bits(self):
        return self.c.num_input_bits()

    def inputs(self):
        return self.c.inputs()

    def outputs(self):
        return self.c.outputs()

    def num_gates(self):
        return self.c.num_gates()

    def next_gate(self):
        for g in self.c.next_gate():
            yield g

class replace_xnor_with_xor(Circuit_Transformation):
    """ Replace XNOR gates with XOR gates and inversion gate.
        The inversion gate is propagated if possible (i.e., not output).

        This transformation requires O(#XNOR_gates) memory
    """
    def __init__(self, c):

        Circuit_Transformation.__init__(self,c)
        self.n_gates = None
        self.outs = None
        self.msg = None

    def message(self):
        if self.msg is None:
            for g in self.next_gate():
                pass

        ret = StringIO()
        ret.write("Replaced %d XNOR gates with XOR gates:\n" % self.msg[0])
        ret.write("  inserted %d inverter gates." % self.msg[1])
        return ret.getvalue()

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return self.outs

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def next_gate(self):
        n_gates = self.c.num_gates()
        n_inputs = self.c.num_input_bits()
        n_outputs = self.c.num_output_bits()

        # invert = [False for i in xrange(n_gates+n_inputs)]
        invert = set()

        replaced = 0
        gate_idx = n_inputs
        for g_ins, g_tab in self.c.next_gate():
            d = len(g_ins)
            tab_len = 1<<d
            # invert gate table
            tab = g_tab
            for inp_ix, inp in enumerate(g_ins):
                #if invert[inp]:
                if inp in invert:
                    new_tab = 0
                    swaps = 1<<inp_ix
                    swap_els = 1<<(d-inp_ix)
                    swap_to = 0
                    for s in xrange(swaps): # swaps
                        for e in xrange(swap_els): # elements in swap
                            #swap_to = s*swap_els + e
                            swap_from = (s*swap_els + ((swap_els>>1) + e)%swap_els) % tab_len
                            #print "%d => %d" % (swap_from, swap_to)
                            tab_from = (tab & (1 << swap_from)) >> swap_from
                            new_tab = new_tab | (tab_from << swap_to)
                            swap_to += 1

                    tab = new_tab

            # replace XNOR gate with XOR gate
            if tab == 0b1001:
                #invert[gate_idx] = True
                invert.add(gate_idx)
                replaced += 1
                yield g_ins, 0b0110
            else:
                yield g_ins, tab
            gate_idx += 1

        # insert inverter gates for outputs that need to be inverted
        outs = []
        c_outs = self.c.outputs()
        for out_list, out_desc, out_type in c_outs:
            o_list = []
            for o in out_list:
                #if invert[o]:
                if o in invert:
                    yield (o,), 0b10
                    o_list.append(gate_idx)
                    gate_idx += 1
                else:
                    o_list.append(o)
            outs.append((o_list, out_desc, out_type))

        self.n_gates = gate_idx - n_inputs
        self.outs = outs

        self.msg = (replaced, self.n_gates - n_gates)

class replace_3_by_2(Circuit_Transformation):
    """ Replace 3-input gates with 2-input gates

        This transformation requires O(|C|) memory.
    """

    def __init__(self, c, filename="3inputsReplace.txt"):
        Circuit_Transformation.__init__(self, c)

        self.n_gates = None
        self.outs = None

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return self.outs

    def next_gate(self):
        n_inputs = self.c.num_input_bits()
        n_gate = n_inputs
        stack = []

        # For this we need O(|C|) memory
        g_trans = [None for i in xrange(n_inputs+self.c.num_gates())]
        for i in xrange(n_inputs):
            g_trans[i] = i

        for g_ix, g in enumerate(self.c.next_gate()):
            g_ins, g_tab = g
            d = len(g_ins)
            if d != 3 or threeinputreplace.translate[g_tab] is None:
                yield map(lambda x: g_trans[x],g_ins), g_tab
                g_trans[n_inputs + g_ix] = n_gate
                n_gate += 1
            else:
                r = threeinputreplace.translate[g_tab]
                if r[0] == "0":
                    yield [], 0
                    g_trans[n_inputs + g_ix] = n_gate
                    n_gate += 1
                    continue
                elif r[0] == "1":
                    yield [], 1
                    g_trans[n_inputs + g_ix] = n_gate
                    n_gate += 1
                    continue

                C,B,A = map(lambda x: g_trans[x], g_ins)
                r_pos = 0
                r_len = len(r)
                while r_pos < r_len:
                    e = r[r_pos]
                    if e == "(":
                        stack.append(None)
                    elif e == "A":
                        stack.append(A)
                    elif e == "B":
                        stack.append(B)
                    elif e == "C":
                        stack.append(C)
                    elif e == ",":
                        pass
                    elif e == "[": # gate found
                        # get function table
                        tab = 0
                        r_pos += 1
                        tab_len = 0
                        while r[r_pos] != "]":
                            if r[r_pos] == "0":
                                tab = tab << 1
                            elif r[r_pos] == "1":
                                tab = (tab << 1) | 1
                            tab_len += 1
                            r_pos += 1

                        # determine number of inputs
                        d = 0
                        while tab_len != 1:
                            assert (tab_len & 1) == 0
                            tab_len >>= 1
                            d += 1

                        # get inputs
                        ins = []
                        for i in xrange(d):
                            inp = stack.pop()
                            assert inp is not None
                            ins.append(inp)
                        inp = stack.pop()
                        assert inp is None

                        stack.append(n_gate)
                        yield ins, tab
                        n_gate += 1

                    r_pos += 1

                #  pop output wire from stack
                e = stack.pop()
                g_trans[n_inputs + g_ix] = e

        # determine outputs
        self.outs = []
        for o_list, o_desc, o_type in self.c.outputs():
            self.outs.append((map(lambda x: g_trans[x], o_list), o_desc, o_type))

        self.n_gates = n_gate - n_inputs

class circuit_buffer_RAM(Circuit_Transformation):
    """ Buffers circuit in RAM in constructor.

        This requires O(|C|) memory.
    """
    def __init__(self,c):
        Circuit_Transformation.__init__(self,c)
        self.cache_gates = tuple(c.next_gate())

    def next_gate(self):
        return self.cache_gates

class reorder_DFS(Circuit_Transformation):
    """ Reorder circuit in depth-first order """
    FIRST = 0
    RAND = 1
    MAX_FANOUT = 2
    MIN_FANOUT = 3
    RAND_ALL_MAX_FANOUT = 4
    modes = (FIRST, MAX_FANOUT, MIN_FANOUT, RAND, RAND_ALL_MAX_FANOUT)

    def __init__(self, c, mode, seed = None):
        Circuit_Transformation.__init__(self,c)
        assert mode in self.modes
        self.cache = False
        if mode == self.RAND or mode == self.RAND_ALL_MAX_FANOUT:
            if seed is None:
                self.gates = None
                self.cache = True
            self.seed = seed
        self.mode = mode
        self.outs = None

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return self.outs

    def reset_rand(self):
        seed(self.seed)

    def next_gate(self):
        if self.cache == False or self.gates is None:
            if self.cache:
                self.gates = []

            n_inputs = self.c.num_input_bits()
            n_gates = self.c.num_gates()

            # read in circuit and store in memory
            gate_inputs = [None for i in xrange(n_inputs+n_gates)]
            gate_tables = [None for i in xrange(n_inputs+n_gates)]
            gate_successors = [[] for i in xrange(n_inputs+n_gates)]
            gate_predecessors = [0 for i in xrange(n_inputs+n_gates)]
            gate_translation = [None for i in xrange(n_inputs+n_gates)]

            next_gate = n_inputs
            for g_ins, g_tab in self.c.next_gate():
                gate_inputs[next_gate] = g_ins
                gate_tables[next_gate] = g_tab
                for inp in g_ins:
                    gate_successors[inp].append(next_gate)
                gate_predecessors[next_gate] = len(g_ins)
                next_gate += 1

            # init stack
            S = []
            for i in xrange(n_inputs):
                S.append(i)
                gate_translation[i] = i

            def max_fanout_compare(x, y):
                vx = len(gate_successors[x])
                vy = len(gate_successors[y])
                return vx - vy

            def min_fanout_compare(x, y):
                vx = len(gate_successors[x])
                vy = len(gate_successors[y])
                return vy - vx

            if self.mode == self.RAND_ALL_MAX_FANOUT:
                self.reset_rand()
                shuffle(S)
                S.sort(max_fanout_compare)
            elif self.mode == self.MAX_FANOUT:
                S.sort(max_fanout_compare)
            elif self.mode == self.MIN_FANOUT:
                S.sort(min_fanout_compare)
            elif self.mode == self.RAND:
                self.reset_rand()
                shuffle(S)

            next_gate = n_inputs
            while len(S) > 0:
                e = S.pop()

                # output gate
                if e >= n_inputs:
                    g = map(lambda x: gate_translation[x], gate_inputs[e]), gate_tables[e]
                    if self.cache:
                        self.gates.append(g)
                    else:
                        yield g
                    gate_translation[e] = next_gate
                    next_gate += 1

                # insert child nodes
                new = []
                for s in gate_successors[e]:
                    gate_predecessors[s] -= 1
                    if gate_predecessors[s] == 0:
                        new.append(s)

                if self.mode == self.MAX_FANOUT:
                    new.sort(max_fanout_compare)
                elif self.mode == self.MIN_FANOUT:
                    new.sort(min_fanout_compare)
                elif self.mode == self.RAND or self.mode == self.RAND_ALL_MAX_FANOUT:
                    shuffle(new)

                #if len(new) > 1:
                #    print map(lambda x: (len(gate_successors[x]), gate_tables[x] == 0b0110) , new)

                S.extend(new)

                if self.mode == self.RAND_ALL_MAX_FANOUT:
                    S.sort(max_fanout_compare)

            # determine outputs
            self.outs = []
            for o_list, o_desc, o_type in self.c.outputs():
                self.outs.append((map(lambda x: gate_translation[x],o_list), o_desc, o_type))

        if self.cache:
            for g in self.gates:
                yield g

class reorder_BFS(Circuit_Transformation):
    """ Reorder circuit in topologic BFS order """
    def __init__(self, c):
        Circuit_Transformation.__init__(self,c)
        self.outs = None

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return self.outs

    def next_gate(self):
        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()

        # read in circuit and store in memory
        gate_inputs = [None for i in xrange(n_inputs+n_gates)]
        gate_tables = [None for i in xrange(n_inputs+n_gates)]
        gate_successors = [[] for i in xrange(n_inputs+n_gates)]
        gate_predecessors = [0 for i in xrange(n_inputs+n_gates)]
        gate_translation = [None for i in xrange(n_inputs+n_gates)]

        next_gate = n_inputs
        for g_ins, g_tab in self.c.next_gate():
            gate_inputs[next_gate] = g_ins
            gate_tables[next_gate] = g_tab
            for inp in g_ins:
                gate_successors[inp].append(next_gate)
            gate_predecessors[next_gate] = len(g_ins)
            next_gate += 1

        # init queue
        Q = deque()
        for i in xrange(n_inputs):
            Q.append(i)
            gate_translation[i] = i

        next_gate = n_inputs
        while len(Q) > 0:
            e = Q.popleft()

            # output gate
            if e >= n_inputs:
                yield map(lambda x: gate_translation[x], gate_inputs[e]), gate_tables[e]
                gate_translation[e] = next_gate
                next_gate += 1

            # insert child nodes
            for s in gate_successors[e]:
                gate_predecessors[s] -= 1
                if gate_predecessors[s] == 0:
                    Q.append(s)

        # determine outputs
        self.outs = []
        for o_list, o_desc in self.c.outputs():
            self.outs.append((map(lambda x: gate_translation[x],o_list), o_desc))

class reorder_rand(Circuit_Transformation):
    """ Reorder circuit in random topologic order """
    def __init__(self, c):
        Circuit_Transformation.__init__(self,c)

        self.outs = None
        self.out_gates = None

        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()

        # read in circuit and store in memory
        self.gate_inputs = [None for i in xrange(n_inputs+n_gates)]
        self.gate_tables = [None for i in xrange(n_inputs+n_gates)]
        self.gate_successors = [[] for i in xrange(n_inputs+n_gates)]

        n_gate = n_inputs
        for g_ins, g_tab in self.c.next_gate():
            self.gate_inputs[n_gate] = g_ins
            self.gate_tables[n_gate] = g_tab
            for inp in g_ins:
                self.gate_successors[inp].append(n_gate)
            n_gate += 1

    def outputs(self):
        if self.outs is None:
            self.rerand()
        return self.outs

    def rerand(self):
        """ Re-randomize topologic order of circuit """
        n_inputs = self.c.num_input_bits()
        n_gates = self.c.num_gates()

        self.out_gates = []

        gate_predecessors = [0 for i in xrange(n_inputs+n_gates)]
        gate_translation = [None for i in xrange(n_inputs+n_gates)]
        n_gate = n_inputs
        for g_ins, g_tab in self.c.next_gate():
            gate_predecessors[n_gate] = len(g_ins)
            n_gate += 1

        # init queue
        L = []
        for i in xrange(n_inputs):
            L.append(i)
            gate_translation[i] = i

        n_gate = n_inputs
        while len(L) > 0:
            # pick random element e from L
            e_pos = randint(0,len(L)-1)
            e = L[e_pos]
            last = L.pop()
            if e_pos < len(L):
                L[e_pos] = last

            # output gate
            if e >= n_inputs:
                trans_ins = map(lambda x: gate_translation[x], self.gate_inputs[e])
                self.out_gates.append((trans_ins, self.gate_tables[e]))
                gate_translation[e] = n_gate
                n_gate += 1

            # insert child nodes
            for s in self.gate_successors[e]:
                gate_predecessors[s] -= 1
                if gate_predecessors[s] == 0:
                    L.append(s)

        # determine outputs
        self.outs = []
        for o_list, o_desc, o_type in self.c.outputs():
            trans_outs = map(lambda x: gate_translation[x],o_list)
            self.outs.append((trans_outs, o_desc, o_type))

    def next_gate(self):
        if self.out_gates is None:
            self.rerand()
        for g in self.out_gates:
            yield g


