# -*- coding: utf-8 -*-

"""Tasty utility functions"""

import logging
import os
import os.path
import random
import math
import sys
import warnings
from collections import deque
from gmpy import mpz
from tasty import exc
from itertools import takewhile, count
from datetime import datetime
from logging import handlers

import Gnuplot


from tasty import state

__all__ = [
    "cpu_load",
    "ByteCounter",
    "prepare_resultdir",
    "get_random",
    "tasty_plot",
    "bit2byte",
    "rand",
    "bitlength",
    "chunks",
    "protocol_file",
    "protocol_path",
    "tasty_file",
    "tasty_path",
    "result_file",
    "result_path",
    "mdeque",
    "comp22int",
    "int2comp2",
    "get_randomm"]


if not state.log:
    state.log = log = logging.Logger("LoginManager")
    log.setLevel(logging.ERROR)
    state.cli_formatter = cli_formatter = logging.Formatter(state.color + state.party_name + " %(message)s")
    state.stream_handler = stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(cli_formatter)
    log.addHandler(stream_handler)
    warnings.simplefilter("default", exc.UserWarningOnce)
    warnings.simplefilter("always", exc.UserWarningRepeated)


def init_log():
    """initializes the log"""
    prepare_resultdir()
    file_handler = handlers.RotatingFileHandler(state.config.log_file,
        maxBytes=800000, backupCount=9)
    file_formatter = logging.Formatter(
        state.party_name +
        ":: %s%(levelname)s:%(created)s:%(module)s.%(funcName)s: %(message)s")
    file_handler.setFormatter(file_formatter)
    log.addHandler(file_handler)

    state.cli_formatter = cli_formatter = logging.Formatter(state.color + state.party_name + ": %(message)s" + state.color_reset)
    state.stream_handler.setFormatter(cli_formatter)


_mpz = type(mpz(0))


class mdeque(deque):
    def pop(self, arg=None):
        if arg is None:
            return super(mdeque, self).pop()
        else:
            return tuple(reversed(super(mdeque,self).pop() for x in xrange(arg)))

    def popleft(self, arg=None):
        if arg is None:
            return super(mdeque, self).popleft()
        else:
            return tuple(super(mdeque,self).pop() for x in xrange(arg))



def result_path(name):
    return os.path.join(state.config.protocol_dir, "results", name)


def result_file(name):
    warnings.warn("please use 'result_path()' not 'result_file()'", DeprecationWarning)
    return result_path(name)


def chunks(liste, count):
    for i in xrange(0, len(liste), count):
        yield liste[i:i + count]



def protocol_path(filename):
    return os.path.join(state.config.protocol_dir, filename)


def protocol_file(filename):
    warnings.warn("please use 'protocol_path()' not 'protocol_file()'", DeprecationWarning)
    return protocol_path(filename)


def tasty_path(filename):
    return os.path.join(state.tasty_root, filename)


def tasty_file(filename):
    warnings.warn("please use 'tasty_path()' not 'tasty_file()'", DeprecationWarning)
    return tasty_path(filename)


def prepare_resultdir():
    """creates the protocol result directory if missing"""
    try:
        os.makedirs(os.path.join(state.config.protocol_dir, "results"))
    except OSError, e:
        if e.errno == 17:
            return
        raise


def tasty_plot(title, x_label, y_label, x_axis, y_arrays, scale=False, output_format="PDF", outfile=None, logx=False, logy=False, legend="outside", blackwhite=False, missing=None):
    """draws a graph"""

    import numpy
    g = Gnuplot.Gnuplot()
    g("set style data linespoints")


    if legend=="outside":
        g("set key outside bottom spacing 0.6")
    elif legend=="inside":
        g("set key inside left top spacing 1")
    else:
        raise ValueError("expected legend = \"inside\" or \"outside\"")

    if scale:
        g("set yrange [0:1]")
    else:
        g.ylabel(y_label)
    if logx:
        g('set format x "2^{%L}"')
        g("set logscale x 2")
    if logy:
        g('set format y "2^{%L}"')
        g("set logscale y")
    if missing:
        g("set datafile missing \"%s\""%missing)

    dt = datetime.now()
    dt_str = dt.strftime("%Y%m%d")
    if output_format=="PDF":
        if blackwhite:
            g("set term pdf monochrome dashed")
        else:
            g("set term pdf color dashed")

            g('set style line 1 lt 1 lw 1 linecolor rgb "dark-blue"')
            g('set style line 2 lt 2 lw 1 linecolor rgb "black"')
            g('set style line 3 lt 3 lw 1 linecolor rgb "dark-magenta"')
            g('set style line 4 lt 4 lw 1 linecolor rgb "dark-green"')
            g('set style line 5 lt 5 lw 1 linecolor rgb "brown"')
            g('set style line 6 lt 6 lw 1 linecolor rgb "grey20"')
            g('set style line 7 lt 7 lw 1 linecolor rgb "dark-red"')
            g('set style line 8 lt 8 lw 1 linecolor rgb "black"')
            g('set style line 9 lt 9 lw 1 linecolor rgb "blue"')
            g('set style increment user')


        if outfile:
            file_name = outfile
        else:
            file_name = result_dir("%s-%s.pdf" % (title, dt_str))
        g("set output '%s'" % file_name)
    elif output_format=="PS":
        if blackwhite:
            g('set term postscript eps monochrome dashed font "Helvetica,8"')
        else:
            g('set term postscript eps color font "Helvetica,8"')
        if outfile:
            file_name = outfile
        else:
            file_name = result_dir("%s-%s.ps" % (title, dt_str))
        g("set output '%s'" % file_name)
    elif output_format=="X":
        pass
    else:
        raise ValueError("output format must be X | PS | PDF.")

    if title:
        g.title(title)
    g.xlabel(x_label)
    x_axis = numpy.array(x_axis)
    r = list()
    for label, data in y_arrays:
        r.append(Gnuplot.Data(zip(x_axis, data), title=label))
    g.plot(*r)
    if not state.config and output_format=="X": # plot to X when invoked from Python
        raw_input('Please press return to continue...\n')




class ByteCounter(object):
    """Counts bytes of objects you made me inspect. Displays result on delete
    """

    def __init__(self, name, formatstr="%c"):
        """Std Constructor,

        @type name: str
        @param name: see time.strftime in python docs

        @type format: str
        @param format: see time.strftime in python docs
        """

        self.name = name
        self.fmt = formatstr
        self.byte_count = 0

    def __call__(self, data):
        self.byte_count += data

    def get_and_reset(self):
        """returns the actual counted number of bytes and resets the counter"""
        a = self.byte_count
        self.byte_count = 0
        return a

    def __str__(self):
        return "ByteCounter '%s': %d bytes" % (self.name,
            self.byte_count)


if sys.platform == "linux2":
    import subprocess
    def cpu_count():
        """counts the number of cpus"""
        return int(subprocess.Popen(
            "cat /proc/cpuinfo | grep \"^vendor_id\" | wc -l",
            shell=True, stdout=subprocess.PIPE).communicate()[0][:-1])
    def cpu_load():
        """linux version of getting cpu load"""
        l = float(subprocess.Popen(
            "ps -eao \'pcpu\' | awk \'{a+=$1} END {print a}\' | sed 's/,/./'",
            shell=True, stdout=subprocess.PIPE).communicate()[0][:-1])
        return l / cpu_count()
elif sys.platform == "win32":
    warnings.warn("Not yet tested!")
    import wmi
    def cpu_load():
        """counts the number of cpus"""

        myWMI = wmi.WMI()
        loads = [cpu.LoadPercentage for cpu in myWMI.Win32_Processor()]
        a = 0
        for load in loads:
            a += 1
            return "Proc " + str(a) + ": \t" + str(load) + " percent"
elif sys.platform == "macos" or sys.platform == "darwin":
    import subprocess
    def cpu_count():
        """counts the number of cpus"""
        return int(subprocess.Popen(
            "hwprefs cpu_count",
            shell=True, stdout=subprocess.PIPE).communicate()[0][:-1])
    def cpu_load():
        """linux version of getting cpu load"""
        l = float(subprocess.Popen(
            "ps -eao \'pcpu\' | awk \'{a+=$1} END {print a}\' | sed 's/,/./'",
            shell=True, stdout=subprocess.PIPE).communicate()[0][:-1])
        return l / cpu_count()
else:
    raise NotImplementedError("No cpu_load procedure for your platform/OS.")

rand = random.Random(random.randint(0, 2 ** 64 - 1))
def get_random(fr, to, num = 1):
    """Generator provides random integers"""
    for x in xrange(num):
        yield rand.randint(fr, to)

def get_randomm(fr, to, num = 1):
    """Generator provides random integers"""
    for x in xrange(num):
        yield mpz(rand.randint(fr, to))


def bit2byte(i):
    """
    Convert i in bits into i in bytes (8 bit = 1 byte, 9 bit = 2 byte, 10bit = 2byte, ...)
    """
    # for i = k*8+[1..7], i//8 would be k which is to small, therefor
    # we need i//8 + 1 (to get k+1). However
    # if i = k*8, the result would be k+1 which is
    # to big in that case, therefore (i - 1)//8 + 1

    return ((i-1)//8)+1


def int2comp2(value, bitlen):
    """ Convert bitlen-bit integer value into 2-complement
    """
    if value >= 0:
        return value
    else:
        return (mpz(1) << bitlen ) + value

def comp22int(val, bitlen):
    """ Convert bitlen-bit value from 2-complement into integer
    """
    assert type(val) == _mpz, "value must be an mpz"
    if val.getbit(bitlen - 1) == 0:
        return val
    else:
        return - ((mpz(1) << bitlen) - val)

def bitlength(v):
    """ Determine number of bits required to represent value v
    """
    if isinstance(v, _mpz):
        bitlen = v.bit_length()
    else:
        bitlen = mpz(v).bit_length()
    if v >= 0:
        return bitlen
    else:
        return bitlen + 1



def nogen(val):
    try:
        val[0]
        return val
    except TypeError:
        return tuple(val)


# new version is faster
#def value2bits(val, bitlen):
    #""" Convert value into list of bits """
    #bits = [None for i in xrange(bitlen)]
    #tval = val
    #for i in xrange(bitlen):
        #bits[i] = val & 0x1
        #val >>= 1
    #assert val == 0, "Input too large: %d has bitlen %d, %d expected (%d remaining)"%(tval, bitlength(tval), bitlen, val)
    #return bits


def value2bits(val, bitlen):
    assert type(val) == _mpz, "must be an mpz"
    assert val.bit_length() <= bitlen, "Input too large: %d has bitlen %d, %d expected (%d remaining)"%(val, val.bit_length(), bitlen, val >> bitlen)
    getbit = val.getbit
    return [mpz(getbit(i)) for i in xrange(bitlen)]



def bits2value(bits):
    if __debug__:
        bits = nogen(bits)
        assert all(map(lambda x: x == 0 or x == 1, bits)), "you must specify an iterable containing only 0 or 1"
    val = mpz(0)
    try:
        for b in reversed(nogen(bits)):
            val <<= 1
            val |= b
    except TypeError:
        print bits
        raise
    return val

def str2mpz(string):
    return mpz(string, 256)


def tastyrange(start, stop, step=1):
    return takewhile(lambda x: x<stop, (start+i*step for i in count()))


def clean_tmpfiles():
    for i in (
        "protocol_final.py",
        "protocol_final.pyc",
        "protocol_final.pyo",
        "protocol_setup_client.py",
        "protocol_setup_client.pyc",
        "protocol_setup_client.pyo",
        "protocol_setup_server.py",
        "protocol_setup_server.pyc",
        "protocol_setup_server.pyo",
        "protocol_online_client.py",
        "protocol_online_client.pyc"
        "protocol_online_client.pyo"
        "protocol_online_server.py",
        "protocol_online_server.pyc",
        "protocol_online_server.pyo"):
        try:
            os.remove(protocol_path(i))
        except Exception, e:
            pass
