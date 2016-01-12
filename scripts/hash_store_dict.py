#!/usr/bin/env python

"""
Implementation of the interface hash_store using in-memory dictionaries in Python
"""

# BC, 6/17/2015
from bitarray import bitarray
import json

class hash_store_dict(object):
    """
    Implementation of hash storage using dictionaries

    Abstract a hash store and allow several different storage mechanisms.
    Use duck typing for compatibility across different implementations.

    The methods that should be implemented are:
    - Constructor: hash_store(config_str)
    - Iterator methods: __iter__, next
    - add(key, value)
    - close()
    - __getitem__(key)  -- for general data store not an efficient method -- use iterators whenever possible

    Additional methods implemented for this version:
    - (none)

    The config file for open should be JSON and contain the following fields:
    - "features": These are the features to be processed:
      [{"name": "feat1"}, {"name": "feat2"}]
    - additional fields will be ignored -- e.g., the feat_store description can be re-used
    """

    def __init__(self, config_str=None):
        """x.__init__(config_str) initializes feature store with JSON string parameters"""
        if config_str!=None:
            self.config = json.loads(config_str)
            self.feat = {}
            self.feat_names = set([x['name'] for x in self.config])
            self.index_created = False
            self.nested_index_created = False

    def add(self, key, y):
        """x.add(key, y) adds y to hash store with key 'key'; y is a list of hash values"""
        if not hasattr(self, 'config'):
            raise ValueError('feat_store_list: must provide configuration before using a feature store')
        if (type(y) is not dict):
            raise ValueError('feat_store_list: item added to feat store must be a dictionary')
        for ky in y:
            if (ky not in self.feat_names):
                raise ValueError('feat_store_list: configuration specified feature names not used in add()')
        self.feat[key] = y

    def close(self):
        """x.close() closes the feature store -- in this case does nothing"""
        return

    def create_indexes(self, num_fns_per_band):
        """create_indexes(num_fns_per band) : create indexes for hash values grouped by 'num_fns_per_band'
        """
        # Loop over one item and pre-calculate bands
        slices = {}
        done = False
        for (ky, hval) in self.feat.iteritems():
            for nm in self.feat_names:
                i1 = 0
                slices[nm] = []
                if (hval[nm] is None):
                    continue
                while (i1+num_fns_per_band)<=len(hval[nm]):
                    slices[nm].append((i1, i1+num_fns_per_band))
                    i1 += num_fns_per_band
                done = True
            if (done):
                break
        
        # Create arrays for indexes
        self.index = {}
        for nm in self.feat_names:
            self.index[nm] = []
            for sl in slices[nm]:
                self.index[nm].append({})

        # Create indexes
        for (ky, hval) in self.feat.iteritems():
            for nm in hval.iterkeys():
                hval_nm = hval[nm]
                if (hval_nm is None):
                    continue
                is_bitarray = False
                if isinstance(hval_nm[0],bitarray):
                    is_bitarray = True
                i1 = 0
                for sl in slices[nm]:
                    if is_bitarray:
                        tp = tuple([barr.tobytes() for barr in hval_nm[sl[0]:sl[1]]])
                    else:
                        tp = tuple(hval_nm[sl[0]:sl[1]])
                    if (tp not in self.index[nm][i1]):
                        self.index[nm][i1][tp] = set([])
                    self.index[nm][i1][tp].add(ky)
                    i1 += 1
        self.slices = slices
        self.index_created = True

    def create_nested_indexes(self, slice_sizes):
        """create_nested_indexes(self, slice_sizes) 
        Created a nested set of inverted indices based on different slice sizes.
        The slice sizes should be monotone increasing.  E.g., slice_size=[1,2,4,7,10].
        This creates indices for slices, [0:1], [0:2], [0:4], [0:7], [0:10].  The maximum
        slice size is the number of hash functions.
        """
        
        # Note: For now only one slice_size list is being used for all features.
        # In the future it makes sense to make feature specific slice sizes. I.e., slices_sizes
        # should be a dictionary.

        # Loop over one item and pre-calculate bands
        slices = {}
        done = False
        for (ky, hval) in self.feat.iteritems():
            for nm in self.feat_names:
                i1 = 0
                slices[nm] = []
                if (hval[nm] is None):
                    continue
                sz_last = 0
                for sz in slice_sizes:
                    if (sz<=0) or (sz <= sz_last) or (sz>len(hval[nm])):
                        raise RuntimeError('slices sizes must be monotone increasing')
                    slices[nm].append((0,sz))
                    sz_last = sz
                done = True
            if (done):
                break

        # Create arrays for indexes
        self.nested_index = {}
        self.children = {}
        for nm in self.feat_names:
            self.nested_index[nm] = []
            self.children[nm] = []
            for sl in slices[nm]:
                self.nested_index[nm].append({})
                self.children[nm].append({})

        # Create indexes
        for (ky, hval) in self.feat.iteritems():
            for nm in hval.iterkeys():
                hval_nm = hval[nm]
                if (hval_nm is None):
                    continue
                is_bitarray = False
                if isinstance(hval_nm[0],bitarray):
                    is_bitarray = True
                i1 = 0
                for sl in slices[nm]:
                    if is_bitarray:
                        tp = tuple([barr.tobytes() for barr in hval_nm[sl[0]:sl[1]]])
                    else:
                        tp = tuple(hval_nm[sl[0]:sl[1]])
                    if (tp not in self.nested_index[nm][i1]):
                        self.nested_index[nm][i1][tp] = set([])
                    self.nested_index[nm][i1][tp].add(ky)
                    if i1>=1:
                        sl_prev = slices[nm][i1-1]
                        if is_bitarray:
                            tp_prev = tuple([barr.tobytes() for barr in hval_nm[sl_prev[0]:sl_prev[1]]])
                        else:
                            tp_prev = tuple(hval_nm[sl_prev[0]:sl_prev[1]])
                        if (tp_prev not in self.children[nm][i1-1]):
                            self.children[nm][i1-1][tp_prev] = set([])
                        self.children[nm][i1-1][tp_prev].add(tp)
                    i1 += 1
        self.nested_slices = slices
        self.nested_index_created = True

    def __getitem__(self, i):
        """x.__getitem__(i) <==> x[i]"""
        if not hasattr(self, 'config'):
            raise Exception('must provide configuration before using a feature store')
        return self.feat[i]

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        self.iter = self.feat.iteritems()
        return self

    def num_nested_levels(self, feat_name):
        return len(self.nested_slices[feat_name])

    def keys(self):
        """x.keys() returns list of keys"""
        return self.feat.keys()

    def names(self):
        """x.keys() returns list of feature names"""
        return self.feat_names

    def next(self):
        """x.next() -> the next value, or raise StopIteration"""
        if not hasattr(self, 'config'):
            raise Exception('must provide configuration before using a feature store')
        try:
            (key, value) = self.iter.next()
            return (key, value)
        except StopIteration:
            raise StopIteration()

    def retrieve(self, feat_nm, ht_list):
        if (ht_list is None):
            result = []
            return
        if (not self.index_created):
            raise Exception('index not created')
        result = []
        idx = self.index[feat_nm]
        is_bitarray = False
        if isinstance(ht_list[0], bitarray):
            is_bitarray = True
        i1 = 0
        for sl in self.slices[feat_nm]:
            if is_bitarray:
                h_sl = tuple([barr.tobytes() for barr in ht_list[sl[0]:sl[1]]])
            else:
                h_sl = tuple(ht_list[sl[0]:sl[1]])
            if (h_sl in idx[i1]):
                result.append(idx[i1][h_sl])
            i1 += 1
        return result

    def retrieve_children(self, feat_nm, ht_list, level):
        if (ht_list is None):
            result = []
            return
        if (not self.nested_index_created):
            raise Exception('nested index not created')
        result = []
        children = self.children[feat_nm][level]
        is_bitarray = False
        if isinstance(ht_list[0], bitarray):
            is_bitarray = True
        sl = self.nested_slices[feat_nm][level]
        if is_bitarray:
            h_sl = tuple([barr.tobytes() for barr in ht_list[sl[0]:sl[1]]])
        else:
            h_sl = tuple(ht_list[sl[0]:sl[1]])
        if (h_sl in children):
            result = children[h_sl]
        return result

    def retrieve_nested_keys(self, feat_nm, level):
        if level >= len(self.nested_index[feat_nm]):
            return list([])
        else:
            return self.nested_index[feat_nm][level].keys()

    def retrieve_nested(self, feat_nm, ht_list, level):
        if (ht_list is None):
            result = []
            return
        if (not self.nested_index_created):
            raise Exception('nested index not created')
        result = []
        idx = self.nested_index[feat_nm][level]
        is_bitarray = False
        if isinstance(ht_list[0], bitarray):
            is_bitarray = True
        sl = self.nested_slices[feat_nm][level]
        if is_bitarray:
            h_sl = tuple([barr.tobytes() for barr in ht_list[sl[0]:sl[1]]])
        else:
            h_sl = tuple(ht_list[sl[0]:sl[1]])
        if (h_sl in idx):
            result = idx[h_sl]

        return result
