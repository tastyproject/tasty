# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser
from optparse import OptionParser, OptionGroup
import os

from cPickle import load
from datetime import timedelta
import sys

import tasty
from tasty.cost_results import StopWatch
from tasty import state


def start(config=True):
    """The 'main' function of tasty"""

    usage = """
    %prog <post_processing_script.py> <cost.bin> [<other_cost.bin> ...]
    %prog -i <cost.bin>"""

    parser = g_parser = OptionParser(usage=usage, version="%%prog %s" % tasty.__version__)

    parser.add_option("-I", "--info",
                      action="store_true",
                      dest="info",
                      default=False,
                      help="show program information")

    net_opts = OptionGroup(parser, "general options")
    net_opts.add_option("-i", "--inspect-costs",
                        action="store_true",
                        dest="inspect",
                        default=False,
                        help="show the cost hierarchy and keys of a given cost objs")

    configuration, args = parser.parse_args()

    if configuration.info:
        print state.info_text
        sys.exit(0)

    # checking options given
    if configuration.inspect:
        if len(args) > 1:
            sys.log.error("Please only specify one cost obj to inspect")
            sys.exit(1)

        cost_obj = load(open(args[0], "rb"))

        def explain_type(t):
            if isinstance(t, int):
                return "integer"
            if isinstance(t, StopWatch) or isinstance(t, timedelta):
                return "Time in ms"
            else:
                raise Exception("unexplained: %s", type(t))

        def format(item, indend=0, prefix=""):
            for key, value in item.iteritems():
                full_key = "%s>%s" % (prefix, key)
                if isinstance(value, dict):
                    if value:
                        if not indend:
                            print
                            print full_key + ":"
                        else:
                            print "%s %s:" % (" " * indend, full_key)
                        format(value, indend + 2, full_key)
                elif value:
                    print "%s %s (%s)" % (" " * indend, full_key, explain_type(value))

        print "showing the cost hierarchy:"
        print "number of cost sets: %d" % len(cost_obj[0]),
        print
        config = cost_obj[2]
        try:
            size_1 = max(len(str(v)) for v in config.__dict__.iterkeys())
            size_2 = max(len(str(v)) for v in config.__dict__.itervalues())
            line = "-" * (size_1 + size_2 + 3)
            print "\nconfiguration values"
            print "-" * 79
            for k, v in config.__dict__.iteritems():
                print "%s | %s" % (k.ljust(size_1), v)
            print "-" * 79
            print
            print "%s[0]" % args[0]
            format(cost_obj[0][0], prefix="client")
            print
            print "-" * 79
            print
            print "%s[1]" % args[0]
        except Exception:
            pass
        format(cost_obj[1][0], prefix="server")
    else:
        try:
            directory, mod_name = os.path.split(args.pop(0))
            # preparing analyze script
            mod_name = os.path.splitext(mod_name)[0]
        except Exception, e:
            parser.print_help()
            sys.exit(1)

        old_path = sys.path
        sys.path = [directory] + sys.path
        process_mod = __import__(mod_name, globals(), locals(), [])
        sys.path = old_path

        cost_objs = [load(open(i, "rb")) for i in args]
        process_mod.process_costs(cost_objs)


if __name__ == '__main__':
    start()
