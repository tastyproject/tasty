# -*- coding: utf-8 -*-

from tasty.types import *
from tasty import state
from tasty import utils
from tasty import config
from tasty.types.key import generate_keys
from tasty import cost_results

state.config = config.create_configuration(host="::1", port=8000, client=True, verbose=2, symmetric_security_parameter=80, asymmetric_security_parameter=1024, testing=True, protocol_dir=utils.tasty_path("debug/dummy_protocol"))
cost_results.CostSystem.create_costs()
p,state.key = generate_keys(1024)
utils.init_log()
config.validate_configuration()
