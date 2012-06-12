######################################
### Intel posix compiler configurations pat_debug
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['INTELC_VERSION']
    

config=configuration(map_default_version)


config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['-O0','-g'],
                        CPPDEFINES=['DEBUG']
                        )
                    )
                    
