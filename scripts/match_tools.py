#!/usr/bin/env python

"""
Match Tools

Tools for loading features and hashing data

"""

# BC 7/4/15

import codecs
from feat_store_dict import feat_store_dict
import glob
import gzip
from hash_store_dict import hash_store_dict
import numpy as np
import os
import random
import re
import sys

def create_canopy(hs, feat_nm, seed, sthresh, verbose=False):
    """
    create_canopy(hs, feat_nm, seed, sthresh, verbose=False)
    
    hs = hash store
    feat_nm = feature to create canopy for
    seed = random seed for selecting points for canopy
    sthresh = similarity threshold, between 0 and 1 -- anything above the threshold will be 
              removed from further selection when creating the canopy
    verbose = True/False chatty info on stdout
    """
    if (sthresh<0) or (sthresh>1):
        raise ValueError('create_canopy: similarity threshold should be between 0 and 1')
    ky_set = set(hs.keys())
    prng = random.Random(seed)
    canopy = []

    while len(ky_set)>0:
        # Get initial seed for current canopy set
        canopy_set = set([])
        ky_rnd = prng.sample(ky_set, 1)[0]  # sample random element from set
        canopy_set.add(ky_rnd)
        hs_sig = hs[ky_rnd][feat_nm]
        result = hs.retrieve(feat_nm, hs_sig)
        result = [(r & ky_set) for r in result]
        if verbose:
            print 'seed: {}'.format(ky_rnd)
            print 'result: {}'.format(result)
        result_hash = {}
        num_sets = 0
        for r in result:
            num_sets += 1
            for v in r:
                if v not in result_hash:
                    result_hash[v] = 0
                result_hash[v] += 1
        num_sets *= 1.0
        for ky in result_hash.iterkeys():
            result_hash[ky] /= num_sets
        for ky in result_hash.iterkeys():
            canopy_set.add(ky)
            if (result_hash[ky]>sthresh) and (ky in ky_set):
                ky_set.remove(ky)
        if verbose:
            print 'hs_keys is: {}'.format(hs_sig)
            print 'result_hash is: {}'.format(result_hash)
            print 'canopy set: {}'.format(canopy_set)
        # Append canopy set to canopy
        canopy.append(canopy_set)
    return canopy

def create_hash_from_fs (fs, lsh_classes, lsh_configs, hash_store_class, hash_store_config):
    """
    create_hash_from_fs (fs, lsh_classes, lsh_configs, hash_store_class, hash_store_config)
    
    fs = feature store
    lsh_classes, lsh_configs = classes and configs for each feature; dict with keys from fs.keys()
    hash_store_class, hash_store_config = hash store class and config
    """

    # Feature names
    feat_names = fs.names()

    # Set up LSH for each feature
    lsh_obj = {}
    for nm in feat_names:
        lsh_obj[nm] = lsh_classes[nm](lsh_configs[nm])

    # Perform LSH on each instance and feature
    hs = hash_store_class(hash_store_config)
    num = 0
    had_output = False
    for (ky,val) in fs:
        lsh_vals = {}
        for nm in feat_names:
            lsh_vals[nm] = lsh_obj[nm].encode(val[nm])
        hs.add(ky, lsh_vals)
        num += 1
        if (num % 1000)==0:
            print '{}K '.format(num/1000), 
            had_output = True
            sys.stdout.flush()
    if had_output:
        print
    return hs

def compute_sparse_distances(canopy, feat_store, fname, dist_fn):
    """
    compute_sparse_distances(canopy, feat_store, fname, dist_fn)

    canopy = canopy created from create_canopy -- a list of sets of keys
    feat_store = feature store
    fname = feature name to use for computing distances
    dist_fn = distance function that can be called as dist_fn(x,y)
    """
    dmax = 1.0*len(feat_store.keys())**2
    d = {}
    num_dist = 0
    for cs in canopy:
        for ky1 in cs:
            v1 = feat_store[ky1][fname]
            for ky2 in cs:
                if ky1 not in d:
                    d[ky1] = {}
                if ky2 not in d[ky1]:
                    # compute distance
                    v2 = feat_store[ky2][fname]
                    num_dist += 1
                    d[ky1][ky2] = dist_fn(v1, v2)
    print 'number of distances computed: {} / {} = {} %'.format(num_dist, dmax, 100.0*(num_dist/dmax))
    return d

def read_features_from_counts(count_dir, config, fs_class, limit=None):
    if (limit is None):
        limit = sys.maxint
    # Create feature store
    fs = fs_class(config)
    num = 0
    for count_fn in glob.glob(os.path.join(count_dir, '*.txt.gz')):
        zf = gzip.open(count_fn, 'r')
        count_file = codecs.getreader('utf-8')(zf)
        for ln in count_file:
            f = ln.rstrip().split()
            w_list = [w.split('|')[0] for w in f[2:]]
            w_str = ' '.join(w_list)
            fs.add('@' + f[1], {'words':w_str})
            num += 1
            if (num > limit):
                break
            if (num%1000)==0:
                print '{}K '.format(num/1000),
		sys.stdout.flush()
        count_file.close()
        if (num > limit):
            break
    print
    return fs

def read_vec_features_from_list (list_fn, config_feat, fs_class, config, limit=None):
    """
    read_vec_features_from_list(list_fn, config_feat, fs_class, config, limit=None)

    list_fn  = List file to read from; format of each line is "<key> <vec file name>"
    config_feat   = JSON string to configure feature store; passed to fs_class
    fs_class = Class to use for feature store
    config = dictionary of configuration parameters for ingest
        normalize = set to True to normalize vectors to unit norm after loading
        precision = numpy type -- either numpy.float or numpy.double
    limit = (optional) limit to 'limit' instances loaded
    """

    # Create feature store
    fs = fs_class(config_feat)
    
    # Setup
    precision = config['precision']
    normalize_vec = config['normalize']

    # Open and read list file 
    list_file = open(list_fn, 'r')
    num = 0
    had_output = False
    for ln in list_file:
        ln = ln.rstrip()
        (ky, vec_fn) = ln.split()
        vec = np.fromfile(vec_fn, precision)
        if normalize_vec:
            nrm = np.linalg.norm(vec, 2)
            if (nrm > 0.0):
                vec /= nrm
        fs.add(ky, {'vector':vec})
        num += 1
        if (num % 1000)==0:
            print '{}K '.format(num/1000), 
            sys.stdout.flush()
            had_output = True
        if (limit is not None) and (num>=limit):
            break
    if had_output:
        print
    return fs

def read_features_from_tsv(fn, config, ky_col, fs_class, limit=None):
    """
    read_features_from_tsv(fn, config, ky_col, fs_class)

    fn       = File to read from
    config   = JSON string to configure feature store
    ky_col   = Name of the column to use as a key for the feature store
    fs_class = Class to use for feature store
    limit = (optional) limit to 'limit' instances loaded
    """

    # Create feature store
    fs = fs_class(config)

    # Open file and get header
    if re.search("\.gz$", fn):
        ff_raw = gzip.open(fn,'r')
    else:
        ff_raw = open(fn, 'r')
    feat_file = codecs.getreader('utf-8')(ff_raw)
    hdr = feat_file.readline().rstrip("\n").split('\t')

    #  Find feature indexes in header
    name_col = {}
    for nm in fs.names():
        if (nm not in hdr):
            raise Exception('Field {} not found in file {}'.format(nm, fn))
        name_col[nm] = hdr.index(nm)
    ky_col = hdr.index(ky_col)
        
    # Read in gz tsv file
    num = 0
    for ln in feat_file:
        f = ln.rstrip("\n").split('\t')
        ky = f[ky_col]
        rec = {}
        for (nm, col) in name_col.iteritems():
            rec[nm] = f[col]
        fs.add(ky, rec)
        num += 1
        if (num % 1000)==0:
            print '{}K '.format(num/1000), 
            sys.stdout.flush()
        if (limit is not None) and (num>=limit):
            break
    feat_file.close()
    print

    # Return feature store
    return fs


