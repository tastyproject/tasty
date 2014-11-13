# -*- coding: utf-8 -*-

"""Implements the transformation and optimzation features.
"""


from collections import defaultdict
from ast import *

import copy, sys

from gmpy import mpz

from tasty import state
from tasty.tastyc.bases import (has_parent_node, get_fqnn, add_keyword,
    CALL_TYPE_CTOR, CALL_TYPE_METHOD, CALL_TYPE_TASTY_FUNC_CTOR,
    CALL_TYPE_TASTY_FUNC_CALL, CALL_TYPE_CONVERSION, SetupStanzaMixin,
    OnlineStanzaMixin, NodeInserter)
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

class BasicTastyTransformer(NodeTransformer, bases.TastyCBase):
    """Base class for tasty specific ast transformers"""

    pass


class TastyTransformer(BasicTastyTransformer):
    """More specialized tasty ast transformer base class used for dead/passive
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
        super(TastyTransformer, self).__init__()
        self.symbol_table = symbol_table

    def visit_For(self, node):
        if __debug__:
            state.log.debug("transform %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        new_body = list()
        for i in node.body:
            tmp = self.visit(i)
            if tmp:
                new_body.append(tmp)
        node.body = new_body
        if not new_body:
            return
        return node

    def visit_If(self, node):
        if __debug__:
            state.log.debug("transform %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        new_body = list()
        for i in node.body:
            tmp = self.visit(i)
            if tmp:
                new_body.append(tmp)
        node.body = new_body
        if not new_body:
            return
        return node

    def visit_FunctionDef(self, node):
        if node.name != bases.TastyCBase.protocol_name:
            return node

        new_body = list()
        for child in node.body:
            tmp = self.visit(child)
            if tmp:
                new_body.append(tmp)
        node.body = new_body
        assert len(node.body) > 0
        return node

    def visit_Constructor(self, node):
        for i in node.keywords:
            self.visit(i.value)

        if node.role == self.passive_role:
            add_keyword(node, "passive", True)

        kwargs = node.return_info[0]
        add_keyword(node, "signed", kwargs["signed"])
        add_keyword(node, 'bitlen', kwargs["bitlen"])
        add_keyword(node, 'dim', kwargs["dim"])

        return node

    def visit_tasty_func_ctor(self, node):
        return node

    def visit_tasty_func_call(self, node):
        return node

    def visit_Expr(self, node):
        if __debug__:
            state.log.debug("transform %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        node.value = self.visit(node.value)
        if not node.value:
            return
        return node

    def visit_Method(self, node):
        self.generic_visit(node)
        if ((self.affects_stanza >= Value.C_ONLINE or node.role == bases.TastyCBase.passive_role) and
            node.methodname == "setup_output"):
            return
        if (self.affects_stanza < Value.C_ONLINE or
                node.role == bases.TastyCBase.passive_role):
            if node.methodname == "input":
                return node.func.value
            elif node.methodname == "output":
                return
        return node

    def visit_Call(self, node):
        if __debug__:
            state.log.debug("transform %s", dump(node))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node

        if node.call_type == CALL_TYPE_CTOR:
            return self.visit_Constructor(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CALL:
            return self.visit_tasty_func_call(node)
        elif node.call_type == CALL_TYPE_TASTY_FUNC_CTOR:
            return self.visit_tasty_func_ctor(node)
        elif node.call_type == CALL_TYPE_METHOD:
            return self.visit_Method(node)
        else:
            raise ValueError("found unsupported value %r for node.call_type" % node.call_type)

    def visit_Assign(self, node):
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node
        node.value = self.visit(node.value)
        if not node.value:
            return
        return node

    def visit_AugAssign(self, node):
        if __debug__:
            state.log.debug("\ntransform %s", dump(node, True, True))
        node.value = self.visit(node.value)
        if isinstance(node.op, LShift):
            force_bitlen = None
            force_signed = None
            if (isinstance(node.value, Call) and
                node.value.call_type == CALL_TYPE_CTOR):
                # src_type and dest_type will be different
                src_node = node.value.keywords_map["val"].value
                force_bitlen = node.value.keywords_data.get("force_bitlen")
                force_signed = node.value.keywords_data.get("force_signed")
            elif isinstance(node.value, Attribute):
                src_node = node.value
            else:
                NotImplementedError("transformation for augassign value " \
                    "of type %s not implemented" % type(node.value))

            bitlen_node = Num(n=node.bit_lengths[1])
            dim_node = compile(str(node.dims[1]), "<none>", "eval",
                PyCF_ONLY_AST).body

            signed_node = Name(id=str(node.signeds[1]))

            dest_type, src_type = node.input_types

            new_node = Expr(value=Call(
                func=Attribute(value=Name(id='conversions', ctx=Load()),
                attr=node.methodname, ctx=Load()), args=[src_node,
                node.target, bitlen_node, dim_node, signed_node], keywords=[], starargs=None,
                kwargs=None))

            new_node.value.lineno = node.lineno
            new_node.value.col_offset = node.col_offset
            new_node.value.keywords_map = {}

            if force_bitlen:
                add_keyword(new_node.value, "force_bitlen", force_bitlen)
            # False and True should be enforced
            if force_signed is not None :
                add_keyword(new_node.value, "force_signed", force_signed)
            new_node.value.role = node.value.role
            new_node.value.passive = node.value.passive

            new_node.initial_info = new_node.value.initial_info = node.initial_info
            new_node.value.methodname = node.methodname
            new_node.value.src_type = src_type
            new_node.value.input_types = node.input_types
            new_node.value.dest_type = dest_type
            new_node.value.bit_lengths = node.bit_lengths
            new_node.value.dims = node.dims
            new_node.value.call_type = CALL_TYPE_CONVERSION

            new_node.return_info = new_node.value.return_info = \
                node.return_info

            new_node.parent = node.parent
            new_node.value.parent = new_node
            return new_node
        return node


class SetupTransformer(TastyTransformer, SetupStanzaMixin):
    pass

class OnlineTransformer(TastyTransformer, OnlineStanzaMixin):
    pass

class TypeCompletionTransformer(BasicTastyTransformer):

    def __init__(self, symbol_table):
        super(TypeCompletionTransformer, self).__init__()
        self.symbol_table = symbol_table
        self.global_table = bases.TastyCBase.symbol_table

    def visit_BinOp(self, node):
        if isinstance(node.left, Attribute):
            fqnn = get_fqnn(node.left)
            if fqnn not in self.symbol_table:
                symbol_record = self.global_table.identify(fqnn)
                kwargs = symbol_record["kwargs"]
                symbol_type = kwargs["type"]
                node.left = Call(func=Name(id=symbol_type.__name__), args=[], kwargs=None, starargs=None, keywords=[
                    keyword(arg="bitlen", value=Num(n=kwargs["bitlen"])),
                    keyword(arg="dim", value=Num(n=kwargs["dim"])),
                    keyword(arg="signed", value=Name(id=str(kwargs["signed"]))),
                    keyword(arg="passive", value=Name(id="True")),
                    keyword(arg="empty", value=Name(id="True"))])
        if isinstance(node.right, Attribute):
            fqnn = get_fqnn(node.right)
            if fqnn not in self.symbol_table:
                symbol_record = self.global_table.identify(fqnn)
                symbol_type = symbol_record["node_type"]
                kwargs = symbol_record["kwargs"]
                node.right = Call(func=Name(id=symbol_type.__name__), args=[], kwargs=None, starargs=None, keywords=[
                    keyword(arg="bitlen", value=Num(n=kwargs["bitlen"])),
                    keyword(arg="dim", value=Num(n=kwargs["dim"])),
                    keyword(arg="signed", value=Name(id=str(kwargs["signed"]))),
                    keyword(arg="passive", value=Name(id="True")),
                    keyword(arg="empty", value=Name(id="True"))])
        return node

    def visit_Call(self, node):
        if __debug__:
            state.log.debug("\ntype completion %s", dump(node))
        self.visit(node.func)
        if hasattr(node, "call_type") and node.call_type == CALL_TYPE_CTOR:
            val = node.keywords_map.get("val")
            if val:
                if not isinstance(val.value, Attribute):
                    return node
                fqnn = get_fqnn(val.value)
                if fqnn not in self.symbol_table:
                    symbol_record = self.global_table.identify(fqnn)
                    kwargs = symbol_record["kwargs"]
                    symbol_type = kwargs["type"]
                    node.keywords_map["val"].value = Call(func=Name(id=symbol_type.__name__), args=[], kwargs=None, starargs=None, keywords=[
                        keyword(arg="bitlen", value=Num(n=kwargs["bitlen"])),
                        keyword(arg="dim", value=Num(n=kwargs["dim"])),
                        keyword(arg="signed", value=Name(id=str(kwargs["signed"]))),
                        keyword(arg="passive", value=Name(id="True")),
                        keyword(arg="empty", value=Name(id="True"))])
        return node


class KwargsPropagator(BasicTastyTransformer):

    def __init__(self):
        super(KwargsPropagator, self).__init__()
        self.count = defaultdict(int)

    def visit_ClassDef(self, node):
        return node



class DriverParameterPropagator(BasicTastyTransformer):

    def __init__(self, kwargs=dict()):
        super(DriverParameterPropagator, self).__init__()
        self.kwargs = kwargs

    def visit_Assign(self, node):
        self.generic_visit(node)
        node_value = node.value

        if (isinstance(node_value, Subscript) and
            isinstance(node_value.value, Name) and
            node_value.value.id == bases.TastyCBase.kwargs_name):
            i = node_value.slice.value.s
            try:
                result = self.kwargs[i]
            except TypeError, e:
                if not state.driver_explicitely_assigned:
                    state.log.error("Error: Could not found IODriver default parameter dict '__params__'. Please review your protocol which parameters you are using. and add e.g following line above your protocol method:\n\n__params__ = {{'foo' : 23, 'bar' : 42}}\n\ndef protocol(client, server, params):\n    pass")
                    sys.exit(-1)
                else:
                    state.log.error("Error: Cannot find driver parameters\n" \
                    "It seems you are trying to run a protocol with " \
                    "a driver without default parameters. If you must explicitely " \
                    "assign a driver in your protocol, instantiate it with a dict parameter e.g:\n\n" \
                    "driver = IODriver({'foo' : 23, 'bar' : 42})\n\n"
                    "def protocol(client, server, params):\n    pass\n\n" \
                    "If you want to run a driven protocol interactively, use the prefered form:\n\n" \
                    "__params__ = {{'foo' : 23, 'bar' : 42}}\n\ndef protocol(client, server, params):\n    pass")
                    sys.exit(-1)
            except KeyError:
                raise KeyError("Your driver's parameter dictionary misses following parameter: %s " % i)
            if isinstance(result, int):
                node.value = Num(n=result, lineno=node.lineno,
                    col_offset=node.col_offset)
                node.node_type = int
            else:
                raise NotImplementedError("not implemented for %r" % type(result))
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        for keyword in node.keywords:
            node_value = keyword.value
            if (isinstance(node_value, Subscript) and
                isinstance(node_value.value, Name) and
                node_value.value.id == bases.TastyCBase.kwargs_name):
                i = node_value.slice.value.s
                try:
                    result = self.kwargs[i]
                except KeyError:
                    raise KeyError("cannot find parameter %r in '%s'" % (i, bases.TastyCBase.kwargs_name))
                _type = type(result)
                if isinstance(result, int) or isinstance(result, long):
                    keyword.value = Num(n=result, lineno=node.lineno,
                        col_offset=node.col_offset)
                    node.node_type = _type
                else:
                    raise NotImplementedError("not implemented for %r" % type(result))
        return node



class DanglingGarbledBinder(NodeInserter, BasicTastyTransformer):
    """Changes direct usage of unbounded Garbleds into "bounding a Garbled to the
    appropriate party and using via call by reference.

    This class depends on information gathered by Symbolizer
    """

    def __init__(self):
        super(DanglingGarbledBinder, self).__init__()
        self.sequence = 0

    def visit_ClassDef(self, node):
        if __debug__:
            state.log.debug("transform %s", dump(node, True, True))
        if not has_parent_node(node, bases.TastyCBase.protocol_name):
            return node
        self.generic_visit(node)
        return node

    def bind_garbled(self, node, party):
        name = "tmp_garbled_%s_%d_%d_%d" % (str(node.__class__.__name__), node.lineno, node.col_offset, self.sequence)
        self.sequence += 1
        return self.bind_node(node, party, name)

    def visit_BinOp(self, node):
        if __debug__:
            state.log.debug("\ndangling %s", dump(node, True, True))
        node.left = self.visit(node.left)
        node.right = self.visit(node.right)
        # only direct assignment of binop is ok, all other cases must be
        # rewritten, like e.g binop in args or keyword of a ctor

        if isinstance(node.left, Str):
            return node
        if (isinstance(node.parent, Assign) or
            isinstance(node.parent, AugAssign)):
            return node
        if node.return_info[0]["type"] == Garbled:
            party = node.passive and bases.TastyCBase.passive_name or bases.TastyCBase.active_name
            return self.bind_garbled(node, party)
        return node

    def visit_Assign(self, node):
        return self.generic_visit(node)

    def visit_Call(self, node):
        self.generic_visit(node)
        if __debug__:
            state.log.debug("\ndangling %s", dump(node, True, True))
        if (isinstance(node.parent, Assign) or
            isinstance(node.parent, AugAssign)):
            return node

        if (hasattr(node, "is_ctor") and node.node_type == Garbled):
            party = node.func.passive and bases.TastyCBase.passive_name or bases.TastyCBase.active_name
            new_node = self.bind_garbled(node, party)
            self.replace_in_parent(node, new_node)
            return new_node
        return node

    def visit_UnaryOp(self, node):
        if __debug__:
            state.log.debug("\ndangling %s", dump(node, True, True))
        self.generic_visit(node)
        operand = node.operand
        if ((isinstance(operand, Subscript) or
            isinstance(operand, Attribute)) and not
            isinstance(node.parent, Assign)):
            operand_type = operand.return_info[0]["type"]
            party = operand.passive and bases.TastyCBase.passive_name or bases.TastyCBase.active_name
            if operand_type == Garbled:
                new_node = self.bind_garbled(node, party)
                self.replace_in_parent(node, new_node)
                return new_node
        return node

class ConstantPropagator(BasicTastyTransformer):

    def __init__(self):
        super(ConstantPropagator, self).__init__()
        self.propagated_symbols = set()

    def visit_Assign(self, node):
        self.visit(node.value)
        return node

    def visit_Assign_2nd_pass(self, node):
        #state.log.debug("\nconstant propagation 2nd pass %s",
            #dump(node, True, True))
        target = node.targets[0]
        if isinstance(target, Name):
            fqnn = get_fqnn(target)
            if fqnn in self.propagated_symbols:
                return
        return node

    def visit_Name_2nd_pass(self, node):
        #state.log.debug("\nconstant propagation 2nd pass %s",
            #dump(node, True, True))
        return node

    def visit_Name(self, node):
        #state.log.debug("\nconstant propagation %s", dump(node, True, True))

        if (isinstance(node.parent, Attribute) or
            node.id in tasty.tastyc.analyzation._cost_class_names or
            node.id in (self.active_name, self.passive_name)):
            return node

        try:
            fqnn = get_fqnn(node)
            symbol_record = self.symbol_table.identify(fqnn)
            node_kwargs = symbol_record["kwargs"]
        except Exception, e:
            #if state.config.verbose >= 2:
                #state.log.exception(e)
            pass
        else:
            node = Num(n=node_kwargs["val"], lineno=node.lineno,
                col_offset=node.col_offset)
            self.propagated_symbols.add(fqnn)
        return node

    def cleanup_symbol_table(self):
        for symbol in self.propagated_symbols:
            self.symbol_table.remove_symbol(symbol)


class SimpleEvaluator(BasicTastyTransformer):
    """Evaluates simple operations and function calls on python types"""

    def visit_BinOp(self, node):
        #state.log.debug("\nsimple evaluator %s", dump(node, True, True))

        try:
            val = eval(to_source(node))
            p = node.parent
            lineno = node.lineno
            col_offset = node.col_offset
            node = compile(str(val), "none", "eval", PyCF_ONLY_AST).body
            node.node_type = type(val)
            node.parent = p
            node.lineno = lineno
            node.col_offset = col_offset
        except Exception, e:
            #if state.config.verbose >= 2:
                #state.log.exception(e)
            pass
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, Name) and node.func.id == "bitlength":
            return Num(n=bitlength(node.args[0].n), lineno=node.lineno,
                col_offset=node.col_offset)
        return node


class PlainTypeConverter(BasicTastyTransformer):
    """Evaluates simple operations and function calls on python types"""

    @staticmethod
    def tastify(num, parent):
        """returns a new Integer based tasty type"""

        bits = mpz(num.n).bit_length()
        if num.n < 0:
            type_name = "Signed"
            bits += 1
        else:
            type_name = "Unsigned"
        new_node = Call(func=Name(id=type_name, ctx=Load()),
            args=[], starargs=None, kwargs=None, keywords=[
                keyword(arg="bitlen", value=Num(n=bits)),
                keyword(arg="val", value=num)])
        new_node.parent = parent
        new_node.role = parent.role
        new_node.passive = parent.passive
        return new_node

    def visit_BinOp(self, node):
        #state.log.debug("\nplain type converter %s", dump(node, True, True))

        if isinstance(node.left, Num):
            node.left = PlainTypeConverter.tastify(node.left, node)
        if isinstance(node.right, Num):
            node.right = PlainTypeConverter.tastify(node.right, node)
        return node

    def visit_UnaryOp(self, node):
        #state.log.debug("\nsimple evaluator %s", dump(node, True, True))

        if isinstance(node.operand, Num):
            node.operand = PlainTypeConverter.tastify(node.operand, node)
        return node

    def visit_Compare(self, node):
        #state.log.debug("\nsimple type converter %s", dump(node, True, True))

        if isinstance(node.left, Num):
            node.left = PlainTypeConverter.tastify(node.left, node)
        for ix, right in enumerate(node.comparators):
            if isinstance(right, Num):
                node.comparators[ix] = PlainTypeConverter.tastify(right, node)
        return node

    def visit_Assign(self, node):
        #state.log.debug("\nsimple evaluator %s", dump(node, True, True))
        self.generic_visit(node)
        for target in node.targets:
            if isinstance(target, Name):
                return node
        if isinstance(node.value, Num):
            node.value = PlainTypeConverter.tastify(node.value, node)
        return node

    def visit_FunctionDef(self, node):
        if node.name == state.config.protocol_name:
            self.generic_visit(node)
        return node
