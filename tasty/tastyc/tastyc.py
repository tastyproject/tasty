# -*- coding: utf-8 -*-

"""tastyc configuration module"""

import copy
import sys

import os.path
from ast import *
import gc

from tasty import state
from tasty.exc import TastySyntaxError
from tasty.types import *

from tasty.tastyc import bases

from tasty.tastyc.codegen import to_source
from tasty.tastyc.analyzation import Parenter
from tasty.tastyc.analyzation import Qualificator
from tasty.tastyc.analyzation import Symbolizer
from tasty.tastyc.analyzation import AttributePropagator
from tasty.tastyc.analyzation import ConstantSymbolizer
from tasty.tastyc.pass_dispatching import OnlinePassDispatcher, SetupPassDispatcher, OnlinePruner, SetupPruner
from tasty.tastyc.transformation import DriverParameterPropagator
from tasty.tastyc.transformation import OnlineTransformer, SetupTransformer
from tasty.tastyc.transformation import KwargsPropagator
from tasty.tastyc.transformation import SimpleEvaluator
from tasty.tastyc.transformation import PlainTypeConverter
from tasty.tastyc.transformation import TypeCompletionTransformer
from tasty.tastyc.transformation import ConstantPropagator
from tasty.tastyc.transformation import DanglingGarbledBinder
from tasty.tastyc.analyze_costs import analyze_costs


__all__ = ["compiler_start", "compiler_start_driver_mode"]

state.my_globals = globals()


def compile_protocol():
    """creates custom protocol versions tailored for setup
    and online phase"""

    config = state.config
    full_ast = bases.TastyCBase.full_ast

    setup_ast = copy.deepcopy(full_ast)
    online_ast = copy.deepcopy(full_ast)

    setup_symbol_table = copy.deepcopy(bases.TastyCBase.symbol_table)
    online_symbol_table = copy.deepcopy(bases.TastyCBase.symbol_table)

    if "types" not in bases.TastyCBase.imports:
        types_import = ImportFrom(module='tasty.types',
            names=[alias(name='*', asname=None)], level=0)
        setup_ast.body.insert(0, types_import)
        online_ast.body.insert(0, types_import)
    if "conversions" not in bases.TastyCBase.imports:
        con_import = ImportFrom(module='tasty.types',
            names=[alias(name='conversions', asname=None)], level=0)
        setup_ast.body.insert(0, con_import)
        online_ast.body.insert(0, con_import)

    if __debug__:
        state.log.info("\ncompiling setup protocol version...")
    setup_ast = SetupTransformer(setup_symbol_table).visit(setup_ast)
    SetupPassDispatcher(setup_symbol_table).visit(setup_ast)
    setup_ast = SetupPruner(setup_symbol_table).visit(setup_ast)
    setup_ast = TypeCompletionTransformer(setup_symbol_table).visit(setup_ast)
    fix_missing_locations(setup_ast)

    setup_filename = protocol_path("{0}.py".format(config.final_setup_protocol))
    f = open(setup_filename, "w")
    f.write(to_source(setup_ast))
    f.close()

    if __debug__:
        state.log.info("\ncompiling online protocol version...")
    OnlineTransformer(online_symbol_table).visit(online_ast)
    OnlinePassDispatcher(online_symbol_table).visit(online_ast)
    OnlinePruner(online_symbol_table).visit(online_ast)
    TypeCompletionTransformer(online_symbol_table).visit(online_ast)
    fix_missing_locations(online_ast)

    online_filename = protocol_path("{0}.py".format(config.final_online_protocol))
    f = open(online_filename, "w")
    f.write(to_source(online_ast))
    f.close()

    return setup_ast, online_ast


def propagate_constants(ast):
    p = ConstantPropagator()
    ast = p.visit(ast)
    p.cleanup_symbol_table()
    p.visit_Assign = p.visit_Assign_2nd_pass
    p.visit_Name = p.visit_Name_2nd_pass
    ast = p.visit(ast)
    return ast


def bind_dangling_garbleds(ast):
    p = DanglingGarbledBinder()
    full_ast = p.visit(ast)
    p.finish()
    return full_ast


def do_driver_selection(original_ast):

    log = state.log
    config = state.config

    num_drivers = len(state.driver_classes)
    if num_drivers > 1:
        if config.driver_name in state.driver_classes:
            state.driver_class = config.driver_name
        else:
            while 1:
                chosen_driver = int(raw_input("Found %d different 'Driver' implementations.\nPlease select intended driver via -D <DriverName> flag, or choose from the following list:\n%s\n:" %
                    (num_drivers,
                    "\n".join("%d - %s" % (ix, cname)
                        for ix,cname in enumerate(state.driver_classes)))
                ))
                if 0 <= chosen_driver < len(state.driver_classes):
                    state.driver_class = state.driver_classes[chosen_driver]
                    break
    elif num_drivers == 1:
        state.driver_class = state.driver_classes[0]

    if config.test_mode:
        config.driver_mode = True
        bases.assign_driver(original_ast, "TestDriver")
        state.use_driver = True
        if "TestDriver" not in bases.TastyCBase.imports:
            driver_import = ImportFrom(module='tasty.types.driver',
                names=[alias(name='TestDriver', asname=None)], level=0)
            bases.TastyCBase.imports.add("TestDriver")
            original_ast.body.insert(0, driver_import)
    elif config.use_driver:
        if not state.driver_class:
            state.log.error("You selected driver mode without implementing a test driver.\nPlease provide one by subclassing from 'Driver' in the protocol!")
            sys.exit(-1)
        if not bases.check_driver_assignment(state.driver_class):
            bases.assign_driver(original_ast, state.driver_class)
        if not state.protocol_instrumentated:
            state.log.error("Error: You requested driver mode, but provided a protocol without the 3rd formal parameter 'params'.\nPlease provide a protocol with the signature 'protocol(client, server, params)'")
            sys.exit(-1)
    elif state.driver_class or state.protocol_instrumentated:
        if not bases.check_driver_assignment("IODriver"):
            bases.assign_driver(original_ast, "IODriver", True)
        if "IODriver" not in bases.TastyCBase.imports:
            driver_import = ImportFrom(module='tasty.types.driver',
                names=[alias(name='IODriver', asname=None)], level=0)
            bases.TastyCBase.imports.add("IODriver")
            original_ast.body.insert(0, driver_import)


def clean_protocol_environment():
    """cleaning possibly created modules and memory"""

    bases.TastyCBase.symbol_table.clear()

    try:
        del sys.modules[state.config.final_setup_protocol]
    except KeyError:
        pass

    try:
        del sys.modules[state.config.final_online_protocol]
    except KeyError:
        pass

    gc.collect()


def compiler_start():
    """analyzes protocol structure, runs several optimization technics,
    retrieves abstract costs and transforms tasty protocols into
    internal representation.

    For now we have implemented constant propagation, partial evaluation
    and dead code elimination."""

    log = state.log
    config = state.config

    #if config.exclude_compiler:
        #return

    if __debug__:
        log.info("starting tasty compiler...")
    # this can be important if there are defined and registered new tasty
    # primitives get available at analyzation time in tasty protocols
    old_path = sys.path
    sys.path = [config.protocol_dir, ] + sys.path

    g = globals()
    protocol = __import__("protocol", g,
        g, [])
    sys.path = old_path

    state.my_globals.update(protocol.__dict__)

    bases.TastyCBase.symbol_table.clear()
    text = open(config.protocol_file_path).read().replace("\r\n", "\n")
    bases.TastyCBase.original_ast = original_ast = compile(
        text, config.protocol_file_path, "exec", PyCF_ONLY_AST)
    Parenter().visit(original_ast)
    Qualificator().visit(original_ast)

    do_driver_selection(original_ast)

    AttributePropagator().visit(original_ast)

    fix_missing_locations(original_ast)

    f = open(protocol_path("protocol_final.py"), "w")
    f.write(to_source(original_ast))
    f.close()
    protocol = __import__("protocol_final", g, g, [])

    full_ast = bases.TastyCBase.full_ast =  original_ast

    if not config.use_driver:
        if state.assigned_driver_node:
            bases.TastyCBase.full_ast = full_ast = copy.deepcopy(
                original_ast)
            bases.TastyCBase.full_ast = full_ast = DriverParameterPropagator(
                protocol.driver.next_params().next()).visit(full_ast)
        ConstantSymbolizer().visit(full_ast)
        full_ast = propagate_constants(full_ast)
        full_ast = SimpleEvaluator().visit(full_ast)
        full_ast = PlainTypeConverter().visit(full_ast)
        fix_missing_locations(full_ast)
        symbolizer = Symbolizer(state.my_globals)
        symbolizer.visit(full_ast)
        try:
            symbolizer.check()
        except Exception, e:
            state.log.exception(e)
            sys.exit(-1)

        full_ast = bind_dangling_garbleds(full_ast)

        setup_ast, online_ast = compile_protocol()
        analyze_costs(setup_ast, online_ast)

    if __debug__:
        log.info("tasty compiler done")


def compiler_start_driver_mode(kwargs):
    """called before each driver run iteration"""

    # cleanup
    clean_protocol_environment()

    bases.TastyCBase.full_ast = full_ast = copy.deepcopy(
        bases.TastyCBase.original_ast)

    DriverParameterPropagator(kwargs).visit(full_ast)

    ConstantSymbolizer().visit(full_ast)
    full_ast = propagate_constants(full_ast)
    full_ast = SimpleEvaluator().visit(full_ast)
    full_ast = PlainTypeConverter().visit(full_ast)
    fix_missing_locations(full_ast)

    symbolizer = Symbolizer(state.my_globals)
    symbolizer.visit(full_ast)
    symbolizer.check()

    full_ast = bind_dangling_garbleds(full_ast)

    # compile ast into internal representation (actually real python code)
    setup_ast, online_ast = compile_protocol()

    # static cost analyzation
    analyze_costs(setup_ast, online_ast)
