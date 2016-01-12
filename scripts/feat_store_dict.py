#!/usr/bin/env python

"""
Implementation of the interface feat_store using in-memory dictionaries in Python
"""

# BC, 3/24/2015

import json

class feat_store_dict(object):
    """
    Implementation of feature storage using dictionaries

    The basic idea is to abstract the feature store and allow several different storage mechanisms.
    We use duck typing for compatibility across different implementations.

    The methods that should be implemented are:
    - Constructor: feat_store(config_str)
    - Iterator methods: __iter__, next
    - add(key, value)
    - names(), keys(), close()
    - __getitem__(key)  -- for general data store not an efficient method -- use iterators whenever possible

    Additional methods implemented for this version:
    - (none)

    The config file for open should be JSON and contain the following fields:
    - "features": These are the features to be processed, their name, and type. 
      [{"type": "str", "name": "feat1"}, {"type": "int", "name": "feat2"}]
    - types are "str", "int", and "vec"
    """

    def __init__(self, config_str=None):
        """x.__init__(config_str) initializes feature store with JSON string parameters"""
        if config_str!=None:
            self.config = json.loads(config_str)
            self.feat = {}
            self.feat_names = set([x['name'] for x in self.config])

    def add(self, key, y):
        """x.add(key, y) adds y to feature store with key 'key'"""
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

    def __getitem__(self, i):
        """x.__getitem__(i) <==> x[i]"""
        if not hasattr(self, 'config'):
            raise Exception('feat_store_list: must provide configuration before using a feature store')
        return self.feat[i]

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        self.iter = self.feat.iteritems()
        return self

    def keys(self):
        """x.keys() returns list of keys"""
        return self.feat.keys()

    def names(self):
        """x.keys() returns list of feature names"""
        return self.feat_names

    def next(self):
        """x.next() -> the next value, or raise StopIteration"""
        if not hasattr(self, 'config'):
            raise Exception('feat_store_list: must provide configuration before using a feature store')
        try:
            (key, value) = self.iter.next()
            return (key, value)
        except StopIteration:
            raise StopIteration()
