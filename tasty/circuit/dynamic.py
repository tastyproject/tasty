# -*- coding: utf-8 -*-

"""This module provides basic circuit structures and features"""

from tasty.circuit import Circuit
from tasty.utils import bitlength

from tasty.circuit import SIGNED, UNSIGNED, UNDEF, DROP_MSB, NODROP_MSB

__all__ = ["SubCircuit", "AddCircuit",
           "AddSubCircuit", "AddSub0Circuit",
           "CmpCircuit", "MuxCircuit",
           "Bool2Circuit", "NotCircuit",
           "MultiplicationCircuit", "FastMultiplicationCircuit",
           "MinMaxValueCircuit", "MinMaxValueIndexCircuit", "MinMaxIndexCircuit",
           "VectorMultiplicationCircuit",
           "HornerMergeCircuit",
           "GateCircuit",
           "UnpackCircuit"]


class DynamicCircuit(Circuit):
    """Base class for 'just-in-time' circuits"""

    def output_gate(self, inputs, truth_table):
        """Called for each gate.

        Can be overwritten by subclasses when special checks or processing is
        needed. This vanilla implementation only returns the actual arguments as
        provided.

        @type inputs: iterable
        @param inputs: iterable of input indices used for this gate

        @type truth_table: int
        @param truth_table:
        """
        assert 1 << (1 << len(inputs)) > truth_table
        return inputs, truth_table


class GateCircuit(DynamicCircuit):
    def __init__(self, d, g_tabs):
        """Circuit that evaluates d-input gate with gate tables given in g_tabs"""
        if d < 0:
            raise ValueError("number of inputs must be >= 0")
        if len(g_tabs) == 0:
            raise ValueError("at least one gate table must be provided")
        for tab in g_tabs:
            for i in tab:
                if i != 0 and i != 1:
                    raise ValueError("gate tables must contain 0 and 1 values only")
            if len(tab) != (1 << d):
                raise ValueError("gate table must have 2^d entries")
        self.g_tabs = g_tabs
        self.d = d

    def num_input_bits(self):
        return self.d

    def num_output_bits(self):
        return len(self.g_tabs)

    def num_gates(self):
        return len(self.g_tabs)

    def inputs(self):
        ins = [(1, "input_" + str(i)) for i in xrange(self.d)]
        return ins

    def outputs(self):
        n_outs = len(self.g_tabs)
        return [((self.d + i,), "output_" + str(i), UNDEF) for i in xrange(n_outs)]

    def next_gate(self):
        d = self.d
        g_tabs = self.g_tabs
        ins = range(d)
        for t in g_tabs:
            tab = 0
            for i in xrange(1 << d):
                tab = (tab << 1) | t[i]
            yield ins, tab


class NotCircuit(DynamicCircuit):
    def __init__(self, bitlen):
        """Circuit that evaluates bitwise NOT of bitlen bit value"""
        if bitlen <= 0:
            raise ValueError("bitlen must be > 0")

        self.bitlen = bitlen

    def num_input_bits(self):
        return self.bitlen

    def num_output_bits(self):
        return self.bitlen

    def num_gates(self):
        return self.bitlen

    def inputs(self):
        return ((self.bitlen, "x"),)

    def outputs(self):
        return ((range(self.bitlen, 2 * self.bitlen), "z", UNSIGNED),)

    def next_gate(self):
        g_tab = 0b10
        bitlen = self.bitlen

        for i in xrange(bitlen):
            yield self.output_gate((i,), g_tab)


class Bool2Circuit(DynamicCircuit):
    AND = 0b0001
    OR = 0b0111
    XOR = 0b0110

    def __init__(self, bitlen, g_tab):
        """ Circuit that evaluates boolean operation given in g_tab on bitlen bit values """

        if g_tab not in (self.AND, self.OR, self.XOR):
            raise ValueError("please provide a valid gate table")

        if bitlen <= 0:
            raise ValueError("bitlen must be > 0")

        self.bitlen = bitlen
        self.g_tab = g_tab

    def num_input_bits(self):
        return 2 * self.bitlen

    def num_output_bits(self):
        return self.bitlen

    def num_gates(self):
        return self.bitlen

    def inputs(self):
        return ((self.bitlen, "x"), (self.bitlen, "y"))

    def outputs(self):
        return ((range(2 * self.bitlen, 3 * self.bitlen), "z", UNSIGNED),)

    def next_gate(self):
        g_tab = self.g_tab
        bitlen = self.bitlen

        for i in xrange(bitlen):
            yield self.output_gate((i, bitlen + i), g_tab)


class SubCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength, type_y, drop_msb=NODROP_MSB):
        """Circuit that computes z = x - y for unsigned or signed y
            optionally drop MSB

        @type x_bit_length: int
        @param x_bit_length: |x|

        @type y_bit_length: int
        @param y_bit_length: |y|

        raises ValueError: wrong bitlength
        """

        if x_bitlength < y_bitlength:
            raise NotImplementedError("|x| must be >= |y|")

        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")

        if type_y != SIGNED and type_y != UNSIGNED:
            raise ValueError("type of y must be either signed or unsigned")

        if drop_msb != NODROP_MSB and drop_msb != DROP_MSB:
            raise ValueError("drop_msb must be either NODROP_MSB or DROP_MSB")

        if drop_msb == DROP_MSB and type_y == SIGNED:
            raise NotImplementedError("This functionality has not been implemented yet")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength
        self.type_y = type_y
        self.drop_msb = drop_msb
        self.outs = None
        self.n_gates = None

    def num_input_bits(self):
        """See L{Circuit.num_input_bits}"""
        return self.x_bitlength + self.y_bitlength

    def inputs(self):
        """See L{Circuit.inputs}"""
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def num_output_bits(self):
        """See L{Circuit.num_output_bits}"""
        if self.drop_msb == DROP_MSB:
            return self.x_bitlength
        else:
            return self.x_bitlength + 1

    def num_gates(self):
        """See L{Circuit.num_gates}"""
        if self.n_gates is None:
            for i in self.next_gate():
                pass
        return self.n_gates

    def next_gate(self):
        """See L{Circuit.next_gate}"""
        first_gate_idx = self.num_input_bits()
        next_gate_num = 0
        outs = []

        yield self.output_gate((0, self.x_bitlength), 0b0110)  # z0
        outs.append(first_gate_idx + next_gate_num)
        next_gate_num += 1

        if self.x_bitlength > 1 or self.drop_msb == NODROP_MSB:
            yield self.output_gate((0, self.x_bitlength), 0b0100)  # c0
            next_gate_num += 1

        for i in xrange(1, self.y_bitlength):
            yield self.output_gate((i, self.x_bitlength + i, first_gate_idx + 2 * i - 1), 0b01101001)  # zi
            outs.append(first_gate_idx + next_gate_num)
            next_gate_num += 1
            if i != self.y_bitlength - 1 or self.x_bitlength > self.y_bitlength or self.drop_msb == NODROP_MSB:
                yield self.output_gate((i, self.x_bitlength + i, first_gate_idx + 2 * i - 1), 0b01110001)  # ci
                next_gate_num += 1

        y_msb = self.x_bitlength + self.y_bitlength - 1

        # if input x is longer
        if self.x_bitlength > self.y_bitlength:
            for i in xrange(self.y_bitlength, self.x_bitlength):
                if self.type_y == UNSIGNED:
                    yield self.output_gate((i, first_gate_idx + next_gate_num - 1), 0b0110)  # zi
                    outs.append(first_gate_idx + next_gate_num)
                    next_gate_num += 1
                    if i != self.x_bitlength - 1 or self.drop_msb == NODROP_MSB:
                        yield self.output_gate((i, first_gate_idx + 2 * i - 1), 0b0100)  # ci
                        next_gate_num += 1
                else:
                    yield self.output_gate((i, y_msb, first_gate_idx + 2 * i - 1), 0b01101001)  # zi
                    outs.append(first_gate_idx + next_gate_num)
                    next_gate_num += 1
                    if i != self.x_bitlength - 1 or self.drop_msb == NODROP_MSB:
                        yield self.output_gate((i, y_msb, first_gate_idx + 2 * i - 1), 0b01110001)  # ci
                        next_gate_num += 1

        if self.drop_msb == NODROP_MSB:
            if self.type_y == SIGNED:
                yield self.output_gate((first_gate_idx + 2 * self.x_bitlength - 1, y_msb), 0b0110)
                outs.append(first_gate_idx + next_gate_num)
                next_gate_num += 1
            else:
                outs.append(first_gate_idx + next_gate_num - 1)

        self.n_gates = next_gate_num
        self.outs = outs

    def outputs(self):
        """See L{Circuit.outputs}"""
        if self.outs is None:
            for g in self.next_gate():
                pass
        return ((self.outs, "z", SIGNED),)


class UnpackCircuit(DynamicCircuit):
    def __init__(self, bitlength, n_values, sign):
        """Circuit that unpacks n_values bitlength bit values of type by subtracting R (and rotating if type=SIGNED)

        @type bitlength: int
        @type n_values: int
        @type type: SIGNED|UNSIGNED

        raises ValueError: invalid bitlength or n_values
        """

        if bitlength <= 0:
            raise ValueError("bitlength must be > 0")

        if n_values <= 0:
            raise ValueError("n_values must be > 0")

        if sign != SIGNED and sign != UNSIGNED:
            raise ValueError("type must be either signed or unsigned, got %r" % sign)

        self.bitlength = bitlength
        self.type = sign
        self.n_values = n_values
        self.L = bitlength * n_values
        self.outs = None
        self.n_gates = None

    def num_input_bits(self):
        """See L{Circuit.num_input_bits}"""
        return 2 * self.L

    def inputs(self):
        """See L{Circuit.inputs}"""
        return ((self.L, "val_mod"), (self.L, "R_mod"))

    def num_output_bits(self):
        """See L{Circuit.num_output_bits}"""
        return self.L

    def num_gates(self):
        """See L{Circuit.num_gates}"""
        if self.n_gates is None:
            for i in self.next_gate():
                pass
        return self.n_gates

    def next_gate(self):
        """See L{Circuit.next_gate}"""
        first_gate_idx = self.num_input_bits()
        next_gate_num = 0
        outs = []
        akt_outs = []

        # first chunk
        if self.bitlength == 1:
            if self.type == SIGNED:
                yield self.output_gate((0, self.L), 0b1001)  # not z0
            else:
                yield self.output_gate((0, self.L), 0b0110)  # z0
            outs.append([first_gate_idx + next_gate_num])
            next_gate_num += 1
            if self.n_values > 1:
                yield self.output_gate((0, self.L), 0b0100)  # c0
                next_gate_num += 1
        else:
            yield self.output_gate((0, self.L), 0b0110)  # z0
            akt_outs.append(first_gate_idx + next_gate_num)
            next_gate_num += 1
            yield self.output_gate((0, self.L), 0b0100)  # c0
            next_gate_num += 1

            for j in xrange(1, self.bitlength - 1):
                pos = j
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01101001)  # zi
                akt_outs.append(first_gate_idx + next_gate_num)
                next_gate_num += 1
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01110001)  # ci
                next_gate_num += 1

            # invert leftmost output
            pos = self.bitlength - 1
            if self.type == SIGNED:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b10010110)  # not zi
            else:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01101001)  # zi
            akt_outs.append(first_gate_idx + next_gate_num)
            next_gate_num += 1

            outs.append(akt_outs)
            akt_outs = []

            if self.n_values > 1:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01110001)  # ci
                next_gate_num += 1

        # other chunks
        for i in xrange(1, self.n_values):
            for j in xrange(0, self.bitlength - 1):
                pos = i * self.bitlength + j
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01101001)  # zi
                akt_outs.append(first_gate_idx + next_gate_num)
                next_gate_num += 1
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01110001)  # ci
                next_gate_num += 1

            # invert leftmost output
            pos = i * self.bitlength + self.bitlength - 1
            if self.type == SIGNED:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b10010110)  # not zi
            else:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01101001)  # zi
            akt_outs.append(first_gate_idx + next_gate_num)
            next_gate_num += 1

            outs.append(akt_outs)
            akt_outs = []

            if i < self.n_values - 1:
                yield self.output_gate((pos, self.L + pos, first_gate_idx + 2 * pos - 1), 0b01110001)  # ci
                next_gate_num += 1
        self.n_gates = next_gate_num
        self.outs = outs

    def outputs(self):
        """See L{Circuit.outputs}"""
        if self.outs is None:
            for g in self.next_gate():
                pass
        out = map(lambda x: (x[1], "z" + str(x[0]), self.type), enumerate(self.outs))
        out.reverse()
        return out


class AddCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength, type_x, type_y, drop_msb=NODROP_MSB):
        """Circuit that computes z = x + y for unsigned or signed y
            optionally drop MSB

        @type x_bit_length: int
        @param x_bit_length: |x|

        @type y_bit_length: int
        @param y_bit_length: |y|

        raises ValueError: wrong bitlength
        """

        if x_bitlength < y_bitlength:
            raise NotImplementedError("|x| must be >= |y|")

        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")

        if type_x != UNSIGNED and type_x != SIGNED:
            raise ValueError("type of x must be either signed or unsigned")

        if type_y != UNSIGNED and type_y != SIGNED:
            raise ValueError("type of y must be either signed or unsigned")

        if drop_msb != NODROP_MSB and drop_msb != DROP_MSB:
            raise ValueError("drop_msb must be either NODROP_MSB or DROP_MSB")

        if drop_msb == DROP_MSB and type_y == SIGNED:
            raise NotImplementedError("This functionality has not been implemented yet")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength
        self.type_x = type_x
        self.type_y = type_y
        self.drop_msb = drop_msb
        self.outs = None
        self.n_gates = None

    def num_input_bits(self):
        """See L{Circuit.num_input_bits}"""

        return self.x_bitlength + self.y_bitlength

    def inputs(self):
        """See L{Circuit.inputs}"""
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def num_output_bits(self):
        """See L{Circuit.num_output_bits}"""
        if self.drop_msb == DROP_MSB:
            return self.x_bitlength
        else:
            return self.x_bitlength + 1

    def num_gates(self):
        """See L{Circuit.num_gates}"""
        if self.n_gates is None:
            for i in self.next_gate():
                pass
        return self.n_gates

    def next_gate(self):
        """See L{Circuit.next_gate}"""
        first_gate_idx = self.num_input_bits()
        next_gate_num = 0
        outs = []

        yield self.output_gate((0, self.x_bitlength), 0b0110)  # z0
        outs.append(first_gate_idx + next_gate_num)
        next_gate_num += 1

        if self.x_bitlength > 1 or self.drop_msb == NODROP_MSB:
            yield self.output_gate((0, self.x_bitlength), 0b0001)  # c0
            next_gate_num += 1

        for i in xrange(1, self.y_bitlength):
            yield self.output_gate((i, self.x_bitlength + i, first_gate_idx + 2 * i - 1), 0b01101001)  # zi
            outs.append(first_gate_idx + next_gate_num)
            next_gate_num += 1
            if i != self.y_bitlength - 1 or self.x_bitlength > self.y_bitlength or self.drop_msb == NODROP_MSB:
                yield self.output_gate((i, self.x_bitlength + i, first_gate_idx + 2 * i - 1), 0b00010111)  # ci
                next_gate_num += 1

        y_msb = self.x_bitlength + self.y_bitlength - 1

        # if input x is longer
        if self.x_bitlength > self.y_bitlength:
            for i in xrange(self.y_bitlength, self.x_bitlength):
                if self.type_y == UNSIGNED:
                    yield self.output_gate((i, first_gate_idx + next_gate_num - 1), 0b0110)  # zi
                    outs.append(first_gate_idx + next_gate_num)
                    next_gate_num += 1
                    if i != self.x_bitlength - 1 or self.drop_msb == NODROP_MSB:
                        yield self.output_gate((i, first_gate_idx + 2 * i - 1), 0b0001)  # ci
                        next_gate_num += 1
                else:
                    yield self.output_gate((i, y_msb, first_gate_idx + 2 * i - 1), 0b01101001)  # zi
                    outs.append(first_gate_idx + next_gate_num)
                    next_gate_num += 1
                    if i != self.x_bitlength - 1 or self.drop_msb == NODROP_MSB:
                        yield self.output_gate((i, y_msb, first_gate_idx + 2 * i - 1), 0b00010111)  # ci
                        next_gate_num += 1

        if self.drop_msb == NODROP_MSB:
            if self.type_y == SIGNED:
                yield self.output_gate((first_gate_idx + 2 * self.x_bitlength - 1, y_msb), 0b0110)
                outs.append(first_gate_idx + next_gate_num)
                next_gate_num += 1
            else:
                outs.append(first_gate_idx + next_gate_num - 1)

        self.n_gates = next_gate_num
        self.outs = outs

    def outputs(self):
        """See L{Circuit.outputs}"""
        if self.outs is None:
            for g in self.next_gate():
                pass
        if self.type_x == UNSIGNED and self.type_y == UNSIGNED:
            o_type = UNSIGNED
        else:
            o_type = SIGNED
        return ((self.outs, "z", o_type),)


class AddSubCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength, type_x=SIGNED, type_y=UNSIGNED, drop_msb=NODROP_MSB):
        """Circuit that computes z = x + y if ctrl = 0 and z = x - y if ctrl = 1
           optionally drop MSB
        """
        if x_bitlength < y_bitlength:
            raise ValueError("|x| must be >= |y|")

        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")

        if type_x != UNSIGNED and type_x != SIGNED:
            raise ValueError("type of x must be either signed or unsigned")

        if type_y != UNSIGNED and type_y != SIGNED:
            raise ValueError("type of y must be either signed or unsigned")
        if type_y != UNSIGNED:
            raise NotImplementedError()

        if drop_msb != NODROP_MSB and drop_msb != DROP_MSB:
            raise ValueError("drop_msb must be either NODROP_MSB or DROP_MSB")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength
        self.type_x = type_x
        self.type_y = type_y
        self.drop_msb = drop_msb

    def num_input_bits(self):
        return self.x_bitlength + self.y_bitlength + 1

    def inputs(self):
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"), (1, "ctrl"))

    def num_output_bits(self):
        if self.drop_msb == NODROP_MSB:
            return self.x_bitlength + 1
        else:
            return self.x_bitlength

    def outputs(self):
        first_gate_idx = self.x_bitlength + 2 * self.y_bitlength + 1
        last_gate_idx = first_gate_idx + 2 * self.x_bitlength - 1
        o = range(first_gate_idx, last_gate_idx, 2)
        if self.drop_msb == NODROP_MSB:
            if self.type_x == SIGNED:
                o.append(last_gate_idx + 2)
            else:
                o.append(last_gate_idx + 1)

        return ((o, "z", SIGNED),)

    def next_gate(self):
        ctrl_idx = self.x_bitlength + self.y_bitlength
        first_gate_idx = ctrl_idx + 1
        for i in xrange(self.y_bitlength):
            yield self.output_gate((self.x_bitlength + i, ctrl_idx), 0b0110)
        next_gate_idx = first_gate_idx + self.y_bitlength
        yield self.output_gate((0, first_gate_idx, ctrl_idx), 0b01101001)  # z0
        yield self.output_gate((0, first_gate_idx, ctrl_idx), 0b00010111)  # c0
        for i in xrange(1, self.y_bitlength):
            yield self.output_gate((i, first_gate_idx + i, next_gate_idx + 2 * i - 1), 0b01101001)  # zi
            yield self.output_gate((i, first_gate_idx + i, next_gate_idx + 2 * i - 1), 0b00010111)  # ci
        # if |x| > |y|
        for i in xrange(self.y_bitlength, self.x_bitlength):
            yield self.output_gate((i, ctrl_idx, next_gate_idx + 2 * i - 1), 0b01101001)  # zi
            yield self.output_gate((i, ctrl_idx, next_gate_idx + 2 * i - 1), 0b00010111)  # ci
        next_gate_idx += 2 * self.x_bitlength
        if self.drop_msb == NODROP_MSB:
            yield self.output_gate((next_gate_idx - 1, ctrl_idx), 0b0110)
            if self.type_x == SIGNED:
                msb_x = self.x_bitlength - 1
                yield self.output_gate((next_gate_idx, msb_x), 0b0110)

    def num_gates(self):
        n_gates = self.y_bitlength + 2 * self.x_bitlength
        if self.drop_msb == NODROP_MSB:
            n_gates += 1
            if self.type_x == SIGNED:
                n_gates += 1
        return n_gates


class AddSub0Circuit(DynamicCircuit):
    def __init__(self, bitlength):
        """Circuit that computes z = 0 + x if ctrl = 0 and z = 0 - x if ctrl = 1
        """
        if bitlength <= 0:
            raise ValueError("length of x must be > 0")

        self.bitlength = bitlength

    def num_input_bits(self):
        return self.bitlength + 1

    def inputs(self):
        return ((self.bitlength, "x"), (1, "ctrl"))

    def num_output_bits(self):
        return self.bitlength + 1

    def outputs(self):
        first_gate_idx = 2 * self.bitlength + 1
        last_gate_idx = first_gate_idx + 2 * self.bitlength - 1
        o = range(first_gate_idx, last_gate_idx, 2)
        o.append(last_gate_idx + 1)
        return ((o, "z", SIGNED),)

    def next_gate(self):
        ctrl_idx = self.bitlength
        first_gate_idx = ctrl_idx + 1
        for i in xrange(self.bitlength):
            yield self.output_gate((i, ctrl_idx), 0b0110)
        next_gate_idx = first_gate_idx + self.bitlength
        yield self.output_gate((first_gate_idx, ctrl_idx), 0b0110)  # z0
        yield self.output_gate((first_gate_idx, ctrl_idx), 0b0001)  # c0
        for i in xrange(1, self.bitlength):
            yield self.output_gate((first_gate_idx + i, next_gate_idx + 2 * i - 1), 0b0110)  # zi
            yield self.output_gate((first_gate_idx + i, next_gate_idx + 2 * i - 1), 0b0001)  # ci
        next_gate_idx += 2 * self.bitlength
        yield self.output_gate((next_gate_idx - 1, ctrl_idx), 0b0110)

    def num_gates(self):
        return 3 * self.bitlength + 1


class CmpCircuit(DynamicCircuit):
    # TODO: Add unsigned / signed comparisons
    LESS = 0
    LESSEQUAL = 1
    GREATER = 2
    GREATEREQUAL = 3
    EQUAL = 4
    NOTEQUAL = 5

    def __init__(self, x_bitlength, y_bitlength, cmp_type, signed_x, signed_y):
        """Circuit that computes z = (x cmp y)

        @type x_bit_length: int
        @param x_bit_length: the bit length of the minuend

        @type y_bit_length: int
        @param y_bit_length: the bit length of the subtracend

        raises ValueError: different bit length of x and y or
        either bit length == 0
        """

        if x_bitlength < y_bitlength:
            raise NotImplementedError("x_bitlength must be larger or equal then y_bitlength")

        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")

        self.signed_x = signed_x
        self.signed_y = signed_y

        if cmp_type == self.LESS:
            self.front_table = 0b0100
            self.first_table = 0b0100
            self.other_tables = 0b01110001
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b00101011
            elif signed_x == SIGNED:
                self.signed_table = 0b0111
            elif signed_y == SIGNED:
                self.signed_table = 0b0010
        elif cmp_type == self.LESSEQUAL:
            self.front_table = 0b0100
            self.first_table = 0b1101
            self.other_tables = 0b01110001
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b00101011
            elif signed_x == SIGNED:
                self.signed_table = 0b0111
            elif signed_y == SIGNED:
                self.signed_table = 0b0010
        elif cmp_type == self.GREATER:
            self.front_table = 0b0111
            self.first_table = 0b0010
            self.other_tables = 0b01001101
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b01001101
            elif signed_x == SIGNED:
                self.signed_table = 0b0010
            elif signed_y == SIGNED:
                self.signed_table = 0b0111
        elif cmp_type == self.GREATEREQUAL:
            self.front_table = 0b0111
            self.first_table = 0b1011
            self.other_tables = 0b01001101
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b01001101
            elif signed_x == SIGNED:
                self.signed_table = 0b0010
            elif signed_y == SIGNED:
                self.signed_table = 0b0111
        elif cmp_type == self.EQUAL:
            self.front_table = 0b0100
            self.first_table = 0b1001
            self.other_tables = 0b01000001
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b00001001
            elif signed_x == SIGNED:
                self.signed_table = 0b0010
            elif signed_y == SIGNED:
                self.signed_table = 0b0010
        elif cmp_type == self.NOTEQUAL:
            self.front_table = 0b0111
            self.first_table = 0b0110
            self.other_tables = 0b01111101
            if signed_x == SIGNED and signed_y == SIGNED:
                self.signed_table = 0b01101111
            elif signed_x == SIGNED:
                self.signed_table = 0b0111
            elif signed_y == SIGNED:
                self.signed_table = 0b0111
        else:
            raise ValueError("Wrong type")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength

    def num_input_bits(self):
        return self.x_bitlength + self.y_bitlength

    def inputs(self):
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def num_output_bits(self):
        return 1

    def num_gates(self):
        return self.x_bitlength

    def next_gate(self):
        ind = 0
        if self.signed_y == SIGNED:
            print "y_upper"
            y_upper = self.y_bitlength - 1
            ind += 1
        else:
            y_upper = self.y_bitlength
        if self.signed_x == SIGNED:
            print "x_upper"
            x_upper = self.x_bitlength - 1
            ind += 1
        else:
            x_upper = self.x_bitlength

        first_gate_idx = self.num_input_bits()
        yield self.output_gate((0, self.x_bitlength), self.first_table)  # c0
        for i in xrange(1, y_upper):
            yield self.output_gate((i, self.x_bitlength + i, first_gate_idx + i - 1), self.other_tables)  # ci
        for i in xrange(y_upper, x_upper):
            yield self.output_gate((i, first_gate_idx + i - 1), self.front_table)  # ci
        if self.signed_x == self.signed_y == SIGNED:
            yield self.output_gate(
                (3 * self.x_bitlength - ind, self.x_bitlength, self.x_bitlength + self.y_bitlength - 1),
                self.signed_table)  #cn
        elif self.signed_x == SIGNED:
            print "YEEHAA"
            yield self.output_gate((2 * self.x_bitlength - ind, self.x_bitlength - 1), self.signed_table)
        elif self.signed_y == SIGNED:
            yield self.output_gate((3 * self.x_bitlength - ind, self.x_bitlength + self.y_bitlength - 1),
                                   self.signed_table)


    def outputs(self):
        first_gate_idx = self.num_input_bits()
        ret = (first_gate_idx + self.x_bitlength - 1, )  # c_msb
        return ((ret, "z", UNDEF),)


class MultiplicationCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength):
        """Circuit that computes z = x * y, where x and y are unsigned integers

        @type x_bit_length: int
        @param x_bit_length: the bit length of the minuend

        @type y_bit_length: int
        @param y_bit_length: the bit length of the subtracend

        raises ValueError: different bit length of x and y or
        either bit length == 0
        """

        if x_bitlength < y_bitlength:
            raise NotImplementedError("x must have at least as many bits as y")
        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength

        self.outs = None
        self.n_gates = None

    def num_gates(self):
        if self.y_bitlength == 1:
            return self.x_bitlength
        else:
            if self.n_gates is None:
                for i in self.next_gate():
                    pass
            return self.n_gates

    def num_input_bits(self):
        return self.x_bitlength + self.y_bitlength

    def num_output_bits(self):
        if self.y_bitlength == 1:
            return self.x_bitlength + self.y_bitlength - 1
        else:
            return self.x_bitlength + self.y_bitlength

    def inputs(self):
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def next_gate(self):
        if self.y_bitlength == 1:
            for i in xrange(self.x_bitlength):
                yield self.output_gate((i, self.x_bitlength), 0b0001)
        else:
            first_gate_idx = self.y_bitlength + self.x_bitlength
            next_gate_idx = first_gate_idx
            # first row
            for i in xrange(self.x_bitlength):
                yield self.output_gate((i, self.x_bitlength), 0b0001)
            self.outs = [next_gate_idx]
            next_gate_idx += self.x_bitlength

            # other rows
            for j in xrange(1, self.y_bitlength):

                # right
                yield self.output_gate((0, self.x_bitlength + j), 0b0001)  # bit_mul = x_0 * y_j
                if j == 1:
                    u_idx = first_gate_idx + 1
                else:
                    u_idx = first_gate_idx + self.x_bitlength + 3 * self.x_bitlength * (j - 2) + 4
                yield self.output_gate((next_gate_idx, u_idx), 0b0110)  # z0 = sum(bit_mul + sum(x_1*y_0))
                yield self.output_gate((next_gate_idx, u_idx), 0b0001)  # c0 = carry(bit_mul + sum(x_1*y_0))
                self.outs.append(next_gate_idx + 1)
                next_gate_idx += 3

                # middle
                for i in xrange(1, self.x_bitlength - 1):
                    yield self.output_gate((i, self.x_bitlength + j), 0b0001)  # x_i * y_j
                    if j == 1:
                        u_idx = first_gate_idx + i + 1
                    else:
                        u_idx = first_gate_idx + self.x_bitlength + 3 * self.x_bitlength * (j - 2) + 3 * i + 4
                    yield self.output_gate((u_idx, next_gate_idx, next_gate_idx - 1), 0b01101001)  # zi
                    yield self.output_gate((u_idx, next_gate_idx, next_gate_idx - 1), 0b00010111)  # ci
                    # self.outs.append(next_gate_idx + 1)
                    next_gate_idx += 3

                # left
                if j == 1:
                    yield self.output_gate((self.x_bitlength - 1, self.x_bitlength + 1),
                                           0b0001)  # bit_mul = x_msb * y_1
                    yield self.output_gate((next_gate_idx, next_gate_idx - 1), 0b0110)  # z0 = sum(bit_mul + carry)
                    yield self.output_gate((next_gate_idx, next_gate_idx - 1), 0b0001)  # c0 = carry(bit_mul + carry)
                    next_gate_idx += 3
                else:
                    yield self.output_gate((self.x_bitlength - 1, self.x_bitlength + j),
                                           0b0001)  # bit_mul = x_msb * y_j
                    u_idx = first_gate_idx + self.x_bitlength + 3 * self.x_bitlength * (j - 2) + 3 * i + 5
                    yield self.output_gate((next_gate_idx, next_gate_idx - 1, u_idx),
                                           0b01101001)  # z = sum(bit_mul + carry)
                    yield self.output_gate((next_gate_idx, next_gate_idx - 1, u_idx),
                                           0b00010111)  # c = carry(bit_mul + carry)
                    next_gate_idx += 3

            # last row
            next_out_idx = next_gate_idx - 3 * (self.x_bitlength - 1) + 1
            for i in xrange(1, self.x_bitlength - 1):
                self.outs.append(next_out_idx)
                next_out_idx += 3
            self.outs.append(next_gate_idx - 2)
            self.outs.append(next_gate_idx - 1)

            self.n_gates = next_gate_idx - first_gate_idx

    def outputs(self):
        if self.y_bitlength == 1:
            return ((range(self.x_bitlength + 1, 2 * self.x_bitlength + 1), "z", UNSIGNED),)
        else:
            if self.outs is None:
                for i in self.next_gate():
                    pass
            return ((self.outs, "z", UNSIGNED),)


class HornerMergeCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength, m):
        """Computes x * 2^m + y
        """
        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")
        if m < 0:
            raise ValueError("m must be >= 0")

        if y_bitlength <= m:
            raise NotImplementedError("y longer than m")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength
        self.m = m
        self.outs = None
        self.n_gates = None

    def num_gates(self):
        if self.n_gates is None:
            for i in self.next_gate():
                pass
        return self.n_gates

    def num_input_bits(self):
        return self.x_bitlength + self.y_bitlength

    def num_output_bits(self):
        return self.x_bitlength + self.m

    def inputs(self):
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def outputs(self):
        if self.outs is None:
            for i in self.next_gate():
                pass
        return ((self.outs, "z", UNDEF),)

    def next_gate(self):
        total_inputs = self.x_bitlength + self.y_bitlength
        next_gate_num = 0

        # pass last m bits of y
        outs = []
        for i in xrange(self.m):
            outs.append(self.x_bitlength + i)

        # add remaining bits of y with x
        y_rest = []
        for i in xrange(self.m, self.y_bitlength):
            y_rest.append(self.x_bitlength + i)
        x_inputs = range(self.x_bitlength)
        both_inputs = x_inputs + y_rest

        c = AddCircuit(self.x_bitlength, self.y_bitlength - self.m, UNSIGNED, UNSIGNED, DROP_MSB)
        for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
            yield g
        c_outs = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
        outs += c_outs

        self.n_gates = c.num_gates()
        self.outs = outs


class FastMultiplicationCircuit(DynamicCircuit):
    def __init__(self, x_bitlength, y_bitlength, break_length=20):
        """Circuit that computes z = x * y, where x and y are unsigned integers
        the recursive Karatsuba algorithm switches to the base-case when bitlength <= break_length

        @type x_bit_length: int
        @param x_bit_length: the bit length of the minuend

        @type y_bit_length: int
        @param y_bit_length: the bit length of the subtracend

        @type break_length: int
        @param break_length: breakpoint at which to switch to the base case

        raises ValueError: invalid parameters
        """

        if x_bitlength < y_bitlength:
            raise NotImplementedError("x must have at least as many bits as y")
        if x_bitlength <= 0 or y_bitlength <= 0:
            raise ValueError("length of x and y must be > 0")
        if break_length < 4:
            raise ValueError("break length must be >= 4")

        self.x_bitlength = x_bitlength
        self.y_bitlength = y_bitlength
        self.break_length = break_length

        self.outs = None
        self.n_gates = None

    def num_gates(self):
        if self.n_gates is None:
            for i in self.next_gate():
                pass
        return self.n_gates

    def num_input_bits(self):
        return self.x_bitlength + self.y_bitlength

    def num_output_bits(self):
        if self.y_bitlength == 1:
            return self.x_bitlength + self.y_bitlength - 1
        else:
            return self.x_bitlength + self.y_bitlength

    def inputs(self):
        return ((self.x_bitlength, "x"), (self.y_bitlength, "y"))

    def next_gate(self):
        # base case
        if self.y_bitlength < self.break_length:
            c = MultiplicationCircuit(self.x_bitlength, self.y_bitlength)
            for g in c.next_gate():
                yield g
            self.outs = c.outputs()[0][0]
            self.n_gates = c.num_gates()

        else:
            # Karatsuba recursion:
            # x = x1 * 2^m + x0
            # y = y1 * 2^m + y0
            #
            # z2 = x1 * y1
            # z0 = x0 * y0
            # z1 = x1 * y0 + x0 * y1
            # = (x1 + x0)*(y1+y0) - z2 - z0
            #
            # z = z2 * 2^(2m) + z1 * 2^m  + z0
            total_inputs = self.x_bitlength + self.y_bitlength
            next_gate_num = 0

            m = self.y_bitlength >> 1
            x0 = range(0, m)
            x1 = range(m, self.x_bitlength)
            y0 = range(self.x_bitlength, self.x_bitlength + m)
            y1 = range(self.x_bitlength + m, self.x_bitlength + self.y_bitlength)

            # z2 = x1 * y1
            c = FastMultiplicationCircuit(len(x1), len(y1), self.break_length)
            both_inputs = x1 + y1
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            z2 = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # z0 = x0 * y0
            c = FastMultiplicationCircuit(len(x0), len(y0), self.break_length)
            both_inputs = x0 + y0
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            z0 = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # ---------------------------------------
            # z1 = (x1 + x0)*(y1+y0) - z2 - z0

            # va = x1 + x0
            c = AddCircuit(len(x1), len(x0), UNSIGNED, UNSIGNED)
            both_inputs = x1 + x0
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            va = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # vb = y1 + y0
            c = AddCircuit(len(y1), len(y0), UNSIGNED, UNSIGNED)
            both_inputs = y1 + y0
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            vb = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # vm = va * vb
            c = FastMultiplicationCircuit(len(va), len(vb), self.break_length)
            both_inputs = va + vb
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            vm = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # vma = vm - z2
            c = SubCircuit(len(vm), len(z2), UNSIGNED, DROP_MSB)  # won't underflow
            both_inputs = vm + z2
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            vma = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # z1 = vma - z0
            c = SubCircuit(len(vma), len(z0), UNSIGNED, DROP_MSB)  # won't underflow
            both_inputs = vma + z0
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            z1 = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # ---------------------------------------
            # z = z2 * 2^(2m) + z1 * 2^m  + z0
            #   = (z2 * 2^m + z1) * 2^m + z0
            # z0 >= 0, z1 >= 0, z2 >= 0

            # m1 = HornerMergeCircuit(z2,z1,m)
            c = HornerMergeCircuit(len(z2), len(z1), m)
            both_inputs = z2 + z1
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            m1 = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            # z = HornerMergeCircuit(m1,z0,m)
            c = HornerMergeCircuit(len(m1), len(z0), m)
            both_inputs = m1 + z0
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            z = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += c.num_gates()

            self.n_gates = next_gate_num
            self.outs = z

    def outputs(self):
        if self.outs is None:
            for i in self.next_gate():
                pass
        return ((self.outs, "z", UNSIGNED),)


# def determine_minimum_break_value():
#        # determine minimum break value
#        for x_len in xrange(3,100):
#            y_len = x_len
#            min_break = [y_len]
#            c = KaratsubaMultiplicationCircuit(x_len, y_len, y_len)
#            min_gates = c.costs_XORtransformed()
#            school_gates = min_gates
#            for break_len in xrange(3,y_len):
#                c = KaratsubaMultiplicationCircuit(x_len, y_len, break_len)
#                gates = c.costs_XORtransformed()
#                if gates == min_gates:
#                    min_break.append(break_len)
#                elif gates < min_gates:
#                    min_gates = gates
#                    min_break = [break_len]
#            delta = float(school_gates - min_gates)*100/school_gates
#            print x_len, " => ", min_break, ", delta=", delta, "total=", min_gates


class MuxCircuit(DynamicCircuit):
    def __init__(self, bitlength):
        """Circuit that computes z = x_0 if ctrl=0 and z = x_1 if ctrl=1
        """
        if bitlength <= 0:
            raise ValueError("Bitlength must be positive")
        self.bitlength = bitlength

    def num_gates(self):
        return self.bitlength

    def num_input_bits(self):
        return 2 * self.bitlength + 1

    def inputs(self):
        return ((self.bitlength, "x_0"), (self.bitlength, "x_1"), (1, "ctrl"))

    def num_output_bits(self):
        return self.bitlength

    def next_gate(self):
        s_index = 2 * self.bitlength
        for i in xrange(0, self.bitlength):
            yield self.output_gate((i, i + self.bitlength, s_index), 0b00011011)

    def outputs(self):
        first_gate_idx = 2 * self.bitlength + 1
        return ((range(first_gate_idx, first_gate_idx + self.bitlength), "z", UNDEF),)


class MinMaxValueCircuit(DynamicCircuit):
    #TODO: Add unsigned / signed
    MIN = 0
    MAX = 1

    def __init__(self, n, bitlength, minmax_type, signed):
        """Circuit that computes z=min_i x_i if minmax_type=MIN and z=max_i x_i if minmax_type=MAX
        """
        if bitlength <= 0:
            raise ValueError("Bitlength must be > 0")
        if n < 2:
            raise ValueError("Number of inputs must be >= 2")
        if minmax_type != self.MIN and minmax_type != self.MAX:
            raise ValueError("Type must be MIN or MAX")
        self.minmax_type = minmax_type
        self.n = n
        self.bitlength = bitlength
        self.outs = None
        self.n_gates = None
        self.signed = signed

    def num_input_bits(self):
        return self.n * self.bitlength

    def inputs(self):
        ret = []
        for ix in xrange(self.n):
            ret.append((self.bitlength, "x_" + str(ix)))
        return ret

    def num_output_bits(self):
        return self.bitlength

    def next_gate(self):
        total_inputs = self.num_input_bits()

        if self.minmax_type == self.MIN:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.GREATEREQUAL, self.signed, self.signed)
        elif self.minmax_type == self.MAX:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.LESS, self.signed, self.signed)
        c_num_gates = c.num_gates()

        m = MuxCircuit(self.bitlength)
        m_num_gates = m.num_gates()

        next_gate_num = 0
        left_inputs = range(self.bitlength)

        for i in xrange(1, self.n):
            right_inputs = range(i * self.bitlength, (i + 1) * self.bitlength)
            both_inputs = left_inputs + right_inputs

            # Compare
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            cmp_output = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0][0]
            next_gate_num += c_num_gates

            # Multiplex
            m_inputs = both_inputs + [cmp_output]
            for g in m.subcircuit_next_gate(m_inputs, next_gate_num, total_inputs):
                yield g
            left_inputs = m.subcircuit_outputs(m_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += m_num_gates

        # determine outputs
        self.outs = left_inputs
        self.n_gates = next_gate_num

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return ((self.outs, "z", UNDEF),)


class MinMaxValueIndexCircuit(DynamicCircuit):
    #TODO: Add unsigned / signed
    MIN = 0
    MAX = 1

    def __init__(self, n, bitlen, minmax_type, signed):
        """Circuit that computes (val,idx)=min_i x_i if minmax_type=MIN and (val,idx)=max_i x_i if minmax_type=MAX
        """
        if bitlen <= 0:
            raise ValueError("Bitlength must be > 0")
        if n < 2:
            raise ValueError("Number of inputs must be >= 2")
        if minmax_type != self.MIN and minmax_type != self.MAX:
            raise ValueError("Type must be MIN or MAX")
        self.minmax_type = minmax_type
        self.n = n
        self.log_n1 = bitlength(n - 1)
        self.bitlength = bitlen
        self.outs = None
        self.n_gates = None
        self.signed = signed

    def num_input_bits(self):
        return self.n * self.bitlength

    def inputs(self):
        ret = []
        for ix in xrange(self.n):
            ret.append((self.bitlength, "x_" + str(ix)))
        return ret

    def num_output_bits(self):
        return self.bitlength + self.log_n1

    def next_gate(self):
        total_inputs = self.num_input_bits()

        if self.minmax_type == self.MIN:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.GREATER, self.signed, self.signed)
        elif self.minmax_type == self.MAX:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.LESS, self.signed, self.signed)
        c_num_gates = c.num_gates()

        m = MuxCircuit(self.bitlength)
        m_num_gates = m.num_gates()

        next_gate_num = 0

        prev_layer_values = []  # list of values in previous layer
        prev_layer_indices = []  # list of indices in previous layer

        # first layer
        for i in xrange(self.n / 2):
            # Compare
            left_inputs = range(2 * i * self.bitlength, (2 * i + 1) * self.bitlength)
            right_inputs = range((2 * i + 1) * self.bitlength, (2 * (i + 1)) * self.bitlength)
            both_inputs = left_inputs + right_inputs
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            c_output = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0][0]
            next_gate_num += c_num_gates

            prev_layer_indices.append([c_output])

            # MUX
            m_inputs = both_inputs + [c_output]
            for g in m.subcircuit_next_gate(m_inputs, next_gate_num, total_inputs):
                yield g
            m_outputs = m.subcircuit_outputs(m_inputs, next_gate_num, total_inputs)[0]
            next_gate_num += m_num_gates

            prev_layer_values.append(m_outputs)

        # last gate in last layer
        if self.n % 2 == 1:
            v = range(self.bitlength * (self.n - 1), self.bitlength * self.n)
            prev_layer_values.append(v)
            prev_layer_indices.append([None])

        # remaining layers
        for d in xrange(1, self.log_n1):
            this_layer_values = []
            this_layer_indices = []

            values_in_layer = len(prev_layer_values)

            for i in xrange(values_in_layer / 2):  # for each pair in this layer
                # Compare
                left_inputs = prev_layer_values[2 * i]
                right_inputs = prev_layer_values[2 * i + 1]
                both_inputs = left_inputs + right_inputs
                for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                    yield g
                c_output = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0][0]
                next_gate_num += c_num_gates

                # MUX index
                left_index = prev_layer_indices[2 * i]
                right_index = prev_layer_indices[2 * i + 1]
                for j in xrange(d):
                    lj = left_index[j]
                    rj = right_index[j]
                    if rj is None:
                        yield self.output_gate((lj, c_output), 0b0010)
                    else:
                        yield self.output_gate((lj, rj, c_output), 0b00011011)
                mux_outs = range(next_gate_num + total_inputs, next_gate_num + total_inputs + d)
                next_gate_num += d
                this_layer_indices.append(mux_outs + [c_output])

                # MUX values
                m_inputs = both_inputs + [c_output]
                for g in m.subcircuit_next_gate(m_inputs, next_gate_num, total_inputs):
                    yield g
                m_outputs = m.subcircuit_outputs(m_inputs, next_gate_num, total_inputs)[0]
                next_gate_num += m_num_gates

                this_layer_values.append(m_outputs)

            # last gate in this layer
            if values_in_layer % 2 == 1:
                last_value = prev_layer_values[values_in_layer - 1]
                last_idx = prev_layer_indices[values_in_layer - 1]
                this_layer_values.append(last_value)
                this_layer_indices.append(last_idx + [None])

            prev_layer_values = this_layer_values
            prev_layer_indices = this_layer_indices

        # determine outputs
        self.outs = (prev_layer_values, prev_layer_indices)
        self.n_gates = next_gate_num

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return ((self.outs[0][0], "val", UNDEF), (self.outs[1][0], "idx", UNSIGNED))


class MinMaxIndexCircuit(DynamicCircuit):
    #TODO: Add unsigned / signed
    MIN = 0
    MAX = 1

    def __init__(self, n, bitlen, minmax_type, signed):
        """Circuit that computes idx=min_i x_i if minmax_type=MIN and idx=max_i x_i if minmax_type=MAX
        """

        if bitlen <= 0:
            raise ValueError("Bitlength must be > 0")
        if n < 2:
            raise ValueError("Number of inputs must be >= 2")
        if minmax_type != self.MIN and minmax_type != self.MAX:
            raise ValueError("Type must be MIN or MAX")
        self.minmax_type = minmax_type
        self.n = n
        self.log_n1 = bitlength(n - 1)
        self.bitlength = bitlen
        self.outs = None
        self.n_gates = None
        self.signed = signed

    def num_input_bits(self):
        return self.n * self.bitlength

    def inputs(self):
        ret = []
        for ix in xrange(self.n):
            ret.append((self.bitlength, "x_" + str(ix)))
        return ret

    def num_output_bits(self):
        return self.log_n1

    def next_gate(self):
        total_inputs = self.num_input_bits()

        if self.minmax_type == self.MIN:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.GREATER, self.signed, self.signed)
        elif self.minmax_type == self.MAX:
            c = CmpCircuit(self.bitlength, self.bitlength, CmpCircuit.LESS, self.signed, self.signed)
        c_num_gates = c.num_gates()

        m = MuxCircuit(self.bitlength)
        m_num_gates = m.num_gates()

        next_gate_num = 0

        prev_layer_values = []  # list of values in previous layer
        prev_layer_indices = []  # list of indices in previous layer

        # first layer
        for i in xrange(self.n / 2):
            # Compare
            left_inputs = range(2 * i * self.bitlength, (2 * i + 1) * self.bitlength)
            right_inputs = range((2 * i + 1) * self.bitlength, (2 * (i + 1)) * self.bitlength)
            both_inputs = left_inputs + right_inputs
            for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            c_output = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0][0]
            next_gate_num += c_num_gates

            prev_layer_indices.append([c_output])

            # MUX value
            if self.n != 2:
                m_inputs = both_inputs + [c_output]
                for g in m.subcircuit_next_gate(m_inputs, next_gate_num, total_inputs):
                    yield g
                m_outputs = m.subcircuit_outputs(m_inputs, next_gate_num, total_inputs)[0]
                next_gate_num += m_num_gates

                prev_layer_values.append(m_outputs)

        # last gate in last layer
        if self.n % 2 == 1:
            v = range(self.bitlength * (self.n - 1), self.bitlength * self.n)
            prev_layer_values.append(v)
            prev_layer_indices.append([None])

        # remaining layers
        for d in xrange(1, self.log_n1):
            this_layer_values = []
            this_layer_indices = []

            values_in_layer = len(prev_layer_values)

            for i in xrange(values_in_layer / 2):  # for each pair in this layer
                # Compare
                left_inputs = prev_layer_values[2 * i]
                right_inputs = prev_layer_values[2 * i + 1]
                both_inputs = left_inputs + right_inputs
                for g in c.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                    yield g
                c_output = c.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0][0]
                next_gate_num += c_num_gates

                # MUX index
                left_index = prev_layer_indices[2 * i]
                right_index = prev_layer_indices[2 * i + 1]
                for j in xrange(d):
                    lj = left_index[j]
                    rj = right_index[j]
                    if rj is None:
                        yield self.output_gate((lj, c_output), 0b0010)
                    else:
                        yield self.output_gate((lj, rj, c_output), 0b00011011)
                mux_outs = range(next_gate_num + total_inputs, next_gate_num + total_inputs + d)
                next_gate_num += d
                this_layer_indices.append(mux_outs + [c_output])

                # MUX values but not in last layer
                if d != self.log_n1 - 1:
                    m_inputs = both_inputs + [c_output]
                    for g in m.subcircuit_next_gate(m_inputs, next_gate_num, total_inputs):
                        yield g
                    m_outputs = m.subcircuit_outputs(m_inputs, next_gate_num, total_inputs)[0]
                    next_gate_num += m_num_gates

                    this_layer_values.append(m_outputs)

            # last gate in this layer
            if values_in_layer % 2 == 1:
                last_value = prev_layer_values[values_in_layer - 1]
                last_idx = prev_layer_indices[values_in_layer - 1]
                this_layer_values.append(last_value)
                this_layer_indices.append(last_idx + [None])

            prev_layer_values = this_layer_values
            prev_layer_indices = this_layer_indices

        # determine outputs
        self.outs = prev_layer_indices
        self.n_gates = next_gate_num

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return ((self.outs[0], "idx", UNSIGNED),)


class VectorMultiplicationCircuit(DynamicCircuit):
    def __init__(self, n, bitlength, MULT=FastMultiplicationCircuit):
        """Circuit that computes z = sum(x_i * y_i),
           where x_i and y_i are given in sign-magnitude representation
        @type n: uint
        @param n: dimension of input vectors

        @type bitlength: uint
        @param bitlength: bitlength of input vectors
        """
        if bitlength <= 0:
            raise ValueError("Bitlength must be > 0")
        if n < 1:
            raise ValueError("Number of inputs must be >= 1")
        self.n = n
        self.bitlength = bitlength
        self.outs = None
        self.n_gates = None
        self.MULT = MULT

    def num_input_bits(self):
        return 2 * self.n * (self.bitlength + 1)

    def inputs(self):
        ret = []
        for i in xrange(self.n):
            i_str = str(i)
            ret.append((1, "sign(x_" + i_str + ")"))
            ret.append((self.bitlength, "abs(x_" + i_str + ")"))
            ret.append((1, "sign(y_" + i_str + ")"))
            ret.append((self.bitlength, "abs(y_" + i_str + ")"))
        return ret

    def num_output_bits(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return len(self.outs)

    def next_gate(self):
        total_inputs = self.num_input_bits()
        next_gate_num = 0

        m = self.MULT(self.bitlength, self.bitlength)
        m_num_gates = m.num_gates()

        # multiply magnitudes
        left_inputs = range(1, 1 + self.bitlength)
        right_inputs = range(2 + self.bitlength, 2 + 2 * self.bitlength)
        both_inputs = left_inputs + right_inputs
        for g in m.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
            yield g
        m_output = m.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
        m_output_len = len(m_output)
        next_gate_num += m_num_gates

        # multiply signs
        yield self.output_gate((0, 1 + self.bitlength), 0b0110)
        sign_output = total_inputs + next_gate_num
        next_gate_num += 1

        # convert into two's complement
        both_inputs = m_output + [sign_output]
        s = AddSub0Circuit(m_output_len)
        s_num_gates = s.num_gates()
        for g in s.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
            yield g
        last_output = s.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
        last_output_len = s.num_output_bits()
        next_gate_num += s_num_gates

        # optimization: drop some msbs during accumulation
        max_value = (1 << self.bitlength) - 1
        max_product = max_value * max_value
        max_sum = max_product
        max_sum_bitlen = bitlength(max_sum)
        assert last_output_len == max_sum_bitlen + 1

        for i in xrange(1, self.n):
            # multiply magnitudes
            left_inputs = range(i * 2 * (self.bitlength + 1) + 1, i * 2 * (self.bitlength + 1) + 1 + self.bitlength)
            right_inputs = range(i * 2 * (self.bitlength + 1) + 2 + self.bitlength,
                                 i * 2 * (self.bitlength + 1) + 2 + 2 * self.bitlength)
            both_inputs = left_inputs + right_inputs
            for g in m.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            m_output = m.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            m_output_len = len(m_output)
            next_gate_num += m_num_gates

            # multiply signs
            left_sign = i * 2 * (self.bitlength + 1)
            right_sign = i * 2 * (self.bitlength + 1) + 1 + self.bitlength
            yield self.output_gate((left_sign, right_sign), 0b0110)
            sign_output = total_inputs + next_gate_num
            next_gate_num += 1

            # accumulate
            both_inputs = last_output + m_output + [sign_output]

            # optimization: drop some msbs during accumulation
            if bitlength(max_sum + max_product) == max_sum_bitlen:
                s = AddSubCircuit(last_output_len, m_output_len, AddSubCircuit.DROP_MSB)
            else:
                s = AddSubCircuit(last_output_len, m_output_len, AddSubCircuit.NODROP_MSB)
                max_sum_bitlen += 1

            s_num_gates = s.num_gates()
            for g in s.subcircuit_next_gate(both_inputs, next_gate_num, total_inputs):
                yield g
            last_output = s.subcircuit_outputs(both_inputs, next_gate_num, total_inputs)[0]
            last_output_len = s.num_output_bits()
            next_gate_num += s_num_gates

            max_sum += max_product

        # determine outputs
        self.outs = last_output
        self.n_gates = next_gate_num

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return ((self.outs, "z", SIGNED),)


from reader import *

if __name__ == '__main__':
    c = GateCircuit(2, ([0, 0, 0, 1], [0, 1, 1, 1]))
    c.check()
