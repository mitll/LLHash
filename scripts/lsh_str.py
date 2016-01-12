#!/usr/bin/env python

"""
Locality sensitive hashing for strings using character n-grams
"""
# BC, 3/2/2015

from bitarray import bitarray
import json
import numpy as np
import random
import text_tools as tt

class lsh_str_ngram_minhash (object):
    """
    Implements a class that performs locality sensitive hashing on strings.
    Uses character n-grams and min-hash.

    Typical usage:
    >>> config = '{"seed":25, "n":5, "num_functions":10, "num_bits":32, "verbose":false}'
    >>> ls = lsh_str_ngram_minhash(config)
    >>> y = ls.encode('hello')
    """

    NUM_BITS = 63  # Number of max bits to use -- should be <= the number of bits in an int; typically values are 31 or 63 to avoid <0 numbers

    def __init__ (self, config):
        """
        config : configuration in JSON format
        """

        # Basic setup
        self.config = json.loads(config)
        self.n = self.config['n']
        self.seed = self.config['seed']
        self.prng = random.Random(self.seed)
        self.num_fns = self.config['num_functions']
        self.num_bits = self.config['num_bits']
        self.bit_mask = 2**self.num_bits-1
        self.full_bit_mask = int(2**lsh_str_ngram_minhash.NUM_BITS-1)
        if ('lower_case' in self.config):
            self.lower = self.config['lower_case']
        else:
            self.lower = False
        if ('normalize' in self.config):
            self.normalize = self.config['normalize']
        else:
            self.normalize = False
        if (self.normalize):
            self.utf8_rewrite_hash = tt.create_utf8_rewrite_hash()

        if ('verbose' in self.config):
            self.verbose = self.config['verbose']
        else:
            self.verbose = False

        # Checks
        if (self.num_bits > lsh_str_ngram_minhash.NUM_BITS):
            raise Exception('Number of bits must be <= {}'.format(lsh_str_ngram_minhash.NUM_BITS))
        
        # Generate parameters for minhash
        # (unsigned) (a*x+b) >> (w-M) ; a is a random int, b is a random integer, both are < 2^w
        # Based on preprint by Mikkel Thorup, "High Speed Hashing for Integers and Strings"
        # Note odd 'a' is not needed
        self.a = []
        self.b = []
        self.shift = lsh_str_ngram_minhash.NUM_BITS-self.num_bits
        for i in xrange(0,self.num_fns):
            a1 = int(self.prng.randint(0,2**lsh_str_ngram_minhash.NUM_BITS-1))
            b1 = int(self.prng.randint(0,2**lsh_str_ngram_minhash.NUM_BITS-1))
            self.a.append(a1)
            self.b.append(b1)

        # Verbose output
        if (self.verbose):
            print 'Initializing lsh_str:'
            print '\tConfig is: {}'.format(self.config)
            print '\tBit mask is: {}'.format(self.bit_mask)
            print '\tFull bit mask is: {}'.format(self.full_bit_mask)
            print

    def encode (self, s):
        """
        x : string to encode
        output: list of hash codes, length is 'num_functions'
                each hashcode has 'num_bits' significant bits
        """
        if (self.lower):
            s = s.lower()
        if (self.normalize):
            s = tt.convertUTF8_to_ascii(s, self.utf8_rewrite_hash)

        if (self.n=='token'):
            ng = self.__get_char_tokens(s)
        else:
            ng = self.__get_char_ngrams(s)
        output, output_str = self.__min_hash(ng)
        if (self.verbose):
            print 'ngrams are: {}'.format(ng)
            print 'output is: {}'.format(output)
            print 'output_str is: {}'.format(output_str)
            print
        return output

    def __get_char_ngrams (self, s):
        ng = []
        for i in xrange(0,len(s)-self.n+1):
            ng.append(s[i:i+self.n])
        return ng

    def __get_char_tokens (self, s):
        return s.split()
        
    def __min_hash (self, ngrams):
        out = None
        out_str = None
        for ng in ngrams:
            hvals = self.__univ_hash(ng)
            if (out==None):
                out = hvals
                out_str = [ng for x in hvals]
                continue
            for i in xrange(0, self.num_fns):
                if (hvals[i] < out[i]):
                    out[i] = hvals[i]
                    out_str[i] = ng
        return out, out_str

    def __univ_hash (self, s):
        hs = hash(s) & self.full_bit_mask
        hash_list = []
        for i in xrange(0, self.num_fns):
            hv = int(((self.a[i]*hs+self.b[i]) >> self.shift) & self.bit_mask)
            hash_list.append(hv)
        return hash_list
