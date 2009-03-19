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

config.VersionRange("6.0",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32','_WINDOWS','_WIN32_WINNT=0x500']
                        )
                    )
config.VersionRange("7-*",
                    append=ConfigValues(
                        CPPDEFINES=['WIN32','_WINDOWS','_WIN32_WINNT=0x501']
                        )
                    )
    



