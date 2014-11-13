# -*- coding: utf-8 -*-

from copy import copy, deepcopy
from tasty import types
from tasty import state
from tasty.tastyc.analyzation import register_class_for_analyzation

class getPolyCoefficients(types.TastyFunction):
    def __call__(self, val=tuple()):
        """
        @ŧype roots: ModularVec
        @param roots: is expected to be a list/tuple of roots of the polynomial.

        getPolyCoefficients computes the coefficients a_i of the polynomial p(x)= sum_{i=0}^n{a_i * x^i}
        with the given roots.
        So what we want to do is simplify p(x) = (x-roots[0]) * (x-roots[1]) * ... * (x-roots[n])
                                    to p(x) = a_n x^n + ... + a_2 x^2 + a_1 x + a_0
        Basically you could use Viete's formula, but this naive approach would cost heaps of multiplications.
        (about O(n*2^n))
        This algorithm uses a 'recursive' approach to compute the coefficients which reuses multiplications.
        Overall it will need O(n^2) multiplications.

        The idea:
        Compute coefficients for every dimension d from 0 to n with the first d roots.
        The formulas for the coefficients of dimension d are:
        a_{d,d} = 1
        a_{d,0} = -a_{d-1,0} * roots(d-1)
        a_{d,i} = -a_{d-1,i} * roots(d-1) + a_{d-1,i-1}

        The first few iterations look like this:
        d | i->        0 |                    1 |              2 | 3
        ------------------------------------------------------------------
        0 |            1 |
        1 |         -r_0 |                    1 |
        2 |      r_0*r_1 |           -(r_0+r_1) |              1 |
        3 | -r_0*r_1*r_2 | r_0r_2+r_1r_2+r_0r_1 | -(r_0+r_1+r_2) | 1
        """

        roots = val
        n = len(roots)
        assert n>0
        # we want the coefficients to be of the same type as the roots. So we can't just use 1 as the neutral
        # element.

        oneElement = roots[0] / roots[0]

        # for dimension = 1
        coeff = [-roots[0], oneElement]
        # and now the bigger dimensions
        for i in xrange(2, n + 1):

            new = [ -roots[i-1] * coeff[0] ]
            for j in xrange(1,i):
                new.append( -roots[i-1] * coeff[j] + coeff[j-1] )
            new.append(oneElement)
            coeff = new
        if isinstance(roots, types.PlainVec):
            coeff = type(roots)(val=coeff)
        return coeff

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        #state.log.debug("getPolyCoefficients.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname, input_types, bit_lengths, dims. role, passive, precompute)
        #TODO: fill out costs if relevant
        return dict()

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        #state.log.debug("getPolyCoefficients.returns(%r %r %r, %r)", methodname, input_types, bit_lengths, dims)
        d = copy(dims[0])
        d[0] += 1
        return ({"type" : types.ModularVec, "bitlen" : state.config.asymmetric_security_parameter, "dim" : d, "signed" : signeds[0]},)

class evalPoly(types.TastyFunction):
    def __call__(self, coeff, x):
        """
        evaluates the polynomial p = sum_{i=0}^{n}{coeff[i] * x^i} at the point x by using Horner's scheme
        coeff has to be a list/tuple
        """
        ret = copy(coeff[-1])
        for i in xrange(len(coeff)-2, -1, -1):
            ret *= x
            ret += coeff[i]
        return ret

    @staticmethod
    def calc_costs(methodname, input_types, bit_lengths, dims, role, passive, precompute):
        #state.log.debug("getPolyCoefficients.calc_costs(%r, %r, %r, %r, %r, %r, %r)", methodname. input_types, bit_lengths, dims, role, passive, precompute)
        #TODO: fill out costs if relevant
        return dict()

    @staticmethod
    def returns(methodname, input_types, bit_lengths, dims, signeds):
        #state.log.debug("evalPoly.returns(%r %r %r, %r)", methodname, input_types, bit_lengths, dims)
        #TODO: Immo, or Wilko: please recheck
        return ({"type" : types.ModularVec, "bitlen" : state.config.asymmetric_security_parameter, "dim" : dims[1], "sigend" : signeds[0]},)

register_class_for_analyzation(getPolyCoefficients)
register_class_for_analyzation(evalPoly)
