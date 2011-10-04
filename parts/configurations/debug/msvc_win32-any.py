######################################
### Microsoft compiler configurations pat_debug
######################################

import sys
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['MSVC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("6.0",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Od','/MDd','/W3','/GZ'],
                        CXXFLAGS=['/EHsc','/GR'],
                        CPPDEFINES=['DEBUG']
                        )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Od','/MDd','/W3','/RTC1'],
                        CXXFLAGS=['/EHsc','/GR'],
                        CPPDEFINES=['DEBUG']
                        )
                    )


