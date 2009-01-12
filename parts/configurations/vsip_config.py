######################################
### WDK configurations
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script
import re

g_env=SCons.Script.DefaultEnvironment()


def vsip_deftool_add(map,tool,ver,config):
    map['tools']=[(tool,{'version':ver,'verbose':1})]
    return True




if sys.platform=='win32':    
    configuration('release','vsip','8.0.60301',vsip_deftool_add)
    configuration('debug','vsip','8.0.60301',vsip_deftool_add)
    
    configuration('release','vsip','8.0.61205.56',vsip_deftool_add)
    configuration('debug','vsip','8.0.61205.56',vsip_deftool_add)
    
#defaults
    configuration('release','vsip',None,vsip_deftool_add)
    configuration('debug','vsip',None,vsip_deftool_add)