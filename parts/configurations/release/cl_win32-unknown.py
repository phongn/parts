######################################
### Microsoft compiler configurations release
######################################

import sys
from parts.config_base import *
from parts.config import *
import SCons.Script

def map_default_version(env):
    return env['MSVC_VERSION']
    

config=configuration(map_default_version)

config.VersionRange("6.0",
                    append=ConfigValues(
                        CCFLAGS=['/Ox','/MD','/W3'],
                        CXXFLAGS=['$CCFLAGS','/EHsc','/GR']
                        )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CCFLAGS=['/nologo','/Od','/MDd','/W3','/Zc:wchar_t','/RTC1'],
                        CXXFLAGS=['$CCFLAGS','/EHsc','/GR']
                        )
                    )

