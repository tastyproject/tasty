# -*- coding: utf-8 -*-

"""features for collecting abstract protocol costs"""

from ast import *

from tasty.tastyc import bases
from tasty.tastyc.bases import (CALL_TYPE_CTOR, CALL_TYPE_CONVERSION, CALL_TYPE_METHOD,
                                CALL_TYPE_TASTY_FUNC_CTOR, CALL_TYPE_TASTY_FUNC_CALL)
from tasty.types import conversions
from tasty import state
from tasty.exc import UnknownSymbolError, FqnnError
from tasty import cost_results

__all__ = ["analyze_costs"]


def find_assign_node(node):
    if isinstance(node.parent, Assign):
        return node.parent
    else:
        return find_assign_node(node.parent)


class CostEvaluator(bases.TastyVisitor):
    def __init__(self, cost_obj, precompute=True):
        super(CostEvaluator, self).__init__()
        self.cost_obj = cost_obj
        self.precompute = precompute

    def visit_ClassDef(self, node):
        pass

    def visit_If(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        if not bases.has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        if isinstance(node.test, Attribute) or isinstance(node.test, Subscript):
            return_rec = node.test.return_info[0]
            self.cost_obj(
                **return_rec["type"].calc_costs("__nonzero__", tuple(), (return_rec["bitlen"],), (return_rec["dim"],),
                                                node.role,
                                                node.passive, self.precompute))
        else:
            self.visit(node.test)

        for i in node.body:
            self.visit(i)


    def visit_UnaryOp(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        self.visit(node.operand)
        self.cost_obj(**node.initial_info["type"].calc_costs(node.methodname, tuple(),
                                                             node.bit_lengths, node.dims, node.role, node.passive,
                                                             self.precompute))

    def visit_For(self, node):
        # state.log.debug("\ncosts %d %s", id(node), dump(node, True, True))
        if isinstance(node.iter, Call):
            for i in xrange(node.iter.args[0].n):
                for j in node.body:
                    self.visit(j)
        elif isinstance(node.iter, Attribute):
            count = node.iter.return_info[0]["dim"][0]
            for i in xrange(count):
                for j in node.body:
                    self.visit(j)


    def visit_BinOp(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        if isinstance(node.left, Str):
            return node

        self.visit(node.left)
        self.visit(node.right)

        self.cost_obj(**node.initial_info["type"].calc_costs(node.methodname, node.input_types,
                                                             node.bit_lengths, node.dims, self.active_role,
                                                             node.passive,
                                                             self.precompute))

    def visit_BoolOp(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        self.generic_visit(node)

    def visit_Compare(self, node):
        # state.log.debug("\ncosts %s", dump(node))

        fqnn = bases.get_fqnn(node.left)
        party_name = fqnn[0]
        if party_name == self.passive_name:
            passive = True
            role = self.passive_role
        else:
            passive = False
            role = self.active_role

        try:
            left_symbol_record = self.symbol_table.identify(fqnn)
            left_kwargs = left_symbol_record["kwargs"]

        except UnknownSymbolError:
            left_kwargs = node.left.return_info[0]

        left_type = left_kwargs["type"]
        left_bitlen = left_kwargs["bitlen"]
        left_dim = left_kwargs["dim"]
        left_signed = left_kwargs["signed"]

        try:
            right_fqnn = bases.get_fqnn(node.comparators[0])
            right_symbol_record = self.symbol_table.identify(right_fqnn)
            right_kwargs = right_symbol_record["kwargs"]
        except FqnnError, e:
            right_kwargs = node.comparators[0].return_info[0]

        right_type = right_kwargs["type"]
        right_bitlen = right_kwargs["bitlen"]
        right_dim = right_kwargs["dim"]
        right_signed = right_kwargs["signed"]

        if isinstance(node.ops[0], In):
            bit_lengths = (right_bitlen, left_bitlen)
            dims = (right_dim, left_dim)
            self.cost_obj(**right_type.calc_costs(node.methodname, (left_type,), bit_lengths, dims, role,
                                                  passive, self.precompute))
        else:
            bit_lengths = (left_bitlen, right_bitlen)
            dims = (left_dim, right_dim)
            self.cost_obj(**left_type.calc_costs(node.methodname, (right_type,), bit_lengths, dims, role,
                                                 passive, self.precompute))

    def visit_Assign(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        self.visit(node.value)

    def visit_AugAssign(self, node):
        # state.log.debug("\ncosts %s", dump(node, True, True))
        self.visit(node.value)

    def visit_constructor(self, node):
        self.generic_visit(node)
        self.check_costs(node)

    def visit_method(self, node):
        if hasattr(node.func, "attr") and (node.func.attr in ("output", "setup_output", "input")):
            return
        if isinstance(node.func, Name) and node.func.id in ("protocol_path",
                                                            "protocol_file", "tasty_path", "tasty_file"):
            return

        self.generic_visit(node)
        self.check_costs(node)

    def visit_tasty_function_call(self, node):
        self.generic_visit(node)
        node_type = node.initial_info["type"]

        self.cost_obj(**node.tasty_function.calc_costs(
            node.methodname, node.input_types, node.bit_lengths, node.dims,
            node.role, node.passive, self.precompute))

    def visit_tasty_function_ctor(self, node):
        pass

    def visit_conversion(self, node):
        src_type = node.src_type
        dest_type = node.dest_type

        self.cost_obj(**conversions.calc_costs(node.func.attr,
                                               (src_type, dest_type), node.bit_lengths, node.dims, node.role,
                                               node.passive,
                                               self.precompute))

    def visit_Call(self, node):
        """
        """

        if not bases.has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        if node.call_type == CALL_TYPE_CTOR:
            self.visit_constructor(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CALL:
            self.visit_tasty_function_call(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CTOR:
            self.visit_tasty_function_ctor(node)
        elif node.call_type == CALL_TYPE_METHOD:
            self.visit_method(node)
        elif node.call_type == CALL_TYPE_CONVERSION:
            self.visit_conversion(node)
        else:
            raise ValueError("found unsupported value %r for node.call_type" % node.call_type)

    def check_costs(self, node):
        if __debug__:
            state.log.debug("\ncosts %s", dump(node, True, True))
        try:
            node_type = node.initial_info["type"]
        except AttributeError:
            node_type = node.return_info[0]["type"]

        passive = node.passive
        role = node.role

        self.cost_obj(**node_type.calc_costs(
            node.methodname, node.input_types, node.bit_lengths, node.dims,
            role, passive, self.precompute))


def analyze_costs(setup_ast, online_ast):
    costs = cost_results.CostSystem.costs["abstract"]
    if __debug__:
        state.log.debug("\nAnalyzing abstract costs for setup protocol version...")
    CostEvaluator(costs["setup"]["accumulated"], True).visit(setup_ast)
    if __debug__:
        state.log.debug("\nAnalyzing abstract costs for online protocol version...")
    CostEvaluator(costs["online"]["accumulated"], False).visit(online_ast)
