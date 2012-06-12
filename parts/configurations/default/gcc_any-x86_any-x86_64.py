######################################
### gcc compiler configurations debug
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['GCC_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    prepend=ConfigValues(
                        CCFLAGS=['-m64']
                        )
                    )
