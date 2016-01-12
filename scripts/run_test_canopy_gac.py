#!/usr/bin/env python

#
# Run a simple example of canopy greedy agglomerative clustering
#

# Written by BC, 6/2015

import numpy as np
from canopy import canopy_gac

# Define points
x = [[0.0,0.0],[0.0,1.0],[1.0,0.0],[1.0,1.0],[2.0,2.0],[2.5,2.5]]

# Define canopies
canopy = [set([0,1,2,3]), set([3,4]), set([5])]
thresh = 1.1
lc = 'average'

# Compute distances -- 
d = {}
for ci in canopy:
    for i in ci:
        for j in ci:
            if (i not in d):
                d[i] = {}
            d[i][j] = np.linalg.norm(np.array(x[i])-np.array(x[j]))
            
# Print out initial data
print 'Canopies are: {}\n'.format(canopy)
print 'Distance matrix is {}\n'.format(d)

# Run canopy
print 'Canopy clustering with a threshold of {}:'.format(thresh)
clust1 = canopy_gac(d, canopy, thresh, lc)
print 'Clusters are:'
for c in clust1:
    print '{}'.format(c)
print

