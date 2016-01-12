#!/bin/sh

#
# Example script for ingest of vectors 
#

list=lists/list_test.txt
precision=float
outfile=datastore/test_ds.dat

./run_ingest_vec.py --precision $precision --list $list --outfile $outfile --num_bits 8
./run_ingest_vec.py --precision $precision --list $list --outfile $outfile --num_bits 16
./run_ingest_vec.py --precision $precision --list $list --outfile $outfile --num_bits 32
