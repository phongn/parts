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
                        CCFLAGS=['/nologo','/Ox','/MD','/W3','/Zc:wchar_t'],
                        CXXFLAGS=['/EHsc','/GR'],
                        LINKFLAGS=['/nodefaultlib:"libmmd.lib"']
                        )
                    )
