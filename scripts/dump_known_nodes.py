"""
import sys
import os
# load the SCons code
import scons_setup
scons_setup.scons_path()

sys.path=[#os.path.abspath('./'),
            #os.path.abspath('../'),

            # this is a hack till better code is generated
            #'c:/python26/lib/site-packages/parts',
            #'c:/python27/lib/site-packages/parts'
          ]+sys.path

import cPickle
import pprint

import parts.pickle_helpers as pickle_helpers
import parts.glb as glb

datafile=sys.argv[1]
tmp=os.path.split(os.path.split(os.path.abspath(datafile))[0])[1]

glb.engine._cache_key=tmp

glb.pnodes.dump()
"""
