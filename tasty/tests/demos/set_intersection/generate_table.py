# -*- coding: utf-8 -*-

from tasty.cost_results import extract_costs
from tasty.utils import tasty_plot
from tasty.postprocessing import *
from tasty.tastyc.bases import dump_table

def process_costs(cost_objs):

    x_label = "Bitlength"

    # -----------------
    # TIME
    # -----------------
    
    x_values = [i["params"]["SETSIZE_C"] for i in cost_objs[0][0]]

    y_values = extract_costs(cost_objs[0],
        ("C setup", "client>real>setup>duration"),
        ("S setup", "server>real>setup>duration"),
        ("C Online", "client>real>online>duration"),
        ("S Online", "server>real>online>duration"))

    send_values = extract_costs(cost_objs[0],
        ("C setup send", "client>real>setup>send"),
        ("S setup send", "server>real>setup>send"),
        ("C online send", "client>real>online>send"),
        ("S online send", "server>real>online>send"))

    total_send = add_values(send_values, ("C setup send", "S setup send", "C online send", "S online send"), "Send total")


    print "Elements (m = n)  |",
    for i in x_values:
        print str(i).ljust(10), " |",

    print
    for label, data in y_values:
        print label.ljust(16), " |",
        for i in data:
            print str(i).ljust(10), " |",
        print

    print total_send[0].ljust(16), " |", 
    for i in total_send[1]:
        print str(i).ljust(10), " |",
        
