# -*- coding: utf-8 -*-

from string import rstrip

from tasty.circuit import Circuit, SIGNED, UNSIGNED, UNDEF
from tasty import state


__all__ = ["PSSW09Circuit", "FairplayMP20Circuit", "FairplayMP21Circuit"]


class PSSW09Circuit(Circuit):
    """ Read circuit in [PSSW09] format """

    def __read_head(self):
        f = file(self.filename)
        self.f = f

        # num gates, num wires
        l = f.readline()
        l_items = l.split(" ")
        assert len(l_items) == 2
        self.n_gates = int(l_items[0])
        self.n_wires = int(l_items[1])

        # inputs and outputs
        l = f.readline()
        l_items = l.split(" ")
        assert len(l_items) == 4
        self.a_inputs = int(l_items[0])
        self.b_inputs = int(l_items[1])
        self.a_outputs = int(l_items[2])
        self.b_outputs = int(l_items[3])

        l = f.readline()

        self.state = 0

    def __init__(self, filename):
        self.filename = filename
        self.__read_head()

    def num_gates(self):
        return self.n_gates

    def num_input_bits(self):
        return self.a_inputs + self.b_outputs

    def inputs(self):
        return ((self.a_inputs, "a_inputs"), (self.b_inputs, "b_inputs"))

    def num_output_bits(self):
        return self.a_outputs + self.b_outputs

    def outputs(self):
        start_a = self.n_gates + self.a_inputs + self.b_inputs - self.a_outputs - self.b_outputs
        end_a = start_a + self.a_outputs
        end_b = end_a + self.b_outputs
        outs = []
        if start_a != end_a:
            outs.append((range(start_a, end_a), "a_outputs", UNDEF))
        if end_a != end_b:
            outs.append((range(end_a, end_b), "b_outputs", UNDEF))
        return outs

    def next_gate(self):
        # reset f if necessary
        if self.state != 0:
            self.f.close()
            self.__read_head()

        self.state = 1

        next_gate = self.a_inputs + self.b_inputs

        shift_index = [None for i in xrange(self.n_wires)]

        for i in xrange(self.n_gates):
            l = self.f.readline()
            l_items = l.split(" ")
            if len(l_items) == 1:  # skip empty line
                continue
            d = int(l_items[0])
            e = int(l_items[1])

            assert e == 1
            gate_num = int(l_items[2 + d])

            # there might be holes in the wires
            if gate_num != next_gate:
                # shift gate indices
                shift_index[gate_num] = next_gate

            # compute gate table
            str_gate_tab = l_items[2 + d + e]
            gate_tab = 0
            for j in xrange(1 << d):
                gate_tab = (gate_tab << 1) | int(str_gate_tab[j])

            replaced_inputs = []
            for inp in l_items[2:2 + d]:
                inp_int = int(inp)
                replaced_inp = shift_index[inp_int]
                if replaced_inp is None:
                    replaced_inputs.append(inp_int)
                else:
                    replaced_inputs.append(replaced_inp)
            yield (replaced_inputs, gate_tab)
            next_gate += 1


class FileCircuitPSS09(Circuit):
    """ Read circuit in [PSS09] CMP format """

    def __read_head(self):
        f = file(self.filename)
        self.f = f

        # num gates
        l = f.readline()
        n_gates = int(l)

        # party_a i/o
        l = f.readline()
        l_items = l.split(" ")
        assert len(l_items) == 4
        a_inputs = int(l_items[2])
        a_outputs = int(l_items[3])

        # party_b i/o
        l = f.readline()
        l_items = l.split(" ")
        assert len(l_items) == 4
        b_inputs = int(l_items[2])
        b_outputs = int(l_items[3])

        l = f.readline()  # empty line

        # determine inputs
        inputs = []
        n_inputs = a_inputs + b_inputs
        next_input = 0
        while next_input < n_inputs:
            l = f.readline()
            l_items = l.split(" ")
            l_ins = int(l_items[2])
            l_desc = l_items[1]
            assert len(l_items) == l_ins + 3
            l_inputs = map(lambda x: int(rstrip(x)), l_items[3:3 + l_ins])
            assert l_inputs == range(next_input, next_input + l_ins), "Inputs must be ordered consecutively"
            inputs.append((l_ins, l_desc))
            next_input += l_ins

        l = f.readline()  # empty line

        self.state = 0

        self.n_gates = n_gates
        self.n_inputs = n_inputs
        self.n_outputs = a_outputs + b_outputs
        self.ins = inputs
        self.outs = None

    def __init__(self, filename):
        self.filename = filename
        self.__read_head()

    def check(self):
        Circuit.check(self)

    def num_gates(self):
        return self.n_gates

    def num_input_bits(self):
        return self.n_inputs

    def inputs(self):
        return self.ins

    def num_output_bits(self):
        return self.n_outputs

    def next_gate(self):
        # reset f if necessary
        if self.state != 0:
            self.f.close()
            self.__read_head()

        for i in xrange(self.num_gates()):
            l = self.f.readline()
            l_items = l.split(" ")
            d = int(l_items[1])
            assert len(l_items) == d + 4
            tab = 0
            tab_str = l_items[-1]
            for i in xrange(1 << d):
                tab <<= 1
                if tab_str[i] == '1':
                    tab |= 1
            ins = map(int, l_items[2:2 + d])
            yield ins, tab

        self.f.readline()  # empty line

        self.outs = []
        rem_outputs = self.n_outputs
        while rem_outputs > 0:
            l = self.f.readline()
            l_items = l.split(" ")
            l_outs = int(l_items[2])
            l_desc = l_items[1]
            rem_outputs -= l_outs
            assert len(l_items) == l_outs + 3
            self.outs.append((map(lambda x: int(rstrip(x)), l_items[3:3 + l_outs]), l_desc, UNDEF))
        self.f.close()

        self.state = 1

    def outputs(self):
        # reset f if necessary
        if self.outs is None:
            for g in self.next_gate():
                pass

        return self.outs


class FairplayMP20Circuit(Circuit):
    """ Read circuit in [BNP08] CNV format """

    def read_ins(self):
        if self.state is not None:
            self.f.close()
        self.f = file(self.filename)
        l = rstrip(self.f.readline())
        assert l == "FMT - Input:"
        l = rstrip(self.f.readline())
        ins = []
        next_in = 0
        while l != "Gates:":
            l_items = l.split(',')
            assert l_items[0] == "input"
            l_desc = l_items[1] + ":" + l_items[2]
            l_ins = len(l_items) - 3
            l_inputs = map(lambda x: int(x), l_items[3:])
            assert l_inputs == range(next_in, next_in + l_ins)
            next_in += l_ins
            ins.append((l_ins, l_desc))
            l = rstrip(self.f.readline())
        self.ins = ins
        self.n_inputs = next_in
        self.state = 0  # ins read

    def __init__(self, filename):
        self.filename = filename
        self.state = None
        self.n_gates = None
        self.n_outputs = None
        self.outs = None
        self.read_ins()

    def num_input_bits(self):
        return self.n_inputs

    def num_gates(self):
        if self.n_gates is None:
            for g in self.next_gate():
                pass
        return self.n_gates

    def inputs(self):
        return self.ins

    def num_output_bits(self):
        if self.n_outputs is None:
            for g in self.next_gate():
                pass
        return self.n_outputs

    def outputs(self):
        if self.outs is None:
            for g in self.next_gate():
                pass
        return self.outs

    def next_gate(self):
        if self.state != 0:
            self.read_ins()

        # read gates
        l = rstrip(self.f.readline())
        n_gate = self.n_inputs
        while l != "FMT - Output:":
            l_items = l.split(",")
            # gate,32,2,0 1 1 0,9,8
            assert l_items[0] == "gate"
            l_gate_num = int(l_items[1])
            assert l_gate_num == n_gate
            l_ins = int(l_items[2])
            l_inputs = map(lambda x: int(x), l_items[4:])
            l_inputs.reverse()
            l_tab = l_items[3]
            tab = 0
            for i in xrange(1 << l_ins):
                tab = (tab << 1) | int(l_tab[2 * i])
            yield l_inputs, tab

            l = rstrip(self.f.readline())
            n_gate += 1

        # read outputs
        outs = []
        n_outputs = 0

        ZERO_GATE = None
        ONE_GATE = None

        l = rstrip(self.f.readline())
        l_items = l.split(",")
        while l_items[0] == "output":
            # output,voters[0],output,106,-2
            l_desc = l_items[1] + ":" + l_items[2]
            l_outs = map(lambda x: int(x), l_items[3:])

            # replace negative wire values with constant gates
            for pos in xrange(len(l_outs)):
                if l_outs[pos] == -2:
                    state.log.debug("Warning: found wire -2, assuming this is constant 0")
                    if ZERO_GATE is None:
                        yield [], 0
                        ZERO_GATE = n_gate
                        n_gate += 1
                    l_outs[pos] = ZERO_GATE
                elif l_outs[pos] == -1:
                    state.log.debug("Warning: found wire -1, assuming this is constant 1")
                    if ONE_GATE is None:
                        yield [], 1
                        ONE_GATE = n_gate
                        n_gate += 1
                    l_outs[pos] = ONE_GATE
                else:
                    assert l_outs[pos] >= 0 and l_outs[pos] < n_gate
            outs.append((l_outs, l_desc, UNDEF))
            n_outputs += len(l_outs)

            l = rstrip(self.f.readline())
            l_items = l.split(",")

        self.n_gates = n_gate - self.n_inputs
        self.n_outputs = n_outputs
        self.outs = outs

        self.state = 1


class FairplayMP21Circuit(Circuit):
    """ Read circuit in Fairplay 2.1 format """

    def next_items(self):
        l = rstrip(self.f.readline())
        while len(l) >= 2 and l[0] == "/" and l[1] == "/":  # skip comments
            l = rstrip(self.f.readline())
        return l.split(':')

    def __init__(self, filename):
        self.filename = filename

        f = file(self.filename)
        self.f = f

        # read inputs
        inputs = []
        n_inputs = 0
        it = self.next_items()
        while it[0] == 'input_player':
            p_name = it[1]
            p_ninputs = int(it[2])
            p_inp_values = int(it[3])
            akt_inputs = 0
            for i in xrange(p_inp_values):
                it = self.next_items()
                assert it[0] == "input"
                in_name = it[1]
                in_len = int(it[2])
                akt_inputs += in_len
                inputs.append((in_len, in_name))
            assert akt_inputs == p_ninputs
            n_inputs += p_ninputs
            it = self.next_items()

        self.inp = inputs
        self.ninp = n_inputs

        # skip empty line
        if len(it) == 1:
            it = self.next_items()

        # read outputs
        outputs = []
        n_outputs = 0
        while it[0] == 'result_player':
            p_name = it[1]
            p_outp_values = int(it[2])
            for i in xrange(p_outp_values):
                # result:alice.output:1:36
                it = self.next_items()
                assert it[0] == "result"
                out_name = it[1]
                out_len = int(it[2])
                n_outputs += out_len
                assert len(it) == out_len + 3
                out_wires = map(int, it[3:])
                # outputs.append((out_wires, out_name, UNDEF))
                outputs.append((out_wires, out_name, SIGNED))
            it = self.next_items()

        self.outs = outputs
        self.noutp = n_outputs

        # skip empty line
        if len(it) == 1:
            it = self.next_items()

        # read gates
        gates = []
        next_gid = 0
        while it[0] == 'gate':
            # gate:0:12:0:1:1
            g_id = int(it[1])
            g_owire = int(it[2])
            g_a = int(it[3])
            g_b = int(it[4])
            g_tab = int(it[5])
            assert g_id == next_gid
            assert g_owire == next_gid + n_inputs
            gates.append(((g_a, g_b), g_tab))
            next_gid += 1
            it = self.next_items()

        self.gates = gates

    def num_input_bits(self):
        return self.ninp

    def inputs(self):
        return self.inp

    def num_output_bits(self):
        return self.noutp

    def outputs(self):
        return self.outs

    def num_gates(self):
        return len(self.gates)

    def next_gate(self):
        for g in self.gates:
            yield g


if __name__ == '__main__':
    import tasty.utils
    import logging

    state.log.setLevel(logging.ERROR)
