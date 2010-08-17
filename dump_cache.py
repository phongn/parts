import sys
import os
import cPickle
import pprint

datafile=sys.argv[1]

try:
    if os.path.exists(datafile):
        output = open(datafile, 'rb')
        tmp=cPickle.load(output)
        (tmp,stored_data)=tmp
        output.close()
        
except IOError,ec:
    pass


pp=pprint.PrettyPrinter()
pp.pprint(stored_data)