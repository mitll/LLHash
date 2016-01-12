#!/usr/bin/env python
#
# Ingest vectors into a feat store and hash store
#

# Written by BC, 12/1/2015

import argparse
import numpy as np
from scripts.match_tools import *
from scripts.feat_store_dict import feat_store_dict
from scripts.hash_store_dict import hash_store_dict
from scripts.lsh_vec import lsh_vec
import cPickle as pickle
import gzip

# Main driver: command line interface
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest vectors and produce a data store.")
    parser.add_argument("--list", type=str, help="List of '<key> <filename>' pairs of vectors to ingest", required=True)
    parser.add_argument("--precision", type=str, help="precision -- float or double", required=False, default='float')
    parser.add_argument("--outfile", type=str, help="output file for the HashStore", required=True)
    parser.add_argument("--num_bits", type=int, help="number of bits for each hash function", required=True)

    args = parser.parse_args()
    list_fn = args.list
    precision_str = args.precision
    out_fn = args.outfile
    num_bits = args.num_bits

    if precision_str=='float':
        precision = np.float32
    elif precision_str=='double':
        precision = np.float64
    else:
        raise ValueError('Unknown precision for vector: {}'.format(precision_str))

    # Configuration for feature store 
    config_feat = '[{"type": "vec", "name": "vector"}]'
    fs_class = feat_store_dict
    config = {'precision':precision, 'normalize':True}
    limit = None

    # Create vec feature store
    fs = read_vec_features_from_list (list_fn, config_feat, fs_class, config, limit)

    # Create hash stores
    print 'Creating LSH tables ...'
    lsh_classes = {'vector':lsh_vec}
    lsh_configs = {'vector':{"method":"rp_acos", "seed":25, "num_functions":6, "num_bits":num_bits, "verbose":True}}
    hs = create_hash_from_fs (fs, lsh_classes, lsh_configs, hash_store_dict, config_feat)
    num_fns_per_band = 1

    # Try out a hash
    key_list = hs.keys()
    print 'a few keys: {}'.format(key_list[0:10])
    for ky in key_list[0:10]:
        print 'ky , hashvalue : {} {}'.format(ky, hs[ky])

    # Create indices
    print 'Creating indexes for tables ...'
    num_fns = lsh_configs['vector']['num_functions']
    hs.create_indexes(num_fns_per_band)

    # Try a retrieval
    item_num = 0
    hv = hs[key_list[item_num]]['vector']
    print 'retrieving things close to hash for key: {}'.format(key_list[item_num])
    r = hs.retrieve('vector', hv)
    print 'result: {}'.format(r)

    # Save the hashstore
    print 'Saving the hashstore to : {}'.format(out_fn)
    outfile = gzip.open(out_fn, 'wb')
    pickle.dump(hs, outfile)
    outfile.close()
    
