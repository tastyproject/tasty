# -*- coding: utf-8 -*-

import os
import shutil
import os.path
from optparse import OptionParser, OptionGroup

import sys
import pkg_resources

import tasty
from tasty import state


def main():
    usage = "usage: %prog [options] path/to/protocol/directory/"
    parser = OptionParser(usage=usage, version="%%prog %s" % tasty.__version__)

    parser.add_option("-I", "--info",
                      action="store_true",
                      dest="info",
                      default=False,
                      help="show program information")

    std_opts = OptionGroup(parser, "protocol options")
    std_opts.add_option("-d", "--by_daemons_be_driven",
                        action="store_true",
                        dest="use_driver",
                        default=False,
                        help="create an instrumented protocol environment (good for protocol cost plots and "
                             "parametrized metrics)")
    parser.add_option_group(std_opts)
    options, args = parser.parse_args()

    if options.info:
        print state.info_text
        sys.exit(0)

    if len(args) != 1:
        parser.print_help()
        sys.exit(-2)
    path = args[0]
    if os.path.exists(path):
        print "Path already exists. Choose another one"
        sys.exit(1)

    if options.use_driver == True:
        status_text = "creating reference tasty protocol environment with benchmark support in '{0}'\n".format(path)
        env_dir = pkg_resources.resource_filename("tasty", "resources/tasty_init/driver_reference_protocol")
    else:
        status_text = "creating reference tasty protocol environment in '{0}'\n".format(path)
        env_dir = pkg_resources.resource_filename("tasty", "resources/tasty_init/reference_protocol")

    print status_text
    shutil.copytree(env_dir, path, ignore=lambda d, f: [".svn"])

    open(os.path.join(path, "__init__.py"), "w").write("\n")

    print "created following files in tasty protocol environment:"
    print '------------------------------------------------------'
    f = os.listdir(path)
    f.sort()
    for j in f:
        print j


if __name__ == '__main__':
    main()
