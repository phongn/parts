######################################
### Intel win32 compiler configurations debug
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['INTELC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/Od','/MDd','/W3','/Zc:wchar_t','/RTC1'],
                        CXXFLAGS=['/EHsc','/GR'],
                        LINKFLAGS=['/nodefaultlib:"libmmdd.lib"']
                        )
                    )

