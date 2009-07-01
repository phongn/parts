######################################
### default gcc configurations default
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['GCC_VERSION']

config=configuration(map_default_version)

config.VersionRange("3-*",
                    append=ConfigValues(
                        CCFLAGS=['-m64'],
                        LINKFLAGS=['-m64']
                        )
                    )
    



