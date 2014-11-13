# -*- coding: utf-8 -*-

"""This module provides features to create and evaluate garbled circuits"""

__all__ = ["AbstractCreatorGarbledCircuit", "AbstractEvaluatorGarbledCircuit"]

### CreatorGarbledCircuit
class AbstractCreatorGarbledCircuit(object):
    """
    Creator Garbled Circuit Abstract Class
    DOCUMENT ME!!!
    """
    _circuit_counter = 0

    def __init__(self, circuit, R, inputs):
        self.circuit = self.optimize_circuit(circuit) #optimize the circuit for gc
        #self.circuit = circuit
        self.circuit_id = self._circuit_counter
        AbstractCreatorGarbledCircuit._circuit_counter += 1
        self.inputs = inputs
        self.R = R
        self.outputs = [None]

    def optimize_circuit(self, c):
        """ 
        Overwrite this with the appropriate circuit transformation for your gc-implementation
        """
        return c

    def next_garbled_gate(self):
        """ """
        #map inputs to input_bits
        # list of list to one single tuple in same order
        inputs = self.inputs = reduce(lambda x, y: tuple(x) + tuple(y), self.inputs) 
        u = self.circuit.num_input_bits()
        if len(inputs) != u:
            raise ValueError("Number of garbled inputs of does not match "
                "number of circuit inputs! (expected %d, got %d)"%(u, len(inputs)))
        k = self.circuit.num_gates()

        garbled_wires = [None for i in xrange(u + k)] #initialize all wires

        # map input-bits to input-wires
        if len(self.inputs) != u:
            raise ValueError("Number of garbled inputs of does not match "
                             "number of circuit inputs")

        garbled_wires[:u] = inputs

        # add costs:
        self.creation_costs()

        # create garbled gates
        for ix, gate in enumerate(self.circuit.next_gate()):
            inputs, truth = gate
            wireval, garbled_table = self.create_garbled_gate([garbled_wires[i] for i in inputs], truth, ix)
            garbled_wires[u + ix] = wireval
            if garbled_table: # None for gates without any table (e.g. XOR-Gates)
                yield garbled_table

        self.outputs = [(garbled_wires[idx] for idx in output[0])
                        for output in self.circuit.outputs()]


    def results(self):
        for i in self.outputs:
            yield i



class AbstractEvaluatorGarbledCircuit(object):
    """A garbled circuit"""

    _circuit_counter = 0

    def __init__(self, circuit, next_garbled_gate, garbled_inputs):
        self.circuit = self.optimize_circuit(circuit)
        self.next_garbled_gate = next_garbled_gate

        self.circuit_id = AbstractEvaluatorGarbledCircuit._circuit_counter
        AbstractEvaluatorGarbledCircuit._circuit_counter += 1
        self.garbled_inputs = garbled_inputs

    def set_inputs(self, inputs):
        self.garbled_inputs = inputs


    def optimize_circuit(self, c):
        """ 
        Overwrite this with the appropriate circuit transformation for your gc-implementation
        """
        return c

    def evaluate(self):
        """Used in online phase

        @type garbled_input: iterable
        @param garbled_inputs: iterable of keys

        @rtype: iterable
        @return: returns the keys of output"""

        #serialize the inputs into one big list of garbled wires
        garbled_inputs = self.garbled_inputs = reduce(lambda x, y: tuple(x) + tuple(y), self.garbled_inputs)
        u = self.circuit.num_input_bits()

        k = self.circuit.num_gates()
        garbled_wires = [None for i in xrange(u + k)]

        if len(garbled_inputs) != u:
            raise ValueError("Number of garbled inputs does not match "
                "number of circuit inputs! (got %d, expect %d)"%(len(garbled_inputs), u))
        garbled_wires[:u] = garbled_inputs
        self.evaluation_costs()

        # evaluate garbled gates
        for ix, gate in enumerate(self.circuit.next_gate()):
            inputs, truth = gate
            len_inputs = len(inputs)
            garbled_wires[u + ix] = self.evaluate_garbled_gate([garbled_wires[i] for i in inputs], truth, ix)
#            yield None

        for i in self.next_garbled_gate:
            # unreachable unless your circuits do not match or your 
            # evaluate_garbled_gate does not use all of self.next_garbled_gate
            assert False, "Circuit and Garbled Circuit does not Match!"

        self.outputs = [(garbled_wires[outwire] for outwire in output[0]) for output in self.circuit.outputs()]

    def eval (self):
#        for i in self.evaluate_next_gate():
#            pass
        self.evaluate()
        return self.outputs



    def results(self):
        try:
            for i in self.outputs:
                yield i
        except AttributeError:
            self.eval()
            for i in self.outputs:
                yield i
