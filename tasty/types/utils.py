from tasty.circuit import DROP_MSB, SIGNED, UNSIGNED
from math import ceil, log
def map_signed(x):
    return x and SIGNED or UNSIGNED

def ceilog(val):
    return int(ceil(log(val, 2)))

