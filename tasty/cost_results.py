# -*- coding: utf-8 -*-

import operator
import re
import os
import os.path
import copy
from numbers import Number

from tasty.utils import prepare_resultdir, result_path
from collections import defaultdict
from datetime import datetime, timedelta

from tasty import state

__all__ = ["CostSystem", "convert_bytes", "to_ms", ]

ends_duration = re.compile(".*-duration$").match

def to_ms(td):
    return td.days * 86400000.0 + td.seconds * 1000.0 + td.microseconds / 1000.0

POW_2_10 = 1<<10
POW_2_20 = 1<<20
POW_2_30 = 1<<30
POW_2_40 = 1<<40

def convert_bytes(bytes):
    _bytes = float(bytes)
    if bytes >= POW_2_40:
        return _bytes / POW_2_40, "TiB"
    elif bytes >= POW_2_30:
        return _bytes / POW_2_30, "GiB"
    elif bytes >= POW_2_20:
        return _bytes / POW_2_20, "MiB"
    elif bytes >= POW_2_10:
        return _bytes / POW_2_10, "KiB"
    return bytes, "B"


class CostTemplate(defaultdict):
    def __init__(self, name="protocol_costs"):
        self.name = name
        defaultdict.__init__(self, int)

    def __call__(self, **args):
        for k, v in args.iteritems():
            self[k] += v

    #def __str__(self):
        #line = "    " + "-" * 64
        #text = ["", "    | %s |" % self.name.center(60), line]
        #if not super(CostTemplate, self).__len__():
            #text.append("    | %s |" % "None".center(60))
        #else:
            #text += ["    | %s| %s|" % (a.ljust(15), str(b).ljust(44)) for a, b in self.iteritems()]
        #text.append(line)
        #text.append("\n")
        #return "\n".join(text)

    def __iadd__(self, other):
        for k, v in other.iteritems():
            self[k] += v
        return self

    def __add__(self, other):
        c = copy.deepcopy(self)
        c.name = self.name
        for k, v in other.iteritems():
            c[k] += v
        return c

    def __mul__(self, other):
        c = copy.deepcopy(self)
        c.name = self.name
        if isinstance(other, int):
            for k, v in c.iteritems():
                c[k] *= other
        else:
            for k, v in other.iteritems():
                c[k] *= v
        return c


class StopWatch(object):
    """dead simple stop watch"""

    def __init__(self):
        self.calculated_time = timedelta()
        self.times = list()
        self.running = False

    def start(self):
        if not self.running:
            #self.times.append([datetime.now()])
            self.tmptime=datetime.now()
            self.running = True

    def stop(self):
        if self.running:
            #self.times[-1].append(datetime.now())
            self.calculated_time += datetime.now() - self.tmptime
            self.running = False

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def calculate(self):
        if self.calculated_time:
            return self.calculated_time
        if not self.times:
            return timedelta()
        if self.running:
            t = copy.deepcopy(self.times)
            t[-1].append(datetime.now())
            return reduce(operator.add, (b-a for a, b in t))
        self.calculated_time = reduce(operator.add, (b-a for a, b in self.times))
        return self.calculated_time

    def __getstate__(self):
        tmp = self.calculate()
        return tmp

    def __setstate__(self, state):
        self.calculated_time = state
        self.times = list()
        self.running = False

    def __str__(self):
        return str(self.calculate())

    def __repr__(self):
        return str(self.calculate())

class StopWatchGroup(list):
    """Manages a set of WatchClocks"""

    def start(self):
        for i in self:
            i.start()

    def stop(self):
        for i in self:
            i.stop()

    def toggle(self):
        for i in self:
            i.toggle()

    def __str__(self):
        return "\n".join(str(i.calculate()) for i in self)

class CostSystem(object):
    costs = None
    other_costs = None
    online_stopwatch_group = None

    @staticmethod
    def get_costs():
        if not CostSystem.costs:
            return CostSystem.create_costs()
        return CostSystem.costs

    @staticmethod
    def create_costs():
        costs = defaultdict(dict)
        tmp = costs["abstract"]
        tmp["analyze"] = {"accumulated" : CostTemplate("")}
        tmp["setup"] = {"accumulated" : CostTemplate("")}
        tmp["online"] = {"accumulated" : CostTemplate("")}
        tmp["ot"] = StopWatch()

        tmp = costs["abstract instantiated"]
        tmp["accumulated"] = CostTemplate("")

        tmp = costs["theoretical"]
        tmp["analyze"] = {"accumulated" : CostTemplate("")}
        tmp["setup"] = {"accumulated" : CostTemplate("")}
        tmp["online"] = {"accumulated" : CostTemplate("")}

        tmp = costs["real"]
        tmp["analyze"] = {"duration" : StopWatch(), "send" : 0, "recv" : 0, "accumulated" : CostTemplate()}
        tmp["setup"] = {"duration" : StopWatch(), "send" : 0, "recv" : 0, "accumulated" : CostTemplate()}
        tmp["online"] = {"duration" : StopWatch(), "send" : 0, "recv" : 0, "accumulated" : CostTemplate()}

        CostSystem.costs = costs
        CostSystem.online_stopwatch_group = StopWatchGroup()
        CostSystem.online_stopwatch_group.append(tmp["online"]["duration"])
        return costs

    @staticmethod
    def finalize_costs():
        c = CostSystem.costs
        c["abstract"]["accumulated"] = c["abstract"]["setup"]["accumulated"] + c["abstract"]["online"]["accumulated"]
        c["theoretical"]["accumulated"] = c["theoretical"]["setup"]["accumulated"] + c["theoretical"]["online"]["accumulated"]
        c["real"]["combined"] = {
            "accumulated" : c["real"]["setup"]["accumulated"] + c["real"]["online"]["accumulated"],
            "duration" : c["real"]["setup"]["duration"].calculate() + c["real"]["online"]["duration"].calculate(),
            "send" : c["real"]["setup"]["send"] + c["real"]["online"]["send"],
            "recv" : c["real"]["setup"]["recv"] + c["real"]["online"]["recv"]}

    @staticmethod
    def generate_cost_report():

        costs = CostSystem.costs
        other_costs = CostSystem.other_costs

        rss = costs["real"]["setup"]["send"]
        rsr = costs["real"]["setup"]["recv"]
        rs = costs["real"]["setup"]
        ors = other_costs["real"]["setup"]
        ro = costs["real"]["online"]
        oro = other_costs["real"]["online"]
        ros = costs["real"]["online"]["send"]
        ror = costs["real"]["online"]["recv"]
        dt_setup = costs["real"]["setup"]["duration"].calculate()
        dt_online = costs["real"]["online"]["duration"].calculate()
        dt_other_setup = costs["real"]["setup"]["duration"].calculate()
        dt_other_online = costs["real"]["online"]["duration"].calculate()

        result = [
            "**************",
            "Abstract Costs",
            "**************",
            "%d OTs" % costs["abstract"]["accumulated"].get("ot", 0),
            "",
            "Garbled Circuit:"]

        if "3" in costs["abstract"]["accumulated"]:
            result.append("    %d 3-input-gates" % costs["abstract"]["accumulated"]["3"])
        if "2_NONXOR" in costs["abstract"]["accumulated"]:
            result.append("    %d 2-input non-XOR gate" % costs["abstract"]["accumulated"]["2_NONXOR"])

        if "send garbled bits" in costs["abstract"]["accumulated"]:
            result.extend([
                "",
                "C->S:",
                "    %d garbled bits" % costs["abstract"]["accumulated"]["send garbled bits"]])
        elif "recv garbled bits" in other_costs["abstract"]["accumulated"]:
            result.extend([
                "",
                "C->S:",
                "    %d garbled bits" % other_costs["abstract"]["accumulated"]["recv garbled bits"]])

        if "recv garbled bits" in costs["abstract"]["accumulated"]:
            result.extend([
                "",
                "C<-S:",
                "    %d garbled bits" % costs["abstract"]["accumulated"]["recv garbled bits"]])
        elif "send garbled bits" in other_costs["abstract"]["accumulated"]:
            result.extend([
                "",
                "C<-S:",
                "    %d garbled bits" % other_costs["abstract"]["accumulated"]["send garbled bits"]])

        result.append("")
        result.append("")
        result.extend([
            "*****************",
            "Theoretical Costs",
            "*****************",
            "",
            "Setup Phase",
            "-----------",
            costs["theoretical"]["setup"]["accumulated"]["Send"] and "C->S: %s %s"%convert_bytes(costs["theoretical"]["setup"]["accumulated"]["Send"]) or False,
            other_costs["theoretical"]["setup"]["accumulated"]["Send"] and "C<-S: %s %s"%convert_bytes(other_costs["theoretical"]["setup"]["accumulated"]["Send"]) or False,
            "C:"])
        if "SHA256" in costs["theoretical"]["setup"]["accumulated"]:
            result.append("   %d SHA256-Hashes" % costs["theoretical"]["setup"]["accumulated"]["SHA256"])
        if "EC_MUL" in costs["theoretical"]["setup"]["accumulated"]:
            result.append("   %d EC Multiplications" % costs["theoretical"]["setup"]["accumulated"]["EC_Mul"])
        result.append("S:")
        if "SHA256" in other_costs["theoretical"]["setup"]["accumulated"]:
            result.append("   %d SHA256-Hashes" % other_costs["theoretical"]["setup"]["accumulated"]["SHA256"])
        if "EC_MUL" in other_costs["theoretical"]["setup"]["accumulated"]:
            result.append("   %d EC Multiplications" % other_costs["theoretical"]["setup"]["accumulated"]["EC_Mul"])
        result.append("")
        result.append("Online Phase")
        result.append("------------")
        if "Send" in costs["theoretical"]["online"]["accumulated"] and costs["theoretical"]["online"]["accumulated"] != 0:
            result.append("C->S: %s %s" % convert_bytes(costs["theoretical"]["online"]["accumulated"]["Send"]))
        if "Send" in other_costs["theoretical"]["online"]["accumulated"] and other_costs["theoretical"]["online"]["accumulated"]["Send"] != 0:
            result.append("C<-S: %s %s" % convert_bytes(other_costs["theoretical"]["online"]["accumulated"]["Send"]))
        result.append("C: ")
        if "SHA256" in costs["theoretical"]["online"]["accumulated"]:
            result.append("    %d SHA256 Hashes" % costs["theoretical"]["online"]["accumulated"]["SHA256"])
        if "Paillier_ENC" in costs["theoretical"]["online"]["accumulated"]:
            result.append("   %d Paillier Encryptions" % costs["theoretical"]["online"]["accumulated"]["Paillier_ENC"])
        if "Paillier_DEC" in costs["theoretical"]["online"]["accumulated"]:
            result.append("   %d Paillier Decryptions" % costs["theoretical"]["online"]["accumulated"]["Paillier_DEC"])
        result.append("S:")
        if "SHA256" in other_costs["theoretical"]["online"]["accumulated"]:
            result.append("    %d SHA256 Hashes" % other_costs["theoretical"]["online"]["accumulated"]["SHA256"])
        if "Paillier_ENC" in other_costs["theoretical"]["online"]["accumulated"]:
            result.append("   %d Paillier Encryptions" % other_costs["theoretical"]["online"]["accumulated"]["Paillier_ENC"])

        result.extend(["",
            "",
            "**********",
            "Real Costs",
            "**********"])
        if "send" in costs["real"]["analyze"] and costs["real"]["analyze"]["send"] != 0:
            result.append("C->S: %s %s tasty init overhead" % convert_bytes(costs["real"]["analyze"]["send"]))
        if "recv" in costs["real"]["analyze"] and costs["real"]["analyze"]["recv"] != 0:
            result.append("C<-S: %s %s tasty init overhead" % convert_bytes(costs["real"]["analyze"]["recv"]))
        result.append("")
        result.append("Analyzation Phase")
        result.append("-----------------")

        d = to_ms(costs["real"]["analyze"]["duration"].calculate())
        if d:
            result.append("C: %s ms"  % d)

        d = to_ms(other_costs["real"]["analyze"]["duration"].calculate())
        if d:
            result.append("S: %s ms"  % d)

        result.extend(["",
            "Setup Phase",
            "-----------",
            "C->S: %s %s" % convert_bytes(rss),
            "C<-S: %s %s" % convert_bytes(rsr),
            "C: %s ms" % to_ms(dt_setup),
            "S: %s ms" % to_ms(dt_other_setup),
            "Protocol run times:"
            ])
        for p, cur in (("C", rs), ("S", ors)):
            it = cur.keys()
            it.remove("duration")
            for i in it:
                if ends_duration(i):
                    result.append(" %s: %s %s ms"%(p, i, to_ms(cur[i].calculate())))

        result.extend([
            "",
            "Online Phase",
            "------------",
            "C->S: %s %s" % convert_bytes(ros),
            "C<-S: %s %s" % convert_bytes(ror),
            "S: %s ms" % to_ms(dt_online),
            "C: %s ms" % to_ms(dt_other_online),
            "Protocol run times:"
            ])
        for p, cur in (("C", ro), ("S", oro)):
            it = cur.keys()
            it.remove("duration")
            for i in it:
                if ends_duration(i):
                    result.append(" %s: %s %s ms"%(p, i, to_ms(cur[i].calculate())))

        result.extend([
            "",
            "--------------------------------",
            "Total (Analyzation+Setup+Online)",
            "--------------------------------",
            "C->S: %s %s" % convert_bytes(costs["real"]["combined"]["send"]),
            "C<-S: %s %s" % convert_bytes(costs["real"]["combined"]["recv"]),

            "C:",
            "    %d ms" % to_ms(costs["real"]["combined"]["duration"]),

            "S:",
            "    %d ms" % to_ms(other_costs["real"]["combined"]["duration"])])
        t = "\n".join(filter(lambda x:x and x or False, result))
        open(result_path("costs.txt"), "w").write(t)
        return t

def extract(item):
    if isinstance(item, StopWatch):
        return to_ms(item.calculate())
    if isinstance(item, timedelta):
        to_ms(item)
    else:
        return item

def extract_costs(cost_obj, *names, **kwargs):
    """list of cost data sets which should be returned

    usage:
        a name consists of following elements separated with '>':
        party>cost_type>[phase]>value

        'party' must be one of 'client' | 'server'
        'cost_type' must be one out of 'real' | 'abstract' | 'theoretical'
        'phase' is optional, but when you provide it, it must be one out of 'analyze' | 'setup' | 'online' | 'combined',
        'value' must be one out of 'send', 'recv', 'duration', ...

        examples::
            x_values = xrange(10) # the x values used for creating cost data
            y_values = self.extract_costs("client>real>online>send", "client>real>setup>send", "client>real>combined>send")
            tasty_plot("my beautiful tasty graph", "x_axis_name", "y_axis_name", x_value_list, y_values)
    """


    def get_elements(splitted, key, elem):
        if len(splitted) == 0:
            e = extract(elem)
            if not isinstance(e, Number):
                return []
            return [(key, extract(elem))]
        match = splitted.pop(0)
        try:
            return map(lambda x: ("%s %s"%(key, x[0]), x[1]),
                       reduce(lambda y, x: x + y,
                              map(lambda x: get_elements(splitted, x, elem[x]),
                                  filter(match, elem.keys())),
                              []))
        except AttributeError:
            return []

    cost_types = ["real", "abstract", "theoretical"]
    phase_types = ['analyze', 'setup', 'online', 'combined']

    data_sets = list()
    for i in names:
        if isinstance(i, str):
            splitted = i.split(">")
            label = None
        if isinstance(i, list) or isinstance(i, tuple):
            splitted = i[1].split(">")
            label = i[0]

        party_name = splitted.pop(0)

        if party_name == "client":
            costs = cost_obj[0]
        elif party_name == "server":
            costs = cost_obj[1]
        else:
            raise ValueError("first parameter must be 'client' or 'server'")

        matches = map(lambda x: re.compile("^%s$"%x).match, splitted)

        data = [get_elements(copy.deepcopy(matches), party_name, c) for c in costs]
        ddata = defaultdict(list)
        for i in data:
            for j in i:
                ddata[j[0]].append(j[1])

        def set_label(l,default):
            if default:
                return default
            else:
                return l

        fdata = [[set_label(x,label), ddata[x]] for x in ddata.keys()]

        if "scale" in kwargs and kwargs["scale"]:
            for x in fdata:
                _max = max(x[1])
                if _max:
                    x[1] = [float(j) / _max for j in x[1]]
                x[0] = "%s (MAX: %r)" % (x[0], _max)
        data_sets.extend(fdata)
    return data_sets
