# -*- coding: utf-8 -*-

import copy

from collections import deque

from ast import *

from gmpy import mpz
from tasty.exc import UnknownSymbolError, TastySyntaxError, GoOutHere, FqnnError
from tasty import state
from tasty.tastyc.codegen import to_source
from tasty.types.metatypes import Value
from tasty.types.party import PartyAttribute

AUGASSIGN_METHODS = {
    Add:        '__iadd__',
    Sub:        '__isub__',
    Mult:       '__imul__',
    Div:        '__idiv__'
}

BINOP_METHODS = {
    Add:        '__add__',
    Sub:        '__sub__',
    Mult:       '__mul__',
    Div:        '__div__',
    FloorDiv:   '__floordiv__',
    Mod:        '__mod__',
    LShift:     '__lshift__',
    RShift:     '__rshift__',
    BitOr:      '__or__',
    BitAnd:     '__and__',
    BitXor:     '__xor__'
}

CMPOP_METHODS = {
    Eq:         '__eq__',
    Gt:         '__gt__',
    GtE:        '__ge__',
    In:         '__contains__',
    #Is:         '__is__',
    #IsNot:      'is not',
    Lt:         '__lt__',
    LtE:        '__le__',
    NotEq:      '__ne__',
    NotIn:      '__contains__'
}


UNARYOP_METHODS = {
    Invert:     '__invert__',
    Not:        '_not',
    UAdd:       '__abs__',
    USub:       '__neg__'
}


CALL_TYPE_CTOR = 0
CALL_TYPE_METHOD = 1
CALL_TYPE_TASTY_FUNC_CTOR = 2
CALL_TYPE_TASTY_FUNC_CALL = 3
CALL_TYPE_CONVERSION = 4
CALL_TYPE_MAX = 5


PASS_NAME = {Value.C_SETUP : "client setup", Value.S_SETUP : "server setup", Value.C_ONLINE : "client online", Value.S_ONLINE : "server online"}


class SetupStanzaMixin(object):
    def __init__(self):
        if state.config.client:
            self.affects_stanza = Value.C_SETUP
            self.affects_demask = Value.NO_C_SETUP
        else:
            self.affects_stanza = Value.S_SETUP
            self.affects_demask = Value.NO_S_SETUP
        self.stanza_name = PASS_NAME[self.affects_stanza]


class OnlineStanzaMixin(object):
    def __init__(self):
        if state.config.client:
            self.affects_stanza = Value.C_ONLINE
            self.affects_demask = Value.NO_C_ONLINE
        else:
            self.affects_stanza = Value.S_ONLINE
            self.affects_demask = Value.NO_S_ONLINE
        self.stanza_name = PASS_NAME[self.affects_stanza]


class NodeInserter(object):
    def __init__(self):
        self.additions = list()

    def finish(self):
        for container, before_node, assignment in self.additions:
            container.insert(container.index(before_node), assignment)

    def mark_for_insertion_in_node(self, node, before_node, assignment):
        """Insert the newly created assignment at appropriate place right before
        before_node and overwrite before_node in parent with a call by
        reference (attribute).

        Attention: Actual insertion must be defered after this visitor has
        finished hole ast, since modifying a list while iterating over it
        invalidates the iterator. The dirty work is done in add_nodes"""

        if isinstance(node, FunctionDef):
            # next compount node, we can insert it here
            self.additions.append((node.body, before_node, assignment))
            assignment.parent = node
        elif isinstance(node, For):
            # next compount node, we can insert it here
            self.additions.append((node.body, before_node, assignment))
            assignment.parent = node
        elif isinstance(node, BinOp):
            # insert assignment before node
            self.mark_for_insertion_in_node(node.parent, node, assignment)
        elif isinstance(node, keyword) or isinstance(node, Call):
            self.mark_for_insertion_in_node(node.parent, node, assignment)
        elif isinstance(node, Assign):
            self.mark_for_insertion_in_node(node.parent, node, assignment)
        else:
            raise NotImplementedError("implement insertion for node type %r" %
                type(node))

    def replace_in_parent(self, node, new_node):
        """replaces node with new_node in node's parent node"""
        parent = node.parent
        if isinstance(parent, BinOp):
            if parent.left == node:
                parent.left = new_node
            elif parent.right == node:
                parent.right = new_node
            else:
                raise ValueError("could not found the child node you gave me in this parent node.")
        elif isinstance(parent, Assign):
            if parent.value == node:
                parent.value = new_node
            else:
                raise ValueError("could not found the child node you gave me in this parent node.")
        else:
            raise NotImplementedError("Not implemented for node type %r" %
                type(parent))

    def bind_node(self, node, party, name):
        """assigns 'node' as symbol 'name' to Party 'party' and returns
        the attribute node"""
        fqnn = party, name
        attribute = Attribute(value=Name(id=party, ctx=Load()), attr=name)
        assignment = Assign(targets=[attribute], value=node)
        fix_missing_locations(attribute)
        fix_missing_locations(assignment)

        attribute.return_info = node.return_info

        kwargs = node.return_info[0]

        self.symbol_table.add_symbol(fqnn, kwargs=kwargs)
        #self.symbol_table.dump()

        attribute.role = node.role
        attribute.passive = node.passive
        attribute.parent = node.parent

        assignment.role = node.role
        assignment.passive = node.passive
        assignment.parent = node.parent

        self.mark_for_insertion_in_node(node.parent, node, assignment)
        return attribute

class TastySymbolTable(object):
    def __init__(self, parent=None):
        self._symbol_table = dict()
        self._deleted_symbol_table = dict()
        self._parent_table = parent

    def identify(self, fqnn):
        """retrieve meta data from the symbol table if present"""

        try:
            return self._symbol_table[fqnn]
        except KeyError:
            pass

        try:
            return self._deleted_symbol_table[fqnn]
        except KeyError:
            pass

        #also trying to find fqnn in parent tables if present, else raise
        try:
            return self.parent_table.identify(fqnn)
        except AttributeError:
            raise UnknownSymbolError("Unknown symbol %r" % list(fqnn))


    def add_symbol(self, fqnn, kwargs=None, args=None, bitmask=0, lineno=1,
        colno=1):

        if __debug__:
            state.log.debug("adding symbol '%r' with %r to symbol table...", list(fqnn), kwargs)

        assert "type" in kwargs
        assert "bitlen" in kwargs
        assert "dim" in kwargs
        assert "signed" in kwargs

        if kwargs is not None  and isinstance(kwargs, dict):
            kwargs = copy.deepcopy(kwargs)
        else:
            kwargs = dict()

        if args is not None  and isinstance(args, list):
            args = copy.deepcopy(args)
        else:
            args = list()

        self._symbol_table[fqnn] = {
            "args" : args,
            "kwargs" : kwargs,
            "bitmask" : bitmask,
            "lineno" : lineno,
            "colno" : colno}

    def __contains__(self, fqnn):
        return fqnn in self._symbol_table

    def remove_symbol(self, fqnn):
        if __debug__:
            state.log.debug("deleting symbol '%r' from symbol table", list(fqnn))
        try:
            self._deleted_symbol_table[fqnn] = self._symbol_table[fqnn]
            del self._symbol_table[fqnn]
        except KeyError:
            pass

    def clear(self):
        self._symbol_table.clear()

    def dump(self):
        symbol_len = 1
        if not self._symbol_table:
            rows = [("-", ("-",))]
        else:
            rows = list()
            for k, v in self._symbol_table.iteritems():
                record = list()
                tmp = copy.copy(v)
                entry = tmp["kwargs"].items()
                del tmp["kwargs"]
                entry.extend(tmp.items())
                k_str = str(k)
                symbol_len = max(symbol_len, len(k_str))
                ii = iter(entry)
                first_k, first_v = ii.next()
                record.append("%s : %s" % (str(first_k), str(first_v)))
                for j, w in ii:
                    record.append(
                        ("%s : %s" % (str(j), str(w)))
                )
                rows.append((k_str, record))
        dump_table("\nSymbol table records:", symbol_len, rows)


class TastyCBase(object):
    """Base class for tasty compiler
    """

    symbol_table = TastySymbolTable()
    active_role = None
    passive_role = None
    active_name = None
    passive_name = None
    kwargs_name = None
    protocol_name = None
    original_ast = None
    full_ast = None
    imports = set()
    read_fqnns = set()


class TastyVisitor(NodeVisitor, TastyCBase):
    """Base class for tasty specific ast visitors"""

    pass


def has_parent_node(node, parent_fqnn):
    """checks if node has a parent node with name 'parent_fqnn'"""

    mynode = node
    #while hasattr(mynode, "parent") and mynode.parent:
    try:
        while 1:
            if (isinstance(mynode.parent, FunctionDef) and
                mynode.parent.name == parent_fqnn):
                return True
            mynode = mynode.parent
    except AttributeError:
        #state.log.debug(dump(mynode, True, True))
        #if state.config.verbose >= 2:
        #state.log.exception(e)
        pass
    return False


def get_parameter_dims(obj):
    if not isinstance(obj, List):
        raise TypeError()
    item = obj.elts[0]
    bitlen = 0
    for i in item.keywords:
        if i.arg == "bitlen":
            bitlen = i.value.n
            return bitlen
    raise ValueError()

def get_actual_dims_ast(obj):
    dims = list()
    dims.append(len(obj.elts))
    for i in obj.elts:
        if isinstance(i, List) or isinstance(i, Tuple):
            dims.extend(get_actual_dims_ast(i))
            break
    return dims

def get_actual_dims_python(obj):
    dims = list()
    dims.append(len(obj))
    for i in obj:
        if isinstance(i, list) or isinstance(i, tuple):
            dims.extend(get_actual_dims_python(i))
            break
    return dims


def dump_table(header, symbol_len, rows):
    """helper method to create and displays a nicely formatted table
    as debug information.

    @type lines: interable of iterables of strings
    @param lines: , n rows of m columns to display"""

    line = "\033[34;1m%s\033[0;0m" % ("-" * 79)
    state.log.debug(header)
    empty_k = " " * symbol_len
    for name, record in rows:
        state.log.debug(line)
        ii = iter(record)
        state.log.debug("%s | %s" % (name.ljust(symbol_len), ii.next()))
        for b in ii:
            state.log.debug("%s | %s" % (empty_k.ljust(symbol_len), b))
    else:
        state.log.debug(line + "\n")


def symbol_record_2_return_info(record):
    raise Exception()


def return_info_2_symbol_record(info):
    raise Exception()


def find_fqnn(node):
    """Recursivly searches for an inner node which represents a fqnn"""

    try:
        return get_fqnn(node)
    except Exception, e:
        if isinstance(node, Call):
            return find_fqnn(node.func)
        elif isinstance(node, Attribute):
            return find_fqnn(node.value)
        raise e


def get_fqnn(node):
    """returns the fully qualified node name, but as a tuple

    e.g:
        None, 'foo' -> foo (fqnn via Name node)
        server, 'foo' -> server.foo (fqnn via Attribute node)
        None, 'foo[0]' -> foo[0] (fqnn via Subscript node)
    """

    if hasattr(node, "fqnn"):
        return node.fqnn
    if isinstance(node, BinOp):
        raise FqnnError("bad style")
    elif isinstance(node, Attribute):
        try:
            fqnn = node.fqnn = node.value.id, node.attr
            return fqnn
        except AttributeError:
            fqnn = node.fqnn = get_fqnn(node.value)
            return fqnn
    elif isinstance(node, Name):
        fqnn = node.fqnn = (node.id,)
        return fqnn
    elif isinstance(node, Subscript):
        if isinstance(node.value, Name):
            raise TastySyntaxError("TASTYL only supports bounded subscriptions")
        if isinstance(node.slice.value, Name):
            fqnn = node.fqnn = (node.value.value.id, node.value.attr,
                node.slice.value.id)
            return fqnn
        elif isinstance(node.slice.value, Num):
            fqnn = node.fqnn = (node.value.value.id, node.value.attr,
                node.slice.value.n)
            return fqnn
        else:
            raise FqnnError(
                "Error in line %d: fqnn for type '%s' cannot be evaluated" % (
                    node.lineno, type(node)))
    else:
        #if state.config.verbose >= 2:
            #state.log.error("fqnn for node type '%s' cannot be evaluated" %
                #type(node))
            #state.log.error(dump(node, True, True))
        raise FqnnError("Error in line %d: fqnn for type '%s' " \
            "cannot be evaluated" % (node.lineno, type(node)))


def infer_arg_Attribute(arg):
    return TastyCBase.symbol_table.identify(get_fqnn(arg))["kwargs"]


def eval_arg(arg):
    real_data = eval(to_source(arg))
    return {"type" : type(real_data), "bitlen" : None, "dim" : [len(real_data)], "signed" : None, "val" : real_data}


def eval_num_arg(arg):
    n = arg.n
    return {"type" : int, "bitlen" : mpz(n).bit_length(), "dim" : [1], "signed" : True if n < 0 else False, "val" : n}

def infer_iterable(arg):
    for item in arg.elts:
        if isinstance(item, Attribute):
            arg.return_info = infer_arg_Attribute(item)
        else:
            raise NotImplementedError("infer_iterable not implemented for type %r" % type(item))
    return {"type" : isinstance(arg, Tuple) and tuple or list, "bitlen" : None, "dim" : [len(arg.elts)], "signed" : None, "val" : None}


def retrieve_node_args(node, iterable=None):

    if not iterable:
        iterable = node.args

    for arg in iterable:
        if isinstance(arg, Num):
            arg.return_info = (eval_num_arg(arg),)
        elif isinstance(arg, Attribute) or isinstance(arg, Name):
            arg.return_info = (infer_arg_Attribute(arg),)
        elif isinstance(arg, List):
            try:
                arg.return_info = (eval_arg(arg),)
            except Exception:
                arg.return_info = (infer_iterable(arg),)
        elif isinstance(arg, Tuple):
            try:
                arg.return_info = (eval_arg(value),)
            except Exception:
                arg.return_info = (infer_iterable(arg),)
        elif (isinstance(arg, BinOp) or
            isinstance(arg, Subscript) or
            isinstance(arg, UnaryOp) or
            isinstance(arg, Call) or
            isinstance(arg, Str)):
            pass
        else:
            raise NotImplementedError(
                "Positional argument parsing not implemented for '%s'" %
                    type(arg))


def copy_type_info(dst_node, src_node):
    """Copies symbol metadata from source to destination node"""

    try:
        dst_node.node_type = src_node.node_type
    except AttributeError:
        pass
    try:
        dst_node.ctor_kwargs = src_node.ctor_kwargs
    except AttributeError:
        pass
    try:
        dst_node.return_info = src_node.return_info
    except AttributeError:
        pass
    try:
        dst_node.bitlen_not_finished = src_node.bitlen_not_finished
    except AttributeError:
        pass

    try:
        dst_node.signed_not_finished = src_node.signed_not_finished
    except AttributeError:
        pass


def set_inherited_attributes(node, attribute_list):
    """propagates synthesized attributes of node to all child nodes"""

    attributes = [(a, getattr(node, a))
        for a in attribute_list if hasattr(node, a)]
    for child in walk(node):
        for k, v in attributes:
            setattr(child, k, v)

def add_keyword(node, name, value):
    if not isinstance(value, AST):
        value = compile(str(value), "", "single", PyCF_ONLY_AST).body[0].value
    if name not in node.keywords_map:
        kw = keyword(arg=name,
                            value=value, lineno=node.lineno,
                            col_offset=node.col_offset+100)
        node.keywords.append(kw)
        node.keywords_map[name] = kw

def propagate_kwargs(node):
    if __debug__:
        state.log.debug("\npropagate kwargs %s", dump(node, True, True))
    try:
        kwargs = None
        val_keyword = node.keywords_map["val"]
        if isinstance(val_keyword.value, Attribute):
            fqnn = get_fqnn(val_keyword.value)
            val_symbol_record = TastyCBase.symbol_table.identify(fqnn)
            kwargs = val_symbol_record["kwargs"]
        elif isinstance(val_keyword.value, Num):
            kwargs = val_keyword.return_info[0]
        else:
            if not issubclass(val_keyword.return_info[0][0], PartyAttribute):
                raise GoOutHere()
            kwargs = val_keyword.return_info[0]

        #add_keyword(node, 'bitlen', kwargs["bitlen"])
        #add_keyword(node, 'dim', kwargs["dim"])

        fix_missing_locations(node)
    except GoOutHere:
        pass


def annotate_node(node):
    try:
        symbol_record = TastyCBase.symbol_table.identify(get_fqnn(node))
        kwargs = symbol_record["kwargs"]
        node.return_info = (kwargs,)
    except (FqnnError, UnknownSymbolError):
        if isinstance(node, Num):
            node.return_info = (eval_num_arg(node),)
        else:
            raise NotImplementedError(type(node))

def find_keyword(key, node):
    """Returns the index and instance of the keyword named 'key' in the construtor call named 'node'.
    Otherwise you will get a (None, None) tuple.

    Since we don't now, when which transformer adds or removes a keyword, so
    it's a bad idea to keep the position/index of keywords beyond the lifetime
    of the current visitor class."""

    for ix, keyword in enumerate(node.keywords):
        if keyword.arg == key:
            return ix, keyword
    return None, None


def annotate_item_of_node(runner, argument, node, add_type=True):
    """retrieves type information via symbol_table or via inference and adds
        them into the nodes' appropriate data sinks used by all compiler passes.
    """

    if (isinstance(argument, Attribute) or
        isinstance(argument, Name)):
        fqnn = get_fqnn(argument)
        symbol_record = runner.symbol_table.identify(fqnn)
        kwargs = symbol_record["kwargs"]
        node_type = kwargs["type"]
        if add_type:
            node.input_types.append(node_type)
        node.bit_lengths.append(kwargs["bitlen"])
        node.dims.append(kwargs["dim"])
        node.signeds.append(kwargs["signed"])
        argument.return_info = (kwargs,)
    else:
        runner.visit(argument)
        kwargs = argument.return_info[0]
        if add_type:
            node.input_types.append(kwargs["type"])
        node.bit_lengths.append(kwargs["bitlen"])
        node.dims.append(kwargs["dim"])
        node.signeds.append(kwargs["signed"])


def handle_target_node(runner, target, value_node):
    if isinstance(target, Tuple):
        return_info = value_node.return_info
        if len(return_info) != len(target.elts):
            raise SyntaxError("wrong number of type " \
                "information records provided")
        for ix, i in enumerate(target.elts):
            i_fqnn = get_fqnn(i)
            runner.symbol_table.add_symbol(i_fqnn,
                kwargs=return_info[ix],
                lineno=target.lineno,
                colno=target.col_offset)
    elif (isinstance(target, Attribute) or
        isinstance(target, Name) or
        isinstance(target, Subscript)):
        fqnn = get_fqnn(target)

        try:
            kwargs = value_node.return_info[0]
        except AttributeError:
            kwargs = dict()

        value_node_rec = value_node.return_info[0]

        try:
            value_fqnn = get_fqnn(value_node)
            if value_fqnn[0] != fqnn[0]:
                raise TastySyntaxError("Syntax error at line %d: for sending and/or conversion please use the tasty operator '<<='" % target.lineno)
        except FqnnError:
            pass

        if hasattr(value_node, "bitlen_not_finished"):
            runner.nodes_without_bitlen[fqnn] = value_node

        if hasattr(value_node, "signed_not_finished"):
            runner.nodes_without_signed[fqnn] = value_node

        if isinstance(target, Subscript):
            try_finish_bitlenless(runner, fqnn[:2], kwargs["bitlen"])
            try_finish_signed(runner, fqnn[:2], kwargs["signed"])

        if hasattr(value_node, "tasty_function"):
            kwargs["tasty_function"] = value_node.tasty_function
        try:
            runner.symbol_table.add_symbol(fqnn,
                kwargs=kwargs,
                lineno=target.lineno,
                colno=target.col_offset)
        except TastySyntaxError, e:
            if state.config.verbose >= 2:
                state.log.exception(e)


def try_finish_bitlenless(runner, fqnn, bitlen):
    backref = runner.nodes_without_bitlen.get(fqnn)
    if backref:
        backref_symbol_record = runner.symbol_table.identify(fqnn)
        backref_kwargs = backref_symbol_record["kwargs"]

        _bitlen = copy.copy(bitlen)

        backref.return_info[0]["bitlen"] = _bitlen

        backref_kwargs["bitlen"] = _bitlen

        if hasattr(backref, "keywords_data"):
            backref.keywords_data["bitlen"] = _bitlen

        add_keyword(backref, 'bitlen', _bitlen)

        lb = len(backref.bit_lengths)
        if lb == 1:
            backref.bit_lengths = (_bitlen,)
        else:
            backref.bit_lengths = tuple([bitlen].extend(backref.bit_lengths[1:]))

        delattr(backref, "bitlen_not_finished")
        del runner.nodes_without_bitlen[fqnn]
        #runner.symbol_table.dump()

def try_finish_signed(runner, fqnn, signed):
    backref = runner.nodes_without_signed.get(fqnn)
    if backref:
        backref_symbol_record = runner.symbol_table.identify(fqnn)
        backref_kwargs = backref_symbol_record["kwargs"]

        backref.return_info[0]["signed"] = signed

        backref_kwargs["signed"] = signed

        if hasattr(backref, "keywords_data"):
            backref.keywords_data["signed"] = signed

        add_keyword(backref, 'signed', signed)

        lb = len(backref.signeds)
        if lb == 1:
            backref.signeds = (signed,)
        else:
            backref.signeds = tuple([signed].extend(backref.signeds[1:]))

        delattr(backref, "signed_not_finished")
        del runner.nodes_without_signed[fqnn]
        #runner.symbol_table.dump()


def check_driver_assignment(driver_class_name):
    if state.assigned_driver_node and state.assigned_driver_node.value.func.id == driver_class_name:
         return True
    return False


def assign_driver(protocol, driver_class_name, with_args = False):
    index = 0
    args = []

    if with_args and state.driver_params:
        args.append(state.driver_params.value)
    if not state.assigned_driver_node:
        for ix, i in enumerate(protocol.body):
            if isinstance(i, FunctionDef):
                index = ix
                break

        assign = Assign(targets=[Name(id="driver", ctx=Store())],
            value=Call(func=Name(id=driver_class_name, ctx=Load()), args=args,
            keywords=[], starargs=None, kwargs=None))
        assign.targets[0].parent = assign
        assign.value.func.parent = assign.value
        assign.value.parent = assign
        assign.parent = protocol
        protocol.body.insert(index, assign)
        state.assigned_driver_node = assign
    else:
        node = state.assigned_driver_node
        node.value = Call(func=Name(id=driver_class_name, ctx=Load()), args=args,
            keywords=[], starargs=None, kwargs=None)
        node.value.func.parent = node.value
        node.value.parent = node
