# -*- coding: utf-8 -*-

"""Implements TastyFunction base class and tastys \*circuit classes"""

from copy import copy

from tasty.types.metatypes import Value
from tasty.types.party import Party
from tasty import state
import tasty.types
from tasty.exc import TastySyntaxError
from tasty.circuit import SIGNED, Circuit
from tasty.protocols.gc_protocols import GCProtocol


__all__ = ["TastyFunction", "PlainCircuit", "GarbledCircuit"]


class TastyFunction(object):
    """Important. TastyFunctions must be instantiated during protocol
    analyzation, so we get member methods here in contrast to normal
    tasty types' which are static methods"""

    def calc_costs(self, methodname, input_types, bit_lengths, dims, role, passive, precompute):
        """tastyc stuff"""
        raise NotImplementedError()

    @staticmethod
    def affects(methodname, input_types, role):
        """tastyc stuff"""
        if __debug__:
            state.log.debug("TastyFunction.affects(%r, %r, %r)", methodname, input_types, role)
        return Value.S_ONLINE if role else Value.C_ONLINE

    def returns(self, methodname, input_types, bit_lengths, dims, signeds):
        """tastyc stuff"""
        raise NotImplementedError()


class CircuitMixin(object):
    """Infrastructure for circuit implementations"""

    def __init__(self, circuit, inputs=None, outputs=None):
        if not isinstance(circuit, Circuit):
            raise TypeError("Provide only Circuit objects")
        self.circuit = circuit
        self.inputs = self.outputs = None

        if inputs:
            if not iter(inputs):
                raise TypeError("inputs must be iterable")
            self.inputs = tuple(inputs)

        if outputs:
            if not iter(outputs):
                raise TypeError("outputs must be iterable")
            self.outputs = tuple(outputs)


    def map_inputs(self, inval, inmap):
        """
        first sanitize inputs, in the end, inval should be a list of
        input values and inmap should be a list of the coresponding
        input names:
        inval = dict, inmap = None:
          => Create inmap list and fill inval with correct values
        inval = list, inmap = list
          => everything fine
        inval = list, inmap = none
          => inmap = self.inputs
        then map the inputs in the order the circuit expects it
        """

        def do_map(c, inval, inmap):
            indict = {}

            # drop inputs with 0 input-wires
            c = [x for x in c
                 if x[0]]

            for pos, i in enumerate(c):
                indict[i[1]] = (pos, i[0])

            ret = [None for i in xrange(len(c))]

            for val, m in zip(inval, inmap):
                ret[indict[m][0]] = val
            return ret

        c = self.circuit.inputs()

        # FIXME: @Immo: this is br0ken -> "inlist" unknown
        if isinstance(inval, dict):
            inmap = inval.keys()
            inval = [inval[i] for i in ilist]

        elif iter(inval):
            inval = tuple(inval)
            if not inmap:
                if not self.inputs:
                    raise TastySyntaxError("No input mapping specified. " \
                                           "You must either specify it on creation or on call!")
                inmap = self.inputs
        else:
            raise TastySyntaxError("Your argument must be a list of inputs")

        return do_map(c, inval, inmap)

    def map_outputs(self, outputs, omap):

        # o is in form ((owires, oname, otype), (owires, oname, otype)...)
        o = self.circuit.outputs()
        odict = {}
        for pos, i in enumerate(o):
            odict[i[1]] = (pos)

        if not omap:
            if not self.outputs:
                raise TastySyntaxError("You must specify output order either " \
                                       "on creation or on call")
            omap = self.outputs

        return tuple(outputs[odict[i]] for i in omap)


class PlainCircuit(TastyFunction, CircuitMixin):
    """A circuit with plain values - nice for debugging purposes"""

    def __call__(self, inputs, outputs):
        """ inputs is list or dictionary of plain input values
         outputs is list or dictionary of plain output values"""

        circuit = self.circuit

        c_ins = circuit.inputs()
        c_outs = circuit.outputs()

        # Optionally reorder inputs
        if isinstance(inputs, list) or isinstance(inputs, tuple):
            inputs_reordered = inputs
        elif isinstance(inputs, dict):
            # Reorder inputs according to dictionary
            inputs_reordered = list()
            for c_in_len, c_in_desc in c_ins:
                if c_in_desc not in inputs:
                    raise ValueError("input '%s' of circuit not specified"
                                     % c_in_desc)
                inputs_reordered.append(inputs[c_in_desc])
        else:
            raise TypeError("Inputs must be either list, tuple, or dict")

        # Check inputs for correct type and length
        for inp, c_inp in zip(inputs_reordered, c_ins):
            inp_len = inp.get_bitlen()
            c_inp_len = c_inp[0]
            assert inp_len == c_inp_len, \
                "Bitlength of input does not match. expected: %d got: %d" % \
                (c_inp_len, inp_len)
            assert isinstance(inp, tasty.types.Unsigned), "Input expected to be Unsigned value"

        # Optionally reorder outputs
        if isinstance(outputs, list) or isinstance(outputs, tuple):
            outputs_reordered = outputs
        elif isinstance(outputs, dict):
            # Reorder outputs according to dictionary
            outputs_reordered = list()
            for c_out_wires, c_out_desc, c_out_type in c_outs:
                if c_out_desc not in outputs:
                    raise ValueError("output '%s' of circuit not specified" % c_out_desc)
                outputs_reordered.append(outputs[c_out_desc])
        else:
            raise TypeError("Outputs must be either list, tuple, or dict")

        # Check outputs for correct type and length
        for out, c_out in zip(outputs_reordered, c_outs):
            out_len = out.get_bitlen()
            c_out_len = len(c_out[0])
            assert out_len == c_out_len, \
                "Bitlength of output does not match. expected: %d got: %d" % \
                (c_out_len, out_len)
            assert isinstance(out, tasty.types.Unsigned), \
                "Output expected to be Unsigned value"

        # collect input values
        input_vals = map(lambda x: x.get_value(), inputs_reordered)
        # evaluate circuit
        output_vals = circuit.eval(input_vals)

        # write output values
        for val, out in zip(output_vals, outputs_reordered):
            out.set_value(val)

    def returns(self, methodname, input_types, bit_lengths, dims, signeds):
        # FIXME: signed or unsigned?
        return tuple({"type": tasty.types.Unsigned, "bitlen": len(i[0]), "dim": [1], "signed": False}
                     for i in self.circuit.outputs())

    def calc_costs(self, methodname, input_types, bit_lengths, dims, role, passive, precompute):
        raise NotImplementedError()


class GarbledCircuit(TastyFunction, CircuitMixin):
    """A garbled circuit type for tasty"""

    @staticmethod
    def affects(methodname, input_types, role):
        """Used by tastyc transformation pass"""

        if __debug__:
            state.log.debug("GarbledCircuit.affects(%r, %r, %r)",
                            methodname, input_types, role)
        if methodname == "GarbledCircuit":
            return Value.S_SETUP | Value.C_SETUP | Value.C_ONLINE
        if methodname == "__call__":
            return Value.S_SETUP | Value.C_SETUP | Value.C_ONLINE
        else:
            raise TastySyntaxError(
                "A GarbledCircuit can only be created and evaluated")

    def returns(self, methodname, input_types, bit_lengths, dims, signeds):
        """Used for tastyc inference pass"""

        if __debug__:
            state.log.debug("GarbledCircuit.returns(%r, %r, %r, %r)",
                            methodname, input_types, bit_lengths, dims)
        if methodname == "__call__":
            # TODO: @Immo: please check if signed return value is correct
            return tuple({"type": tasty.types.Garbled, "bitlen": len(i[0]), "dim": [1], "signed": False}
                         for i in self.circuit.outputs())
        else:
            raise NotImplementedError("returns() not " \
                                      "implemented for GarbledCircuit.%s" % methodname)

    def calc_costs(self, methodname, input_types, bit_lengths, dims, role, passive, precompute):
        """Used for tastyc cost retrieval"""

        # FIXME: @Immo, please repair
        return self.circuit.gate_types()

    def __call__(self, invals, inmap=None, omap=None):
        """evaluates the circuit"""

        # run gc protocol
        # map outputs
        # return apropriate...
        if state.precompute:
            if state.active_party.role == Party.SERVER:
                invals = [tasty.types.Garbled.get_zero_value(x.gid)
                          for x in invals]
        else:
            if state.active_party.role == Party.CLIENT:
                invals = [x.get_value() for x in invals]

        inputs = inp = self.map_inputs(invals, inmap)
        out = self.circuit.outputs()

        if state.precompute:

            # First we must create the new garbled circuit with the zero values
            # of the garbled inputs on server side, client side will create the
            # counterpart of the protocol
            if state.active_party.role == Party.SERVER:
                gc = GCProtocol(state.active_party,
                                (self.circuit, state.R, inputs))
            else:
                gc = GCProtocol(state.active_party, (self.circuit,))

            # store the circuit in the gc object
            gc.circuit = self.circuit

            # store the newly created gc protocol object in the party to be able
            # to access it at online phase again
            state.active_party.push_gc(gc)

            # precomputation results of the gc are the zero-values of the
            # outputs on the server, empty on the client
            pr = tuple(gc.get_precomputation_results())
            if state.active_party.role == Party.SERVER:
                gc.outputgids = gids = [
                    tasty.types.Garbled.create_zero_values(values=zv)
                    for zv in pr]
                otmp = [tasty.types.Garbled(gid=gid, bitlen=len(out[i][0]),
                                            signed=(out[i][2] == SIGNED)) for i, gid in enumerate(gids)]
            else:
                otmp = [tasty.types.Garbled(gid=0, bitlen=0, signed=False)
                        for i in self.circuit.outputs()]

            return self.map_outputs(otmp, omap)


        else:  # Online
            gc = state.active_party.pop_gc()
            if state.active_party.role == Party.SERVER:
                # server has nothing to do, force protocol-run
                gc(None)
                tuple(gc.get_results())
                return tuple(tasty.types.Garbled(bitlen=len(out[i][0]),
                                                 gid=gid, signed=(out[i][2] == SIGNED))
                             for i, gid in enumerate(gc.outputgids))
            else:  #Client, the actual results...
                gc((gc.circuit, inputs))
                # Generate a list of garbleds
                otmp = tuple(tasty.types.Garbled(bitlen=len(res),
                                                 val=tasty.types.Garbled.CTuple(res),
                                                 signed=(out[i][2] == SIGNED))
                             for i, res in enumerate(gc.get_results()))
                return self.map_outputs(otmp, omap)

