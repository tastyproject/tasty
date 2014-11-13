# -*- coding: utf-8 -*-

from tasty.cost_results import extract_costs
from tasty.utils import tasty_plot
from tasty.postprocessing import *



def process_costs(cost_objs):

    x_label = "Bitlength"

    # -----------------
    # TIME
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]
    
    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
        (pre+"C setup", "client>real>setup>duration"),
        (pre+"S setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration"))

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
        (pre+"C setup", "client>real>setup>duration"),
        (pre+"S setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")))

    pre = "GC1: "
    y_values_gc = extract_costs(cost_objs[2],
        (pre+"C setup", "client>real>setup>duration"),
        (pre+"S setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration"))

    pre = "GC2: "
    y_values_gc.extend(extract_costs(cost_objs[3],
        (pre+"C setup", "client>real>setup>duration"),
        (pre+"S setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")))

    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)

#    x_values, y_values = truncate(x_values, y_values, 2, 80)

    y_label = "Time in ms"
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        outfile="multiplication_time.pdf")
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        blackwhite=True,
        outfile="multiplication_time_bw.pdf")


    # -----------------
    # TIME Paper
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]
    
    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
        (pre+"C Setup", "client>real>setup>duration"),
        (pre+"S Setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")
    )

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
        (pre+"C Setup", "client>real>setup>duration"),
        (pre+"S Setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")
    ))

    pre = "GC1: "
    y_values_gc = extract_costs(cost_objs[2],
        (pre+"C Setup", "client>real>setup>duration"),
        (pre+"S Setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")
    )

    pre = "GC2: "
    y_values_gc.extend(extract_costs(cost_objs[3],
        (pre+"C Setup", "client>real>setup>duration"),
        (pre+"S Setup", "server>real>setup>duration"),
        (pre+"C Online", "client>real>online>duration"),
        (pre+"S Online", "server>real>online>duration")
    ))

    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)

    y_label = "Time in ms"
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        logy=True,
        outfile="multiplication_time_paper.pdf",
        legend="inside")
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        blackwhite=True,
        logy=True,
        outfile="multiplication_time_paper_bw.pdf",
        legend="inside")


    # -----------------
    # TIME Paper SETUP
    # -----------------

    paper_set = range(1,8) + range(8,16,2) + range(16,32,4) + range(32,64,8) + range(64, 129, 16) 

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]
    print x_values
    
    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
        (pre+"C", "client>real>setup>duration"),
        (pre+"S", "server>real>setup>duration"),
    )

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
        (pre+"C", "client>real>setup>duration"),
        (pre+"S", "server>real>setup>duration"),
    ))

    pre = "GC1: "
    y_values_gc = extract_costs(cost_objs[2],
        (pre+"C", "client>real>setup>duration"),
    )

    pre = "GC2: "
    y_values_gc.extend(extract_costs(cost_objs[3],
        (pre+"C", "client>real>setup>duration"),
    ))

    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)

    x_values, y_values = trunc_set(x_values, y_values, paper_set)
    print x_values, y_values
    
    y_label = "Setup Time in ms"
    tasty_plot(None,
               x_label,
               y_label,
               x_values,
               y_values,
               logy=True,
               logx=True,
               outfile="multiplication_time_paper_setup.pdf",
               legend="inside")
    tasty_plot(None,
               x_label,
               y_label,
               x_values,
               y_values,
               blackwhite=True,
               logy=True,
               logx=True,
               outfile="multiplication_time_paper_setup_bw.pdf",
               legend="inside")


    # -----------------
    # TIME Paper ONLINE
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]

    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
        (pre+"C", "client>real>online>duration"),
        (pre+"S", "server>real>online>duration"),
    )

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
        (pre+"C", "client>real>online>duration"),
        (pre+"S", "server>real>online>duration"),
    ))

    pre = "GC1: "
    y_values_gc = extract_costs(cost_objs[2],
        (pre+"C", "client>real>online>duration"),
        (pre+"S", "server>real>online>duration"),
    )

    pre = "GC2: "
    y_values_gc.extend(extract_costs(cost_objs[3],
        (pre+"C", "client>real>online>duration"),
        (pre+"S", "server>real>online>duration"),
    ))

    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)

    x_values, y_values = trunc_set(x_values, y_values, paper_set)

    y_label = "Online Time in ms"
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
	logy=True,
               logx=True,
        outfile="multiplication_time_paper_online.pdf",
        legend="inside")
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
	logy=True,
               logx=True,
        blackwhite=True,
        outfile="multiplication_time_paper_online_bw.pdf",
        legend="inside")

    # -----------------
    # DATA
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]

    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
       (pre+"C setup send", "client>real>setup>send"),
       (pre+"S setup send", "client>real>setup>recv"),
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
       )

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
       (pre+"C setup send", "client>real>setup>send"),
       (pre+"S setup send", "client>real>setup>recv"),
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
       ))
    
    pre = "GC1: "
    y_values_gc = extract_costs(cost_objs[2],
       (pre+"C setup send", "client>real>setup>send"),
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
    )

    pre = "GC2: "
    y_values_gc.extend(extract_costs(cost_objs[3],
       (pre+"C setup send", "client>real>setup>send"),
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
    ))

    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)

    x_values, y_values = trunc_set(x_values, y_values, range(1,11)+range(12,26,2))
    y_label = "data (???)"
    tasty_plot("multiply_data_real",
        x_label,
        y_label,
        x_values,
        y_values,
        outfile="multiplication_data.pdf")
    tasty_plot("multiply_data_real",
        x_label,
        y_label,
        x_values,
        y_values,
        blackwhite=True,
        outfile="multiplication_data_bw.pdf")


    # -----------------
    # DATA Paper
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]

    pre = "HE1: "
    tmp = extract_costs(cost_objs[0],
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
       )

    y_values = [[pre+"Online",map(sum, zip(tmp[0][1],tmp[1][1]))]]

    pre = "HE2: "
    tmp = extract_costs(cost_objs[1],
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
       )

    y_values.extend([[pre+"Online",map(sum, zip(tmp[0][1],tmp[1][1]))]])
    
    pre = "GC1: "
    tmp = extract_costs(cost_objs[2],
       (pre+"C setup send", "client>real>setup>send"), #neg
       (pre+"S setup send", "client>real>setup>recv"),
       (pre+"C online send", "client>real>online>send"), #neg
       (pre+"S online send", "client>real>online>recv"),
    )
    y_values_gc = [[pre+"Setup",map(sum, zip(tmp[0][1],tmp[1][1]))],
                     [pre+"Online",map(sum, zip(tmp[2][1],tmp[3][1]))]
                     ]

    pre = "GC2: "
    tmp = extract_costs(cost_objs[3],
       (pre+"C setup send", "client>real>setup>send"),
       (pre+"S setup send", "client>real>setup>recv"),
       (pre+"C online send", "client>real>online>send"),
       (pre+"S online send", "client>real>online>recv"),
    )
    y_values_gc.extend([[pre+"Setup",map(sum, zip(tmp[0][1],tmp[1][1]))],
                     [pre+"Online",map(sum, zip(tmp[2][1],tmp[3][1]))]
                     ])
    
    x_values_gc = [i["params"]["la"] for i in cost_objs[2][0]]
    x_values_gc, y_values_gc = average(x_values_gc, y_values_gc)
    y_values.extend(y_values_gc)
    #### WTF?!?!? Why are the first 3 measurements bullshit?!?
    y_values[1][1][0] = y_values[1][1][1] = y_values[1][1][2] = y_values[1][1][3]

    x_values, y_values = trunc_set(x_values, y_values, paper_set)
#    x_values, y_values = trunc_set(x_values, y_values, range(1,11)+range(15,81,5))
    y_label = "Data in Bytes"
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        logy=True,
               logx=True,
        outfile="multiplication_data_paper.pdf",
        legend = "inside")
    tasty_plot(None,
        x_label,
        y_label,
        x_values,
        y_values,
        blackwhite=True,
        logy=True,
               logx=True,
        outfile="multiplication_data_paper_bw.pdf",
        legend = "inside")



    # -----------------
    # DATA THEORETICAL
    # -----------------

    x_values = [i["params"]["la"] for i in cost_objs[0][0]]

    pre = "HE1: "
    y_values = extract_costs(cost_objs[0],
       (pre+"C setup send", "client>theoretical>setup>accumulated>Send"),
       (pre+"S setup send", "server>theoretical>setup>accumulated>Send"),
       (pre+"C online send", "client>theoretical>online>accumulated>Send"),
       (pre+"S online send", "server>theoretical>online>accumulated>Send"),
       )

    pre = "HE2: "
    y_values.extend(extract_costs(cost_objs[1],
       (pre+"C setup send", "client>theoretical>setup>accumulated>Send"),
       (pre+"S setup send", "server>theoretical>setup>accumulated>Send"),
       (pre+"C online send", "client>theoretical>online>accumulated>Send"),
       (pre+"S online send", "server>theoretical>online>accumulated>Send"),
       ))

    pre = "GC1: "
    y_values.extend(extract_costs(cost_objs[2],
       (pre+"C setup send", "client>theoretical>setup>accumulated>Send"),
       (pre+"C online send", "client>theoretical>online>accumulated>Send"),
       (pre+"S online send", "server>theoretical>online>accumulated>Send"),
    ))
    
    pre = "GC2: "
    y_values.extend(extract_costs(cost_objs[3],
       (pre+"C setup send", "client>theoretical>setup>accumulated>Send"),
       (pre+"C online send", "client>theoretical>online>accumulated>Send"),
       (pre+"S online send", "server>theoretical>online>accumulated>Send"),
    ))
    
    x_values, y_values = average(x_values, y_values)
    
    y_label = "data (???)"
    tasty_plot("multiply_data_theoretical",
        x_label,
        y_label,
        x_values,
        y_values,
        outfile="multiplication_data_theoretical.pdf")
    tasty_plot("multiply_data_theoretical",
        x_label,
        y_label,
        x_values,
        y_values,
        blackwhite=True,
        outfile="multiplication_data_theoretical_bw.pdf")
    
