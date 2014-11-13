# -*- coding: utf-8 -*-

"""Implements everything needed to infer calls to types and generate a
symbol table with the symbols used in a protocol. Furthermore some visitors
analyze and validate the overall protocol structure and retrieve important
information we need for further compiler passes.

For debugging purposes, uncomment all #state.log.debug(...) calls and invoke
tasty with "-vv", they are commented out for performance reasons.
"""

from ast import *
import copy

from gmpy import mpz

from tasty import types
from tasty import state

from tasty.exc import TastySyntaxError, UnknownSymbolError, InternalError, FqnnError

from tasty.tastyc.codegen import to_source
from tasty.tastyc import bases
from tasty.types.driver import Driver
from tasty.tastyc.bases import (
    get_fqnn, set_inherited_attributes, set_inherited_attributes,
    eval_arg, copy_type_info, copy_type_info,
    retrieve_node_args, handle_target_node, copy_type_info, find_fqnn,
    copy_type_info, has_parent_node, UNARYOP_METHODS, BINOP_METHODS,
    add_keyword, CALL_TYPE_CTOR, CALL_TYPE_METHOD,
    CALL_TYPE_TASTY_FUNC_CTOR, CALL_TYPE_TASTY_FUNC_CALL, annotate_node,
    propagate_kwargs, try_finish_bitlenless, eval_num_arg,
    annotate_item_of_node, try_finish_signed)

_cost_class_names = set([
    "Signed", "SignedVec",
    "Unsigned", "UnsignedVec",
    "Homomorphic", "HomomorphicVec",
    "Modular", "ModularVec",
    "Garbled", "GarbledVec",
    "PlainCircuit", "FairplayCircuit", "GarbledCircuit"])


_types_module = __import__("tasty.types", fromlist=["*", ]).__dict__

__all__ = ["register_class_for_analyzation"]


def register_class_for_analyzation(cls):
    """Registers custom L{Value}, L{Vec} or L{TastyFunction} subclasses.

    Usage is mandatory if you want to have full cost and optimization support"""

    if __debug__:
        state.log.debug("registering class '%s' for analyzation...", cls)
    if not isinstance(cls, type):
        raise TypeError("only classes can be registered")
    _cost_class_names.add(cls.__name__)
    _types_module[cls.__name__] = cls


class Parenter(bases.TastyVisitor):
    """ sets a parent attribute to all ast nodes"""

    def generic_visit(self, node):
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        item.parent = node
                        self.generic_visit(item)
            elif isinstance(value, AST):
                value.parent = node
                self.generic_visit(value)
            else:
                try:
                    value.parent = node
                except AttributeError:
                    pass


class Qualificator(bases.TastyVisitor):
    """get node of protocol method"""

    def __init__(self):
        super(Qualificator, self).__init__()
        server_or_client = not state.config.client
        self.active_index = int(server_or_client)
        self.passive_index = int(not server_or_client)

    def visit_ClassDef(self, node):
        for base in node.bases:
            if base.id == "Driver":
                state.driver_classes.append(node.name)

    def visit_Assign(self, node):
        if node.targets[0].id == state.driver_name:
            state.assigned_driver_node = node
            state.driver_explicitely_assigned = True
        if node.targets[0].id == "__params__":
            state.driver_params = node

    def visit_FunctionDef(self, node):
        if node.name == state.config.protocol_name:
            bases.TastyCBase.protocol_name = node.name
            try:
                bases.TastyCBase.kwargs_name = node.args.args[2].id
                state.protocol_instrumentated = True
            except IndexError:
                pass
            bases.TastyCBase.active_name = \
                node.args.args[self.active_index].id
            bases.TastyCBase.passive_name = \
                node.args.args[self.passive_index].id
            bases.TastyCBase.active_role = self.active_index
            bases.TastyCBase.passive_role = self.passive_index

    def visit_ImportFrom(self, node):
        #state.log.debug("\nQualificator %s", dump(node, True, True))
        if node.module == "tasty.types":
            for _alias in node.names:
                if _alias.name == "*":
                    bases.TastyCBase.imports.add("types")
                elif _alias.name == "conversions":
                    bases.TastyCBase.imports.add("conversions")
                elif _alias.name == state.config.driver_name:
                    raise TastySyntaxError("Found unallowed import statement: " \
                        "'from tasty.types import driver' at line %r. " \
                        "Please delete this statement." % node.lineno)
        if node.module == "tasty.types.driver":
            for _alias in node.names:
                if _alias.name == "IODriver":
                    bases.TastyCBase.imports.add("IODriver")
                elif _alias.name == "TestDriver":
                    bases.TastyCBase.imports.add("TestDriver")

    def visit_Import(self, node):
        #state.log.debug("\nQualificator %s", dump(node, True, True))
        for _alias in node.names:
            if _alias.name == "tasty.types":
                raise TastySyntaxError("Found unallowed import statement: " \
                    "'import tasty.types' at line %r. " \
                    "Please delete this statement and rewrite your protocol " \
                    "for direct usage of tasty types." % node.lineno)
            if _alias.name == "tasty.types.conversions":
                raise TastySyntaxError("Found unallowed import statement: " \
                    "'import tasty.types.conversions' at line %r. " \
                    "Please delete this statement." % node.lineno)
            if _alias.name == "tasty.types.driver":
                raise TastySyntaxError("Found unallowed import statement: " \
                    "'import tasty.types.driver' at line %r. " \
                    "Please delete this statement." % node.lineno)

class AttributePropagator(bases.TastyVisitor):
    """ propagates synthesized attributes into all child nodes"""

    def visit_ClassDef(self, node):
        pass

    def visit_Assign(self, node):
        #state.log.debug("\nattribute propagator %s", dump(node, True, True))

        target = node.targets[0]
        if isinstance(target, Attribute):
            if target.value.id == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True
        elif isinstance(target, Subscript):
            if target.value.value.id == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True
        elif isinstance(target, Tuple):
            if target.elts[0].value.id == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True
        elif isinstance(target, Name):
            node.role = self.active_role
            node.passive = False
        else:
            raise NotImplementedError("not implemented for %r" % type(target))

        set_inherited_attributes(node, ("role", "passive"))


    def visit_AugAssign(self, node):
        #state.log.debug("\nattribute propagator %s", dump(node, True, True))

        if isinstance(node.op, LShift):
            if isinstance(node.target, Attribute):
                if node.target.value.id == self.active_name:
                    node.target.role = self.active_role
                    node.target.passive = False
                    node.value.role = self.passive_role
                    node.value.passive = True
                else:
                    node.target.role = self.passive_role
                    node.target.passive = True
                    node.value.role = self.active_role
                    node.value.passive = False

            elif isinstance(node.target, Subscript):
                if node.target.value.value.id == self.active_name:
                    node.target.role = self.active_role
                    node.target.passive = False
                    node.value.role = self.passive_role
                    node.value.passive = True
                else:
                    node.target.role = self.passive_role
                    node.target.passive = True
                    node.value.role = self.active_role
                    node.value.passive = False
        else:
            if isinstance(node.target, Attribute):
                if node.target.value.id == self.active_name:
                    node.target.role = node.value.role = self.active_role
                    node.target.passive = node.value.passive = False
                else:
                    node.target.role = node.value.role = self.passive_role
                    node.target.passive = node.value.passive = True
            elif isinstance(node.target, Subscript):
                if node.target.value.value.id == self.active_name:
                    node.target.role = node.value.role = self.active_role
                    node.target.passive = node.value.passive = False
                else:
                    node.target.role = node.value.role = self.passive_role
                    node.target.passive = node.value.passive = True

        set_inherited_attributes(node.value, ("role", "passive"))

    def visit_Expr(self, node):
        #state.log.debug("\nattribute propagator %s", dump(node, True, True))
        if (isinstance(node.value, Call) and
            isinstance(node.value.func, Attribute)):
            fqnn = get_fqnn(node.value.func)
            if fqnn[0] == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True

        set_inherited_attributes(node, ("role", "passive"))

    def visit_If(self, node):
        for i in node.body:
            self.visit(i)
        self.visit(node.test)
        if hasattr(node.test, "role"):
            node.role = node.test.role
            node.passive = node.test.passive
        for i in node.body:
            if hasattr(i, "role"):
                node.role = i.role
                node.passive = i.passive
                break

    def visit_Subscript(self, node):
        self.visit(node.value)
        if hasattr(node.value, "role"):
            node.role = node.value.role
            node.passive = node.value.passive
        else:
            fqnn = get_fqnn(node)
            if fqnn[0] == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True

    def visit_Attribute(self, node):
        try:
            fqnn = get_fqnn(node)
            if fqnn[0] == self.active_name:
                node.role = self.active_role
                node.passive = False
            else:
                node.role = self.passive_role
                node.passive = True
        except Exception:
            pass

    def visit_Compare(self, node):
        self.generic_visit(node)
        if hasattr(node.left, "role"):
            node.role = node.left.role
            node.passive = node.left.passive
            return
        for i in node.comparators:
            if hasattr(i, "role"):
                node.role = node.i.role
                node.passive = node.i.passive
                return
        raise AttributeError("any of compare subnode has a role")

class ConstantSymbolizer(bases.TastyVisitor):
    """A minimal symbolizer for global constants. See L{Symbolizer} for detailed
    information"""

    def visit_Assign(self, node):
        """Only assignments of global aka party unbounded symbol/variable nodes
        gets analyzed, stored and annotated"""

        if isinstance(node.value, Num):
            #state.log.debug("symbolize constant %s", dump(node, True, True))
            for target in node.targets:
                self.symbol_table.add_symbol(
                    get_fqnn(target),
                    kwargs=eval_num_arg(node.value),
                    lineno=target.lineno,
                    colno=target.col_offset)


class Symbolizer(bases.TastyVisitor):
    """main class for type inference and symbolization

    Here we are collecting information about party attributes if we can
    identify constructor invocation of subclasses of tasty plain and
    encrypted types. Tasty syntax restrictions requires that each type must
    only be invoked using keyword arguments, e.g 'Type(**kwarg) code to
    retrieve the actual type to store the type in node and to be able to
    statically analyze its impact on the protocol behaviour.

    For a description of the content of resulting symbol records,
    see L{SymbolTable} documentation.

    Used node_attributes::
        + call_type: integer constant indicating constructor, method, tasty func
        + keywords_data: dict (node_type, kwargs,)
        + initial_info: tuple of tuples, (node_type, bitlen, dim, signed), ...)
        + return_info: tuple of tuples, ((node_type0, bitlen0, dim0, signed0), ...)
        + tasty_function: node
    """

    def __init__(self, my_globals):
        super(Symbolizer, self).__init__()
        self.my_globals = my_globals
        self.nodes_without_bitlen = dict() # fqnn -> node
        self.nodes_without_signed = dict() # fqnn -> node

    def visit_If(self, node):
        if not bases.has_parent_node(node, bases.TastyCBase.protocol_name):
            return

        if isinstance(node.test, Attribute):
            symbol_record = self.symbol_table.identify(get_fqnn(node.test))
            node.test.return_info = (symbol_record["kwargs"],)
        else:
            self.visit(node.test)
            if not hasattr(node.test, "return_info"):
                raise NotImplementedError("Inferency of test component of 'if' code not implemented" % type(node.test))

        for i in node.body:
            self.visit(i)
        while True:
            else_ = node.orelse
            num_items = len(else_)
            if num_items == 1:
                if isinstance(else_[0], If):
                    node = else_[0]
                    for i in node.body:
                        self.visit(i)
                else:
                    for i in else_:
                        self.visit(i)
                    break
            else:
                break

    def visit_For(self, node):
        """Creates a symbol_table entry for node.target and visits each
        body node.

        TASK: metatasty: Use stacked symbol_tables to store 'node.target'
        symbol table entry. This would give much more symbol_record accuracy.
        """

        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))
        fqnn = get_fqnn(node.target)

        target_rec = dict()
        if isinstance(node.iter, Call):
            if isinstance(node.iter.func, Name):
                if isinstance(node.iter.args[0], Num):
                    target_rec["type"] = types.Unsigned
                    target_rec["bitlen"] = mpz(node.iter.args[0].n).bit_length()
                    target_rec["dim"] = [1]
                    target_rec["signed"] = False
                else:
                    arg_fqnn = get_fqnn(node.iter.args[0])
                    symbol_record = self.symbol_table.identify(arg_fqnn)
                    target_rec = symbol_record["kwargs"]
            else:
                raise TastySyntaxError("'for' not handled for iteration node type %s" % type(node.iter.func))
        elif isinstance(node.iter, Attribute):
            arg_fqnn = get_fqnn(node.iter)
            symbol_record = self.symbol_table.identify(arg_fqnn)
            kwargs = symbol_record["kwargs"]
            node.iter.return_info = (kwargs,)

            iter_node_type = kwargs["type"]
            bit_lengths = (kwargs["bitlen"], )
            dims = (kwargs["dim"],)
            signeds = (kwargs["signed"],)
            node.target.return_info = iter_node_type.returns(
                "__getitem__", tuple(), bit_lengths, dims, signeds)
            target_rec = node.target.return_info[0]
        else:
            raise NotImplementedError(
                "'for' not handled for iteration node type %s" % type(node.iter))


        self.symbol_table.add_symbol(
            fqnn,
            kwargs=target_rec,
            lineno=node.lineno,
            colno=node.col_offset)

        #self.symbol_table.dump()
        for i in node.body:
            self.visit(i)

    def visit_constructor(self, node):
        """here we inspect constructor invocations."""

        if __debug__:
            state.log.debug("\ninfer ctor %s", dump(node, True, True))

        node.call_type = CALL_TYPE_CTOR
        node.methodname = node.node_type.__name__

        self.visit(node.func)
        for i in node.keywords:
            self.visit(i)

        if hasattr(node, "keywords_data"):
            raise InternalError(
                "trying to overwrite keywords_data attribute twice")

        # keyword name -> object
        # real objects of ast representation
        node.keywords_data = dict()

        # keyword name -> keyword node
        # used for fast access to keyword nodes
        node.keywords_map = dict()

        if node.args:
            raise TastySyntaxError(
                "Tasty type constructors must not use positional arguments")

        for ix, kw in enumerate(node.keywords):
            value = kw.value
            key = kw.arg
            node.keywords_map[key] = kw
            node.keywords_data[key] = value

            if isinstance(value, Num):
                evaled = eval_num_arg(value)
                node.keywords_data[key] = evaled["val"]
                evaled["type"] = node.node_type
                kw.return_info = (evaled,)
            elif isinstance(value, Attribute):
                symbol_record = self.symbol_table.identify(get_fqnn(value))
                kwargs = copy.deepcopy(symbol_record["kwargs"])
                kw.return_info = (kwargs,)
            elif isinstance(value, List):
                eval_value = eval_arg(value)
                node.keywords_data[key] = eval_value["val"]
                kw.return_info = (eval_value,)
            elif isinstance(value, Tuple):
                eval_value = eval_arg(value)
                node.keywords_data[key] = eval_value["val"]
                kw.return_info = (eval_value,)
            elif isinstance(value, Name):
                if value.id == "None":
                    raise TastySyntaxError("'None' not allowed as constructor argument")
                elif value.id == "True":
                    kw.return_info = ({"type" : bool, "bitlen" : None, "dim" : None, "signed" : None},)
                    node.keywords_data[key] = True
                elif value.id == "False":
                    kw.return_info = ({"type" : bool, "bitlen" : None, "dim" : None, "signed" : None},)
                    node.keywords_data[key] = False
                else:
                    raise NotImplementedError("argument %r not handled" % value.id)
            elif (isinstance(value, UnaryOp) or
                isinstance(value, BinOp) or
                isinstance(value, BoolOp) or
                isinstance(value, Subscript)):
                kw.return_info = kw.value.return_info
            else:
                raise NotImplementedError(
                    "unhandled node type %s" % type(value))

        val = node.keywords_map.get("val")
        if val:
            kwargs = val.return_info[0]
            for k, v in kwargs.iteritems():
                if (k not in node.keywords_data and
                    k not in ("force_signed", "force_bitlen")):
                    node.keywords_data[k] = v

        if "dim" not in node.keywords_data:
            if (issubclass(node.node_type, types.PlainType) or
                issubclass(node.node_type, types.GarbledType) or
                issubclass(node.node_type, types.HomomorphicType)):
                node.keywords_data["dim"] = [1]
            elif issubclass(node.node_type, types.Vec):
                # otherwise inspect val kwargs for dims
                val_node = node.keywords_data["val"]
                if isinstance(val, Attribute):
                    symbol_record = self.symbol_table.identify(get_fqnn(val_node))
                    kwargs = symbol_record["kwargs"]
                    node.keywords_data["dim"] = kwargs["dim"]
                else:
                    raise NotImplementedError(
                        "not implemented for %s" % type(val))

        dim = node.keywords_data["dim"]
        try:
            iter(dim)
        except TypeError:
            node.keywords_data["dim"] = dim = [dim]
        except KeyError:
            raise

        if "force_bitlen" in node.keywords_data:
            node.keywords_data["bitlen"] = node.keywords_data["force_bitlen"]

        if "force_signed" in node.keywords_data:
            node.keywords_data["signed"] = node.keywords_data["force_signed"]

        if not "signed" in node.keywords_data:
            try:
                val = node.keywords_data["val"]
                node.keywords_data["signed"] = val.return_info[0]["signed"]
            except KeyError:
                node.signed_not_finished = True

        if "bitlen" not in node.keywords_data:
            if node.node_type in (types.Modular, types.ModularVec):
                node.keywords_data["bitlen"] = \
                    state.config.asymmetric_security_parameter
            elif issubclass(node.node_type, types.TastyFunction):
                pass
            else:
                #node.keywords_data["bitlen"] = e
                # the type declaration is not yet completed. Later we must
                # ensure correct tasty type initialization and set in node
                # and symbol table if present
                node.bitlen_not_finished = True
                if __debug__:
                    state.log.debug("bitlen_not_finished")

        force_bitlen = node.keywords_data.get("force_bitlen")
        if force_bitlen:
            node.keywords_data["bitlen"] = force_bitlen

        force_signed = node.keywords_data.get("force_signed")
        if force_signed:
            node.keywords_data["signed"] = True

        val_return_rec = None
        bit_lengths = None
        dims = None

        if val:
            #propagate_kwargs(node)
            val_return_rec = val.return_info[0]
            input_types = (val_return_rec["type"],)
            bit_lengths = (node.keywords_data["bitlen"], val_return_rec["bitlen"])
            dims = (node.keywords_data["dim"], val_return_rec["dim"])
            signeds = (node.keywords_data.get("signed"), val_return_rec["signed"])
        else:
            input_types = tuple()
            bit_lengths = (node.keywords_data.get("bitlen"),)
            dims = (node.keywords_data["dim"],)
            signeds = (node.keywords_data.get("signed"), None)

        # in this special case we must populate input_types, bit_lengths, dims
        # and signeds after calling returns()
        node.return_info = node.node_type.returns(node.methodname, input_types, bit_lengths, dims, signeds)
        return_rec = node.return_info[0]

        if val:
            node.input_types = (val_return_rec["type"],)
            node.bit_lengths = (return_rec["bitlen"], val_return_rec["bitlen"])
            node.dims = (return_rec["dim"], val_return_rec["dim"])
            node.signeds = (return_rec["signed"], val_return_rec["signed"])
        else:
            node.input_types = tuple()
            node.bit_lengths = (return_rec["bitlen"],)
            node.dims = (return_rec["dim"],)
            node.signeds = (return_rec["signed"],)

        if isinstance(node.parent, Attribute):
            copy_type_info(node.parent, node)

        assert hasattr(node, "return_info")
        assert hasattr(node, "node_type")
        assert(isinstance(node.keywords_data, dict))
        assert "dim" in node.keywords_data
        assert type(node.return_info[0]["dim"]) != dict

        node.initial_info = node.return_info[0]
        #self.symbol_table.dump()

    def visit_tasty_function_ctor(self, node):
        """ tasty functions should only be infered when be dereferenced/called"""
        if __debug__:
            state.log.debug("\ninfer tasty_func_ctor %s", dump(node, True, True))

        node.tasty_function = eval(to_source(node), self.my_globals)
        node.return_info = ({"type" : node.node_type, "bitlen" : None, "dim" : None, "signed" : None},)
        node.methodname = node.func.id
        node.call_type = CALL_TYPE_TASTY_FUNC_CTOR
        node.initial_info = node.return_info[0]
        node.input_types = tuple()

    def visit_tasty_func_call(self, node):
        if __debug__:
            state.log.debug("\ninfer tasty func call %d %s", id(node), dump(node, True, True))

        if isinstance(node.func, Name):
            fqnn = get_fqnn(node.func)
            symbol_record = self.symbol_table.identify(fqnn)
            # checking for tasty function
            kwargs = symbol_record["kwargs"]
            node.tasty_function = kwargs["tasty_function"]
            kwargs = symbol_record["kwargs"]
            node_type = kwargs["type"]
            node.initial_info = kwargs
        elif isinstance(node.func, Call):
            self.visit(node.func)
            node.tasty_function = node.func.tasty_function
        else:
            raise UnknownSymbolError() # than this is not a tasty func

        for i in node.args:
            self.visit(i)

        retrieve_node_args(node)

        node.methodname = "__call__"
        node.call_type = CALL_TYPE_TASTY_FUNC_CALL

        node.input_types = list()
        node.bit_lengths = list()
        node.dims = list()
        node.signeds = list()
        for arg in node.args:
            ri = arg.return_info[0]
            node.input_types.append(ri["type"])
            node.bit_lengths.append(ri["bitlen"])
            node.dims.append(ri["dim"])
            node.signeds.append(ri["signed"])

        node.return_info = node.tasty_function.returns(
            node.methodname, node.input_types, node.bit_lengths, node.dims,
            node.signeds)

        if isinstance(node.parent, Attribute):
            copy_type_info(node.parent, node)
        elif isinstance(node.func, Call):
            # directly called tasty functions after instantiation
            node.initial_info = node.func.return_info[0]

    def visit_method(self, node):
        """here we inspect function and method calls"""

        if __debug__:
            state.log.debug("\ninfer method %d %s", id(node), dump(node, True, True))
        node.call_type = CALL_TYPE_METHOD

        # handling method of party attribute
        if (isinstance(node.func, Attribute) and
            isinstance(node.func.value, Attribute)):
            attribute_symbol_record = self.symbol_table.identify(
                get_fqnn(node.func.value))
            node.func.return_info = node.func.value.return_info = \
                (attribute_symbol_record["kwargs"],)

        self.visit(node.func)
        for i in node.args:
            self.visit(i)

        if hasattr(node, "attr"):
            if node.attr == "input":
                node.methodname = "input"
            elif node.attr == "output":
                node.methodname = "output"
            else:
                raise NotImplementedError()
            assert hasattr(node, "methodname")
            return

        if hasattr(node.func, "attr"):
            if node.func.attr == "input":
                cnode = node.func.value
                node.methodname = "input"
                if (hasattr(cnode, "call_type") and
                    cnode.call_type == CALL_TYPE_CTOR):
                    add_keyword(cnode, "empty", True)
                copy_type_info(node, node.func)
                node.initial_info = cnode.return_info[0]
                node.input_types = tuple()
                node.dims = tuple()
                return
            elif node.func.attr in ("output", "setup_output"):
                node.methodname = node.func.attr
                return

        retrieve_node_args(node)

        symbol_table = self.symbol_table


        # handles methods of bounded party attributes
        if isinstance(node.func, Attribute):
            if hasattr(node.func.value, "call_type") and node.func.value.call_type == CALL_TYPE_CTOR:
                attribute_node_type = node.func.value.node_type
                attribute_kwargs = node.func.value.return_info[0]
            elif (isinstance(node.func.value, Attribute) or
                isinstance(node.func.value, Call)):
                fqnn = find_fqnn(node.func.value)
                attribute_symbol_record = symbol_table.identify(fqnn)
                attribute_kwargs = attribute_symbol_record["kwargs"]
                attribute_node_type = attribute_kwargs["type"]
            elif isinstance(node.func.value, Subscript):
                attribute_kwargs = node.func.value.return_info[0]
                attribute_node_type = attribute_kwargs["type"]
            node.methodname = methodname = node.func.attr
            node.input_types = list()
            node.bit_lengths = [attribute_kwargs["bitlen"]]
            node.dims = [attribute_kwargs["dim"]]
            node.signeds = [attribute_kwargs["signed"]]
            node.input_types.extend([arg.return_info[0]["type"]
                for arg in node.args])
            node.dims.extend([arg.return_info[0]["dim"] for arg in node.args])
            node.bit_lengths.extend([arg.return_info[0]["bitlen"]
                for arg in node.args])
            node.return_info = attribute_node_type.returns(
                node.methodname, node.input_types, node.bit_lengths, node.dims, node.signeds)
            node.initial_info = attribute_kwargs
        else:
            raise TastySyntaxError(
                "expected a method of a subclass of Value or Vec, got '%s'" %
                type(node.func))

        if isinstance(node.parent, Attribute):
            copy_type_info(node.parent, node)
        assert hasattr(node, "return_info")
        assert hasattr(node, "initial_info")
        assert hasattr(node, "methodname")
        assert type(node.return_info[0]) == dict
        assert type(node.initial_info) == dict

    def visit_Call(self, node):
        """We 'll inspect calls and decide if they are constructor invocations,
        tasty function invocations, object methods or global functions /
        procedures. Then we call the appropriate inference handler method"""

        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))

        if isinstance(node.func, Name):
            name_node = node.func
            if name_node.id in _cost_class_names:
                node.node_type = name_node.node_type = node_type = \
                    _types_module[name_node.id]

                if issubclass(node_type, types.TastyFunction):
                    self.visit_tasty_function_ctor(node)
                    return
                if name_node.id in ('Homomorphic', 'HomomorphicVec',
                    "Modular", "ModularVec"):
                    state.generate_keys = True
                self.visit_constructor(node)
                return
            else:
                try:
                    self.visit_tasty_func_call(node)
                    return
                except (FqnnError,
                    UnknownSymbolError), e:
                    if __debug__:
                        state.log.exception(e)
                    pass
                except Exception, e:
                    if __debug__:
                        state.log.exception(e)
                    raise TypeError("Used Type %r not a registered type of TASTY" % name_node.id)
        if isinstance(node.func, Call):
            self.visit_tasty_func_call(node)
            return

        self.visit_method(node)

    def visit_Subscript(self, node):
        if not has_parent_node(node, self.protocol_name):
            return
        if __debug__:
            state.log.debug("\ninfer %d %s", id(node), dump(node, True, True))

        fqnn = get_fqnn(node.value)
        symbol_record = self.symbol_table.identify(fqnn)
        kwargs = symbol_record["kwargs"]
        node_type = kwargs["type"]
        node.initial_info = kwargs
        node.input_types = tuple()
        node.bit_lengths = (kwargs["bitlen"],)
        node.dims = (kwargs["dim"],)
        node.signeds = (kwargs["signed"],)
        node.methodname = "__getitem__"
        node.return_info = node_type.returns(node.methodname, node.input_types, node.bit_lengths, node.dims, node.signeds)


    def visit_Assign(self, node):
        if not has_parent_node(node, self.protocol_name):
            return
        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))

        value_node = node.value
        try:
            annotate_node(value_node)
        except (NotImplementedError, UnknownSymbolError):
            self.visit(value_node)

        if __debug__:
            state.log.debug("\nactual node %s", dump(node, True, True))
        assert hasattr(value_node, "return_info")

        for target in node.targets:
            handle_target_node(self, target, value_node)

        self.symbol_table.dump()

    def visit_AugAssign(self, node):
        """ checking for tasty operators with previously undefined targets and
        annotates them with the type information of the source"""

        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))

        left_node = node.target
        right_node = node.value
        fqnn = get_fqnn(left_node)

        if isinstance(node.op, LShift):
            # special treatment, since semantic redefined as sending operator
            # with optional type conversion

            if not isinstance(node.target, Attribute):
                raise TastySyntaxError("Can only send to a party")

            if node.value.passive:
                direction = "receive"
            else:
                direction = "send"

            try:
                # processing bound party attribute, both sides have same type
                right_fqnn = get_fqnn(right_node)
                symbol_record = self.symbol_table.identify(right_fqnn)
                dest_return_rec = symbol_record["kwargs"]
                dest_type = dest_return_rec["type"]
                dest_bitlen = dest_return_rec["bitlen"]
                dest_dim = dest_return_rec["dim"]
                dest_signed = dest_return_rec["signed"]
                node.input_types = (dest_type, dest_type)
                node.bit_lengths = (dest_bitlen, dest_bitlen)
                node.dims = (dest_dim, dest_dim)
                node.signeds = (dest_signed, dest_signed)
                node.return_info = ((dest_type, dest_bitlen, dest_dim, dest_signed),)
                node.methodname = "%s_%s_%s" % (
                    dest_type.__name__, dest_type.__name__, direction)
            except (FqnnError, UnknownSymbolError):
                if not isinstance(right_node, Call):
                    raise TastySyntaxError("value of tasty operator must be " \
                    "a constructor call of a type of TASTY or a " \
                    "bound PartyAttribute, got %r" %
                    type(right_node))

                # tasty operator including type conversion

                self.visit(right_node)

                node.return_info = right_node.return_info
                dest_return_rec = right_node.return_info[0]

                src_node = right_node.keywords_map["val"]
                src_return_rec = src_node.return_info[0]
                src_type = src_return_rec["type"]
                dest_type = dest_return_rec["type"]

                node.input_types = (dest_return_rec["type"], src_return_rec["type"])
                node.bit_lengths = (dest_return_rec["bitlen"], src_return_rec["bitlen"])
                node.dims = (dest_return_rec["dim"], src_return_rec["dim"])
                node.signeds = (dest_return_rec["signed"], src_return_rec["signed"])
                node.methodname = "%s_%s_%s" % (
                    src_type.__name__, dest_type.__name__, direction)

            try_finish_bitlenless(self, fqnn, dest_return_rec["bitlen"])
            try_finish_signed(self, fqnn, dest_return_rec["signed"])

            node.initial_info = node.return_info[0]

            self.symbol_table.add_symbol(
                fqnn,
                kwargs=dest_return_rec,
                lineno=node.lineno,
                colno=node.col_offset)
        else:
            # normal pythonic operator behaviour

            fqnn = get_fqnn(left_node)

            node.dims = list()
            node.bit_lengths = list()
            node.input_types = list()
            node.signeds = list()

            annotate_item_of_node(self, left_node, node, False)
            annotate_item_of_node(self, right_node, node)

            node.methodname = bases.AUGASSIGN_METHODS[type(node.op)]

            node.return_info = left_node.return_info[0]["type"].returns(node.methodname,
                node.input_types, node.bit_lengths, node.dims, node.signeds)

            kwargs = node.return_info[0]

            self.symbol_table.add_symbol(
                fqnn,
                kwargs=kwargs,
                lineno=node.lineno,
                colno=node.col_offset)

    def visit_Compare(self, node):
        if __debug__:
            state.log.debug("infer %s", dump(node, True, True))

        if len(node.comparators) > 2:
            raise TastySyntaxError("tastyc is not yet ready for more than 2 comparision items")

        left_node = node.left
        right_node = node.comparators[0]

        node.dims = list()
        node.bit_lengths = list()
        node.input_types = list()
        node.signeds = list()

        node.methodname = bases.CMPOP_METHODS[type(node.ops[0])]

        annotate_item_of_node(self, left_node, node, False)
        annotate_item_of_node(self, right_node, node)

        node_type = left_node.return_info[0]["type"]

        node.return_info = node_type.returns(
            node.methodname, node.input_types, node.bit_lengths,
            node.dims, node.signeds)

        node.initial_info = node.left.return_info[0]

    def visit_UnaryOp(self, node):
        if __debug__:
            state.log.debug("infer %s", dump(node, True, True))

        node.dims = list()
        node.bit_lengths = list()
        node.input_types = list()
        node.signeds = list()

        annotate_item_of_node(self, node.operand, node, False)

        node.methodname = UNARYOP_METHODS[type(node.op)]

        node_type = node.operand.return_info[0]["type"]

        node.return_info = node_type.returns(node.methodname, node.input_types,
            node.bit_lengths, node.dims, node.signeds)

        node.initial_info = node.operand.return_info[0]

    def visit_BinOp(self, node):
        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))

        if isinstance(node.left, Str):
            return

        node.dims = list()
        node.bit_lengths = list()
        node.input_types = list()
        node.signeds = list()

        left_node = node.left
        right_node = node.right

        annotate_item_of_node(self, left_node, node, False)
        annotate_item_of_node(self, right_node, node)

        node_type = left_node.return_info[0]["type"]
        node.initial_info = left_node.return_info[0]

        node.methodname = bases.BINOP_METHODS[type(node.op)]

        node.return_info = node_type.returns(
            node.methodname, node.input_types, node.bit_lengths, node.dims, node.signeds)

    def visit_BoolOp(self, node):
        if __debug__:
            state.log.debug("\ninfer %s", dump(node, True, True))

        self.generic_visit(node)
        retrieve_node_args(node, node.values)

        value = node.values[0]
        node_type = value.return_info[0]["type"]
        node.initial_info = node.value.return_info[0]
        node.methodname = BINOP_METHODS[type(node.op)]
        node.input_types = list()
        node.bit_lengths = list()
        node.dims = list()
        for ix, arg in enumerate(value.tasty_args):
            return_rec = arg.node_return_info[0]
            if ix:
                node.input_types.append(return_rec["type"])
            node.bit_lengths.append(return_rec["bitlen"])
            node.dims.append(return_rec["dim"])

        node.return_info = node_type.returns(node.methodname,
            node.input_types, node.bit_lengths, node.dims, node.signeds)

    def check(self):
        if self.nodes_without_bitlen:
            raise TastySyntaxError("Following variables are declared without " \
                " bitlen and are not finished by either reassignment or " \
                "item assignment: %r" % self.nodes_without_bitlen)
