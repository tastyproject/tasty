# -*- coding: utf-8 -*-

import os.path

config = None

log = None

R = None

protocol_run = False

precompute = True

tasty_ot = None

role = None

active_party = None

passive_party = None

tasty_root = os.path.abspath(os.path.dirname(__file__))

generate_keys = False

my_globals = None

report = None

key = None

color = "\033[32;1m"
color_reset = "\033[0;0m"

party_name = "client"

# optional multiprocessing.Pipe object for communication with parent processes
# like e.g. unittests
parent_pipe = None

protocol_instrumentated = False

assigned_driver_node = None

driver_explicitely_assigned = False

driver_name = "driver"

driver_classes = list()

driver_class = None

driver_params = None

info_text = """TASTY: Tool for Automating Secure Two-partY computations

URL: http://tastyproject.net

(c) 2009-2010 System Security Lab, Ruhr-University Bochum, Germany

License: GPL version 3

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Contact: info@tastyproject.net
"""
