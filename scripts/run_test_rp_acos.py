#!/usr/bin/env python

#
# Try out method of Charikar using projection on random hyperplanes (rp_acos)
#

# BC, 3/3/2015

import numpy as np
import time
from lsh_vec import lsh_vec

# Some config constants
config = {"method":"rp_acos", "seed":25, "num_functions":20, "num_bits":64, "verbose":False}
num_eg = 5000
dim = 250
num_calc = 1000
num_show = 10

# Initialize object
print
print 'Encoding {} examples and comparing actual versus approximate inner product'.format(num_eg)
print 'Using M. S. Charikar method\n'
print 'Config is : {}'.format(config)
lsh = lsh_vec(config)

# Generate some random examples and then encode them
np.random.seed(72)
y = np.zeros((dim,num_eg))
by = []
for i in xrange(0,num_eg):
    x = np.random.randn(dim)
    nx = np.linalg.norm(x,2)
    nx = nx if (nx>0) else 1.0
    x = (1/nx)*x
    bx = lsh.encode(x)
    y[:,i] = x
    by.append(bx)

# Find actual inner product
st = time.clock()
ip = y.T.dot(y)
en = time.clock()
print 'time per actual inner product: {}'.format((en-st)/(num_eg*num_eg))

# Print out results
print '\nA few of ip:\n'
i1 = np.random.random_integers(low=0, high=num_eg-1, size=(num_calc))
i2 = np.random.random_integers(low=0, high=num_eg-1, size=(num_calc))
i1 = np.c_[i1,i2]
s = 0.0
s2 = 0.0
j=0 
st = time.clock()
for i in i1:
    tp = tuple(i)
    b1 = by[tp[0]]
    b2 = by[tp[1]]
    # print 'bit vecs: {} {}'.format(b1, b2)
    dh = lsh.approx_cos(b1,b2)
    s += (dh-ip[tp])
    s2 += (dh-ip[tp])**2
    if (j<num_show):
        print 'Actual ip: {} {}'.format(tp, ip[tp])
        print 'Approx cos: {}'.format(dh)
        print
    j += 1
en = time.clock()

mean = (1.0/num_calc)*s
std = np.sqrt((1.0/num_calc)*s2-mean*mean)
print 'Mean: {}'.format(mean)
print 'Std: {}'.format(std)
print 'time per approx inner product: {}'.format((en-st)/num_calc)
print
