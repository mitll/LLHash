#!/usr/bin/env python

#
# Run some tests on the feat store with a few examples
#

# Written by BC, 3/24/15

from feat_store_dict import feat_store_dict as feat_store

# Initialize the feature store
config = '[{"name":"name","type":"str","idx":0},{"name":"age","type":"int","idx":1}]'
print 'Config is {}\n'.format(config)
fs = feat_store(config)

# Add something to the feature store
print 'Trying to add something with correct syntax ...'
dgood = {"name":"Bob Jones","age":25}
print '{}'.format(dgood)
fs.add(72, dgood)

# Add another thing to the feature store
fs.add(25, {"name":"Tommy Lee","age":30})

# Add something wrong
print 'Trying to add something with incorrect syntax ...'
dbad = {"namey":"Tommy Lee","age":30}
print '{}'.format(dbad)
try:
    fs.add(2, dbad)
except ValueError as e:
    print 'Caught exception: {}'.format(e)
print

# Iterate over all instances
print 'Iterating over all instances -- these are not guaranteed to be in instance order:'
for (i,f) in fs:
    print "item #: {} , value: {}".format(i, f)
print

# Retrieve specific instance
print 'Retrieving instance 72 :'
print "feat store [ {} ] = {}".format(1, fs[72])
print

# Finding keys
print "Keys are:"
print "{}".format(fs.keys())
print

# Close the feature store
print 'Closing the feature store'
print
fs.close()

