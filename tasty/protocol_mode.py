# -*- coding: utf-8 -*-

"""Implements the features needed for the real mode of tasty"""

import re
import time
import sys
import tasty
import cPickle
import gc
import os.path
import shutil
import socket

from datetime import datetime
from multiprocessing import Pipe

from tasty import state

from tasty import utils
from tasty import tastyot
from tasty import osock
from tasty.types import Party, PassiveParty
from tasty.tastyc import compiler_start
from tasty.types.key import generate_keys
from tasty import cost_results

from tasty.config import runtime_config_check
from tasty.tastyc.tastyc import compiler_start_driver_mode

from tasty.protocols import protocol as tastyprotocol
from tasty.protocols.transport import Transport
from tasty.tastyc import bases
from tasty.crypt.garbled_circuit import generate_R
#from tasty.debug_kram import _protocol_pass
import tasty.types.key
import multiprocessing
#import cProfile
#import pstats
import socket

__all__ = ["protocol_pass", "process_client_mode", "process_server_mode", "_protocol_pass"]


def _protocol_pass():
    tasty.protocol_mode.protocol_pass(state.client, state.server)

def process_client_mode():
    while 1:
        if __debug__:
            state.log.info("starting in client mode...")
        cost_results.CostSystem.create_costs()
        state.key = None
        state.client = client = state.active_party = Party(Party.CLIENT)
        state.server = server = state.passive_party = PassiveParty(Party.SERVER)

        if __debug__:
            state.log.info("trying to connect to server...")
        waiting = False
        while 1:
            try:
                sock = osock.ClientObjectSocket(state.config.host, state.config.port)
                break
            except socket.error, e:
                try:
                    sock = osock.ClientObjectSocket(state.config.host,
                        state.config.port, family=socket.AF_INET)
                    break
                except socket.error, e:
                    if not state.config.client_waiting:
                        raise
                    pass
                if not waiting:
                    waiting = True
                    if __debug__:
                        state.log.info("waiting for server to come up...")
                time.sleep(1)

        client.set_socket(sock)
        runtime_config_check(sock)

        if __debug__:
            state.log.info("Starting homomorphic key generation...")
        public_key, state.key = generate_keys(
            state.config.asymmetric_security_parameter)
        if __debug__:
            state.log.info("key generation done")

        sock.sendobj(public_key)

        cost_results.CostSystem.costs["real"]["analyze"]["duration"].start()
        compiler_start()
        #cProfile.runctx('compiler_start()', globals(), locals(), "tasty.debug")
        cost_results.CostSystem.costs["real"]["analyze"]["duration"].stop()

        #p = pstats.Stats('tasty.debug')
        #p.sort_stats('cumulative').print_stats()
        protocol_pass(client, server)
        if not state.config.serve_forever:
            break
        assert len(state.key._key.r) == 0


def process_server_mode():
    try:
        server_socket = osock.ServerObjectSocket(state.config.host,
            state.config.port)
    except socket.error, e:
            # defaults to ipv6 but a ipv4 address was given, testing it
        server_socket = osock.ServerObjectSocket(state.config.host,
        state.config.port, family=socket.AF_INET)

    while 1:
        if __debug__:
            state.log.info("starting in server mode...")
        cost_results.CostSystem.create_costs()
        state.server = server = state.active_party = Party(Party.SERVER,
            server_socket=server_socket)
        state.client = client = state.passive_party = PassiveParty(Party.CLIENT)

        if __debug__:
            state.log.info("waiting for client...")

        sock, addr = server_socket.accept()
        server.set_socket(sock)

        if __debug__:
            state.log.info("incoming connection from %s %d", addr[0], addr[1])

        runtime_config_check(sock)

        state.R = generate_R()

        state.key  = sock.recvobj()

        cost_results.CostSystem.costs["real"]["analyze"]["duration"].start()
        compiler_start()
        #cProfile.runctx('compiler_start()', globals(), locals(), "tasty.debug")
        cost_results.CostSystem.costs["real"]["analyze"]["duration"].stop()

        #p = pstats.Stats('tasty.debug')
        #p.sort_stats('cumulative').print_stats()
        protocol_pass(client, server)
        if not state.config.serve_forever:
            break


def do_protocol(
    client,
    server,
    setup_protocol,
    online_protocol,
    kwargs=dict()):
    """Does the dirty work - runs the protocol phases"""

    if __debug__:
        state.log.info("Starting setup phase...")
    state.protocol_run = True
    state.precompute = True

    if state.config.server:
        sock = server.socket()
        party = server
    else:
        sock = client.socket()
        party = client

    costs = cost_results.CostSystem.get_costs()

    analyze_costs = costs["real"]["analyze"]
    setup_costs = costs["real"]["setup"]
    online_costs = costs["real"]["online"]

    #sync the partys
    tastyprotocol.Protocol.sync(sock)
    sock.send_count.get_and_reset()
    sock.recv_count.get_and_reset()

    setup_costs["duration"].start()
    if __debug__:
        state.log.info("precomputing '%d' OTs", costs["abstract"]["setup"]["accumulated"].get("ot", 0))
    state.tasty_ot = tastyot.TastyOT(party, costs["abstract"]["setup"]["accumulated"].get("ot", 0))
    if __debug__:
        state.log.debug("OTs done")

    if state.generate_keys:
        #state.key.reset()
        ENC_count = costs["abstract"]["online"]["accumulated"].get("Enc", 0)
        if __debug__:
            state.log.info("precomputing '%d' random masks for homomorphic values", ENC_count)
        state.key.precompute(ENC_count, state.config.threads)
    if __debug__:
        state.log.debug("rs done")
    protocol_method = getattr(setup_protocol, state.config.protocol_name)

    if state.protocol_instrumentated:
        protocol_method(client, server, kwargs)
    else:
        protocol_method(client, server)

    tastyprotocol.Protocol.precompute()
    setup_costs["duration"].stop()
    setup_costs["send"] = sock.send_count.get_and_reset()
    setup_costs["recv"] = sock.recv_count.get_and_reset()
    # sync the partys
    tastyprotocol.Protocol.sync(sock)
    sock.send_count.get_and_reset()
    sock.recv_count.get_and_reset()

    if __debug__:
        state.log.info("setup phase done.\n")

    ############################################

    if __debug__:
        state.log.info("Starting online phase...\n")
    state.precompute = False

    online_costs["duration"].start()
    protocol_method = getattr(online_protocol, state.config.protocol_name)
    if state.protocol_instrumentated:
        protocol_method(client, server, kwargs)
    else:
        protocol_method(client, server)

    online_costs["duration"].stop()
    online_costs["send"] = send=sock.send_count.get_and_reset()
    online_costs["recv"] = recv=sock.recv_count.get_and_reset()
    state.protocol_run = False
    if __debug__:
        state.log.info("online phase done.\n")
    tastyprotocol.Protocol.sync(sock)

    cost_results.CostSystem.finalize_costs()

    if state.config.server:
        server.socket().sendobj(costs)
        state.report = report = server.socket().recvobj()
    else:
        cost_results.CostSystem.other_costs = client.socket().recvobj()
        report = cost_results.CostSystem.generate_cost_report()
        client.socket().sendobj(report)
    if state.config.analyze:
        state.log.info(report + "\n")
    sock.send_count.get_and_reset()
    sock.recv_count.get_and_reset()


def driver_run_iterations(client, server, driver):
    if __debug__:
        state.log.info("Executing driver for tasty protocol...\n")

    log = state.log
    config = state.config

    for kwargs in driver.next_params():
        if __debug__:
            state.log.info("Using parameters %r", kwargs)
        cost_results.CostSystem.create_costs()
        cost_results.CostSystem.costs["params"] = kwargs
        driver.new_iteration()

        compiler_start_driver_mode(kwargs)

        ### FIXME: FIND OUT WHY THIS IS NECESSARY!!
        time.sleep(1)

        setup_protocol = __import__(config.final_setup_protocol,
            globals(), locals(), [])
        online_protocol = __import__(config.final_online_protocol,
            globals(), locals(), [])

        setup_protocol.driver = driver
        online_protocol.driver = driver

        do_protocol(client, server, setup_protocol, online_protocol, kwargs)
        if config.client:
            driver.next_costs(cost_results.CostSystem.costs, cost_results.CostSystem.other_costs)
            client = state.active_party = Party(client.role,
                socket=client.socket())
            server = state.passive_party = PassiveParty(Party.SERVER)
        else:
            server = state.active_party = Party(server.role,
                socket=server.socket(), server_socket=server.server_socket())
            client = state.passive_party = PassiveParty(Party.CLIENT)

        driver.iteration_end()

    if config.client:
        path = utils.result_path("costs.bin")
        if os.path.isfile(path):
            shutil.copyfile(path, path + ".old")
        cPickle.dump((driver.client_costs(), driver.server_costs(), config), open(path, "wb"), 2)

def protocol_pass(client, server):
    """Does the dirty work"""

    config = state.config
    log = state.log

    if state.config.server:
        sock = server.socket()
    else:
        sock = client.socket()
    costs = cost_results.CostSystem.get_costs()
    analyze_costs = costs["real"]["analyze"]
    analyze_costs["send"] = sock.send_count.get_and_reset()
    analyze_costs["recv"] = sock.send_count.get_and_reset()

    old_path = sys.path
    sys.path = [state.config.protocol_dir, ] + sys.path

    if state.assigned_driver_node:

        driver_protocol = __import__("protocol_final", globals(), locals(), [])
        driver = getattr(driver_protocol, "driver")

        if state.config.use_driver:
            driver_run_iterations(client, server, driver)
        else:
            setup_protocol = __import__(state.config.final_setup_protocol,
                globals(), locals(), [])
            online_protocol = __import__(state.config.final_online_protocol,
                globals(), locals(), [])
            kwargs = driver.next_params().next()
            do_protocol(client, server, setup_protocol, online_protocol, kwargs)
    else:
        setup_protocol = __import__(state.config.final_setup_protocol, globals(),
            locals(), [])
        online_protocol = __import__(state.config.final_online_protocol, globals(),
            locals(), [])

        do_protocol(client, server, setup_protocol, online_protocol)

    sys.path = old_path
