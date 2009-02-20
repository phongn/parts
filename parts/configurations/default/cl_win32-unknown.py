######################################
### Microsoft compiler configurations default
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['MSVC_VERSION']
    

config=configuration(map_default_version)

