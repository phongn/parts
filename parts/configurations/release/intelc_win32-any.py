######################################
### Intel win32 compiler configurations release
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['INTELC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("7-10.*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Ox','/MD','/W3'],
                        CXXFLAGS=['/EHsc','/GR']
                        )
                    )
                    
config.VersionRange("11-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Ox','/MD','/W3'],
                        CXXFLAGS=['/EHsc','/GR']
                        )
                    )
                    
