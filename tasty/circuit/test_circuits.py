# -*- coding: utf-8 -*-

# This file contains circuits for testing purposes

from tasty.circuit import Circuit, UNDEF

class Testcircuit_MultiDegree(Circuit):
    def __init__(self, d_from, d_to):
        """ Circuit consisting of gates with [d_from, d_to] inputs.
            The circuit has 1 input and (d_to - d_from + 1) independent (parallel) gates and outputs.
         """
        assert d_to >= 0, \
            "d_to must be >= 0"
        assert d_from <= d_to, \
            "d_from must be <= d_to"
        self.d_from = d_from
        self.d_to = d_to

    def num_input_bits(self):
        return 1

    def num_output_bits(self):
        return self.d_to-self.d_from+1

    def num_gates(self):
        return self.d_to-self.d_from+1

    def inputs(self):
        return [(1, "input")]

    def outputs(self):
        return [((i,), "output_"+str(i-1), UNDEF) for i in xrange(1,self.d_to-self.d_from+2)]

    def next_gate(self):
        for d in xrange(self.d_from, self.d_to+1):
            if d == 3:
                tab = 0b00011111    # table which is not replaced by replace_3_to_2
            else:
                tab = 0b1
            yield [0 for i in xrange(d)], tab

class Testcircuit_MultiDegree_All(Circuit):
    def __init__(self, d_from, d_to):
        """ Circuit consisting of gates with [d_from, d_to] inputs.
            The circuit has d_to inputs and one gate for each possible gate table
        """
        assert d_to >= 0, \
            "d_to must be >= 0"
        assert d_from <= d_to, \
            "d_from must be <= d_to"
        self.d_from = d_from
        self.d_to = d_to
        self.n_gates = None

    def num_input_bits(self):
        return self.d_to

    def num_output_bits(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def inputs(self):
        return [(self.d_to, "input")]

    def outputs(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return [((self.d_to+i,), "output_"+str(i), UNDEF) for i in xrange(self.n_gates)]

    def next_gate(self):
        n_gates = 0
        for d in xrange(self.d_from, self.d_to+1):
            ins = range(d)
            for tab in xrange(1<<(1<<d)):
                n_gates += 1
                yield ins, tab
        self.n_gates = n_gates

if __name__ == '__main__':
    #c = Testcircuit_MultiDegree(0,10)
    c = Testcircuit_MultiDegree_All(0,3)
    c.check()
