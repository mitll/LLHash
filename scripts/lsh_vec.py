#!/usr/bin/env python

"""
Locality sensitive hashing for vectors
"""

# BC, 3/2/2015

from bitarray import bitarray
import json
import numpy as np

class lsh_vec(object):
    """
    Implements a class that performs locality sensitive hashing on vectors

    Note: 
    1) rp_acos is the method of Charikar using random hyperplanes.  
       Pr_{h}[h(x)=h(y)] = 1 - (1/\pi) * theta(x,y)
    """
    def __init__ (self, config):
        """
        config : file in JSON format
        """
        # If it's a string read in a file; otherwise assume it is a dict
        if (type(config) is str):
            # Read in config file
            config_file = open(config, 'r')
            self.config = json.load(config_file)
            config_file.close()
        elif (type(config) is dict):
            self.config = config
        else:
            raise Exception('Unknown config type')
        self.verbose = self.config['verbose']
        if (self.verbose):
            print 'Config is: {}'.format(self.config)

        # Initialize depending on type of LSH
        if (self.config['method']=='rp_acos'):
            self.rp_matrices = None
            self.L = self.config['num_functions']
            self.k = self.config['num_bits']
            self.prng = np.random.RandomState(self.config['seed'])
        else:
            raise Exception('Unknown LSH method requested: {}'.format(self.config['method']))

    def encode (self, x):
        """
        x : vector to encode
        output: list of hash codes, length is L (specified in config as num_functions)
        """
        bx = None
        if (self.config['method']=='rp_acos'):
            bx = self.__encode_rp_acos(x)
        return bx

    def __encode_rp_acos (self, x):
        if (self.rp_matrices is None):
            # We don't really need to store this since it can be generated on the fly
            # This is a convenience
            self.in_dim = len(x)
            self.rp_matrices = []
            for j in xrange(0, self.L):
                rp_matrix = self.prng.randn(self.k, self.in_dim)
                for i in xrange(0,rp_matrix.shape[0]):
                    nr = np.linalg.norm(rp_matrix[i,:], 2)
                    rp_matrix[i,:] = (1/nr)*rp_matrix[i,:]
                self.rp_matrices.append(rp_matrix)
        bx = []
        for i in xrange(0,self.L):
            y = self.rp_matrices[i].dot(x)
            yl = [(lambda z: 1 if (z>=0) else 0)(z) for z in list(y)] 
            bx.append(bitarray(yl))
        return bx

    def hamming (self, x, y):
        """
        x, y: hash codes for two vectors 
        output: x, y -> average Hamming distance across L functions
        """
        s = 0.0
        for i in xrange(0, self.L):
            s += self.k-(x[i]^y[i]).count()
        s *= (1.0/self.L)
        return s

    def norm_hamming (self, x, y):
        """
        x, y: hash codes for two vectors 
        output: x, y -> average normalized Hamming distance across L functions. 
                The Hamming distance is normalized to a probability.
        """
        s = 0.0
        for i in xrange(0, self.L):
            s += 1.0-(1.0/self.k)*((x[i]^y[i]).count())
        s *= (1.0/self.L)
        return s

    def approx_angle(self, x, y):
        """
        x, y: hash codes for two vectors 
        output: approximate angle between vectors
        """
        dh = self.norm_hamming(x, y)
        d = np.pi*(1-dh)
        return d

    def approx_cos(self, x, y):
        """
        x, y: hash codes for two vectors 
        output: approximate cosine of angle between vectors
        """
        dh = self.norm_hamming(x, y)
        d = np.cos(np.pi*(1-dh))
        return d
