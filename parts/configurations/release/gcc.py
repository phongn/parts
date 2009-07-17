######################################
### gcc compiler configurations release
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['GCC_VERSION']
    
config=configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=['-O2']
                        )
                    )

