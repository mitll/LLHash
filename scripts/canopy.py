#!/usr/bin/env python

"""
Canopy clustering:
Perform clustering using canopies -- a list of sets that cover all keys in the data
"""

import copy

# BC, 6/2015

def canopy_gac (d, canopy, threshold, lc, verbose=False):
    """
    Given distance data (d), a canopy (c), threshold, and linkage criterion (lc),
    perform canopy greedy agglomerative clustering.

    clust = canopy_clustering (d, canopy, threshold, lc)

    inputs:

    d = Sparse distance function in dictionary of dictionaries; e.g., d[0][3] is d(0,3). Matrix should be symmetric
    c = Canopy -- list of sets -- keys should correspond to d[][]
    threshold = float
    lc = Linkage criterion; one of 'single' (minimum distance), 'complete' (maximum distance), or 'average'

    output:
    clust = list of sets -- each set is a cluster
    """

    # Initial clusters are individual points
    clust = {}
    for ky in d.iterkeys():
        clust[ky] = set([ky])
    
    # Canopy indices
    (c_idx, c_inv_idx) = _create_indices(canopy)

    # Clustering distance matrix
    d_clust = copy.deepcopy(d)

    # Main loop
    (dmin, ki, kj) = _find_dmin(d_clust)
    if verbose:
        print "dmin: {} @ ({},{})".format(dmin, ki, kj)
    while (dmin < threshold):
        clust[ki] |= clust[kj]
        del clust[kj]
        if verbose:
            print "new clust: {}".format(clust)

        # Redo canopy based on new clusters
        # A cluster belongs to a canopy if all members of the cluster are in that canopy
        _merge_indices(ki, kj, c_idx, c_inv_idx)
        if verbose:
            print 'new c_idx  : {}'.format(c_idx)
            print 'new inv idx: {}'.format(c_inv_idx)

        # Delete row kj.  Recompute row 'ki' using new clusters
        _delete_row_and_col(d_clust, kj)
        _compute_row(d_clust, d, ki, c_idx, c_inv_idx, clust, lc)
        if verbose:
            print "new d_clust: {}".format(d_clust)

        # Find dmin for next round
        (dmin, ki, kj) = _find_dmin(d_clust)
        if verbose:
            print "dmin: {} @ ({},{})".format(dmin, ki, kj)

    # Output
    clust_out = []
    for c in clust.itervalues():
        clust_out.append(c)
    return clust_out

def _compute_row(d_clust, d, ki, c_idx, c_inv_idx, clust, lc):
    # recompute row given key 'ki'
    d_clust[ki] = {}
    for cn in c_inv_idx[ki]:  # iterate over the canopies ki is in
        for kcol in c_idx[cn]: # need to compute d(ki,kcol) for all kcol in the canopy
            if (kcol not in d_clust[ki]):
                # print 'ki = {}, clust(ki) = {}'.format(ki, clust[ki])
                # print 'kcol = {}, clust(kcol) = {}'.format(kcol, clust[kcol])
                d_clust[ki][kcol] = _compute_linkage(clust[ki], clust[kcol], d, lc)
                d_clust[kcol][ki] = d_clust[ki][kcol]

def _compute_linkage (c1, c2, d, lc):
    if (lc=='single'):  # min
        dval = float("inf")
        for i1 in c1:
            for j1 in c2:
                if (d[i1][j1]<dval):
                    dval = d[i1][j1]
    elif (lc=='complete'): # max
        dval = float("-inf")
        for i1 in c1:
            for j1 in c2:
                if (d[i1][j1]>dval):
                    dval = d[i1][j1]
    elif (lc=='average'):
        dval = 0.0
        num = 0.0
        for i1 in c1:
            for j1 in c2:
                num += 1.0
                dval += d[i1][j1]
        dval /= num
    else:
        raise Exception('unknown linkage criterion: {}'.format(lc))

    return dval

def _create_indices (canopy):
    c_idx = copy.deepcopy(canopy)
    c_inv_idx = {}
    for cnum in xrange(0,len(canopy)):
        for ky in canopy[cnum]:
            if (ky not in c_inv_idx):
                c_inv_idx[ky] = set([])
            c_inv_idx[ky].add(cnum)
    return (c_idx, c_inv_idx)

def _delete_row_and_col (d_clust, k):
    del d_clust[k]
    for ky in d_clust.iterkeys():
        if (k in d_clust[ky]):
            del d_clust[ky][k]

def _find_dmin (d):
    dm = float("inf")
    ki = -1
    kj = -1

    for k1 in d.iterkeys():
        for k2 in d[k1].iterkeys():
            if (k1!=k2) and (d[k1][k2]<dm):
                dm = d[k1][k2]
                ki = k1
                kj = k2
    return (dm, ki, kj)

def _merge_indices(ki, kj, c_idx, c_inv_idx):
    ci = c_inv_idx[ki]
    cj = c_inv_idx[kj]

    # Remove ki and kj from canopies where they both don't occur
    cdiff = ci ^ cj   # symmetric difference
    for i in cdiff:
        c_idx[i].discard(ki)
        c_idx[i].discard(kj)

    # New key for combined canopy will be ki; remove kj from intersection
    cint = ci & cj
    for i in cint:
        c_idx[i].discard(kj)

    # Now update inverted index
    c_inv_idx[ki] &= c_inv_idx[kj]
    del c_inv_idx[kj]
