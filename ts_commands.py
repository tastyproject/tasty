# -*- coding: utf-8 -*-


import os
import sys
from distutils.cmd import Command
import subprocess

commands = dict()

__all__ = ["commands", ]

try:
    from epydoc import cli
except ImportError:
    print 'epydoc not installed, skipping API documentation target.'
else:
    class apidoc(Command):
        description = 'Builds the api documentation'
        user_options = [
            ('format=', 'f',
                "Output format: html, pdf, ps, dvi, latex. Default = html"),
            ('check', None, "check completeness of docs"),
            ('verbose', "v", "verbose mode")]
        boolean_options = ["check", "verbose"]
        def __init__(self, dist):
            Command.__init__(self, dist)
            self.args = [
                '--no-sourcecode',
                '--no-imports',
                '--no-frames',
                '--dotpath=%s' % '/usr/bin/dot',
                '--graph=%s' % 'all',
                '-n', 'Tasty - API documentation',
                '--inheritance=%s' % 'included',
                '--docformat=%s' % 'epytext',
                '--output=%s' % os.path.join("docs", "api"),
                'tasty']
        def initialize_options(self):
            self.check = False
            self.format = 'html'
            self.verbose = False
        def finalize_options(self):
            if self.format not in ["html", "pdf", "ps", "dvi", "latex"]:
                self.format = 'html'
                print "Invalid output format, reset to html."
            self.args.append("--%s" % self.format)
            if self.check:
                self.args.append('--check')
            if self.verbose:
                self.args.append("-v")
        def run(self):
            old_argv = sys.argv[1:]
            sys.argv[1:] = self.args
            try:
                cli.cli()
            except:
                pass
            finally:
                sys.argv[1:] = old_argv
    commands.update({'apidoc': apidoc})


#try:
    #from pylint import lint
#except ImportError:
    #print 'pylint not installed, skipping code analyser.'
#else:
    #class check(Command):
        #description = 'checks coding style conventions'
        #user_options = [("error", "e", "shows only errors"),]
        #boolean_options = ["error",]

        #def initialize_options(self):
            #self.error = False
            #self.args = ['--rcfile=pylint.rc', 'tasty']

        #def finalize_options(self):
            #if self.error:
                #self.args.append("-e")

        #def run(self):
            #try:
                #lint.Run(self.args)
            #except:
                #pass
    #commands['check'] = check


#try:
    #from figleaf.annotate_html import main as figleaf_gen
#except ImportError:
    #print 'figleaf not installed, no functional tests for you.'
#else:
    #class cov(Command):
        #description = 'code coverage analysis with detailed html report'
        #user_options = []
        #boolean_options = []

        #def initialize_options(self):
            #pass

        #def finalize_options(self):
            #pass

        #def run(self):
            ## Ugly, but neccessary: when installed in development mode and
            ## calling figleaf.main() directly, local package path of tasty
            ## is missing in sys.path.
            #p = subprocess.Popen(
                #"figleaf " + os.path.join("tasty", "tests", "__init__.py"),
                #shell=True)
            #sts = os.waitpid(p.pid, 0)

            #old_argv = sys.argv[1:]
            #sys.argv[1:] = ["-x", "coverage_exclude.txt", "-d",
                #"coverage_report"]
            #try:
                #figleaf_gen()
            #except:
                #pass
            #finally:
                #sys.argv[1:] = old_argv
                #os.remove(".figleaf")
    #commands['cov'] = cov

#class run_perf(Command):
    #description = 'runs performance tests'
    #user_options = [("iterations=", "i", "number of iterations"),
        #("show", "s", "shows each graph and waits for input to proceed")]
    #boolean_options = ["show"]

    #def initialize_options(self):
        #self.iterations = 1
        #self.show = False

    #def finalize_options(self):
        #self.iterations = int(self.iterations)

    #def run(self):
        #try:
            #perf.run(self.iterations, self.show)
        #except:
            #pass
#commands['perf'] = run_perf
