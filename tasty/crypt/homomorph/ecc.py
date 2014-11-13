# -*- coding: utf-8 -*-

import gmpy
import math
from gmpy import mpz

from tasty import cost_results, state

_EC_lib = {"P-192":(mpz(-3), mpz("64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1", 16),
                    mpz(6277101735386680763835789423207666416083908700390324961279),
                    mpz("188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012",16),
                    mpz("07192b95ffc8da78631011ed6b24cdd573f977a11e794811",16),
                    mpz(6277101735386680763835789423176059013767194773182842284081) ),
           "secp256r1":(mpz("ffffffff00000001000000000000000000000000fffffffffffffffffffffffc",16),
                        mpz("5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b",16),
                        mpz("ffffffff00000001000000000000000000000000ffffffffffffffffffffffff",16),
                        mpz("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296",16),
                        mpz("4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5",16),
                        mpz("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551",16) ),
           "secp224r1":(mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFE",16),
                        mpz("B4050A850C04B3ABF54132565044B0B7D7BFD8BA270B39432355FFB4",16),
                        mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000001",16),
                        mpz("B70E0CBD6BB4BF7F321390B94A03C1D356C21122343280D6115C1D21",16),
                        mpz("BD376388B5F723FB4C22DFE6CD4375A05A07476444D5819985007E34",16),
                        mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFF16A2E0B8F03E13DD29455C5C2A3D",16) ),
           "secp192r1":(mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFC",16),
                        mpz("64210519E59C80E70FA7E9AB72243049FEB8DEECC146B9B1",16),
                        mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFF",16),
                        mpz("188DA80EB03090F67CBF20EB43A18800F4FF0AFD82FF1012",16),
                        mpz("07192B95FFC8DA78631011ED6B24CDD573F977A11E794811",16),
                        mpz("FFFFFFFFFFFFFFFFFFFFFFFF99DEF836146BC9B1B4D22831",16) ),
           "secp160r1":(mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFC",16),
                        mpz("1C97BEFC54BD7A8B65ACF89F81D4D4ADC565FA45",16),
                        mpz("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFF",16),
                        mpz("4A96B5688EF573284664698968C38BB913CBFC82",16),
                        mpz("23A628553168947D59DCC912042351377AC5FB32",16),
                        mpz("0100000000000000000001F4C8F927AED3CA752257",16) )
                        }

def getEC(name):
    """
    looks up Elliptic Curve definition in the library. Name is the name of the EC, e.g. secp256r1
    """
    if name in _EC_lib.keys():
        vals = _EC_lib[name]
        return EllipticCurve(vals[0],vals[1],vals[2],vals[3],vals[4],vals[5])
    else:
        raise NotImplementedError("Elliptic Curve " + name + " is not implemented yet.")

def decodePoint(comp_point, EC):
    """
        Point decoding as described in http://www.secg.org/download/aid-385/sec1_final.pdf
        Returns an ECPoint Object
    """
    type = comp_point[0:2]
    if not type in ('00','02','03','04'):
        raise Exception("Unknown type of pointcompression: " + comp_point)
    if type == '00':
        return ECPoint(0,0,EC,True)
    pointDecLength = EC.bitlen / 4
    if type == '04':
        if len(comp_point) != 2*pointDecLength + 2:
            raise Exception("Format error: " + comp_point)
        x = mpz(comp_point[2:pointDecLength+2],16)
        y = mpz(comp_point[pointDecLength+2:len(comp_point)],16)
        if x == y == 0:
            infinity = True
        else:
            infinity = False
        return ECPoint(x,y,EC,infinity)
    else:
        xdec = comp_point[2:len(comp_point)]
        if len(xdec) != pointDecLength:
            raise Exception("Format error: " + comp_point)
        x = mpz(xdec,16)
        ys = EC.eval(x)
        type = int(type)
        if type%2 == ys[0]%2:
            if x == ys[0] == 0:
                return ECPoint(x,ys[0],EC,True)
            else:
                return ECPoint(x,ys[0],EC,False)
        else:
            if x == ys[1] == 0:
                return ECPoint(x,ys[1],EC,True)
            else:
                return ECPoint(x,ys[1],EC,False)


def decompressPoint(comp_point, EC):
    """
    """
    comp_point.EC = EC
    comp_point.p = EC.p
    if comp_point.compress:
        ys = EC.eval(comp_point.x)
        if ys[0]%2 == comp_point.y:
            comp_point.y = ys[0]
        else:
            comp_point.y = ys[1]
    return comp_point

def modular_sqrt(a, p):
    """ Find a quadratic residue (mod p) of 'a'. p
        must be an odd prime.

        Solve the congruence of the form:
            x^2 = a (mod p)
        And returns x. Note that p - x is also a root.

        0 is returned is no square root exists for
        these a and p.

        The Shanks-Tonelli algorithm is used (except
        for some simple cases in which the solution
        is known from an identity). This algorithm
        runs in polynomial time (unless the
        generalized Riemann hypothesis is false).
    """
    # Simple cases
    #
    if gmpy.legendre(a, p) != 1:
        return 0
    elif a == 0:
        return 0
    elif p == 2:
        return a
    elif p % 4 == 3:
        return pow(a, (p + 1) / 4, p)

    # Partition p-1 to s * 2^e for an odd s (i.e.
    # reduce all the powers of 2 from p-1)
    #
    s = p - 1
    e = 0
    while s % 2 == 0:
        s /= 2
        e += 1

    # Find some 'n' with a legendre symbol n|p = -1.
    # Shouldn't take long.
    #
    n = mpz(2)
    while gmpy.legendre(n, p) != -1:
        n += 1

    # Here be dragons!
    # Read the paper "Square roots from 1; 24, 51,
    # 10 to Dan Shanks" by Ezra Brown for more
    # information
    #

    # x is a guess of the square root that gets better
    # with each iteration.
    # b is the "fudge factor" - by how much we're off
    # with the guess. The invariant x^2 = ab (mod p)
    # is maintained throughout the loop.
    # g is used for successive powers of n to update
    # both a and b
    # r is the exponent - decreases with each update
    #
    x = pow(a, (s + 1) / 2, p)
    b = pow(a, s, p)
    g = pow(n, s, p)
    r = e

    while True:
        t = b
        m = 0
        for m in xrange(r):
            if t == 1:
                break
            t = pow(t, 2, p)

        if m == 0:
            return x

        gs = pow(g, 2 ** (r - m - 1), p)
        g = (gs * gs) % p
        x = (x * gs) % p
        b = (b * g) % p
        r = m


class EllipticCurve(object):
    def __init__(self, a, b, p, gx, gy, order):
        """
        creates a EllipticCurve object with the parameters y^2 = x^3 + a*x + b over the Field F_p, p prim
        with the generator point (gx, gy). Order is the order of the generator point
        """
        self.p = p
        self.a = a
        self.b = b
        self.ord = order
        self.G = ECPoint(gx, gy, self)
        self.bitlen = int(math.ceil(math.log(self.p,2)))

    def getGenerator(self):
        """
        returns the generator point
        """
        return self.G

    def getOrder(self):
        """
        returns the order of the generator point
        """
        return self.ord

    def hasPoint(self, point):
        """
        returns True if point is part of this Elliptic Curve
        """
        y = pow(point.y,2,self.p)
        x = (pow(point.x,3,self.p) + self.a * point.x + self.b) % self.p
        return y == x

    def nextPoint(self, start_x):
        """
        Find smallest x >= start_x s.t. (x,y) is on EC
        """
        x = start_x % self.p
        y = self.eval(x)[0]
        while not self.hasPoint(ECPoint(x,y,self)):
            x += 1
            y = self.eval(x)[0]
        return ECPoint(x,y,self)

    def eval(self, x):
        """
        evaluates the EC equation at the point x. Returns the 2 possible y values
        """
        ev = (pow(x,3,self.p) + self.a * x + self.b) % self.p
        sqrt = modular_sqrt(ev, self.p)
        return (sqrt, self.p-sqrt)

class ECPoint(object):
    def __init__(self, x, y, EC, infinity=False):
        self.EC = EC
        self.p = EC.p
        self.x = x
        self.y = y
        self.infinity = infinity
        self.compress = False

    def __add__(self, X):
        if X == self:
            return X * 2
        if self.infinity:
            return X
        if X.infinity:
            return self
        d = self.x - X.x
        if d==0: #Then the point is infinity
            return ECPoint(0,0,self.EC,True)
        s = gmpy.divm(self.y - X.y, d, self.p)
        xn = (pow(s, 2, self.p) - self.x - X.x) % self.p
        yn = (-self.y + s * (self.x - xn)) % self.p
        return ECPoint(xn , yn, self.EC)

    def __sub__(self, X):
        return self.__add__(ECPoint(X.x, -X.y % X.p, X.EC, X.infinity))

    #===========================================================================
    # std. point multiplication with affine coordinates
    # was replaced by multiplication which uses Jacobian coordinates -> faster! Yeah!
    #
    # def __mul__(self, k):
    #    if k == 1:
    #        return self
    #    if k == 2: #then we want to do a point doubling
    #        if self.y == 0: #then we get the infinity point
    #            return ECPoint(0,0,self.EC,True)
    #        s = gmpy.divm(3 * pow(self.x, 2, self.p) + self.EC.a, 2 * self.y, self.p)
    #        xn = (pow(s, 2, self.p) - (2 * self.x)) % self.p
    #        yn = (-self.y + s * (self.x - xn)) % self.p
    #        return ECPoint(xn, yn, self.EC)
    #    else: #We use the square and multiply in an additive way
    #        Y = None
    #        P = self
    #        for i in range( int(math.floor(math.log(k, 2)))+1 ):
    #            if k % 2 == 1:
    #                if Y is None:
    #                    Y = P
    #                else:
    #                    Y += P
    #            P = P * 2
    #            k = k >> 1
    #        return Y
    #===========================================================================

    def __mul__(self,k):
        """
        point multiplication
        uses Jacobian coordinates internally for speedup
        """
        if state.precompute:
            cost_results.CostSystem.costs["theoretical"]["setup"]["accumulated"](EC_Mul=1)
        else:
            cost_results.CostSystem.costs["theoretical"]["online"]["accumulated"](EC_Mul=1)

        if self.infinity:
            return ECPoint(0,0,self.EC,True)
        if k==1:
            return self
        if k==2: # point doubling with affine coordinates
            if self.y == 0: #then we get the infinity point
                return ECPoint(0,0,self.EC,True)
            s = gmpy.divm(3 * pow(self.x, 2, self.p) + self.EC.a, 2 * self.y, self.p)
            xn = (pow(s, 2, self.p) - (2 * self.x)) % self.p
            yn = (-self.y + s * (self.x - xn)) % self.p
            return ECPoint(xn, yn, self.EC)
        pc = (0,0,1)
        for bit in gmpy.digits(k,2):
            pc = self._doubleP(pc)
            if bit == "1":
                pc = self._addP(pc)
        x = gmpy.divm(pc[0],pow(pc[2],2,self.p),self.p)
        y = gmpy.divm(pc[1],pow(pc[2],3,self.p),self.p)
        return ECPoint(x,y,self.EC)

    def _addP(self,pc):
        """
        adds a point in Jacobian coordinates
        pc is expected to be a tuple of (x,y,z)
        return a tuple of Jacobian coordinates
        """
        if pc == (0,0,1): #infinity
            return (self.x,self.y,1)
        A = (self.x * pow(pc[2],2,self.p)) % self.p
        B = (self.y * pow(pc[2],3,self.p)) % self.p
        C = A - pc[0]
        D = B - pc[1]
        x = (pow(D,2,self.p)-(pow(C,3,self.p)+2*pc[0]*pow(C,2,self.p))) % self.p
        y = (D*(pc[0]*pow(C,2,self.p) - x) - pc[1]*pow(C,3,self.p)) % self.p
        z = (pc[2]*C) % self.p
        return (x,y,z)

    def _doubleP(self,pc):
        """
        point doubling with Jacobian coordinates
        pc is expected to be a tuple of (x,y,z)
        self can be any point, but the modul p of it is used
        returns a tuple of Jacobian coordinates
        """
        if pc == (0,0,1): #infinity
            return (0,0,1)
        A = (mpz(4)*pc[0] * pow(pc[1],2,self.p))
        B = (mpz(8)*pow(pc[1],4,self.p))
        C = (mpz(3)*(pc[0]-pow(pc[2],2,self.p))*(pc[0]+pow(pc[2],2,self.p)) )
        D = (mpz(-2)*A + pow(C,2,self.p)) % self.p
        x = D
        y = (C*(A-D)-B) % self.p
        z = (mpz(2)*pc[1]*pc[2]) % self.p
        return (x,y,z)



    def __str__(self):
        if self.infinity:
            return "Infinity"
        else:
            return "%d, %d" % (self.x,self.y)

    def __eq__(self,X):
        if X is None:
            return False
        return self.x == X.x and self.y == X.y and self.EC == X.EC and self.infinity == X.infinity


    def __getstate__(self):
        if self.infinity:
            return {"infinity": self.infinity}

        state = {
            "compress": self.compress,
            "x": self.x.binary()
            }

        if self.compress:
            state["y"] = (self.y % 2).binary()
        else:
            state["y"] = self.y.binary()
        return state

    def __setstate__(self, state):
        self.infinity = infinity = state.get("infinity", False)
        if infinity:
            self.y = mpz(0)
            self.x = mpz(0)
            self.compress = False
            return

        self.compress = state["compress"]
        self.x = mpz(state["x"], 256)
        self.y = mpz(state["y"], 256)


    def encode(self, compress=False):
        """
        Point encoding as described in http://www.secg.org/download/aid-385/sec1_final.pdf
        returns a hexstring representation of the ECPoint
        """
        if self.infinity:
            return "00"
        pointInHexLen = self.EC.bitlen/4
        x = hex(self.x)
        x = x[2:].zfill(pointInHexLen)
        if compress:
            y = self.y % 2
            if y == 0:
                return "02" + x
            else:
                return "03" + x
        else:
            y = hex(self.y)[2:].zfill(pointInHexLen)
            return "04" + x + y



