# -*- coding: utf-8 -*-

from tasty import state
from tasty.utils import value2bits, bits2value
from cStringIO import StringIO
from gmpy import mpz

# Types
UNSIGNED = 0
SIGNED = 1
UNDEF = 2

# Drop MSB?
NODROP_MSB = 3
DROP_MSB = 4


class Circuit(object):
    """Base class for circuits

    Circuits must be sorted topologically.

    input and output indices are of type int
    """
    def num_input_bits(self):
        """Returns number of input bits

        @rtype: int
        @return: number of input bits
        """
        raise NotImplementedError()

    def inputs(self):
        """Returns input bit lengths

        @rtype: iterable
        @return: iterable of bit lengths of input arguments
        """
        raise NotImplementedError()

    def num_output_bits(self):
        """Returns the number of output bits

        @rtype: int
        @return: number of output bits
        """

        raise NotImplementedError()

    def outputs(self):
        """Returns tuple (output indices, name, type) for each wire

        @rtype: iterable
        @return: iterable of (iterable of output indices, string, UNSIGNED|SIGNED|UNDEF)
        """

        raise NotImplementedError()

    def num_gates(self):
        """Returns the number of gates

        @rtype: int
        @return: number of gates
        """
        raise NotImplementedError()

    def next_gate(self):
        """Returns a gate - generator method

        @rtype: iterable
        @return: an iterable of (iterable of input indices, truth table)
        """
        raise NotImplementedError()

    def __str__(self):
        """Returns a formatted informal representation string

        @rtype: str
        """

        ret = StringIO()
        num_inputs = self.num_input_bits()
        ret.write("#input bits: %d \n" % num_inputs)
        ret.write("inputs: %s\n" % str(self.inputs()))
        ret.write("#output bits: %d\n" % self.num_output_bits())
        ret.write("outputs: %s\n" % str(self.outputs()))
        ret.write("#gates: %d\n" % self.num_gates())
        for gx, g in enumerate(self.next_gate()):
            inputs, truth_table = g
            ret.write("    %d %s %s\n" % (
                num_inputs + gx, str(inputs), bin(truth_table)))
        return ret.getvalue()

    def check(self):
        """Check that circuit is in correct format

        @rtype: NoneType"""

        # check inputs
        ins=0
        for n, desc in self.inputs():
            ins += n
        assert self.num_input_bits() == ins, \
            "Number of inputs does not match"

        # check outputs
        outs = 0
        for o, desc, type_ in self.outputs():
            iter(o) # check if output list is iterable
            assert type_ == UNSIGNED or type_ == SIGNED or type_ == UNDEF
            outs += len(o)
        assert self.num_output_bits() == outs, \
            "Number of outputs does not match"

        # check gates
        gate_idx = self.num_input_bits()
        for inputs, table in self.next_gate():
            assert table < (1<<(1<<len(inputs))), \
                "Size of function table too large"
            for i in inputs:
                assert i < gate_idx, "Circuit not sorted topologically"
            gate_idx += 1
        assert gate_idx == self.num_gates() + self.num_input_bits(), \
            "Number of gates does not match"

    def eval(self, inputs):
        """Evaluate circuit on plain inputs"""

        assert len(inputs) == len(self.inputs()), \
            "#inputs must match #inputs of circuit"

        u = self.num_input_bits()
        k = self.num_gates()

        wire_values = [None for i in xrange(u + k)] #  values of wires

        # assign inputs
        input_desc = self.inputs()
        k = 0
        for ix, i in enumerate(inputs): # for each input i
            v = i
            l, desc = input_desc[ix]
            state.log.debug("%s:", desc)

            wire_values[k:k+l] = value2bits(mpz(v),l)
            k+=l


        # evaluate gates
        state.log.debug("Evaluating gates:")

        for gx, g in enumerate(self.next_gate()): # for each gate
            g_ins, g_tab = g

            # determine index into gate table
            tab_idx = 0
            for i in g_ins:
                tab_idx <<= 1
                tab_idx |= wire_values[i]

            # evaluate gate
            lookup_idx = (1<<len(g_ins)) - tab_idx - 1
            val = (g_tab & (1 << lookup_idx)) >> lookup_idx
            wire_values[u+gx] = val

            state.log.debug("%d: %s %s @ %d => %d", u+gx, g_ins, bin(g_tab), tab_idx, val)

        # read outputs
        output_values = []
        for out, desc, type_ in self.outputs():
            trans_out = map(lambda x: wire_values[x], out)
            o_val = bits2value(trans_out)
            output_values.append(o_val)
        return output_values

    def subcircuit_next_gate(self, input_translation, gate_id_shift, total_inputs):
        """ Returns next gate of this circuit as subcircuit within an other circuit.
            input_translation: list of which input is associated to which wire
            gate_id_shift: where to start indexing gates
        """
        ins = self.num_input_bits()
        assert len(input_translation) == ins
        delta = total_inputs - ins + gate_id_shift
        for g_ins, g_table in self.next_gate():
            translated_ins = []
            for v in g_ins:
                if v < ins:
                    translated_ins.append(input_translation[v])
                else:
                    translated_ins.append(v+delta)
            yield (translated_ins, g_table)

    def subcircuit_outputs(self, input_translation, gate_id_shift, total_inputs):
        """ Returns outputs of this circuit as subcircuit within an other circuit.
            input_translation: list of which input is associated to which wire
            gate_id_shift: where to start indexing gates
            total_inputs: total number of inputs of outer circuit
        """
        ins = self.num_input_bits()
        delta_gate = total_inputs - ins + gate_id_shift
        ret = []
        for o, desc, type_ in self.outputs():
            akt_ret = []
            for i in o:
                if i < ins:
                    akt_ret.append(input_translation[i])
                else:
                    akt_ret.append(i + delta_gate)
            ret.append(akt_ret)
        return ret

    def gate_types(self):
        """ Count different types of gates.
            2-input gates are separated into XOR and NONXOR gates """
        gates = {}
        for g_in, g_tab in self.next_gate():
            d=len(g_in)
            if d==2:
                if g_tab == 0b0110:
                    if "2_XOR" not in gates:
                        gates["2_XOR"] = 0
                    gates["2_XOR"] += 1
                else:
                    if "2_NONXOR" not in gates:
                        gates["2_NONXOR"] = 0
                    gates["2_NONXOR"] += 1
            else:
                if str(d) not in gates:
                    gates[str(d)] = 0
                gates[str(d)] += 1
        return gates
