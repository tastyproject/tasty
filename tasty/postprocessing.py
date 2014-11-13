# -*- coding: utf-8 -*-
""" utilities for postprocessing """

from itertools import ifilter
import copy

def normalize(li):
    """ Normalize all graphs in li """
    for l in li:
        m = float(max(l[1]))
        l[0] += " (max: %d)" % m
        if m == 0:
            continue
        else:
            l[1]=map(lambda x: x/m, l[1])
    return li


def average(xvalues, list_of_yvalues):
    list_of_yvalues = copy.deepcopy(list_of_yvalues)
    newxvalues = []
    xindexes = {}
    for x in xvalues:
        if x not in newxvalues:
            newxvalues.append(x)
            xindexes[x] = filter(lambda i: xvalues[i] == x, xrange(len(xvalues)))


    for l in list_of_yvalues:
        newl1 = [0 for i in newxvalues]
        for i, x in enumerate(newxvalues):
            newl1[i] = sum(map(lambda j: int(j in xindexes[x]) and l[1][j], xrange(len(l[1]))))/len(xindexes[x])

        l[1] = newl1

    return newxvalues, list_of_yvalues


def get_yvalues(yvals, name):
    for i in yvals:
        if i[0] == name:
            return i[1]

def fold_values(yvals, names, newname, operation):
    yval = map(lambda x: get_yvalues(yvals, x), names)

    return [newname, map(operation, zip(*yval))]
    

def substract_values(yvals, name1, name2, newname=None):
    if not newname:
        newname = "(%s) - (%s)"%(name1,name2)

    return fold_values(yvals, name1, name2, newname, lambda x: x[0] - y[1])

def add_values(yvals, names, newname):
    if not newname:
        newname = "sum of %s"%name[0]
        for i in name[1:]:
            newname += " and %s"%i
    return fold_values(yvals, names, newname, sum)


def truncate(xvals, yvals, fr, to):
    yvals = copy.deepcopy(yvals)
    newxvals = filter(lambda x: x >= fr and x <= to, xvals)
    for yval in yvals:
        yval[1] = filter(lambda x: x != False, map(lambda x: xvals[x] >= fr and xvals[x] <= to and yval[1][x], xrange(len(xvals))))
    return newxvals, yvals
    

def trunc_set(xvals, yvals, x_set):
    yvals = copy.deepcopy(yvals)
    newxvals = filter(lambda x: x in x_set, xvals)
    for yval in yvals:
        yval[1] = filter(lambda x: type(x) != type(False), map(lambda x: xvals[x] in x_set and yval[1][x], xrange(len(xvals))))
    return newxvals, yvals
            
