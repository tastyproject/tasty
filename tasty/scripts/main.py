# -*- coding: utf-8 -*-

"""Tasty framework configuration"""

import sys

from tasty import state
from tasty.config import create_configuration, validate_configuration
from tasty import cost_results
from tasty import utils
from tasty import protocol_mode


def start(parent_pipe=None):
    """The 'main' function of tasty.

    @type parent_pipe: multiprocessing.Pipe
    @keyword parent_pipe: An optional communication socket with an instrumenting
    parent process.
    """

    state.parent_pipe = parent_pipe
    create_configuration()

    utils.init_log()
    validate_configuration()
    cost_results.CostSystem.get_costs()
    old_path = sys.path
    sys.path = [state.config.protocol_dir, ] + sys.path

    # keep this import since we need all custom classes be registered before
    # compiler run

    if state.config.server:
        protocol_mode.process_server_mode()
    else:
        protocol_mode.process_client_mode()

    sys.path = old_path

    if __debug__:
        state.log.info("done - bye...")


if __name__ == '__main__':
    start()
