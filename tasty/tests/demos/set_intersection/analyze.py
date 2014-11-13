# -*- coding: utf-8 -*-
from tasty.cost_results import extract_costs
from tasty.utils import tasty_plot

def process_costs(cost_objs):
    """ Process measured cost objects """
    x_values = [i["params"]["SETSIZE_C"] for i in cost_objs[0][0]]

    # select costs to be drawn
    y_values = extract_costs(cost_objs[0],
    	# C's online time
        ("C Online","client>real>online>duration"),
        # S's online time
        ("S Online","server>real>online>duration"),
        ("S Setup time", "server>real>setup>duration"),
        ("C Setup time", "client>real>setup>duration"))

    x = extract_costs(cost_objs[0], ("", "client>real>analyze>duration"), ("","server>real>analyze>duration"))
    print x
    print y_values

    x_label = "set size"  # label of x axis
    y_label = "Time in ms" # label of y axis
    graph_name = "Times for set intersection"

    # draw graph into PDF file
    tasty_plot(graph_name, x_label, y_label, x_values, y_values, legend="inside", outfile="intersection_time.pdf", logx = True, logy=True)

