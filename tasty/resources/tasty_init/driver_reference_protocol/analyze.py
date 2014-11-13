# -*- coding: utf-8 -*-

from tasty.cost_results import extract_costs
from tasty.utils import tasty_plot
from tasty.postprocessing import *

def process_costs(cost_objs):
    """ Process measured cost objects """
    x_values = [i["params"]["L"] for i in cost_objs[0][0]]

    # select intended costs
    y_values = extract_costs(cost_objs[0],
        ("C Online", "client>real>online>duration"), # C's online time
        ("S Online", "server>real>online>duration")) # S's online time

    x_label = "bitlength" # label of x axis
    y_label = "Time in ms" # label of y axis
    graph_name = "Times for example" # name of figure

    # draw graph into PDF file
    tasty_plot(graph_name, x_label, y_label, x_values, y_values, outfile="example_graph.pdf")
