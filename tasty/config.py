# -*- coding: utf-8 -*-

"""This module handles configuration creation and validation"""

import hashlib
import os
import os.path
import sys
import logging
import warnings

from ConfigParser import ConfigParser
from optparse import OptionParser, OptionGroup, OptionValueError

import tasty
from tasty.exc import *
from tasty import utils
from tasty import state
from tasty import types
import tasty.protocols.otprotocols
from tasty.protocols.otprotocols import *
from tasty.types.party import Party

__all__ = ["config", "create_configuration", "post_configuration"]

COLOR = {"n" : "", "r" : '\033[1;31m', "g" : '\033[1;32m', "y" : '\033[1;33m',
    "b" : '\033[1;34m', "m" : '\033[1;35m', "c" : '\033[1;36m'}
COLOR_CHOICES = ("n", "r", "g", "y", "m", "c")


g_parser = None

def create_configuration(**kwargs):
    """Creates and returns a valid config object.

    It merges cli arguments, actual parameters of this function and
    key/value pairs of a given config file.

    Used in conjunction with L{validate_configuration}

    Precedence of origin in descending order:
        - Actual keyword arguments
        - command line arguments
        - config file values

    In addition this function sets the global configuration object.

    @type protocol_dir: str
    @keyword protocol_dir: the directory of the protocol file to process

    @type port: int
    @keyword port: port number

    @type host: str
    @keyword host: host to connect to/ listen on

    @type analyze: bool
    @keyword analyze: only run analyze phase

    @type client: bool
    @keyword client: if True tasty runs as client, otherwise in server mode

    @type threads: bool
    @keyword threads: number of threads/processes to use

    @type filter_callgraph: bool
    @keyword filter_callgraph: If True only shows relevant information,
    otherwise shows all calling graph nodes

    @type security_level: "ultra-short" | "short" | "medium" | "long"
    @keyword security_level: ultra-short/short/medium/long-term security

    @type ot_type: "Paillier" | "EC" | "EC_c"
    @keyword ot_type: type of OT protocol

    @type ot_chain: list
    @keyword ot_chain: list of used OT protocols

    @type use_driver: bool
    @param use_driver: if True, and a procedure with the signature
    driver(client, server) is present in precified tasty protocol, tasty will
    execute the that method instead of the original run procedure, and creates a
    graph of the result

    @type symmetric_security_parameter: int
    @keyword symmetric_security_parameter: bit length of

    @type asymmetric_security_parameter: int
    @keyword asymmetric_security_parameter: number of threads/processes to use

    @type compiler_warnings_are_errors: bool
    @keyword compiler_warnings_are_errors: turns warnings into errors

    @type homomorphic_type: HomomorphicType
    @type homomorphic_type: the actual implementation of HomomorphicType

    @type testing: bool
    @keyword testing: set this to True if you create a test config and want
    to relax config var validation

    @rtype: instance
    @return: instance of an old style class providing values as attributes

    """

    #if state.config:
        #warnings.warn("Reconfiguring tasty. Hopefully you know what you are doing", UserWarningOnce)

    usage = "usage: %%prog [options] %s" % os.path.join(
        "path", "to", "protocol", "directory")
    global g_parser
    parser = g_parser = OptionParser(usage=usage, version="%%prog %s" % tasty.__version__)

    parser.add_option("-I", "--info",
        action="store_true",
        dest="info",
        default=False,
        help="show program information")

    net_opts = OptionGroup(parser, "network options")
    mode_opts = OptionGroup(parser, "operational options")
    protocol_opts = OptionGroup(parser, "protocol options")
    compiler_opts = OptionGroup(parser, "compiler options")

    net_opts.add_option("-p", "--port",
        action="store",
        dest="port",
        type="int",
        help="port number")
    net_opts.add_option("-H", "--host",
        action="store",
        dest="host",
        help="host address")

    #mode_opts.add_option("-L", "--log-file",
        #action="store",
        #dest="log_file",
        #help="explicitly specify the complete log file path and name (default=protocol_dir/results/tasty.log)")
    mode_opts.add_option("-c", "--client",
        action="store_true",
        dest="client",
        default=False,
        help="run in client mode")
    mode_opts.add_option("-s", "--server",
        action="store_true",
        dest="server",
        default=False,
        help="run in server mode")
    mode_opts.add_option("-F", "--forever",
        action="store_true",
        dest="serve_forever",
        default=False,
        help="run until killed by user (in conjunction with both options '--server' or '--client'")

    mode_opts.add_option("-t", "--threads",
        action="store",
        dest="threads",
        type="int",
        default=1,
        help="number of cpus to use. Not fully used yet!")
    mode_opts.add_option("-C", "--color",
        action="store",
        dest="color",
        choices=COLOR_CHOICES,
        default=None,
        help="Output color. Especially when tasty puts its output into the same terminal, its nice to have a different color for each party."
        " Choose one of (n)one, (r)ed, (g)reen, (y)ellow, (c)yan, (m)agenta")
    mode_opts.add_option("-v", "--verbose",
        action="count",
        dest="verbose",
        default=0,
        help="debug output level, can be repeated to increase verbosity")
    mode_opts.add_option("-f", "--force-protocol",
        action="store_true",
        dest="force_protocol",
        default=False,
        help="force usage of given protocol and send it to other party if protocols differ. If both parties use this, it will be set to False.")
    mode_opts.add_option("-A", "--accept-protocol",
        action="store_true",
        dest="accept_protocol",
        default=False,
        help="if other party wants to force you using its protocol version tasty denyies and exits with error. This flag makes this party accept forced protocols. Warning: Only activate this flag, if you are controlling both parties and accept that this is a potential security thread.")
    mode_opts.add_option("--test_mode",
        action="store_true",
        dest="test_mode",
        default=False,
        help="Internal flag!!! This flag must not be used directly, but should be set for functional tests.")
    mode_opts.add_option("--client-fail-if-no-server",
        action="store_false",
        dest="client_waiting",
        default=True,
        help="makes the client to fail if no server is reachable. Default behaviour is waiting for a server to come up.")

    protocol_opts.add_option("-l", "--security_level",
        action="store",
        dest="security_level",
        type="string",
        default="short",
        help="security level can be either 'ultra-short', 'short' (default), 'medium' or 'long'")

    protocol_opts.add_option("-d", "--driver",
        action="store_true",
        dest="use_driver",
        default=False,
        help="turn tasty into driver/batch mode")

    protocol_opts.add_option("-P", "--protocol_name",
        action="store",
        dest="protocol_name",
        default="protocol",
        help="name of actual protocol method to run. default='protocol'?")

    protocol_opts.add_option("-D", "--driver_name",
        action="store",
        dest="driver_name",
        help="name of actual Driver implementation to use if more than one provided.?")

    protocol_opts.add_option("-O", "--oblivious_transfer",
        action="store",
        dest="ot_chain",
        default=False,
        help="overwrite oblivious chain")

    #compiler_opts.add_option("-E", "--exclude_compiler",
        #action="store_true",
        #dest="exclude_compiler",
        #default=False,
        #help="only run compiled protocol without compiling it")
    compiler_opts.add_option("-a", "--analyze",
        action="store_true",
        dest="analyze",
        default=False,
        help="showing costs on exit")
    #compiler_opts.add_option("-u", "--find_unused",
        #action="store_true",
        #dest="find_unused",
        #default=False,
        #help="searches for potentially unused attributes and constants. For now there are many false positives so this is optionally")
    compiler_opts.add_option("--homomorphic_type",
        action="store",
        dest="homomorphic_type",
        default=types.Paillier,
        help="sets the homomorphic type to use")
    compiler_opts.add_option("--homomorphic_vec_type",
        action="store",
        dest="homomorphic_vec_type",
        default=types.PaillierVec,
        help="sets the homomorphic vec type to use")
    compiler_opts.add_option("--WError", action="store_true",
        help="turn warnings into errors", dest="compiler_warnings_are_errors", default=False)

    parser.add_option_group(compiler_opts)
    parser.add_option_group(mode_opts)
    parser.add_option_group(net_opts)
    parser.add_option_group(protocol_opts)

    configuration, args = parser.parse_args()

    #if len(sys.argv) <= 1:
        #parser.print_help()
        #sys.exit(0)

    if configuration.info:
        sys.exit(0)

    if "verbose" in kwargs:
        configuration.verbose = kwargs["verbose"]

    if "protocol_dir" in kwargs:
        configuration.protocol_dir = os.path.abspath(kwargs["protocol_dir"])
    else:
        try:
            configuration.protocol_dir = os.path.abspath(args[0])
        except IndexError:
            pass

    if "host" in kwargs:
        configuration.host = kwargs["host"]

    if "port" in kwargs:
        configuration.port = kwargs["port"]

    if "client" in kwargs:
        configuration.client = kwargs["client"]

    if "threads" in kwargs:
        configuration.threads = kwargs["threads"]

    if "analyze" in kwargs:
        configuration.analyze = kwargs["analyze"]

    if "ot_chain" in kwargs:
        configuration.ot_chain = kwargs["ot_chain"]

    if "color" in kwargs:
        if kwargs["color"] not in COLOR_CHOICES:
            raise OptionValueError("unknown color %r specified" % kwargs["color"])
        configuration.color = COLOR[kwargs["color"]]

    if "verbose" in kwargs:
        configuration.ot_chain = kwargs["verbose"]

    if "client-fail-if-no-server" in kwargs:
        configuration.client_waiting = kwargs["client-fail-if-no-server"]

    if "security_level" in kwargs:
        configuration.security_level = kwargs["security_level"]

    if "asymmetric_security_parameter" in kwargs:
        configuration.asymmetric_security_parameter = kwargs["asymmetric_security_parameter"]

    if "symmetric_security_parameter" in kwargs:
        configuration.symmetric_security_parameter = kwargs["symmetric_security_parameter"]

    if "compiler_warnings_are_errors" in kwargs:
        configuration.compiler_warnings_are_errors = kwargs["compiler_warnings_are_errors"]

    if "test_mode" in kwargs:
        configuration.test_mode = kwargs["test_mode"]

    log_name = "tasty_%s.log" % ("client" if configuration.client else "server")
    try:
        configuration.log_file = os.path.join(configuration.protocol_dir, "results", log_name)
    except AttributeError:
        parser.print_help()
        sys.exit(0)

    if not configuration.client_waiting and configuration.server:
	    raise ValueError("specifying client waiting option makes only sence for clients!")

    if configuration.color == "n" or sys.platform == "win32":
        state.color = ""
        state.color_reset = ""
    elif configuration.server:
        state.party_name = "server"
        if not configuration.color:
            # make server log output blue, for client it's already set to green
            state.color = "\033[35;1m"
    if configuration.color:
        state.color = COLOR[configuration.color]

    # important - don't delete that
    state.config = configuration

    return configuration

def validate_configuration():
    """called after log was created"""

    global g_parser
    config = state.config

    if config.compiler_warnings_are_errors:
        warnings.simplefilter('error')

    if not config.protocol_dir or not os.path.isdir(config.protocol_dir):
        state.log.error("cannot find protocol directory!")
        parser.print_help()
        sys.exit(-2)

    if not config.client and not config.server:
        state.log.error("Error: Choose either client or server mode!")
        g_parser.print_help()
        sys.exit(-2)

    config.file_path = os.path.join(
        config.protocol_dir, "protocol.ini")

    if not os.path.isfile(config.file_path):
        state.log.error("Missing config file")
        g_parser.print_help()
        if __debug__:
            dump_config(config)
        raise Exception()

    protocol_file_path = os.path.join(
        config.protocol_dir, "protocol.py")

    if not os.path.isfile(protocol_file_path):
        protocol_file_path = os.path.join(
            config.protocol_dir, "protocol.pyc")
        if not os.path.isfile(protocol_file_path):
            state.log.error("Missing protocol file")
            g_parser.print_help()
            sys.exit(-2)

    config.protocol_file_path = protocol_file_path

    config.protocol = os.path.splitext(
        os.path.basename(protocol_file_path))[0]

    if config.client:
        role_part = "client"
        state.role = Party.CLIENT
    else:
        role_part = "server"
        state.role = Party.SERVER

    config.final_setup_protocol = "protocol_setup_%s" % role_part

    config.final_online_protocol = "protocol_online_%s" % role_part

    config.final_protocol = "protocol_final"

    config_file = ConfigParser()
    config_file.read([config.file_path, ])

    # prepare same protocol version check
    config.protocol_hash = hashlib.sha256(
        open(protocol_file_path).read()).hexdigest()

    for key, value in config_file.items("main"):
        if getattr(config, key, None):
            continue
        try:
            setattr(config, key, int(value))
        except ValueError:
            setattr(config, key, value)

    #ot_chain = config.ot_chain = config.ot_chain.split(":")
    ot_chain = config.ot_chain
    #subs = tasty.protocols.otprotocols.OTProtocol.__subclasses__()
    #for ix, i in enumerate(ot_chain):
        #for j in subs:
            #if i == j.__name__:
                #ot_chain[ix] = j

    if config.security_level == "ultra-short":
        config.symmetric_security_parameter = 80
        config.asymmetric_security_parameter = 1024
        if config.ot_chain == "Paillier":
            config.ot_chain = [PaillierOT]
        elif config.ot_chain == "EC":
            config.ot_chain = [IKNP03, NP_EC_OT_secp160r1]
        else:
            config.ot_chain = [IKNP03, NP_EC_OT_secp160r1_c]
    elif config.security_level == "short":
        config.symmetric_security_parameter = 96
        config.asymmetric_security_parameter = 1776
        if config.ot_chain == "Paillier":
            config.ot_chain = [PaillierOT]
        elif config.ot_chain == "EC":
            config.ot_chain = [IKNP03, NP_EC_OT_secp192r1]
        else:
            config.ot_chain = [IKNP03, NP_EC_OT_secp192r1_c]
    elif config.security_level == "medium":
        config.symmetric_security_parameter = 112
        config.asymmetric_security_parameter = 2432
        if config.ot_chain == "Paillier":
            config.ot_chain = [PaillierOT]
        if config.ot_chain == "EC":
            config.ot_chain = [IKNP03, NP_EC_OT_secp224r1]
        else:
            config.ot_chain = [IKNP03, NP_EC_OT_secp224r1_c]
    elif config.security_level == "long":
        config.symmetric_security_parameter = 128
        config.asymmetric_security_parameter = 3248
        if config.ot_chain == "Paillier":
            config.ot_chain = [PaillierOT]
        if config.ot_chain ==  "EC":
            config.ot_chain = [IKNP03, NP_EC_OT_secp256r1]
        else:
            config.ot_chain = [IKNP03, NP_EC_OT_secp256r1_c]
    else:
        raise ValueError("security_level must be either \"ultra-short\", \"short\", \"medium\", or \"long\".")

    del g_parser

    types.Homomorphic = config.homomorphic_type
    types.HomomorphicVec = config.homomorphic_vec_type

    if config.verbose == 1:
        state.log.setLevel(logging.INFO)
    elif config.verbose >= 2:
        state.log.setLevel(logging.DEBUG)
    if __debug__:
        dump_config(config)


def dump_config(config):
    size_1 = max(len(str(v)) for v in config.__dict__.iterkeys())
    size_2 = max(len(str(v)) for v in config.__dict__.itervalues())
    #line = "-" * (size_1 + size_2 + 3)
    line = "-" * 79
    state.log.info("configuration values")
    state.log.info(line)
    for k, v in config.__dict__.iteritems():
        state.log.info("%s | %s", k.ljust(size_1), v)
    state.log.info(line +  "\n")


def runtime_config_check(sock):

    if __debug__:
        state.log.info("checking configuration...")
    config = state.config
    log = state.log
    sock.sendobj((tasty.__version__, config))
    other_version, other_config = sock.recvobj()

    if __debug__:
        log.info("checking tasty version...")
    if tasty.__version__ != other_version:
        log.error("Error: tasty version mismatch - Exiting...")
        sys.exit(-2)

    if __debug__:
        log.info("checking driver usage...")
    if config.use_driver != other_config.use_driver:
        log.error("Error: parties differ at tasty driver usage - Exiting...\n\n")
        sys.exit(-2)

    if __debug__:
        log.info("checking driver implementation...")
    if config.driver_name != other_config.driver_name:
        log.error("Error: parties differ at tasty driver implementations - Exiting...\n\n")
        sys.exit(-2)

    if __debug__:
        log.info("checking tasty protocol hash...")
    if config.protocol_hash != other_config.protocol_hash:
        if config.force_protocol and other_config.force_protocol:
            config.force_protocol = False

        if config.force_protocol:
            if not other_config.accept_protocol:
                log.error("Error: Their party does not accept our protocol version - Exiting...")
                sys.exit(-2)
            else:
                log.critical("Warning: Protocols differ but other party accepted our protocol version")
                sock.sendobj(open(config.protocol_file_path).read())
        elif other_config.force_protocol:
            if not config.accept_protocol:
                log.error("Error: Our party does not accept their protocol version - Exiting...")
                sys.exit(-2)
            else:
                log.critical("Warning: Protocols differ but this party accepted their protocol version")
                open(config.protocol_file_path, "w").write(sock.recvobj())
        else:
            log.error("Error: Using not the same protocol version.")
            sys.exit(-2)

    if __debug__:
        state.log.info("checking done")
