######################################
### WDK configurations
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script
import re

g_env=SCons.Script.DefaultEnvironment()


def WDK_deftool_add(map,tool,ver,config):
    map['tools']=[(tool,{'version':ver,'verbose':1})]
    return True




if sys.platform=='win32':    
    configuration('release','wdk','3790.1830',WDK_deftool_add)
    configuration('debug','wdk','3790.1830',WDK_deftool_add)
    
#defaults
    configuration('release','wdk',None,WDK_deftool_add)
    configuration('debug','wdk',None,WDK_deftool_add)