#!/usr/bin/env python
#
# Match across two data sets using TSV files
#

# BC, 6/30/15

import argparse
import codecs
from feat_store_dict import feat_store_dict
from hash_store_dict import hash_store_dict
from lsh_str import lsh_str_ngram_minhash
import gzip
import re
import sys

from match_tools import create_hash_from_fs
from match_tools import read_features_from_tsv

# Main driver: command line interface
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Combine multiple graph in a directory.")
    parser.add_argument("--profile1", type=str, help="Profile 1 file (tsv.gz format)", required=True)
    parser.add_argument("--profile2", type=str, help="Profile 2 file (tsv.gz format)", required=True)
    parser.add_argument("--output", type=str, help="Output file with matches and scores", required=True)

    args = parser.parse_args()
    p1_fn = args.profile1
    p2_fn = args.profile2
    out_fn = args.output

    config_feat = '[{"name":"userName","type":"str"},{"name":"fullName","type":"str"}]'
    config_lsh_str_user = '{"seed":32, "n":4, "num_functions":10, "num_bits":32, "verbose":false, "lower_case":true, "normalize":false}'
    config_lsh_str_full = '{"seed":32, "n":5, "num_functions":20, "num_bits":32, "verbose":false, "lower_case":true, "normalize":true}'
    key_col = 'userName'

    # Read in profiles
    print 'Reading in TSV files ...'
    limit = None
    fs1 = read_features_from_tsv (p1_fn, config_feat, key_col, feat_store_dict, limit)
    fs2 = read_features_from_tsv (p2_fn, config_feat, key_col, feat_store_dict, limit)
    print 'Done!\n'

    # Create hashes
    print 'Creating LSH tables ...'
    lsh_classes = {'userName':lsh_str_ngram_minhash,'fullName':lsh_str_ngram_minhash}
    lsh_configs = {'userName':config_lsh_str_user,'fullName':config_lsh_str_full}
    hs1 = create_hash_from_fs (fs1, lsh_classes, lsh_configs, hash_store_dict, config_feat)
    hs2 = create_hash_from_fs (fs2, lsh_classes, lsh_configs, hash_store_dict, config_feat)
    print 'Done!!!\n'

    # Create indexes
    print 'Creating indexes for tables ...'
    hs1.create_indexes(2)
    hs2.create_indexes(2)
    print 'Done!\n'

    # Do retrievals based on features
    print 'Now performing retrievals ...'
    output_file = codecs.open(out_fn, 'w', encoding='utf-8')
    num = 0
    output_file.write("key1\tkey2\tfeature\tscore")
    output_file.write("\n")
    for (ky, ht) in hs1:
        if (ky is None) or (ht is None):
            continue
        # fs1_val = fs1[ky]
        for nm in fs1.names():
            res_list = hs2.retrieve(nm, ht[nm])
            if (res_list is None) or (len(res_list)==0):
                continue
            tot = 0
            full_set = {}
            for rs in res_list:
                for ky2 in rs:
                    if (ky2 not in full_set):
                        full_set[ky2] = 0
                    full_set[ky2] += 1
                tot += 1
            for ky2 in full_set.keys():
                output_file.write(u'{}\t{}'.format(ky, ky2))
                score = float(full_set[ky2])/tot
                output_file.write('\t{}\t{}\n'.format(nm, score))
        num += 1 
        if (num%10000)==0:
            print ' {}K'.format(num/1000),
            sys.stdout.flush()
    output_file.close()
    print 'Done!\n'
