# -*- coding: utf-8 -*-

from tasty.tastyc import bases
from tasty.tastyc.transformation import BasicTastyTransformer
from collections import defaultdict
from ast import *

import copy

from gmpy import mpz

from tasty import state
from tasty.tastyc.bases import (has_parent_node, get_fqnn, add_keyword,
    CALL_TYPE_CTOR, CALL_TYPE_METHOD, CALL_TYPE_TASTY_FUNC_CALL,
    CALL_TYPE_TASTY_FUNC_CTOR, CALL_TYPE_CONVERSION)
from tasty.tastyc.codegen import to_source
from tasty.tastyc import bases
from tasty.types import conversions
import tasty.types
from tasty.exc import UnknownSymbolError
from tasty.types import Value, Garbled
from tasty.types.party import Party, PartyAttribute
from tasty.utils import bitlength, protocol_path
import tasty.tastyc.analyzation
import tasty.tastyc.analyze_costs


class PassDispatcher(bases.TastyVisitor):
    """More specialized tasty ast visitor base class used for dead/passive
    code elimination.

    Tasty creates two versions of each tasty protocol. One for the setup phase
    and one for the online phase. Each phase has its own requirements, which
    will be expressed in the affects static method of each tasty type.
    The result of the affects method is a bitmask, which will be checked against
    a stanza value, which indicates the phase for which the code must be valid.
    If bitmask & stanza is zero, this code will be rejected,
    otherwise the code will be accepted for the current phase.

    Tasks this transformer performs:
        - deleting comments
        - transforms left shift operator aka tasty operator into matching
        conversion procedure
        - deletes code, which is not needed or used in the setup or online
        protocol version
    """

    def __init__(self, symbol_table):
        super(PassDispatcher, self).__init__()
        self.symbol_table = symbol_table

    def visit_For(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        for i in node.body:
            self.visit(i)

    def visit_If(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        for i in node.body:
            self.visit(i)

    def visit_Expr(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node))

        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        self.visit(node.value)
        assert hasattr(node, "value")

    def visit_Assign(self, node):
        if __debug__:
            state.log.debug("\npass dispatch pre %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        self.visit(node.value)

        if isinstance(node.value, Attribute):
            symbol_record = self.symbol_table.identify(get_fqnn(node.value))
            symbol_record["bitmask"] = node.bitmask = Value.S_ONLINE if node.role else Value.C_ONLINE
        elif isinstance(node.value, Num):
            node.bitmask = 15
        else:
            node.bitmask = node.value.bitmask

        assert hasattr(node, "bitmask")

    def visit_Constructor(self, node):
        if __debug__:
            state.log.debug("\npass dispatch ctor %s", dump(node))
        for i in node.keywords:
            self.visit(i.value)

        self.check_affects(node)
        assert hasattr(node, "bitmask")

    def visit_Conversion(self, node):
        if __debug__:
            state.log.debug("\npass dispatch ctor %s", dump(node))
        for i in node.keywords:
            self.visit(i.value)

        node.bitmask = conversions.affects(node.methodname, node.input_types, node.role)


    def visit_Method(self, node):
        io_funcs = ("input", "output", "setup_output")
        if __debug__:
            state.log.debug("\npass dispatch method %s", dump(node))
        self.visit(node.func)
        if node.methodname in io_funcs:
            # passive or setup pass nodes are removed by former transformer
            node.bitmask = self.affects_stanza
        else:
            self.check_affects(node)

    def visit_tasty_func_ctor(self, node):
        self.check_affects(node)

    def visit_tasty_func_call(self, node):
        if __debug__:
            state.log.debug("\npass dispatch tasty func call %s", dump(node, True, True))
        self.check_affects(node)

    def visit_Call(self, node):
        #state.log.debug("pass dispatch Call %s", dump(node))

        if node.call_type == CALL_TYPE_CTOR:
            self.visit_Constructor(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CALL:
            self.visit_tasty_func_call(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CTOR:
            self.visit_tasty_func_ctor(node)
        elif node.call_type == CALL_TYPE_METHOD:
            self.visit_Method(node)
        elif node.call_type == CALL_TYPE_CONVERSION:
            self.visit_Conversion(node)
        else:
            raise ValueError("found unsupported value %r for node.call_type" % node.call_type)

    def visit_Attribute(self, node):
        #state.log.debug("\npass dispatch %s", dump(node, True, True))
        self.visit(node.value)

    def visit_Subscript(self, node):
        #state.log.debug("\npass dispatch %s", dump(node, True, True))
        self.check_affects(node)

    def visit_BoolOp(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node, True, True))

        for arg in node.values:
            self.visit(arg)

        self.check_affects(node)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

        self.check_affects(node)

    def visit_UnaryOp(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node, True, True))

        self.visit(node.operand)
        self.check_affects(node)

    def visit_Compare(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return
        self.check_affects(node)

    def visit_AugAssign(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node, True, True))
        assert not isinstance(node.op, LShift)
        self.visit(node.value)
        try:
            node.bitmask = node.value.bitmask
        except AttributeError:
            node.bitmask = self.check_simple_affects(node.value)

    def check_affects(self, node):
        node_type = node.initial_info["type"]
        node.bitmask = node_type.affects(node.methodname, node.input_types, node.role)

        if __debug__:
            state.log.debug("bitmask = %d" % node.bitmask)
            state.log.debug("affects_stanza = %d" % self.affects_stanza)
        if not (node.bitmask & self.affects_stanza):
            if __debug__:
                state.log.debug("marked for deletion of %s.%s(...) node at line %d by bitmask check...", node_type.__name__, node.methodname, node.lineno)
            return True
        else:
            if __debug__:
                state.log.debug("marked for keeping %s.%s(...) node at line %d by bitmask check...", node_type.__name__, node.methodname, node.lineno)
            return False

    def check_simple_affects(self, node):
        if isinstance(node, Attribute):
            fqnn = get_fqnn(node)
            symbol_record = self.symbol_table.identify(fqnn)
            return symbol_record["bitmask"]
        else:
            raise NotImplementedError("Not implemented for %r" % type(node))



class SetupPassDispatcher(PassDispatcher, bases.SetupStanzaMixin):
    pass


class OnlinePassDispatcher(PassDispatcher, bases.OnlineStanzaMixin):
    pass


class NodePruneByBitmask(BasicTastyTransformer):
    def __init__(self, symbol_table):
        super(NodePruneByBitmask, self).__init__()
        self.symbol_table = symbol_table

    def visit_Call(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        if __debug__:
            state.log.debug("\nprune %s", dump(node))

        if node.methodname in ("output", "setup_output", "input"):
            return node

        if self.check_remove(node):
            return
        return node

    def visit_BinOp(self, node):
        #if not has_parent_node(node, bases.TastyCBase.protocol_name):
        #return node
        return node

    def visit_BoolOp(self, node):
        #if not has_parent_node(node, bases.TastyCBase.protocol_name):
        #return node
        return node

    def visit_UnaryOp(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node
        return node

    def visit_Compare(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node
        return node

    def visit_FunctionDef(self, node):
        if node.name != state.config.protocol_name:
            return node

        assert len(node.body) > 0

        new_body = list()
        for i in node.body:
            tmp = self.visit(i)
            if tmp:
                new_body.append(tmp)
        node.body = new_body

        if not node.body:
            node.body.append(Pass())
        assert len(node.body) > 0
        return node

    def visit_For(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        new_body = list()
        for i in node.body:
            tmp = self.visit(i)
            if tmp:
                new_body.append(tmp)
        node.body = new_body

        if not node.body:
            return
        return node

    def visit_Expr(self, node):
        if __debug__:
            state.log.debug("\npass dispatch %s", dump(node))

        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        node.value = self.visit(node.value)
        if not node.value:
            return
        return node

    def visit_AugAssign(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        assert not isinstance(node.op, LShift)

        if self.check_remove(node):
            return
        return node

    def visit_Assign(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node
        if __debug__:
            state.log.debug("prune %s", dump(node, True, True))

        node.value = self.visit(node.value)
        if not node.value or self.check_remove(node):
            for target in node.targets:
                if (isinstance(target, Attribute) or
                    isinstance(target, Subscript)):
                    self.symbol_table.remove_symbol(get_fqnn(target))
                elif isinstance(target, Tuple):
                    for item in target.elts:
                        self.symbol_table.remove_symbol(get_fqnn(item))
                elif isinstance(target, Name):
                    self.symbol_table.remove_symbol(get_fqnn(target))
                else:
                    raise NotImplementedError("pruning of assign " \
                        "for node %r not yet implemented" % type(target))
            return
        return node

    def check_remove(self, node):
        if not (node.bitmask & self.affects_stanza):
            if __debug__:
                state.log.debug("pruning %s", dump(node))
            return True
        if __debug__:
            state.log.debug("keeping %s", dump(node))
        return False

class SetupPruner(NodePruneByBitmask, bases.SetupStanzaMixin):
    pass


class OnlinePruner(NodePruneByBitmask, bases.OnlineStanzaMixin):
    pass
